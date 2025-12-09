#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifica se todas as 3 implementações estão completas"""
import json

print("=" * 80)
print("VERIFICACAO FINAL DAS IMPLEMENTACOES")
print("=" * 80)

# 1. Verificar API de Futuros
try:
    from src.futures_data_api import FuturesDataAPI
    api = FuturesDataAPI()
    print("\n1. API de Futuros: OK")
    print(f"   Simbolos mapeados: {list(api.symbols_map.keys())}")
except Exception as e:
    print(f"\n1. API de Futuros: ERRO - {e}")

# 2. Verificar Estrategia de Futuros
try:
    from src.futures_strategy import FuturesDayTradeStrategy
    config = json.load(open('config.json'))
    strategy = FuturesDayTradeStrategy(config)
    print("\n2. Estrategia de Futuros: OK")
    print(f"   Config: {strategy.futures_config}")
except Exception as e:
    print(f"\n2. Estrategia de Futuros: ERRO - {e}")

# 3. Verificar Configuração
try:
    config = json.load(open('config.json'))
    print("\n3. Configuracao:")
    print(f"   Ativos brasileiros: {len(config['monitored_tickers'])}")
    print(f"   Contratos futuros: {len(config['monitored_futures'])}")
    print(f"   Futures daytrade config: {'futures_daytrade' in config}")
    if 'futures_daytrade' in config:
        print(f"   Futures enabled: {config['futures_daytrade'].get('enabled', False)}")
except Exception as e:
    print(f"\n3. Configuracao: ERRO - {e}")

# 4. Verificar MonitoringService
try:
    from src.monitoring_service import MonitoringService
    config = json.load(open('config.json'))
    service = MonitoringService(config)
    print("\n4. MonitoringService:")
    print(f"   Futures API disponivel: {hasattr(service, 'futures_api')}")
    if hasattr(service, 'futures_api'):
        print(f"   Futures API tipo: {type(service.futures_api).__name__}")
except Exception as e:
    print(f"\n4. MonitoringService: ERRO - {e}")

print("\n" + "=" * 80)
print("VERIFICACAO CONCLUIDA")
print("=" * 80)

