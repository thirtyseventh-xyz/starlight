import os
import threading
import utils.gunicorn
from app import app

def webserver():
    utils.gunicorn.StandaloneApplication(
        app,
        {
            "bind":"0.0.0.0:8135",
            "workers": int(os.environ.get("GUNICORN_WORKERS"))
        }
    ).run()

webserver()
