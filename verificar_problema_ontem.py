#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificar por que não capturou dados ontem mesmo com mercado aberto
"""

import json
import sqlite3
from datetime import datetime, timedelta
from src.trading_schedule import TradingSchedule

print("=" * 70)
print("ANÁLISE: Por que não capturou dados ontem?")
print("=" * 70)
print()

# Verificar status de ontem
ts = TradingSchedule()
yesterday = datetime.now() - timedelta(days=1)

print(f"Data de ontem: {yesterday.strftime('%d/%m/%Y')}")
print(f"Era dia útil: {ts.is_trading_day(yesterday)}")
print()

# Verificar status em diferentes horários de ontem
horarios_teste = [
    (9, 45, "Pré-mercado"),
    (10, 0, "Abertura"),
    (12, 0, "Meio-dia"),
    (15, 0, "Tarde"),
    (17, 0, "Fechamento"),
    (18, 0, "Após fechamento")
]

print("Status do mercado em diferentes horários de ontem:")
for hora, minuto, desc in horarios_teste:
    test_time = yesterday.replace(hour=hora, minute=minuto, second=0)
    status = ts.get_trading_status(test_time)
    print(f"  {desc} ({hora:02d}:{minuto:02d}): {status}")

print()

# Verificar capturas de ontem no banco
print("VERIFICANDO BANCO DE DADOS:")
conn = sqlite3.connect('agents_orders.db')
cursor = conn.cursor()

# Capturas de ontem
yesterday_start = yesterday.replace(hour=0, minute=0, second=0).isoformat()
yesterday_end = yesterday.replace(hour=23, minute=59, second=59).isoformat()

cursor.execute('''
    SELECT COUNT(*) FROM market_data_captures 
    WHERE source="real" 
    AND timestamp >= ? 
    AND timestamp <= ?
''', (yesterday_start, yesterday_end))
count_ontem = cursor.fetchone()[0]

print(f"  Capturas de ontem: {count_ontem}")

# Verificar se há capturas por hora
cursor.execute('''
    SELECT strftime('%H', timestamp) as hora, COUNT(*) as cnt
    FROM market_data_captures 
    WHERE source="real" 
    AND timestamp >= ? 
    AND timestamp <= ?
    GROUP BY hora
    ORDER BY hora
''', (yesterday_start, yesterday_end))
capturas_por_hora = cursor.fetchall()

if capturas_por_hora:
    print("  Capturas por hora:")
    for hora, cnt in capturas_por_hora:
        print(f"    {hora}:00 - {cnt} capturas")
else:
    print("  Nenhuma captura encontrada para ontem")

# Verificar última captura antes de ontem
cursor.execute('''
    SELECT MAX(timestamp) FROM market_data_captures 
    WHERE source="real" 
    AND timestamp < ?
''', (yesterday_start,))
ultima_antes = cursor.fetchone()[0]

if ultima_antes:
    print(f"  Última captura antes de ontem: {ultima_antes[:19]}")
else:
    print("  Nenhuma captura antes de ontem encontrada")

conn.close()

print()
print("=" * 70)
print("CONCLUSÃO:")
print("=" * 70)

if count_ontem == 0:
    print("❌ PROBLEMA CONFIRMADO: Nenhuma captura de ontem!")
    print()
    print("Possíveis causas:")
    print("  1. O script iniciar_agentes.py não estava rodando")
    print("  2. O loop de monitoramento estava pulando scans")
    print("  3. Erro silencioso que não foi logado")
    print("  4. Problema de conexão com API")
    print()
    print("SOLUÇÃO:")
    print("  - Verificar se o script estava rodando")
    print("  - Verificar logs de erro")
    print("  - Garantir que o loop não pula scans quando mercado aberto")
else:
    print(f"✅ Dados capturados: {count_ontem} capturas")
    if capturas_por_hora:
        print("  Distribuição por hora parece normal")

