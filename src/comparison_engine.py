"""
Motor de Comparação Matemática: Opções vs Ações
Compara matematicamente qual é a melhor oportunidade de investimento.
"""

import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class InvestmentOpportunity:
    """Representa uma oportunidade de investimento."""
    instrument_type: str  # 'options' ou 'spot'
    symbol: str
    expected_return: float
    risk_adjusted_return: float  # Sharpe-like ratio
    leverage_effect: float  # Efeito de alavancagem
    capital_required: float
    max_loss: float
    max_gain: float
    score: float  # Score final para comparação


class ComparisonEngine:
    """
    Motor de comparação matemática entre opções e ações.
    
    Métricas utilizadas:
    1. Expected Return (Retorno Esperado)
    2. Risk-Adjusted Return (Sharpe Ratio)
    3. Leverage Effect (Efeito de Alavancagem)
    4. Capital Efficiency (Eficiência de Capital)
    5. Risk/Reward Ratio
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate
    
    def calculate_spot_opportunity(
        self,
        asset: str,
        current_price: float,
        expected_price_change_pct: float,
        volatility: float,
        capital_available: float,
        risk_per_trade: float = 0.02
    ) -> InvestmentOpportunity:
        """
        Calcula métricas para oportunidade em ação (spot).
        
        Args:
            asset: Ticker da ação
            current_price: Preço atual
            expected_price_change_pct: Movimento esperado (%)
            volatility: Volatilidade histórica
            capital_available: Capital disponível
            risk_per_trade: Risco máximo por trade (% do capital)
        """
        # Capital alocado baseado no risco
        max_loss_amount = capital_available * risk_per_trade
        stop_loss_pct = 0.02  # 2% stop loss padrão para ações
        capital_required = max_loss_amount / stop_loss_pct
        
        # Limitar ao capital disponível
        capital_required = min(capital_required, capital_available)
        quantity = capital_required / current_price
        
        # Retorno esperado
        expected_return = expected_price_change_pct
        
        # Retorno em valor
        expected_return_value = capital_required * (expected_price_change_pct / 100)
        
        # Risk-adjusted return (Sharpe-like)
        # Assumindo que o movimento esperado é a média e volatilidade é o desvio
        risk_adjusted_return = (expected_price_change_pct / 100 - self.risk_free_rate) / volatility if volatility > 0 else 0
        
        # Leverage effect (1:1 para ações)
        leverage_effect = 1.0
        
        # Max loss e gain
        max_loss = capital_required * stop_loss_pct
        max_gain = capital_required * (expected_price_change_pct / 100)
        
        # Score combinado
        score = self._calculate_score(
            expected_return_value,
            risk_adjusted_return,
            leverage_effect,
            capital_required,
            max_loss,
            max_gain
        )
        
        return InvestmentOpportunity(
            instrument_type='spot',
            symbol=asset,
            expected_return=expected_return_value,
            risk_adjusted_return=risk_adjusted_return,
            leverage_effect=leverage_effect,
            capital_required=capital_required,
            max_loss=max_loss,
            max_gain=max_gain,
            score=score
        )
    
    def calculate_option_opportunity(
        self,
        asset: str,
        strike: float,
        current_price: float,
        option_premium: float,
        delta: float,
        gamma: float,
        vega: float,
        days_to_expiry: int,
        implied_vol: float,
        expected_price_change_pct: float,
        capital_available: float,
        risk_per_trade: float = 0.02
    ) -> InvestmentOpportunity:
        """
        Calcula métricas para oportunidade em opção.
        
        Args:
            asset: Ticker do ativo subjacente
            strike: Strike da opção
            current_price: Preço atual do ativo
            option_premium: Prêmio da opção
            delta: Delta da opção
            gamma: Gamma da opção
            vega: Vega da opção
            days_to_expiry: Dias até expiração
            implied_vol: Volatilidade implícita
            expected_price_change_pct: Movimento esperado do ativo (%)
            capital_available: Capital disponível
            risk_per_trade: Risco máximo por trade (% do capital)
        """
        # Capital alocado baseado no risco
        max_loss_amount = capital_available * risk_per_trade
        
        # Para opções, o risco máximo é o prêmio pago
        premium_per_contract = option_premium * 100  # Opções são multiplicadas por 100
        contracts_affordable = int(max_loss_amount / premium_per_contract)
        
        if contracts_affordable <= 0:
            contracts_affordable = 1
        
        capital_required = contracts_affordable * premium_per_contract
        
        # Retorno esperado da opção baseado no movimento do ativo
        # Movimento esperado em valor
        price_change = current_price * (expected_price_change_pct / 100)
        
        # Valor da opção após movimento (aproximação usando delta)
        # Para calls: novo_preço ≈ preço_atual + (delta * movimento_ativo)
        new_option_value = option_premium + (delta * price_change)
        
        # Retorno esperado
        expected_return_pct = ((new_option_value - option_premium) / option_premium) * 100 if option_premium > 0 else 0
        expected_return_value = capital_required * (expected_return_pct / 100)
        
        # Risk-adjusted return
        # Considerar volatilidade implícita e tempo até expiração
        time_factor = days_to_expiry / 365.0
        risk_adjusted_return = (expected_return_pct / 100 - self.risk_free_rate * time_factor) / implied_vol if implied_vol > 0 else 0
        
        # Leverage effect (alavancagem da opção)
        # Quantas ações você controla com o mesmo capital?
        shares_equivalent = contracts_affordable * 100  # Cada contrato = 100 ações
        capital_for_shares = shares_equivalent * current_price
        leverage_effect = capital_for_shares / capital_required if capital_required > 0 else 1.0
        
        # Max loss (prêmio pago) e max gain (ilimitado teoricamente, mas limitamos pelo movimento esperado)
        max_loss = capital_required  # Perda total do prêmio
        max_gain = expected_return_value  # Ganho esperado
        
        # Score combinado
        score = self._calculate_score(
            expected_return_value,
            risk_adjusted_return,
            leverage_effect,
            capital_required,
            max_loss,
            max_gain
        )
        
        return InvestmentOpportunity(
            instrument_type='options',
            symbol=f"{asset}_{strike}_C",
            expected_return=expected_return_value,
            risk_adjusted_return=risk_adjusted_return,
            leverage_effect=leverage_effect,
            capital_required=capital_required,
            max_loss=max_loss,
            max_gain=max_gain,
            score=score
        )
    
    def compare_opportunities(
        self,
        spot_opp: InvestmentOpportunity,
        option_opp: InvestmentOpportunity
    ) -> Tuple[InvestmentOpportunity, str]:
        """
        Compara duas oportunidades e retorna a melhor.
        
        Returns:
            Tuple[InvestmentOpportunity, str]: (melhor oportunidade, razão)
        """
        # Comparar scores
        if option_opp.score > spot_opp.score:
            reason = (
                f"Opcao melhor: Score {option_opp.score:.2f} vs {spot_opp.score:.2f}. "
                f"Leverage: {option_opp.leverage_effect:.2f}x, "
                f"Retorno esperado: R$ {option_opp.expected_return:.2f} vs R$ {spot_opp.expected_return:.2f}"
            )
            return option_opp, reason
        else:
            reason = (
                f"Acao melhor: Score {spot_opp.score:.2f} vs {option_opp.score:.2f}. "
                f"Menor risco, retorno esperado: R$ {spot_opp.expected_return:.2f} vs R$ {option_opp.expected_return:.2f}"
            )
            return spot_opp, reason
    
    def _calculate_score(
        self,
        expected_return_value: float,
        risk_adjusted_return: float,
        leverage_effect: float,
        capital_required: float,
        max_loss: float,
        max_gain: float
    ) -> float:
        """
        Calcula score combinado para comparação.
        
        Fórmula:
        score = (expected_return * risk_adjusted_return * leverage_effect) / (capital_required / max_loss)
        
        Quanto maior o score, melhor a oportunidade.
        """
        if capital_required == 0 or max_loss == 0:
            return 0.0
        
        # Normalizar valores
        return_normalized = expected_return_value / 1000.0  # Normalizar para escala de milhares
        risk_adj_normalized = max(risk_adjusted_return, 0)  # Não permitir negativo
        leverage_normalized = min(leverage_effect, 10.0)  # Limitar leverage a 10x
        
        # Eficiência de capital (quanto retorno por real investido)
        capital_efficiency = expected_return_value / capital_required if capital_required > 0 else 0
        
        # Risk/reward ratio
        risk_reward_ratio = max_gain / max_loss if max_loss > 0 else 0
        
        # Score combinado (pesos ajustáveis)
        score = (
            return_normalized * 0.3 +  # Retorno esperado (30%)
            risk_adj_normalized * 0.3 +  # Risk-adjusted return (30%)
            leverage_normalized * 0.2 +  # Leverage effect (20%)
            capital_efficiency * 0.1 +  # Capital efficiency (10%)
            risk_reward_ratio * 0.1  # Risk/reward ratio (10%)
        )
        
        return score

