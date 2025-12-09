#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Executa backtest com dados reais brasileiros e gera análise completa
"""
import sys
from pathlib import Path
import pandas as pd
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orders_repository import OrdersRepository
from src.agents import DayTradeOptionsStrategy
from src.b3_costs import B3CostCalculator
import logging

logging.basicConfig(level=logging.WARNING)  # Reduzir logs
logger = logging.getLogger(__name__)

def executar_backtest():
    """Executa backtest com dados reais."""
    print("=" * 100)
    print("BACKTEST COM DADOS REAIS BRASILEIROS")
    print("=" * 100)
    
    repo = OrdersRepository()
    calculator = B3CostCalculator()
    
    # Carregar configuração
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Buscar dados reais
    print("\n1. Carregando dados reais brasileiros...")
    captures = repo.get_market_data_captures()
    brasil = captures[captures['ticker'].str.contains('.SA', na=False)].copy()
    brasil = brasil[brasil['source'] == 'real']
    
    print(f"   Total: {len(brasil)} capturas de {brasil['ticker'].nunique()} ativos")
    
    # Processar por data
    brasil['timestamp'] = pd.to_datetime(brasil['timestamp'], errors='coerce')
    brasil['date'] = brasil['timestamp'].dt.date
    
    datas = sorted(brasil['date'].unique())
    ativos = sorted(brasil['ticker'].unique())
    
    print(f"   Periodo: {datas[0]} a {datas[-1]} ({len(datas)} dias)")
    
    # Criar estratégia
    strategy = DayTradeOptionsStrategy(config, logger)
    
    print("\n2. Executando backtest...")
    propostas_todas = []
    
    for data in datas:
        dados_data = brasil[brasil['date'] == data].copy()
        market_data = {'spot': {}, 'options': {}}
        
        for ticker in ativos:
            dados_ticker = dados_data[dados_data['ticker'] == ticker]
            if dados_ticker.empty:
                continue
            
            # Primeira e última captura do dia
            primeira = dados_ticker.iloc[0]
            ultima = dados_ticker.iloc[-1]
            
            open_price = primeira.get('open_price', 0) or primeira.get('last_price', 0)
            close_price = ultima.get('close_price', 0) or ultima.get('last_price', 0)
            
            if open_price == 0 or close_price == 0:
                continue
            
            intraday_return = (close_price / open_price) - 1
            volume = ultima.get('volume', 0) or 0
            adv = ultima.get('adv', 0) or volume
            volume_ratio = volume / adv if adv > 0 else 1.0
            
            market_data['spot'][ticker] = {
                'open': open_price,
                'close': close_price,
                'last': close_price,
                'high': ultima.get('high_price', 0) or max(open_price, close_price),
                'low': ultima.get('low_price', 0) or min(open_price, close_price),
                'volume': volume,
                'adv': adv,
                'intraday_return': intraday_return,
                'volume_ratio': volume_ratio
            }
        
        # Gerar propostas
        try:
            proposals = strategy.generate(config.get('nav', 1000000), pd.Timestamp(data), market_data)
            propostas_todas.extend([(data, p) for p in proposals])
            print(f"   {data}: {len(proposals)} propostas")
        except Exception as e:
            print(f"   {data}: Erro - {e}")
    
    print(f"\n3. Total de propostas geradas: {len(propostas_todas)}")
    
    if propostas_todas:
        # Salvar resultados
        resultados = []
        for data, prop in propostas_todas:
            resultados.append({
                'date': data,
                'proposal_id': prop.proposal_id,
                'ticker': prop.metadata.get('underlying', prop.symbol.split('_')[0]),
                'symbol': prop.symbol,
                'side': prop.side,
                'quantity': prop.quantity,
                'price': prop.price,
                'intraday_return': prop.metadata.get('intraday_return', 0),
                'volume_ratio': prop.metadata.get('volume_ratio', 0),
                'delta': prop.metadata.get('delta', 0),
                'comparison_score': prop.metadata.get('comparison_score', 0)
            })
        
        df = pd.DataFrame(resultados)
        output_file = f"propostas_backtest_reais_{datas[0]}_{datas[-1]}.csv"
        df.to_csv(output_file, index=False)
        print(f"\n4. Resultados salvos em: {output_file}")
        
        # Estatísticas
        print("\n5. Estatisticas:")
        print(f"   Por ativo:")
        for ticker, count in df['ticker'].value_counts().head(10).items():
            print(f"     {ticker}: {count} propostas")
        
        print(f"\n   Por data:")
        for date, count in df['date'].value_counts().items():
            print(f"     {date}: {count} propostas")
        
        print(f"\n   Intraday return medio: {df['intraday_return'].mean()*100:.3f}%")
        print(f"   Volume ratio medio: {df['volume_ratio'].mean():.2f}x")
    
    print("\n" + "=" * 100)
    return propostas_todas

if __name__ == '__main__':
    executar_backtest()

