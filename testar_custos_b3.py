#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste rápido do módulo de custos B3"""
from src.b3_costs import B3CostCalculator

calc = B3CostCalculator()
print('=' * 60)
print('TESTE DE CÁLCULO DE CUSTOS B3')
print('=' * 60)

# Exemplo: Operação de R$ 10.000 com lucro de 1%
entry_value = 10000
exit_value = 10100  # 1% de lucro

costs = calc.calculate_total_costs(entry_value, exit_value, 'options')

print(f'\nOperação:')
print(f'  Entrada: R$ {entry_value:,.2f}')
print(f'  Saída: R$ {exit_value:,.2f}')
print(f'\nResultados:')
print(f'  Lucro bruto: R$ {costs["profit_bruto"]:,.2f}')
print(f'  Custos operacionais: R$ {costs["total_operational_costs"]:,.2f}')
print(f'  Impostos (20%): R$ {costs["total_taxes"]:,.2f}')
print(f'  Lucro líquido: R$ {costs["profit_liquido"]:,.2f}')
print(f'\nRentabilidade:')
print(f'  Bruta: {costs["profit_pct_bruto"]:.3f}%')
print(f'  Líquida: {costs["profit_pct_liquido"]:.3f}%')
print(f'  Impacto dos custos: {(costs["profit_pct_bruto"] - costs["profit_pct_liquido"]):.3f}%')

print('\n' + '=' * 60)
print('RENTABILIDADE MÍNIMA NECESSÁRIA:')
print('=' * 60)
for valor in [1000, 5000, 10000, 50000]:
    min_pct = calc.calculate_minimum_profit_pct(valor, 'options')
    print(f'  R$ {valor:>8,.0f}: {min_pct*100:>6.3f}% mínimo')

