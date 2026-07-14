import sentry_sdk
from flask import Blueprint, session, jsonify, abort
from werkzeug.exceptions import HTTPException
import utils.db
from utils.models import User
import utils.auth

admin_api = Blueprint("admin_api",__name__,url_prefix="/api/admin")

@admin_api.errorhandler(HTTPException)
def json_error_reporting(e):
    return jsonify(error=e.name,context=e.description), e.code

@admin_api.before_request
def auth_check():
    if not utils.auth.check_admin(session):
        abort(401,description="invalid_session")

@admin_api.route("/user/info/<user_id>")
def get_user_info(user_id):
    db_session = utils.db.SessionLocal()
    try:
        if user_id.isdigit():
            user_id = int(user_id)
            user = db_session.query(User).filter(User.id == user_id).first()
        else:
            user = db_session.query(User).filter(User.oidc_ident == user_id).first()
        if user:
            return {
                "id": user.id,
                "oidc_ident": user.oidc_ident,
                "slack_id": user.slack_id,
                "username": user.username,
                "join_date": str(user.join_date),
                "last_session_clear_date": str(user.last_session_clear_date),
                "admin": user.admin
            }
    except Exception as e:
        sentry_sdk.capture_exception(e)
        abort(500,description="internal_server_error")
    finally:
        db_session.close()