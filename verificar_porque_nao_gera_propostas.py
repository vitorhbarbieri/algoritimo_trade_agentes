#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifica por que não está gerando propostas"""
from src.orders_repository import OrdersRepository
import pandas as pd
import json

repo = OrdersRepository()
with open('config.json', 'r') as f:
    config = json.load(f)

cfg = config.get('daytrade_options', {})
min_intraday = cfg.get('min_intraday_return', 0.006)
min_volume = cfg.get('min_volume_ratio', 0.3)

print("=" * 80)
print("VERIFICACAO: Por que nao gera propostas?")
print("=" * 80)
print(f"\nThresholds configurados:")
print(f"  min_intraday_return: {min_intraday*100:.2f}%")
print(f"  min_volume_ratio: {min_volume:.2f}x")

captures = repo.get_market_data_captures()
brasil = captures[captures['ticker'].str.contains('.SA', na=False)].copy()
brasil['timestamp'] = pd.to_datetime(brasil['timestamp'], errors='coerce')
brasil['date'] = brasil['timestamp'].dt.date

print(f"\nAnalisando dados reais...")
print(f"Total capturas: {len(brasil)}")

# Analisar cada ativo em cada data
datas = sorted(brasil['date'].unique())
ativos = sorted(brasil['ticker'].unique())

oportunidades_perdidas = []
oportunidades_validas = []

for data in datas[:3]:  # Primeiras 3 datas
    dados_data = brasil[brasil['date'] == data]
    
    for ticker in ativos[:5]:  # Primeiros 5 ativos
        dados_ticker = dados_data[dados_data['ticker'] == ticker]
        if dados_ticker.empty:
            continue
        
        primeira = dados_ticker.iloc[0]
        ultima = dados_ticker.iloc[-1]
        
        open_price = primeira.get('open_price', 0) or primeira.get('last_price', 0)
        close_price = ultima.get('close_price', 0) or ultima.get('last_price', 0)
        
        if open_price == 0 or close_price == 0:
            continue
        
        intraday_return = (close_price / open_price) - 1
        volume = ultima.get('volume', 0) or 0
        adv = ultima.get('adv', 0) or volume
        volume_ratio = volume / adv if adv > 0 else 1.0
        
        passa_intraday = intraday_return >= min_intraday
        passa_volume = volume_ratio >= min_volume
        
        if passa_intraday and passa_volume:
            oportunidades_validas.append({
                'data': data,
                'ticker': ticker,
                'intraday': intraday_return,
                'volume_ratio': volume_ratio
            })
        else:
            oportunidades_perdidas.append({
                'data': data,
                'ticker': ticker,
                'intraday': intraday_return,
                'volume_ratio': volume_ratio,
                'motivo': 'intraday' if not passa_intraday else 'volume'
            })

print(f"\nOportunidades VALIDAS encontradas: {len(oportunidades_validas)}")
for opp in oportunidades_validas[:10]:
    print(f"  {opp['data']} {opp['ticker']}: intraday={opp['intraday']*100:.2f}%, volume={opp['volume_ratio']:.2f}x")

print(f"\nOportunidades PERDIDAS (nao passam filtros): {len(oportunidades_perdidas)}")
for opp in oportunidades_perdidas[:10]:
    print(f"  {opp['data']} {opp['ticker']}: intraday={opp['intraday']*100:.2f}%, volume={opp['volume_ratio']:.2f}x (motivo: {opp['motivo']})")

print("\n" + "=" * 80)

