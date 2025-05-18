#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from iptv_login_automation import IPTVLoginAutomation

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

SENDPULSE_API_URL = os.getenv('SENDPULSE_API_URL', 'https://api.sendpulse.com')
SENDPULSE_CLIENT_ID = os.getenv('SENDPULSE_CLIENT_ID')
SENDPULSE_CLIENT_SECRET = os.getenv('SENDPULSE_CLIENT_SECRET')
SENDPULSE_BOT_ID = os.getenv('SENDPULSE_BOT_ID')

# Inicializa a aplicação Flask
app = Flask(__name__)

class SendPulseAPI:
    def __init__(self):
        self.api_url = SENDPULSE_API_URL
        self.client_id = SENDPULSE_CLIENT_ID
        self.client_secret = SENDPULSE_CLIENT_SECRET
        self.bot_id = SENDPULSE_BOT_ID
        self.access_token = None

        if not self.client_id or not self.client_secret or not self.bot_id:
            logger.error("Credenciais do SendPulse não configuradas.")
            raise ValueError("Credenciais do SendPulse não configuradas.")

    def get_access_token(self):
        try:
            response = requests.post(
                f"{self.api_url}/oauth/access_token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                return self.access_token
            else:
                logger.error(f"Erro ao obter token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Erro ao obter token: {str(e)}")
            return None

    def send_whatsapp_message(self, phone, message):
        if not self.access_token:
            self.get_access_token()
        if not self.access_token:
            logger.error("Token de acesso ausente.")
            return False

        try:
            phone = ''.join(filter(str.isdigit, phone))
            if not phone.startswith('55'):
                phone = f"55{phone}"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            url = f"{self.api_url}/whatsapp/{self.bot_id}/sendMessage"
            payload = {
                "phone": phone,
                "message": {
                    "type": "text",
                    "text": message
                }
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code in [200, 201]:
                logger.info(f"Mensagem enviada com sucesso para {phone}")
                return True
            else:
                logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            return False

def format_credentials_message(user_data):
    return (
        "🎉 *Seu teste de IPTV foi criado com sucesso!* 🎉\n\n"
        "Aqui estão suas credenciais de acesso:\n\n"
        f"📱 *Usuário:* `{user_data['username']}`\n"
        f"🔑 *Senha:* `{user_data['password']}`\n"
        f"⏱️ *Expiração:* {user_data['expiry']}\n\n"
        "Para acessar, utilize qualquer aplicativo IPTV compatível com listas M3U.\n\n"
        "Agradecemos seu interesse em nosso serviço! Se gostar, entre em contato para assinar um plano completo."
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logger.info(f"Webhook recebido: {data}")

    phone = data.get('phone')
    text = data.get('text')

    if not phone or not text:
        logger.warning("Dados incompletos no webhook")
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    try:
        linhas = text.split('\n')
        usuario = senha = None
        for linha in linhas:
            if 'usuario:' in linha.lower():
                usuario = linha.split(':', 1)[1].strip()
            if 'senha:' in linha.lower():
                senha = linha.split(':', 1)[1].strip()

        if not usuario or not senha:
            logger.warning("Falha ao extrair usuário/senha")
            return jsonify({"status": "error", "message": "Formato inválido"}), 400

        # Geração simulada de dados do usuário
        user_data = {
            'username': usuario,
            'password': senha,
            'expiry': '24 horas'
        }

        credentials_message = format_credentials_message(user_data)

        sendpulse_api = SendPulseAPI()
        success = sendpulse_api.send_whatsapp_message(phone, credentials_message)

        if success:
            return jsonify({"status": "success", "message": "Credenciais enviadas"}), 200
        else:
            return jsonify({"status": "error", "message": "Falha ao enviar mensagem"}), 500

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return jsonify({"status": "error", "message": "Erro interno"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
