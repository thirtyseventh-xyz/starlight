import os
import sentry_sdk
from flask import Flask, request, redirect, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from slack_sdk import WebClient
from sentry_sdk.integrations.flask import FlaskIntegration

#This code is spaghetti and needs to be fixed lol TODO: split stuff into separate files using blueprints and make it more organized
# oh also TODO: get url safe checks on all the places users can input stuff (rn just the oauth callback)

load_dotenv()

slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

sentry_sdk.init(os.environ.get("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)
limiter = Limiter(get_remote_address,app=app, default_limits=["20000 per day", "5000 per hour"] )

main_url = os.environ.get("PROD_MAIN_URL")

@app.route("/")
def get_out():
    return redirect(main_url)

@app.errorhandler(404)
def fancy_404(e):
    return redirect(main_url+"/error?code=404&message=page+not+found%2E+maybe+you+are+looking+for+this+page+on+the+main+sparkle+domain+and+not+the+api%3F")

from routes.oauth import oauth_routes
from routes.misc import misc_routes

app.register_blueprint(oauth_routes)
app.register_blueprint(misc_routes)