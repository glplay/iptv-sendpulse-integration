import logging
import requests
import pickle
import os

logger = logging.getLogger("iptv_login_automation")

class IPTVLoginAutomation:
    def __init__(self, username, password, painel_url, token_file="cookies.pkl"):
        self.username = username
        self.password = password
        self.painel_url = painel_url
        self.token_file = token_file
        self.session = requests.Session()
        self._login()

    def _login(self):
        """Faz login no painel e salva cookies se necessário."""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "rb") as f:
                    self.session.cookies.update(pickle.load(f))
                    logger.info("Cookies carregados de %s", self.token_file)
                    return
            except Exception as e:
                logger.warning("Erro ao carregar cookies: %s", e)

        login_url = f"{self.painel_url}/login"
        payload = {
            "username": self.username,
            "password": self.password
        }

        try:
            response = self.session.post(login_url, data=payload)
            response.raise_for_status()

            if "dashboard" in response.url:
                with open(self.token_file, "wb") as f:
                    pickle.dump(self.session.cookies, f)
                logger.info("Login bem-sucedido e cookies salvos.")
            else:
                raise Exception("Login falhou. Verifique as credenciais.")

        except Exception as e:
            logger.error("Erro ao fazer login: %s", str(e))
            raise

    def criar_usuario_teste(self, phone):
        """Cria um usuário de teste IPTV vinculado ao telefone informado."""

        criar_url = f"{self.painel_url}/lines/test"

        payload = {
            "notes": phone,
            "package_p2p": "64399dca5ea59e8a1de2b083",
            "krator_package": "1",
            "package_iptv": 95,
            "testDuration": 4
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            response = self.session.post(criar_url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            username = data.get("username", "N/A")
            password = data.get("password", "N/A")
            logger.info(f"Usuário de teste IPTV criado: {username}")
            return username, password

        except Exception as e:
            logger.error("Erro ao criar usuário de teste IPTV: %s", e)
            raise
