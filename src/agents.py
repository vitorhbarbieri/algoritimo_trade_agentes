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


class DayTradeOptionsStrategy:
    """Estratégia de daytrade focada em compra de CALLs ATM/OTM curta."""
    
    def __init__(self, config: Dict, logger: Optional[StructuredLogger] = None):
        self.full_config = config
        self.config = config.get('daytrade_options', {})
        self.logger = logger
        self.bs = BlackScholes()
    
    def generate(self, nav: float, timestamp: pd.Timestamp, market_data: Dict) -> List[OrderProposal]:
        """Gera propostas de daytrade de opções."""
        proposals = []
        cfg = self.config
        
        # Verificar se estratégia está habilitada
        if not cfg.get('enabled', True):
            return proposals
        
        # Obter universo de ativos
        spot_data = market_data.get('spot', {})
        options_data = market_data.get('options', {})
        
        if not spot_data:
            if self.logger:
                self.logger.log_error("DayTradeOptionsStrategy: Nenhum dado spot disponível")
            return proposals
        
        # Se não houver opções, tentar buscar para cada ativo com momentum
        if not options_data:
            if self.logger:
                self.logger.log_error("DayTradeOptionsStrategy: Nenhum dado de opções disponível")
            # Continuar mesmo sem opções - pode gerar propostas baseadas apenas em momentum
            # Mas não vamos gerar propostas sem opções
            return proposals
        
        # Iterar sobre ativos disponíveis
        for asset, spot_info in spot_data.items():
            try:
                # 1. Verificar momentum e volume intraday
                open_price = spot_info.get('open', 0)
                last_price = spot_info.get('close', spot_info.get('last', 0))
                
                if open_price == 0 or last_price == 0:
                    continue
                
                intraday_return = (last_price / open_price) - 1
                min_intraday_return = cfg.get('min_intraday_return', 0.005)
                
                if intraday_return < min_intraday_return:
                    continue
                
                # Calcular volume ratio
                volume_day = spot_info.get('volume', 0)
                # Tentar obter ADV (Average Daily Volume) ou usar volume médio
                adv = spot_info.get('adv', spot_info.get('avg_volume', spot_info.get('average_volume', volume_day)))
                if adv == 0:
                    # Se não tiver ADV, usar volume do dia atual como fallback
                    adv = max(volume_day, 1)
                
                volume_ratio = volume_day / adv
                min_volume_ratio = cfg.get('min_volume_ratio', 0.25)
                
                if volume_ratio < min_volume_ratio:
                    continue
                
                # 2. Buscar chain de opções para o ativo
                # Os dados podem vir como lista ou dict organizado por ativo
                if isinstance(options_data, list):
                    # Se for lista, filtrar por underlying
                    options_chain = [
                        opt for opt in options_data 
                        if isinstance(opt, dict) and opt.get('underlying') == asset
                    ]
                elif isinstance(options_data, dict):
                    # Se for dict, buscar diretamente
                    options_chain = options_data.get(asset, [])
                else:
                    # Caso não seja lista nem dict, retornar lista vazia
                    options_chain = []
                
                if not options_chain:
                    continue
                
                # Filtrar calls viáveis
                viable_calls = []
                max_dte = cfg.get('max_dte', 7)
                delta_min = cfg.get('delta_min', 0.20)
                delta_max = cfg.get('delta_max', 0.60)
                max_spread_pct = cfg.get('max_spread_pct', 0.05)
                min_option_volume = cfg.get('min_option_volume', 200)
                
                for opt in options_chain:
                    # Verificar se é CALL
                    option_type = opt.get('option_type', 'C')
                    if option_type != 'C':
                        continue
                    
                    # Verificar dias até expiração
                    expiry = pd.to_datetime(opt.get('expiry', timestamp))
                    days_to_expiry = (expiry - timestamp).days
                    if days_to_expiry <= 0 or days_to_expiry > max_dte:
                        continue
                    
                    # Calcular greeks se não estiverem disponíveis
                    strike = opt.get('strike', 0)
                    if strike == 0:
                        continue
                    
                    bid = opt.get('bid', 0)
                    ask = opt.get('ask', 0)
                    mid = opt.get('mid', (bid + ask) / 2 if bid > 0 and ask > 0 else 0)
                    
                    if mid == 0:
                        continue
                    
                    # Calcular spread percentual
                    spread_pct = (ask - bid) / mid if mid > 0 else 1.0
                    if spread_pct > max_spread_pct:
                        continue
                    
                    # Verificar volume
                    volume = opt.get('volume', opt.get('open_interest', 0))
                    if volume < min_option_volume:
                        continue
                    
                    # Calcular greeks usando Black-Scholes
                    time_to_expiry = days_to_expiry / 365.0
                    iv = opt.get('implied_vol', opt.get('implied_volatility', 0.25))
                    r = self.full_config.get('risk_free_rate', 0.05)
                    
                    delta = self.bs.delta(last_price, strike, time_to_expiry, r, iv, 'C')
                    gamma = self.bs.gamma(last_price, strike, time_to_expiry, r, iv)
                    vega = self.bs.vega(last_price, strike, time_to_expiry, r, iv)
                    
                    # Verificar delta
                    if not (delta_min <= delta <= delta_max):
                        continue
                    
                    viable_calls.append({
                        'option': opt,
                        'strike': strike,
                        'expiry': expiry,
                        'days_to_expiry': days_to_expiry,
                        'bid': bid,
                        'ask': ask,
                        'mid': mid,
                        'spread_pct': spread_pct,
                        'volume': volume,
                        'delta': delta,
                        'gamma': gamma,
                        'vega': vega,
                        'iv': iv
                    })
                
                if not viable_calls:
                    continue
                
                # 3. Selecionar melhor call (maior gamma, menor spread, maior liquidez)
                best_call = max(
                    viable_calls,
                    key=lambda o: (o['gamma'], -o['spread_pct'], o['volume'])
                )
                
                # 4. Calcular sizing baseado no risco
                risk_per_trade = cfg.get('risk_per_trade', 0.002)
                max_risk = nav * risk_per_trade
                premium_per_contract = best_call['mid'] * 100  # Opções são multiplicadas por 100
                
                if premium_per_contract == 0:
                    continue
                
                qty = int(max_risk / premium_per_contract)
                
                if qty <= 0:
                    continue
                
                # 5. Gerar OrderProposal
                proposal_id = f"DAYOPT-{asset}-{best_call['strike']}-{best_call['expiry'].strftime('%Y%m%d')}-{int(timestamp.timestamp())}"
                
                proposal = OrderProposal(
                    proposal_id=proposal_id,
                    strategy='daytrade_options',
                    instrument_type='options',
                    symbol=f"{asset}_{best_call['strike']}_C_{best_call['expiry'].strftime('%Y%m%d')}",
                    side='BUY',
                    quantity=qty,
                    price=best_call['ask'],  # Preço de compra (ask)
                    order_type='LIMIT',
                    metadata={
                        'underlying': asset,
                        'strike': best_call['strike'],
                        'expiry': best_call['expiry'].isoformat(),
                        'days_to_expiry': best_call['days_to_expiry'],
                        'delta': best_call['delta'],
                        'gamma': best_call['gamma'],
                        'vega': best_call['vega'],
                        'iv': best_call['iv'],
                        'intraday_return': float(intraday_return),
                        'volume_ratio': float(volume_ratio),
                        'spread_pct': float(best_call['spread_pct']),
                        'premium': float(best_call['mid']),
                        'max_risk': float(max_risk),
                        'take_profit_pct': cfg.get('take_profit_pct', 0.10),
                        'stop_loss_pct': cfg.get('stop_loss_pct', 0.40),
                        'eod_close': True
                    }
                )
                
                proposals.append(proposal)
                
                if self.logger:
                    self.logger.log_trader_proposal(proposal_id, 'daytrade_options', {
                        'asset': asset,
                        'intraday_return': intraday_return,
                        'volume_ratio': volume_ratio,
                        'strike': best_call['strike'],
                        'delta': best_call['delta']
                    })
            
            except Exception as e:
                if self.logger:
                    self.logger.log_error(f"Erro em DayTradeOptionsStrategy para {asset}: {str(e)}")
                continue
        
        return proposals


