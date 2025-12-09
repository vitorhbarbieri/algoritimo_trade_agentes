#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtest usando dados reais brasileiros capturados
Executa agentes baseados em dados de mercado reais temporizados
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orders_repository import OrdersRepository
from src.agents import TraderAgent, DayTradeOptionsStrategy
from src.b3_costs import B3CostCalculator
from src.trading_schedule import TradingSchedule
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def executar_backtest_dados_reais():
    """Executa backtest usando dados reais brasileiros."""
    print("=" * 100)
    print("BACKTEST COM DADOS REAIS BRASILEIROS")
    print("=" * 100)
    
    repo = OrdersRepository()
    calculator = B3CostCalculator()
    schedule = TradingSchedule()
    
    # Buscar dados reais brasileiros
    print("\n1. CARREGANDO DADOS REAIS BRASILEIROS...")
    print("-" * 100)
    
    captures = repo.get_market_data_captures()
    brasil = captures[captures['ticker'].str.contains('.SA', na=False)].copy()
    brasil = brasil[brasil['source'] == 'real']  # Apenas dados reais
    
    if brasil.empty:
        print("⚠️ Nenhum dado brasileiro real encontrado")
        return
    
    print(f"[OK] {len(brasil)} capturas brasileiras reais encontradas")
    
    # Agrupar por data e ticker
    brasil['timestamp'] = pd.to_datetime(brasil['timestamp'], errors='coerce')
    brasil['date'] = brasil['timestamp'].dt.date
    
    ativos = sorted(brasil['ticker'].unique())
    print(f"[OK] {len(ativos)} ativos brasileiros com dados")
    
    # Carregar configuração
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Criar estratégia de daytrade
    daytrade_strategy = DayTradeOptionsStrategy(config, logger)
    
    print("\n2. EXECUTANDO BACKTEST POR DATA...")
    print("-" * 100)
    
    datas = sorted(brasil['date'].unique())
    print(f"Datas disponíveis: {len(datas)}")
    for d in datas:
        print(f"  - {d}")
    
    resultados = []
    propostas_geradas = []
    
    for data in datas:
        print(f"\n📅 Processando data: {data}")
        print("-" * 100)
        
        dados_data = brasil[brasil['date'] == data].copy()
        
        # Agrupar por ticker e preparar market_data
        market_data = {'spot': {}, 'options': {}}
        
        for ticker in ativos:
            dados_ticker = dados_data[dados_data['ticker'] == ticker].copy()
            
            if dados_ticker.empty:
                continue
            
            # Pegar primeira captura (abertura) e última (fechamento)
            primeira_captura = dados_ticker.iloc[0]
            ultima_captura = dados_ticker.iloc[-1]
            
            # Calcular preços
            open_price = primeira_captura.get('open_price', 0) or primeira_captura.get('last_price', 0)
            close_price = ultima_captura.get('close_price', 0) or ultima_captura.get('last_price', 0)
            last_price = ultima_captura.get('last_price', 0) or close_price
            
            if open_price == 0 or close_price == 0:
                continue
            
            # Calcular intraday_return
            intraday_return = (close_price / open_price) - 1 if open_price > 0 else 0
            
            # Calcular volume (soma do dia ou último valor)
            volume = ultima_captura.get('volume', 0) or 0
            adv = ultima_captura.get('adv', 0) or volume
            volume_ratio = volume / adv if adv > 0 else 1.0
            
            spot_info = {
                'open': open_price,
                'high': ultima_captura.get('high_price', 0) or max(open_price, close_price),
                'low': ultima_captura.get('low_price', 0) or min(open_price, close_price),
                'close': close_price,
                'last': last_price,
                'volume': volume,
                'adv': adv,
                'intraday_return': intraday_return,
                'volume_ratio': volume_ratio
            }
            
            market_data['spot'][ticker] = spot_info
            
            # Tentar carregar opções se disponível
            if pd.notna(ultima_captura.get('options_data')):
                try:
                    if isinstance(ultima_captura['options_data'], str):
                        options_data = json.loads(ultima_captura['options_data'])
                    else:
                        options_data = ultima_captura['options_data']
                    
                    if options_data:
                        market_data['options'][ticker] = options_data
                except:
                    pass
        
        # Gerar propostas usando dados reais
        timestamp = pd.Timestamp(data)
        
        try:
            # Usar a estratégia de daytrade
            nav = config.get('nav', 1000000)
            proposals = daytrade_strategy.generate(nav, timestamp, market_data)
            
            print(f"  [OK] {len(proposals)} propostas geradas para {data}")
            
            for prop in proposals:
                prop_dict = {
                    'proposal_id': prop.proposal_id,
                    'date': data,
                    'ticker': prop.metadata.get('underlying', prop.symbol.split('_')[0]),
                    'symbol': prop.symbol,
                    'side': prop.side,
                    'quantity': prop.quantity,
                    'price': prop.price,
                    'metadata': prop.metadata,
                    'source': 'real_backtest'
                }
                propostas_geradas.append(prop_dict)
                
        except Exception as e:
            logger.error(f"Erro ao gerar propostas para {data}: {e}")
            continue
    
    print(f"\n3. RESUMO DE PROPOSTAS GERADAS:")
    print("-" * 100)
    print(f"Total de propostas geradas: {len(propostas_geradas)}")
    
    if propostas_geradas:
        df_propostas = pd.DataFrame(propostas_geradas)
        
        print(f"\nPor ativo:")
        por_ativo = df_propostas.groupby('ticker').size().sort_values(ascending=False)
        for ticker, count in por_ativo.items():
            print(f"  {ticker}: {count} propostas")
        
        print(f"\nPor data:")
        por_data = df_propostas.groupby('date').size().sort_values(ascending=False)
        for data, count in por_data.items():
            print(f"  {data}: {count} propostas")
        
        # Salvar propostas
        output_file = f"propostas_backtest_reais_{datas[0]}_{datas[-1]}.csv"
        df_propostas.to_csv(output_file, index=False)
        print(f"\n[OK] Propostas salvas em: {output_file}")
    
    print("\n" + "=" * 100)
    print("BACKTEST CONCLUÍDO")
    print("=" * 100)
    
    return propostas_geradas

if __name__ == '__main__':
    propostas = executar_backtest_dados_reais()

