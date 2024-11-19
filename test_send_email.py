from uplink import Consumer, post, Body, json
from uplink.auth import BearerToken

# Define the MailCoachClient class
class MailCoachClient(Consumer):
    @json
    @post("/api/transactional-mails/send")
    def send_email(self, body: Body(type=dict)):
        pass

# Function to get a MailCoachClient instance
def get_mailcoach_client() -> MailCoachClient:
    mailcoach_api_key = "HBfh7qbzbJEqpLXoWIBwWVCwY0QIbFoCXy6jlWgO3b19228e"
    mailcoach_base_url = "https://yourmove.mailcoach.app"
    bearer_auth = BearerToken(mailcoach_api_key)
    return MailCoachClient(mailcoach_base_url, auth=bearer_auth)

# Function to send a completion email
def send_completion_email(email):
    mailcoach_client = get_mailcoach_client()
    mailcoach_client.send_email(
        body={
            "mail_name": "yourmove-photos-complete-v2",
            "subject": "Your AI photos are ready!",
            "from": "dmitri@yourmove.ai",
            "cc": "support@yourmove.ai",
            "to": email,
            "replacements": {
                "email": email,
                "link": f"https://web.yourmove.ai/ai-photo?is_retrieve=true&email_ref={email}",
            }
        }
    )
    print(f"Test email sent to {email}")

# Test function
def test_send_completion_email():
    test_email = "damirakyan@gmail.com"
    send_completion_email(test_email)

if __name__ == "__main__":
    test_send_completion_email() 