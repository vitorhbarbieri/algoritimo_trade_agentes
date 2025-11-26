"""
Monitor de Mercado - Busca oportunidades e assimetrias em tempo real.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

try:
    from .pricing import BlackScholes
    from .market_data_api import create_market_data_api
    from .crypto_api import create_crypto_api
except ImportError:
    from pricing import BlackScholes
    from market_data_api import create_market_data_api
    from crypto_api import create_crypto_api

logger = logging.getLogger(__name__)


class MarketMonitor:
    """Monitora mercado buscando oportunidades e assimetrias."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.opportunities = []
        self.last_scan = None
    
    def scan_volatility_arbitrage(self, ticker: str, spot_price: float, options_chain: List[Dict]) -> List[Dict]:
        """
        Escaneia oportunidades de Volatility Arbitrage.
        
        Teoria: Opções com IV muito diferente da volatilidade histórica.
        Assimetria: Mispricing entre preço de mercado e modelo teórico.
        """
        opportunities = []
        
        if not options_chain:
            return opportunities
        
        bs = BlackScholes()
        r = self.config.get('risk_free_rate', 0.05)
        threshold = self.config.get('vol_arb_threshold', 0.05)
        
        # Calcular volatilidade histórica (simplificado)
        hist_vol = 0.25  # Placeholder - calcular de dados históricos
        
        for opt in options_chain:
            strike = opt.get('strike', 0)
            expiry = opt.get('expiry')
            days_to_expiry = (pd.to_datetime(expiry) - datetime.now()).days if expiry else 30
            
            if days_to_expiry <= 0:
                continue
            
            time_to_expiry = days_to_expiry / 365.0
            market_iv = opt.get('implied_vol', 0.25)
            market_price = opt.get('mid', 0)
            
            if market_price == 0:
                continue
            
            option_type = opt.get('option_type', 'C')
            
            # Preço teórico usando IV histórica
            theoretical_price = bs.price(spot_price, strike, time_to_expiry, r, hist_vol, option_type)
            
            # Preço teórico usando IV de mercado
            theoretical_price_iv = bs.price(spot_price, strike, time_to_expiry, r, market_iv, option_type)
            
            # Mispricing
            mispricing = (market_price - theoretical_price_iv) / theoretical_price_iv if theoretical_price_iv > 0 else 0
            
            # IV spread (diferença entre IV de mercado e histórica)
            iv_spread = market_iv - hist_vol
            
            if abs(mispricing) > threshold or abs(iv_spread) > 0.1:
                opportunities.append({
                    'type': 'vol_arb',
                    'ticker': ticker,
                    'strike': strike,
                    'expiry': expiry,
                    'option_type': option_type,
                    'mispricing': mispricing,
                    'iv_spread': iv_spread,
                    'market_price': market_price,
                    'theoretical_price': theoretical_price_iv,
                    'market_iv': market_iv,
                    'hist_vol': hist_vol,
                    'opportunity_score': abs(mispricing) + abs(iv_spread) * 2
                })
        
        return sorted(opportunities, key=lambda x: x['opportunity_score'], reverse=True)
    
    def scan_pairs_trading(self, ticker1: str, price1: float, ticker2: str, price2: float, 
                          history: List[float]) -> Optional[Dict]:
        """
        Escaneia oportunidades de Pairs Trading.
        
        Teoria: Cointegração entre dois ativos relacionados.
        Assimetria: Desvio temporário da relação histórica.
        """
        if len(history) < 30:
            return None
        
        ratio = price1 / price2 if price2 > 0 else 0
        mean_ratio = np.mean(history)
        std_ratio = np.std(history)
        
        if std_ratio == 0:
            return None
        
        zscore = (ratio - mean_ratio) / std_ratio
        threshold = self.config.get('pairs_zscore_threshold', 2.0)
        
        if abs(zscore) > threshold:
            return {
                'type': 'pairs',
                'ticker1': ticker1,
                'ticker2': ticker2,
                'price1': price1,
                'price2': price2,
                'ratio': ratio,
                'mean_ratio': mean_ratio,
                'zscore': zscore,
                'opportunity_score': abs(zscore),
                'signal': 'SELL_BUY' if zscore > 0 else 'BUY_SELL'
            }
        
        return None
    
    def scan_spread_arbitrage(self, symbol: str, bid: float, ask: float) -> Optional[Dict]:
        """
        Escaneia oportunidades de Spread Arbitrage.
        
        Teoria: Spread bid-ask anormalmente alto indica liquidez baixa.
        Assimetria: Oportunidade de fazer market making.
        """
        if bid == 0 or ask == 0:
            return None
        
        spread = ask - bid
        spread_pct = (spread / bid) * 100 if bid > 0 else 0
        
        threshold = self.config.get('spread_threshold', 0.5)  # 0.5%
        
        if spread_pct > threshold:
            return {
                'type': 'spread_arb',
                'symbol': symbol,
                'bid': bid,
                'ask': ask,
                'spread': spread,
                'spread_pct': spread_pct,
                'opportunity_score': spread_pct
            }
        
        return None
    
    def scan_momentum_opportunities(self, prices: pd.Series, volume: pd.Series) -> List[Dict]:
        """
        Escaneia oportunidades de Momentum.
        
        Teoria: Tendências persistem no curto prazo.
        Assimetria: Inércia de preços após movimentos fortes.
        """
        opportunities = []
        
        if len(prices) < 20:
            return opportunities
        
        # Calcular momentum
        returns = prices.pct_change()
        momentum_5 = returns.tail(5).mean()
        momentum_20 = returns.tail(20).mean()
        
        # Volume médio
        avg_volume = volume.tail(20).mean()
        current_volume = volume.iloc[-1] if len(volume) > 0 else 0
        
        # Volume spike
        volume_spike = (current_volume / avg_volume) if avg_volume > 0 else 1
        
        # Oportunidade se momentum forte + volume alto
        if abs(momentum_5) > 0.02 and volume_spike > 1.5:
            opportunities.append({
                'type': 'momentum',
                'momentum_5': momentum_5,
                'momentum_20': momentum_20,
                'volume_spike': volume_spike,
                'signal': 'BUY' if momentum_5 > 0 else 'SELL',
                'opportunity_score': abs(momentum_5) * volume_spike
            })
        
        return opportunities
    
    def scan_mean_reversion(self, prices: pd.Series) -> List[Dict]:
        """
        Escaneia oportunidades de Mean Reversion.
        
        Teoria: Preços retornam à média após desvios extremos.
        Assimetria: Movimentos exagerados que tendem a reverter.
        """
        opportunities = []
        
        if len(prices) < 20:
            return opportunities
        
        # Média móvel
        sma_20 = prices.tail(20).mean()
        current_price = prices.iloc[-1]
        
        # Desvio da média
        deviation = (current_price - sma_20) / sma_20 if sma_vol > 0 else 0
        
        # Volatilidade
        returns = prices.pct_change()
        volatility = returns.tail(20).std()
        
        # Z-score
        zscore = deviation / volatility if volatility > 0 else 0
        
        threshold = self.config.get('mean_reversion_threshold', 2.0)
        
        if abs(zscore) > threshold:
            opportunities.append({
                'type': 'mean_reversion',
                'current_price': current_price,
                'sma_20': sma_20,
                'deviation': deviation,
                'zscore': zscore,
                'signal': 'BUY' if zscore < -threshold else 'SELL',
                'opportunity_score': abs(zscore)
            })
        
        return opportunities
    
    def scan_all_opportunities(self, market_data: Dict) -> List[Dict]:
        """Escaneia todas as oportunidades disponíveis."""
        all_opportunities = []
        
        # Volatility Arbitrage
        for ticker, data in market_data.get('spot', {}).items():
            if ticker in market_data.get('options', {}):
                vol_arb = self.scan_volatility_arbitrage(
                    ticker,
                    data.get('close', 0),
                    market_data['options'][ticker]
                )
                all_opportunities.extend(vol_arb)
        
        # Pairs Trading
        spot_data = market_data.get('spot', {})
        tickers = list(spot_data.keys())
        for i in range(len(tickers)):
            for j in range(i+1, len(tickers)):
                ticker1, ticker2 = tickers[i], tickers[j]
                # Implementar histórico de ratios
                pairs_opp = self.scan_pairs_trading(
                    ticker1, spot_data[ticker1].get('close', 0),
                    ticker2, spot_data[ticker2].get('close', 0),
                    []
                )
                if pairs_opp:
                    all_opportunities.append(pairs_opp)
        
        return sorted(all_opportunities, key=lambda x: x.get('opportunity_score', 0), reverse=True)

