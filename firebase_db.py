import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Get Firebase key from environment variable
firebase_key = os.environ.get("FIREBASE_KEY")

if not firebase_key:
    raise Exception("FIREBASE_KEY not set in environment variables")

# Convert string → JSON
cred_dict = json.loads(firebase_key)

# Initialize Firebase
cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Firestore DB
db = firestore.client()