import os
import requests
import jwt
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
        return 400

    token_request_payload = {
        "client_id": str(os.environ.get("HCA_OAUTH_CLIENT_ID")),
        "client_secret": str(os.environ.get("HCA_OAUTH_CLIENT_SECRET")),
        "redirect_uri": str(os.environ.get("REDIRECT_URI")),
        "code": str(code),
        "grant_type": "authorization_code"
    }
    token_request_result = requests.post("https://auth.hackclub.com/oauth/token",data=token_request_payload)

    token_request_response = token_request_result.json()
    access_token = token_request_response['access_token']
    jwt_token = token_request_response['id_token']

    jwt_public =

    jwt_data = jwt.decode(jwt_token,)

    return redirect()






