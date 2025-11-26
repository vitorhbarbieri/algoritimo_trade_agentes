"""
Módulo de precificação: Black-Scholes, greeks e implied volatility.
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from typing import Tuple, Dict


class BlackScholes:
    """Implementação de Black-Scholes e greeks analíticos."""
    
    @staticmethod
    def d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
        """Calcula d1 e d2 para Black-Scholes."""
        if T <= 0:
            return (0.0, 0.0)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return (d1, d2)
    
    @staticmethod
    def price(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'C') -> float:
        """Calcula preço de opção usando Black-Scholes."""
        if T <= 0:
            if option_type == 'C':
                return max(0, S - K)
            else:
                return max(0, K - S)
        
        if sigma <= 0:
            if option_type == 'C':
                return max(0, S - K * np.exp(-r * T))
            else:
                return max(0, K * np.exp(-r * T) - S)
        
        d1, d2 = BlackScholes.d1_d2(S, K, T, r, sigma)
        
        if option_type == 'C':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        return max(0, price)
    
    @staticmethod
    def delta(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'C') -> float:
        """Calcula delta."""
        if T <= 0:
            if option_type == 'C':
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
        
        if sigma <= 0:
            return 0.0
        
        d1, _ = BlackScholes.d1_d2(S, K, T, r, sigma)
        
        if option_type == 'C':
            return norm.cdf(d1)
        else:
            return -norm.cdf(-d1)
    
    @staticmethod
    def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calcula gamma."""
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1, _ = BlackScholes.d1_d2(S, K, T, r, sigma)
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    @staticmethod
    def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calcula vega."""
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1, _ = BlackScholes.d1_d2(S, K, T, r, sigma)
        return S * norm.pdf(d1) * np.sqrt(T) / 100.0
    
    @staticmethod
    def theta(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'C') -> float:
        """Calcula theta."""
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1, d2 = BlackScholes.d1_d2(S, K, T, r, sigma)
        
        term1 = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
        
        if option_type == 'C':
            term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
        else:
            term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
        
        return (term1 + term2) / 365.0
    
    @staticmethod
    def all_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'C') -> Dict[str, float]:
        """Calcula todos os greeks."""
        return {
            'delta': BlackScholes.delta(S, K, T, r, sigma, option_type),
            'gamma': BlackScholes.gamma(S, K, T, r, sigma),
            'vega': BlackScholes.vega(S, K, T, r, sigma),
            'theta': BlackScholes.theta(S, K, T, r, sigma, option_type)
        }
    
    @staticmethod
    def implied_volatility(price: float, S: float, K: float, T: float, r: float, option_type: str = 'C') -> float:
        """Calcula volatilidade implícita."""
        if T <= 0:
            return 0.0
        
        if option_type == 'C':
            intrinsic = max(0, S - K)
        else:
            intrinsic = max(0, K - S)
        
        if price <= intrinsic:
            return 0.0
        
        def objective(sigma):
            return BlackScholes.price(S, K, T, r, sigma, option_type) - price
        
        try:
            iv = brentq(objective, 0.0001, 2.0, maxiter=100)
            return max(0.0, iv)
        except:
            for sigma in np.linspace(0.01, 2.0, 200):
                if abs(objective(sigma)) < 0.01:
                    return sigma
            return 0.25

