"""
Módulos dos agentes: TraderAgent e RiskAgent.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from statsmodels.tsa.stattools import coint, adfuller

try:
    from .pricing import BlackScholes
    from .utils import StructuredLogger
except ImportError:
    from pricing import BlackScholes
    from utils import StructuredLogger


@dataclass
class OrderProposal:
    """Proposta de ordem do TraderAgent."""
    proposal_id: str
    strategy: str
    instrument_type: str  # 'spot', 'futures', 'options'
    symbol: str
    side: str  # 'BUY', 'SELL'
    quantity: float
    price: Optional[float] = None
    order_type: str = 'LIMIT'
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PortfolioManager:
    """Gerencia portfólio e posições."""
    
    def __init__(self, initial_nav: float = 1000000.0):
        self.initial_nav = initial_nav
        self.nav = initial_nav
        self.positions = {}  # {symbol: quantity}
        self.cash = initial_nav
        self.snapshots = []
    
    def get_nav(self) -> float:
        """Retorna NAV atual."""
        return self.nav
    
    def get_positions(self) -> Dict[str, float]:
        """Retorna posições atuais."""
        return self.positions.copy()
    
    def update_position(self, symbol: str, quantity: float, price: float):
        """Atualiza posição."""
        if symbol not in self.positions:
            self.positions[symbol] = 0.0
        self.positions[symbol] += quantity
        self.cash -= quantity * price
        if self.positions[symbol] == 0:
            del self.positions[symbol]
    
    def snapshot(self, date: pd.Timestamp, market_prices: Dict[str, float]):
        """Cria snapshot do portfólio."""
        position_value = sum(self.positions.get(s, 0) * market_prices.get(s, 0) for s in self.positions)
        self.nav = self.cash + position_value
        self.snapshots.append({
            'date': date,
            'nav': self.nav,
            'cash': self.cash,
            'position_value': position_value,
            'positions': self.positions.copy()
        })
    
    def get_aggregate_greeks(self, market_data: Dict) -> Dict[str, float]:
        """Calcula greeks agregados do portfólio."""
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0
        
        for symbol, quantity in self.positions.items():
            if symbol in market_data:
                greeks = market_data[symbol].get('greeks', {})
                total_delta += quantity * greeks.get('delta', 0)
                total_gamma += quantity * greeks.get('gamma', 0)
                total_vega += quantity * greeks.get('vega', 0)
                total_theta += quantity * greeks.get('theta', 0)
        
        return {
            'delta': total_delta,
            'gamma': total_gamma,
            'vega': total_vega,
            'theta': total_theta
        }


class TraderAgent:
    """Agente criativo que gera propostas de trading."""
    
    def __init__(self, config: Dict, logger: Optional[StructuredLogger] = None):
        self.config = config
        self.logger = logger
        self.proposal_counter = 0
    
    def generate_proposals(self, date: pd.Timestamp, market_data: Dict) -> List[OrderProposal]:
        """Gera propostas de trading."""
        proposals = []
        
        # Estratégia 1: Delta-hedged Volatility Arbitrage
        if self.config.get('enable_vol_arb', True):
            vol_arb_proposals = self._vol_arb_strategy(date, market_data)
            proposals.extend(vol_arb_proposals)
        
        # Estratégia 2: Pairs/Statistical Arbitrage
        if self.config.get('enable_pairs', True):
            pairs_proposals = self._pairs_strategy(date, market_data)
            proposals.extend(pairs_proposals)
        
        return proposals
    
    def _vol_arb_strategy(self, date: pd.Timestamp, market_data: Dict) -> List[OrderProposal]:
        """Delta-hedged Volatility Arbitrage."""
        proposals = []
        threshold = self.config.get('vol_arb_threshold', 0.05)
        underlying = self.config.get('vol_arb_underlying', 'AAPL')
        
        if 'options' not in market_data or underlying not in market_data.get('spot', {}):
            return proposals
        
        spot_price = market_data['spot'][underlying].get('close', 0)
        if spot_price == 0:
            return proposals
        
        options_chain = market_data.get('options', {}).get(underlying, [])
        if not options_chain:
            return proposals
        
        for opt in options_chain[:10]:
            strike = opt.get('strike', 0)
            expiry = opt.get('expiry', date)
            days_to_expiry = (pd.to_datetime(expiry) - date).days
            if days_to_expiry <= 0:
                continue
            
            time_to_expiry = days_to_expiry / 365.0
            iv = opt.get('implied_vol', 0.25)
            mid_price = opt.get('mid', 0)
            
            if mid_price == 0:
                continue
            
            option_type = opt.get('option_type', 'C')
            r = self.config.get('risk_free_rate', 0.05)
            
            bs = BlackScholes()
            theoretical_price = bs.price(spot_price, strike, time_to_expiry, r, iv, option_type)
            
            mispricing = (mid_price - theoretical_price) / theoretical_price
            
            if abs(mispricing) > threshold:
                self.proposal_counter += 1
                proposal_id = f"VOL_ARB_{self.proposal_counter}"
                
                if mispricing > 0:
                    side = 'SELL'
                else:
                    side = 'BUY'
                
                quantity = self.config.get('vol_arb_size', 10)
                
                proposal = OrderProposal(
                    proposal_id=proposal_id,
                    strategy='vol_arb',
                    instrument_type='options',
                    symbol=f"{underlying}_{strike}_{option_type}",
                    side=side,
                    quantity=quantity,
                    price=mid_price,
                    metadata={
                        'underlying': underlying,
                        'strike': strike,
                        'expiry': expiry,
                        'option_type': option_type,
                        'mispricing': mispricing,
                        'theoretical_price': theoretical_price,
                        'market_price': mid_price
                    }
                )
                proposals.append(proposal)
                
                if self.logger:
                    self.logger.log_trader_proposal(proposal_id, 'vol_arb', {
                        'mispricing': mispricing,
                        'underlying': underlying
                    })
        
        return proposals
    
    def _pairs_strategy(self, date: pd.Timestamp, market_data: Dict) -> List[OrderProposal]:
        """Pairs/Statistical Arbitrage."""
        proposals = []
        ticker1 = self.config.get('pairs_ticker1', 'AAPL')
        ticker2 = self.config.get('pairs_ticker2', 'MSFT')
        zscore_threshold = self.config.get('pairs_zscore_threshold', 2.0)
        
        if ticker1 not in market_data.get('spot', {}) or ticker2 not in market_data.get('spot', {}):
            return proposals
        
        spot1 = market_data['spot'][ticker1]
        spot2 = market_data['spot'][ticker2]
        
        price1 = spot1.get('close', 0)
        price2 = spot2.get('close', 0)
        
        if price1 == 0 or price2 == 0:
            return proposals
        
        ratio = price1 / price2
        
        if 'pairs_history' not in self.__dict__:
            self.pairs_history = []
        
        self.pairs_history.append(ratio)
        if len(self.pairs_history) > 60:
            self.pairs_history.pop(0)
        
        if len(self.pairs_history) < 30:
            return proposals
        
        mean_ratio = np.mean(self.pairs_history)
        std_ratio = np.std(self.pairs_history)
        
        if std_ratio == 0:
            return proposals
        
        zscore = (ratio - mean_ratio) / std_ratio
        
        if abs(zscore) > zscore_threshold:
            self.proposal_counter += 1
            proposal_id = f"PAIRS_{self.proposal_counter}"
            
            if zscore > zscore_threshold:
                side1 = 'SELL'
                side2 = 'BUY'
            else:
                side1 = 'BUY'
                side2 = 'SELL'
            
            quantity = self.config.get('pairs_size', 100)
            
            proposal1 = OrderProposal(
                proposal_id=f"{proposal_id}_1",
                strategy='pairs',
                instrument_type='spot',
                symbol=ticker1,
                side=side1,
                quantity=quantity,
                price=price1,
                metadata={
                    'ticker2': ticker2,
                    'zscore': zscore,
                    'ratio': ratio,
                    'mean_ratio': mean_ratio
                }
            )
            
            proposal2 = OrderProposal(
                proposal_id=f"{proposal_id}_2",
                strategy='pairs',
                instrument_type='spot',
                symbol=ticker2,
                side=side2,
                quantity=quantity,
                price=price2,
                metadata={
                    'ticker1': ticker1,
                    'zscore': zscore,
                    'ratio': ratio,
                    'mean_ratio': mean_ratio
                }
            )
            
            proposals.extend([proposal1, proposal2])
            
            if self.logger:
                self.logger.log_trader_proposal(proposal_id, 'pairs', {
                    'zscore': zscore,
                    'ticker1': ticker1,
                    'ticker2': ticker2
                })
        
        return proposals


class RiskAgent:
    """Agente controlador que valida/modifica/rejeita propostas."""
    
    def __init__(self, portfolio_manager: PortfolioManager, config: Dict, logger: Optional[StructuredLogger] = None):
        self.portfolio = portfolio_manager
        self.config = config
        self.logger = logger
        self.kill_switch_active = False
    
    def evaluate_proposal(self, proposal: OrderProposal, market_data: Dict) -> Tuple[str, Optional[OrderProposal], str]:
        """
        Avalia proposta.
        Returns: (decision, modified_proposal, reason)
        decision: 'APPROVE', 'MODIFY', 'REJECT'
        """
        if self.kill_switch_active:
            return ('REJECT', None, 'Kill switch ativo')
        
        # Verificar limites de exposição
        max_exposure = self.config.get('max_exposure', 0.5)
        current_exposure = abs(sum(self.portfolio.positions.values()))
        if current_exposure > self.portfolio.nav * max_exposure:
            return ('REJECT', None, f'Exposição máxima excedida: {current_exposure:.2f}')
        
        # Verificar limites de greeks
        greeks = self.portfolio.get_aggregate_greeks(market_data)
        max_delta = self.config.get('max_delta', 1000)
        max_gamma = self.config.get('max_gamma', 500)
        max_vega = self.config.get('max_vega', 1000)
        
        if abs(greeks['delta']) > max_delta:
            return ('REJECT', None, f'Delta agregado excedido: {greeks["delta"]:.2f}')
        
        if abs(greeks['gamma']) > max_gamma:
            return ('REJECT', None, f'Gamma agregado excedido: {greeks["gamma"]:.2f}')
        
        if abs(greeks['vega']) > max_vega:
            return ('REJECT', None, f'Vega agregado excedido: {greeks["vega"]:.2f}')
        
        # Modificar quantidade se necessário
        max_position_size = self.config.get('max_position_size', 10000)
        if proposal.quantity > max_position_size:
            proposal.quantity = max_position_size
            return ('MODIFY', proposal, f'Quantidade reduzida para {max_position_size}')
        
        # Aprovar
        if self.logger:
            self.logger.log_risk_evaluation(proposal.proposal_id, 'APPROVE', 'Proposta aprovada', {})
        
        return ('APPROVE', proposal, 'Proposta aprovada')
    
    def kill_switch(self):
        """Ativa kill switch."""
        self.kill_switch_active = True
        if self.logger:
            self.logger.log_decision('kill_switch', {'active': True})

