from flask import Blueprint,redirect,request, session
from slack_sdk import WebClient
import requests
import base64
import os
import sentry_sdk
import datetime
import secrets
import utils.auth
import utils.db
from utils.models import User

slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

encryption_key = base64.urlsafe_b64decode(os.environ.get("ENCRYPTION_KEY"))

main_url = os.environ.get("PROD_MAIN_URL")

auth = Blueprint("oauth", __name__, url_prefix="/auth")

@auth.before_request
def check_session():
    if request.endpoint in ("oauth.clear_sessions", "oauth.logout", "oauth.hackatime_outgoing", "oauth.hackatime_callback"):
        if not utils.auth.check_session(session):
            return redirect(main_url+"/error?code=401&message=you+are+not+signed+in!")

@auth.route("/login")
def send_auth():
    if os.environ.get("DISABLE_OAUTH").lower() == "true":
        return redirect(main_url+"/error?code=423&message=sign+in+is+currently+disabled")

    if utils.auth.check_session(session):
        return redirect(main_url)

    redirect_url = "https://auth.hackclub.com/oauth/authorize?client_id="+str(os.environ.get("HCA_OAUTH_CLIENT_ID"))+"&redirect_uri="+str(os.environ.get("HCA_OAUTH_REDIRECT_URI").replace(":","%3A").replace("/","%2F"))+"&response_type=code&scope=openid+name+verification_status+slack_id"
    return redirect(redirect_url)

@auth.route("/callback")
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

    encrypted_token = utils.auth.encrypt_token(access_token, hca_id, encryption_key) #encrypt stuff so we dont get jumped by meta

    session['created_at'] = datetime.datetime.now(tz=datetime.timezone.utc)

    db_session = utils.db.SessionLocal()

    #check if an entry for the oidc id already exists in the database
    account_search_result = db_session.query(User).filter(User.oidc_ident == hca_id).all()

    if len(account_search_result) == 0:#new account creation
        try:
            slack_user_data = slack_client.users_profile_get(user=hca_user_data_json['identity']['slack_id'])
            slack_display_name = slack_user_data['profile']['display_name_normalized']

            new_user = User(
                oidc_ident=hca_id,
                hca_token=encrypted_token,
                eligible=ysws_eligible,
                slack_id=hca_user_data_json['identity']['slack_id'],
                username=slack_display_name
            )

            db_session.add(new_user)
            db_session.commit()

            new_user = db_session.query(User).filter(User.oidc_ident == hca_id).all()[0]
            if new_user.id == 1: # this is like certainly a bad idea but i cba to make it better
                new_user.admin = True
                db_session.commit()

            session['user_id'] = new_user.id

        except Exception as e:
            sentry_sdk.capture_exception(e)
            return redirect(main_url + "/error?code=500&message=something+failed+trying+to+create+your+account+in+our+system%2E+please+contact+%40thirtyseven+on+slack+immediately")  #

    elif len(account_search_result) == 1: #account already exists
        existing_account = account_search_result[0]
        session['user_id'] = existing_account.id
    else:
        return redirect(main_url+"/error?code=500&message=something%20went%20wrong%20setting%20up%20your%20account.%20please%20contact%20%40thirtyseven%20on%20slack%20immediately!")

    db_session.close()
    return redirect(main_url+"/dashboard")

@auth.route("/clear-sessions")
def clear_sessions():
    db_session = utils.db.SessionLocal()
    try:
        user = db_session.query(User).where(User.id == session['user_id']).first()

        user.last_session_clear_date = datetime.datetime.now()
        db_session.commit()

        session.clear()
        return redirect(main_url)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return redirect(main_url+"/error?code=500&message=something+went+wrong+trying+to+clear+your+sessions.%20please%20contact%20%40thirtyseven%20on%20slack%20immediately!")
    finally:
        db_session.close()

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(main_url)

@auth.route("/hackatime/link")
def hackatime_outgoing():
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    hackatime_oauth_url = "https://hackatime.hackclub.com/oauth/authorize?client_id="+str(os.environ.get("HACKATIME_OAUTH_CLIENT_ID")+"&redirect_uri="+str(os.environ.get("HACKATIME_OAUTH_REDIRECT_URI"))+"&response_type=code&scope=profile+read&state="+str(state))
    return redirect(hackatime_oauth_url)

@auth.route("/hackatime/callback")
def hackatime_callback():
    db_session = utils.db.SessionLocal()
    try:
        state = request.args.get("state")
        code = request.args.get("code")

        if state != session.pop("oauth_state"):
            return redirect(main_url + "/error?code=400&message=invalid+oauth+state")

        hackatime_token_request_data = {
            "client_id": str(os.environ.get("HACKATIME_OAUTH_CLIENT_ID")),
            "client_secret": str(os.environ.get("HACKATIME_OAUTH_CLIENT_SECRET")),
            "code": code,
            "redirect_uri": str(os.environ.get("HACKATIME_OAUTH_REDIRECT_URI")),
            "grant_type": "authorization_code"
        }

        token_req_response = requests.post("https://hackatime.hackclub.com/oauth/token", json=hackatime_token_request_data)
        hackatime_token = token_req_response.json()['access_token']

        user = db_session.query(User).where(User.id == session['user_id']).first()

        hackatime_token = utils.auth.encrypt_token(hackatime_token,user.oidc_ident,encryption_key)

        user.hackatime_token = hackatime_token
        db_session.commit()

        return redirect(main_url)

    except Exception as e:
        sentry_sdk.capture_exception(e)
        return redirect(main_url+"/error?code=500&message=something+went+wrong+trying+to+link+your+hackatime+account")
    finally:
        db_session.close()