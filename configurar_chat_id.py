#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script rápido para configurar chat_id do Telegram."""

import requests
import json
from pathlib import Path

TOKEN = "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM"

print("=" * 70)
print("CONFIGURANDO CHAT ID DO TELEGRAM")
print("=" * 70)

# Tentar obter automaticamente
print("\n1. Tentando obter chat_id automaticamente...")
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        updates = data.get('result', [])
        
        if updates:
            last_update = updates[-1]
            if 'message' in last_update:
                chat_id = last_update['message']['chat']['id']
                print(f"   Chat ID encontrado: {chat_id}")
                
                # Salvar no config.json
                config_path = Path('config.json')
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                config['notifications']['telegram']['chat_id'] = str(chat_id)
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                print(f"   Configuracao salva!")
                
                # Testar envio
                print("\n2. Testando envio de mensagem...")
                send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': 'Teste: Configuracao concluida!'
                }
                test_response = requests.post(send_url, json=payload, timeout=10)
                if test_response.status_code == 200:
                    print("   Mensagem de teste enviada com sucesso!")
                    print("   Verifique seu Telegram!")
                else:
                    print(f"   Erro ao enviar: {test_response.status_code}")
                    print(f"   Resposta: {test_response.text}")
            else:
                print("   Nenhuma mensagem encontrada nos updates")
        else:
            print("   Nenhum update encontrado")
            print("\n   INSTRUCOES:")
            print("   1. Abra o Telegram")
            print("   2. Procure pelo seu bot")
            print("   3. Envie qualquer mensagem (ex: /start)")
            print("   4. Execute este script novamente")
            
            # Pedir chat_id manualmente
            print("\n   OU informe o chat_id manualmente:")
            chat_id_manual = input("   Chat ID: ").strip()
            if chat_id_manual:
                config_path = Path('config.json')
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                config['notifications']['telegram']['chat_id'] = chat_id_manual
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                print("   Configuracao salva!")
except Exception as e:
    print(f"   Erro: {e}")
    print("\n   Informe o chat_id manualmente:")
    chat_id_manual = input("   Chat ID: ").strip()
    if chat_id_manual:
        config_path = Path('config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['notifications']['telegram']['chat_id'] = chat_id_manual
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("   Configuracao salva!")

print("\n" + "=" * 70)

