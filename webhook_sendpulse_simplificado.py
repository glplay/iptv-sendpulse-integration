#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import os
from integracao_iptv_sendpulse_simplificado import IPTVSendPulseIntegration
import logging
import gunicorn

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook_sendpulse.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações da integração
IPTV_API_URL = os.environ.get("IPTV_API_URL", "https://mcapi.knewcms.com:2087/lines/test")
SENDPULSE_API_URL = os.environ.get("SENDPULSE_API_URL", "https://api.sendpulse.com")
SENDPULSE_CLIENT_ID = os.environ.get("SENDPULSE_CLIENT_ID")
SENDPULSE_CLIENT_SECRET = os.environ.get("SENDPULSE_CLIENT_SECRET")

# Inicializar a integração
integracao = IPTVSendPulseIntegration(
    IPTV_API_URL,
    SENDPULSE_API_URL,
    SENDPULSE_CLIENT_ID,
    SENDPULSE_CLIENT_SECRET
)

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
        resultado = integracao.processar_solicitacao_teste(numero_telefone)
        
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
    # Obter a porta do ambiente (para compatibilidade com serviços de hospedagem)
    port = int(os.environ.get("PORT", 5000))
    
    # Executar o servidor Flask
    app.run(host='0.0.0.0', port=port)
