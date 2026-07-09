from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
import utils.db
from utils.models import User


def encrypt_token(token, id, key):#i had to get claude (booo) to help with some of this, as i have no idea how encryption works. i have done my research outside of that, making sure what it told me to do makes sense
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)

    ciphertext = aesgcm.encrypt(nonce,token.encode(),id.encode())
    return base64.urlsafe_b64encode(nonce + ciphertext).decode() #encode the nonce with it

def decrypt_token(encrypted_token, id, key):
    data = base64.urlsafe_b64decode(encrypted_token.encode()) #read the encrypted token properly
    aesgcm = AESGCM(key)

    nonce, ciphertext = data[:12], data[12:]

    access_token = aesgcm.decrypt(nonce,ciphertext,id.encode()).decode()
    return access_token

def check_session(session) -> bool: # returns true if the session is valid
    if not session.get("user_id"):
        session.clear()
        return False

    db_session = utils.db.SessionLocal()

    user = db_session.query(User).where(User.id == session['user_id']).first()
    oldest_session_date = user.last_session_clear_date

    if oldest_session_date:
        session_date = session['created_at']

        if session_date >= oldest_session_date: #only pass the session if its newer than the last clear
            return True
    else:
        return True
    session.clear()
    return False