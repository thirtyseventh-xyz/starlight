from flask import Blueprint
from app import limiter
import os
import requests
import sentry_sdk

misc_routes = Blueprint("misc",__name__,url_prefix="/misc")

@misc_routes.route("/rsvp-count")
@limiter.limit("60 per minute")
def send_submissions():
    custom_response_headers = {"Access-Control-Allow-Origin": "*"}
    submission_request_cap = 150

    #get number of rsvps from fillout
    headers = {"Authorization": "Bearer " + str(os.environ.get("FILLOUT_API_KEY"))}
    url = "https://api.fillout.com/v1/api/forms/" + str(os.environ.get("FILLOUT_FORM_ID")) + "/submissions?limit=" + str(submission_request_cap)

    response = requests.get(url,headers=headers)

    if response.status_code != 200:
        sentry_sdk.capture_message(
            "request to fillout to get stats failed",
            level="warning",
            tags={"token_request_status_code":response.status_code},
            extras={"request_json":response.json()}
        )
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

    return {"total_submissions":submissions},200,custom_response_headers

@misc_routes.route("/status")
def basic_status(): # this is entirely the wrong way to do this but it works and i dont care
    return {"ok":"true"},200