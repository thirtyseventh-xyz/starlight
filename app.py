import os

import flask
from flask import Flask
from flask import redirect
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/")
def get_out():
    return redirect(os.environ.get("PROD_MAIN_URL"))