"""
Engine de backtest: executa backtest walk-forward.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    from .agents import TraderAgent, RiskAgent, PortfolioManager
    from .execution import ExecutionSimulator
    from .utils import StructuredLogger, calculate_metrics
    from .data_loader import DataLoader
except ImportError:
    from agents import TraderAgent, RiskAgent, PortfolioManager
    from execution import ExecutionSimulator
    from utils import StructuredLogger, calculate_metrics
    from data_loader import DataLoader


class BacktestEngine:
    """Engine principal de backtest."""
    
    def __init__(self, config: Dict, logger: Optional[StructuredLogger] = None):
        self.config = config
        self.logger = logger or StructuredLogger()
        self.portfolio_manager = PortfolioManager(config.get('nav', 1000000))
        self.risk_agent = RiskAgent(self.portfolio_manager, config, self.logger)
        self.execution_simulator = ExecutionSimulator(config, self.logger)
        self.trader_agent = TraderAgent(config, self.logger)
        self.spot_data = None
        self.futures_data = None
        self.options_data = None
    
    def load_data(self, spot_df: pd.DataFrame, futures_df: pd.DataFrame = None, options_df: pd.DataFrame = None):
        """Carrega dados para backtest."""
        self.spot_data = spot_df
        self.futures_data = futures_df if futures_df is not None else pd.DataFrame()
        self.options_data = options_df if options_df is not None else pd.DataFrame()
    
    def run(self, start_date: str = None, end_date: str = None) -> Dict:
        """Executa backtest completo."""
        if self.spot_data is None or self.spot_data.empty:
            raise ValueError("Dados não carregados")
        
        dates = sorted(self.spot_data['date'].unique())
        
        if start_date:
            dates = [d for d in dates if pd.to_datetime(start_date) <= pd.to_datetime(d)]
        if end_date:
            dates = [d for d in dates if pd.to_datetime(d) <= pd.to_datetime(end_date)]
        
        for date in dates:
            market_data = self._prepare_market_data(date)
            proposals = self.trader_agent.generate_proposals(pd.to_datetime(date), market_data)
            
            for proposal in proposals:
                decision, modified_proposal, reason = self.risk_agent.evaluate_proposal(proposal, market_data)
                
                if decision == 'APPROVE':
                    order = {
                        'order_id': proposal.proposal_id,
                        'symbol': proposal.symbol,
                        'side': proposal.side,
                        'quantity': proposal.quantity,
                        'price': proposal.price,
                        'order_type': proposal.order_type
                    }
                    
                    market_price = self._get_market_price(proposal.symbol, date)
                    fill = self.execution_simulator.execute_order(order, market_price)
                    
                    if fill:
                        self.portfolio_manager.update_position(
                            proposal.symbol,
                            fill['quantity'] if proposal.side == 'BUY' else -fill['quantity'],
                            fill['price']
                        )
            
            # Snapshot do portfólio
            market_prices = self._get_all_market_prices(date)
            self.portfolio_manager.snapshot(pd.to_datetime(date), market_prices)
        
        # Calcular métricas
        returns = self._calculate_returns()
        nav_series = pd.Series([s['nav'] for s in self.portfolio_manager.snapshots])
        metrics = calculate_metrics(returns, nav_series)
        
        return {
            'metrics': metrics,
            'snapshots': self.portfolio_manager.snapshots,
            'fills': self.execution_simulator.get_fills().to_dict('records'),
            'orders': []
        }
    
    def _prepare_market_data(self, date: pd.Timestamp) -> Dict:
        """Prepara dados de mercado para uma data."""
        market_data = {'spot': {}, 'futures': {}, 'options': {}}
        
        date_pd = pd.to_datetime(date)
        
        # Spot data
        if self.spot_data is not None and not self.spot_data.empty:
            spot_date = self.spot_data[self.spot_data['date'] <= date_pd]
            if not spot_date.empty:
                latest_spot = spot_date.groupby('ticker').last()
                for ticker, row in latest_spot.iterrows():
                    market_data['spot'][ticker] = {
                        'close': row['close'],
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'volume': row['volume']
                    }
        
        # Options data
        if self.options_data is not None and not self.options_data.empty:
            opt_date = self.options_data[self.options_data['date'] <= date_pd]
            if not opt_date.empty:
                market_data['options'] = opt_date.to_dict('records')
        
        return market_data
    
    def _get_market_price(self, symbol: str, date: pd.Timestamp) -> float:
        """Obtém preço de mercado para um símbolo."""
        date_pd = pd.to_datetime(date)
        
        if self.spot_data is not None and not self.spot_data.empty:
            spot_date = self.spot_data[(self.spot_data['date'] <= date_pd) & (self.spot_data['ticker'] == symbol)]
            if not spot_date.empty:
                return float(spot_date.iloc[-1]['close'])
        
        return 0.0
    
    def _get_all_market_prices(self, date: pd.Timestamp) -> Dict[str, float]:
        """Obtém todos os preços de mercado."""
        prices = {}
        market_data = self._prepare_market_data(date)
        for ticker, data in market_data['spot'].items():
            prices[ticker] = data['close']
        return prices
    
    def _calculate_returns(self) -> pd.Series:
        """Calcula retornos do portfólio."""
        if len(self.portfolio_manager.snapshots) < 2:
            return pd.Series()
        
        navs = [s['nav'] for s in self.portfolio_manager.snapshots]
        returns = pd.Series(navs).pct_change().dropna()
        return returns
    
    def _run_window(self, start_date: str, end_date: str, window_num: int) -> Dict:
        """Executa uma janela de backtest."""
        return self.run(start_date, end_date)

