#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifica configuração atualizada"""
import json

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

print("=" * 80)
print("VERIFICACAO DA CONFIGURACAO ATUALIZADA")
print("=" * 80)

print(f"\nAtivos brasileiros: {len(config['monitored_tickers'])}")
print(f"Contratos futuros: {len(config['monitored_futures'])}")
print(f"Total monitorado: {len(config['monitored_tickers']) + len(config['monitored_futures'])}")

print("\nFuturos configurados:")
for f in config['monitored_futures']:
    print(f"  - {f}")

print("\nPrimeiros 10 ativos:")
for t in config['monitored_tickers'][:10]:
    print(f"  - {t}")

print("\n" + "=" * 80)

