import logging
import requests

logger = logging.getLogger("iptv_login_automation")

class IPTVLoginAutomation:
    def __init__(self, token_jwt: str, painel_url: str):
        self.token = token_jwt
        self.painel_url = painel_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        logger.info(f"Painel IPTV URL definido como: {self.painel_url}")

    def criar_usuario_teste(self, phone: str):
        """Cria um usuário de teste IPTV vinculado ao telefone informado."""
        criar_url = f"{self.painel_url}/lines/test"

        payload = {
            "notes": phone,
            "package_p2p": "64399dca5ea59e8a1de2b083",
            "krator_package": "1",
            "package_iptv": 95,
            "testDuration": 4
        }

        try:
            response = self.session.post(criar_url, json=payload)
            response.raise_for_status()

            data = response.json()
            username = data.get("username", "N/A")
            password = data.get("password", "N/A")
            logger.info(f"Usuário de teste IPTV criado: {username}")
            return username, password

        except Exception as e:
            logger.error("Erro ao criar usuário de teste IPTV: %s", e)
            raise
