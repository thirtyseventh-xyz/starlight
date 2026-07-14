from flask import Blueprint, session
import utils.auth

shop_api = Blueprint("shop_api",__name__,static_url_path="/api/shop")

@shop_api.before_request
def auth_check():
    if not utils.auth.check_session(session):
        return {"status":"error","error":"unauthorized"}, 401

