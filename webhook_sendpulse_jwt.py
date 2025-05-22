from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Token retirado do sessionStorage (válido temporariamente)
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Njk5MDk2LCJpYXQiOjE3NDc5MzQ1ODYsImV4cCI6MTc0Nzk0MTc4Nn0.9MWdWS9GWp6pNwnA2Oj8nkmj0qJTOx3BrJLIC-J_its"

# Cabeçalhos com autenticação
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}"
}

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        # Faz a requisição para criar o teste IPTV
        response = requests.post(
            'https://apinew.knewcms.com/lines/test',
            headers=HEADERS,
            json={}
        )

        # Trata o retorno
        if response.status_code == 200:
            data = response.json()

            # Extração de dados do teste criado
            login = data.get("username")
            senha = data.get("password")

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
    app.run(debug=True, port=5001)
