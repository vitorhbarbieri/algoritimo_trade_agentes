#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar o sistema de notificações por email.
"""

import json
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from email_notifier import EmailNotifier
except ImportError:
    from src.email_notifier import EmailNotifier

def testar_email():
    """Testa o sistema de email."""
    print("=" * 70)
    print("🧪 TESTE DO SISTEMA DE NOTIFICAÇÕES POR EMAIL")
    print("=" * 70)
    
    # Carregar configuração
    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ Arquivo config.json não encontrado!")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Verificar configurações de email
    print("\n📋 Verificando configurações...")
    email_enabled = config.get('email_notifications_enabled', True)
    email_destinatario = config.get('email_destinatario', '')
    email_remetente = config.get('email_remetente', '')
    email_senha = config.get('email_senha', '')
    
    print(f"   Notificações habilitadas: {'✅ Sim' if email_enabled else '❌ Não'}")
    print(f"   Destinatário: {email_destinatario if email_destinatario else '❌ Não configurado'}")
    print(f"   Remetente: {email_remetente if email_remetente else '❌ Não configurado'}")
    print(f"   Senha: {'✅ Configurada' if email_senha else '❌ Não configurada'}")
    
    if not email_enabled:
        print("\n⚠️  Notificações por email estão desabilitadas no config.json")
        print("   Para habilitar, defina 'email_notifications_enabled': true")
        return False
    
    if not email_remetente or not email_senha:
        print("\n❌ Email não configurado corretamente!")
        print("\n📝 Para configurar:")
        print("   1. Abra config.json")
        print("   2. Configure:")
        print("      - email_remetente: seu email Gmail")
        print("      - email_senha: senha de app do Gmail (não a senha normal!)")
        print("      - email_destinatario: email que receberá as notificações")
        print("\n   Para Gmail:")
        print("   - Ative autenticação de 2 fatores")
        print("   - Gere uma 'Senha de app' em: https://myaccount.google.com/apppasswords")
        print("   - Use essa senha de app no config.json")
        return False
    
    # Criar notificador
    print("\n🔧 Inicializando EmailNotifier...")
    try:
        notifier = EmailNotifier(config)
        print("   ✅ EmailNotifier inicializado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao inicializar: {e}")
        return False
    
    # Teste 1: Oportunidade única
    print("\n📧 Teste 1: Enviando email de oportunidade única...")
    try:
        opportunity = {
            'type': 'daytrade_options',
            'symbol': 'AAPL_150_C_20250125',
            'ticker': 'AAPL',
            'opportunity_score': 0.75,
            'strike': 150.0,
            'delta': 0.45,
            'intraday_return': 0.008,
            'volume_ratio': 1.5
        }
        notifier.notify_opportunity_found(opportunity)
        print("   ✅ Email de oportunidade enviado!")
    except Exception as e:
        print(f"   ❌ Erro ao enviar: {e}")
        return False
    
    # Aguardar um pouco para evitar rate limiting
    import time
    print("\n⏳ Aguardando 3 segundos...")
    time.sleep(3)
    
    # Teste 2: Múltiplas oportunidades
    print("\n📧 Teste 2: Enviando email de múltiplas oportunidades...")
    try:
        opportunities = [
            {
                'type': 'vol_arb',
                'symbol': 'AAPL_150_C',
                'ticker': 'AAPL',
                'opportunity_score': 0.65
            },
            {
                'type': 'pairs',
                'symbol': 'AAPL/MSFT',
                'ticker': 'AAPL',
                'opportunity_score': 0.58
            }
        ]
        notifier.notify_multiple_opportunities(opportunities)
        print("   ✅ Email de múltiplas oportunidades enviado!")
    except Exception as e:
        print(f"   ❌ Erro ao enviar: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 70)
    print("\n📬 Verifique sua caixa de entrada:")
    print(f"   {email_destinatario}")
    print("\n💡 Dicas:")
    print("   - Verifique também a pasta de SPAM")
    print("   - Se não receber, verifique as configurações de email")
    print("   - Para Gmail, use 'Senha de app', não a senha normal")
    print("\n🔄 O sistema enviará emails automaticamente quando:")
    print("   - Encontrar oportunidades de trading")
    print("   - Gerar propostas importantes (especialmente daytrade)")
    print("   - Ocorrer erros no sistema")
    print("   - Kill switch for ativado")
    
    return True

if __name__ == '__main__':
    sucesso = testar_email()
    sys.exit(0 if sucesso else 1)

