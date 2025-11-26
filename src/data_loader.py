"""
Módulo para geração e carregamento de dados sintéticos e CSV.
Também suporta busca de dados reais via APIs.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

try:
    from .market_data_api import fetch_real_market_data, create_market_data_api
except ImportError:
    try:
        from market_data_api import fetch_real_market_data, create_market_data_api
    except ImportError:
        def fetch_real_market_data(*args, **kwargs):
            raise ImportError("market_data_api não disponível")
        def create_market_data_api(*args, **kwargs):
            raise ImportError("market_data_api não disponível")

class DataLoader:
    """Carrega dados de CSV ou gera dados sintéticos."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def generate_synthetic_spot(self, tickers: list = ['AAPL', 'MSFT'], start_date: str = '2024-01-01', end_date: str = '2024-12-31', seed: int = 42) -> pd.DataFrame:
        """Gera dados sintéticos de ações."""
        np.random.seed(seed)
        dates = pd.date_range(start_date, end_date, freq='D')
        dates = dates[dates.weekday < 5]
        data = []
        for ticker in tickers:
            n_days = len(dates)
            returns = np.random.normal(0.0005, 0.02, n_days)
            base_price = 150.0 if ticker == 'AAPL' else 300.0
            prices = base_price * np.exp(np.cumsum(returns))
            for i, date in enumerate(dates):
                price = prices[i]
                high = price * (1 + abs(np.random.normal(0, 0.01)))
                low = price * (1 - abs(np.random.normal(0, 0.01)))
                open_price = price * (1 + np.random.normal(0, 0.005))
                volume = int(np.random.lognormal(14, 0.5))
                data.append({'date': date, 'ticker': ticker, 'open': round(open_price, 2), 'high': round(high, 2), 'low': round(low, 2), 'close': round(price, 2), 'volume': volume})
        df = pd.DataFrame(data)
        return df.sort_values(['date', 'ticker'])
    
    def generate_synthetic_futures(self, contracts: list = ['ESZ25'], start_date: str = '2024-01-01', end_date: str = '2024-12-31', seed: int = 42) -> pd.DataFrame:
        """Gera dados sintéticos de futuros."""
        np.random.seed(seed + 1)
        dates = pd.date_range(start_date, end_date, freq='D')
        dates = dates[dates.weekday < 5]
        data = []
        for contract in contracts:
            expiry = pd.to_datetime('2024-12-19')
            n_days = len(dates)
            returns = np.random.normal(0.0003, 0.015, n_days)
            base_price = 4300.0
            prices = base_price * np.exp(np.cumsum(returns))
            for i, date in enumerate(dates):
                if date >= expiry:
                    continue
                price = prices[i]
                high = price * (1 + abs(np.random.normal(0, 0.008)))
                low = price * (1 - abs(np.random.normal(0, 0.008)))
                open_price = price * (1 + np.random.normal(0, 0.004))
                volume = int(np.random.lognormal(12, 0.6))
                data.append({'date': date, 'contract': contract, 'expiry': expiry, 'open': round(open_price, 2), 'high': round(high, 2), 'low': round(low, 2), 'close': round(price, 2), 'volume': volume})
        df = pd.DataFrame(data)
        return df.sort_values(['date', 'contract'])
    
    def generate_synthetic_options_chain(self, underlying: str = 'AAPL', start_date: str = '2024-01-01', end_date: str = '2024-12-31', strikes: Optional[list] = None, seed: int = 42) -> pd.DataFrame:
        """Gera chain de opções sintética."""
        np.random.seed(seed + 2)
        if strikes is None:
            base_strike = 150.0
            strikes = [base_strike + i * 5 for i in range(-5, 6)]
        dates = pd.date_range(start_date, end_date, freq='D')
        dates = dates[dates.weekday < 5]
        spot_df = self.generate_synthetic_spot([underlying], start_date, end_date, seed)
        spot_prices = spot_df.set_index(['date', 'ticker'])['close']
        data = []
        expiry = pd.to_datetime('2024-12-19')
        for date in dates:
            if date >= expiry:
                continue
            try:
                spot_price = spot_prices.loc[(date, underlying)]
            except KeyError:
                continue
            days_to_expiry = (expiry - date).days
            if days_to_expiry <= 0:
                continue
            base_iv = 0.25 + np.random.normal(0, 0.05)
            base_iv = max(0.15, min(0.40, base_iv))
            for strike in strikes:
                for option_type in ['C', 'P']:
                    moneyness = spot_price / strike
                    time_to_expiry = days_to_expiry / 365.0
                    iv = base_iv * (1 + 0.1 * (moneyness - 1))
                    if option_type == 'C':
                        intrinsic = max(0, spot_price - strike)
                    else:
                        intrinsic = max(0, strike - spot_price)
                    time_value = spot_price * iv * np.sqrt(time_to_expiry) * 0.4
                    mid_price = intrinsic + time_value
                    mid_price = max(0.01, mid_price)
                    bid = mid_price * 0.98
                    ask = mid_price * 1.02
                    open_interest = int(np.random.lognormal(6, 1))
                    data.append({'date': date, 'underlying': underlying, 'expiry': expiry, 'strike': strike, 'option_type': option_type, 'bid': round(bid, 2), 'ask': round(ask, 2), 'mid': round(mid_price, 2), 'implied_vol': round(iv, 4), 'open_interest': open_interest})
        df = pd.DataFrame(data)
        return df.sort_values(['date', 'strike', 'option_type'])
    
    def load_spot_csv(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def load_futures_csv(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df['expiry'] = pd.to_datetime(df['expiry'])
        return df
    
    def load_options_csv(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df['expiry'] = pd.to_datetime(df['expiry'])
        return df
    
    def save_csv(self, df: pd.DataFrame, filename: str):
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        return filepath
    
    def load_from_api(self, tickers: list = ['AAPL', 'MSFT'], start_date: str = None, end_date: str = None, api_type: str = 'yfinance', use_fallback: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Carrega dados reais de mercado via APIs."""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        data = fetch_real_market_data(tickers=tickers, start_date=start_date, end_date=end_date, api_type=api_type, use_fallback=use_fallback)
        return data['spot'], data['futures'], data['options']

