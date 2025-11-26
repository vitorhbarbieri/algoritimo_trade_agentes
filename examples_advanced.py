"""
Exemplos de uso das funcionalidades avançadas:
- Sizing (Kelly, Risk Parity, etc.)
- Novas estratégias
- Integração com broker
"""

import sys
from pathlib import Path
import json
import pandas as pd
import numpy as np

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_loader import DataLoader
from pricing import BlackScholes
from agents import TraderAgent, RiskAgent, PortfolioManager
from execution import ExecutionSimulator
from backtest import BacktestEngine
from utils import StructuredLogger
from sizing import (
    create_sizing_method,
    FixedFractionSizing,
    RiskBasedSizing,
    KellyCriterionSizing,
    RiskParitySizing,
    AdaptiveSizing
)
from strategies import (
    MomentumStrategy,
    MeanReversionStrategy,
    BreakoutStrategy,
    RSIStrategy,
    MACDStrategy
)
from broker_adapters import create_broker_adapter


def example_sizing_methods():
    """Exemplo de uso dos diferentes métodos de sizing."""
    print("=" * 70)
    print("EXEMPLO: Métodos de Sizing")
    print("=" * 70)
    
    nav = 1000000.0
    price = 150.0
    signal_strength = 0.7
    stop_loss = 145.0
    
    # Fixed Fraction
    fixed_fraction = create_sizing_method('fixed_fraction', nav, {'fraction': 0.02})
    size1 = fixed_fraction.calculate_size(signal_strength, price, stop_loss)
    print(f"\n1. Fixed Fraction (2%): {size1:.2f} ações")
    
    # Risk-Based
    risk_based = create_sizing_method('risk_based', nav, {'risk_per_trade': 0.02})
    size2 = risk_based.calculate_size(signal_strength, price, stop_loss)
    print(f"2. Risk-Based (2% risco): {size2:.2f} ações")
    
    # Kelly Criterion
    kelly = create_sizing_method('kelly', nav, {'kelly_fraction': 0.25})
    size3 = kelly.calculate_size(signal_strength, price, stop_loss, expected_return=0.05, volatility=0.20)
    print(f"3. Kelly Criterion (Quarter Kelly): {size3:.2f} ações")
    
    # Risk Parity
    risk_parity = create_sizing_method('risk_parity', nav, {'target_volatility': 0.15})
    size4 = risk_parity.calculate_size(signal_strength, price, stop_loss, volatility=0.20)
    print(f"4. Risk Parity (15% vol alvo): {size4:.2f} ações")
    
    # Adaptive
    adaptive = create_sizing_method('adaptive', nav)
    size5 = adaptive.calculate_size(signal_strength, price, stop_loss, volatility=0.20, market_regime='trending')
    print(f"5. Adaptive (trending): {size5:.2f} ações")


