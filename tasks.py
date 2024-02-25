import os
import requests
import supabase
from celery import Celery
from celery.utils.log import get_task_logger

app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"))
logger = get_task_logger(__name__)

astria_key = 'sd_ua9DSqDPqkN3C5KEYstmhNM9wTHwQE'
astria_headers = {'Authorization': f'Bearer {astria_key}'}


s_url: str = 'https://vptyvojtavfnwxsxrgkg.supabase.co'
s_key: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwdHl2b2p0YXZmbnd4c3hyZ2tnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY3ODY0OTQ1MCwiZXhwIjoxOTk0MjI1NDUwfQ.98olPSl8POqZBlBZs86jfrLIGRNQFNlSXfvtPRa_lVY'
supabase: Client = create_client(s_url, s_key)
supabase_headers = {"apiKey": s_key,"Authorization": "Bearer " + s_key,"Content-Type": "application/json"}

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
    for item in prompts_json:
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
