import firebase_admin
from firebase_admin import credentials, firestore
import os, json

if not firebase_admin._apps:
    if "FIREBASE_KEY" in os.environ:
        cred_dict = json.loads(os.environ["FIREBASE_KEY"])
        cred = credentials.Certificate(cred_dict)
    else:
        raise Exception("FIREBASE_KEY not set in environment variables")

    firebase_admin.initialize_app(cred)

db = firestore.client()