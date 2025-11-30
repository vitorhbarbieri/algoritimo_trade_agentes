#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste para verificar se os timestamps estão usando timezone de São Paulo"""

import json
import sqlite3
from datetime import datetime
import pytz

# Timezone de São Paulo
B3_TIMEZONE = pytz.timezone('America/Sao_Paulo')

print("=" * 70)
print("TESTE DE TIMEZONE - Verificando timestamps salvos")
print("=" * 70)
print()

# Verificar timestamps no banco
conn = sqlite3.connect('agents_orders.db')
cursor = conn.cursor()

print("1. VERIFICANDO TIMESTAMPS NO BANCO:")
print()

# Últimas capturas de mercado
cursor.execute('''
    SELECT timestamp, ticker 
    FROM market_data_captures 
    WHERE source="real" 
    ORDER BY timestamp DESC 
    LIMIT 5
''')
capturas = cursor.fetchall()

print("  Últimas 5 capturas de mercado:")
for ts, ticker in capturas:
    # Tentar parsear o timestamp
    try:
        if 'T' in ts:
            # ISO format com timezone
            if ts.endswith('Z'):
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            elif '+' in ts or ts.count('-') > 2:
                dt = datetime.fromisoformat(ts)
            else:
                dt = datetime.fromisoformat(ts)
            
            # Converter para timezone de São Paulo se não tiver timezone
            if dt.tzinfo is None:
                dt = B3_TIMEZONE.localize(dt)
            else:
                dt = dt.astimezone(B3_TIMEZONE)
            
            print(f"    {ticker}: {dt.strftime('%d/%m/%Y %H:%M:%S %Z')}")
        else:
            print(f"    {ticker}: {ts} (formato antigo)")
    except Exception as e:
        print(f"    {ticker}: {ts} (erro ao parsear: {e})")

print()

# Verificar timezone atual do sistema
print("2. TIMEZONE DO SISTEMA:")
print(f"  Timezone local: {datetime.now().astimezone().tzinfo}")
print(f"  Timezone B3 (SP): {B3_TIMEZONE}")
print(f"  Hora atual (local): {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print(f"  Hora atual (B3): {datetime.now(B3_TIMEZONE).strftime('%d/%m/%Y %H:%M:%S %Z')}")
print()

# Testar função get_b3_timestamp
print("3. TESTANDO FUNÇÃO get_b3_timestamp:")
try:
    from src.orders_repository import get_b3_timestamp
    ts_b3 = get_b3_timestamp()
    print(f"  Timestamp gerado: {ts_b3}")
    
    # Parsear e mostrar em formato legível
    dt_b3 = datetime.fromisoformat(ts_b3)
    if dt_b3.tzinfo:
        dt_b3_sp = dt_b3.astimezone(B3_TIMEZONE)
        print(f"  Em formato legível (B3): {dt_b3_sp.strftime('%d/%m/%Y %H:%M:%S %Z')}")
    else:
        print(f"  ⚠️  AVISO: Timestamp sem timezone!")
except Exception as e:
    print(f"  ❌ Erro: {e}")

print()
print("=" * 70)
print("TESTE CONCLUÍDO")
print("=" * 70)

conn.close()

