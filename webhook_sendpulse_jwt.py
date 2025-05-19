#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import os
import json
import logging
import requests
from datetime import datetime
from iptv_login_automation import IPTVLoginAutomation

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
IPTV_API_URL = os.environ.get("IPTV_API_URL", "https://mcapi.knewcms.com:2087/lines/test")
IPTV_PANEL_URL = os.environ.get("IPTV_PANEL_URL", "https://mcapi.knewcms.com:2087")
IPTV_USERNAME = os.environ.get("IPTV_USERNAME", "")
IPTV_PASSWORD = os.environ.get("IPTV_PASSWORD", "")
SENDPULSE_API_URL = os.environ.get("SENDPULSE_API_URL", "https://api.sendpulse.com")
SENDPULSE_CLIENT_ID = os.environ.get("SENDPULSE_CLIENT_ID", "")
SENDPULSE_CLIENT_SECRET = os.environ.get("SENDPULSE_CLIENT_SECRET", "")
TOKEN_FILE = os.environ.get("TOKEN_FILE", "iptv_token.json")

# Inicializar a automação de login
iptv_automation = IPTVLoginAutomation(
    username=IPTV_USERNAME,
    password=IPTV_PASSWORD,
    painel_url=IPTV_PANEL_URL,
    token_file=TOKEN_FILE
)

# Variável global para armazenar o token do SendPulse
sendpulse_token = None

def obter_token_sendpulse():
    """
    Obtém o token de autenticação do SendPulse usando client_credentials.
    
    Returns:
        str: Token de acesso ou None em caso de falha
    """
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

