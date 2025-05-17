#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webhook para integração entre SendPulse e painel IPTV.
Este script recebe solicitações do SendPulse via webhook, extrai os 4 últimos dígitos
do número de telefone do cliente, cria um usuário de teste no painel IPTV e
envia as credenciais de volta para o cliente via WhatsApp.
"""

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

# Configurações do SendPulse
SENDPULSE_API_URL = os.getenv('SENDPULSE_API_URL', 'https://api.sendpulse.com')
SENDPULSE_CLIENT_ID = os.getenv('SENDPULSE_CLIENT_ID')
SENDPULSE_CLIENT_SECRET = os.getenv('SENDPULSE_CLIENT_SECRET')
SENDPULSE_BOT_ID = os.getenv('SENDPULSE_BOT_ID')

# Inicializa a aplicação Flask
app = Flask(__name__)

class SendPulseAPI:
    """Classe para interação com a API do SendPulse."""
    
    def __init__(self):
        """Inicializa a classe com configurações básicas."""
        self.api_url = SENDPULSE_API_URL
        self.client_id = SENDPULSE_CLIENT_ID
        self.client_secret = SENDPULSE_CLIENT_SECRET
        self.bot_id = SENDPULSE_BOT_ID
        self.access_token = None
        self.token_expires = 0
        
        if not self.client_id or not self.client_secret or not self.bot_id:
            logger.error("Credenciais do SendPulse não configuradas. Configure as variáveis de ambiente.")
            raise ValueError("Credenciais do SendPulse não configuradas")
    
    def get_access_token(self):
        """Obtém um token de acesso para a API do SendPulse."""
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
                logger.error(f"Erro ao obter token de acesso: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter token de acesso: {str(e)}")
            return None
    
    def send_whatsapp_message(self, phone, message):
        """Envia uma mensagem via WhatsApp usando a API do SendPulse."""
        if not self.access_token:
            self.get_access_token()
            
        if not self.access_token:
            logger.error("Não foi possível obter token de acesso para enviar mensagem")
            return False
        
        try:
            # Formatar o número de telefone (remover caracteres não numéricos)
            phone = ''.join(filter(str.isdigit, phone))
            
            # Garantir que o número tenha o formato internacional
            if not phone.startswith('55'):
                phone = f"55{phone}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'bot_id': self.bot_id,
                'phone': phone,
                'message': message
            }
            
            response = requests.post(
                f"{self.api_url}/whatsapp/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Mensagem enviada com sucesso para {phone}")
                return True
            else:
                logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            return False


def extract_phone_last_digits(phone_number):
    """Extrai os 4 últimos dígitos do número de telefone."""
    # Remover caracteres não numéricos
    clean_number = ''.join(filter(str.isdigit, phone_number))
    
    # Obter os 4 últimos dígitos
    last_digits = clean_number[-4:] if len(clean_number) >= 4 else clean_number
    
    return last_digits


def format_credentials_message(user_data):
    """Formata a mensagem com as credenciais para envio via WhatsApp."""
    message = (
        "🎉 *Seu teste de IPTV foi criado com sucesso!* 🎉\n\n"
        "Aqui estão suas credenciais de acesso:\n\n"
        f"📱 *Usuário:* `{user_data['username']}`\n"
        f"🔑 *Senha:* `{user_data['password']}`\n"
        f"⏱️ *Expiração:* {user_data['expiry']}\n\n"
        "Para acessar, utilize qualquer aplicativo IPTV compatível com listas M3U.\n\n"
        "Agradecemos seu interesse em nosso serviço! Se gostar, entre em contato para assinar um plano completo."
    )
    return message


@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint principal do webhook para receber solicitações do SendPulse."""
    try:
        data = request.json
        logger.info(f"Webhook recebido: {data}")
        
        # Verificar se é uma mensagem do WhatsApp
        if 'message' not in data or 'phone' not in data:
            logger.warning("Dados incompletos no webhook")
            return jsonify({"status": "error", "message": "Dados incompletos"}), 400
        
        message_text = data['message'].strip().upper()
        phone_number = data['phone']
        
        # Verificar se a mensagem é uma solicitação de teste
        if message_text == "TESTE":
            logger.info(f"Solicitação de teste recebida do número {phone_number}")
            
            # Extrair os 4 últimos dígitos do número de telefone
            last_digits = extract_phone_last_digits(phone_number)
            logger.info(f"Últimos 4 dígitos extraídos: {last_digits}")
            
            # Inicializar a automação do IPTV
            iptv_automation = IPTVLoginAutomation()
            
            # Fazer login e obter o token JWT
            token = iptv_automation.login_and_get_token()
            
            if not token:
                logger.error("Falha ao obter token JWT")
                return jsonify({"status": "error", "message": "Falha ao autenticar no painel IPTV"}), 500
            
            # Criar usuário de teste
            user_data = iptv_automation.create_test_user(last_digits)
            
            if not user_data:
                logger.error("Falha ao criar usuário de teste")
                return jsonify({"status": "error", "message": "Falha ao criar usuário de teste"}), 500
            
            # Formatar mensagem com as credenciais
            credentials_message = format_credentials_message(user_data)
            
            # Enviar credenciais via WhatsApp
            sendpulse_api = SendPulseAPI()
            message_sent = sendpulse_api.send_whatsapp_message(phone_number, credentials_message)
            
            if message_sent:
                logger.info(f"Credenciais enviadas com sucesso para {phone_number}")
                return jsonify({"status": "success", "message": "Credenciais enviadas com sucesso"}), 200
            else:
                logger.error(f"Falha ao enviar credenciais para {phone_number}")
                return jsonify({"status": "error", "message": "Falha ao enviar credenciais"}), 500
        else:
            logger.info(f"Mensagem não reconhecida como solicitação de teste: {message_text}")
            return jsonify({"status": "ignored", "message": "Mensagem não reconhecida como solicitação de teste"}), 200
            
    except Exception as e:
        logger.error(f"Erro no processamento do webhook: {str(e)}")
        return jsonify({"status": "error", "message": f"Erro interno: {str(e)}"}), 500


if __name__ == "__main__":
    # Configurações para execução local
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Iniciar o servidor Flask
    app.run(host='0.0.0.0', port=port, debug=debug)
