import os
import requests
import base64
import sentry_sdk
import auth
from flask import Flask, request, redirect, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from slack_sdk import WebClient
from pyairtable import Api, formulas
from sentry_sdk.integrations.flask import FlaskIntegration

#This code is spaghetti and needs to be fixed lol TODO: split stuff into separate files using blueprints and make it more organized
# oh also TODO: get url safe checks on all the places users can input stuff (rn just the oauth callback)

load_dotenv()

slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

sentry_sdk.init(os.environ.get("SENTRY_DSN"), integrations=[FlaskIntegration()])
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
