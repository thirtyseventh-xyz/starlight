from flask import Blueprint, send_from_directory,render_template
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
frontend_dist = os.path.join(project_root, "frontend", "dist")
frontend_assets = os.path.join(frontend_dist, "assets")
frontend_routes = Blueprint("frontend",__name__,template_folder=frontend_dist,static_folder=frontend_assets,static_url_path="/assets")

@frontend_routes.route("/")
def index():
    return render_template("index.html")

@frontend_routes.route("/<path:path>")
def static_proxy(path):
    if path != "" and os.path.exists(os.path.join(frontend_dist, path)): #if its an asset file, grab it from assets
        return send_from_directory(frontend_dist, path)
    return render_template("index.html")