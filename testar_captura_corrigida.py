#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste da captura corrigida"""

import json
import sqlite3
from src.monitoring_service import MonitoringService

print("Testando captura corrigida...")
print()

# Carregar config
with open('config.json') as f:
    config = json.load(f)

# Criar monitoring service
monitoring = MonitoringService(config)

# Executar scan
print("Executando scan_market()...")
result = monitoring.scan_market()

print()
print("RESULTADOS:")
print(f"  Status: {result.get('status')}")
print(f"  Dados capturados: {result.get('data_captured', 'N/A')}")
print(f"  Propostas: {result.get('proposals', 0)}")
print(f"  Oportunidades: {result.get('opportunities', 0)}")

# Verificar banco
print()
print("VERIFICANDO BANCO DE DADOS:")
conn = sqlite3.connect('agents_orders.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM market_data_captures WHERE source="real" ORDER BY timestamp DESC LIMIT 1')
total = cursor.fetchone()[0]
print(f"  Total de capturas: {total}")

cursor.execute('SELECT ticker, COUNT(*) as cnt FROM market_data_captures WHERE source="real" GROUP BY ticker ORDER BY cnt DESC LIMIT 5')
top_tickers = cursor.fetchall()
print("  Top 5 tickers capturados:")
for ticker, cnt in top_tickers:
    print(f"    {ticker}: {cnt} capturas")

conn.close()

print()
print("Teste concluído!")

