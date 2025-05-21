import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IPTV_URL = "https://apinew.knewcms.com/lines/test"

class IPTVLoginAutomation:
    def __init__(self, jwt_token: str):
        self.jwt_token = jwt_token

    def criar_usuario_teste(self):
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "notes": "0000",
            "package_p2p": "64399dca5ea59e8a1de2b083",
            "krator_package": "1",
            "package_iptv": 95,
            "testDuration": 4
        }

        try:
            logger.info("Iniciando criação de teste IPTV para: %s", payload)
            response = requests.post(IPTV_URL, headers=headers, json=payload)

            if response.status_code == 201:
                logger.info("Login IPTV criado com sucesso.")
                return response.json()
            else:
                logger.error("Erro HTTP %s ao fazer login no painel IPTV.", response.status_code)
                logger.error("Resposta do servidor: %s", response.text)
                return None

        except requests.exceptions.RequestException as e:
            logger.error("Erro ao criar usuário IPTV: %s", str(e))
            return None

if __name__ == "__main__":
    from webhook_sendpulse_jwt import obter_jwt_token

    jwt = obter_jwt_token()
    if jwt:
        automacao = IPTVLoginAutomation(jwt)
        resultado = automacao.criar_usuario_teste()
        if resultado:
            print("\nResultado:")
            print(resultado)
        else:
            print("\n❌ Falha ao gerar o login de teste.")
    else:
        logger.error("Erro ao criar usuário IPTV: Token JWT não disponível.")
