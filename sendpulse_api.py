import requests
import logging
import time

logger = logging.getLogger("sendpulse_api")

class SendPulseAPI:
    def __init__(self, client_id, client_secret, token_url="https://api.sendpulse.com/oauth/access_token"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None
        self.token_expires_at = 0
        self.base_url = "https://api.sendpulse.com"
        self._autenticar()

    def _autenticar(self):
        try:
            response = requests.post(self.token_url, data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })

            print("Resposta bruta da autenticação:", response.status_code, response.text)  # LOG DEBUG

            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expires_at = time.time() + data["expires_in"]

            logger.info("Token de acesso obtido com sucesso.")
        except Exception as e:
            logger.error("Erro ao obter token de acesso: %s", e)
            raise

    def _verificar_token(self):
        if not self.access_token or time.time() > self.token_expires_at:
            self._autenticar()

    def _get_headers(self):
        self._verificar_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def obter_ou_criar_contato(self, phone):
        headers = self._get_headers()

        search_url = f"{self.base_url}/contacts/search?phone={phone}"
        resp = requests.get(search_url, headers=headers)

        if resp.status_code == 200:
            dados = resp.json()
            if dados.get("data"):
                return dados["data"][0]["id"]

        create_url = f"{self.base_url}/whatsapp/contacts"
        body = {
            "phone": phone,
            "variables": {}
        }

        resp = requests.post(create_url, headers=headers, json=body)

        if resp.status_code in [200, 201]:
            return resp.json()["data"]["contact_id"]
        else:
            logger.error(f"Erro ao criar contato: {resp.status_code} - {resp.text}")
            raise Exception("Não foi possível obter ou criar o contato.")

    def enviar_mensagem_whatsapp(self, phone, mensagem):
        try:
            contact_id = self.obter_ou_criar_contato(phone)
        except Exception as e:
            logger.error(f"Erro ao obter contact_id: {e}")
            return 422, {"error": str(e)}

        url = f"{self.base_url}/whatsapp/messages/send"

        payload = {
            "contact_id": contact_id,
            "type": "text",
            "message": {
                "text": mensagem
            }
        }

        headers = self._get_headers()
        print("Enviando mensagem com token:", self.access_token)  # LOG DEBUG

        try:
            response = requests.post(url, json=payload, headers=headers)
            print("Resposta envio mensagem:", response.status_code, response.text)  # LOG DEBUG
            return response.status_code, response.json()
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
            return 500, {"error": str(e)}

    def disparar_evento(self, event_name, phone, login, senha):
        """
        Dispara um evento do tipo webhook para iniciar um fluxo no SendPulse.
        """
        url = f"{self.base_url}/events/transmission"
        headers = self._get_headers()

        payload = {
            "event": event_name,
            "payload": {
                "phone": phone,
                "login": login,
                "senha": senha
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            print("Resposta do evento:", response.status_code, response.text)
            return response.status_code, response.json()
        except Exception as e:
            logger.error(f"Erro ao disparar evento: {e}")
            return 500, {"error": str(e)}
