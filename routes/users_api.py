from flask import Blueprint, session, request
from utils.db import SessionLocal
from utils.models import User

users_api = Blueprint("users_api", __name__, url_prefix="/api/user")

@users_api.before_request
def auth_check():
    if not session.get("user_id"):
        return {"error":"unauthorized"}, 401

@users_api.route("/me")
def get_user_info():
    user_id = session.get("user_id")
    db_session = SessionLocal()

    user = db_session.query(User).filter(User.id == user_id).all()[0]

    return {
        "id": user.id,
        "slack_id": user.slack_id,
        "username": user.username
    }, 200

@users_api.route("/me/update-username", methods=['PUT'])
def update_username():
    user_id = session.get("user_id")
    db_session = SessionLocal()

    user = db_session.query(User).filter(User.id == user_id).all()[0]

    user.username = request.get_json()['username']
    db_session.commit()
    db_session.close()

    return {"status":"success"}, 200
