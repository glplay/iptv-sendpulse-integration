import os
import requests
import logging
from datetime import datetime, timedelta

class SendPulseAPI:
    def __init__(self, client_id, client_secret, token_url="https://api.sendpulse.com/oauth/access_token"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None
        self.token_expiration = datetime.utcnow()

    def autenticar(self):
        if self.access_token and datetime.utcnow() < self.token_expiration:
            return self.access_token

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(self.token_url, json=payload)
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self.token_expiration = datetime.utcnow() + timedelta(seconds=expires_in)
            logging.info("Token de acesso obtido com sucesso.")
            return self.access_token
        else:
            logging.error(f"Falha na autenticação SendPulse: {response.text}")
            raise Exception("Erro ao autenticar com SendPulse")

    def enviar_mensagem_whatsapp(self, telefone_destino, mensagem):
        try:
            token = self.autenticar()

            url = "https://api.sendpulse.com/whatsapp/contacts/send"

            payload = {
                "phone": telefone_destino,
                "message": {
                    "type": "text",
                    "text": mensagem
                }
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                logging.info(f"Mensagem WhatsApp enviada com sucesso para {telefone_destino}")
            else:
                logging.error(f"Erro ao enviar mensagem WhatsApp: {response.status_code} - {response.text}")

            return response.status_code, response.text

        except Exception as e:
            logging.error(f"Exceção ao enviar mensagem WhatsApp: {e}")
            return 500, str(e)
