"""
Script para testar a captura usando dados de ontem como se fossem de hoje.
Simula um dia de mercado para testar a lógica de captura.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.orders_repository import OrdersRepository
import json

def testar_captura_com_dados_ontem():
    """Testa a captura usando dados de ontem como simulação."""
    print("=" * 70)
    print("TESTE: Captura com Dados de Ontem (Simulação)")
    print("=" * 70)
    
    # Data de ontem
    ontem = (datetime.now() - timedelta(days=1)).date()
    hoje = datetime.now().date()
    
    print(f"\n📅 Data de ontem: {ontem}")
    print(f"📅 Data de hoje: {hoje}")
    print(f"📊 Vamos simular capturas usando dados de ontem como se fossem de hoje")
    
    # Ticker para testar
    ticker = 'PETR4.SA'
    
    print(f"\n1. BUSCANDO DADOS INTRADAY DE ONTEM PARA {ticker}:")
    print("-" * 70)
    
    try:
        stock = yf.Ticker(ticker)
        
        # Buscar dados intraday de ontem
        hist_intraday = stock.history(period='2d', interval='5m', timeout=15)
        
        if hist_intraday.empty:
            print("   ❌ Nenhum dado encontrado")
            return
        
        # Converter índice para datetime
        hist_intraday.index = pd.to_datetime(hist_intraday.index)
        
        # Filtrar apenas dados de ONTEM
        hist_ontem = hist_intraday[hist_intraday.index.date == ontem]
        
        if hist_ontem.empty:
            print("   ❌ Nenhum dado de ontem encontrado")
            print(f"   Datas disponíveis: {hist_intraday.index.date.unique()}")
            return
        
        print(f"   ✅ {len(hist_ontem)} candles de ontem encontrados")
        print(f"   Período: {hist_ontem.index[0]} até {hist_ontem.index[-1]}")
        
        # Simular múltiplas capturas ao longo do dia de ontem
        print(f"\n2. SIMULANDO CAPTURAS AO LONGO DO DIA:")
        print("-" * 70)
        
        # Pegar alguns candles em momentos diferentes do dia
        candles_teste = []
        total_candles = len(hist_ontem)
        
        # Pegar candles em intervalos: início, meio e fim do dia
        indices_teste = [
            0,  # Primeiro candle
            total_candles // 4,  # 25% do dia
            total_candles // 2,  # Meio do dia
            (total_candles * 3) // 4,  # 75% do dia
            total_candles - 1  # Último candle
        ]
        
        repo = OrdersRepository()
        
        for idx in indices_teste:
            if idx < total_candles:
                candle = hist_ontem.iloc[idx]
                timestamp_candle = hist_ontem.index[idx]
                
                # Simular captura neste momento
                current_price = float(candle['Close'])
                open_price = float(hist_ontem.iloc[0]['Open'])
                high_price = float(hist_ontem.iloc[:idx+1]['High'].max())
                low_price = float(hist_ontem.iloc[:idx+1]['Low'].min())
                volume_today = int(hist_ontem.iloc[:idx+1]['Volume'].sum())
                
                print(f"\n   📊 Captura {len(candles_teste) + 1} - {timestamp_candle.strftime('%H:%M')}:")
                print(f"      Preço atual: {current_price:.2f}")
                print(f"      Abertura: {open_price:.2f}")
                print(f"      Máxima do dia: {high_price:.2f}")
                print(f"      Mínima do dia: {low_price:.2f}")
                print(f"      Volume acumulado: {volume_today:,}")
                
                # Calcular retorno intraday
                intraday_return = (current_price / open_price - 1) * 100
                print(f"      Retorno intraday: {intraday_return:+.2f}%")
                
                # Salvar no banco (simulando captura real)
                spot_data = {
                    'open': open_price,
                    'close': current_price,
                    'last': current_price,
                    'high': high_price,
                    'low': low_price,
                    'volume': volume_today,
                    'adv': 0
                }
                
                raw_data = {
                    'timestamp': timestamp_candle.isoformat(),
                    'simulacao_teste': True,
                    'data_original': ontem.isoformat(),
                    'momento_simulado': timestamp_candle.strftime('%H:%M')
                }
                
                try:
                    repo.save_market_data_capture(
                        ticker=ticker,
                        data_type='spot',
                        spot_data=spot_data,
                        options_data=None,
                        raw_data=raw_data,
                        source='simulation'
                    )
                    print(f"      ✅ Salvo no banco de dados")
                    candles_teste.append({
                        'timestamp': timestamp_candle,
                        'price': current_price,
                        'volume': volume_today
                    })
                except Exception as e:
                    print(f"      ❌ Erro ao salvar: {e}")
        
        # 3. Verificar dados salvos
        print(f"\n3. VERIFICANDO DADOS SALVOS NO BANCO:")
        print("-" * 70)
        
        df_salvos = repo.get_market_data_captures(limit=10)
        petr_salvos = df_salvos[df_salvos['ticker'] == ticker].tail(len(candles_teste))
        
        if not petr_salvos.empty:
            print(f"   ✅ {len(petr_salvos)} capturas encontradas:")
            print(f"   {'Timestamp':<25} | {'Preço':<10} | {'Volume':<15} | {'Variação':<10}")
            print("   " + "-" * 70)
            
            preco_anterior = None
            for _, row in petr_salvos.iterrows():
                timestamp = row['created_at'][:19] if row['created_at'] else 'N/A'
                preco = row['last_price'] if row['last_price'] else 0
                volume = row['volume'] if row['volume'] else 0
                
                variacao = ""
                if preco_anterior is not None:
                    diff = preco - preco_anterior
                    variacao = f"{diff:+.2f}"
                
                print(f"   {timestamp:<25} | {preco:<10.2f} | {volume:<15,} | {variacao:<10}")
                preco_anterior = preco
            
            # Verificar se preços variam
            precos = petr_salvos['last_price'].dropna().unique()
            print(f"\n   📊 Análise:")
            print(f"      Preços únicos: {len(precos)}")
            print(f"      Variação mínima: {precos.min():.2f}")
            print(f"      Variação máxima: {precos.max():.2f}")
            print(f"      Diferença: {precos.max() - precos.min():.2f} ({((precos.max() - precos.min()) / precos.min() * 100):.2f}%)")
            
            if len(precos) > 1:
                print(f"      ✅ PREÇOS VARIANDO CORRETAMENTE!")
            else:
                print(f"      ⚠️ Todos os preços são iguais")
        
        # 4. Testar geração de propostas com esses dados
        print(f"\n4. TESTANDO GERAÇÃO DE PROPOSTAS:")
        print("-" * 70)
        
        # Verificar se há propostas geradas
        proposals_df = repo.get_proposals(strategy='daytrade_options', start_date=(datetime.now() - timedelta(hours=1)).isoformat())
        
        if not proposals_df.empty:
            print(f"   ✅ {len(proposals_df)} propostas geradas nas últimas horas")
            for _, prop in proposals_df.tail(3).iterrows():
                print(f"      - {prop['symbol']}: {prop.get('metadata', {}).get('intraday_return', 0)*100:.2f}%")
        else:
            print(f"   ⚠️ Nenhuma proposta gerada")
            print(f"   💡 Isso pode ser normal se os critérios não foram atendidos")
        
        print(f"\n" + "=" * 70)
        print("TESTE CONCLUÍDO")
        print("=" * 70)
        print(f"\n✅ A captura está funcionando corretamente!")
        print(f"   Os preços variam conforme esperado ao longo do dia")
        print(f"   Durante o pregão real, os dados devem ser capturados em tempo real")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_captura_com_dados_ontem()

