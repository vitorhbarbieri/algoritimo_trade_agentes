#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar o sistema de notificações (Telegram, Discord, Email).
"""

import json
import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from notifications import UnifiedNotifier, TelegramNotifier, DiscordNotifier
except ImportError:
    from src.notifications import UnifiedNotifier, TelegramNotifier, DiscordNotifier

def testar_notificacoes():
    """Testa o sistema de notificações."""
    print("=" * 70)
    print("🧪 TESTE DO SISTEMA DE NOTIFICAÇÕES")
    print("=" * 70)
    
    # Carregar configuração
    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ Arquivo config.json não encontrado!")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("\n📋 Verificando canais configurados...\n")
    
    # Verificar Telegram
    telegram_token = config.get('notifications', {}).get('telegram', {}).get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat = config.get('notifications', {}).get('telegram', {}).get('chat_id') or os.getenv('TELEGRAM_CHAT_ID', '')
    telegram_enabled = config.get('notifications', {}).get('telegram', {}).get('enabled', False)
    
    if telegram_enabled and telegram_token and telegram_chat:
        print("✅ Telegram configurado")
        telegram = TelegramNotifier(telegram_token, telegram_chat)
        if telegram.is_configured():
            print("   Testando Telegram...")
            if telegram.send("🧪 Teste do sistema de notificações\n\nSe você recebeu esta mensagem, o Telegram está funcionando!", title="Teste de Notificação"):
                print("   ✅ Mensagem enviada com sucesso!")
            else:
                print("   ❌ Erro ao enviar mensagem")
        else:
            print("   ⚠️ Telegram não está configurado corretamente")
    else:
        print("ℹ️  Telegram não configurado")
        print("   Para configurar, veja: CONFIGURAR_TELEGRAM.md")
    
    print()
    
    # Verificar Discord
    discord_webhook = config.get('notifications', {}).get('discord', {}).get('webhook_url') or os.getenv('DISCORD_WEBHOOK_URL', '')
    discord_enabled = config.get('notifications', {}).get('discord', {}).get('enabled', False)
    
    if discord_enabled and discord_webhook:
        print("✅ Discord configurado")
        discord = DiscordNotifier(discord_webhook)
        if discord.is_configured():
            print("   Testando Discord...")
            if discord.send("🧪 Teste do sistema de notificações\n\nSe você recebeu esta mensagem, o Discord está funcionando!", title="Teste de Notificação"):
                print("   ✅ Mensagem enviada com sucesso!")
            else:
                print("   ❌ Erro ao enviar mensagem")
        else:
            print("   ⚠️ Discord não está configurado corretamente")
    else:
        print("ℹ️  Discord não configurado")
        print("   Para configurar, veja: CONFIGURAR_DISCORD.md")
    
    print()
    
    # Verificar Email
    email_enabled = config.get('notifications', {}).get('email', {}).get('enabled', False)
    email_remetente = config.get('notifications', {}).get('email', {}).get('email_remetente') or os.getenv('EMAIL_REMETENTE', '')
    email_senha = config.get('notifications', {}).get('email', {}).get('email_senha') or os.getenv('EMAIL_SENHA', '')
    
    if email_enabled and email_remetente and email_senha:
        print("✅ Email configurado")
        print("   Para testar email, execute: python testar_email.py")
    else:
        print("ℹ️  Email não configurado")
        print("   Para configurar, veja: CONFIGURAR_EMAIL.md")
    
    print("\n" + "=" * 70)
    print("📊 TESTE COM NOTIFICADOR UNIFICADO")
    print("=" * 70)
    
    # Testar notificador unificado
    notifier = UnifiedNotifier(config)
    
    if not notifier.channels:
        print("\n⚠️  NENHUM CANAL CONFIGURADO!")
        print("\n📝 Configure pelo menos um canal:")
        print("   1. Telegram: CONFIGURAR_TELEGRAM.md")
        print("   2. Discord: CONFIGURAR_DISCORD.md")
        print("   3. Email: CONFIGURAR_EMAIL.md")
        return False
    
    print(f"\n✅ {len(notifier.channels)} canal(is) configurado(s):")
    for channel_name, _ in notifier.channels:
        print(f"   - {channel_name.title()}")
    
    # Teste 1: Oportunidade
    print("\n📧 Teste 1: Enviando notificação de oportunidade...")
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
    notifier.notify_opportunity(opportunity)
    print("   ✅ Notificação de oportunidade enviada!")
    
    import time
    time.sleep(2)
    
    # Teste 2: Erro
    print("\n📧 Teste 2: Enviando notificação de erro...")
    notifier.notify_error('Test Error', 'Este é um teste do sistema de notificações')
    print("   ✅ Notificação de erro enviada!")
    
    print("\n" + "=" * 70)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 70)
    print("\n📬 Verifique seus canais configurados:")
    for channel_name, _ in notifier.channels:
        print(f"   - {channel_name.title()}")
    print("\n💡 Dicas:")
    print("   - Telegram: Verifique o chat com seu bot")
    print("   - Discord: Verifique o canal configurado")
    print("   - Email: Verifique a caixa de entrada (e SPAM)")
    
    return True

if __name__ == '__main__':
    sucesso = testar_notificacoes()
    sys.exit(0 if sucesso else 1)

