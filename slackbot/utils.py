import os
import slack_sdk
from slack_sdk.web import SlackResponse

client = slack_sdk.WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def get_user_info(slack_id:str) -> SlackResponse|None:
    user_info = client.users_profile_get(user=slack_id)
    if not user_info['ok']:
        return None

    return user_info

def dm_user_blocks(slack_id:str,blocks:list,metadata:dict|None=None):
    client.chat_postMessage(
        channel=slack_id,
        blocks=blocks,
        metadata=metadata
    )

def dm_user(slack_id:str,message:str):
    client.chat_postMessage(
        channel=slack_id,
        text=message
    )