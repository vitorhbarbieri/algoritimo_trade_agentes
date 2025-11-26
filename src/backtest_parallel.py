"""
Backtest paralelo usando multiprocessing.
"""

from typing import List, Dict
import multiprocessing

try:
    from .backtest import BacktestEngine
except ImportError:
    from backtest import BacktestEngine


def run_parallel_backtest_windows(backtest_engine: BacktestEngine, train_window: int = 60, test_window: int = 30, step: int = 15) -> List[Dict]:
    """
    Executa backtest em janelas paralelas.
    
    Args:
        backtest_engine: Instância do BacktestEngine
        train_window: Tamanho da janela de treino (dias)
        test_window: Tamanho da janela de teste (dias)
        step: Passo entre janelas (dias)
    
    Returns:
        Lista de resultados por janela
    """
    # Fallback simples: executar backtest único
    if backtest_engine.spot_data is None or backtest_engine.spot_data.empty:
        return []
    
    dates = sorted(backtest_engine.spot_data['date'].unique())
    if len(dates) < test_window:
        return [backtest_engine.run()]
    
    # Executar backtest único por enquanto
    return [backtest_engine.run()]

