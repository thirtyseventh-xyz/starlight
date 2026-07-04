from flask import Blueprint, send_from_directory

frontend_routes = Blueprint("frontend",__name__,static_folder="frontend/dist", static_url_path="")

@frontend_routes.route("/")
def index():
    return send_from_directory(frontend_routes.static_folder, "index.html")

@frontend_routes.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(frontend_routes.static_folder, path)