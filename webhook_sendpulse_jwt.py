import os
import json
import logging
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Função para obter o token JWT do SendPulse via client_id e client_secret
def get_sendpulse_access_token():
    url = os.getenv("SENDPULSE_TOKEN_URL")
    client_id = os.getenv("SENDPULSE_CLIENT_ID")
    client_secret = os.getenv("SENDPULSE_CLIENT_SECRET")

    logging.info("Solicitando token de acesso ao SendPulse...")

    response = requests.post(url, json={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    })

    if response.status_code == 200:
        token = response.json().get("access_token")
        logging.info("Token de acesso obtido com sucesso.")
        return token
    else:
        logging.error(f"Erro ao obter token: {response.text}")
        return None

# Função para criar o teste IPTV
def criar_teste_iptv(numero):
    url = os.getenv("IPTV_URL") + "/lines/test"
    jwt = os.getenv("IPTV_JWT_TOKEN")

    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json"
    }

    payload = {
        "notes": str(numero),
        "package_p2p": "64399dca5ea59e8a1de2b083",
        "krator_package": "1",
        "package_iptv": 95,
        "testDuration": 4
    }

    logging.info(f"Iniciando criação de teste IPTV para: {numero}")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        dados = response.json()
        logging.info(f"Teste criado com sucesso: {dados}")
        return dados
    else:
        logging.error(f"Erro ao criar teste IPTV: {response.text}")
        return None

# Função para enviar a mensagem WhatsApp via SendPulse
def enviar_mensagem(numero, login, senha):
    token = get_sendpulse_access_token()
    if not token:
        return False

    url = "https://api.sendpulse.com/whatsapp/contacts/send"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "phone": numero,
        "book_id": 0,
        "message": {
            "type": "template",
            "template": {
                "name": "iptv_teste",
                "language": {"code": "pt_BR"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": login},
                            {"type": "text", "text": senha}
                        ]
                    }
                ]
            }
        }
    }

    logging.info("Enviando mensagem WhatsApp com dados do teste...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        logging.info("Mensagem enviada com sucesso.")
        return True
    else:
        logging.error(f"Erro ao enviar mensagem WhatsApp: {response.status_code} - {response.text}")
        return False

@app.route("/webhook/iptv-teste", methods=["POST"])
def webhook_iptv_teste():
    data = request.json
    numero = data.get("phone")

    if not numero:
        return jsonify({"error": "Telefone não fornecido"}), 400

    dados_teste = criar_teste_iptv(numero)

    if not dados_teste:
        return jsonify({"error": "Falha ao criar teste"}), 500

    login = dados_teste.get("username")
    senha = dados_teste.get("password")

    if not login or not senha:
        return jsonify({"error": "Dados de login incompletos"}), 500

    sucesso = enviar_mensagem(numero, login, senha)

    if sucesso:
        return jsonify({"mensagem": "Teste criado e mensagem enviada"})
    else:
        return jsonify({"mensagem": "Teste criado, mas falha ao enviar mensagem"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=10000)
