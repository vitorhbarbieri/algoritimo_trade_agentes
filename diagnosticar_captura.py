#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para identificar problemas na captura de dados.
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from monitoring_service import MonitoringService
    from trading_schedule import TradingSchedule
except ImportError:
    from src.monitoring_service import MonitoringService
    from src.trading_schedule import TradingSchedule

print("=" * 70)
print("DIAGNÓSTICO DE CAPTURA DE DADOS")
print("=" * 70)
print()

# 1. Verificar banco de dados
print("1. VERIFICANDO BANCO DE DADOS...")
try:
    conn = sqlite3.connect('agents_orders.db')
    cursor = conn.cursor()
    
    # Verificar capturas de ontem
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    cursor.execute('SELECT COUNT(*) FROM market_data_captures WHERE source="real" AND timestamp >= ?', (yesterday,))
    count_yesterday = cursor.fetchone()[0]
    
    # Verificar capturas hoje
    today_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
    cursor.execute('SELECT COUNT(*) FROM market_data_captures WHERE source="real" AND timestamp >= ?', (today_start,))
    count_today = cursor.fetchone()[0]
    
    # Última captura
    cursor.execute('SELECT MAX(timestamp) FROM market_data_captures WHERE source="real"')
    last_capture = cursor.fetchone()[0]
    
    print(f"  Capturas de ontem: {count_yesterday}")
    print(f"  Capturas de hoje: {count_today}")
    print(f"  Última captura: {last_capture[:19] if last_capture else 'N/A'}")
    
    conn.close()
except Exception as e:
    print(f"  ERRO: {e}")

print()

# 2. Verificar configuração
print("2. VERIFICANDO CONFIGURAÇÃO...")
try:
    with open('config.json') as f:
        config = json.load(f)
    
    tickers = config.get('monitored_tickers', [])
    print(f"  Tickers configurados: {len(tickers)}")
    print(f"  Primeiros 5: {tickers[:5]}")
    
    daytrade_enabled = config.get('daytrade_options', {}).get('enabled', False)
    print(f"  DayTrade habilitado: {daytrade_enabled}")
except Exception as e:
    print(f"  ERRO: {e}")

print()

# 3. Verificar horário B3
print("3. VERIFICANDO HORÁRIO B3...")
try:
    ts = TradingSchedule()
    b3_time = ts.get_current_b3_time()
    status = ts.get_trading_status()
    
    print(f"  Hora atual (B3): {b3_time.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"  Status: {status}")
    print(f"  É dia útil: {ts.is_trading_day()}")
    print(f"  Está em horário de trading: {ts.is_trading_hours()}")
    
    # Verificar se ontem era dia útil
    yesterday_date = datetime.now() - timedelta(days=1)
    was_trading_day = ts.is_trading_day(yesterday_date)
    print(f"  Ontem era dia útil: {was_trading_day}")
except Exception as e:
    print(f"  ERRO: {e}")

print()

# 4. Testar captura de dados real
print("4. TESTANDO CAPTURA DE DADOS REAL...")
try:
    import yfinance as yf
    
    test_ticker = config.get('monitored_tickers', ['PETR4.SA'])[0]
    print(f"  Testando com: {test_ticker}")
    
    stock = yf.Ticker(test_ticker)
    
    # Tentar buscar dados intraday
    try:
        hist = stock.history(period='1d', interval='5m', timeout=10)
        if hist is not None and not hist.empty:
            print(f"  ✅ Dados intraday obtidos: {len(hist)} períodos")
            print(f"     Último preço: R$ {hist.iloc[-1]['Close']:.2f}")
            print(f"     Último timestamp: {hist.index[-1]}")
        else:
            print(f"  ⚠️  Nenhum dado retornado")
    except Exception as e:
        print(f"  ❌ Erro ao buscar dados intraday: {e}")
        
        # Tentar dados diários
        try:
            hist_daily = stock.history(period='5d', interval='1d', timeout=10)
            if hist_daily is not None and not hist_daily.empty:
                print(f"  ✅ Dados diários obtidos: {len(hist_daily)} dias")
                print(f"     Último preço: R$ {hist_daily.iloc[-1]['Close']:.2f}")
            else:
                print(f"  ⚠️  Nenhum dado diário retornado")
        except Exception as e2:
            print(f"  ❌ Erro ao buscar dados diários: {e2}")
            
except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# 5. Testar MonitoringService.scan_market()
print("5. TESTANDO MonitoringService.scan_market()...")
try:
    monitoring = MonitoringService(config)
    result = monitoring.scan_market()
    
    print(f"  Status: {result.get('status')}")
    print(f"  Oportunidades: {result.get('opportunities', 0)}")
    print(f"  Propostas: {result.get('proposals', 0)}")
    
    # Verificar se dados foram salvos após o scan
    conn = sqlite3.connect('agents_orders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM market_data_captures WHERE source="real" ORDER BY timestamp DESC LIMIT 1')
    new_captures = cursor.fetchone()[0]
    conn.close()
    
    print(f"  Capturas no banco após scan: {new_captures}")
    
except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("DIAGNÓSTICO CONCLUÍDO")
print("=" * 70)

