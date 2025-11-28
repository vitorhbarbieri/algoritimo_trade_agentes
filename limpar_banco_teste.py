#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para limpar dados de teste do banco de dados."""

import sqlite3
from pathlib import Path

db_path = Path('agents_orders.db')

if not db_path.exists():
    print("Banco de dados nao encontrado!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Limpando banco de dados...")

# Limpar todas as tabelas
tables = ['proposals', 'risk_evaluations', 'executions', 'open_positions', 'performance_snapshots', 'market_data_captures']

for table in tables:
    try:
        cursor.execute(f"DELETE FROM {table}")
        count = cursor.rowcount
        print(f"  - {table}: {count} registros removidos")
    except Exception as e:
        print(f"  - {table}: Erro - {e}")

conn.commit()
conn.close()

print("\nBanco de dados limpo com sucesso!")

