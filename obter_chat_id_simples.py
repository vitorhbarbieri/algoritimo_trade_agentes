#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script simples para obter chat_id do Telegram sem interação."""

import requests
import json
from pathlib import Path

TOKEN = "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM"

print("=" * 70)
print("OBTENDO CHAT ID DO TELEGRAM")
print("=" * 70)

print("\n1. Buscando mensagens recentes...")
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

try:
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('ok'):
            updates = data.get('result', [])
            
            if updates:
                print(f"   Encontrados {len(updates)} updates")
                
                # Pegar o último update
                last_update = updates[-1]
                
                if 'message' in last_update:
                    chat = last_update['message']['chat']
                    chat_id = chat['id']
                    first_name = chat.get('first_name', 'N/A')
                    username = chat.get('username', 'N/A')
                    
                    print(f"\n2. CHAT ID ENCONTRADO!")
                    print(f"   Chat ID: {chat_id}")
                    print(f"   Nome: {first_name}")
                    if username != 'N/A':
                        print(f"   Username: @{username}")
                    
                    # Salvar no config.json
                    print("\n3. Salvando no config.json...")
                    config_path = Path('config.json')
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    config['notifications']['telegram']['chat_id'] = str(chat_id)
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    
                    print("   Configuracao salva!")
                    
                    # Testar envio
                    print("\n4. Enviando mensagem de teste...")
                    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                    payload = {
                        'chat_id': chat_id,
                        'text': '✅ Configuracao concluida! Voce recebera notificacoes dos agentes aqui.'
                    }
                    
                    test_response = requests.post(send_url, json=payload, timeout=10)
                    if test_response.status_code == 200:
                        print("   Mensagem de teste enviada com sucesso!")
                        print("   Verifique seu Telegram!")
                    else:
                        print(f"   Erro ao enviar: {test_response.status_code}")
                        print(f"   Resposta: {test_response.text}")
                    
                    print("\n" + "=" * 70)
                    print("SUCESSO! Telegram configurado!")
                    print("=" * 70)
                else:
                    print("   Nenhuma mensagem encontrada nos updates")
            else:
                print("   Nenhum update encontrado")
                print("\n   INSTRUCOES:")
                print("   1. Abra o Telegram")
                print("   2. Procure pelo seu bot")
                print("   3. Envie qualquer mensagem (ex: /start)")
                print("   4. Execute este script novamente")
        else:
            print(f"   Erro na API: {data.get('description', 'Erro desconhecido')}")
    else:
        print(f"   Erro HTTP: {response.status_code}")
        print(f"   Resposta: {response.text}")
        
except Exception as e:
    print(f"   Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("METODOS ALTERNATIVOS:")
print("=" * 70)
print("\n1. Via URL no navegador:")
print(f"   https://api.telegram.org/bot{TOKEN}/getUpdates")
print("\n2. Procure por 'chat':{'id':123456789} na resposta")
print("\n3. Ou use o bot @userinfobot no Telegram")

