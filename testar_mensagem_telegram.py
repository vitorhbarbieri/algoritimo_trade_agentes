#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste do formato melhorado da mensagem do Telegram."""

import json
import sys
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.notifications import TelegramNotifier

# Carregar config
with open('config.json', 'r') as f:
    config = json.load(f)

# Criar proposta de teste com formato melhorado
proposal_test = {
    'proposal_id': 'DAYOPT-TESTE-15.00-20251202-1234567890',
    'symbol': 'PETR4.SA_15.00_C_20251202',
    'side': 'BUY',
    'quantity': 100,
    'price': 0.10,  # Preço unitário
    'metadata': {
        'underlying': 'PETR4.SA',
        'strike': 15.00,
        'entry_price': 0.10,
        'entry_price_total': 1000.0,
        'exit_price_tp': 0.11,
        'exit_price_tp_total': 1100.0,
        'exit_price_sl': 0.06,
        'exit_price_sl_total': 600.0,
        'ticket_value': 1000.0,
        'take_profit_pct': 0.10,
        'stop_loss_pct': 0.40,
        'gain_value': 100.0,
        'loss_value': 400.0,
        'delta': 0.45,
        'gamma': 0.02,
        'iv': 0.25,
        'intraday_return': 0.015,
        'volume_ratio': 1.5,
        'days_to_expiry': 5,
        'eod_close': True
    }
}

# Inicializar notificador
telegram_config = config.get('notifications', {}).get('telegram', {})
notifier = TelegramNotifier(
    bot_token=telegram_config.get('bot_token'),
    chat_id=telegram_config.get('chat_id')
)

print("=" * 70)
print("TESTE DE MENSAGEM TELEGRAM - FORMATO MELHORADO")
print("=" * 70)
print()

if notifier.is_configured():
    print("Enviando mensagem de teste...")
    result = notifier.send_proposal_with_approval(proposal_test)
    
    if result:
        print("✅ Mensagem enviada com sucesso!")
        print("Verifique seu Telegram para ver o formato melhorado.")
    else:
        print("❌ Erro ao enviar mensagem")
else:
    print("❌ Telegram não configurado")
    print("Configure bot_token e chat_id no config.json")

