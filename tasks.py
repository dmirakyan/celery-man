import os
import socket
import requests
import supabase
from celery import Celery
from celery.utils.log import get_task_logger
from supabase import create_client, Client
from uplink import Consumer, post, Body, json, Path
from uplink.auth import BearerToken
from firebase_config import db
from firebase_admin import firestore


# def get_redis_host():
#     redis_host = os.environ.get('REDIS_HOST', 'host.docker.internal')
#     if redis_host == 'host.docker.internal':
#         try:
#             # Attempt to resolve host.docker.internal
#             redis_host = socket.gethostbyname('host.docker.internal')
#         except socket.gaierror:
#             # If it fails, fallback to localhost
#             redis_host = 'localhost'
#     return redis_host

# REDIS_HOST = get_redis_host()
# redis_url = f'redis://{REDIS_HOST}:6379/0'

# celery_app = Celery('celery-man', broker=redis_url, backend=redis_url)
# app = Celery('celery-man', broker=redis_url)

app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"))
logger = get_task_logger(__name__)

astria_key = 'sd_ua9DSqDPqkN3C5KEYstmhNM9wTHwQE'
astria_headers = {'Authorization': f'Bearer {astria_key}'}

mailcoach_api_key = "HBfh7qbzbJEqpLXoWIBwWVCwY0QIbFoCXy6jlWgO3b19228e"
mailcoach_base_url = "https://yourmove.mailcoach.app"

s_url: str = 'https://vptyvojtavfnwxsxrgkg.supabase.co'
s_key: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwdHl2b2p0YXZmbnd4c3hyZ2tnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY3ODY0OTQ1MCwiZXhwIjoxOTk0MjI1NDUwfQ.98olPSl8POqZBlBZs86jfrLIGRNQFNlSXfvtPRa_lVY'

supabase: Client = create_client(s_url, s_key)
supabase_headers = {"apiKey": s_key,"Authorization": "Bearer " + s_key,"Content-Type": "application/json"}

class MailCoachClient(Consumer):
    @json
    @post("/api/transactional-mails/send")
    def send_email(self, body: Body(type=dict)):
        pass

    @json
    @post("/api/email-lists/{list_uuid}/subscribers")
    def subscribe_to_list(self, list_uuid: Path, body: Body(type=dict)):
        pass

def get_mailcoach_client() -> MailCoachClient:
    bearer_auth = BearerToken(mailcoach_api_key)
    return MailCoachClient(mailcoach_base_url, auth=bearer_auth)

def send_completion_email(email):
    mailcoach_client = get_mailcoach_client()
    mailcoach_client.send_email(
        body= {
            "mail_name": "yourmove-photos-complete-v2",
            "subject": "Your AI photos are ready!",
            "from": "dmitri@yourmove.ai",
            "cc": "support@yourmove.ai",
            "to": email,
            "replacements": {
                "email": email, 
            }
        }
    )
    return {}

def send_completion_email_external(email):
    mailcoach_client = get_mailcoach_client()
    mailcoach_client.send_email(
        body= {
            "mail_name": "yourmove-photo-submission-external ",
            "subject": "Your AI photos are ready!",
            "from": "dmitri@yourmove.ai",
            "cc": "support@yourmove.ai",
            "to": email,
        }
    )

# This was an insane function to create lol. Why not just call both. Weird level of abstraction.
# def send_completion_emails(email):
#     send_completion_email(email)
#     send_completion_email_external(email)

def send_error_email(email):
    mailcoach_client = get_mailcoach_client()
    mailcoach_client.send_email(
        body= {
            "mail_name": "yourmove-photo-submission",
            "subject": "There was an error :/",
            "from": "support@yourmove.ai",
            "to": "support@yourmove.ai",
            "replacements": {
                "topic": "This is a test" + email, 
                "email": email,
                "details": "There was an error" + email,
            }
        }
    )
    return {}


@app.task(name='celery_add')
def celery_add(x, y):
    logger.info(f'Adding {x} + {y}')
    return x + y

def update_output_urls_to_db(tune_id, email, output_urls):
    ai_photos_ref = db.collection("aiPhotosRequests").where("email", "==", email).where("tuneId", "==", tune_id).limit(1)
    docs = ai_photos_ref.get()
    
    if not docs:
        print(f"No matching document found for email: {email} and tuneId: {tune_id}")
        return
    
    doc = docs[0]
    doc_ref = doc.reference
    
    doc_ref.update({
        "status": "processed",
        "outputUrls": output_urls,
        "updatedAt": firestore.SERVER_TIMESTAMP
    })

@app.task(name='push_outputs_v2')
def push_outputs_v2(email,tune_id):
    # this function takes a specified email and tune id. and then pushes it to supabase storage
    # supabase storage should already exist
    # but I can specify any id 
    logger.info(f'Pushing images for {email}, tune id = {tune_id}')
    # return x + y
    bucket_result = email
    prompts_json = requests.get(f'https://api.astria.ai/tunes/{tune_id}/prompts', headers=astria_headers).json()
    astria_images = []
    output_urls = []  # To store the URLs of uploaded images

    folder_name = f"tune_{tune_id}"

    for item in prompts_json:
        if 'images' in item:
            astria_images.extend(item['images']) 

    for link in astria_images:
        filename = link[-14:]
        response = requests.get(link)
        if response.status_code == 200:
            file_path = f"{folder_name}/{filename}"
            # Upload the file content directly to Supabase Storage
            upload_response = supabase.storage.from_(bucket_result).upload(file_path, response.content)
            if upload_response.status_code in [200, 201]:
                logger.info(f"Uploaded {filename} to Supabase bucket '{bucket_result}'")
                # Construct and store the public URL for the uploaded image
                public_url = f"{s_url}/storage/v1/object/public/{bucket_result}/{file_path}"
                output_urls.append(public_url)
            else:
                logger.error(f"Failed to upload {filename} to Supabase: {upload_response.status_code}")
    
    update_output_urls_to_db(tune_id, email, output_urls)
    send_completion_email(email)