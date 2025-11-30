"""
Script para analisar dados de mercado capturados e sugerir critérios realistas.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.orders_repository import OrdersRepository
import pandas as pd
import json
from datetime import datetime, timedelta

def analisar_dados_mercado():
    """Analisa dados capturados e sugere critérios."""
    print("=" * 70)
    print("ANÁLISE DE DADOS DE MERCADO - SUGESTÃO DE CRITÉRIOS")
    print("=" * 70)
    
    orders_repo = OrdersRepository()
    
    # 1. Analisar capturas de dados (últimas 48h)
    print("\n1. ANÁLISE DE CAPTURAS DE DADOS:")
    print("-" * 70)
    
    captures_df = orders_repo.get_market_data_captures(limit=500)
    
    if captures_df.empty:
        print("❌ Nenhuma captura encontrada no banco de dados")
        return
    
    # Filtrar últimas 48h
    captures_df['created_at'] = pd.to_datetime(captures_df['created_at'], errors='coerce', utc=True)
    two_days_ago = pd.Timestamp.now(tz='UTC') - timedelta(days=2)
    recent_captures = captures_df[captures_df['created_at'] >= two_days_ago]
    
    print(f"   Total de capturas (últimas 48h): {len(recent_captures)}")
    
    if recent_captures.empty:
        print("   ⚠️ Nenhuma captura nas últimas 48h")
        recent_captures = captures_df.tail(100)  # Usar últimas 100 se não houver dados recentes
    
    # 2. Analisar dados spot capturados
    print("\n2. ANÁLISE DE DADOS SPOT:")
    print("-" * 70)
    
    # Filtrar apenas dados spot
    spot_captures = recent_captures[recent_captures['data_type'] == 'spot'].copy()
    
    if spot_captures.empty:
        print("   ❌ Nenhum dado spot encontrado")
        return
    
    spot_df = spot_captures.copy()
    
    # Calcular estatísticas
    print(f"   Total de registros spot: {len(spot_df)}")
    print(f"   Tickers únicos: {spot_df['ticker'].nunique()}")
    
    # Calcular intraday returns usando as colunas do banco
    spot_df['intraday_return'] = (spot_df['last_price'] / spot_df['open_price'] - 1) * 100
    spot_df = spot_df[spot_df['open_price'] > 0]  # Remover zeros
    
    if len(spot_df) > 0:
        intraday_returns = spot_df['intraday_return'].abs()
        
        print(f"\n   📊 ESTATÍSTICAS DE RETORNO INTRADAY:")
        print(f"      Média: {intraday_returns.mean():.3f}%")
        print(f"      Mediana: {intraday_returns.median():.3f}%")
        print(f"      Percentil 25: {intraday_returns.quantile(0.25):.3f}%")
        print(f"      Percentil 50: {intraday_returns.quantile(0.50):.3f}%")
        print(f"      Percentil 75: {intraday_returns.quantile(0.75):.3f}%")
        print(f"      Percentil 90: {intraday_returns.quantile(0.90):.3f}%")
        print(f"      Percentil 95: {intraday_returns.quantile(0.95):.3f}%")
        print(f"      Máximo: {intraday_returns.max():.3f}%")
        
        # Sugestão baseada em percentil 50 (mediana)
        suggested_min_return = max(0.001, intraday_returns.quantile(0.50) / 100)  # 50% dos casos
        print(f"\n   💡 SUGESTÃO min_intraday_return: {suggested_min_return:.4f} ({suggested_min_return*100:.2f}%)")
        print(f"      (Baseado na mediana: {intraday_returns.median()/100:.4f})")
    
    # Analisar volumes
    print(f"\n   📊 ESTATÍSTICAS DE VOLUME:")
    volumes = spot_df[spot_df['volume'] > 0]['volume']
    
    if len(volumes) > 0:
        print(f"      Média: {volumes.mean():,.0f}")
        print(f"      Mediana: {volumes.median():,.0f}")
        print(f"      Percentil 25: {volumes.quantile(0.25):,.0f}")
        print(f"      Percentil 50: {volumes.median():,.0f}")
        print(f"      Percentil 75: {volumes.quantile(0.75):,.0f}")
        
        # Usar ADV se disponível, senão calcular volume ratio usando mediana
        adv_available = spot_df[spot_df['adv'] > 0]['adv']
        if len(adv_available) > 0:
            # Calcular volume ratio usando ADV real
            spot_df_with_adv = spot_df[spot_df['adv'] > 0].copy()
            spot_df_with_adv['volume_ratio_calc'] = spot_df_with_adv['volume'] / spot_df_with_adv['adv']
            
            volume_ratios_valid = spot_df_with_adv[spot_df_with_adv['volume_ratio_calc'] > 0]['volume_ratio_calc']
            
            print(f"\n   📊 ESTATÍSTICAS DE VOLUME RATIO (usando ADV):")
            if len(volume_ratios_valid) > 0:
                print(f"      Média: {volume_ratios_valid.mean():.3f}")
                print(f"      Mediana: {volume_ratios_valid.median():.3f}")
                print(f"      Percentil 25: {volume_ratios_valid.quantile(0.25):.3f}")
                print(f"      Percentil 50: {volume_ratios_valid.quantile(0.50):.3f}")
                print(f"      Percentil 75: {volume_ratios_valid.quantile(0.75):.3f}")
                
                suggested_min_volume_ratio = max(0.05, volume_ratios_valid.quantile(0.20))  # 20% dos casos
                print(f"\n   💡 SUGESTÃO min_volume_ratio: {suggested_min_volume_ratio:.3f}")
                print(f"      (Baseado no percentil 20: {volume_ratios_valid.quantile(0.20):.3f})")
        else:
            # Estimar usando mediana como proxy do ADV
            avg_volume = volumes.median()
            volume_ratios = spot_df['volume'] / avg_volume
            
            print(f"\n   📊 ESTATÍSTICAS DE VOLUME RATIO (estimado - ADV não disponível):")
            volume_ratios_valid = volume_ratios[volume_ratios > 0]
            if len(volume_ratios_valid) > 0:
                print(f"      Média: {volume_ratios_valid.mean():.3f}")
                print(f"      Mediana: {volume_ratios_valid.median():.3f}")
                print(f"      Percentil 25: {volume_ratios_valid.quantile(0.25):.3f}")
                
                suggested_min_volume_ratio = max(0.05, volume_ratios_valid.quantile(0.20))  # 20% dos casos
                print(f"\n   💡 SUGESTÃO min_volume_ratio: {suggested_min_volume_ratio:.3f}")
                print(f"      (Baseado no percentil 20: {volume_ratios_valid.quantile(0.20):.3f})")
    
    # 3. Analisar dados de opções (se houver)
    print("\n3. ANÁLISE DE DADOS DE OPÇÕES:")
    print("-" * 70)
    
    # Filtrar capturas de opções
    options_captures = recent_captures[recent_captures['data_type'] == 'options'].copy()
    
    options_data_list = []
    for _, capture in options_captures.iterrows():
        try:
            options_json = capture.get('options_data', '[]')
            if isinstance(options_json, str):
                options_data = json.loads(options_json)
            else:
                options_data = options_json if isinstance(options_json, list) else []
            
            if isinstance(options_data, list):
                for opt in options_data:
                    if isinstance(opt, dict):
                        options_data_list.append({
                            'underlying': opt.get('underlying', capture.get('ticker', '')),
                            'strike': opt.get('strike', 0),
                            'expiry': opt.get('expiry', ''),
                            'delta': opt.get('delta', 0),
                            'gamma': opt.get('gamma', 0),
                            'vega': opt.get('vega', 0),
                            'iv': opt.get('iv', opt.get('implied_volatility', 0)),
                            'spread_pct': opt.get('spread_pct', 0),
                            'volume': opt.get('volume', 0),
                            'days_to_expiry': opt.get('days_to_expiry', 0),
                            'option_type': opt.get('option_type', 'C')
                        })
        except Exception as e:
            continue
    
    if options_data_list:
        options_df = pd.DataFrame(options_data_list)
        print(f"   Total de registros de opções: {len(options_df)}")
        
        # Filtrar apenas CALLs
        if 'option_type' in options_df.columns:
            calls_df = options_df[options_df['option_type'] == 'C']
        else:
            calls_df = options_df
        
        if len(calls_df) > 0:
            print(f"\n   📊 ESTATÍSTICAS DE DELTA (CALLs):")
            deltas = calls_df['delta'].abs()
            print(f"      Média: {deltas.mean():.3f}")
            print(f"      Mediana: {deltas.median():.3f}")
            print(f"      Percentil 25: {deltas.quantile(0.25):.3f}")
            print(f"      Percentil 50: {deltas.quantile(0.50):.3f}")
            print(f"      Percentil 75: {deltas.quantile(0.75):.3f}")
            
            print(f"\n   📊 ESTATÍSTICAS DE DTE (Days to Expiry):")
            dte = calls_df[calls_df['days_to_expiry'] > 0]['days_to_expiry']
            if len(dte) > 0:
                print(f"      Média: {dte.mean():.1f} dias")
                print(f"      Mediana: {dte.median():.1f} dias")
                print(f"      Percentil 25: {dte.quantile(0.25):.1f} dias")
                print(f"      Percentil 50: {dte.quantile(0.50):.1f} dias")
                print(f"      Percentil 75: {dte.quantile(0.75):.1f} dias")
            
            print(f"\n   📊 ESTATÍSTICAS DE SPREAD (%):")
            spreads = calls_df[calls_df['spread_pct'] > 0]['spread_pct'] * 100
            if len(spreads) > 0:
                print(f"      Média: {spreads.mean():.2f}%")
                print(f"      Mediana: {spreads.median():.2f}%")
                print(f"      Percentil 75: {spreads.quantile(0.75):.2f}%")
                print(f"      Percentil 90: {spreads.quantile(0.90):.2f}%")
                
                suggested_max_spread = min(0.15, spreads.quantile(0.75) / 100)  # 75% dos casos
                print(f"\n   💡 SUGESTÃO max_spread_pct: {suggested_max_spread:.3f} ({suggested_max_spread*100:.2f}%)")
            
            print(f"\n   📊 ESTATÍSTICAS DE VOLUME DE OPÇÕES:")
            opt_volumes = calls_df[calls_df['volume'] > 0]['volume']
            if len(opt_volumes) > 0:
                print(f"      Média: {opt_volumes.mean():,.0f}")
                print(f"      Mediana: {opt_volumes.median():,.0f}")
                print(f"      Percentil 25: {opt_volumes.quantile(0.25):,.0f}")
                
                suggested_min_opt_volume = max(50, opt_volumes.quantile(0.25))
                print(f"\n   💡 SUGESTÃO min_option_volume: {int(suggested_min_opt_volume)}")
    
    # 4. Resumo e sugestões
    print("\n" + "=" * 70)
    print("RESUMO DE SUGESTÕES PARA config.json")
    print("=" * 70)
    
    print("\n📋 CRITÉRIOS SUGERIDOS (baseados em dados reais):")
    print("-" * 70)
    
    suggestions = {}
    
    if len(spot_df) > 0:
        intraday_returns = spot_df['intraday_return'].abs()
        # Usar percentil 20 para capturar mais oportunidades (80% dos casos passarão)
        suggestions['min_intraday_return'] = max(0.001, intraday_returns.quantile(0.20) / 100)
        print(f"   min_intraday_return: {suggestions['min_intraday_return']:.4f} ({suggestions['min_intraday_return']*100:.2f}%)")
        print(f"      (Atual: 0.0050 = 0.50%)")
        diff = (suggestions['min_intraday_return'] - 0.005) * 100
        if diff < 0:
            print(f"      ⬇️ Redução sugerida: {abs(diff):.2f}%")
        else:
            print(f"      ⬆️ Aumento sugerido: {diff:.2f}%")
    
    if 'volume_ratios_valid' in locals() and len(volume_ratios_valid) > 0:
        suggestions['min_volume_ratio'] = max(0.05, volume_ratios_valid.quantile(0.15))  # 15% dos casos (mais oportunidades)
        print(f"\n   min_volume_ratio: {suggestions['min_volume_ratio']:.3f}")
        print(f"      (Atual: 0.25)")
        diff = 0.25 - suggestions['min_volume_ratio']
        if diff > 0:
            print(f"      ⬇️ Redução sugerida: {diff:.3f}")
        else:
            print(f"      ⬆️ Aumento sugerido: {abs(diff):.3f}")
    
    if 'calls_df' in locals() and len(calls_df) > 0:
        deltas = calls_df['delta'].abs()
        suggestions['delta_min'] = max(0.10, deltas.quantile(0.15))  # Mais flexível
        suggestions['delta_max'] = min(0.80, deltas.quantile(0.85))
        print(f"\n   delta_min: {suggestions['delta_min']:.2f}")
        print(f"      (Atual: 0.20)")
        print(f"   delta_max: {suggestions['delta_max']:.2f}")
        print(f"      (Atual: 0.60)")
        
        dte = calls_df[calls_df['days_to_expiry'] > 0]['days_to_expiry']
        if len(dte) > 0:
            suggestions['max_dte'] = int(min(21, dte.quantile(0.80)))  # Mais flexível
            print(f"\n   max_dte: {suggestions['max_dte']} dias")
            print(f"      (Atual: 7 dias)")
            print(f"      ⬆️ Aumento sugerido: {suggestions['max_dte'] - 7} dias")
        
        spreads = calls_df[calls_df['spread_pct'] > 0]['spread_pct']
        if len(spreads) > 0:
            suggestions['max_spread_pct'] = min(0.15, spreads.quantile(0.80))  # Mais flexível
            print(f"\n   max_spread_pct: {suggestions['max_spread_pct']:.3f} ({suggestions['max_spread_pct']*100:.2f}%)")
            print(f"      (Atual: 0.05 = 5.00%)")
            print(f"      ⬆️ Aumento sugerido: {(suggestions['max_spread_pct'] - 0.05)*100:.2f}%")
        
        opt_volumes = calls_df[calls_df['volume'] > 0]['volume']
        if len(opt_volumes) > 0:
            suggestions['min_option_volume'] = int(max(50, opt_volumes.quantile(0.15)))  # Mais flexível
            print(f"\n   min_option_volume: {suggestions['min_option_volume']}")
            print(f"      (Atual: 200)")
            print(f"      ⬇️ Redução sugerida: {200 - suggestions['min_option_volume']}")
    else:
        # Valores padrão mais flexíveis se não houver dados de opções
        suggestions['delta_min'] = 0.15
        suggestions['delta_max'] = 0.70
        suggestions['max_dte'] = 14
        suggestions['max_spread_pct'] = 0.10
        suggestions['min_option_volume'] = 100
        print("\n   ⚠️ Nenhum dado de opções encontrado, usando valores padrão flexíveis:")
        print(f"      delta_min: {suggestions['delta_min']:.2f} (Atual: 0.20)")
        print(f"      delta_max: {suggestions['delta_max']:.2f} (Atual: 0.60)")
        print(f"      max_dte: {suggestions['max_dte']} dias (Atual: 7)")
        print(f"      max_spread_pct: {suggestions['max_spread_pct']:.3f} (Atual: 0.05)")
        print(f"      min_option_volume: {suggestions['min_option_volume']} (Atual: 200)")
    
    # Manter take_profit_pct como solicitado (0.50%)
    suggestions['take_profit_pct'] = 0.005  # 0.50%
    print(f"\n   take_profit_pct: {suggestions['take_profit_pct']:.4f} ({suggestions['take_profit_pct']*100:.2f}%)")
    print(f"      (Mantido conforme solicitado)")
    
    # Salvar sugestões
    print("\n" + "=" * 70)
    print("💾 SUGESTÕES SALVAS EM: sugestoes_criterios.json")
    print("=" * 70)
    
    with open('sugestoes_criterios.json', 'w', encoding='utf-8') as f:
        json.dump(suggestions, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Análise concluída!")
    print("\n📝 PRÓXIMOS PASSOS:")
    print("   1. Revisar as sugestões acima")
    print("   2. Aplicar em config.json se aprovadas")
    print("   3. Testar com os novos critérios")

if __name__ == '__main__':
    analisar_dados_mercado()

