"""
Script para executar o backtest sem precisar do notebook.
"""

import sys
from pathlib import Path
import json
import pandas as pd
import numpy as np

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from data_loader import DataLoader
    from pricing import BlackScholes
    from agents import TraderAgent, RiskAgent, PortfolioManager
    from execution import ExecutionSimulator
    from backtest import BacktestEngine
    from utils import StructuredLogger, calculate_metrics, get_version_info
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("\nPor favor, instale as dependências:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

def main():
    print("=" * 70)
    print("MVP AGENTS - BACKTEST")
    print("=" * 70)
    
    # Carregar configuração
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print("\n1. Gerando dados sintéticos...")
    data_loader = DataLoader(data_dir='data')
    
    spot_df = data_loader.generate_synthetic_spot(
        tickers=['AAPL', 'MSFT'],
        start_date='2024-01-01',
        end_date='2024-12-31',
        seed=42
    )
    
    futures_df = data_loader.generate_synthetic_futures(
        contracts=['ESZ25'],
        start_date='2024-01-01',
        end_date='2024-12-31',
        seed=42
    )
    
    options_df = data_loader.generate_synthetic_options_chain(
        underlying='AAPL',
        start_date='2024-01-01',
        end_date='2024-12-31',
        seed=42
    )
    
    print(f"   ✓ Spot: {len(spot_df)} registros")
    print(f"   ✓ Futuros: {len(futures_df)} registros")
    print(f"   ✓ Opções: {len(options_df)} registros")
    
    # Salvar CSVs
    data_loader.save_csv(spot_df, 'spot.csv')
    data_loader.save_csv(futures_df, 'futures.csv')
    data_loader.save_csv(options_df, 'options_chain.csv')
    
    print("\n2. Configurando backtest engine...")
    logger = StructuredLogger(log_dir='logs')
    backtest_engine = BacktestEngine(config, logger)
    backtest_engine.setup(data_loader, BlackScholes)
    backtest_engine.load_data(spot_df, futures_df, options_df)
    
    print("\n3. Executando backtest...")
    # Resetar componentes
    backtest_engine.portfolio_manager = PortfolioManager(config['nav'])
    backtest_engine.risk_agent = RiskAgent(backtest_engine.portfolio_manager, config, logger)
    backtest_engine.execution_simulator = ExecutionSimulator(config, logger)
    
    backtest_engine.run_simple()
    
    print("\n4. Analisando resultados...")
    metrics = backtest_engine.get_aggregate_metrics()
    
    print("\n" + "=" * 70)
    print("MÉTRICAS DE PERFORMANCE")
    print("=" * 70)
    for metric, value in metrics.items():
        if 'ratio' in metric.lower() or 'rate' in metric.lower():
            print(f"  {metric:20s}: {value:>10.4f}")
        elif 'return' in metric.lower() or 'drawdown' in metric.lower() or 'volatility' in metric.lower():
            print(f"  {metric:20s}: {value:>10.2f}%")
        else:
            print(f"  {metric:20s}: {value:>10.0f}")
    
    # Salvar resultados
    Path('output').mkdir(exist_ok=True)
    
    portfolio_snapshots = backtest_engine.get_portfolio_snapshots_df()
    if not portfolio_snapshots.empty:
        portfolio_snapshots.to_csv('output/portfolio_snapshots.csv', index=False)
        print(f"\n✓ {len(portfolio_snapshots)} snapshots salvos")
    
    orders_df = backtest_engine.execution_simulator.get_orders_dataframe()
    if not orders_df.empty:
        orders_df.to_csv('output/orders.csv', index=False)
        print(f"✓ {len(orders_df)} ordens salvas")
    
    fills_df = backtest_engine.execution_simulator.get_fills_dataframe()
    if not fills_df.empty:
        fills_df.to_csv('output/fills.csv', index=False)
        print(f"✓ {len(fills_df)} fills salvos")
    
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv('output/metrics.csv', index=False)
    print("✓ Métricas salvas")
    
    print("\n" + "=" * 70)
    print("BACKTEST CONCLUÍDO!")
    print("=" * 70)
    print(f"\nArquivos gerados em output/")
    print(f"Logs em logs/")

if __name__ == '__main__':
    main()