def criar_usuario_teste_iptv(ultimos_digitos_cliente):
    """
    Cria um usuário de teste no painel IPTV usando o token JWT.
    
    Args:
        ultimos_digitos_cliente (str): Os 4 últimos dígitos do número do cliente
        
    Returns:
        dict: Dados do usuário criado (username, password, exp_date) ou None em caso de falha
    """
    try:
        # Obter o token JWT
        token = iptv_automation.get_token()
        if not token:
            logger.error("Não foi possível obter o token JWT")
            return None
        
        url = IPTV_API_URL
        
        # Payload conforme capturado no DevTools
        payload = {
            "notes": ultimos_digitos_cliente,
            "package_p2p": "64399dca5ea59e8a1de2b083",
            "krator_package": "1",
            "package_iptv": 95,
            "testDuration": 4  # Duração do teste em horas
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Extrair informações relevantes da resposta
        usuario_info = {
            "username": data.get("username"),
            "password": data.get("password"),
            "exp_date": data.get("exp_date")
        }
        
        logger.info(f"Usuário de teste criado com sucesso: {usuario_info['username']}")
        return usuario_info
    except Exception as e:
        logger.error(f"Erro ao criar usuário de teste IPTV: {str(e)}")
        
        # Se o erro for de autenticação (401), tentar renovar o token e tentar novamente
        if hasattr(e, 'response') and e.response.status_code == 401:
            logger.info("Tentando renovar o token JWT e criar usuário novamente")
            token = iptv_automation.get_token(force_refresh=True)
            if token:
                try:
                    headers["Authorization"] = f"Bearer {token}"
                    response = requests.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    
                    data = response.json()
                    usuario_info = {
                        "username": data.get("username"),
                        "password": data.get("password"),
                        "exp_date": data.get("exp_date")
                    }
                    
                    logger.info(f"Usuário de teste criado com sucesso após renovação do token: {usuario_info['username']}")
                    return usuario_info
                except Exception as retry_error:
                    logger.error(f"Erro ao criar usuário após renovação do token: {str(retry_error)}")
        
        return None

def enviar_credenciais_whatsapp(numero_telefone, usuario_info):
    """
    Envia as credenciais do usuário de teste via WhatsApp usando a API do SendPulse.
    
    Args:
        numero_telefone (str): Número de telefone do cliente (com código do país)
        usuario_info (dict): Informações do usuário (username, password, exp_date)
        
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    global sendpulse_token
    
    if not sendpulse_token:
        sendpulse_token = obter_token_sendpulse()
        if not sendpulse_token:
            return False
    
    try:
        url = f"{SENDPULSE_API_URL}/whatsapp/contacts/sendByPhone"
        
        # Formatar a data de expiração para melhor legibilidade
        exp_date = usuario_info.get("exp_date", "")
        if exp_date:
            try:
                # Converter para objeto datetime e formatar
                exp_datetime = datetime.fromisoformat(exp_date.replace("Z", "+00:00"))
                exp_date_formatada = exp_datetime.strftime("%d/%m/%Y %H:%M")
            except:
                exp_date_formatada = exp_date
        
        # Montar a mensagem com as credenciais
        mensagem = (
            f"*Suas credenciais de teste IPTV*\n\n"
            f"Usuário: *{usuario_info.get('username', '')}*\n"
            f"Senha: *{usuario_info.get('password', '')}*\n"
            f"Expira em: {exp_date_formatada}\n\n"
            f"Baixe o aplicativo WTV PLAYER e aproveite!"
        )
        
        headers = {
            "Authorization": f"Bearer {sendpulse_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "phone": numero_telefone,
            "message": mensagem
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Credenciais enviadas com sucesso para o número {numero_telefone}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar credenciais via WhatsApp: {str(e)}")
        
        # Se o erro for de autenticação, tentar renovar o token e tentar novamente
        if hasattr(e, 'response') and e.response.status_code in [401, 403]:
            logger.info("Tentando renovar o token do SendPulse e enviar mensagem novamente")
            sendpulse_token = obter_token_sendpulse()
            if sendpulse_token:
                try:
                    headers["Authorization"] = f"Bearer {sendpulse_token}"
                    response = requests.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    
                    logger.info(f"Credenciais enviadas com sucesso após renovação do token para o número {numero_telefone}")
                    return True
                except Exception as retry_error:
                    logger.error(f"Erro ao enviar mensagem após renovação do token: {str(retry_error)}")
        
        return False

def processar_solicitacao_teste(numero_telefone):
    """
    Processa uma solicitação completa de teste: extrai os últimos 4 dígitos do número,
    cria o usuário e envia as credenciais.
    
    Args:
        numero_telefone (str): Número de telefone do cliente (com código do país)
        
    Returns:
        dict: Resultado da operação com status e mensagem
    """
    # Extrair os 4 últimos dígitos do número de telefone
    ultimos_digitos = numero_telefone[-4:]
    logger.info(f"Extraindo os 4 últimos dígitos do número: {ultimos_digitos}")
    
    # Criar usuário de teste
    usuario_info = criar_usuario_teste_iptv(ultimos_digitos)
    if not usuario_info:
        return {
            "sucesso": False,
            "mensagem": "Falha ao criar usuário de teste IPTV"
        }
    
    # Enviar credenciais via WhatsApp
    envio_sucesso = enviar_credenciais_whatsapp(numero_telefone, usuario_info)
    if not envio_sucesso:
        return {
            "sucesso": False,
            "mensagem": "Usuário criado, mas falha ao enviar credenciais via WhatsApp",
            "usuario_info": usuario_info
        }
    
    return {
        "sucesso": True,
        "mensagem": "Usuário criado e credenciais enviadas com sucesso",
        "usuario_info": usuario_info
    }

@app.route('/', methods=['GET'])
def home():
    """
    Rota principal para verificar se o serviço está funcionando
    """
    return jsonify({
        "status": "online",
        "message": "Webhook IPTV-SendPulse está funcionando! Use /webhook/iptv-teste para criar testes."
    })

@app.route('/webhook/iptv-teste', methods=['POST'])
def webhook_iptv_teste():
    """
    Webhook para receber solicitações de teste IPTV do chatbot do SendPulse.
    
    Espera receber um JSON com:
    {
        "phone": "5511999999999"
    }
    
    Os 4 últimos dígitos são extraídos automaticamente do número de telefone.
    """
    try:
        data = request.json
        logger.info(f"Recebido webhook: {data}")
        
        if not data:
            return jsonify({"status": "erro", "mensagem": "Dados não fornecidos"}), 400
        
        numero_telefone = data.get('phone')
        
        if not numero_telefone:
            return jsonify({
                "status": "erro", 
                "mensagem": "Número de telefone não fornecido"
            }), 400
        
        # Processar a solicitação (os 4 últimos dígitos são extraídos automaticamente)
        resultado = processar_solicitacao_teste(numero_telefone)
        
        if resultado["sucesso"]:
            return jsonify({
                "status": "sucesso",
                "mensagem": resultado["mensagem"]
            }), 200
        else:
            return jsonify({
                "status": "erro",
                "mensagem": resultado["mensagem"]
            }), 500
            
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return jsonify({
            "status": "erro",
            "mensagem": f"Erro interno: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Verificar se temos um token JWT válido
    token = iptv_automation.get_token()
    if not token:
        logger.warning("Não foi possível obter um token JWT válido. Execute o script iptv_login_automation.py manualmente.")
    
    # Obter a porta do ambiente (para compatibilidade com serviços de hospedagem)
    port = int(os.environ.get("PORT", 5000))
    
    # Executar o servidor Flask
    app.run(host='0.0.0.0', port=port)
