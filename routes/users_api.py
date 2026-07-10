import os
import sentry_sdk
from flask import Blueprint, session, request
import utils.db
from utils.models import User
import utils.auth

users_api = Blueprint("users_api", __name__, url_prefix="/api/user")
encryption_key = os.environ.get("ENCRYPTION_KEY")

@users_api.before_request
def auth_check():
    if not utils.auth.check_session(session):
        return {"status":"error","error":"unauthorized"}, 401

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
        sentry_sdk.capture_exception(e)
        return {"status": "error", "error": "internal_server_error"}, 500
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
        sentry_sdk.capture_exception(e)
        return {"status":"error", "error":"internal_server_error"}, 500
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


    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {"status":"error", "error":"internal_server_error"}, 500
    finally:
        db_session.close()