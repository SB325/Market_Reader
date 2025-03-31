import json
import pdb
import os, sys
from pushover import Client
from dotenv import load_dotenv
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__)))

load_dotenv(os.path.join(os.path.dirname(__file__)) + "/notify_creds.env")   

key = os.getenv("PUSHOVER_KEY")
token = os.getenv("PUSHOVER_TOKEN")

class push_notify():
    def __init__(self, key: str = key, token: str = token):
        self.client = Client(user_key=key, api_token=token)

    def send(self, title: str = "", 
                    message: str = "",
                    priority: int = None,
                    expire: int = None,
                    retry: int = None,
                    url: str = None,
                    url_title: str = None,
                    html: int = 0,
                    timestamp: int = None,
                ):
        if priority:
            assert expire, "If priority is set, expire must be set as well."
            assert retry, "If priority is set, retry must be set as well."
            assert expire>retry, "Retry must not be larger than expire."
            assert retry>=30, "Retry must be greater than 30 seconds"
            assert len(title)<=250, "Title must be less than 250 characters."
            assert len(message)<=1024, "Message must be less than 1024 characters."

        response = self.client.send_message(message=message, 
                                title=title,
                                priority=priority,  # Lowest(-2), Low(-1), Normal(0)-default, High(1), Emergency(2)                                                                                                                                             
                                expire=expire,      # in seconds
                                retry=retry,        # retry period in seconds  
                                url=url,           # Clickable link that opens in browser
                                url_title=url_title,     # 
                                html=html,          # If message contains html, set this flag to true and tags will be implemented
                                timestamp=timestamp # Unix timestamp of message, regardless of time displayed on device
                            )

        return json.dumps(response.__dict__)

if __name__ == "__main__":
    pn = push_notify()
    response = pn.send(title="TSLA", 
                       priority=2, 
                       expire=60, 
                       retry=30, 
                       message="TSLA lost money today!")
    print(response)