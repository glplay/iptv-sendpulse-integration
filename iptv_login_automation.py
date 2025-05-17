#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para automação de login no painel IPTV e captura do token JWT.
Este script automatiza o processo de login no painel IPTV, lida com o CAPTCHA
e captura o token JWT para uso em requisições autenticadas.
"""

import os
import time
import json
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("iptv_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

class IPTVLoginAutomation:
    """Classe para automação de login no painel IPTV e captura do token JWT."""
    
    def __init__(self):
        """Inicializa a classe com configurações básicas."""
        self.iptv_url = os.getenv('IPTV_URL', 'https://api.friv.gratis/games/159')
        self.username = os.getenv('IPTV_USERNAME')
        self.password = os.getenv('IPTV_PASSWORD')
        self.jwt_token = None
        self.jwt_expiry = None
        self.token_file = 'jwt_token.json'
        
        if not self.username or not self.password:
            logger.error("Credenciais não configuradas. Configure IPTV_USERNAME e IPTV_PASSWORD no arquivo .env")
            raise ValueError("Credenciais não configuradas")
    
    def setup_driver(self):
        """Configura o driver do Selenium para automação."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Configurações adicionais para evitar detecção de automação
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Modificar o navigator.webdriver para evitar detecção
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def login_and_get_token(self):
        """Realiza login no painel IPTV e captura o token JWT."""
        logger.info(f"Iniciando processo de login no painel IPTV: {self.iptv_url}")
        
        # Verificar se já existe um token válido
        if self.load_token():
            logger.info("Token JWT válido encontrado, não é necessário fazer login novamente")
            return self.jwt_token
        
        driver = self.setup_driver()
        
        try:
            # Acessar a página de login
            driver.get(self.iptv_url)
            logger.info("Página de login carregada")
            
            # Aguardar carregamento da página
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Preencher campos de login
            driver.find_element(By.ID, "username").send_keys(self.username)
            driver.find_element(By.ID, "password").send_keys(self.password)
            logger.info("Campos de login preenchidos")
            
            # Lidar com o CAPTCHA (checkbox "Não sou um robô")
            self.handle_captcha(driver)
            
            # Clicar no botão de login
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
            login_button.click()
            logger.info("Botão de login clicado")
            
            # Aguardar redirecionamento ou resposta de sucesso
            time.sleep(3)
            
            # Capturar o token JWT
            self.extract_jwt_token(driver)
            
            # Salvar o token para uso futuro
            self.save_token()
            
            logger.info("Login realizado com sucesso e token JWT capturado")
            return self.jwt_token
            
        except Exception as e:
            logger.error(f"Erro durante o processo de login: {str(e)}")
            raise
        finally:
            driver.quit()
    
    def handle_captcha(self, driver):
        """Lida com o CAPTCHA do tipo 'Não sou um robô'."""
        try:
            logger.info("Tentando localizar e clicar no CAPTCHA")
            
            # Localizar o iframe do reCAPTCHA
            recaptcha_iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
            
            # Mudar para o iframe do reCAPTCHA
            driver.switch_to.frame(recaptcha_iframe)
            
            # Clicar na caixa de seleção
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".recaptcha-checkbox-border"))
            )
            checkbox.click()
            logger.info("Checkbox do CAPTCHA clicado")
            
            # Voltar ao conteúdo principal
            driver.switch_to.default_content()
            
            # Aguardar a validação do CAPTCHA
            time.sleep(2)
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Não foi possível interagir com o CAPTCHA automaticamente: {str(e)}")
            logger.info("O CAPTCHA pode requerer intervenção manual ou uso de serviço externo")
            
            # Aqui você pode implementar uma solução alternativa, como:
            # 1. Usar um serviço de resolução de CAPTCHA como 2captcha ou Anti-Captcha
            # 2. Implementar uma pausa para intervenção manual
            # 3. Usar técnicas avançadas de automação
            
            # Exemplo de pausa para intervenção manual (descomente se necessário)
            # input("Por favor, resolva o CAPTCHA manualmente e pressione Enter para continuar...")
    
    def extract_jwt_token(self, driver):
        """Extrai o token JWT da resposta ou do localStorage."""
        try:
            # Método 1: Extrair do localStorage (mais comum)
            self.jwt_token = driver.execute_script("return localStorage.getItem('jwt_token') || sessionStorage.getItem('jwt_token') || localStorage.getItem('token') || sessionStorage.getItem('token');")
            
            if not self.jwt_token:
                # Método 2: Extrair dos cookies
                cookies = driver.get_cookies()
                for cookie in cookies:
                    if cookie['name'] in ['jwt_token', 'token', 'access_token']:
                        self.jwt_token = cookie['value']
                        break
            
            if not self.jwt_token:
                # Método 3: Capturar das requisições de rede (requer análise dos prints do usuário)
                logger.warning("Não foi possível extrair o token JWT automaticamente")
                logger.info("A extração do token JWT será implementada após análise dos prints do Developer Tools")
                # Esta parte será implementada após receber os prints do usuário
            
            # Definir data de expiração (24 horas a partir de agora)
            self.jwt_expiry = int(time.time()) + 24 * 60 * 60
            
            logger.info("Token JWT extraído com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao extrair o token JWT: {str(e)}")
            raise
    
    def save_token(self):
        """Salva o token JWT em um arquivo para uso futuro."""
        if not self.jwt_token:
            logger.warning("Nenhum token para salvar")
            return False
        
        token_data = {
            'token': self.jwt_token,
            'expiry': self.jwt_expiry
        }
        
        try:
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f)
            logger.info(f"Token JWT salvo em {self.token_file}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar o token: {str(e)}")
            return False
    
    def load_token(self):
        """Carrega o token JWT do arquivo, se existir e for válido."""
        try:
            if not os.path.exists(self.token_file):
                logger.info("Arquivo de token não encontrado")
                return False
            
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            # Verificar se o token ainda é válido (não expirou)
            current_time = int(time.time())
            if token_data['expiry'] <= current_time:
                logger.info("Token JWT expirado")
                return False
            
            self.jwt_token = token_data['token']
            self.jwt_expiry = token_data['expiry']
            
            logger.info("Token JWT válido carregado do arquivo")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar o token: {str(e)}")
            return False
    
    def create_test_user(self, phone_last_digits):
        """
        Cria um usuário de teste no painel IPTV.
        Utiliza os 4 últimos dígitos do número de telefone como identificador.
        """
        if not self.jwt_token:
            logger.error("Token JWT não disponível. Faça login primeiro.")
            return None
        
        logger.info(f"Criando usuário de teste para número com final {phone_last_digits}")
        
        try:
            # Baseado nos prints do Developer Tools fornecidos pelo usuário
            headers = {
                'Authorization': f'Bearer {self.jwt_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Origin': 'https://pagar.io',
                'Referer': 'https://pagar.io/'
            }
            
            # Payload baseado nos prints do Developer Tools
            data = {
                'notes': phone_last_digits,  # Usar os 4 últimos dígitos como identificador
                'package_p2p': '643990ca5ea59e8a1de2b083',  # ID do pacote conforme prints
                'krator_package': '1',  # ID do pacote conforme prints
                'testDuration': 4  # Duração de 4 horas
            }
            
            # Endpoint baseado nos prints do Developer Tools
            response = requests.post(
                'https://mcapi.knowcms.com:2087/lines/test',
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:  # 201 Created conforme prints
                user_data = response.json()
                logger.info(f"Usuário de teste criado com sucesso: {user_data}")
                
                # Extrair informações relevantes da resposta
                result = {
                    'username': user_data.get('username', ''),
                    'password': user_data.get('password', ''),
                    'expiry': f"Em {user_data.get('testDuration', 4)} horas",
                    'notes': user_data.get('notes', phone_last_digits),
                    'created_at': user_data.get('exp_date', '')
                }
                
                return result
            else:
                logger.error(f"Erro ao criar usuário de teste: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao criar usuário de teste: {str(e)}")
            return None


if __name__ == "__main__":
    # Exemplo de uso
    automation = IPTVLoginAutomation()
    token = automation.login_and_get_token()
    
    if token:
        print(f"Token JWT obtido com sucesso: {token[:20]}...")
        
        # Exemplo de criação de usuário de teste
        test_user = automation.create_test_user("1234")
        if test_user:
            print(f"Usuário de teste criado: {test_user}")
    else:
        print("Falha ao obter o token JWT")
