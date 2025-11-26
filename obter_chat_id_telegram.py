#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simples para obter Chat ID do Telegram.
Envia uma mensagem de teste e mostra o Chat ID.
"""

import requests
import json
from pathlib import Path

TELEGRAM_BOT_TOKEN = "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM"

def obter_chat_id():
    """Obtém o chat_id do Telegram."""
    print("=" * 70)
    print("📱 OBTENDO CHAT ID DO TELEGRAM")
    print("=" * 70)
    
    print("\n📝 INSTRUÇÕES:")
    print("   1. Abra o Telegram no seu celular")
    print("   2. Procure pelo seu bot (criado com @BotFather)")
    print("   3. Envie qualquer mensagem para o bot (ex: /start)")
    print("   4. Aguarde...")
    
    input("\n⏳ Pressione ENTER após enviar a mensagem para o bot...")
    
    # Buscar updates
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('ok'):
                updates = data.get('result', [])
                
                if updates:
                    # Pegar o último update
                    last_update = updates[-1]
                    
                    if 'message' in last_update:
                        message = last_update['message']
                        chat = message['chat']
                        
                        chat_id = chat['id']
                        first_name = chat.get('first_name', 'N/A')
                        username = chat.get('username', 'N/A')
                        
                        print(f"\n✅ CHAT ID ENCONTRADO!")
                        print(f"   Chat ID: {chat_id}")
                        print(f"   Nome: {first_name}")
                        if username != 'N/A':
                            print(f"   Username: @{username}")
                        
                        # Enviar mensagem de teste
                        print(f"\n🧪 Enviando mensagem de teste...")
                        send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                        test_payload = {
                            'chat_id': chat_id,
                            'text': '✅ *Configuração concluída!*\n\nVocê receberá notificações dos agentes aqui.',
                            'parse_mode': 'Markdown'
                        }
                        
                        test_response = requests.post(send_url, json=test_payload, timeout=10)
                        
                        if test_response.status_code == 200:
                            print("   ✅ Mensagem de teste enviada!")
                            print("   📱 Verifique seu Telegram!")
                        else:
                            print(f"   ⚠️  Erro ao enviar teste: {test_response.status_code}")
                        
                        # Salvar no config.json
                        config_path = Path('config.json')
                        if config_path.exists():
                            with open(config_path, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                            
                            if 'notifications' not in config:
                                config['notifications'] = {}
                            if 'telegram' not in config['notifications']:
                                config['notifications']['telegram'] = {}
                            
                            config['notifications']['telegram'] = {
                                'enabled': True,
                                'bot_token': TELEGRAM_BOT_TOKEN,
                                'chat_id': str(chat_id)
                            }
                            
                            with open(config_path, 'w', encoding='utf-8') as f:
                                json.dump(config, f, indent=2, ensure_ascii=False)
                            
                            print(f"\n✅ Configuração salva em config.json!")
                            print(f"\n📱 Chat ID: {chat_id}")
                            print(f"   Token: {TELEGRAM_BOT_TOKEN[:20]}...")
                            
                            return chat_id
                        else:
                            print(f"\n⚠️  Chat ID encontrado mas erro ao salvar")
                            return chat_id
                    else:
                        print("\n⚠️  Nenhuma mensagem encontrada nos updates.")
                else:
                    print("\n⚠️  Nenhum update encontrado.")
                    print("\n💡 Certifique-se de:")
                    print("   1. Ter enviado uma mensagem para o bot")
                    print("   2. Ter aguardado alguns segundos")
                    print("   3. Tentar novamente")
            else:
                error_desc = data.get('description', 'Erro desconhecido')
                print(f"\n❌ Erro na API: {error_desc}")
        else:
            print(f"\n❌ Erro HTTP: {response.status_code}")
            print(f"   Resposta: {response.text}")
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    # Método alternativo
    print("\n" + "=" * 70)
    print("💡 MÉTODO ALTERNATIVO")
    print("=" * 70)
    print("\nSe não funcionou, use @userinfobot:")
    print("   1. Abra Telegram")
    print("   2. Procure @userinfobot")
    print("   3. Envie /start")
    print("   4. Ele mostrará seu Chat ID")
    
    chat_id_input = input("\n📱 Digite seu Chat ID manualmente: ").strip()
    
    if chat_id_input and chat_id_input.replace('-', '').isdigit():
        chat_id = int(chat_id_input.replace('-', ''))
        
        # Salvar
        config_path = Path('config.json')
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'notifications' not in config:
                config['notifications'] = {}
            if 'telegram' not in config['notifications']:
                config['notifications']['telegram'] = {}
            
            config['notifications']['telegram'] = {
                'enabled': True,
                'bot_token': TELEGRAM_BOT_TOKEN,
                'chat_id': str(chat_id)
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Configuração salva!")
            
            # Testar
            print(f"\n🧪 Testando envio...")
            send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            test_payload = {
                'chat_id': chat_id,
                'text': '✅ Configuração concluída! Você receberá notificações aqui.'
            }
            
            test_response = requests.post(send_url, json=test_payload, timeout=10)
            if test_response.status_code == 200:
                print("   ✅ Mensagem de teste enviada!")
                print("   📱 Verifique seu Telegram!")
            else:
                print(f"   ⚠️  Erro: {test_response.status_code}")
            
            return chat_id
    
    return None

if __name__ == '__main__':
    chat_id = obter_chat_id()
    
    if chat_id:
        print("\n" + "=" * 70)
        print("✅ TELEGRAM CONFIGURADO!")
        print("=" * 70)
        print(f"\n📱 Chat ID: {chat_id}")
        print("\n🧪 Para testar:")
        print("   python testar_notificacoes.py")
    else:
        print("\n❌ Não foi possível configurar automaticamente.")
        print("\n💡 Configure manualmente no config.json:")
        print('   "notifications": {')
        print('     "telegram": {')
        print('       "enabled": true,')
        print('       "bot_token": "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM",')
        print('       "chat_id": "SEU_CHAT_ID_AQUI"')
        print('     }')
        print('   }')

