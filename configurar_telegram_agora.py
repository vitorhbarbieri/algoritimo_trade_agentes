#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para configurar Telegram rapidamente no config.json."""

import json
import os

def configurar_telegram():
    """Configura Telegram no config.json."""
    
    print("=" * 70)
    print("CONFIGURACAO RAPIDA DO TELEGRAM")
    print("=" * 70)
    
    # Token fornecido anteriormente
    token_padrao = "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM"
    
    print(f"\nToken do bot (pressione Enter para usar o padrao):")
    print(f"Padrao: {token_padrao[:20]}...")
    token_input = input("Token: ").strip()
    bot_token = token_input if token_input else token_padrao
    
    print(f"\nChat ID (seu numero: +5511996204459):")
    print("Para obter o chat_id, envie uma mensagem para seu bot e execute:")
    print("  python obter_chat_id_telegram.py")
    chat_id = input("Chat ID: ").strip()
    
    if not chat_id:
        print("\nERRO: Chat ID e obrigatorio!")
        print("Execute: python obter_chat_id_telegram.py")
        return False
    
    # Carregar config
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"ERRO ao carregar config.json: {e}")
        return False
    
    # Atualizar config
    if 'notifications' not in config:
        config['notifications'] = {}
    if 'telegram' not in config['notifications']:
        config['notifications']['telegram'] = {}
    
    config['notifications']['telegram']['enabled'] = True
    config['notifications']['telegram']['bot_token'] = bot_token
    config['notifications']['telegram']['chat_id'] = chat_id
    
    # Salvar config
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("\nSUCESSO: config.json atualizado!")
        print(f"  - Bot Token: {bot_token[:20]}...")
        print(f"  - Chat ID: {chat_id}")
        return True
    except Exception as e:
        print(f"ERRO ao salvar config.json: {e}")
        return False

if __name__ == '__main__':
    sucesso = configurar_telegram()
    if sucesso:
        print("\nTestando configuracao...")
        import subprocess
        subprocess.run(['python', 'testar_telegram.py'])

