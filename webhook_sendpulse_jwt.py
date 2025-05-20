#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import os
import json
import logging
import requests
from datetime import datetime
from iptv_login_automation import IPTVLoginAutomation
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook_sendpulse_jwt.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações da integração
IPTV_API_URL = os.getenv("IPTV_API_URL", "https://mcapi.knewcms.com:2087/lines/test")
IPTV_PANEL_URL = os.getenv("IPTV_PANEL_URL", "https://mcapi.knewcms.com:2087")
IPTV_USERNAME = os.getenv("IPTV_USERNAME", "")
IPTV_PASSWORD = os.getenv("IPTV_PASSWORD", "")
SENDPULSE_API_URL = os.getenv("SENDPULSE_API_URL", "https://api.sendpulse.com")
SENDPULSE_CLIENT_ID = os.getenv("SENDPULSE_CLIENT_ID", "")
SENDPULSE_CLIENT_SECRET = os.getenv("SENDPULSE_CLIENT_SECRET", "")
TOKEN_FILE = os.getenv("TOKEN_FILE", "iptv_token.json")

# Inicializar a automação de login
import iptv_automation
class IPTVLoginAutomation:
    def __init__(self, username, password, painel_url, token_file):
        self.username = username
        self.password = password
        self.painel_url = painel_url
        self.token_file = token_file

# Variável global para armazenar o token do SendPulse
sendpulse_token = None


def obter_token_sendpulse():
    global sendpulse_token
    try:
        url = f"{SENDPULSE_API_URL}/oauth/access_token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": SENDPULSE_CLIENT_ID,
            "client_secret": SENDPULSE_CLIENT_SECRET
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        sendpulse_token = data.get("access_token")
        logger.info("Token do SendPulse obtido com sucesso")
        return sendpulse_token
    except Exception as e:
        logger.error(f"Erro ao obter token do SendPulse: {str(e)}")
        return None


def criar_usuario_teste_iptv(ultimos_digitos):
    try:
        token = iptv_automation.get_token()
        if not token:
            logger.error("Token JWT não disponível para criar usuário")
            return None

        payload = {
            "notes": ultimos_digitos,
            "package_p2p": "64399dca5ea59e8a1de2b083",
            "krator_package": "1",
            "package_iptv": 95,
            "testDuration": 4
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(IPTV_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Usuário IPTV criado: {data.get('username')}")
        return {
            "username": data.get("username"),
            "password": data.get("password"),
            "exp_date": data.get("exp_date")
        }
    except Exception as e:
        logger.error(f"Erro ao criar usuário IPTV: {str(e)}")
        return None


def enviar_credenciais_whatsapp(numero_telefone, username, password, exp_date):
    global sendpulse_token
    if not sendpulse_token:
        sendpulse_token = obter_token_sendpulse()

    if not sendpulse_token:
        logger.error("Token do SendPulse não disponível")
        return False

    try:
        url = f"{SENDPULSE_API_URL}/whatsapp/contacts/sendByPhone"
        headers = {
            "Authorization": f"Bearer {sendpulse_token}",
            "Content-Type": "application/json"
        }
        mensagem = (
            f"*Suas credenciais de teste IPTV*\n\n"
            f"Usuário: *{username}*\n"
            f"Senha: *{password}*\n"
            f"Expira em: {exp_date}\n\n"
            f"Baixe o aplicativo WTV PLAYER e aproveite!"
        )
        payload = {
            "phone": numero_telefone,
            "message": mensagem
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Credenciais enviadas para {numero_telefone}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar credenciais via WhatsApp: {str(e)}")
        return False

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "mensagem": "API IPTV funcionando"}), 200
    
@app.route('/webhook/iptv-teste', methods=['POST'])
def webhook_iptv_teste():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "erro", "mensagem": "Dados não fornecidos"}), 400
        numero_telefone = data.get('phone')
        if not numero_telefone:
            return jsonify({"status": "erro", "mensagem": "Número de telefone não fornecido"}), 400

        ultimos_digitos = numero_telefone[-4:]
        user_info = criar_usuario_teste_iptv(ultimos_digitos)

        if not user_info:
            return jsonify({"status": "erro", "mensagem": "Erro ao criar usuário IPTV"}), 500

        envio_sucesso = enviar_credenciais_whatsapp(
            numero_telefone,
            user_info["username"],
            user_info["password"],
            user_info["exp_date"]
        )

        if envio_sucesso:
            return jsonify({"status": "sucesso", "mensagem": "Credenciais enviadas com sucesso"}), 200
        else:
            return jsonify({"status": "erro", "mensagem": "Falha ao enviar credenciais via WhatsApp"}), 500

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return jsonify({"status": "erro", "mensagem": f"Erro interno: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
