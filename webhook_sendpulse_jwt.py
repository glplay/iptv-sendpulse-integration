from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# URLs corretas
LOGIN_URL = "https://apinew.knewcms.com/auth/login"
CREATE_TEST_URL = "https://apinew.knewcms.com/lines/test"

# Credenciais do painel
USERNAME = "glplay"
PASSWORD = "09kjksz"

def get_jwt_token():
    """Faz login na API do painel e retorna o token JWT."""
    try:
        payload = {
            "username": USERNAME,
            "password": PASSWORD,
            "twoFacToken": ""
        }
        response = requests.post(LOGIN_URL, json=payload)
        if response.status_code == 201:
            return response.json().get("token")
        else:
            print(f"[Erro Login] Status: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[Exceção Login] {e}")
        return None

@app.route("/webhook/iptv-teste", methods=["POST"])
def gerar_teste():
    token = get_jwt_token()
    if not token:
        return jsonify({
            "success": False,
            "message": "Falha ao autenticar usuário. Token não obtido."
        }), 401

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(CREATE_TEST_URL, headers=headers, json={})
        if response.status_code == 201:
            data = response.json()
            return jsonify({
                "success": True,
                "iptv_username": data.get("username"),
                "iptv_password": data.get("password"),
                "message": f"Login: {data.get('username')}\nSenha: {data.get('password')}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": f"Erro ao criar teste IPTV: {response.status_code} - {response.text}"
            }), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro inesperado ao criar teste: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
