#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script não-interativo para configurar chat_id do Telegram."""

import requests
import json
from pathlib import Path

TOKEN = "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM"

print("=" * 70)
print("CONFIGURANDO CHAT ID DO TELEGRAM")
print("=" * 70)

# Tentar obter automaticamente
print("\nTentando obter chat_id automaticamente...")
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
                print("\n" + "=" * 70)
                exit(0)
        
        print("   Nenhum update encontrado")
        print("\n   INSTRUCOES:")
        print("   1. Abra o Telegram")
        print("   2. Procure pelo seu bot")
        print("   3. Envie qualquer mensagem (ex: /start)")
        print("   4. Execute: python configurar_chat_id_auto.py")
        print("\n   OU configure manualmente no config.json:")
        print('   "chat_id": "SEU_CHAT_ID_AQUI"')
        
except Exception as e:
    print(f"   Erro: {e}")

print("\n" + "=" * 70)

