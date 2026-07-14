from flask import Blueprint, session, request
from utils.models import User, Order, Project
import utils.db
import utils.auth
import sentry_sdk

shop_api = Blueprint("shop_api",__name__,static_url_path="/api/shop")

@shop_api.before_request
def auth_check():
    if not utils.auth.check_session(session):
        return {"status":"error","error":"unauthorized"}, 401

@shop_api.route("/order", methods=["POST"])
def order_item():
    db_session = utils.db.SessionLocal()
    try:
        user_id = session.get("user_id")
        user = db_session.query(User).filter(User.id == user_id).first()

        item_id:int = request.json()['shop_item_id']
        project_id:int = request.json()['associated_project_id']

        project = db_session.query(Project).filter(Project.id == project_id).first()

        order = Order(
            item_id=item_id,
            user=user,
            project=project
        )

        db_session.add(order)
        db_session.commit()

    except Exception as e:
        sentry_sdk.capture_exception(e,extras={"user_id":user.oidc_ident})
        return {"status":"error", "error":"internal_server_error"}, 500
    finally:
        db_session.close()
