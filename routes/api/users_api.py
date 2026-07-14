import os
import base64
import requests
import sentry_sdk
from flask import Blueprint, session, request, jsonify, abort
from werkzeug.exceptions import HTTPException
import utils.db
from utils.models import User
import utils.auth

users_api = Blueprint("users_api", __name__, url_prefix="/api/user")
encryption_key = base64.urlsafe_b64decode(os.environ.get("ENCRYPTION_KEY"))

@users_api.errorhandler(HTTPException)
def json_error_reporting(e):
    return jsonify(error=e.name,context=e.description), e.code

@users_api.before_request
def auth_check():
    if not utils.auth.check_session(session):
        abort(401,description="invalid_session")

@users_api.route("/me")
def get_user_info():
    db_session = utils.db.SessionLocal()
    try:
        user_id = session.get("user_id")
        user = db_session.query(User).filter(User.id == user_id).all()[0]

        return {
            "id": user.id,
            "slack_id": user.slack_id,
            "username": user.username,
            "join_date": str(user.join_date)
        }, 200
    except Exception as e:
        sentry_sdk.capture_exception(e,extras={"user_id":user.oidc_ident})
        abort(500,description="internal_server_error")
    finally:
        db_session.close()

@users_api.route("/me/update-username", methods=['PUT'])
def update_username():
    db_session = utils.db.SessionLocal()
    try:
        user_id = session.get("user_id")
        user = db_session.query(User).filter(User.id == user_id).first()

        user.username = request.get_json()['username']
        db_session.commit()

        return {"status":"success"}, 200
    except Exception as e:
        sentry_sdk.capture_exception(e,extras={"user_id":user.oidc_ident})
        abort(500,description="internal_server_error")
    finally:
        db_session.close()

@users_api.route("/me/hackatime-projects")
def get_all_hackatime_projects():
    db_session = utils.db.SessionLocal()
    try:
        user_id = session.get("user_id")
        user = db_session.query(User).filter(User.id == user_id).first()

        encrypted_hackatime_token = user.hackatime_token
        hackatime_token = utils.auth.decrypt_token(encrypted_hackatime_token,user.oidc_ident,encryption_key)

        hackatime_auth_headers = {"Authorization": "Bearer "+hackatime_token}

        projects_data = requests.get("https://hackatime.hackclub.com/api/v1/authenticated/projects", headers=hackatime_auth_headers)
        projects = projects_data.json()['projects']

        returned_data = []
        for project in projects:
            project_name = project['name']
            project_seconds = project['total_seconds']

            returned_data.append({
                "name": project_name,
                "time": project_seconds
            })
        return returned_data

    except Exception as e:
        sentry_sdk.capture_exception(e,extras={"user_id":user.oidc_ident})
        abort(500,description="internal_server_error")
    finally:
        db_session.close()
