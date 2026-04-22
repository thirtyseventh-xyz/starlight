import os
import requests
import base64
import auth
from flask import Flask, request, redirect, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from slack_sdk import WebClient
from pyairtable import Api, formulas

#This code is spaghetti and needs to be fixed lol TODO: split stuff into separate files using blueprints and make it more organized
# oh also TODO: get url safe checks on all the places users can input stuff (rn just the oauth callback)

load_dotenv()

slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

app = Flask(__name__)
limiter = Limiter(get_remote_address,app=app, default_limits=["20000 per day", "5000 per hour"] )

encryption_key = base64.urlsafe_b64decode(os.environ.get("ENCRYPTION_KEY"))

main_url = os.environ.get("PROD_MAIN_URL")

airtable_api = Api(os.environ.get("AIRTABLE_API_KEY"))
auth_table = airtable_api.table(os.environ.get("AIRTABLE_BASE_ID"),os.environ.get("AIRTABLE_AUTH_TABLE_ID"))
users_table = airtable_api.table(os.environ.get("AIRTABLE_BASE_ID"),os.environ.get("AIRTABLE_USERS_TABLE_ID"))

@app.route("/")
def get_out():
    return redirect(main_url)

@app.errorhandler(404)
def fancy_404(e):
    return redirect(main_url+"/error?code=404&message=page+not+found%2E+maybe+you+are+looking+for+this+page+on+the+main+sparkle+domain+and+not+the+api%3F")

@app.route("/oauth/callback")
def recieve_auth(): #handle the data returned from the oauth endpoint
    #basic checks and stuff
    if os.environ.get("DISABLE_OAUTH").lower() == "true":
        return redirect(main_url+"/error?code=423&message=sign+in+is+currently+disabled")

    code = request.args.get("code")

    if code is None:
        print("the code passed to the oauth callback param was none, someone broke something")
        return redirect(main_url+ "/error?code=400&message=either%20something%20has%20gone%20horribly%20wrong%2C%20or%20you%20found%20this%20endpoint%20and%20never%20tried%20to%20do%20anything%20important%20in%20the%20first%20place%2E%20if%20you%20didn't%20expect%20an%20error%2C%20please%20contact%20%40thirtyseven%20on%20slack")

    final_client_response = make_response(redirect(main_url+"/auth/callback")) #setup the request now so i can add data later

    #aquire the access token from hca
    token_request_payload = {
        "client_id": str(os.environ.get("HCA_OAUTH_CLIENT_ID")),
        "client_secret": str(os.environ.get("HCA_OAUTH_CLIENT_SECRET")),
        "redirect_uri": str(os.environ.get("REDIRECT_URI")),
        "code": str(code),
        "grant_type": "authorization_code"
    }
    token_request_result = requests.post("https://auth.hackclub.com/oauth/token",data=token_request_payload)

    if token_request_result.status_code != 200:
        print("request to hca to get access token failed with code "+str(token_request_result.status_code)+"\nit failed with data "+str(token_request_result.json()))
        return redirect(main_url+"/error?code=500&message=something+has+gone+very+wrong+server+side+%28probably%29%2C+please+let+%40thirtyseven+know+on+slack+that+this+happened")

    token_request_response = token_request_result.json()
    access_token = token_request_response['access_token']

    hca_authed_req_headers = {"Authorization": "Bearer "+access_token}

    #get userdata from hca
    hca_user_data_request = requests.get("https://auth.hackclub.com/api/v1/me",headers=hca_authed_req_headers)
    hca_user_data_json = hca_user_data_request.json()

    hca_id = hca_user_data_json['identity']['id']
    ysws_eligible = hca_user_data_json['identity']['ysws_eligible']

    if not ysws_eligible: #get out if youre not eligible
        return redirect(main_url+"/error?code=403&message=you+are+not+eligible+to+participate+in+ysws+events")

    encrypted_token = auth.encrypt_token(access_token, hca_id, encryption_key) #encrypt stuff so we dont get jumped by meta

    #check if an entry for the oidc id already exists in airtable
    account_search_formula = formulas.match({"OIDC ID":hca_id})
    account_search_result = auth_table.all(formula=account_search_formula)

    if len(account_search_result) == 0: # check if there is any auth accounts with the same oidc as the current user
        #new account creation
        try:
            session_token, session_hash = auth.generate_session_token()

            airtable_new_auth_entry = {
               "OIDC ID": hca_id,
               "Name": hca_user_data_json['identity']['first_name'] + " " + hca_user_data_json['identity']['last_name'],
               "Encrypted HCA Access Token": encrypted_token,
               "Eligible": ysws_eligible,
               "Slack ID": hca_user_data_json['identity']['slack_id'],
               "Session Tokens": session_hash
            }

            auth_response = auth_table.create(airtable_new_auth_entry) # create the user in the auth table

            slack_user_data = slack_client.users_profile_get(user=hca_user_data_json['identity']['slack_id'])
            slack_display_name = slack_user_data['profile']['display_name_normalized']

            airtable_new_user_entry = {
                "Username": slack_display_name,
                "Auth Entry": [auth_response['id']]
            }

            users_table.create(airtable_new_user_entry) # create the user in the users db

            final_client_response.set_cookie( #add the cookie to the response to the client
                "sparkle_token",
                session_token,
                domain=".sparkle.dino.icu",
                httponly=True,
                samesite="lax",
                secure=True
            )
        except Exception as e:
            print("airtable identity creation failed! \n"+str(e))
            return redirect(main_url + "/error?code=500&message=something+failed+trying+to+create+your+account+in+our+system%2E+please+contact+%40thirtyseven+on+slack+immediately")  #

    elif len(account_search_result) == 1: #account already exists, but user is going through oauth so they need a new session token
        try:
            account_data = account_search_result[0]['fields']
            record_id = account_search_result[0]['id']

            #make a new session token and hash it
            session_token, session_hash = auth.generate_session_token()

            #get the current list of session tokens
            token_list_str = account_data['Session Tokens'] # TODO: This breaks if there are no listed tokens in airtable
            token_list = token_list_str.split("/n")

            token_list.append(session_hash) #add the new token to the list
            token_list_str = "\n".join(token_list)

            #ad the token list to airtable
            session_create_data = {"Session Tokens": token_list_str}
            auth_table.update(record_id, session_create_data)

            final_client_response.set_cookie( #add the cookie to the response to the client
                "sparkle_token",
                session_token,
                domain=".sparkle.dino.icu",
                httponly=True,
                samesite="lax",
                secure=True
            )
        except Exception as e:
            print("airtable session creation failed! \n"+str(e))
            return main_url+"/error?code=500&message=something%20went%20wrong%20signing%20you%20in.%20please%20contact%20%40thirtyseven%20on%20slack"
    else:
        return main_url+"/error?code=500&message=something%20went%20wrong%20setting%20up%20your%20account.%20please%20contact%20%40thirtyseven%20on%20slack%20immediately!"

    return final_client_response

