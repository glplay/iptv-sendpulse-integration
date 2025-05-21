# sendpulse_api.py

import requests
import logging

class SendPulseAPI:
    def __init__(self, client_id, client_secret, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None

    def authenticate(self):
        """Obtém o token de acesso da API do SendPulse"""
        try:
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            response = requests.post(self.token_url, data=payload)
            response.raise_for_status()
            self.access_token = response.json()['access_token']
            logging.info("Token de acesso obtido com sucesso.")
            return self.access_token
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao obter token de acesso: {e}")
            return None
