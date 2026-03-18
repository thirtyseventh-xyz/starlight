import os
import requests
import jwt
import json
from jwt.algorithms import RSAAlgorithm
from flask import Flask
from flask import redirect
from flask import request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/")
def get_out():
    return redirect(os.environ.get("PROD_MAIN_URL"))

@app.route("/oauth/callback")
def recieve_auth():
    code = request.args.get("code")

    if code is None:
        return {"error": "wow either you broke something really bad, or you found this endpoint and never tried to do anything important in the first place. if you didn't expect an error, please contact @thirtyseven on slack"}, 400

    token_request_payload = {
        "client_id": str(os.environ.get("HCA_OAUTH_CLIENT_ID")),
        "client_secret": str(os.environ.get("HCA_OAUTH_CLIENT_SECRET")),
        "redirect_uri": str(os.environ.get("REDIRECT_URI")),
        "code": str(code),
        "grant_type": "authorization_code"
    }
    token_request_result = requests.post("https://auth.hackclub.com/oauth/token",data=token_request_payload)

    if token_request_result.status_code != 200 and token_request_result.status_code != 201:
        return token_request_result.status_code

    token_request_response = token_request_result.json()
    access_token = token_request_response['access_token']

    headers = {
        "Authorization": "Bearer " +access_token
    }

    response = requests.get("https://auth.hackclub.com/api/v1/me",headers=headers)
    response_json = response.json()

    return redirect(os.environ.get("PROD_MAIN_URL")+"/auth/callback")






