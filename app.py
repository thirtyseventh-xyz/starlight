import os
import requests
import base64
from flask import Flask
from flask import redirect
from flask import request
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()

app = Flask(__name__)
limiter = Limiter(get_remote_address,app=app, default_limits=["20000 per day", "5000 per hour"] )

key = base64.urlsafe_b64decode(os.environ.get("ENCRYPTION_KEY"))
def encrypt_token(token, id):#i had to get claude (booo) to help with some of this, as i have no idea how encryption works. i have done my research outside of that, making sure what it told me to do makes sense
    aesgcm = AESGCM(key) #load the key

    nonce = os.urandom(12) #generate a random 96 bit nonce

    ciphertext = aesgcm.encrypt(nonce,token.encode(),id.encode()) #actually encrypt ti
    return base64.urlsafe_b64encode(nonce + ciphertext).decode() #encode the nonce with it

def decrypt_token(encrypted_token, id):
    data = base64.urlsafe_b64decode(encrypted_token.encode()) #read the encrypted token properly
    aesgcm = AESGCM(key) #load the key

    nonce, ciphertext = data[:12], data[12:] #split the nonce and ciphertext

    access_token = aesgcm.decrypt(nonce,ciphertext,id.encode()).decode() #decrypt the thing
    return access_token

main_url = os.environ.get("PROD_MAIN_URL")


@app.route("/")
def get_out():
    return redirect(main_url)

@app.route("/oauth/callback")
def recieve_auth(): #handle the data returned from the oauth endpoint
    #basic hecks and stuffc
    if os.environ.get("DISABLE_OAUTH").lower() == "true":
        return "endpoint currently disabled", 423

    code = request.args.get("code")

    if code is None:
        return "either something has gone horribly wrong, or you found this endpoint and never tried to do anything important in the first place. if you didn't expect an error, please contact @thirtyseven on slack", 400

    #aquire the access token from hca
    token_request_payload = {
        "client_id": str(os.environ.get("HCA_OAUTH_CLIENT_ID")),
        "client_secret": str(os.environ.get("HCA_OAUTH_CLIENT_SECRET")),
        "redirect_uri": str(os.environ.get("REDIRECT_URI")),
        "code": str(code),
        "grant_type": "authorization_code"
    }
    token_request_result = requests.post("https://auth.hackclub.com/oauth/token",data=token_request_payload)

    if token_request_result.status_code != 200 and token_request_result.status_code != 201:
        return "something has gone very wrong server side (probably), please let @thirtyseven know on slack that this happened", token_request_result.status_code

    token_request_response = token_request_result.json()
    access_token = token_request_response['access_token']

    hca_authed_req_headers = {
        "Authorization": "Bearer "+access_token
    }

    #get userdata from hca
    hca_user_data_request = requests.get("https://auth.hackclub.com/api/v1/me",headers=hca_authed_req_headers)
    hca_user_data_json = hca_user_data_request.json()

    hca_id = hca_user_data_json['identity']['id']
    ysws_eligible = hca_user_data_json['identity']['ysws_eligible']

    if not ysws_eligible: #get out if youre not eligible
        return redirect(main_url+"/error?code=401&message=you+are+not+eligible+to+participate+in+ysws+events")

    encrypted_token = encrypt_token(access_token,hca_id) #encrypt stuff so we dont get jumped by meta

    #init airtable data and stuff
    auth_table_url = "https://api.airtable.com/v0/"+os.environ.get("AIRTABLE_BASE_ID")+"/"+os.environ.get("AIRTABLE_TABLE_ID") #table where entries for auth system are
    airtable_req_headers = {
        "Authorization": "Bearer "+os.environ.get("AIRTABLE_API_KEY")
    }
    #check if an entry for the oidc id already exists in airtable
    url = auth_table_url+"?filterByFormula=%7BOIDC%20ID%7D%3D'"+hca_id+"'"
    account_search_result = requests.get(url,headers=airtable_req_headers) #get entries with an oidc matching the current one
    account_search_result = account_search_result.json()


    if not len(account_search_result['records']) == 1: # check if there is any auth accounts with the same oidc as the current user
        #new account creation #TODO: make something reflect this in the other table, the one used for basic account management
        airtable_new_acc_payload = {
            "records":[
                {
                   "fields": {
                       "OIDC ID": hca_id,
                       "Name": hca_user_data_json['identity']['first_name'] + " " + hca_user_data_json['identity']['last_name'],
                       "Encrypted HCA Access Token": encrypted_token,
                       "Eligible": ysws_eligible,
                       "Slack ID": hca_user_data_json['identity']['slack_id']
                   }
                }
            ]
        }

        airtable_response = requests.post(auth_table_url,headers=airtable_req_headers,json=airtable_new_acc_payload)

        if airtable_response.status_code != 200:
            print("airtable identity storing failed with http code "+str(airtable_response.status_code)+"\nit failed with response"+str(airtable_response.json()))
            return "oh crap something failed trying to create your account in our system. please contact @thirtyseven on slack immediately",500



    return redirect(main_url+"/auth/callback")

@app.route("/tempapi/rsvp-submissions")
@limiter.limit("60 per minute")
def send_submissions():
    #get number of rsvps from fillout
    headers = {"Authorization": "Bearer " + str(os.environ.get("FILLOUT_API_KEY"))}
    url = "https://api.fillout.com/v1/api/forms/" + str(os.environ.get("FILLOUT_FORM_ID")) + "/submissions?limit=50&sort=asc"

    response = requests.get(url,headers=headers)

    #send it to the client
    custom_response_headers = {"Access-Control-Allow-Origin": "*"}

    if response.status_code == 200:
        return {"total_submissions":response.json()['totalResponses']},200,custom_response_headers
    else:
        print("[ERROR] call to fillout api did not return successfully\n|    request returned http code "+str(response.status_code)+"\n\    with error: "+str(response.json()['message']))
        return {"total_submissions":-1},500,custom_response_headers
