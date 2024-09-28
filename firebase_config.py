import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    cred = credentials.Certificate(json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT')))
    firebase_admin.initialize_app(cred, {"storageBucket": "yourmove-ai.appspot.com"})
    return firestore.client()

db = initialize_firebase()