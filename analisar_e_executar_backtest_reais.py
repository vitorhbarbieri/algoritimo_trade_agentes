#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análise completa e execução de backtest com dados reais brasileiros
"""
import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orders_repository import OrdersRepository
from src.agents import DayTradeOptionsStrategy
from src.b3_costs import B3CostCalculator
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def analisar_e_executar():
    """Analisa dados reais e executa backtest."""
    print("=" * 100)
    print("ANALISE E BACKTEST COM DADOS REAIS BRASILEIROS")
    print("=" * 100)
    
    repo = OrdersRepository()
    calculator = B3CostCalculator()
    
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    cfg = config.get('daytrade_options', {})
    
    print("\n1. CARREGANDO DADOS REAIS...")
    captures = repo.get_market_data_captures()
    brasil = captures[captures['ticker'].str.contains('.SA', na=False)].copy()
    brasil = brasil[brasil['source'] == 'real']
    
    print(f"   Total: {len(brasil)} capturas de {brasil['ticker'].nunique()} ativos")
    
    brasil['timestamp'] = pd.to_datetime(brasil['timestamp'], errors='coerce')
    brasil['date'] = brasil['timestamp'].dt.date
    brasil = brasil.sort_values('timestamp')  # Ordenar ASC por timestamp
    
    datas = sorted(brasil['date'].unique())
    ativos = sorted(brasil['ticker'].unique())
    
    print(f"   Periodo: {datas[0]} a {datas[-1]} ({len(datas)} dias)")
    
    print("\n2. ANALISANDO DADOS POR DIA...")
    oportunidades_por_dia = {}
    
    for data in datas:
        dados_data = brasil[brasil['date'] == data].copy()
        oportunidades_dia = []
        
        for ticker in ativos:
            dados_ticker = dados_data[dados_data['ticker'] == ticker]
            if dados_ticker.empty or len(dados_ticker) < 2:
                continue
            
            # Primeira e última captura do dia (ordenadas por timestamp ASC)
            primeira = dados_ticker.iloc[0]
            ultima = dados_ticker.iloc[-1]
            
            open_price = primeira.get('open_price', 0) or primeira.get('last_price', 0)
            close_price = ultima.get('close_price', 0) or ultima.get('last_price', 0)
            
            if open_price == 0 or close_price == 0:
                continue
            
            intraday_return = (close_price / open_price) - 1 if open_price > 0 else 0
            volume = ultima.get('volume', 0) or 0
            adv = ultima.get('adv', 0) or volume
            volume_ratio = volume / adv if adv > 0 else 1.0
            
            passa_intraday = intraday_return >= cfg.get('min_intraday_return', 0.006)
            passa_volume = volume_ratio >= cfg.get('min_volume_ratio', 0.3)
            
            oportunidades_dia.append({
                'ticker': ticker,
                'open': open_price,
                'close': close_price,
                'intraday_return': intraday_return,
                'volume_ratio': volume_ratio,
                'passa_filtros': passa_intraday and passa_volume
            })
        
        oportunidades_por_dia[data] = oportunidades_dia
        
        # Estatísticas do dia
        validas = [o for o in oportunidades_dia if o['passa_filtros']]
        print(f"   {data}: {len(validas)}/{len(oportunidades_dia)} oportunidades validas")
        if validas:
            for v in validas[:3]:
                print(f"      {v['ticker']}: intraday={v['intraday_return']*100:.2f}%, volume={v['volume_ratio']:.2f}x")
    
    print("\n3. EXECUTANDO BACKTEST...")
    strategy = DayTradeOptionsStrategy(config, logger)
    propostas_todas = []
    
    for data in datas:
        dados_data = brasil[brasil['date'] == data].copy()
        market_data = {'spot': {}, 'options': {}}
        
        for ticker in ativos:
            dados_ticker = dados_data[dados_data['ticker'] == ticker]
            if dados_ticker.empty or len(dados_ticker) < 2:
                continue
            
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
        
        try:
            proposals = strategy.generate(config.get('nav', 1000000), pd.Timestamp(data), market_data)
            propostas_todas.extend([(data, p) for p in proposals])
            print(f"   {data}: {len(proposals)} propostas geradas")
        except Exception as e:
            print(f"   {data}: Erro - {str(e)[:50]}")
    
    print(f"\n4. RESULTADO FINAL:")
    print(f"   Total de propostas geradas: {len(propostas_todas)}")
    
    if propostas_todas:
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
        print(f"   Resultados salvos em: {output_file}")
        
        print(f"\n   Por ativo:")
        for ticker, count in df['ticker'].value_counts().head(10).items():
            print(f"     {ticker}: {count} propostas")
    else:
        print("\n   NENHUMA PROPOSTA GERADA")
        print("   Motivo: Dados nao passam pelos filtros (intraday_return < 0.6% ou volume_ratio < 0.3x)")
        print("\n   Recomendacao:")
        print("   - Verificar se capturas estao representando abertura/fechamento corretos")
        print("   - Considerar reduzir temporariamente min_intraday_return para testar")
        print("   - Coletar mais dados para ter historico de volumes")
    
    print("\n" + "=" * 100)
    return propostas_todas

if __name__ == '__main__':
    analisar_e_executar()

