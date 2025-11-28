#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste direto do Telegram para diagnosticar o problema."""

import requests
import json

TOKEN = "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM"
CHAT_ID = "25531123"

print("=" * 70)
print("TESTE DIRETO DO TELEGRAM")
print("=" * 70)

print(f"\n1. Token: {TOKEN[:20]}...")
print(f"2. Chat ID: {CHAT_ID}")

# Teste 1: Verificar se o bot está funcionando
print("\n3. Testando getMe...")
try:
    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        bot_info = response.json()
        if bot_info.get('ok'):
            print(f"   Bot OK: {bot_info['result']['first_name']}")
        else:
            print(f"   Erro: {bot_info}")
    else:
        print(f"   Erro HTTP: {response.status_code}")
except Exception as e:
    print(f"   Erro: {e}")

# Teste 2: Buscar updates para ver chat_ids disponíveis
print("\n4. Buscando updates (mensagens recentes)...")
try:
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        updates = data.get('result', [])
        print(f"   Updates encontrados: {len(updates)}")
        
        if updates:
            print("\n   Chat IDs encontrados:")
            for update in updates:
                if 'message' in update:
                    chat = update['message']['chat']
                    chat_id = chat['id']
                    first_name = chat.get('first_name', 'N/A')
                    username = chat.get('username', 'N/A')
                    print(f"     - Chat ID: {chat_id}, Nome: {first_name}, Username: @{username}")
        else:
            print("   Nenhum update encontrado!")
            print("\n   IMPORTANTE: Envie uma mensagem para o bot primeiro!")
            print("   1. Abra o Telegram")
            print("   2. Procure pelo seu bot")
            print("   3. Envie qualquer mensagem (ex: /start)")
            print("   4. Execute este script novamente")
except Exception as e:
    print(f"   Erro: {e}")

# Teste 3: Tentar enviar mensagem
print(f"\n5. Tentando enviar mensagem para chat_id: {CHAT_ID}...")
try:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': 'Teste: Mensagem de teste do sistema de agentes!'
    }
    response = requests.post(url, json=payload, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            print("   SUCESSO! Mensagem enviada!")
            print("   Verifique seu Telegram!")
        else:
            print(f"   Erro: {result}")
            if result.get('error_code') == 400:
                print("\n   PROBLEMA: chat not found")
                print("   Possiveis causas:")
                print("   1. Chat ID incorreto")
                print("   2. Voce ainda nao iniciou conversa com o bot")
                print("   3. O bot foi bloqueado")
                print("\n   SOLUCAO:")
                print("   1. Abra o Telegram")
                print("   2. Procure pelo bot")
                print("   3. Envie /start")
                print("   4. Execute: python obter_chat_id_simples.py")
    else:
        print(f"   Erro HTTP: {response.status_code}")
        print(f"   Resposta: {response.text}")
except Exception as e:
    print(f"   Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

