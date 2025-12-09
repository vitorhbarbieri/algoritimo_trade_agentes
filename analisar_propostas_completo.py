#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análise completa de propostas: aprovadas vs rejeitadas
Foco em daytrade: comprar início do dia, desfazer no final
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orders_repository import OrdersRepository
from src.trading_schedule import TradingSchedule
import yfinance as yf

def analisar_propostas_completo(data_inicio=None, data_fim=None):
    """Análise completa de propostas para refinar parâmetros."""
    print("=" * 80)
    print("ANÁLISE COMPLETA DE PROPOSTAS - DAYTRADE")
    print("=" * 80)
    
    repo = OrdersRepository()
    schedule = TradingSchedule()
    
    if not data_inicio:
        data_inicio = schedule.get_current_b3_time().date() - timedelta(days=7)
    if not data_fim:
        data_fim = schedule.get_current_b3_time().date()
    
    print(f"\n📅 Período: {data_inicio} a {data_fim}")
    
    # Buscar todas as propostas
    proposals_df = repo.get_proposals()
    if proposals_df.empty:
        print("⚠️ Nenhuma proposta encontrada")
        return
    
    # Filtrar por data
    proposals_df['created_at'] = pd.to_datetime(proposals_df['created_at'], errors='coerce')
    proposals_df['date_only'] = proposals_df['created_at'].apply(
        lambda x: x.date() if pd.notna(x) and hasattr(x, 'date') else None
    )
    
    proposals_periodo = proposals_df[
        (proposals_df['date_only'] >= data_inicio) &
        (proposals_df['date_only'] <= data_fim)
    ].copy()
    
    # Buscar avaliações de risco
    risk_eval_df = repo.get_risk_evaluations()
    
    # Mesclar propostas com avaliações
    proposals_merged = proposals_periodo.merge(
        risk_eval_df[['proposal_id', 'decision', 'reason']],
        on='proposal_id',
        how='left'
    )
    
    # Separar aprovadas e rejeitadas
    aprovadas = proposals_merged[proposals_merged['decision'] == 'APPROVE'].copy()
    rejeitadas = proposals_merged[proposals_merged['decision'] == 'REJECT'].copy()
    sem_avaliacao = proposals_merged[proposals_merged['decision'].isna()].copy()
    
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    print("-" * 80)
    print(f"Total de propostas: {len(proposals_merged)}")
    print(f"  ✅ Aprovadas: {len(aprovadas)} ({len(aprovadas)/len(proposals_merged)*100:.1f}%)")
    print(f"  ❌ Rejeitadas: {len(rejeitadas)} ({len(rejeitadas)/len(proposals_merged)*100:.1f}%)")
    print(f"  ⚠️ Sem avaliação: {len(sem_avaliacao)} ({len(sem_avaliacao)/len(proposals_merged)*100:.1f}%)")
    
    # Analisar apenas daytrade
    daytrade_aprovadas = aprovadas[aprovadas['strategy'] == 'daytrade_options'].copy()
    daytrade_rejeitadas = rejeitadas[rejeitadas['strategy'] == 'daytrade_options'].copy()
    
    print(f"\n🎯 DAYTRADE OPTIONS:")
    print("-" * 80)
    print(f"Aprovadas: {len(daytrade_aprovadas)}")
    print(f"Rejeitadas: {len(daytrade_rejeitadas)}")
    
    # Analisar métricas das aprovadas vs rejeitadas
    def extrair_metricas(df):
        """Extrai métricas do metadata."""
        metricas = []
        for idx, row in df.iterrows():
            try:
                metadata_str = row.get('metadata', '{}')
                if isinstance(metadata_str, str):
                    metadata = json.loads(metadata_str.replace("'", '"'))
                else:
                    metadata = metadata_str
                
                metricas.append({
                    'proposal_id': row['proposal_id'],
                    'intraday_return': metadata.get('intraday_return', 0),
                    'volume_ratio': metadata.get('volume_ratio', 0),
                    'comparison_score': metadata.get('comparison_score', 0),
                    'delta': metadata.get('delta', 0),
                    'take_profit_pct': metadata.get('take_profit_pct', 0),
                    'stop_loss_pct': metadata.get('stop_loss_pct', 0),
                    'gain_loss_ratio': metadata.get('gain_loss_ratio', 0),
                    'underlying': metadata.get('underlying', 'N/A'),
                    'date': row['date_only']
                })
            except:
                continue
        return pd.DataFrame(metricas)
    
    metricas_aprovadas = extrair_metricas(daytrade_aprovadas)
    metricas_rejeitadas = extrair_metricas(daytrade_rejeitadas)
    
    print(f"\n📈 MÉTRICAS COMPARATIVAS:")
    print("-" * 80)
    
    if not metricas_aprovadas.empty:
        print("\n✅ APROVADAS:")
        print(f"  Intraday Return médio: {metricas_aprovadas['intraday_return'].mean()*100:.2f}%")
        print(f"  Volume Ratio médio: {metricas_aprovadas['volume_ratio'].mean():.2f}x")
        print(f"  Comparison Score médio: {metricas_aprovadas['comparison_score'].mean():.2f}")
        print(f"  Delta médio: {metricas_aprovadas['delta'].mean():.3f}")
        print(f"  Gain/Loss Ratio médio: {metricas_aprovadas['gain_loss_ratio'].mean():.2f}")
    
    if not metricas_rejeitadas.empty:
        print("\n❌ REJEITADAS:")
        print(f"  Intraday Return médio: {metricas_rejeitadas['intraday_return'].mean()*100:.2f}%")
        print(f"  Volume Ratio médio: {metricas_rejeitadas['volume_ratio'].mean():.2f}x")
        print(f"  Comparison Score médio: {metricas_rejeitadas['comparison_score'].mean():.2f}")
        print(f"  Delta médio: {metricas_rejeitadas['delta'].mean():.3f}")
        print(f"  Gain/Loss Ratio médio: {metricas_rejeitadas['gain_loss_ratio'].mean():.2f}")
    
    # Analisar desempenho real das aprovadas
    print(f"\n💰 ANÁLISE DE DESEMPENHO DAS APROVADAS:")
    print("-" * 80)
    
    resultados_aprovadas = []
    for idx, row in daytrade_aprovadas.iterrows():
        try:
            proposal_id = row['proposal_id']
            symbol = row['symbol']
            created_at = row['created_at']
            metadata_str = row.get('metadata', '{}')
            
            if isinstance(metadata_str, str):
                metadata = json.loads(metadata_str.replace("'", '"'))
            else:
                metadata = metadata_str
            
            underlying = metadata.get('underlying', symbol.split('_')[0] if '_' in symbol else symbol)
            entry_price = metadata.get('entry_price', row.get('price', 0))
            take_profit_pct = metadata.get('take_profit_pct', 0.008)
            stop_loss_pct = metadata.get('stop_loss_pct', 0.30)
            
            # Buscar preço de fechamento
            date_str = created_at.strftime('%Y-%m-%d')
            ticker_yf = underlying if '.SA' in underlying or underlying in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'DIS', 'NFLX'] else f"{underlying}.SA"
            
            try:
                stock = yf.Ticker(ticker_yf)
                hist = stock.history(start=date_str, end=(datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'))
                
                if hist.empty:
                    continue
                
                close_price = float(hist.iloc[-1]['Close'])
                open_price = float(hist.iloc[0]['Open'])
                
                # Para daytrade: verificar movimento do dia
                day_move = (close_price - open_price) / open_price if open_price > 0 else 0
                
                # Calcular resultado teórico
                delta = metadata.get('delta', 0.5)
                option_move = day_move * delta
                
                if entry_price > 0:
                    estimated_close = entry_price * (1 + option_move)
                    
                    if estimated_close >= entry_price * (1 + take_profit_pct):
                        resultado = 'TP'
                        pnl_pct = take_profit_pct
                    elif estimated_close <= entry_price * (1 - stop_loss_pct):
                        resultado = 'SL'
                        pnl_pct = -stop_loss_pct
                    else:
                        resultado = 'ABERTO'
                        pnl_pct = (estimated_close - entry_price) / entry_price
                    
                    resultados_aprovadas.append({
                        'proposal_id': proposal_id,
                        'date': date_str,
                        'underlying': underlying,
                        'open_price': open_price,
                        'close_price': close_price,
                        'day_move': day_move,
                        'entry_price': entry_price,
                        'estimated_close': estimated_close,
                        'resultado': resultado,
                        'pnl_pct': pnl_pct,
                        'intraday_return': metadata.get('intraday_return', 0),
                        'volume_ratio': metadata.get('volume_ratio', 0),
                        'comparison_score': metadata.get('comparison_score', 0)
                    })
            except:
                continue
        except:
            continue
    
    if resultados_aprovadas:
        resultados_df = pd.DataFrame(resultados_aprovadas)
        
        print(f"\nTotal analisado: {len(resultados_df)}")
        tp_count = len(resultados_df[resultados_df['resultado'] == 'TP'])
        sl_count = len(resultados_df[resultados_df['resultado'] == 'SL'])
        aberto_count = len(resultados_df[resultados_df['resultado'] == 'ABERTO'])
        
        print(f"  ✅ Take Profit: {tp_count} ({tp_count/len(resultados_df)*100:.1f}%)")
        print(f"  ❌ Stop Loss: {sl_count} ({sl_count/len(resultados_df)*100:.1f}%)")
        print(f"  ⏳ Abertas: {aberto_count} ({aberto_count/len(resultados_df)*100:.1f}%)")
        
        if tp_count + sl_count > 0:
            taxa_acerto = tp_count / (tp_count + sl_count) * 100
            print(f"\n  Taxa de acerto: {taxa_acerto:.1f}%")
        
        pnl_medio = resultados_df['pnl_pct'].mean() * 100
        print(f"  PnL médio: {pnl_medio:.2f}%")
        
        # Análise por métricas
        print(f"\n📊 ANÁLISE POR MÉTRICAS:")
        print("-" * 80)
        
        # Filtrar apenas TP
        tp_df = resultados_df[resultados_df['resultado'] == 'TP']
        if not tp_df.empty:
            print("\n✅ Propostas que atingiram TP:")
            print(f"  Intraday Return médio: {tp_df['intraday_return'].mean()*100:.2f}%")
            print(f"  Volume Ratio médio: {tp_df['volume_ratio'].mean():.2f}x")
            print(f"  Comparison Score médio: {tp_df['comparison_score'].mean():.2f}")
        
        # Filtrar apenas SL
        sl_df = resultados_df[resultados_df['resultado'] == 'SL']
        if not sl_df.empty:
            print("\n❌ Propostas que atingiram SL:")
            print(f"  Intraday Return médio: {sl_df['intraday_return'].mean()*100:.2f}%")
            print(f"  Volume Ratio médio: {sl_df['volume_ratio'].mean():.2f}x")
            print(f"  Comparison Score médio: {sl_df['comparison_score'].mean():.2f}")
        
        # Salvar resultados
        output_file = f"analise_completa_{data_inicio}_{data_fim}.csv"
        resultados_df.to_csv(output_file, index=False)
        print(f"\n✅ Resultados salvos em: {output_file}")
    
    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES PARA REFINAR PARÂMETROS:")
    print("-" * 80)
    
    if not metricas_aprovadas.empty and not metricas_rejeitadas.empty:
        # Comparar médias
        diff_intraday = metricas_aprovadas['intraday_return'].mean() - metricas_rejeitadas['intraday_return'].mean()
        diff_volume = metricas_aprovadas['volume_ratio'].mean() - metricas_rejeitadas['volume_ratio'].mean()
        diff_score = metricas_aprovadas['comparison_score'].mean() - metricas_rejeitadas['comparison_score'].mean()
        
        print("\nDiferenças entre Aprovadas e Rejeitadas:")
        print(f"  Intraday Return: {diff_intraday*100:.2f}% (aprovadas são {diff_intraday*100:.2f}% melhores)")
        print(f"  Volume Ratio: {diff_volume:.2f}x (aprovadas são {diff_volume:.2f}x melhores)")
        print(f"  Comparison Score: {diff_score:.2f} (aprovadas são {diff_score:.2f} melhores)")
        
        # Sugerir thresholds mínimos baseados nas aprovadas
        min_intraday = metricas_aprovadas['intraday_return'].quantile(0.25)
        min_volume = metricas_aprovadas['volume_ratio'].quantile(0.25)
        min_score = metricas_aprovadas['comparison_score'].quantile(0.25)
        
        print(f"\nSugestão de thresholds mínimos (percentil 25 das aprovadas):")
        print(f"  min_intraday_return: {min_intraday*100:.2f}%")
        print(f"  min_volume_ratio: {min_volume:.2f}x")
        print(f"  min_comparison_score: {min_score:.2f}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--inicio', help='Data de início (YYYY-MM-DD)')
    parser.add_argument('--fim', help='Data de fim (YYYY-MM-DD)')
    args = parser.parse_args()
    
    data_inicio = datetime.strptime(args.inicio, '%Y-%m-%d').date() if args.inicio else None
    data_fim = datetime.strptime(args.fim, '%Y-%m-%d').date() if args.fim else None
    
    analisar_propostas_completo(data_inicio, data_fim)

