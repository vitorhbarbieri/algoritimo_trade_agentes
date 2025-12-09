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
    
    def __init__(self, bot_token: str = None, chat_id: str = None, orders_repo=None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID', '')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.orders_repo = orders_repo  # Para salvar mensagens quando usado diretamente
    
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
                logger.info("Notificacao Telegram enviada")
                return True
            else:
                logger.error(f"Erro Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Telegram: {e}")
            return False
    
    def send_opportunity(self, opportunity: Dict):
        """Envia notificação de oportunidade formatada."""
        if not self.is_configured():
            logger.warning("Telegram nao configurado - mensagem nao enviada")
            return False
        
        opp_type = opportunity.get('type', 'unknown')
        symbol = opportunity.get('symbol') or opportunity.get('ticker', 'N/A')
        score = opportunity.get('opportunity_score', 0)
        
        message = f"""
*Nova Oportunidade*

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
    
    def send_proposal_with_approval(self, proposal: Dict) -> bool:
        """
        Envia proposta de ordem com botões de aprovação/cancelamento.
        
        Args:
            proposal: Dicionário com dados da proposta incluindo:
                - proposal_id: ID único da proposta
                - symbol: Símbolo do ativo
                - side: BUY ou SELL
                - quantity: Quantidade
                - price: Preço
                - expected_gain: Ganho esperado (R$)
                - expected_gain_pct: Ganho esperado (%)
                - max_loss: Perda máxima (R$)
                - metadata: Metadados adicionais
        """
        if not self.is_configured():
            logger.warning("Telegram nao configurado - mensagem nao enviada")
            return False
        
        try:
            proposal_id = proposal.get('proposal_id', 'UNKNOWN')
            symbol = proposal.get('symbol', 'N/A')
            side = proposal.get('side', 'BUY')
            quantity = proposal.get('quantity', 0)
            metadata = proposal.get('metadata', {})
            
            # Extrair informações do metadata
            entry_price_unit = metadata.get('entry_price', proposal.get('price', 0))
            entry_price_total = metadata.get('entry_price_total', 0)
            if entry_price_total == 0:
                # Calcular se não estiver no metadata
                # Ajustar multiplicador baseado no tipo de instrumento
                multiplier = 100 if metadata.get('comparison_type') == 'options' else 1
                entry_price_total = entry_price_unit * quantity * multiplier
            
            exit_price_tp_unit = metadata.get('exit_price_tp', 0)
            exit_price_tp_total = metadata.get('exit_price_tp_total', 0)
            if exit_price_tp_total == 0 and exit_price_tp_unit > 0:
                exit_price_tp_total = exit_price_tp_unit * quantity * 100
            
            exit_price_sl_unit = metadata.get('exit_price_sl', 0)
            exit_price_sl_total = metadata.get('exit_price_sl_total', 0)
            if exit_price_sl_total == 0 and exit_price_sl_unit > 0:
                exit_price_sl_total = exit_price_sl_unit * quantity * 100
            
            ticket_value = metadata.get('ticket_value', 1000.0)  # Padronizado R$ 1000
            take_profit_pct = metadata.get('take_profit_pct', 0.10)
            stop_loss_pct = metadata.get('stop_loss_pct', 0.40)
            gain_value = metadata.get('gain_value', ticket_value * take_profit_pct)
            loss_value = metadata.get('loss_value', ticket_value * stop_loss_pct)
            underlying = metadata.get('underlying', 'N/A')
            strike = metadata.get('strike', 0)
            delta = metadata.get('delta', 0)
            eod_close = metadata.get('eod_close', True)
            
            # Se não tiver preços de saída calculados, calcular agora
            if exit_price_tp_unit == 0:
                exit_price_tp_unit = entry_price_unit * (1 + take_profit_pct)
                # Ajustar multiplicador baseado no tipo de instrumento
                multiplier = 100 if metadata.get('comparison_type') == 'options' else 1
                exit_price_tp_total = exit_price_tp_unit * quantity * multiplier
            
            if exit_price_sl_unit == 0:
                exit_price_sl_unit = entry_price_unit * (1 - stop_loss_pct)
                # Ajustar multiplicador baseado no tipo de instrumento
                multiplier = 100 if metadata.get('comparison_type') == 'options' else 1
                exit_price_sl_total = exit_price_sl_unit * quantity * multiplier
            
            # Determinar tipo de instrumento
            instrument_type = metadata.get('comparison_type', 'options')
            instrument_label = 'Opção' if instrument_type == 'options' else 'Ação'
            comparison_score = metadata.get('comparison_score', 0)
            
            # Formatar mensagem rica e detalhada
            # ID destacado no topo para fácil identificação
            message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*📊 NOVA PROPOSTA - DAYTRADE*
*ID: {proposal_id}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Tipo:* {instrument_label}
*Ativo:* `{symbol}`
*Ativo Base:* {underlying}
*Operação:* {side}
*Quantidade:* {quantity:.0f} {'contratos' if instrument_type == 'options' else 'ações'}

*⭐ SCORE:* {comparison_score:.2f}

*💵 VALOR DA OPERAÇÃO:*
• Ticket Padronizado: R$ {ticket_value:,.2f}

*📈 PREÇOS:*
• Preço de Entrada: R$ {entry_price_unit:.2f} (Total: R$ {entry_price_total:,.2f})
• Preço de Saída (TP): R$ {exit_price_tp_unit:.2f} (Total: R$ {exit_price_tp_total:,.2f})
• Preço de Saída (SL): R$ {exit_price_sl_unit:.2f} (Total: R$ {exit_price_sl_total:,.2f})

*💰 GANHO E PERDA (Ticket R$ {ticket_value:,.2f}):*
• Ganho Esperado: R$ {gain_value:,.2f} ({take_profit_pct*100:.1f}%)
• Perda Máxima: R$ {loss_value:,.2f} ({stop_loss_pct*100:.1f}%)

*🎯 GATILHOS DE SAÍDA:*
• Take Profit: {take_profit_pct*100:.1f}% → R$ {exit_price_tp_unit:.2f} (Total: R$ {exit_price_tp_total:,.2f})
• Stop Loss: {stop_loss_pct*100:.1f}% → R$ {exit_price_sl_unit:.2f} (Total: R$ {exit_price_sl_total:,.2f})
• Fechamento EOD: {'SIM' if eod_close else 'NÃO'} (fechamento automático no fim do dia)

*📊 DETALHES TÉCNICOS:*
"""
            
            # Adicionar detalhes técnicos
            if instrument_type == 'options':
                if strike > 0:
                    message += f"• Strike: R$ {strike:.2f}\n"
                if delta > 0:
                    message += f"• Delta: {delta:.3f}\n"
                if 'gamma' in metadata:
                    message += f"• Gamma: {metadata['gamma']:.4f}\n"
                if 'vega' in metadata:
                    message += f"• Vega: {metadata['vega']:.4f}\n"
                if 'iv' in metadata:
                    message += f"• IV: {metadata['iv']*100:.1f}%\n"
                if 'days_to_expiry' in metadata:
                    message += f"• DTE: {metadata['days_to_expiry']} dias\n"
            
            # Detalhes comuns
            if 'intraday_return' in metadata:
                message += f"• Momentum Intraday: {metadata['intraday_return']*100:.2f}%\n"
            if 'volume_ratio' in metadata:
                message += f"• Volume Ratio: {metadata['volume_ratio']:.2f}x\n"
            
            # Informação de comparação
            if comparison_score > 0:
                message += f"\n*🔍 ANÁLISE COMPARATIVA:*\n"
                message += f"• Score: {comparison_score:.2f} (maior = melhor)\n"
                if instrument_type == 'options':
                    message += f"• Escolhida: Opção (melhor que ação direta)\n"
                else:
                    message += f"• Escolhida: Ação (melhor que opção)\n"
            
            # ID simplificado destacado no início para fácil copy/paste
            message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*✅ APROVAÇÃO RÁPIDA:*

`/aprovar {proposal_id}`  ← Copie e cole
`/cancelar {proposal_id}`  ← Copie e cole

*ID:* `{proposal_id}`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            message += f"\n_Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_"
            
            # Criar botões inline
            keyboard = {
                'inline_keyboard': [
                    [
                        {'text': '✅ APROVAR', 'callback_data': f'approve_{proposal_id}'},
                        {'text': '❌ CANCELAR', 'callback_data': f'cancel_{proposal_id}'}
                    ]
                ]
            }
            
            # Enviar mensagem com botões
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'reply_markup': json.dumps(keyboard),
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Proposta enviada com botões: {proposal_id}")
                
                # Salvar mensagem enviada (se orders_repo disponível)
                if hasattr(self, 'orders_repo') and self.orders_repo:
                    try:
                        self.orders_repo.save_telegram_message(
                            message_text=message,
                            message_type='proposal',
                            title="Nova Proposta - Daytrade",
                            priority='high',
                            proposal_id=proposal_id,
                            success=True
                        )
                    except Exception as e:
                        logger.warning(f"Erro ao salvar mensagem de proposta: {e}")
                
                return True
            else:
                logger.error(f"Erro ao enviar proposta: {response.status_code} - {response.text}")
                
                # Salvar falha
                if hasattr(self, 'orders_repo') and self.orders_repo:
                    try:
                        self.orders_repo.save_telegram_message(
                            message_text=message,
                            message_type='proposal',
                            title="Nova Proposta - Daytrade",
                            priority='high',
                            proposal_id=proposal_id,
                            success=False,
                            error_message=f"{response.status_code} - {response.text}"
                        )
                    except Exception as e:
                        logger.warning(f"Erro ao salvar falha de proposta: {e}")
                
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar proposta com aprovação: {e}")
            
            # Salvar erro
            if hasattr(self, 'orders_repo') and self.orders_repo:
                try:
                    self.orders_repo.save_telegram_message(
                        message_text=str(proposal),
                        message_type='proposal',
                        title="Nova Proposta - Daytrade",
                        priority='high',
                        proposal_id=proposal.get('proposal_id', 'UNKNOWN'),
                        success=False,
                        error_message=str(e)
                    )
                except:
                    pass
            
            return False
    
    def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> bool:
        """Responde a uma callback query do Telegram."""
        try:
            url = f"{self.api_url}/answerCallbackQuery"
            payload = {
                'callback_query_id': callback_query_id,
                'text': text,
                'show_alert': show_alert
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao responder callback: {e}")
            return False
    
    def edit_message_reply_markup(self, chat_id: str, message_id: int, new_text: str = None) -> bool:
        """Atualiza mensagem após aprovação/cancelamento."""
        try:
            url = f"{self.api_url}/editMessageText"
            payload = {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': new_text,
                'parse_mode': 'Markdown'
            }
            if new_text:
                payload['text'] = new_text
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao editar mensagem: {e}")
            return False
    
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
    
    def __init__(self, config: Dict, orders_repo=None):
        self.config = config
        self.channels = []
        self.orders_repo = orders_repo  # Para salvar mensagens enviadas
        
        # Telegram
        telegram_enabled = config.get('notifications', {}).get('telegram', {}).get('enabled', False)
        if telegram_enabled:
            telegram_config = config.get('notifications', {}).get('telegram', {})
            telegram = TelegramNotifier(
                bot_token=telegram_config.get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN', ''),
                chat_id=telegram_config.get('chat_id') or os.getenv('TELEGRAM_CHAT_ID', ''),
                orders_repo=orders_repo  # Passar orders_repo para TelegramNotifier também
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
    
    def send(self, message: str, title: str = None, priority: str = 'normal', 
             message_type: str = 'other', proposal_id: str = None) -> bool:
        """Envia notificação em todos os canais configurados e salva para rastreabilidade."""
        if not self.channels:
            return False
        
        results = []
        success = False
        error_msg = None
        
        for channel_name, channel in self.channels:
            try:
                result = channel.send(message, title, priority)
                results.append(result)
                if result:
                    success = True
            except Exception as e:
                logger.error(f"Erro ao enviar via {channel_name}: {e}")
                results.append(False)
                if not error_msg:
                    error_msg = str(e)
        
        # Salvar mensagem enviada para rastreabilidade
        if self.orders_repo:
            try:
                # Determinar tipo de mensagem automaticamente se não especificado
                if message_type == 'other':
                    if title:
                        title_lower = title.lower()
                        if 'status' in title_lower or 'atualização' in title_lower:
                            message_type = 'status'
                        elif 'proposta' in title_lower or 'proposal' in title_lower:
                            message_type = 'proposal'
                        elif 'oportunidade' in title_lower or 'opportunity' in title_lower:
                            message_type = 'opportunity'
                        elif 'erro' in title_lower or 'error' in title_lower:
                            message_type = 'error'
                        elif 'kill switch' in title_lower:
                            message_type = 'kill_switch'
                        elif 'mercado aberto' in title_lower or 'market open' in title_lower:
                            message_type = 'market_open'
                        elif 'mercado fechado' in title_lower or 'market close' in title_lower:
                            message_type = 'market_close'
                        elif 'eod' in title_lower or 'fechamento' in title_lower:
                            message_type = 'eod'
                        elif 'saúde' in title_lower or 'health' in title_lower or 'captura' in title_lower:
                            message_type = 'health'
                
                self.orders_repo.save_telegram_message(
                    message_text=message,
                    message_type=message_type,
                    title=title,
                    priority=priority,
                    proposal_id=proposal_id,
                    success=success,
                    error_message=error_msg if not success else None,
                    channel='telegram' if 'telegram' in [c[0] for c in self.channels] else 'other'
                )
            except Exception as e:
                logger.warning(f"Erro ao salvar mensagem Telegram: {e}")
        
        return any(results)
    
    def notify_opportunity(self, opportunity: Dict):
        """Notifica oportunidade encontrada."""
        if not self.channels:
            logger.warning("Nenhum canal de notificacao configurado! Mensagem nao enviada.")
            return False
        
        results = []
        for channel_name, channel in self.channels:
            try:
                if hasattr(channel, 'send_opportunity'):
                    result = channel.send_opportunity(opportunity)
                    results.append(result)
                    logger.info(f"Notificacao enviada via {channel_name}: {result}")
                elif hasattr(channel, 'notify_opportunity_found'):
                    result = channel.notify_opportunity_found(opportunity)
                    results.append(result)
                    logger.info(f"Notificacao enviada via {channel_name}: {result}")
                else:
                    # Fallback genérico
                    opp_type = opportunity.get('type', 'unknown')
                    symbol = opportunity.get('symbol') or opportunity.get('ticker', 'N/A')
                    message = f"Nova oportunidade: {opp_type} - {symbol}"
                    result = channel.send(message, title="Oportunidade", priority='high')
                    results.append(result)
                    logger.info(f"Notificacao enviada via {channel_name}: {result}")
            except Exception as e:
                logger.error(f"Erro ao notificar oportunidade via {channel_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                results.append(False)
        
        return any(results)
    
    def notify_error(self, error_type: str, error_message: str, details: Dict = None):
        """Notifica erro."""
        success = False
        for channel_name, channel in self.channels:
            try:
                if hasattr(channel, 'send_error'):
                    result = channel.send_error(error_type, error_message)
                    if result:
                        success = True
                elif hasattr(channel, 'notify_error'):
                    result = channel.notify_error(error_type, error_message, details)
                    if result:
                        success = True
                else:
                    message = f"Erro: {error_type}\n{error_message}"
                    result = channel.send(message, title="Erro no Sistema", priority='critical')
                    if result:
                        success = True
            except Exception as e:
                logger.error(f"Erro ao notificar erro via {channel_name}: {e}")
        
        # Salvar mensagem de erro
        if self.orders_repo:
            try:
                message_text = f"Erro: {error_type}\n{error_message}"
                if details:
                    message_text += f"\nDetalhes: {json.dumps(details)}"
                self.orders_repo.save_telegram_message(
                    message_text=message_text,
                    message_type='error',
                    title="Erro no Sistema",
                    priority='critical',
                    success=success
                )
            except Exception as e:
                logger.warning(f"Erro ao salvar mensagem de erro: {e}")
    
    def notify_kill_switch(self, reason: str, nav_loss: float):
        """Notifica kill switch."""
        success = False
        for channel_name, channel in self.channels:
            try:
                if hasattr(channel, 'send_kill_switch'):
                    result = channel.send_kill_switch(reason, nav_loss)
                    if result:
                        success = True
                elif hasattr(channel, 'notify_kill_switch'):
                    result = channel.notify_kill_switch(reason, nav_loss)
                    if result:
                        success = True
                else:
                    message = f"KILL SWITCH ATIVADO!\nMotivo: {reason}\nPerda: {nav_loss:.2%}"
                    result = channel.send(message, title="KILL SWITCH", priority='critical')
                    if result:
                        success = True
            except Exception as e:
                logger.error(f"Erro ao notificar kill switch via {channel_name}: {e}")
        
        # Salvar mensagem de kill switch
        if self.orders_repo:
            try:
                message_text = f"KILL SWITCH ATIVADO!\nMotivo: {reason}\nPerda: {nav_loss:.2%}"
                self.orders_repo.save_telegram_message(
                    message_text=message_text,
                    message_type='kill_switch',
                    title="KILL SWITCH",
                    priority='critical',
                    success=success
                )
            except Exception as e:
                logger.warning(f"Erro ao salvar mensagem de kill switch: {e}")

