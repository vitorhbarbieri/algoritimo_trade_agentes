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
    from .comparison_engine import ComparisonEngine, InvestmentOpportunity
except ImportError:
    from pricing import BlackScholes
    from utils import StructuredLogger
    from comparison_engine import ComparisonEngine, InvestmentOpportunity


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
        self.comparison_engine = ComparisonEngine(
            risk_free_rate=config.get('risk_free_rate', 0.05)
        )
    
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
                import logging
                logging.warning("DayTradeOptionsStrategy: Nenhum dado spot disponível")
            return proposals
        
        # Se não houver opções, continuar para gerar propostas spot
        if not options_data:
            if self.logger:
                import logging
                logging.info("DayTradeOptionsStrategy: Nenhum dado de opções disponível - gerando propostas spot")
            # Continuar para gerar propostas baseadas em momentum spot
            # A estratégia pode gerar propostas spot quando enable_spot=True
        
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
                
                # 3. COMPARAÇÃO MATEMÁTICA: Opções vs Ações
                # Primeiro, avaliar oportunidade em ações (spot)
                STANDARD_TICKET_VALUE = 1000.0
                take_profit_pct = cfg.get('take_profit_pct', 0.10)
                stop_loss_pct = cfg.get('stop_loss_pct', 0.40)
                
                # Calcular volatilidade histórica (simplificado - usar IV como proxy se disponível)
                historical_volatility = spot_info.get('volatility', spot_info.get('iv', 0.25))
                if historical_volatility == 0:
                    historical_volatility = 0.25  # Fallback
                
                # Calcular oportunidade em ações
                spot_opportunity = None
                enable_spot = cfg.get('enable_spot_trading', True)
                if enable_spot:
                    try:
                        spot_opportunity = self.comparison_engine.calculate_spot_opportunity(
                            asset=asset,
                            current_price=last_price,
                            expected_price_change_pct=intraday_return * 100,  # Converter para %
                            volatility=historical_volatility,
                            capital_available=nav,
                            risk_per_trade=cfg.get('risk_per_trade', 0.002)
                        )
                    except Exception as e:
                        if self.logger:
                            import logging
                            logging.warning(f"Erro ao calcular oportunidade spot para {asset}: {e}")
                
                # Avaliar melhor opção disponível
                best_option_opportunity = None
                best_option_call = None
                
                if viable_calls:
                    # Selecionar melhor call (maior gamma, menor spread, maior liquidez)
                    best_call = max(
                        viable_calls,
                        key=lambda o: (o['gamma'], -o['spread_pct'], o['volume'])
                    )
                    
                    # Calcular oportunidade em opções
                    try:
                        best_option_opportunity = self.comparison_engine.calculate_option_opportunity(
                            asset=asset,
                            strike=best_call['strike'],
                            current_price=last_price,
                            option_premium=best_call['mid'],
                            delta=best_call['delta'],
                            gamma=best_call['gamma'],
                            vega=best_call['vega'],
                            days_to_expiry=best_call['days_to_expiry'],
                            implied_vol=best_call['iv'],
                            expected_price_change_pct=intraday_return * 100,
                            capital_available=nav,
                            risk_per_trade=cfg.get('risk_per_trade', 0.002)
                        )
                        best_option_call = best_call
                    except Exception as e:
                        if self.logger:
                            import logging
                            logging.warning(f"Erro ao calcular oportunidade opção para {asset}: {e}")
                
                # Comparar e escolher a melhor oportunidade
                if spot_opportunity and best_option_opportunity:
                    best_opp, comparison_reason = self.comparison_engine.compare_opportunities(
                        spot_opportunity, best_option_opportunity
                    )
                    
                    if self.logger:
                        import logging
                        logging.info(f"{asset}: {comparison_reason}")
                    
                    # Gerar proposta baseada na melhor oportunidade
                    if best_opp.instrument_type == 'options':
                        proposal = self._create_option_proposal(
                            asset, best_option_call, last_price, intraday_return, volume_ratio,
                            timestamp, cfg, STANDARD_TICKET_VALUE, best_opp.score
                        )
                        if proposal:
                            proposals.append(proposal)
                    else:
                        proposal = self._create_spot_proposal(
                            asset, last_price, intraday_return, volume_ratio,
                            timestamp, cfg, STANDARD_TICKET_VALUE, best_opp.score
                        )
                        if proposal:
                            proposals.append(proposal)
                
                elif best_option_opportunity:
                    # Só tem opção disponível
                    proposal = self._create_option_proposal(
                        asset, best_option_call, last_price, intraday_return, volume_ratio,
                        timestamp, cfg, STANDARD_TICKET_VALUE, best_option_opportunity.score
                    )
                    if proposal:
                        proposals.append(proposal)
                
                elif spot_opportunity and enable_spot:
                    # Só tem ação disponível
                    proposal = self._create_spot_proposal(
                        asset, last_price, intraday_return, volume_ratio,
                        timestamp, cfg, STANDARD_TICKET_VALUE, spot_opportunity.score
                    )
                    if proposal:
                        proposals.append(proposal)
                
                # Se não houver opções mas estratégia permite trading spot, continuar
                elif enable_spot and not viable_calls:
                    # Gerar proposta de ação mesmo sem opções
                    proposal = self._create_spot_proposal(
                        asset, last_price, intraday_return, volume_ratio,
                        timestamp, cfg, STANDARD_TICKET_VALUE, 0.5  # Score padrão
                    )
                    if proposal:
                        proposals.append(proposal)
            
            except Exception as e:
                if self.logger:
                    import logging
                    logging.error(f"Erro em DayTradeOptionsStrategy para {asset}: {str(e)}")
                continue
        
        # Aplicar filtro de horário (priorizar 12:00-15:00)
        # Baseado em análise: 53.4% dos sucessos ocorrem neste horário
        current_hour = timestamp.hour if hasattr(timestamp, 'hour') else pd.Timestamp.now().hour
        
        def calcular_score_com_horario(prop):
            """Calcula score ajustado pelo horário."""
            base_score = prop.metadata.get('comparison_score', 0)
            
            # Multiplicador baseado no horário
            if 12 <= current_hour <= 15:
                # Horário ideal: multiplicador 1.2x (prioriza)
                horario_multiplier = 1.2
            elif 10 <= current_hour < 12 or 15 < current_hour <= 16:
                # Horário bom: multiplicador 1.0x (normal)
                horario_multiplier = 1.0
            else:
                # Horário não ideal: multiplicador 0.7x (reduz prioridade)
                horario_multiplier = 0.7
            
            return base_score * horario_multiplier
        
        # Ordenar propostas por score ajustado (priorização)
        proposals_with_scores = []
        for prop in proposals:
            adjusted_score = calcular_score_com_horario(prop)
            proposals_with_scores.append((adjusted_score, prop))
        
        # Ordenar por score ajustado (maior primeiro)
        proposals_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Filtrar por score mínimo se configurado (usar score original, não ajustado)
        min_score = cfg.get('min_comparison_score', 0)
        filtered_proposals = []
        for adjusted_score, prop in proposals_with_scores:
            original_score = prop.metadata.get('comparison_score', 0)
            if original_score >= min_score:
                filtered_proposals.append(prop)
        
        # Retornar apenas as melhores oportunidades (top 10)
        return filtered_proposals[:10]
    
    def _create_option_proposal(
        self, asset: str, best_call: Dict, last_price: float, intraday_return: float,
        volume_ratio: float, timestamp: pd.Timestamp, cfg: Dict,
        STANDARD_TICKET_VALUE: float, comparison_score: float
    ) -> Optional[OrderProposal]:
        """Cria proposta de opção."""
        try:
            premium_unit = best_call['mid']
            premium_per_contract = premium_unit * 100
            
            if premium_per_contract == 0:
                return None
            
            qty = int(STANDARD_TICKET_VALUE / premium_per_contract)
            if qty <= 0:
                qty = 1
            
            actual_value = qty * premium_per_contract
            if actual_value < STANDARD_TICKET_VALUE * 0.8:
                qty = int(STANDARD_TICKET_VALUE / premium_per_contract) + 1
                actual_value = qty * premium_per_contract
            
            # ID simplificado: apenas últimos 4 dígitos do timestamp
            # Exemplo: 3456 (últimos 4 dígitos do timestamp Unix)
            timestamp_short = str(int(timestamp.timestamp()))[-4:]
            proposal_id = timestamp_short
            
            entry_price_unit = best_call['ask']
            entry_price_total = entry_price_unit * qty * 100
            take_profit_pct = cfg.get('take_profit_pct', 0.10)
            stop_loss_pct = cfg.get('stop_loss_pct', 0.40)
            
            exit_price_tp_unit = entry_price_unit * (1 + take_profit_pct)
            exit_price_tp_total = exit_price_tp_unit * qty * 100
            exit_price_sl_unit = entry_price_unit * (1 - stop_loss_pct)
            exit_price_sl_total = exit_price_sl_unit * qty * 100
            
            ticket_value = STANDARD_TICKET_VALUE
            gain_value = ticket_value * take_profit_pct
            loss_value = ticket_value * stop_loss_pct
            
            proposal = OrderProposal(
                proposal_id=proposal_id,
                strategy='daytrade_options',
                instrument_type='options',
                symbol=f"{asset}_{best_call['strike']}_C_{best_call['expiry'].strftime('%Y%m%d')}",
                side='BUY',
                quantity=qty,
                price=entry_price_unit,
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
                    'ticket_value': float(ticket_value),
                    'entry_price': float(entry_price_unit),
                    'entry_price_total': float(entry_price_total),
                    'exit_price_tp': float(exit_price_tp_unit),
                    'exit_price_tp_total': float(exit_price_tp_total),
                    'exit_price_sl': float(exit_price_sl_unit),
                    'exit_price_sl_total': float(exit_price_sl_total),
                    'take_profit_pct': take_profit_pct,
                    'stop_loss_pct': stop_loss_pct,
                    'gain_value': float(gain_value),
                    'loss_value': float(loss_value),
                    'comparison_score': float(comparison_score),
                    'comparison_type': 'options',
                    'eod_close': True
                }
            )
            
            return proposal
        except Exception as e:
            if self.logger:
                import logging
                logging.error(f"Erro ao criar proposta de opção: {e}")
            return None
    
    def _create_spot_proposal(
        self, asset: str, last_price: float, intraday_return: float,
        volume_ratio: float, timestamp: pd.Timestamp, cfg: Dict,
        STANDARD_TICKET_VALUE: float, comparison_score: float
    ) -> Optional[OrderProposal]:
        """Cria proposta de ação (spot)."""
        try:
            take_profit_pct = cfg.get('take_profit_pct', 0.10)
            stop_loss_pct = cfg.get('stop_loss_pct', 0.40)
            
            # Calcular quantidade para ticket de R$ 1000
            qty = int(STANDARD_TICKET_VALUE / last_price)
            if qty <= 0:
                return None
            
            actual_value = qty * last_price
            
            # ID simplificado: apenas últimos 4 dígitos do timestamp
            timestamp_short = str(int(timestamp.timestamp()))[-4:]
            proposal_id = timestamp_short
            
            entry_price = last_price
            entry_price_total = actual_value
            
            exit_price_tp = entry_price * (1 + take_profit_pct)
            exit_price_tp_total = exit_price_tp * qty
            exit_price_sl = entry_price * (1 - stop_loss_pct)
            exit_price_sl_total = exit_price_sl * qty
            
            ticket_value = STANDARD_TICKET_VALUE
            gain_value = ticket_value * take_profit_pct
            loss_value = ticket_value * stop_loss_pct
            
            proposal = OrderProposal(
                proposal_id=proposal_id,
                strategy='daytrade_options',
                instrument_type='spot',
                symbol=asset,
                side='BUY',
                quantity=qty,
                price=entry_price,
                order_type='LIMIT',
                metadata={
                    'underlying': asset,
                    'intraday_return': float(intraday_return),
                    'volume_ratio': float(volume_ratio),
                    'ticket_value': float(ticket_value),
                    'entry_price': float(entry_price),
                    'entry_price_total': float(entry_price_total),
                    'exit_price_tp': float(exit_price_tp),
                    'exit_price_tp_total': float(exit_price_tp_total),
                    'exit_price_sl': float(exit_price_sl),
                    'exit_price_sl_total': float(exit_price_sl_total),
                    'take_profit_pct': take_profit_pct,
                    'stop_loss_pct': stop_loss_pct,
                    'gain_value': float(gain_value),
                    'loss_value': float(loss_value),
                    'comparison_score': float(comparison_score),
                    'comparison_type': 'spot',
                    'eod_close': True
                }
            )
            
            return proposal
        except Exception as e:
            if self.logger:
                import logging
                logging.error(f"Erro ao criar proposta de ação: {e}")
            return None


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
        """
        Gera propostas de daytrade focadas exclusivamente em ativos brasileiros (B3).
        Filtra automaticamente apenas tickers com sufixo .SA
        """
        proposals = []
        
        # FILTRO CRÍTICO: Processar APENAS ativos brasileiros (.SA)
        # Filtrar market_data para garantir que apenas dados brasileiros sejam processados
        if 'spot' in market_data:
            market_data['spot'] = {
                k: v for k, v in market_data['spot'].items() 
                if '.SA' in str(k) or k.endswith('.SA')
            }
        
        if 'options' in market_data:
            # Filtrar opções apenas de ativos brasileiros
            if isinstance(market_data['options'], dict):
                market_data['options'] = {
                    k: v for k, v in market_data['options'].items()
                    if '.SA' in str(k) or k.endswith('.SA')
                }
            elif isinstance(market_data['options'], list):
                market_data['options'] = [
                    opt for opt in market_data['options']
                    if isinstance(opt, dict) and (
                        '.SA' in str(opt.get('underlying', '')) or 
                        opt.get('underlying', '').endswith('.SA')
                    )
                ]
        
        # Executar estratégias modulares
        nav = self.config.get('nav', 1000000)
        for strategy in self.strategies:
            try:
                strategy_proposals = strategy.generate(nav, date, market_data)
                proposals.extend(strategy_proposals)
            except Exception as e:
                if self.logger:
                    import logging
                    logging.error(f"Erro em estratégia {strategy.__class__.__name__}: {str(e)}")
        
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
                        'metadata': proposal.metadata,
                        'status': 'gerada'  # Status inicial: proposta gerada mas não aprovada pelo RiskAgent
                    }
                    self.orders_repo.save_proposal(proposal_dict)
                except Exception as e:
                    if self.logger:
                        import logging
                        logging.error(f"Erro ao salvar proposta {proposal.proposal_id}: {e}")
        
        return proposals
    
    def _vol_arb_strategy(self, date: pd.Timestamp, market_data: Dict) -> List[OrderProposal]:
        """Delta-hedged Volatility Arbitrage."""
        proposals = []
        threshold = self.config.get('vol_arb_threshold', 0.05)
        underlying = self.config.get('vol_arb_underlying', 'PETR4.SA')
        
        # FILTRO: Apenas ativos brasileiros
        if not ('.SA' in str(underlying) or underlying.endswith('.SA')):
            return proposals
        
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
        ticker1 = self.config.get('pairs_ticker1', 'PETR4.SA')
        ticker2 = self.config.get('pairs_ticker2', 'VALE3.SA')
        
        # FILTRO: Apenas ativos brasileiros
        if not (('.SA' in str(ticker1) or ticker1.endswith('.SA')) and 
                ('.SA' in str(ticker2) or ticker2.endswith('.SA'))):
            return proposals
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
                import pytz
                # Usar timezone B3 para timestamp
                b3_tz = pytz.timezone('America/Sao_Paulo')
                timestamp = datetime.now(b3_tz).isoformat()
                
                evaluation_dict = {
                    'proposal_id': proposal.proposal_id,
                    'timestamp': timestamp,
                    'decision': decision,
                    'reason': reason,
                    'details': {},
                    'modified_quantity': modified_proposal.quantity if modified_proposal else None,
                    'modified_price': modified_proposal.price if modified_proposal else None
                }
                success = self.orders_repo.save_risk_evaluation(evaluation_dict)
                if not success:
                    import logging
                    logging.warning(f"Falha ao salvar avaliação {proposal.proposal_id}")
            except Exception as e:
                import logging
                logging.error(f"Erro ao salvar avaliação {proposal.proposal_id}: {e}")
                import traceback
                logging.error(traceback.format_exc())
    
    def evaluate_proposal(self, proposal: OrderProposal, market_data: Dict) -> Tuple[str, Optional[OrderProposal], str]:
        """
        Avalia proposta.
        Returns: (decision, modified_proposal, reason)
        decision: 'APPROVE', 'MODIFY', 'REJECT'
        """
        if self.kill_switch_active:
            reason = 'Kill switch ativo'
            self._save_evaluation(proposal, 'REJECT', reason)
            return ('REJECT', None, reason)
        
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
            # Nota: Para calcular exposição precisa, precisaríamos dos preços de mercado
            # Por enquanto, usamos uma estimativa baseada na quantidade
            total_options_exposure = sum(
                abs(qty * proposal.price * 100) if proposal.price else abs(qty * 1000)
                for symbol, qty in self.portfolio.positions.items()
                if 'options' in symbol.lower() or '_C_' in symbol or '_P_' in symbol
            )
            # Se não houver posições, usar o risco da proposta atual
            if total_options_exposure == 0:
                total_options_exposure = abs(proposal.quantity * proposal.price * 100) if proposal.price else 0
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
            # Verificar se logger tem método log_decision (StructuredLogger) ou usar logging padrão
            if hasattr(self.logger, 'log_decision'):
                self.logger.log_decision('kill_switch', {'active': True, 'nav_loss': nav_loss})
            else:
                import logging
                logging.warning(f"Kill switch ativado. Perda NAV: {nav_loss:.2%}")
        
        # Notificar por email
        if self.email_notifier:
            self.email_notifier.notify_kill_switch(
                reason=f'NAV loss: {nav_loss:.2%}',
                nav_loss=nav_loss
            )

