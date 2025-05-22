from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

USERNAME = "glplay"
PASSWORD = "09kjksz"

def obter_token_jwt(username, password):
    login_url = "https://apinew.knewcms.com/users/login"
    payload = {
        "username": username,
        "password": password
    }
    try:
        resposta = requests.post(login_url, json=payload)
        if resposta.status_code == 200:
            dados = resposta.json()
            return dados.get("token")
        else:
            print(f"Erro no login: {resposta.text}")
            return None
    except Exception as e:
        print(f"Erro ao obter token: {e}")
        return None

@app.route("/webhook/iptv-teste", methods=["POST"])
def criar_teste_iptv():
    token = obter_token_jwt(USERNAME, PASSWORD)
    if not token:
        return jsonify({"success": False, "message": "Falha ao obter token"}), 401

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        resposta = requests.post("https://apinew.knewcms.com/lines/test", headers=headers, json={})
        if resposta.status_code == 200:
            dados = resposta.json()
            return jsonify({
                "success": True,
                "iptv_username": dados.get("username"),
                "iptv_password": dados.get("password")
            }), 200
        else:
            return jsonify({"success": False, "message": f"Erro ao criar teste: {resposta.text}"}), resposta.status_code
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro inesperado: {e}"}), 500

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=True)
