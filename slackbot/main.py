from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os

load_dotenv() #only necessary for dev, should be called from entrypoint TODO: actually load env from entrypoint rather than two places

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

#hey idiot (future me), remember to use register functions and import from other files. dont write 5000 lines of slackbot

socket_handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))

socket_handler.start()