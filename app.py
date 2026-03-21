import ast
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

def encrypt_token(token, id):
    key = base64.urlsafe_b64decode(os.environ.get("ENCRYPTION_KEY"))
    aesgcm = AESGCM(key)

    nonce = os.urandom(12)

    ciphertext = aesgcm.encrypt(nonce,token.encode(),id.encode())
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()

@app.route("/")
def get_out():
    return redirect(os.environ.get("PROD_MAIN_URL"))

@app.route("/oauth/callback")
def recieve_auth():
    if os.environ.get("DISABLE_OAUTH").lower() == "true":
        return "endpoint currently disabled", 423

    code = request.args.get("code")

    if code is None:
        return "either something has gone horribly wrong, or you found this endpoint and never tried to do anything important in the first place. if you didn't expect an error, please contact @thirtyseven on slack", 400

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
        "Authorization": "Bearer " +access_token
    }

    hca_user_data_request = requests.get("https://auth.hackclub.com/api/v1/me",headers=hca_authed_req_headers)
    hca_user_data_json = hca_user_data_request.json()

    hca_id = hca_user_data_json['identity']['id']
    ysws_eligible = hca_user_data_json['identity']['ysws_eligible']

    encrypted_token = encrypt_token(access_token,hca_id)

    breakpoint()

    return redirect(os.environ.get("PROD_MAIN_URL")+"/auth/callback")

@app.route("/tempapi/rsvp-submissions")
@limiter.limit("60 per minute")
def send_submissions():
    headers = {"Authorization": "Bearer " + str(os.environ.get("FILLOUT_API_KEY"))}
    url = "https://api.fillout.com/v1/api/forms/" + str(os.environ.get("FILLOUT_FORM_ID")) + "/submissions?limit=50&sort=asc"

    response = requests.get(url,headers=headers)

    custom_response_headers = {"Access-Control-Allow-Origin": "*"}

    if response.status_code == 200:
        return {"total_submissions":response.json()['totalResponses']},200,custom_response_headers
    else:
        print("[ERROR] call to fillout api did not return successfully\n|    request returned http code "+str(response.status_code)+"\n\    with error: "+str(response.json()['message']))
        return {"total_submissions":-1},500,custom_response_headers
