import os
import requests

class SendPulseAPI:
    def __init__(self):
        self.client_id = os.getenv('SENDPULSE_CLIENT_ID')
        self.client_secret = os.getenv('SENDPULSE_CLIENT_SECRET')
        self.api_url = os.getenv('SENDPULSE_API_URL', 'https://api.sendpulse.com')
        self.token = None

    def authenticate(self):
        url = f"{self.api_url}/oauth/access_token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        self.token = response.json()["access_token"]

    def send_message(self, chat_id, text):
        if self.token is None:
            self.authenticate()

        url = f"{self.api_url}/telegram/bots/{os.getenv('SENDPULSE_BOT_ID')}/sendMessage"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
