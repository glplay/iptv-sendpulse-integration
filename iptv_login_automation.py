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
        O identificador pode ser um e-mail ou número de telefone.
        Retorna o usuário e senha criados.
        """
        try:
            token = self.get_token()
            if not token:
                raise Exception("Token JWT não disponível.")

            # Gerar usuário e senha aleatórios
            usuario = f"teste_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
            senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            url = f"{self.painel_url}/users"  # Substitua esse endpoint se necessário
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            payload = {
                "username": usuario,
                "password": senha,
                "email": identificador if "@" in identificador else f"{usuario}@teste.com",
                "is_trial": True,
                "days": 1  # Exemplo: 1 dia de teste
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
        Retorna o token JWT do painel IPTV. Se houver um token salvo localmente, ele será reutilizado.
        Caso contrário, será feita uma nova solicitação de login.
        """
        try:
            # Se o token já estiver salvo, tente reutilizar
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    token = data.get("token")
                    if token:
                        logger.info("Token carregado do arquivo com sucesso.")
                        return token

            # Senão, obter um novo token
            login_url = f"{self.painel_url}/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(login_url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            token = data.get("token")
            if not token:
                raise Exception("Token não encontrado na resposta do login")

            # Salvar o token em arquivo
            with open(self.token_file, 'w') as f:
                json.dump({"token": token}, f)

            logger.info("Token obtido e salvo com sucesso.")
            return token

        except Exception as e:
            logger.error(f"Erro ao obter token do painel IPTV: {str(e)}")
            return None
