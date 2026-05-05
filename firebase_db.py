import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

_db = None

def get_db():
    global _db
    if _db is not None:
        return _db

    # Read from env (Render)
    key_json = os.getenv("FIREBASE_KEY")
    if not key_json:
        raise Exception("FIREBASE_KEY not set")

    key_dict = json.loads(key_json)

    # Init only once
    if not firebase_admin._apps:
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db