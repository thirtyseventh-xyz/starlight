from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os

load_dotenv() #only necessary for dev, should be called from entrypoint TODO: actually load env from entrypoint rather than two places

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

import slackbot.handlers.partners

slackbot.handlers.partners.register(app)

socket_handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
socket_handler.start()