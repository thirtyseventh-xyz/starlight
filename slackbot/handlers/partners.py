import slack_bolt
import utils.db
from utils.models import User, PartnerRequest
import slackbot.utils
import ast

def register(app:slack_bolt.app.App):
    print("registered partnering handlers")
    app.command("/sparkle-partner")(partner_specific)
    app.action({"action_id":"deny_personal_partner_request"})(partner_specific_reject_callback)

def partner_specific(ack,respond,command):
    db_session = utils.db.SessionLocal()
    try:
        slack_id = command['user_id']
        ack()

        user = db_session.query(User).filter(User.slack_id == slack_id).first()
        if not user:
            respond("you have not setup your account yet! please login to your account at sparkle.dino.icu/auth/login")
            return

        partner_id = command['text'][2:13]
        partner_data = slackbot.utils.get_user_info(partner_id)
        if not partner_data:
            respond("the mentioned user does not exist!")
            return

        request = PartnerRequest(
            creator=user,
            partner=partner_id
        )

        slackbot.utils.dm_user_blocks(
            partner_id,
            [{"type":"card","slack_icon":{"type":"icon","name":"comment"},"title":{"type":"mrkdwn","text":"@example wants to partner with you!","verbatim":False},"subtitle":{"type":"mrkdwn","text":"this is a partner request for <#C0AG9ASJ5U4|sparkle>","verbatim":False},"body":{"type":"mrkdwn","text":"@example wants to partner with (or teach or learn from) you as part of the <#C0AG9ASJ5U4|sparkle> ysws!","verbatim":False},"actions":[{"type":"button","style":"danger","text":{"type":"plain_text","text":"Decline","emoji":False},"action_id":"deny_personal_partner_request","value":str({"sender":user.slack_id,"partner":partner_id})},{"type":"button","style":"primary","text":{"type":"plain_text","text":"Accept","emoji":False},"action_id":"accept_personal_partner_request","value":str({"sender":user.slack_id,"partner":partner_id})}]}]
        )

        db_session.add(request)
        db_session.commit()

    finally:
        db_session.close()

def partner_specific_reject_callback(ack,body,respond):
    db_session = utils.db.SessionLocal()
    try:
        button_metadata = body['actions'][0]['value']
        button_metadata = ast.literal_eval(button_metadata)

        ack()

        if button_metadata['partner'] != body['user']['id']:
            respond("this request doesnt appear to be intended for you!")
            return

        req_creator = db_session.query(User).filter(User.slack_id == button_metadata['sender']).first()
        partner_req = db_session.query(PartnerRequest).filter(PartnerRequest.partner == button_metadata['partner']).filter(PartnerRequest.creator == req_creator).first()

        if partner_req.status != 0:

            respond(text="this request was already accepted or rejected! im not sure how youre reading this")
            return

        partner_req.status = 2
    finally:
        db_session.close()