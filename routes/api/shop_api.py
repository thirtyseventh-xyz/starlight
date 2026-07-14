from flask import Blueprint, session, request, jsonify, abort
from werkzeug.exceptions import HTTPException
from utils.models import User, Order, Project, ShopItem
import utils.db
import utils.auth
import sentry_sdk

shop_api = Blueprint("shop_api",__name__,url_prefix="/api/shop")

@shop_api.errorhandler(HTTPException)
def json_error_reporting(e):
    return jsonify(error=e.name,context=e.description), e.code

@shop_api.before_request
def auth_check():
    if not utils.auth.check_session(session):
        abort(401,description="invalid_session")


@shop_api.route("/order", methods=["POST"])
def order_item():
    db_session = utils.db.SessionLocal()
    try:
        user_id = session.get("user_id")
        user = db_session.query(User).filter(User.id == user_id).first()

        item_id:int = request.json()['shop_item_id']
        project_id:int = request.json()['associated_project_id']

        project = db_session.query(Project).filter(Project.id == project_id).first()

        if not project:
            abort(404,description="nonexistent_project")
        if not project in user.associated_projects:
            abort(403,description="project_not_associated_with_user")
        if project.prize_redeemed:
            abort(422,description="prize_already_redeemed")

        order = Order(
            item_id=item_id,
            user=user,
            project=project
        )

        db_session.add(order)
        db_session.commit()

    except Exception as e:
        sentry_sdk.capture_exception(e,extras={"user_id":user.oidc_ident})
        abort(500,description="internal_server_error")
    finally:
        db_session.close()

@shop_api.route("/item/all")
def get_all_shop_items():
    db_session = utils.db.SessionLocal()
    try:
        items = db_session.query(ShopItem).all()

        items_data:list = []
        for item in items:
            item_data = {
                "name":item.name,
                "description":item.description,
                "image_location":"/static/shop_images/"+item.image_location,
                "id":item.id
            }
            items_data.append(item_data)
        return items_data
    except Exception as e:
        sentry_sdk.capture_exception(e)
        abort(500, description="internal_server_error")
    finally:
        db_session.close()

@shop_api.route("/item/<item_id>")
def get_shop_item(item_id):
    db_session = utils.db.SessionLocal()
    try:
        item = db_session.query(ShopItem).filter(ShopItem.id == item_id).first()

        return {
            "name":item.name,
            "description":item.description,
            "image_location":"/static/shop_images/"+item.image_location,
            "id":item.id
        }
    except Exception as e:
        sentry_sdk.capture_exception(e)
        abort(500, description="internal_server_error")
    finally:
        db_session.close()