#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema de Notificações por Email.
Envia emails quando encontra oportunidades, assimetrias ou erros.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sistema de notificações por email."""

    def __init__(self, config: Dict):
        self.config = config
        self.destinatario = config.get('email_destinatario', 'vitorh.barbieri@gmail.com')
        self.remetente = config.get('email_remetente', os.getenv('EMAIL_REMETENTE', ''))
        self.senha = config.get('email_senha', os.getenv('EMAIL_SENHA', ''))
        self.smtp_server = config.get('email_smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('email_smtp_port', 587)
        self.enabled = config.get('email_notifications_enabled', True)
        
        # Histórico de emails enviados (para evitar spam)
        self.last_email_time = {}
        self.email_cooldown = config.get('email_cooldown_seconds', 300)  # 5 minutos
        
    def _can_send_email(self, event_type: str) -> bool:
        """Verifica se pode enviar email (cooldown)."""
        if not self.enabled:
            return False
            
        if not self.remetente or not self.senha:
            logger.warning("Email não configurado. Configure email_remetente e email_senha no config.json")
            return False
            
        now = datetime.now()
        last_time = self.last_email_time.get(event_type)
        
        if last_time:
            elapsed = (now - last_time).total_seconds()
            if elapsed < self.email_cooldown:
                return False
                
        self.last_email_time[event_type] = now
        return True
    
    def _send_email(self, subject: str, body_html: str, body_text: str = None):
        """Envia email."""
        if not self._can_send_email('general'):
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.remetente
            msg['To'] = self.destinatario
            msg['Subject'] = subject
            
            # Versão texto
            if body_text:
                part_text = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(part_text)
            
            # Versão HTML
            part_html = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part_html)
            
            # Enviar
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.remetente, self.senha)
            server.sendmail(self.remetente, self.destinatario, msg.as_string())
            server.quit()
            
            logger.info(f"✅ Email enviado: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {e}")
            return False
    
    def notify_opportunity_found(self, opportunity: Dict):
        """Notifica quando encontra uma oportunidade."""
        if not self._can_send_email('opportunity'):
            return
            
        opp_type = opportunity.get('type', 'unknown')
        symbol = opportunity.get('symbol') or opportunity.get('ticker', 'N/A')
        score = opportunity.get('opportunity_score', 0)
        
        subject = f"🎯 Oportunidade Encontrada: {opp_type.upper()} - {symbol}"
        
        # Template HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .opportunity {{ background-color: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .metric {{ margin: 5px 0; }}
                .score {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
                .footer {{ background-color: #f5f5f5; padding: 10px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Nova Oportunidade de Trading</h1>
            </div>
            <div class="content">
                <div class="opportunity">
                    <h2>Tipo: {opp_type.replace('_', ' ').title()}</h2>
                    <div class="metric"><strong>Ativo:</strong> {symbol}</div>
                    <div class="metric"><strong>Score:</strong> <span class="score">{score:.2f}</span></div>
                    <div class="metric"><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
                </div>
                
                <h3>Detalhes:</h3>
                <pre>{json.dumps(opportunity, indent=2, ensure_ascii=False)}</pre>
                
                <p><strong>Próximos Passos:</strong></p>
                <ul>
                    <li>Acesse o Dashboard para ver mais detalhes</li>
                    <li>O sistema gerará propostas automaticamente</li>
                    <li>RiskAgent avaliará e aprovará/rejeitará</li>
                </ul>
            </div>
            <div class="footer">
                Sistema de Trading Automatizado<br>
                {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            </div>
        </body>
        </html>
        """
        
        # Versão texto
        text = f"""
Nova Oportunidade de Trading

Tipo: {opp_type.replace('_', ' ').title()}
Ativo: {symbol}
Score: {score:.2f}
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Detalhes:
{json.dumps(opportunity, indent=2, ensure_ascii=False)}

Acesse o Dashboard para mais informações.
        """
        
        self._send_email(subject, html, text)
    
    def notify_multiple_opportunities(self, opportunities: List[Dict]):
        """Notifica múltiplas oportunidades encontradas."""
        if not opportunities or not self._can_send_email('opportunities'):
            return
            
        subject = f"🎯 {len(opportunities)} Oportunidades Encontradas"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .opportunity {{ background-color: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #4CAF50; }}
                .metric {{ margin: 5px 0; }}
                .score {{ font-weight: bold; color: #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 {len(opportunities)} Oportunidades Encontradas</h1>
            </div>
            <div class="content">
        """
        
        for i, opp in enumerate(opportunities[:10], 1):  # Limitar a 10
            opp_type = opp.get('type', 'unknown')
            symbol = opp.get('symbol') or opp.get('ticker', 'N/A')
            score = opp.get('opportunity_score', 0)
            
            html += f"""
                <div class="opportunity">
                    <h3>#{i} - {opp_type.replace('_', ' ').title()}</h3>
                    <div class="metric"><strong>Ativo:</strong> {symbol}</div>
                    <div class="metric"><strong>Score:</strong> <span class="score">{score:.2f}</span></div>
                </div>
            """
        
        if len(opportunities) > 10:
            html += f"<p><em>... e mais {len(opportunities) - 10} oportunidades</em></p>"
        
        html += f"""
                <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <p>Acesse o Dashboard para ver todos os detalhes.</p>
            </div>
        </body>
        </html>
        """
        
        self._send_email(subject, html)
    
    def notify_error(self, error_type: str, error_message: str, details: Dict = None):
        """Notifica quando ocorre um erro."""
        if not self._can_send_email('error'):
            return
            
        subject = f"⚠️ Erro no Sistema: {error_type}"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .error {{ background-color: #ffebee; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #f44336; }}
                .details {{ background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ Erro no Sistema</h1>
            </div>
            <div class="content">
                <div class="error">
                    <h2>Tipo: {error_type}</h2>
                    <p><strong>Mensagem:</strong> {error_message}</p>
                    <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                {f'<div class="details"><h3>Detalhes:</h3><pre>{json.dumps(details, indent=2, ensure_ascii=False)}</pre></div>' if details else ''}
                
                <p><strong>Ação Recomendada:</strong></p>
                <ul>
                    <li>Verifique os logs do sistema</li>
                    <li>Acesse o Dashboard para status atual</li>
                    <li>Verifique se o sistema continua funcionando</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        self._send_email(subject, html)
    
    def notify_risk_event(self, event_type: str, message: str, details: Dict = None):
        """Notifica eventos de risco importantes."""
        if not self._can_send_email('risk'):
            return
            
        subject = f"🛡️ Evento de Risco: {event_type}"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .event {{ background-color: #fff3e0; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #FF9800; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ Evento de Risco</h1>
            </div>
            <div class="content">
                <div class="event">
                    <h2>{event_type}</h2>
                    <p>{message}</p>
                    <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    {f'<pre>{json.dumps(details, indent=2, ensure_ascii=False)}</pre>' if details else ''}
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(subject, html)
    
    def notify_kill_switch(self, reason: str, nav_loss: float):
        """Notifica quando kill switch é ativado."""
        subject = "🛑 KILL SWITCH ATIVADO!"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert {{ background-color: #ffebee; padding: 20px; margin: 10px 0; border-radius: 5px; border: 2px solid #d32f2f; text-align: center; }}
                .loss {{ font-size: 32px; font-weight: bold; color: #d32f2f; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛑 KILL SWITCH ATIVADO</h1>
            </div>
            <div class="content">
                <div class="alert">
                    <h2>ATENÇÃO: Sistema Parado por Segurança</h2>
                    <p class="loss">Perda: {nav_loss:.2%}</p>
                    <p><strong>Motivo:</strong> {reason}</p>
                    <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p><strong>Ação:</strong> Todas as operações foram interrompidas automaticamente.</p>
                </div>
                <p><strong>Próximos Passos:</strong></p>
                <ul>
                    <li>Verifique o portfólio no Dashboard</li>
                    <li>Analise as posições abertas</li>
                    <li>Reavalie as estratégias</li>
                    <li>Reinicie o sistema manualmente quando apropriado</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        self._send_email(subject, html)
    
    def notify_daily_summary(self, summary: Dict):
        """Notifica resumo diário."""
        if not self._can_send_email('daily'):
            return
            
        subject = f"📊 Resumo Diário - {datetime.now().strftime('%d/%m/%Y')}"
        
        opportunities_count = summary.get('opportunities_found', 0)
        proposals_count = summary.get('proposals_generated', 0)
        approved_count = summary.get('proposals_approved', 0)
        rejected_count = summary.get('proposals_rejected', 0)
        nav = summary.get('nav', 0)
        nav_change = summary.get('nav_change', 0)
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .metric {{ background-color: #f0f0f0; padding: 15px; margin: 10px 5px; border-radius: 5px; display: inline-block; min-width: 200px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
                .positive {{ color: #4CAF50; }}
                .negative {{ color: #f44336; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Resumo Diário</h1>
                <p>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            <div class="content">
                <div class="metric">
                    <div>Oportunidades Encontradas</div>
                    <div class="metric-value">{opportunities_count}</div>
                </div>
                <div class="metric">
                    <div>Propostas Geradas</div>
                    <div class="metric-value">{proposals_count}</div>
                </div>
                <div class="metric">
                    <div>Propostas Aprovadas</div>
                    <div class="metric-value positive">{approved_count}</div>
                </div>
                <div class="metric">
                    <div>Propostas Rejeitadas</div>
                    <div class="metric-value negative">{rejected_count}</div>
                </div>
                <div class="metric">
                    <div>NAV Atual</div>
                    <div class="metric-value">R$ {nav:,.2f}</div>
                </div>
                <div class="metric">
                    <div>Variação do NAV</div>
                    <div class="metric-value {'positive' if nav_change >= 0 else 'negative'}">
                        {nav_change:+.2%}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(subject, html)

