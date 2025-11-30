"""
Script para testar se a captura de dados está funcionando em tempo real.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.orders_repository import OrdersRepository
from src.monitoring_service import MonitoringService
import json
import pandas as pd
from datetime import datetime

def testar_captura():
    """Testa a captura de dados em tempo real."""
    print("=" * 70)
    print("TESTE: Captura de Dados em Tempo Real")
    print("=" * 70)
    
    # 1. Verificar dados anteriores de PETR4.SA
    print("\n1. VERIFICANDO DADOS ANTERIORES DE PETR4.SA:")
    print("-" * 70)
    
    repo = OrdersRepository()
    df = repo.get_market_data_captures(limit=50)
    petr = df[df['ticker'] == 'PETR4.SA'].tail(10)
    
    if not petr.empty:
        print(f"   Últimas {len(petr)} capturas:")
        print(f"   {'Timestamp':<25} | {'Preço':<10} | {'Volume':<15}")
        print("   " + "-" * 55)
        for _, row in petr.iterrows():
            timestamp = row['created_at'][:19] if row['created_at'] else 'N/A'
            preco = f"{row['last_price']:.2f}" if row['last_price'] else 'N/A'
            volume = f"{row['volume']:,}" if row['volume'] else '0'
            print(f"   {timestamp:<25} | {preco:<10} | {volume:<15}")
        
        # Verificar se preços estão variando
        precos = petr['last_price'].dropna().unique()
        print(f"\n   Preços únicos encontrados: {len(precos)}")
        if len(precos) == 1:
            print(f"   ⚠️ PROBLEMA: Todos os preços são iguais ({precos[0]:.2f})")
        else:
            print(f"   ✅ Preços variando: {precos.min():.2f} a {precos.max():.2f}")
    else:
        print("   ⚠️ Nenhuma captura anterior encontrada")
    
    # 2. Executar uma nova captura
    print("\n2. EXECUTANDO NOVA CAPTURA:")
    print("-" * 70)
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        monitoring = MonitoringService(config)
        result = monitoring.scan_market()
        
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Tickers processados: {result.get('tickers_processed', 0)}")
        print(f"   Dados capturados: {result.get('data_captured', 0)}")
        
        # 3. Verificar nova captura de PETR4.SA
        print("\n3. VERIFICANDO NOVA CAPTURA DE PETR4.SA:")
        print("-" * 70)
        
        df_novo = repo.get_market_data_captures(limit=5)
        petr_novo = df_novo[df_novo['ticker'] == 'PETR4.SA'].tail(1)
        
        if not petr_novo.empty:
            row = petr_novo.iloc[0]
            print(f"   Timestamp: {row['created_at']}")
            print(f"   Preço: {row['last_price']:.2f}")
            print(f"   Volume: {row['volume']:,}")
            print(f"   Abertura: {row['open_price']:.2f}")
            print(f"   Máxima: {row['high_price']:.2f}")
            print(f"   Mínima: {row['low_price']:.2f}")
            
            # Comparar com captura anterior
            if not petr.empty:
                preco_anterior = petr.iloc[-1]['last_price']
                preco_atual = row['last_price']
                variacao = preco_atual - preco_anterior
                variacao_pct = (variacao / preco_anterior * 100) if preco_anterior > 0 else 0
                
                print(f"\n   Comparação com captura anterior:")
                print(f"   Preço anterior: {preco_anterior:.2f}")
                print(f"   Preço atual: {preco_atual:.2f}")
                print(f"   Variação: {variacao:+.2f} ({variacao_pct:+.2f}%)")
                
                if abs(variacao) < 0.01:
                    print(f"   ⚠️ ATENÇÃO: Preço praticamente igual (diferença < R$ 0.01)")
                    print(f"   Isso pode indicar:")
                    print(f"      - Mercado estático")
                    print(f"      - Mercado fechado (usando último preço)")
                    print(f"      - Dados não atualizados")
                else:
                    print(f"   ✅ Preço variando corretamente")
        else:
            print("   ⚠️ Nenhuma nova captura de PETR4.SA encontrada")
    
    except Exception as e:
        print(f"   ❌ Erro ao executar captura: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Teste direto com yfinance
    print("\n4. TESTE DIRETO COM YFINANCE:")
    print("-" * 70)
    
    try:
        import yfinance as yf
        stock = yf.Ticker('PETR4.SA')
        
        # Tentar intraday
        hist = stock.history(period='1d', interval='5m', timeout=10)
        today = datetime.now().date()
        
        if not hist.empty:
            hist.index = pd.to_datetime(hist.index)
            hist_today = hist[hist.index.date == today]
            
            print(f"   Total de candles: {len(hist)}")
            print(f"   Data do primeiro candle: {hist.index[0].date()}")
            print(f"   Data do último candle: {hist.index[-1].date()}")
            print(f"   Data de hoje: {today}")
            print(f"   Candles de HOJE: {len(hist_today)}")
            
            if not hist_today.empty:
                print(f"   ✅ Dados de HOJE disponíveis!")
                print(f"   Último preço de HOJE: {hist_today.iloc[-1]['Close']:.2f}")
            else:
                print(f"   ⚠️ Nenhum candle de HOJE encontrado")
                print(f"   Último preço disponível: {hist.iloc[-1]['Close']:.2f}")
                print(f"   (Pode ser de ontem se mercado fechado)")
        else:
            print("   ❌ Nenhum dado retornado pelo yfinance")
    
    except Exception as e:
        print(f"   ❌ Erro ao testar yfinance: {e}")
    
    print("\n" + "=" * 70)
    print("TESTE CONCLUÍDO")
    print("=" * 70)

if __name__ == '__main__':
    testar_captura()

