from flask import Flask, request, jsonify
import requests
import logging
import os

app = Flask(__name__)

# Configurações SendPulse
SENDPULSE_BOT_ID = "6817c097507ce58f0201fc08"
SENDPULSE_API_TOKEN = os.environ.get("SENDPULSE_API_TOKEN")

# API de criação de teste IPTV
IPTV_API_URL = "https://apinew.knewcms.com/lines/test"
IPTV_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Njk5MDk2LCJpYXQiOjE3NDc5MjU4NjQsImV4cCI6MTc0NzkzMzA2NH0.22uL6qX6bDy8bE9ibf3MVALN4Ae2QEUCGTYfhZji8uE"

logging.basicConfig(level=logging.INFO)

@app.route("/webhook/iptv-teste", methods=["POST"])
def webhook_iptv_teste():
    try:
        data = request.get_json()
        numero = data.get("phone")

        if not numero:
            logging.error("Telefone não fornecido no payload.")
            return jsonify({"error": "Telefone é obrigatório."}), 400

        logging.info(f"Iniciando criação de teste IPTV para: {numero}")

        # Cria o usuário IPTV real
        resultado = criar_usuario_teste_iptv()
        if not resultado:
            return jsonify({"error": "Falha ao criar teste IPTV."}), 500

        username = resultado["username"]
        password = resultado["password"]

        # Monta e envia mensagem via WhatsApp
        mensagem = f"Olá! Seu teste IPTV está pronto.\nLogin: {username}\nSenha: {password}"
        sucesso = enviar_mensagem_whatsapp(numero, mensagem)

        if sucesso:
            return jsonify({"status": "Mensagem enviada com sucesso."}), 200
        else:
            return jsonify({"error": "Erro ao enviar mensagem via WhatsApp."}), 500

    except Exception as e:
        logging.exception("Erro inesperado no webhook.")
        return jsonify({"error": str(e)}), 500

def criar_usuario_teste_iptv():
    try:
        headers = {
            "Authorization": f"Bearer {IPTV_BEARER_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "notes": "1234",
            "package_p2p": "64399dca5ea59e8a1de2b083",
            "krator_package": "1",
            "package_iptv": 95,
            "testDuration": 4
        }

        response = requests.post(IPTV_API_URL, json=payload, headers=headers)
        if response.status_code == 201:
            data = response.json()
            return {
                "username": data.get("username"),
                "password": data.get("password")
            }
        else:
            logging.error(f"Erro ao criar teste IPTV: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logging.exception("Erro na criação do usuário IPTV")
        return None

def enviar_mensagem_whatsapp(telefone, mensagem):
    try:
        headers = {
            "Authorization": f"Bearer {SENDPULSE_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "bot_id": SENDPULSE_BOT_ID,
            "contact": {
                "phone": telefone
            },
            "message": {
                "text": mensagem
            }
        }

        response = requests.post("https://api.sendpulse.com/whatsapp/contacts/send", json=payload, headers=headers)

        if response.status_code == 200:
            logging.info("Mensagem enviada com sucesso via WhatsApp.")
            return True
        else:
            logging.error(f"Erro ao enviar mensagem WhatsApp: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logging.exception("Erro na função enviar_mensagem_whatsapp")
        return False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
