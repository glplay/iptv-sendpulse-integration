#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integracao_iptv_sendpulse.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IPTVSendPulseIntegration:
    def __init__(self, iptv_api_url, sendpulse_api_url, sendpulse_client_id, sendpulse_client_secret):
        """
        Inicializa a integração entre o painel IPTV e o SendPulse WhatsApp.
        
        Args:
            iptv_api_url (str): URL da API do painel IPTV
            sendpulse_api_url (str): URL base da API do SendPulse
            sendpulse_client_id (str): Client ID para autenticação no SendPulse
            sendpulse_client_secret (str): Client Secret para autenticação no SendPulse
        """
        self.iptv_api_url = iptv_api_url
        self.sendpulse_api_url = sendpulse_api_url
        self.sendpulse_client_id = sendpulse_client_id
        self.sendpulse_client_secret = sendpulse_client_secret
        self.sendpulse_token = None
        
    def obter_token_sendpulse(self):
        """
        Obtém o token de autenticação do SendPulse usando client_credentials.
        
        Returns:
            str: Token de acesso ou None em caso de falha
        """
        try:
            url = f"{self.sendpulse_api_url}/oauth/access_token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.sendpulse_client_id,
                "client_secret": self.sendpulse_client_secret
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.sendpulse_token = data.get("access_token")
            logger.info("Token do SendPulse obtido com sucesso")
            return self.sendpulse_token
        except Exception as e:
            logger.error(f"Erro ao obter token do SendPulse: {str(e)}")
            return None
    
    def criar_usuario_teste_iptv(self, ultimos_digitos_cliente):
        """
        Cria um usuário de teste no painel IPTV.
        
        Args:
            ultimos_digitos_cliente (str): Os 4 últimos dígitos do número do cliente
            
        Returns:
            dict: Dados do usuário criado (username, password, exp_date) ou None em caso de falha
        """
        try:
            url = self.iptv_api_url
            
            # Payload conforme capturado no DevTools
            payload = {
                "notes": ultimos_digitos_cliente,
                "package_p2p": "64399dca5ea59e8a1de2b083",
                "krator_package": "1",
                "package_iptv": 95,
                "testDuration": 4  # Duração do teste em horas
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extrair informações relevantes da resposta
            usuario_info = {
                "username": data.get("username"),
                "password": data.get("password"),
                "exp_date": data.get("exp_date")
            }
            
            logger.info(f"Usuário de teste criado com sucesso: {usuario_info['username']}")
            return usuario_info
        except Exception as e:
            logger.error(f"Erro ao criar usuário de teste IPTV: {str(e)}")
            return None
    
    def enviar_credenciais_whatsapp(self, numero_telefone, usuario_info):
        """
        Envia as credenciais do usuário de teste via WhatsApp usando a API do SendPulse.
        
        Args:
            numero_telefone (str): Número de telefone do cliente (com código do país)
            usuario_info (dict): Informações do usuário (username, password, exp_date)
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        if not self.sendpulse_token:
            self.obter_token_sendpulse()
            if not self.sendpulse_token:
                return False
        
        try:
            url = f"{self.sendpulse_api_url}/whatsapp/contacts/sendByPhone"
            
            # Formatar a data de expiração para melhor legibilidade
            exp_date = usuario_info.get("exp_date", "")
            if exp_date:
                try:
                    # Converter para objeto datetime e formatar
                    exp_datetime = datetime.fromisoformat(exp_date.replace("Z", "+00:00"))
                    exp_date_formatada = exp_datetime.strftime("%d/%m/%Y %H:%M")
                except:
                    exp_date_formatada = exp_date
            
            # Montar a mensagem com as credenciais
            mensagem = (
                f"*Suas credenciais de teste IPTV*\n\n"
                f"Usuário: *{usuario_info.get('username', '')}*\n"
                f"Senha: *{usuario_info.get('password', '')}*\n"
                f"Expira em: {exp_date_formatada}\n\n"
                f"Obrigado por testar nosso serviço!"
            )
            
            headers = {
                "Authorization": f"Bearer {self.sendpulse_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "phone": numero_telefone,
                "message": mensagem
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Credenciais enviadas com sucesso para o número {numero_telefone}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar credenciais via WhatsApp: {str(e)}")
            return False
    
    def processar_solicitacao_teste(self, numero_telefone):
        """
        Processa uma solicitação completa de teste: extrai os últimos 4 dígitos do número,
        cria o usuário e envia as credenciais.
        
        Args:
            numero_telefone (str): Número de telefone do cliente (com código do país)
            
        Returns:
            dict: Resultado da operação com status e mensagem
        """
        # Extrair os 4 últimos dígitos do número de telefone
        ultimos_digitos = numero_telefone[-4:]
        logger.info(f"Extraindo os 4 últimos dígitos do número: {ultimos_digitos}")
        
        # Criar usuário de teste
        usuario_info = self.criar_usuario_teste_iptv(ultimos_digitos)
        if not usuario_info:
            return {
                "sucesso": False,
                "mensagem": "Falha ao criar usuário de teste IPTV"
            }
        
        # Enviar credenciais via WhatsApp
        envio_sucesso = self.enviar_credenciais_whatsapp(numero_telefone, usuario_info)
        if not envio_sucesso:
            return {
                "sucesso": False,
                "mensagem": "Usuário criado, mas falha ao enviar credenciais via WhatsApp",
                "usuario_info": usuario_info
            }
        
        return {
            "sucesso": True,
            "mensagem": "Usuário criado e credenciais enviadas com sucesso",
            "usuario_info": usuario_info
        }
