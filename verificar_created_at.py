#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar created_at no banco"""

import sqlite3

conn = sqlite3.connect('agents_orders.db')
cursor = conn.cursor()

cursor.execute('SELECT created_at, timestamp FROM market_data_captures ORDER BY created_at DESC LIMIT 5')
results = cursor.fetchall()

print('Últimos 5 registros:')
for r in results:
    print(f'  created_at: {r[0]}')
    print(f'  timestamp: {r[1][:19] if r[1] else "N/A"}')
    print()

conn.close()

