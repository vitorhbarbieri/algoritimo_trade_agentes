"""
Sistema de Notificações Modular
Suporta múltiplos canais: Telegram, Discord, Email, SMS (via Twilio)
"""

import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationChannel:
    """Interface base para canais de notificação."""
    
    def send(self, message: str, title: str = None, priority: str = 'normal') -> bool:
        """Envia notificação."""
        raise NotImplementedError
    
    def is_configured(self) -> bool:
        """Verifica se está configurado."""
        raise NotImplementedError


class TelegramNotifier(NotificationChannel):
    """Notificador via Telegram Bot."""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID', '')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)
    
    def send(self, message: str, title: str = None, priority: str = 'normal') -> bool:
        if not self.is_configured():
            logger.warning("Telegram não configurado")
            return False
        
        try:
            # Formatar mensagem
            if title:
                full_message = f"*{title}*\n\n{message}"
            else:
                full_message = message
            
            # Emojis baseados na prioridade
            emoji_map = {
                'critical': '🛑',
                'high': '⚡',
                'normal': '📊',
                'low': 'ℹ️'
            }
            emoji = emoji_map.get(priority, '📊')
            full_message = f"{emoji} {full_message}"
            
            # Enviar via API do Telegram
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': full_message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Notificação Telegram enviada")
                return True
            else:
                logger.error(f"❌ Erro Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Telegram: {e}")
            return False
    
    def send_opportunity(self, opportunity: Dict):
        """Envia notificação de oportunidade formatada."""
        opp_type = opportunity.get('type', 'unknown')
        symbol = opportunity.get('symbol') or opportunity.get('ticker', 'N/A')
        score = opportunity.get('opportunity_score', 0)
        
        message = f"""
*🎯 Nova Oportunidade*

*Tipo:* {opp_type.replace('_', ' ').title()}
*Ativo:* `{symbol}`
*Score:* {score:.2f}

*Detalhes:*
"""
        
        # Adicionar detalhes específicos
        if 'strike' in opportunity:
            message += f"Strike: {opportunity['strike']}\n"
        if 'delta' in opportunity:
            message += f"Delta: {opportunity['delta']:.3f}\n"
        if 'intraday_return' in opportunity:
            message += f"Momentum: {opportunity['intraday_return']*100:.2f}%\n"
        if 'volume_ratio' in opportunity:
            message += f"Volume Ratio: {opportunity['volume_ratio']:.2f}x\n"
        
        message += f"\n_Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_"
        
        return self.send(message, title="Oportunidade de Trading", priority='high')
    
    def send_error(self, error_type: str, error_message: str):
        """Envia notificação de erro."""
        message = f"""
*⚠️ Erro no Sistema*

*Tipo:* {error_type}
*Mensagem:* {error_message}

_Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_
"""
        return self.send(message, title="Erro no Sistema", priority='critical')
    
    def send_kill_switch(self, reason: str, nav_loss: float):
        """Envia notificação de kill switch."""
        message = f"""
*🛑 KILL SWITCH ATIVADO*

*Motivo:* {reason}
*Perda NAV:* {nav_loss:.2%}

Todas as operações foram interrompidas automaticamente.

_Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_
"""
        return self.send(message, title="KILL SWITCH", priority='critical')


