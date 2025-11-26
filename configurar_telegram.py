#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para configurar Telegram automaticamente.
Obtém o chat_id e testa a configuração.
"""

import json
import sys
import requests
from pathlib import Path

TELEGRAM_BOT_TOKEN = "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM"

def obter_chat_id(token, phone_number=None):
    """Obtém o chat_id através de uma mensagem."""
    print("=" * 70)
    print("📱 CONFIGURAÇÃO DO TELEGRAM")
    print("=" * 70)
    
    if phone_number:
        print(f"\n📱 Número registrado: {phone_number}")
    
    print("\n📝 IMPORTANTE: Para obter seu Chat ID:")
    print("   1. Abra o Telegram no seu celular")
    print("   2. Procure pelo seu bot (o que você criou com @BotFather)")
    print("   3. Envie qualquer mensagem para o bot (ex: /start ou Olá)")
    print("   4. Aguarde alguns segundos...")
    
    print("\n💡 Dica: Se não souber o nome do bot, procure por:")
    print("   - O username que você escolheu ao criar com @BotFather")
    print("   - Ou use o @userinfobot para obter seu Chat ID diretamente")
    
    input("\n⏳ Pressione ENTER após enviar a mensagem para o bot...")
    
    # Buscar updates do bot
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    print("\n🔍 Buscando mensagens...")
    
    try:
        # Tentar algumas vezes
        for tentativa in range(3):
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok') and data.get('result'):
                    updates = data['result']
                    if updates:
                        # Pegar o último update
                        last_update = updates[-1]
                        if 'message' in last_update:
                            chat_id = last_update['message']['chat']['id']
                            chat_username = last_update['message']['chat'].get('username', 'N/A')
                            chat_first_name = last_update['message']['chat'].get('first_name', 'N/A')
                            chat_phone = last_update['message']['chat'].get('phone_number', 'N/A')
                            
                            print(f"\n✅ Chat ID encontrado!")
                            print(f"   Chat ID: {chat_id}")
                            print(f"   Nome: {chat_first_name}")
                            if chat_username != 'N/A':
                                print(f"   Username: @{chat_username}")
                            if chat_phone != 'N/A':
                                print(f"   Telefone: {chat_phone}")
                            
                            # Verificar se o telefone corresponde (se fornecido)
                            if phone_number and chat_phone != 'N/A':
                                phone_clean = phone_number.replace('+', '').replace(' ', '').replace('-', '')
                                chat_phone_clean = str(chat_phone).replace('+', '').replace(' ', '').replace('-', '')
                                if phone_clean in chat_phone_clean or chat_phone_clean in phone_clean:
                                    print(f"   ✅ Telefone confere!")
                            
                            return chat_id
                        else:
                            print(f"\n⚠️  Tentativa {tentativa + 1}: Nenhuma mensagem encontrada.")
                            if tentativa < 2:
                                print("   Aguardando mais alguns segundos...")
                                import time
                                time.sleep(3)
                    else:
                        print(f"\n⚠️  Tentativa {tentativa + 1}: Nenhum update encontrado.")
                        if tentativa < 2:
                            print("   Aguardando mais alguns segundos...")
                            import time
                            time.sleep(3)
                else:
                    error_desc = data.get('description', 'Erro desconhecido')
                    print(f"\n❌ Erro na API: {error_desc}")
                    break
            else:
                print(f"\n❌ Erro HTTP: {response.status_code}")
                print(f"   Resposta: {response.text}")
                break
    
    except Exception as e:
        print(f"\n❌ Erro ao buscar chat_id: {e}")
    
    # Método alternativo: usar @userinfobot
    print("\n" + "=" * 70)
    print("💡 MÉTODO ALTERNATIVO")
    print("=" * 70)
    print("\nSe não funcionou, use este método:")
    print("   1. Abra o Telegram")
    print("   2. Procure por @userinfobot")
    print("   3. Envie /start")
    print("   4. Ele retornará seu Chat ID (um número)")
    
    chat_id_input = input("\n📱 Digite seu Chat ID manualmente (ou pressione ENTER para pular): ").strip()
    
    if chat_id_input and chat_id_input.replace('-', '').isdigit():
        return int(chat_id_input.replace('-', ''))
    
    return None

def testar_envio(token, chat_id):
    """Testa envio de mensagem."""
    print("\n🧪 Testando envio de mensagem...")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': '✅ *Configuração do Telegram concluída!*\n\nVocê receberá notificações dos agentes aqui.',
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("   ✅ Mensagem de teste enviada com sucesso!")
            print("   📱 Verifique seu Telegram!")
            return True
        else:
            print(f"   ❌ Erro: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def salvar_config(token, chat_id):
    """Salva configuração no config.json."""
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
        'bot_token': token,
        'chat_id': str(chat_id)
    }
    
    # Salvar
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Configuração salva em config.json!")
    return True

def main():
    """Função principal."""
    print("\n🔧 Configurando Telegram...")
    print(f"   Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    
    # Obter chat_id
    phone_number = "+5511996204459"
    chat_id = obter_chat_id(TELEGRAM_BOT_TOKEN, phone_number)
    
    if not chat_id:
        print("\n❌ Não foi possível obter o Chat ID.")
        print("\n💡 Alternativa manual:")
        print("   1. Procure @userinfobot no Telegram")
        print("   2. Envie /start")
        print("   3. Copie seu Chat ID")
        print("   4. Configure manualmente no config.json")
        return False
    
    # Testar envio
    if not testar_envio(TELEGRAM_BOT_TOKEN, chat_id):
        print("\n⚠️  Não foi possível enviar mensagem de teste.")
        print("   Verifique se o token está correto e se você enviou mensagem para o bot.")
        return False
    
    # Salvar configuração
    if salvar_config(TELEGRAM_BOT_TOKEN, chat_id):
        print("\n" + "=" * 70)
        print("✅ TELEGRAM CONFIGURADO COM SUCESSO!")
        print("=" * 70)
        print("\n📱 Você receberá notificações no Telegram quando:")
        print("   - Sistema encontrar oportunidades")
        print("   - Gerar propostas de daytrade")
        print("   - Ocorrer erros")
        print("   - Kill switch for ativado")
        print("\n🧪 Para testar novamente:")
        print("   python testar_notificacoes.py")
        return True
    
    return False

if __name__ == '__main__':
    sucesso = main()
    sys.exit(0 if sucesso else 1)

