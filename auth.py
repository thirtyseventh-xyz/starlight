from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib
import os
import base64
import secrets

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
def generate_session_token():
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()

