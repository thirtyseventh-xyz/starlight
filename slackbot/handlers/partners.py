import slack_bolt
import utils.db
from utils.models import User, PartnerRequest
import slackbot.utils

def register(app:slack_bolt.app.App):
    print("registered partnering handlers")
    app.command("/sparkle-partner")(partner_specific)

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

        request = PartnerRequest(
            creator=user,
            partner=partner_id
        )

        db_session.add(request)
        db_session.commit()

    finally:
        db_session.close()