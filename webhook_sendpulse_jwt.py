from flask import Flask, request, jsonify
import requests
import logging
import os

# Configuração do Flask
app = Flask(__name__)

# Configurações SendPulse
SENDPULSE_BOT_ID = "6817c097507ce58f0201fc08"  # Coloque o seu bot_id aqui
SENDPULSE_API_TOKEN = os.environ.get("SENDPULSE_API_TOKEN")  # ou defina direto na string

# URL da API SendPulse para envio de mensagem WhatsApp
SENDPULSE_API_URL = f"https://api.sendpulse.com/whatsapp/contacts"

# Configuração do log
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

        # Simula a criação do usuário IPTV
        usuario_id = criar_usuario_teste_iptv()
        logging.info(f"Usuário de teste IPTV criado: {usuario_id}")

        # Enviar mensagem WhatsApp via SendPulse
        mensagem = f"Olá! Seu teste IPTV está pronto. ID do usuário: {usuario_id}"
        sucesso = enviar_mensagem_whatsapp(numero, mensagem)

        if sucesso:
            return jsonify({"status": "Mensagem enviada com sucesso."}), 200
        else:
            return jsonify({"error": "Erro ao enviar mensagem via WhatsApp."}), 500

    except Exception as e:
        logging.exception("Erro inesperado no webhook.")
        return jsonify({"error": str(e)}), 500

def criar_usuario_teste_iptv():
    from random import randint
    return str(randint(1000000, 9999999))

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
