#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import argparse
import logging
from playwright.sync_api import sync_playwright

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("iptv_login_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IPTVLoginAutomation:
    def __init__(self, username, password, painel_url, token_file="iptv_token.json"):
        """
        Inicializa a automação de login no painel IPTV.
        
        Args:
            username (str): Nome de usuário para login no painel IPTV
            password (str): Senha para login no painel IPTV
            painel_url (str): URL do painel IPTV
            token_file (str): Arquivo para salvar o token JWT
        """
        self.username = username
        self.password = password
        self.painel_url = painel_url
        self.token_file = token_file
        self.token = None
        self.token_expiry = None
    
    def login_and_get_token(self, headless=False):
        """
        Realiza login no painel IPTV e obtém o token JWT.
        
        Args:
            headless (bool): Se True, executa o navegador em modo headless (sem interface gráfica)
            
        Returns:
            dict: Informações do token (token, data de expiração)
        """
        logger.info(f"Iniciando automação de login no painel IPTV: {self.painel_url}")
        
        with sync_playwright() as p:
            # Iniciar o navegador
            browser_type = p.chromium
            browser = browser_type.launch(headless=headless)
            context = browser.new_context()
            
            # Habilitar captura de requisições de rede
            context.route("**/*", lambda route: route.continue_())
            
            page = context.new_page()
            
            try:
                # Acessar a página de login
                logger.info(f"Acessando página de login: {self.painel_url}")
                page.goto(self.painel_url)
                
                # Aguardar carregamento da página
                page.wait_for_load_state("networkidle")
                
                # Preencher formulário de login
                logger.info("Preenchendo formulário de login")
                page.fill('input[name="username"]', self.username)
                page.fill('input[name="password"]', self.password)
                
                # Resolver CAPTCHA (checkbox)
                logger.info("Resolvendo CAPTCHA (checkbox)")
                
                # Verificar se o CAPTCHA é um iframe (reCAPTCHA)
                captcha_frame = page.frame_locator('iframe[title="reCAPTCHA"]')
                if captcha_frame.count() > 0:
                    # Se for reCAPTCHA, clicar no checkbox dentro do iframe
                    captcha_frame.locator('.recaptcha-checkbox-border').click()
                    # Aguardar resolução do CAPTCHA
                    page.wait_for_timeout(2000)  # Aguardar 2 segundos
                else:
                    # Tentar localizar checkbox diretamente na página
                    page.locator('input[type="checkbox"][name="captcha"]').click()
                
                # Clicar no botão de login
                logger.info("Clicando no botão de login")
                page.click('button[type="submit"]')
                
                # Aguardar redirecionamento após login
                page.wait_for_load_state("networkidle")
                
                # Verificar se o login foi bem-sucedido
                if "dashboard" in page.url or "painel" in page.url:
                    logger.info("Login realizado com sucesso")
                else:
                    logger.error("Falha no login. Verifique as credenciais e o CAPTCHA.")
                    browser.close()
                    return None
                
                # Capturar o token JWT
                logger.info("Capturando o token JWT")
                
                # Método 1: Extrair do localStorage
                token_info = None
                try:
                    local_storage = page.evaluate('''() => {
                        const token = localStorage.getItem('token') || localStorage.getItem('jwt') || localStorage.getItem('auth_token');
                        return token;
                    }''')
                    
                    if local_storage:
                        token_info = {
                            "token": local_storage,
                            "source": "localStorage",
                            "timestamp": time.time(),
                            "expiry": time.time() + 86400  # Assumir validade de 24 horas
                        }
                        logger.info("Token extraído do localStorage")
                except Exception as e:
                    logger.warning(f"Não foi possível extrair token do localStorage: {str(e)}")
                
                # Método 2: Capturar das requisições de rede
                if not token_info:
                    # Navegar para uma página que faça requisições autenticadas
                    logger.info("Navegando para capturar requisições autenticadas")
                    page.goto(f"{self.painel_url}/dashboard")
                    page.wait_for_load_state("networkidle")
                    
                    # Extrair token dos cabeçalhos de requisição
                    headers = page.evaluate('''() => {
                        return fetch('/api/user', {
                            method: 'GET',
                            credentials: 'include'
                        }).then(response => {
                            const headers = {};
                            for (const [key, value] of response.headers.entries()) {
                                headers[key] = value;
                            }
                            return headers;
                        });
                    }''')
                    
                    # Verificar se há token de autorização nos cabeçalhos
                    auth_header = headers.get('authorization')
                    if auth_header and auth_header.startswith('Bearer '):
                        token = auth_header.split(' ')[1]
                        token_info = {
                            "token": token,
                            "source": "authorization_header",
                            "timestamp": time.time(),
                            "expiry": time.time() + 86400  # Assumir validade de 24 horas
                        }
                        logger.info("Token extraído dos cabeçalhos de requisição")
                
                # Método 3: Extrair dos cookies
                if not token_info:
                    cookies = context.cookies()
                    for cookie in cookies:
                        if cookie.get('name') in ['token', 'jwt', 'auth_token']:
                            token_info = {
                                "token": cookie.get('value'),
                                "source": "cookie",
                                "timestamp": time.time(),
                                "expiry": cookie.get('expires') or (time.time() + 86400)
                            }
                            logger.info(f"Token extraído do cookie: {cookie.get('name')}")
                            break
                
                # Método 4: Capturar diretamente do DevTools
                if not token_info:
                    # Navegar para uma página que faça requisições autenticadas
                    page.goto(f"{self.painel_url}/api/user")
                    
                    # Extrair o token do corpo da resposta
                    response_text = page.content()
                    if "token" in response_text or "jwt" in response_text:
                        try:
                            response_json = json.loads(response_text)
                            token = response_json.get('token') or response_json.get('jwt') or response_json.get('access_token')
                            if token:
                                token_info = {
                                    "token": token,
                                    "source": "api_response",
                                    "timestamp": time.time(),
                                    "expiry": time.time() + 86400  # Assumir validade de 24 horas
                                }
                                logger.info("Token extraído da resposta da API")
                        except:
                            logger.warning("Não foi possível extrair token da resposta da API")
                
                # Se ainda não encontrou o token, tentar capturar de todas as requisições
                if not token_info:
                    logger.info("Tentando capturar token de todas as requisições")
                    
                    # Função para interceptar requisições e extrair token
                    token_from_requests = []
                    
                    def handle_request(route):
                        request = route.request
                        headers = request.headers
                        if 'authorization' in headers and headers['authorization'].startswith('Bearer '):
                            token_from_requests.append(headers['authorization'].split(' ')[1])
                        route.continue_()
                    
                    # Configurar interceptação de requisições
                    context.route("**/*", handle_request)
                    
                    # Navegar por algumas páginas para gerar requisições
                    page.goto(f"{self.painel_url}/dashboard")
                    page.wait_for_load_state("networkidle")
                    page.goto(f"{self.painel_url}/users")
                    page.wait_for_load_state("networkidle")
                    
                    # Verificar se capturou algum token
                    if token_from_requests:
                        token_info = {
                            "token": token_from_requests[0],
                            "source": "request_interception",
                            "timestamp": time.time(),
                            "expiry": time.time() + 86400  # Assumir validade de 24 horas
                        }
                        logger.info("Token extraído da interceptação de requisições")
                
                # Se ainda não encontrou o token, fazer uma última tentativa com o DevTools
                if not token_info:
                    logger.info("Tentativa final: extraindo token com DevTools")
                    
                    # Executar script para extrair token de várias fontes
                    token_extraction_script = '''() => {
                        const sources = {};
                        
                        // Verificar localStorage
                        try {
                            const localStorageItems = Object.keys(localStorage);
                            for (const key of localStorageItems) {
                                sources[`localStorage_${key}`] = localStorage.getItem(key);
                            }
                        } catch (e) {}
                        
                        // Verificar sessionStorage
                        try {
                            const sessionStorageItems = Object.keys(sessionStorage);
                            for (const key of sessionStorageItems) {
                                sources[`sessionStorage_${key}`] = sessionStorage.getItem(key);
                            }
                        } catch (e) {}
                        
                        // Verificar cookies
                        try {
                            sources['cookies'] = document.cookie;
                        } catch (e) {}
                        
                        return sources;
                    }'''
                    
                    extraction_results = page.evaluate(token_extraction_script)
                    
                    # Analisar resultados para encontrar possíveis tokens
                    for source, value in extraction_results.items():
                        if value and len(value) > 20 and ('.' in value or value.startswith('ey')):
                            token_info = {
                                "token": value,
                                "source": source,
                                "timestamp": time.time(),
                                "expiry": time.time() + 86400  # Assumir validade de 24 horas
                            }
                            logger.info(f"Token extraído de: {source}")
                            break
                
                # Verificar se conseguiu obter o token
                if token_info:
                    # Salvar o token em arquivo
                    with open(self.token_file, 'w') as f:
                        json.dump(token_info, f, indent=2)
                    
                    logger.info(f"Token JWT salvo em: {self.token_file}")
                    self.token = token_info.get("token")
                    self.token_expiry = token_info.get("expiry")
                    
                    return token_info
                else:
                    logger.error("Não foi possível obter o token JWT")
                    return None
                
            except Exception as e:
                logger.error(f"Erro durante a automação: {str(e)}")
                return None
            finally:
                browser.close()
    
    def get_saved_token(self):
        """
        Obtém o token JWT salvo em arquivo.
        
        Returns:
            dict: Informações do token ou None se não existir ou estiver expirado
        """
        try:
            if not os.path.exists(self.token_file):
                logger.warning(f"Arquivo de token não encontrado: {self.token_file}")
                return None
            
            with open(self.token_file, 'r') as f:
                token_info = json.load(f)
            
            # Verificar se o token está expirado
            current_time = time.time()
            if token_info.get("expiry", 0) < current_time:
                logger.warning("Token JWT expirado")
                return None
            
            logger.info("Token JWT válido encontrado")
            self.token = token_info.get("token")
            self.token_expiry = token_info.get("expiry")
            
            return token_info
        except Exception as e:
            logger.error(f"Erro ao ler arquivo de token: {str(e)}")
            return None
    
    def get_token(self, force_refresh=False):
        """
        Obtém o token JWT, renovando se necessário.
        
        Args:
            force_refresh (bool): Se True, força a renovação do token mesmo que ainda seja válido
            
        Returns:
            str: Token JWT ou None em caso de falha
        """
        if not force_refresh:
            # Tentar obter token salvo
            token_info = self.get_saved_token()
            if token_info:
                return token_info.get("token")
        
        # Se não há token salvo ou force_refresh=True, fazer login e obter novo token
        token_info = self.login_and_get_token()
        if token_info:
            return token_info.get("token")
        
        return None

def main():
    parser = argparse.ArgumentParser(description='Automação de login no painel IPTV')
    parser.add_argument('--username', required=True, help='Nome de usuário para login no painel IPTV')
    parser.add_argument('--password', required=True, help='Senha para login no painel IPTV')
    parser.add_argument('--url', required=True, help='URL do painel IPTV')
    parser.add_argument('--token-file', default='iptv_token.json', help='Arquivo para salvar o token JWT')
    parser.add_argument('--force-refresh', action='store_true', help='Forçar renovação do token mesmo que ainda seja válido')
    parser.add_argument('--headless', action='store_true', help='Executar em modo headless (sem interface gráfica)')
    
    args = parser.parse_args()
    
    automation = IPTVLoginAutomation(
        username=args.username,
        password=args.password,
        painel_url=args.url,
        token_file=args.token_file
    )
    
    if args.force_refresh:
        token_info = automation.login_and_get_token(headless=args.headless)
    else:
        token = automation.get_token(force_refresh=False)
        if token:
            print(f"Token JWT válido: {token[:20]}...")
        else:
            print("Não foi possível obter um token JWT válido")

if __name__ == "__main__":
    main()
