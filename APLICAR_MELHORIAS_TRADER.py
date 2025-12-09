#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para aplicar melhorias sugeridas pela análise de trader experiente.
Ajusta parâmetros no config.json baseado em dados reais.
"""
import json
from pathlib import Path

def aplicar_melhorias():
    """Aplica melhorias sugeridas pela análise."""
    print("=" * 80)
    print("APLICANDO MELHORIAS SUGERIDAS PELA ANÁLISE")
    print("=" * 80)
    
    config_path = Path('config.json')
    
    # Ler configuração atual
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("\n📊 CONFIGURAÇÃO ATUAL:")
    print("-" * 80)
    daytrade = config.get('daytrade_options', {})
    print(f"  min_intraday_return: {daytrade.get('min_intraday_return', 0)*100:.2f}%")
    print(f"  delta_min: {daytrade.get('delta_min', 0):.2f}")
    print(f"  delta_max: {daytrade.get('delta_max', 0):.2f}")
    print(f"  take_profit_pct: {daytrade.get('take_profit_pct', 0)*100:.2f}%")
    print(f"  stop_loss_pct: {daytrade.get('stop_loss_pct', 0)*100:.2f}%")
    print(f"  min_gain_loss_ratio: {daytrade.get('min_gain_loss_ratio', 0):.2f}")
    
    # Aplicar melhorias sugeridas
    print("\n✅ APLICANDO MELHORIAS:")
    print("-" * 80)
    
    # Backup da configuração atual
    backup_path = Path('config.json.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Backup criado: {backup_path}")
    
    # Ajustar parâmetros baseado em análise
    if 'daytrade_options' not in config:
        config['daytrade_options'] = {}
    
    daytrade = config['daytrade_options']
    
    # 1. Reduzir min_intraday_return (baseado em percentil 25: 0.62%)
    daytrade['min_intraday_return'] = 0.006  # 0.6%
    print(f"  ✅ min_intraday_return: {daytrade.get('min_intraday_return', 0)*100:.2f}% → 0.60%")
    
    # 2. Apertar delta (baseado em percentil 25-75: 0.419-0.516)
    daytrade['delta_min'] = 0.40  # Era 0.20
    daytrade['delta_max'] = 0.55  # Era 0.65
    print(f"  ✅ delta_min: {daytrade.get('delta_min', 0):.2f} → 0.40")
    print(f"  ✅ delta_max: {daytrade.get('delta_max', 0):.2f} → 0.55")
    
    # 3. Aumentar Take Profit (baseado em média real: 1.18%)
    daytrade['take_profit_pct'] = 0.012  # 1.2%
    print(f"  ✅ take_profit_pct: {daytrade.get('take_profit_pct', 0)*100:.2f}% → 1.20%")
    
    # 4. Reduzir Stop Loss (mais realista para daytrade)
    daytrade['stop_loss_pct'] = 0.15  # 15%
    print(f"  ✅ stop_loss_pct: {daytrade.get('stop_loss_pct', 0)*100:.2f}% → 15.00%")
    
    # 5. Ajustar min_gain_loss_ratio (1.2% / 15% = 0.08)
    daytrade['min_gain_loss_ratio'] = 0.08
    print(f"  ✅ min_gain_loss_ratio: {daytrade.get('min_gain_loss_ratio', 0):.2f} → 0.08")
    
    # Salvar configuração atualizada
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n✅ CONFIGURAÇÃO ATUALIZADA:")
    print("-" * 80)
    print(f"  min_intraday_return: {daytrade['min_intraday_return']*100:.2f}%")
    print(f"  delta_min: {daytrade['delta_min']:.2f}")
    print(f"  delta_max: {daytrade['delta_max']:.2f}")
    print(f"  take_profit_pct: {daytrade['take_profit_pct']*100:.2f}%")
    print(f"  stop_loss_pct: {daytrade['stop_loss_pct']*100:.2f}%")
    print(f"  min_gain_loss_ratio: {daytrade['min_gain_loss_ratio']:.2f}")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("-" * 80)
    print("  1. Reiniciar agentes para aplicar novas configurações")
    print("  2. Monitorar resultados nas próximas horas/dias")
    print("  3. Comparar com resultados anteriores")
    print("  4. Refinar baseado em novos dados")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    aplicar_melhorias()