@app.route("/tempapi/rsvp-submissions")
@app.route("/misc/rsvp-count")
@limiter.limit("60 per minute")
def send_submissions():
    custom_response_headers = {"Access-Control-Allow-Origin": "*"}
    submission_request_cap = 150

    #get number of rsvps from fillout
    headers = {"Authorization": "Bearer " + str(os.environ.get("FILLOUT_API_KEY"))}
    url = "https://api.fillout.com/v1/api/forms/" + str(os.environ.get("FILLOUT_FORM_ID")) + "/submissions?limit=" + str(submission_request_cap)

    response = requests.get(url,headers=headers)

    if response.status_code != 200: #make sure it worked
        print("call to fillout api did not return successfully\n|    request returned http code " + str(response.status_code) + "\n\    with error: " + str(response.json()['message']))
        return {"total_submissions": -1}, 500, custom_response_headers

    #iteration bs to repeat the submissions request until we get all of them
    offset = 0

    submissions = response.json()['totalResponses']
    while submissions % submission_request_cap == 0:
        offset += submission_request_cap
        url = "https://api.fillout.com/v1/api/forms/" + str(os.environ.get("FILLOUT_FORM_ID")) + "/submissions?limit=" + str(submission_request_cap) + "&offset=" + str(offset)

        response = requests.get(url, headers=headers)
        if response.json()['totalResponses'] == 0:
            break
        submissions += response.json()['totalResponses']


    #send it to the client
    return {"total_submissions":submissions},200,custom_response_headers

@app.route("/misc/status")
def basic_status(): # this is entirely the wrong way to do this but it works and i dont care
    return {"ok":"true"},200
