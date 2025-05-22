from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Token retirado do sessionStorage
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Njk5MDk2LCJpYXQiOjE3NDc5MzQ1ODYsImV4cCI6MTc0Nzk0MTc4Nn0.9MWdWS9GWp6pNwnA2Oj8nkmj0qJTOx3BrJLIC-J_its"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}"
}

@app.route('/webhook/iptv-teste', methods=['POST'])
def handle_webhook():
    try:
        # Verifica o conteúdo recebido
        data = request.get_json()
        print("JSON recebido:", data)

        # Chamada para criação do teste
        response = requests.post(
            'https://apinew.knewcms.com/lines/test',
            headers=HEADERS,
            json={}
        )

        if response.status_code == 200:
            result = response.json()
            login = result.get("username")
            senha = result.get("password")

            return jsonify({
                "success": True,
                "iptv_username": login,
                "iptv_password": senha
            }), 200

        else:
            return jsonify({
                "success": False,
                "message": f"Erro ao criar teste: {response.text}"
            }), response.status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro inesperado: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
