"""
Script para restaurar todos os módulos do diretório src/.
"""

import sys
from pathlib import Path

# Lista de módulos que precisam ser criados
modulos = [
    'pricing.py',
    'data_loader.py', 
    'market_data_api.py',
    'agents.py',
    'execution.py',
    'backtest.py',
    'backtest_parallel.py',
    'sizing.py',
    'strategies.py',
    'broker_adapters.py'
]

print("=" * 70)
print("RESTAURACAO DE MODULOS")
print("=" * 70)
print(f"\nModulos a restaurar: {len(modulos)}")
print("\nPor favor, peca ao assistente:")
print('  "Recrie todos os modulos do diretorio src/ do projeto')
print('   algoritimo_trade_agentes com todo o codigo completo"')
print("\nOu execute manualmente a criacao de cada arquivo.")
print("=" * 70)

