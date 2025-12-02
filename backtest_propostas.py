"""
Script para fazer backtest de todas as propostas geradas comparando com preço de fechamento.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json

sys.path.insert(0, str(Path(__file__).parent))

from src.orders_repository import OrdersRepository
from src.trading_schedule import TradingSchedule
import yfinance as yf

def backtest_propostas(data_inicio=None, data_fim=None):
    """Faz backtest de propostas comparando com preço de fechamento."""
    print("=" * 70)
    print("BACKTEST: Propostas vs Preço de Fechamento")
    print("=" * 70)
    
    repo = OrdersRepository()
    schedule = TradingSchedule()
    
    if not data_inicio:
        data_inicio = schedule.get_current_b3_time().date() - timedelta(days=7)
    if not data_fim:
        data_fim = schedule.get_current_b3_time().date()
    
    print(f"\n📅 Período: {data_inicio} a {data_fim}")
    
    # Buscar todas as propostas do período
    inicio_str = datetime.combine(data_inicio, datetime.min.time()).isoformat()
    fim_str = datetime.combine(data_fim, datetime.max.time()).isoformat()
    
    print(f"\n1. BUSCANDO PROPOSTAS:")
    print("-" * 70)
    
    proposals_df = repo.get_proposals()
    if proposals_df.empty:
        print("   ⚠️ Nenhuma proposta encontrada")
        return
    
    # Filtrar por data - converter para datetime com tratamento de timezone
    try:
        # Converter para datetime, normalizando timezones
        proposals_df['created_at'] = pd.to_datetime(proposals_df['created_at'], errors='coerce')
        
        # Extrair apenas a data (ignorar timezone)
        proposals_df['date_only'] = proposals_df['created_at'].apply(
            lambda x: x.date() if pd.notna(x) and hasattr(x, 'date') else None
        )
        
        # Filtrar por data
        proposals_periodo = proposals_df[
            (proposals_df['date_only'] >= data_inicio) &
            (proposals_df['date_only'] <= data_fim)
        ].copy()
        
        # Remover coluna auxiliar
        proposals_periodo = proposals_periodo.drop(columns=['date_only'])
        
    except Exception as e:
        print(f"   ⚠️ Erro ao filtrar por data: {e}")
        # Fallback: usar todas as propostas
        proposals_periodo = proposals_df
    
    print(f"   ✅ {len(proposals_periodo)} propostas encontradas no período")
    
    # Filtrar apenas daytrade
    daytrade_proposals = proposals_periodo[proposals_periodo['strategy'] == 'daytrade_options']
    print(f"   ✅ {len(daytrade_proposals)} propostas de daytrade")
    
    if daytrade_proposals.empty:
        print("   ⚠️ Nenhuma proposta de daytrade para analisar")
        return
    
    print(f"\n2. ANALISANDO PROPOSTAS:")
    print("-" * 70)
    
    resultados = []
    
    for idx, row in daytrade_proposals.iterrows():
        try:
            proposal_id = row['proposal_id']
            symbol = row['symbol']
            side = row['side']
            quantity = row['quantity']
            price_entry = row['price']
            created_at = row['created_at']
            metadata_str = row.get('metadata', '{}')
            
            # Parse metadata
            if isinstance(metadata_str, str):
                try:
                    metadata = json.loads(metadata_str.replace("'", '"'))
                except:
                    metadata = {}
            else:
                metadata = metadata_str
            
            underlying = metadata.get('underlying', symbol.split('_')[0] if '_' in symbol else symbol)
            take_profit_pct = metadata.get('take_profit_pct', 0.005)
            stop_loss_pct = metadata.get('stop_loss_pct', 0.40)
            entry_price = metadata.get('entry_price', price_entry)
            exit_price_tp = metadata.get('exit_price_tp', entry_price * (1 + take_profit_pct))
            exit_price_sl = metadata.get('exit_price_sl', entry_price * (1 - stop_loss_pct))
            
            # Buscar preço de fechamento do dia
            date_str = created_at.strftime('%Y-%m-%d')
            
            # Normalizar símbolo para yfinance
            ticker_yf = underlying
            if '.SA' not in ticker_yf and underlying not in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'DIS', 'NFLX']:
                ticker_yf = f"{underlying}.SA"
            
            try:
                stock = yf.Ticker(ticker_yf)
                hist = stock.history(start=date_str, end=(datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'))
                
                if hist.empty:
                    close_price = None
                else:
                    close_price = float(hist.iloc[-1]['Close'])
                
            except Exception as e:
                close_price = None
            
            if close_price is None:
                continue
            
            # Calcular resultado teórico
            if side == 'BUY':
                # Para opções, usar preço de fechamento do underlying
                # Simplificação: assumir que opção acompanha movimento do underlying proporcionalmente ao delta
                delta = metadata.get('delta', 0.5)
                
                # Movimento do underlying
                underlying_move = (close_price - entry_price) / entry_price if entry_price > 0 else 0
                
                # Movimento estimado da opção (simplificado)
                option_move = underlying_move * delta
                
                # Preço estimado de fechamento da opção
                if 'instrument_type' in row and row['instrument_type'] == 'options':
                    estimated_close = entry_price * (1 + option_move)
                else:
                    estimated_close = close_price
                
                # Verificar se atingiu TP ou SL
                if estimated_close >= exit_price_tp:
                    resultado = 'TP'
                    pnl_pct = take_profit_pct
                elif estimated_close <= exit_price_sl:
                    resultado = 'SL'
                    pnl_pct = -stop_loss_pct
                else:
                    resultado = 'ABERTO'
                    pnl_pct = (estimated_close - entry_price) / entry_price if entry_price > 0 else 0
            else:
                resultado = 'N/A'
                pnl_pct = 0
            
            resultados.append({
                'proposal_id': proposal_id,
                'symbol': symbol,
                'underlying': underlying,
                'date': date_str,
                'side': side,
                'entry_price': entry_price,
                'close_price': close_price,
                'exit_price_tp': exit_price_tp,
                'exit_price_sl': exit_price_sl,
                'estimated_close': estimated_close if side == 'BUY' else None,
                'resultado': resultado,
                'pnl_pct': pnl_pct,
                'take_profit_pct': take_profit_pct,
                'stop_loss_pct': stop_loss_pct,
                'delta': metadata.get('delta', 0),
                'intraday_return': metadata.get('intraday_return', 0),
                'volume_ratio': metadata.get('volume_ratio', 0)
            })
            
        except Exception as e:
            print(f"   ⚠️ Erro ao processar proposta {row.get('proposal_id', 'N/A')}: {e}")
            continue
    
    if not resultados:
        print("   ⚠️ Nenhum resultado calculado")
        return
    
    resultados_df = pd.DataFrame(resultados)
    
    print(f"\n3. RESULTADOS DO BACKTEST:")
    print("-" * 70)
    
    total = len(resultados_df)
    tp_count = len(resultados_df[resultados_df['resultado'] == 'TP'])
    sl_count = len(resultados_df[resultados_df['resultado'] == 'SL'])
    aberto_count = len(resultados_df[resultados_df['resultado'] == 'ABERTO'])
    
    print(f"   Total analisado: {total}")
    print(f"   Take Profit atingido: {tp_count} ({tp_count/total*100:.1f}%)")
    print(f"   Stop Loss atingido: {sl_count} ({sl_count/total*100:.1f}%)")
    print(f"   Ainda abertas: {aberto_count} ({aberto_count/total*100:.1f}%)")
    
    if total > 0:
        pnl_medio = resultados_df['pnl_pct'].mean() * 100
        pnl_total = resultados_df['pnl_pct'].sum() * 100
        print(f"\n   PnL médio por proposta: {pnl_medio:.2f}%")
        print(f"   PnL total acumulado: {pnl_total:.2f}%")
        
        # Taxa de acerto (TP vs SL)
        if tp_count + sl_count > 0:
            taxa_acerto = tp_count / (tp_count + sl_count) * 100
            print(f"   Taxa de acerto: {taxa_acerto:.1f}%")
    
    # Salvar resultados
    output_file = f"backtest_propostas_{data_inicio}_{data_fim}.csv"
    resultados_df.to_csv(output_file, index=False)
    print(f"\n   ✅ Resultados salvos em: {output_file}")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--inicio', help='Data de início (YYYY-MM-DD)')
    parser.add_argument('--fim', help='Data de fim (YYYY-MM-DD)')
    args = parser.parse_args()
    
    data_inicio = datetime.strptime(args.inicio, '%Y-%m-%d').date() if args.inicio else None
    data_fim = datetime.strptime(args.fim, '%Y-%m-%d').date() if args.fim else None
    
    backtest_propostas(data_inicio, data_fim)