class TraderAgent:
    """Agente criativo que gera propostas de trading."""
    
    def __init__(self, config: Dict, logger: Optional[StructuredLogger] = None, orders_repo=None):
        self.config = config
        self.logger = logger
        self.orders_repo = orders_repo  # Repositório para salvar propostas
        self.proposal_counter = 0
        
        # Inicializar estratégias modulares
        self.strategies = []
        
        # Estratégia de DayTrade Options
        if config.get('daytrade_options', {}).get('enabled', True):
            self.strategies.append(DayTradeOptionsStrategy(config, logger))
    
    def generate_proposals(self, date: pd.Timestamp, market_data: Dict) -> List[OrderProposal]:
        """Gera propostas de trading."""
        proposals = []
        
        # Executar estratégias modulares
        nav = self.config.get('nav', 1000000)
        for strategy in self.strategies:
            try:
                strategy_proposals = strategy.generate(nav, date, market_data)
                proposals.extend(strategy_proposals)
            except Exception as e:
                if self.logger:
                    self.logger.log_error(f"Erro em estratégia {strategy.__class__.__name__}: {str(e)}")
        
        # Estratégia 1: Delta-hedged Volatility Arbitrage
        if self.config.get('enable_vol_arb', True):
            vol_arb_proposals = self._vol_arb_strategy(date, market_data)
            proposals.extend(vol_arb_proposals)
        
        # Estratégia 2: Pairs/Statistical Arbitrage
        if self.config.get('enable_pairs', True):
            pairs_proposals = self._pairs_strategy(date, market_data)
            proposals.extend(pairs_proposals)
        
        # Salvar propostas no banco de dados
        if self.orders_repo:
            for proposal in proposals:
                try:
                    proposal_dict = {
                        'proposal_id': proposal.proposal_id,
                        'timestamp': date.isoformat(),
                        'strategy': proposal.strategy,
                        'instrument_type': proposal.instrument_type,
                        'symbol': proposal.symbol,
                        'side': proposal.side,
                        'quantity': proposal.quantity,
                        'price': proposal.price,
                        'order_type': proposal.order_type,
                        'metadata': proposal.metadata
                    }
                    self.orders_repo.save_proposal(proposal_dict)
                except Exception as e:
                    if self.logger:
                        self.logger.log_error(f"Erro ao salvar proposta {proposal.proposal_id}: {e}")
        
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
        
        # Tratar options como lista ou dict
        options_data = market_data.get('options', {})
        if isinstance(options_data, list):
            # Se for lista, filtrar por underlying
            options_chain = [
                opt for opt in options_data 
                if isinstance(opt, dict) and opt.get('underlying') == underlying
            ]
        elif isinstance(options_data, dict):
            options_chain = options_data.get(underlying, [])
        else:
            options_chain = []
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
    
    def __init__(self, portfolio_manager: PortfolioManager, config: Dict, logger: Optional[StructuredLogger] = None, email_notifier=None, orders_repo=None):
        self.portfolio = portfolio_manager
        self.config = config
        self.logger = logger
        self.email_notifier = email_notifier  # EmailNotifier opcional
        self.orders_repo = orders_repo  # Repositório para salvar avaliações
        self.kill_switch_active = False
    
    def _save_evaluation(self, proposal: OrderProposal, decision: str, reason: str, modified_proposal: Optional[OrderProposal] = None):
        """Salva avaliação no banco de dados."""
        if self.orders_repo:
            try:
                from datetime import datetime
                evaluation_dict = {
                    'proposal_id': proposal.proposal_id,
                    'timestamp': datetime.now().isoformat(),
                    'decision': decision,
                    'reason': reason,
                    'details': {},
                    'modified_quantity': modified_proposal.quantity if modified_proposal else None,
                    'modified_price': modified_proposal.price if modified_proposal else None
                }
                self.orders_repo.save_risk_evaluation(evaluation_dict)
            except Exception as e:
                if self.logger:
                    self.logger.log_error(f"Erro ao salvar avaliação {proposal.proposal_id}: {e}")
    
    def evaluate_proposal(self, proposal: OrderProposal, market_data: Dict) -> Tuple[str, Optional[OrderProposal], str]:
        """
        Avalia proposta.
        Returns: (decision, modified_proposal, reason)
        decision: 'APPROVE', 'MODIFY', 'REJECT'
        """
        if self.kill_switch_active:
            decision = ('REJECT', None, 'Kill switch ativo')
            self._save_evaluation(proposal, 'REJECT', 'Kill switch ativo')
            return decision
        
        # Validações específicas para estratégia de daytrade de opções
        if proposal.strategy == 'daytrade_options':
            daytrade_cfg = self.config.get('daytrade_options', {})
            
            # Verificar risco máximo por trade
            max_risk_per_trade = daytrade_cfg.get('max_risk_per_trade', None)
            if max_risk_per_trade:
                proposal_risk = proposal.metadata.get('max_risk', proposal.quantity * proposal.price * 100)
                if proposal_risk > max_risk_per_trade:
                    reason = f'Risco por trade excedido: {proposal_risk:.2f} > {max_risk_per_trade:.2f}'
                    self._save_evaluation(proposal, 'REJECT', reason)
                    return ('REJECT', None, reason)
            
            # Verificar limite por ativo
            underlying = proposal.metadata.get('underlying', '')
            max_per_asset = self.config.get('max_per_asset_exposure', 0.05)
            current_asset_exposure = abs(self.portfolio.positions.get(proposal.symbol, 0) * proposal.price)
            if current_asset_exposure > self.portfolio.nav * max_per_asset:
                reason = f'Exposição máxima por ativo excedida para {underlying}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
            
            # Verificar liquidez mínima
            spread_pct = proposal.metadata.get('spread_pct', 1.0)
            max_spread = daytrade_cfg.get('max_spread_pct', 0.05)
            if spread_pct > max_spread:
                reason = f'Spread muito alto: {spread_pct:.2%} > {max_spread:.2%}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
            
            # Verificar exposição agregada em opções curtas
            total_options_exposure = sum(
                abs(qty * price) for symbol, qty in self.portfolio.positions.items()
                if 'options' in symbol.lower() or '_C_' in symbol or '_P_' in symbol
            )
            max_options_exposure = daytrade_cfg.get('max_options_exposure_pct', 0.15)
            if total_options_exposure > self.portfolio.nav * max_options_exposure:
                reason = f'Exposição agregada em opções excedida: {total_options_exposure:.2f}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
        
        # Verificar limites de exposição
        max_exposure = self.config.get('max_exposure', 0.5)
        current_exposure = abs(sum(self.portfolio.positions.values()))
        if current_exposure > self.portfolio.nav * max_exposure:
            reason = f'Exposição máxima excedida: {current_exposure:.2f}'
            self._save_evaluation(proposal, 'REJECT', reason)
            return ('REJECT', None, reason)
        
        # Verificar limites de greeks
        greeks = self.portfolio.get_aggregate_greeks(market_data)
        max_delta = self.config.get('max_delta', 1000)
        max_gamma = self.config.get('max_gamma', 500)
        max_vega = self.config.get('max_vega', 1000)
        
        # Adicionar greeks da proposta atual aos agregados
        if proposal.strategy == 'daytrade_options' and proposal.metadata:
            prop_delta = proposal.metadata.get('delta', 0) * proposal.quantity * 100
            prop_gamma = proposal.metadata.get('gamma', 0) * proposal.quantity * 100
            prop_vega = proposal.metadata.get('vega', 0) * proposal.quantity * 100
            
            projected_delta = greeks['delta'] + prop_delta
            projected_gamma = greeks['gamma'] + prop_gamma
            projected_vega = greeks['vega'] + prop_vega
            
            if abs(projected_delta) > max_delta:
                reason = f'Delta agregado projetado excedido: {projected_delta:.2f}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
            
            if abs(projected_gamma) > max_gamma:
                reason = f'Gamma agregado projetado excedido: {projected_gamma:.2f}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
            
            if abs(projected_vega) > max_vega:
                reason = f'Vega agregado projetado excedido: {projected_vega:.2f}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
        else:
            if abs(greeks['delta']) > max_delta:
                reason = f'Delta agregado excedido: {greeks["delta"]:.2f}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
            
            if abs(greeks['gamma']) > max_gamma:
                reason = f'Gamma agregado excedido: {greeks["gamma"]:.2f}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
            
            if abs(greeks['vega']) > max_vega:
                reason = f'Vega agregado excedido: {greeks["vega"]:.2f}'
                self._save_evaluation(proposal, 'REJECT', reason)
                return ('REJECT', None, reason)
        
        # Modificar quantidade se necessário
        max_position_size = self.config.get('max_position_size', 10000)
        if proposal.quantity > max_position_size:
            proposal.quantity = max_position_size
            reason = f'Quantidade reduzida para {max_position_size}'
            self._save_evaluation(proposal, 'MODIFY', reason, proposal)
            return ('MODIFY', proposal, reason)
        
        # Aprovar
        if self.logger:
            self.logger.log_risk_evaluation(proposal.proposal_id, 'APPROVE', 'Proposta aprovada', {})
        
        # Salvar avaliação no banco de dados
        self._save_evaluation(proposal, 'APPROVE', 'Proposta aprovada')
        
        return ('APPROVE', proposal, 'Proposta aprovada')
    
    def kill_switch(self):
        """Ativa kill switch."""
        self.kill_switch_active = True
        
        # Calcular perda de NAV
        nav_loss = (self.portfolio.initial_nav - self.portfolio.nav) / self.portfolio.initial_nav if self.portfolio.initial_nav > 0 else 0
        
        if self.logger:
            self.logger.log_decision('kill_switch', {'active': True, 'nav_loss': nav_loss})
        
        # Notificar por email
        if self.email_notifier:
            self.email_notifier.notify_kill_switch(
                reason=f'NAV loss: {nav_loss:.2%}',
                nav_loss=nav_loss
            )

