"""
Exemplo de uso com dados reais de mercado via APIs.
"""

import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timedelta

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data_loader import DataLoader
from src.pricing import BlackScholes
from src.agents import TraderAgent, RiskAgent, PortfolioManager
from src.execution import ExecutionSimulator
from src.backtest import BacktestEngine
from src.backtest_parallel import run_parallel_backtest_windows
from src.utils import StructuredLogger
from src.market_data_api import fetch_real_market_data, create_market_data_api


def main():
    print("=" * 70)
    print("EXEMPLO: Backtest com Dados Reais de Mercado")
    print("=" * 70)
    
    # Carregar configuração
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print("\n1. Buscando dados reais de mercado...")
    print("   Usando yfinance (Yahoo Finance)")
    
    # Buscar dados reais
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')  # 6 meses
    
    tickers = ['AAPL', 'MSFT']  # Ações americanas
    
    try:
        data = fetch_real_market_data(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            api_type='yfinance',
            use_fallback=True
        )
        
        spot_df = data['spot']
        futures_df = data['futures']
        options_df = data['options']
        
        print(f"   OK Spot: {len(spot_df)} registros")
        print(f"   OK Futuros: {len(futures_df)} registros")
        print(f"   OK Opcoes: {len(options_df)} registros")
        
        if spot_df.empty:
            print("\n⚠️  Nenhum dado de spot encontrado. Usando dados sintéticos...")
            data_loader = DataLoader()
            spot_df = data_loader.generate_synthetic_spot(tickers, start_date, end_date)
            futures_df = data_loader.generate_synthetic_futures([], start_date, end_date)
            options_df = data_loader.generate_synthetic_options_chain(tickers[0], start_date, end_date)
        
        # Salvar dados
        data_loader = DataLoader()
        data_loader.save_csv(spot_df, 'spot_real.csv')
        if not futures_df.empty:
            data_loader.save_csv(futures_df, 'futures_real.csv')
        if not options_df.empty:
            data_loader.save_csv(options_df, 'options_real.csv')
        
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
        
        # Executar backtest simples
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
            print(f"\nOK {len(portfolio_snapshots)} snapshots salvos")
        
        orders_df = backtest_engine.execution_simulator.get_orders_dataframe()
        if not orders_df.empty:
            orders_df.to_csv('output/orders.csv', index=False)
            print(f"OK {len(orders_df)} ordens salvas")
        
        fills_df = backtest_engine.execution_simulator.get_fills_dataframe()
        if not fills_df.empty:
            fills_df.to_csv('output/fills.csv', index=False)
            print(f"OK {len(fills_df)} fills salvos")
        
        metrics_df = pd.DataFrame([metrics])
        metrics_df.to_csv('output/metrics.csv', index=False)
        print("OK Metricas salvas")
        
        print("\n" + "=" * 70)
        print("BACKTEST CONCLUÍDO!")
        print("=" * 70)
        print(f"\nDados usados: {len(spot_df)} registros de {tickers}")
        print(f"Período: {start_date} a {end_date}")
        print(f"\nArquivos gerados em output/")
        print(f"Logs em logs/")
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Dica: Verifique sua conexão com a internet e se yfinance está instalado:")
        print("   pip install yfinance")


def example_parallel_backtest():
    """Exemplo de backtest paralelo."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Backtest Paralelo")
    print("=" * 70)
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Gerar dados sintéticos para exemplo rápido
    data_loader = DataLoader()
    spot_df = data_loader.generate_synthetic_spot(['AAPL'], '2024-01-01', '2024-12-31')
    futures_df = data_loader.generate_synthetic_futures([], '2024-01-01', '2024-12-31')
    options_df = data_loader.generate_synthetic_options_chain('AAPL', '2024-01-01', '2024-12-31')
    
    logger = StructuredLogger(log_dir='logs')
    backtest_engine = BacktestEngine(config, logger)
    backtest_engine.setup(data_loader, BlackScholes)
    backtest_engine.load_data(spot_df, futures_df, options_df)
    
    print("\nExecutando backtest paralelo...")
    print("(Usando multiprocessing como fallback)")
    
    try:
        results = run_parallel_backtest_windows(
            backtest_engine,
            train_window=60,
            test_window=20,
            step=10,
            use_bmad=False  # Usar multiprocessing
        )
        
        print(f"\n✓ {len(results)} janelas processadas")
        
        # Agregar métricas
        if results:
            total_return = sum(r['metrics'].get('total_return', 0) for r in results) / len(results)
            sharpe = sum(r['metrics'].get('sharpe_ratio', 0) for r in results) / len(results)
            
            print(f"\nMétricas Médias:")
            print(f"  Retorno Total: {total_return:.2f}%")
            print(f"  Sharpe Ratio: {sharpe:.4f}")
    
    except Exception as e:
        print(f"❌ Erro no backtest paralelo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Exemplo de uso com dados reais')
    parser.add_argument('--parallel', action='store_true', help='Executar backtest paralelo')
    args = parser.parse_args()
    
    if args.parallel:
        example_parallel_backtest()
    else:
        main()

