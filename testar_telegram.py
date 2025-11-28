#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para testar configuração e envio de mensagens via Telegram."""

import os
import json
import sys

def testar_telegram():
    """Testa configuração e envio de mensagem via Telegram."""
    
    print("=" * 70)
    print("TESTE DE CONFIGURACAO DO TELEGRAM")
    print("=" * 70)
    
    # Carregar config
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"ERRO: Nao foi possivel carregar config.json: {e}")
        return False
    
    # Verificar configuração
    telegram_config = config.get('notifications', {}).get('telegram', {})
    bot_token = telegram_config.get('bot_token', '') or os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = telegram_config.get('chat_id', '') or os.getenv('TELEGRAM_CHAT_ID', '')
    
    print(f"\n1. VERIFICANDO CONFIGURACAO:")
    print(f"   - Bot Token: {'DEFINIDO' if bot_token else 'VAZIO'}")
    print(f"   - Chat ID: {'DEFINIDO' if chat_id else 'VAZIO'}")
    print(f"   - Habilitado: {telegram_config.get('enabled', False)}")
    
    if not bot_token:
        print("\nERRO: Bot token nao configurado!")
        print("   Configure em config.json ou defina TELEGRAM_BOT_TOKEN")
        return False
    
    if not chat_id:
        print("\nERRO: Chat ID nao configurado!")
        print("   Configure em config.json ou defina TELEGRAM_CHAT_ID")
        return False
    
    # Testar inicialização do notificador
    print("\n2. TESTANDO INICIALIZACAO DO NOTIFICADOR:")
    try:
        from src.notifications import UnifiedNotifier
        notifier = UnifiedNotifier(config)
        
        if not notifier.channels:
            print("   ERRO: Nenhum canal configurado!")
            return False
        
        print(f"   Canais configurados: {[name for name, _ in notifier.channels]}")
    except Exception as e:
        print(f"   ERRO ao inicializar: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Testar envio de mensagem
    print("\n3. TESTANDO ENVIO DE MENSAGEM:")
    try:
        opportunity = {
            'type': 'daytrade_options',
            'symbol': 'PETR4.SA',
            'ticker': 'PETR4.SA',
            'opportunity_score': 85.5,
            'strike': 32.50,
            'delta': 0.45,
            'intraday_return': 0.015,
            'volume_ratio': 1.5
        }
        
        result = notifier.notify_opportunity(opportunity)
        
        if result:
            print("   SUCESSO: Mensagem enviada!")
            return True
        else:
            print("   ERRO: Falha ao enviar mensagem")
            return False
            
    except Exception as e:
        print(f"   ERRO ao enviar: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    sucesso = testar_telegram()
    sys.exit(0 if sucesso else 1)

