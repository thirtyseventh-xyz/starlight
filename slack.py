# utility functions for slack and stuff
from slack_bolt import App
from dotenv import load_dotenv
import os
load_dotenv()

token = os.environ.get("SLACK_BOT_TOKEN")
error_channel = os.environ.get("SLACK_ERROR_CHANNEL")

app = App(token=token)

def log_error(error:str):
    if os.environ.get("SLACK_ERROR_LOGGING") == "true":
        app.client.chat_postMessage(markdown_text=error,channel=error_channel)