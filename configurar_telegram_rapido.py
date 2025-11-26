#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuração rápida do Telegram - permite entrada manual do Chat ID.
"""

import json
import os
import requests
from pathlib import Path

# Obter token de variável de ambiente ou config.json
def get_telegram_token():
    """Obtém token do Telegram de variável de ambiente ou config.json."""
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    if token:
        return token
    
    config_path = Path('config.json')
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                token = config.get('notifications', {}).get('telegram', {}).get('bot_token', '')
                if token:
                    return token
        except:
            pass
    
    print("⚠️  Token do Telegram não encontrado!")
    print("   Configure via: export TELEGRAM_BOT_TOKEN='seu_token'")
    return None

TELEGRAM_BOT_TOKEN = get_telegram_token()

def configurar_telegram():
    """Configura Telegram com entrada manual do Chat ID."""
    if not TELEGRAM_BOT_TOKEN:
        print("\n❌ Token do Telegram não configurado!")
        print("\n📝 Configure o token:")
        print("   1. Via variável de ambiente:")
        print("      export TELEGRAM_BOT_TOKEN='seu_token_aqui'")
        print("\n   2. Ou adicione no config.json:")
        print('      "notifications": { "telegram": { "bot_token": "seu_token" } }')
        return False
    
    print("=" * 70)
    print("📱 CONFIGURAÇÃO RÁPIDA DO TELEGRAM")
    print("=" * 70)
    
    print(f"\n✅ Token do Bot configurado: {TELEGRAM_BOT_TOKEN[:20]}...")
    
    print("\n📝 Para obter seu Chat ID:")
    print("   Método 1 (Mais fácil):")
    print("   1. Abra o Telegram")
    print("   2. Procure por @userinfobot")
    print("   3. Envie /start")
    print("   4. Ele mostrará seu Chat ID (um número)")
    print("\n   Método 2:")
    print("   1. Envie uma mensagem para seu bot")
    print("   2. Execute: python obter_chat_id_telegram.py")
    
    print("\n" + "=" * 70)
    
    # Pedir Chat ID
    chat_id_input = input("\n📱 Digite seu Chat ID (ou pressione ENTER para tentar buscar automaticamente): ").strip()
    
    chat_id = None
    
    if chat_id_input and chat_id_input.replace('-', '').isdigit():
        chat_id = int(chat_id_input.replace('-', ''))
        print(f"\n✅ Chat ID informado: {chat_id}")
    else:
        print("\n🔍 Tentando buscar Chat ID automaticamente...")
        print("   (Envie uma mensagem para o bot primeiro se ainda não enviou)")
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('result'):
                    updates = data.get('result', [])
                    if updates:
                        last_update = updates[-1]
                        if 'message' in last_update:
                            chat_id = last_update['message']['chat']['id']
                            print(f"   ✅ Chat ID encontrado: {chat_id}")
        except:
            pass
    
    if not chat_id:
        print("\n⚠️  Não foi possível obter o Chat ID automaticamente.")
        chat_id_input = input("📱 Digite seu Chat ID manualmente: ").strip()
        if chat_id_input and chat_id_input.replace('-', '').isdigit():
            chat_id = int(chat_id_input.replace('-', ''))
        else:
            print("\n❌ Chat ID inválido. Configure manualmente no config.json")
            return False
    
    # Testar envio
    print(f"\n🧪 Testando envio de mensagem para Chat ID {chat_id}...")
    
    send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    test_payload = {
        'chat_id': chat_id,
        'text': '✅ *Configuração do Telegram concluída!*\n\nVocê receberá notificações dos agentes aqui quando:\n• Encontrar oportunidades\n• Gerar propostas de daytrade\n• Ocorrer erros\n• Kill switch ativar',
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(send_url, json=test_payload, timeout=10)
        if response.status_code == 200:
            print("   ✅ Mensagem de teste enviada com sucesso!")
            print("   📱 Verifique seu Telegram!")
        else:
            print(f"   ⚠️  Erro ao enviar: {response.status_code}")
            print(f"   Resposta: {response.text}")
            print("\n   Verifique se:")
            print("   - O Chat ID está correto")
            print("   - Você enviou uma mensagem para o bot primeiro")
    except Exception as e:
        print(f"   ⚠️  Erro: {e}")
    
    # Salvar configuração
    config_path = Path('config.json')
    if not config_path.exists():
        print("\n❌ Arquivo config.json não encontrado!")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Atualizar configuração
    if 'notifications' not in config:
        config['notifications'] = {}
    if 'telegram' not in config['notifications']:
        config['notifications']['telegram'] = {}
    
    config['notifications']['telegram'] = {
        'enabled': True,
        'bot_token': TELEGRAM_BOT_TOKEN,
        'chat_id': str(chat_id)
    }
    
    # Salvar
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("✅ TELEGRAM CONFIGURADO COM SUCESSO!")
    print("=" * 70)
    print(f"\n📱 Chat ID: {chat_id}")
    print(f"   Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print("\n📬 Você receberá notificações quando:")
    print("   ✅ Sistema encontrar oportunidades")
    print("   ✅ Gerar propostas de daytrade")
    print("   ✅ Ocorrer erros")
    print("   ✅ Kill switch for ativado")
    print("\n🧪 Para testar:")
    print("   python testar_notificacoes.py")
    
    return True

if __name__ == '__main__':
    configurar_telegram()

