from flask import Flask, request, jsonify
import requests
import logging
import os
from random import randint

app = Flask(__name__)

# Configurações SendPulse
SENDPULSE_BOT_ID = "6817c097507ce58f0201fc08"
SENDPULSE_API_TOKEN = os.environ.get("SENDPULSE_API_TOKEN")  # ou defina direto aqui

# Logging
logging.basicConfig(level=logging.INFO)

@app.route("/webhook/iptv-teste", methods=["POST"])
def webhook_iptv_teste():
    try:
        data = request.get_json()
        numero = data.get("phone")

        if not numero:
            return jsonify({"error": "Telefone é obrigatório"}), 400

        # Simula criação de login/senha
        login = f"gplay{randint(100, 999)}"
        senha = f"abc{randint(100, 999)}"

        # Enviar mensagem via SendPulse
        mensagem = f"Seu teste IPTV foi criado!\nLogin: {login}\nSenha: {senha}"
        enviar_mensagem_whatsapp(numero, mensagem)

        # Retorna os dados para o SendPulse usar nos próximos blocos
        return jsonify({
            "login": login,
            "senha": senha
        }), 200

    except Exception as e:
        logging.exception("Erro no webhook IPTV")
        return jsonify({"error": str(e)}), 500

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
            logging.info("Mensagem WhatsApp enviada com sucesso.")
        else:
            logging.error(f"Erro ao enviar WhatsApp: {response.status_code} - {response.text}")

    except Exception as e:
        logging.exception("Erro na função enviar_mensagem_whatsapp")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