class DiscordNotifier(NotificationChannel):
    """Notificador via Discord Webhook."""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL', '')
    
    def is_configured(self) -> bool:
        return bool(self.webhook_url)
    
    def send(self, message: str, title: str = None, priority: str = 'normal') -> bool:
        if not self.is_configured():
            logger.warning("Discord não configurado")
            return False
        
        try:
            # Cores baseadas na prioridade
            color_map = {
                'critical': 15158332,  # Vermelho
                'high': 16776960,       # Amarelo
                'normal': 3447003,      # Azul
                'low': 3066993          # Verde
            }
            color = color_map.get(priority, 3447003)
            
            # Criar embed
            embed = {
                'title': title or 'Notificação do Sistema',
                'description': message,
                'color': color,
                'timestamp': datetime.now().isoformat(),
                'footer': {
                    'text': 'Sistema de Trading Automatizado'
                }
            }
            
            payload = {
                'embeds': [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info("✅ Notificação Discord enviada")
                return True
            else:
                logger.error(f"❌ Erro Discord: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Discord: {e}")
            return False
    
    def send_opportunity(self, opportunity: Dict):
        """Envia notificação de oportunidade formatada."""
        opp_type = opportunity.get('type', 'unknown')
        symbol = opportunity.get('symbol') or opportunity.get('ticker', 'N/A')
        score = opportunity.get('opportunity_score', 0)
        
        description = f"**Tipo:** {opp_type.replace('_', ' ').title()}\n"
        description += f"**Ativo:** {symbol}\n"
        description += f"**Score:** {score:.2f}\n\n"
        
        if 'strike' in opportunity:
            description += f"**Strike:** {opportunity['strike']}\n"
        if 'delta' in opportunity:
            description += f"**Delta:** {opportunity['delta']:.3f}\n"
        if 'intraday_return' in opportunity:
            description += f"**Momentum:** {opportunity['intraday_return']*100:.2f}%\n"
        
        embed = {
            'title': '🎯 Nova Oportunidade de Trading',
            'description': description,
            'color': 16776960,  # Amarelo
            'timestamp': datetime.now().isoformat()
        }
        
        payload = {'embeds': [embed]}
        response = requests.post(self.webhook_url, json=payload, timeout=10)
        return response.status_code == 204


class UnifiedNotifier:
    """Notificador unificado que usa múltiplos canais."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.channels = []
        
        # Telegram
        telegram_enabled = config.get('notifications', {}).get('telegram', {}).get('enabled', False)
        if telegram_enabled:
            telegram_config = config.get('notifications', {}).get('telegram', {})
            telegram = TelegramNotifier(
                bot_token=telegram_config.get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN', ''),
                chat_id=telegram_config.get('chat_id') or os.getenv('TELEGRAM_CHAT_ID', '')
            )
            if telegram.is_configured():
                self.channels.append(('telegram', telegram))
                logger.info("✅ Telegram configurado")
        
        # Discord
        discord_enabled = config.get('notifications', {}).get('discord', {}).get('enabled', False)
        if discord_enabled:
            discord_config = config.get('notifications', {}).get('discord', {})
            discord = DiscordNotifier(
                webhook_url=discord_config.get('webhook_url') or os.getenv('DISCORD_WEBHOOK_URL', '')
            )
            if discord.is_configured():
                self.channels.append(('discord', discord))
                logger.info("✅ Discord configurado")
        
        # Email (opcional, via variáveis de ambiente)
        email_enabled = config.get('notifications', {}).get('email', {}).get('enabled', False)
        if email_enabled:
            try:
                from .email_notifier import EmailNotifier
                email_config = config.get('notifications', {}).get('email', {})
                # Usar variáveis de ambiente se não estiverem no config
                email_config.setdefault('email_remetente', os.getenv('EMAIL_REMETENTE', ''))
                email_config.setdefault('email_senha', os.getenv('EMAIL_SENHA', ''))
                email_config.setdefault('email_destinatario', os.getenv('EMAIL_DESTINATARIO', ''))
                
                email = EmailNotifier(email_config)
                if email.enabled and email.remetente and email.senha:
                    self.channels.append(('email', email))
                    logger.info("✅ Email configurado")
            except ImportError:
                logger.warning("EmailNotifier não disponível")
        
        if not self.channels:
            logger.warning("⚠️ Nenhum canal de notificação configurado!")
    
    def send(self, message: str, title: str = None, priority: str = 'normal') -> bool:
        """Envia notificação em todos os canais configurados."""
        if not self.channels:
            return False
        
        results = []
        for channel_name, channel in self.channels:
            try:
                result = channel.send(message, title, priority)
                results.append(result)
            except Exception as e:
                logger.error(f"Erro ao enviar via {channel_name}: {e}")
                results.append(False)
        
        return any(results)
    
    def notify_opportunity(self, opportunity: Dict):
        """Notifica oportunidade encontrada."""
        for channel_name, channel in self.channels:
            try:
                if hasattr(channel, 'send_opportunity'):
                    channel.send_opportunity(opportunity)
                elif hasattr(channel, 'notify_opportunity_found'):
                    channel.notify_opportunity_found(opportunity)
                else:
                    # Fallback genérico
                    opp_type = opportunity.get('type', 'unknown')
                    symbol = opportunity.get('symbol') or opportunity.get('ticker', 'N/A')
                    message = f"Nova oportunidade: {opp_type} - {symbol}"
                    channel.send(message, title="Oportunidade", priority='high')
            except Exception as e:
                logger.error(f"Erro ao notificar oportunidade via {channel_name}: {e}")
    
    def notify_error(self, error_type: str, error_message: str, details: Dict = None):
        """Notifica erro."""
        for channel_name, channel in self.channels:
            try:
                if hasattr(channel, 'send_error'):
                    channel.send_error(error_type, error_message)
                elif hasattr(channel, 'notify_error'):
                    channel.notify_error(error_type, error_message, details)
                else:
                    message = f"Erro: {error_type}\n{error_message}"
                    channel.send(message, title="Erro no Sistema", priority='critical')
            except Exception as e:
                logger.error(f"Erro ao notificar erro via {channel_name}: {e}")
    
    def notify_kill_switch(self, reason: str, nav_loss: float):
        """Notifica kill switch."""
        for channel_name, channel in self.channels:
            try:
                if hasattr(channel, 'send_kill_switch'):
                    channel.send_kill_switch(reason, nav_loss)
                elif hasattr(channel, 'notify_kill_switch'):
                    channel.notify_kill_switch(reason, nav_loss)
                else:
                    message = f"KILL SWITCH ATIVADO!\nMotivo: {reason}\nPerda: {nav_loss:.2%}"
                    channel.send(message, title="KILL SWITCH", priority='critical')
            except Exception as e:
                logger.error(f"Erro ao notificar kill switch via {channel_name}: {e}")

