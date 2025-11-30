#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste rápido para verificar busca de dados reais"""

import json
from datetime import datetime, timedelta, time
import pytz
from simular_dia_mercado_real import SimuladorMercadoReal

# Carregar config
with open('config.json') as f:
    config = json.load(f)

# Data de referência (ontem)
data_ref = datetime.now(pytz.timezone('America/Sao_Paulo')) - timedelta(days=1)

print("=" * 70)
print("TESTE: Busca de Dados REAIS de Mercado")
print("=" * 70)
print(f"Data de referência: {data_ref.date()}")
print()

# Criar simulador
sim = SimuladorMercadoReal(config, data_ref)

# Testar busca de dados para um horário específico
print("Testando busca de dados REAIS para 10:30...")
dados = sim._buscar_dados_historicos(time(10, 30))

print()
print(f"Dados coletados: {len(dados['spot'])} tickers")
print()

if dados['spot']:
    print("Exemplos de dados REAIS coletados:")
    for i, (ticker, info) in enumerate(list(dados['spot'].items())[:5]):
        print(f"  {ticker}:")
        print(f"    Preço: R$ {info['last']:.2f}")
        print(f"    Abertura: R$ {info['open']:.2f}")
        print(f"    Máxima: R$ {info['high']:.2f}")
        print(f"    Mínima: R$ {info['low']:.2f}")
        print(f"    Volume: {info['volume']:,}")
        print(f"    Intervalo usado: {info.get('intervalo_usado', 'N/A')}")
        if info.get('timestamp_real'):
            print(f"    Timestamp real: {info['timestamp_real']}")
        print()
else:
    print("⚠️  Nenhum dado encontrado")

print("=" * 70)

