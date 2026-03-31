def encrypt_token(token, id, key):#i had to get claude (booo) to help with some of this, as i have no idea how encryption works. i have done my research outside of that, making sure what it told me to do makes sense
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import os
    import base64

    aesgcm = AESGCM(key) #load the key

    nonce = os.urandom(12) #generate a random 96 bit nonce

    ciphertext = aesgcm.encrypt(nonce,token.encode(),id.encode()) #actually encrypt ti
    return base64.urlsafe_b64encode(nonce + ciphertext).decode() #encode the nonce with it

def decrypt_token(encrypted_token, id, key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import base64

    data = base64.urlsafe_b64decode(encrypted_token.encode()) #read the encrypted token properly
    aesgcm = AESGCM(key) #load the key

    nonce, ciphertext = data[:12], data[12:] #split the nonce and ciphertext

    access_token = aesgcm.decrypt(nonce,ciphertext,id.encode()).decode() #decrypt the thing
    return access_token
def generate_session_token():
    import secrets
    return secrets.token_urlsafe(32)

