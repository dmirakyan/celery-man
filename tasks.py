import os
import requests
import supabase
from celery import Celery
from celery.utils.log import get_task_logger
from supabase import create_client, Client
from uplink import Consumer, post, Body, json, Path
from uplink.auth import BearerToken



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
            "mail_name": "yourmove-photos-complete",
            "subject": "Your AI photos are ready!",
            "from": "dmitri@yourmove.ai",
            "to": "support@yourmove.ai",
            "replacements": {
                "email": email, 
            }
        }
    )
    return {}

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

@app.task(name='push_outputs')
def push_outputs(email,tune_id):
    # this function takes a specified email and tune id. and then pushes it to supabase storage
    # supabase storage should already exist
    # but I can specify any id 
    logger.info(f'Pushing images for {email}, tune id = {tune_id}')
    # return x + y
    bucket_result = email
    prompts_json = requests.get(f'https://api.astria.ai/tunes/{tune_id}/prompts', headers=astria_headers).json()
    astria_images = []

    for item in prompts_json[0:1]:
        if 'images' in item:
            astria_images.extend(item['images']) 
    for link in astria_images:
        filename = link[-14:]
        response = requests.get(link)
        if response.status_code == 200:
            # Upload the file content directly to Supabase Storage
            upload_response = supabase.storage.from_(bucket_result).upload(filename, response.content)
            if upload_response.status_code in [200, 201]:
                print(f"Uploaded {filename} to Supabase bucket '{bucket_result}'")
            else:
                print(f"Failed to upload {filename} to Supabase: {upload_response.status_code}")
    
    send_completion_email(email)
