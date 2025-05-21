import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from iptv_login_automation import IPTVLoginAutomation
from sendpulse_api import SendPulseAPI

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Inicializar a automação de login IPTV
IPTV_USERNAME = os.getenv("IPTV_USERNAME")
IPTV_PASSWORD = os.getenv("IPTV_PASSWORD")
IPTV_PANEL_URL = os.getenv("IPTV_PANEL_URL")
TOKEN_FILE = os.getenv("TOKEN_FILE", "cookies.pkl")

iptv_automation = IPTVLoginAutomation(
    IPTV_USERNAME,
    IPTV_PASSWORD,
    IPTV_PANEL_URL,
    TOKEN_FILE
)

# Inicializar a API do SendPulse
SENDPULSE_CLIENT_ID = os.getenv("SENDPULSE_CLIENT_ID")
SENDPULSE_CLIENT_SECRET = os.getenv("SENDPULSE_CLIENT_SECRET")
SENDPULSE_TOKEN_URL = os.getenv("SENDPULSE_TOKEN_URL", "https://api.sendpulse.com/oauth/access_token")

sendpulse_api = SendPulseAPI(SENDPULSE_CLIENT_ID, SENDPULSE_CLIENT_SECRET, SENDPULSE_TOKEN_URL)

# Inicializar o app Flask
app = Flask(__name__)

@app.route("/webhook/iptv-teste", methods=["POST"])
def criar_usuario_teste_iptv():
    try:
        data = request.get_json()
        phone = data.get("phone")

        if not phone:
            return jsonify({"error": "Telefone não fornecido"}), 400

        logging.info(f"Iniciando criação de teste IPTV para: {phone}")

        # Criar usuário IPTV de teste
        usuario, senha = iptv_automation.criar_usuario_teste(phone)

        # Criar mensagem de texto
        mensagem = f"🎉 Acesso de Teste IPTV 🎉\n\nUsuário: {usuario}\nSenha: {senha}\n\nBom proveito!"

        # Enviar mensagem WhatsApp via SendPulse
        status, resposta = sendpulse_api.enviar_mensagem_whatsapp(phone, mensagem)

        if status != 200:
            logging.error(f"Erro ao enviar mensagem WhatsApp: {resposta}")
            return jsonify({"error": "Falha ao enviar mensagem WhatsApp"}), 500

        logging.info(f"Usuário IPTV de teste criado e mensagem enviada para: {phone}")
        return jsonify({"message": "Usuário de teste criado e mensagem enviada"}), 200

    except Exception as e:
        logging.error(f"Erro ao criar usuário IPTV: {e}")
        return jsonify({"error": "Erro ao criar usuário IPTV"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
