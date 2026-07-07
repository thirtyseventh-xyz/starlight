import os
import sentry_sdk
from flask import Flask, request, redirect, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from dotenv import load_dotenv
from sentry_sdk.integrations.flask import FlaskIntegration

load_dotenv()

main_url = str(os.environ.get("PROD_MAIN_URL"))

sentry_sdk.init(os.environ.get("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)
limiter = Limiter(get_remote_address,app=app, default_limits=["20000 per day", "5000 per hour"] )

app.secret_key = os.environ.get("FLASK_SECRET_KEY")

app.config["SESSION_TYPE"] = "filesystem"
app.config['SESSION_COOKIE_DOMAIN'] = "."+main_url
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"

Session(app)


@app.errorhandler(404)
def fancy_404(e):
    return redirect(main_url+"/error?code=404&message=page+not+found%2E+maybe+you+are+looking+for+this+page+on+the+main+sparkle+domain+and+not+the+api%3F")

from routes.frontend import frontend_routes
from routes.oauth import oauth_routes
from routes.misc import misc_api

app.register_blueprint(frontend_routes)
app.register_blueprint(oauth_routes)
app.register_blueprint(misc_routes)