def example_new_strategies():
    """Exemplo de uso das novas estratégias."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Novas Estratégias")
    print("=" * 70)
    
    # Gerar dados sintéticos
    data_loader = DataLoader()
    spot_df = data_loader.generate_synthetic_spot(['AAPL'], '2024-01-01', '2024-12-31', seed=42)
    prices = spot_df.set_index(['date', 'ticker']).loc[(slice(None), 'AAPL'), 'close'].reset_index(level=1, drop=True)
    
    # Momentum
    momentum = MomentumStrategy(lookback_short=10, lookback_long=30)
    signal_mom = momentum.generate_signal(prices)
    print(f"\n1. Momentum Strategy:")
    print(f"   Sinal: {signal_mom['signal']:.2f}, Força: {signal_mom['strength']:.2f}")
    
    # Mean Reversion
    mean_rev = MeanReversionStrategy(lookback=20, zscore_threshold=2.0)
    signal_mr = mean_rev.generate_signal(prices)
    print(f"\n2. Mean Reversion Strategy:")
    print(f"   Sinal: {signal_mr['signal']:.2f}, Força: {signal_mr['strength']:.2f}")
    
    # Breakout
    breakout = BreakoutStrategy(lookback=20, breakout_threshold=0.01)
    signal_bo = breakout.generate_signal(prices)
    print(f"\n3. Breakout Strategy:")
    print(f"   Sinal: {signal_bo['signal']:.2f}, Força: {signal_bo['strength']:.2f}")
    
    # RSI
    rsi = RSIStrategy(period=14, oversold=30, overbought=70)
    signal_rsi = rsi.generate_signal(prices)
    rsi_value = rsi.calculate_rsi(prices)
    print(f"\n4. RSI Strategy:")
    print(f"   RSI: {rsi_value:.2f}")
    print(f"   Sinal: {signal_rsi['signal']:.2f}, Força: {signal_rsi['strength']:.2f}")
    
    # MACD
    macd = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
    signal_macd = macd.generate_signal(prices)
    macd_data = macd.calculate_macd(prices)
    print(f"\n5. MACD Strategy:")
    print(f"   MACD: {macd_data['macd']:.4f}, Signal: {macd_data['signal']:.4f}")
    print(f"   Sinal: {signal_macd['signal']:.2f}, Força: {signal_macd['strength']:.2f}")


def example_broker_adapters():
    """Exemplo de uso dos adaptadores de broker."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Adaptadores de Broker")
    print("=" * 70)
    
    # Mock Broker (para desenvolvimento)
    print("\n1. Mock Broker (para desenvolvimento):")
    mock_broker = create_broker_adapter('mock')
    mock_broker.connect()
    print(f"   Conectado: {mock_broker.is_connected()}")
    
    account_info = mock_broker.get_account_info()
    print(f"   Balance: R$ {account_info['balance']:,.2f}")
    
    # IB Adapter (stub)
    print("\n2. Interactive Brokers Adapter:")
    print("   ⚠️ Stub implementado. Para uso real:")
    print("   - Instale: pip install ib_insync")
    print("   - Configure TWS/IB Gateway")
    print("   - Complete a implementação em broker_adapters.py")
    
    # CCXT Adapter (stub)
    print("\n3. CCXT Adapter (para exchanges):")
    print("   ⚠️ Stub implementado. Para uso real:")
    print("   - Instale: pip install ccxt")
    print("   - Configure API keys da exchange")
    print("   - Complete a implementação em broker_adapters.py")


def example_integration():
    """Exemplo de integração completa."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Integração Completa")
    print("=" * 70)
    
    # Carregar configuração
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Setup
    data_loader = DataLoader()
    logger = StructuredLogger(log_dir='logs')
    
    # Gerar dados
    spot_df = data_loader.generate_synthetic_spot(['AAPL'], '2024-01-01', '2024-06-30', seed=42)
    futures_df = data_loader.generate_synthetic_futures([], '2024-01-01', '2024-06-30', seed=42)
    options_df = data_loader.generate_synthetic_options_chain('AAPL', '2024-01-01', '2024-06-30', seed=42)
    
    # Backtest com sizing customizado
    backtest_engine = BacktestEngine(config, logger)
    backtest_engine.setup(data_loader, BlackScholes)
    backtest_engine.load_data(spot_df, futures_df, options_df)
    
    # Usar Kelly Criterion para sizing
    sizing_method = create_sizing_method('kelly', config['nav'], {'kelly_fraction': 0.25})
    
    print("\n✓ Backtest configurado com Kelly Criterion sizing")
    print("  Execute: backtest_engine.run_simple() para rodar")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("EXEMPLOS DE FUNCIONALIDADES AVANÇADAS")
    print("=" * 70)
    
    example_sizing_methods()
    example_new_strategies()
    example_broker_adapters()
    example_integration()
    
    print("\n" + "=" * 70)
    print("✓ Exemplos concluídos!")
    print("=" * 70)

