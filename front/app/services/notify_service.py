from dotenv import load_dotenv
import os

load_dotenv()

WEBHOOK = f"{os.getenv('WEBHOOK')}"

import requests
webhook_url = f"{os.getenv('WEBHOOK')}"
message = {"title": "EventTrace","text": "Success WebHook Teams"}
requests.post(webhook_url, json=message)
