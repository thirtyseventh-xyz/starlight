import os
import requests
from flask import Flask
from flask import redirect
from flask import request
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()
app = Flask(__name__)
limiter = Limiter(get_remote_address,app=app, default_limits=["20000 per day", "5000 per hour"] )

@app.route("/")
def get_out():
    return redirect(os.environ.get("PROD_MAIN_URL"))

@app.route("/oauth/callback")
def recieve_auth():
    if bool(os.environ.get("DISABLE_OAUTH")):
        return "endpoint currently disabled", 423

    code = request.args.get("code")

    if code is None:
        return "wow either something has gone horribly wrong, or you found this endpoint and never tried to do anything important in the first place. if you didn't expect an error, please contact @thirtyseven on slack", 400

    token_request_payload = {
        "client_id": str(os.environ.get("HCA_OAUTH_CLIENT_ID")),
        "client_secret": str(os.environ.get("HCA_OAUTH_CLIENT_SECRET")),
        "redirect_uri": str(os.environ.get("REDIRECT_URI")),
        "code": str(code),
        "grant_type": "authorization_code"
    }
    token_request_result = requests.post("https://auth.hackclub.com/oauth/token",data=token_request_payload)

    if token_request_result.status_code != 200 and token_request_result.status_code != 201:
        return "wow something broke really bad, please let @thirtyseven know on slack that this happened", token_request_result.status_code

    token_request_response = token_request_result.json()
    access_token = token_request_response['access_token']

    hca_authed_req_headers = {
        "Authorization": "Bearer " +access_token
    }

    hca_user_data_request = requests.get("https://auth.hackclub.com/api/v1/me",headers=hca_authed_req_headers)
    hca_user_data_json = hca_user_data_request.json()

    breakpoint()

    return redirect(os.environ.get("PROD_MAIN_URL")+"/auth/callback")

@app.route("/tempapi/rsvp-submissions")
@limiter.limit("60 per minute")
def send_submissions():
    headers = {"Authorization": "Bearer " + str(os.environ.get("FILLOUT_API_KEY"))}
    url = "https://api.fillout.com/v1/api/forms/" + str(os.environ.get("FILLOUT_FORM_ID")) + "/submissions?limit=50&sort=asc"

    response = requests.get(url,headers=headers)

    if response.status_code == 200:
        return {"total_submissions":response.json()['totalResponses']}
    else:
        return {"total_submissions":-1},500






