"""
Sistema de Polling do Telegram para processar comandos e aprovações.
Alternativa simples ao webhook - roda polling periódico.
"""

import requests
import json
import time
import logging
from typing import Dict, Optional
from datetime import datetime
import sqlite3
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents_orders.db")


class TelegramPolling:
    """Processa comandos do Telegram via polling (sem webhook)."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
        
    def get_updates(self) -> list:
        """Busca novas mensagens do Telegram."""
        try:
            url = f"{self.api_url}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 10,
                'allowed_updates': ['message', 'callback_query']
            }
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates = data.get('result', [])
                    if updates:
                        self.last_update_id = updates[-1]['update_id']
                    return updates
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar updates do Telegram: {e}")
            return []
    
    def process_message(self, message: Dict) -> bool:
        """Processa uma mensagem recebida."""
        try:
            chat_id = str(message.get('chat', {}).get('id', ''))
            
            # Só processar mensagens do chat_id configurado
            if chat_id != self.chat_id:
                return False
            
            text = message.get('text', '').strip()
            if not text:
                return False
            
            # Processar comandos
            if text.startswith('/aprovar') or text.startswith('/approve'):
                # Formato: /aprovar PROPOSAL_ID ou /aprovar
                parts = text.split()
                if len(parts) >= 2:
                    proposal_id = parts[1]
                    return self.approve_proposal(proposal_id, chat_id)
                else:
                    # Tentar pegar proposal_id da mensagem respondida
                    reply_to = message.get('reply_to_message')
                    if reply_to:
                        # Procurar proposal_id no texto da mensagem original
                        original_text = reply_to.get('text', '')
                        proposal_id = self._extract_proposal_id(original_text)
                        if proposal_id:
                            return self.approve_proposal(proposal_id, chat_id)
                    self.send_message("Por favor, informe o ID da proposta: /aprovar PROPOSAL_ID")
                    return False
            
            elif text.startswith('/cancelar') or text.startswith('/cancel'):
                parts = text.split()
                if len(parts) >= 2:
                    proposal_id = parts[1]
                    return self.cancel_proposal(proposal_id, chat_id)
                else:
                    reply_to = message.get('reply_to_message')
                    if reply_to:
                        original_text = reply_to.get('text', '')
                        proposal_id = self._extract_proposal_id(original_text)
                        if proposal_id:
                            return self.cancel_proposal(proposal_id, chat_id)
                    self.send_message("Por favor, informe o ID da proposta: /cancelar PROPOSAL_ID")
                    return False
            
            elif text.upper() in ['SIM', 'YES', 'OK', 'APROVAR', 'APROVO']:
                # Resposta simples: SIM para aprovar
                reply_to = message.get('reply_to_message')
                if reply_to:
                    original_text = reply_to.get('text', '')
                    proposal_id = self._extract_proposal_id(original_text)
                    if proposal_id:
                        return self.approve_proposal(proposal_id, chat_id)
            
            elif text.upper() in ['NAO', 'NO', 'CANCELAR', 'CANCELO']:
                # Resposta simples: NÃO para cancelar
                reply_to = message.get('reply_to_message')
                if reply_to:
                    original_text = reply_to.get('text', '')
                    proposal_id = self._extract_proposal_id(original_text)
                    if proposal_id:
                        return self.cancel_proposal(proposal_id, chat_id)
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            return False
    
    def process_callback_query(self, callback_query: Dict) -> bool:
        """Processa callback de botão inline."""
        try:
            callback_id = callback_query.get('id')
            callback_data = callback_query.get('data', '')
            message = callback_query.get('message', {})
            chat_id = str(message.get('chat', {}).get('id', ''))
            
            if chat_id != self.chat_id:
                return False
            
            # Processar callback_data
            if callback_data.startswith('approve_'):
                proposal_id = callback_data.replace('approve_', '')
                result = self.approve_proposal(proposal_id, chat_id)
                self.answer_callback_query(callback_id, "✅ Proposta APROVADA!" if result else "❌ Erro ao aprovar")
                return result
            elif callback_data.startswith('cancel_'):
                proposal_id = callback_data.replace('cancel_', '')
                result = self.cancel_proposal(proposal_id, chat_id)
                self.answer_callback_query(callback_id, "❌ Proposta CANCELADA" if result else "❌ Erro ao cancelar")
                return result
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao processar callback: {e}")
            return False
    
    def _extract_proposal_id(self, text: str) -> Optional[str]:
        """Extrai proposal_id do texto da mensagem."""
        # Procurar por padrão: *Proposta ID:* `PROPOSAL_ID`
        import re
        match = re.search(r'Proposta ID[:\*]*\s*`?([A-Z0-9\-_]+)`?', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Procurar por padrão: DAYOPT-...
        match = re.search(r'(DAYOPT-[A-Z0-9\.]+-[0-9\.]+-[0-9]+)', text)
        if match:
            return match.group(1)
        
        return None
    
    def approve_proposal(self, proposal_id: str, chat_id: str) -> bool:
        """Aprova uma proposta."""
        try:
            # Verificar se proposta existe
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,))
            proposal = cursor.fetchone()
            
            if not proposal:
                self.send_message(f"❌ Proposta `{proposal_id}` não encontrada.")
                conn.close()
                return False
            
            # Criar tabela de aprovações se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proposal_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('APPROVE', 'CANCEL')),
                    timestamp TEXT NOT NULL,
                    telegram_chat_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                )
            """)
            
            # Salvar aprovação
            cursor.execute("""
                INSERT INTO proposal_approvals 
                (proposal_id, action, timestamp, telegram_chat_id)
                VALUES (?, ?, ?, ?)
            """, (
                proposal_id,
                'APPROVE',
                datetime.now().isoformat(),
                chat_id
            ))
            
            # Atualizar status da proposta para 'aprovada'
            try:
                from src.orders_repository import OrdersRepository
                repo = OrdersRepository()
                repo.update_proposal_status(proposal_id, 'aprovada')
            except Exception as e:
                logger.error(f"Erro ao atualizar status da proposta: {e}")
            conn.commit()
            conn.close()
            
            # Atualizar status da proposta para 'aprovada'
            try:
                from src.orders_repository import OrdersRepository
                repo = OrdersRepository()
                repo.update_proposal_status(proposal_id, 'aprovada')
            except Exception as e:
                logger.error(f"Erro ao atualizar status da proposta: {e}")
            
            # Enviar confirmação
            self.send_message(
                f"✅ *Proposta APROVADA!*\n\n"
                f"Proposta ID: `{proposal_id}`\n"
                f"A ordem será processada pelo sistema.\n\n"
                f"_Aprovado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_"
            )
            
            logger.info(f"Proposta {proposal_id} aprovada via Telegram")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aprovar proposta: {e}")
            self.send_message(f"❌ Erro ao aprovar proposta: {str(e)}")
            return False
    
    def cancel_proposal(self, proposal_id: str, chat_id: str) -> bool:
        """Cancela uma proposta."""
        try:
            # Verificar se proposta existe
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,))
            proposal = cursor.fetchone()
            
            if not proposal:
                self.send_message(f"❌ Proposta `{proposal_id}` não encontrada.")
                conn.close()
                return False
            
            # Criar tabela de aprovações se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proposal_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('APPROVE', 'CANCEL')),
                    timestamp TEXT NOT NULL,
                    telegram_chat_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                )
            """)
            
            # Salvar cancelamento
            cursor.execute("""
                INSERT INTO proposal_approvals 
                (proposal_id, action, timestamp, telegram_chat_id)
                VALUES (?, ?, ?, ?)
            """, (
                proposal_id,
                'CANCEL',
                datetime.now().isoformat(),
                chat_id
            ))
            
            # Atualizar status da proposta para 'cancelada'
            try:
                from src.orders_repository import OrdersRepository
                repo = OrdersRepository()
                repo.update_proposal_status(proposal_id, 'cancelada')
            except Exception as e:
                logger.error(f"Erro ao atualizar status da proposta: {e}")
            conn.commit()
            conn.close()
            
            # Atualizar status da proposta para 'cancelada'
            try:
                from src.orders_repository import OrdersRepository
                repo = OrdersRepository()
                repo.update_proposal_status(proposal_id, 'cancelada')
            except Exception as e:
                logger.error(f"Erro ao atualizar status da proposta: {e}")
            
            # Enviar confirmação
            self.send_message(
                f"❌ *Proposta CANCELADA*\n\n"
                f"Proposta ID: `{proposal_id}`\n"
                f"A ordem não será executada.\n\n"
                f"_Cancelado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_"
            )
            
            logger.info(f"Proposta {proposal_id} cancelada via Telegram")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao cancelar proposta: {e}")
            self.send_message(f"❌ Erro ao cancelar proposta: {str(e)}")
            return False
    
    def send_message(self, text: str, parse_mode: str = 'Markdown') -> bool:
        """Envia mensagem para o chat."""
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return False
    
    def answer_callback_query(self, callback_id: str, text: str, show_alert: bool = False) -> bool:
        """Responde a uma callback query."""
        try:
            url = f"{self.api_url}/answerCallbackQuery"
            payload = {
                'callback_query_id': callback_id,
                'text': text,
                'show_alert': show_alert
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao responder callback: {e}")
            return False
    
    def start_polling(self, interval: int = 5):
        """Inicia polling contínuo."""
        logger.info(f"Iniciando polling do Telegram (intervalo: {interval}s)")
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    # Processar mensagens
                    if 'message' in update:
                        self.process_message(update['message'])
                    
                    # Processar callbacks de botões
                    if 'callback_query' in update:
                        self.process_callback_query(update['callback_query'])
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Polling interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro no polling: {e}")
                time.sleep(interval)


def start_telegram_polling(config: Dict):
    """Função auxiliar para iniciar polling."""
    telegram_config = config.get('notifications', {}).get('telegram', {})
    bot_token = telegram_config.get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = telegram_config.get('chat_id') or os.getenv('TELEGRAM_CHAT_ID', '')
    
    if not bot_token or not chat_id:
        logger.warning("Telegram não configurado - polling não iniciado")
        return None
    
    polling = TelegramPolling(bot_token, chat_id)
    return polling

