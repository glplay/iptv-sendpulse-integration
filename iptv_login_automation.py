#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import logging
import random
import string

# Configuração básica de logging
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
    def __init__(self, username, password, painel_url, token_file):
        self.username = username
        self.password = password
        self.painel_url = painel_url
        self.token_file = token_file

        logger.info(f"Painel IPTV URL definido como: {self.painel_url}")

    def criar_usuario_teste(self, identificador):
        """
        Cria um usuário de teste no painel IPTV.
        """
        try:
            token = self.get_token()
            if not token:
                raise Exception("Token JWT não disponível.")

            usuario = f"teste_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
            senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            url = f"{self.painel_url}/users"  # Substitua se necessário
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            payload = {
                "username": usuario,
                "password": senha,
                "email": identificador if "@" in identificador else f"{usuario}@teste.com",
                "is_trial": True,
                "days": 1
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            logger.info(f"Usuário de teste criado com sucesso: {usuario}")
            return usuario, senha

        except Exception as e:
            logger.error(f"Erro ao criar usuário de teste IPTV: {e}")
            raise

    def get_token(self):
        """
        Retorna o token JWT do painel IPTV com tratamento robusto de erros.
        """
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    token = data.get("token")
                    if token:
                        logger.info("Token carregado do arquivo com sucesso.")
                        return token

            login_url = f"{self.painel_url}/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(login_url, json=payload, headers=headers)

            if response.status_code != 200:
                logger.error(f"Erro HTTP {response.status_code} ao fazer login no painel IPTV.")
                logger.error(f"Resposta do servidor: {response.text}")
                return None

            try:
                data = response.json()
            except ValueError:
                logger.error("Erro: resposta do painel IPTV não está em formato JSON.")
                logger.error(f"Conteúdo da resposta: {response.text}")
                return None

            token = data.get("token")
            if not token:
                logger.error("Token não encontrado na resposta do login.")
                return None

            with open(self.token_file, 'w') as f:
                json.dump({"token": token}, f)

            logger.info("Token obtido e salvo com sucesso.")
            return token

        except Exception as e:
            logger.error(f"Erro inesperado ao obter token do painel IPTV: {str(e)}")
            return None
