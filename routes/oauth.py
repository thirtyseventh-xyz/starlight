from flask import Blueprint,redirect,request, session
from pyairtable import Api, formulas
from slack_sdk import WebClient
import requests
import base64
import auth
import os
import sentry_sdk

slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

encryption_key = base64.urlsafe_b64decode(os.environ.get("ENCRYPTION_KEY"))

main_url = os.environ.get("PROD_MAIN_URL")

airtable_api = Api(os.environ.get("AIRTABLE_API_KEY"))
auth_table = airtable_api.table(os.environ.get("AIRTABLE_BASE_ID"),os.environ.get("AIRTABLE_AUTH_TABLE_ID"))
users_table = airtable_api.table(os.environ.get("AIRTABLE_BASE_ID"),os.environ.get("AIRTABLE_USERS_TABLE_ID"))

oauth_routes = Blueprint("oauth",__name__,url_prefix="/oauth")

@oauth_routes.route("/login")
def send_auth():
    if os.environ.get("DISABLE_OAUTH").lower() == "true":
        return redirect(main_url+"/error?code=423&message=sign+in+is+currently+disabled")

    redirect_url = "https://auth.hackclub.com/oauth/authorize?client_id="+str(os.environ.get("HCA_OAUTH_CLIENT_ID"))+"&redirect_uri="+str(os.environ.get("HCA_OAUTH_REDIRECT_URI").replace(":","%3A").replace("/","%2F"))+"&response_type=code&scope=openid+name+verification_status"
    return redirect(redirect_url)

@oauth_routes.route("/callback")
def receive_auth(): #handle the data returned from the oauth endpoint

    if os.environ.get("DISABLE_OAUTH").lower() == "true":
        return redirect(main_url+"/error?code=423&message=sign+in+is+currently+disabled")

    code = request.args.get("code")

    if code is None:
        print("the code passed to the oauth callback param was none, someone broke something")
        return redirect(main_url+ "/error?code=400&message=either%20something%20has%20gone%20horribly%20wrong%2C%20or%20you%20found%20this%20endpoint%20and%20never%20tried%20to%20do%20anything%20important%20in%20the%20first%20place%2E%20if%20you%20didn't%20expect%20an%20error%2C%20please%20contact%20%40thirtyseven%20on%20slack")


    token_request_payload = {
        "client_id": str(os.environ.get("HCA_OAUTH_CLIENT_ID")),
        "client_secret": str(os.environ.get("HCA_OAUTH_CLIENT_SECRET")),
        "redirect_uri": str(os.environ.get("HCA_OAUTH_REDIRECT_URI")),
        "code": str(code),
        "grant_type": "authorization_code"
    }
    token_request_result = requests.post("https://auth.hackclub.com/oauth/token",data=token_request_payload)

    if token_request_result.status_code != 200:
        if token_request_result.status_code == 400 and token_request_result.json()['error'] == "invalid_grant":
            print("print invalid hca grant")
            return redirect(main_url+"/error?code=401&message=invalid+oauth+grant!+if+you+believe+this+is+a+mistake%2C+contact+%40thirtyseven+on+slack")

        sentry_sdk.capture_message(
            "request to hca for access token failed",
            level="warning",
            tags={"token_request_status_code":token_request_result.status_code},
            extras={"request_json":token_request_result.json()}
        )
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

    if len(account_search_result) == 0:#new account creation
        try:
            airtable_new_auth_entry = {
               "OIDC ID": hca_id,
               "Name": hca_user_data_json['identity']['first_name'] + " " + hca_user_data_json['identity']['last_name'],
               "Encrypted HCA Access Token": encrypted_token,
               "Eligible": ysws_eligible,
               "Slack ID": hca_user_data_json['identity']['slack_id']
            }

            auth_response = auth_table.create(airtable_new_auth_entry)

            slack_user_data = slack_client.users_profile_get(user=hca_user_data_json['identity']['slack_id'])
            slack_display_name = slack_user_data['profile']['display_name_normalized']

            airtable_new_user_entry = {
                "Username": slack_display_name,
                "Auth Entry": [auth_response['id']]
            }

            users_table.create(airtable_new_user_entry)

            session['user_id'] = hca_id

        except Exception as e:
            sentry_sdk.capture_exception(e)
            return redirect(main_url + "/error?code=500&message=something+failed+trying+to+create+your+account+in+our+system%2E+please+contact+%40thirtyseven+on+slack+immediately")  #

    elif len(account_search_result) == 1: #account already exists
        session['user_id'] = hca_id
    else:
        return main_url+"/error?code=500&message=something%20went%20wrong%20setting%20up%20your%20account.%20please%20contact%20%40thirtyseven%20on%20slack%20immediately!"

    return redirect(main_url+"/auth/callback")