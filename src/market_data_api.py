"""
Módulo para buscar dados reais de mercado via APIs.
Suporta: yfinance, Brapi.dev.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time
import os
import logging

logger = logging.getLogger(__name__)

BRAPI_TOKEN = os.getenv("BRAPI_API_KEY", os.getenv("BRAPI_TOKEN", ""))
_last_request_time = {}

def _throttle(api_name: str = 'default', min_seconds: float = 1.0):
    """Throttle entre requisições."""
    global _last_request_time
    if api_name in _last_request_time:
        elapsed = time.time() - _last_request_time[api_name]
        if elapsed < min_seconds:
            time.sleep(min_seconds - elapsed)
    _last_request_time[api_name] = time.time()

class MarketDataAPI:
    """Classe base para APIs de dados de mercado."""
    def fetch_spot_data(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError
    def fetch_futures_data(self, contracts: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError
    def fetch_options_chain(self, underlying: str, start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError

class YahooFinanceAPI(MarketDataAPI):
    """API usando yfinance."""
    def __init__(self):
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            raise ImportError("yfinance não instalado. Execute: pip install yfinance")
    
    def _normalize_ticker(self, ticker: str) -> str:
        if '.' in ticker:
            return ticker
        return ticker
    
    def fetch_spot_data(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        _throttle('yfinance', 0.5)
        all_data = []
        for ticker in tickers:
            try:
                ticker_yf = self._normalize_ticker(ticker)
                stock = self.yf.Ticker(ticker_yf)
                hist = stock.history(start=start_date, end=end_date)
                if hist.empty:
                    continue
                hist = hist.reset_index()
                for _, row in hist.iterrows():
                    all_data.append({
                        'date': row['Date'],
                        'ticker': ticker,
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume']) if not pd.isna(row['Volume']) else 0
                    })
            except Exception as e:
                logger.error(f"Erro ao buscar {ticker}: {e}")
                continue
        if not all_data:
            return pd.DataFrame(columns=['date', 'ticker', 'open', 'high', 'low', 'close', 'volume'])
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values(['date', 'ticker'])
    
    def fetch_futures_data(self, contracts: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame(columns=['date', 'contract', 'expiry', 'open', 'high', 'low', 'close', 'volume'])
    
    def fetch_options_chain(self, underlying: str, start_date: str, end_date: str) -> pd.DataFrame:
        _throttle('yfinance', 0.5)
        try:
            ticker_yf = self._normalize_ticker(underlying)
            stock = self.yf.Ticker(ticker_yf)
            expirations = stock.options
            if not expirations:
                return pd.DataFrame(columns=['date', 'underlying', 'expiry', 'strike', 'option_type', 'bid', 'ask', 'mid', 'implied_vol', 'open_interest'])
            all_data = []
            for expiry_str in expirations[:5]:
                try:
                    opt_chain = stock.option_chain(expiry_str)
                    if not opt_chain.calls.empty:
                        for _, row in opt_chain.calls.iterrows():
                            all_data.append({
                                'date': datetime.now().date(),
                                'underlying': underlying,
                                'expiry': pd.to_datetime(expiry_str),
                                'strike': float(row['strike']),
                                'option_type': 'C',
                                'bid': float(row['bid']) if not pd.isna(row['bid']) else 0.0,
                                'ask': float(row['ask']) if not pd.isna(row['ask']) else 0.0,
                                'mid': (float(row['bid']) + float(row['ask'])) / 2 if not pd.isna(row['bid']) and not pd.isna(row['ask']) else 0.0,
                                'implied_vol': float(row['impliedVolatility']) if 'impliedVolatility' in row and not pd.isna(row['impliedVolatility']) else 0.25,
                                'open_interest': int(row['openInterest']) if 'openInterest' in row and not pd.isna(row['openInterest']) else 0
                            })
                    if not opt_chain.puts.empty:
                        for _, row in opt_chain.puts.iterrows():
                            all_data.append({
                                'date': datetime.now().date(),
                                'underlying': underlying,
                                'expiry': pd.to_datetime(expiry_str),
                                'strike': float(row['strike']),
                                'option_type': 'P',
                                'bid': float(row['bid']) if not pd.isna(row['bid']) else 0.0,
                                'ask': float(row['ask']) if not pd.isna(row['ask']) else 0.0,
                                'mid': (float(row['bid']) + float(row['ask'])) / 2 if not pd.isna(row['bid']) and not pd.isna(row['ask']) else 0.0,
                                'implied_vol': float(row['impliedVolatility']) if 'impliedVolatility' in row and not pd.isna(row['impliedVolatility']) else 0.25,
                                'open_interest': int(row['openInterest']) if 'openInterest' in row and not pd.isna(row['openInterest']) else 0
                            })
                except:
                    continue
            if not all_data:
                return pd.DataFrame(columns=['date', 'underlying', 'expiry', 'strike', 'option_type', 'bid', 'ask', 'mid', 'implied_vol', 'open_interest'])
            df = pd.DataFrame(all_data)
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values(['date', 'expiry', 'strike', 'option_type'])
        except Exception as e:
            logger.error(f"Erro ao buscar opções: {e}")
            return pd.DataFrame(columns=['date', 'underlying', 'expiry', 'strike', 'option_type', 'bid', 'ask', 'mid', 'implied_vol', 'open_interest'])

class BrapiAPI(MarketDataAPI):
    """API usando Brapi.dev."""
    def __init__(self, api_key: Optional[str] = None):
        import requests
        self.requests = requests
        self.api_key = api_key or BRAPI_TOKEN
        self.base_url = "https://brapi.dev/api"
    
    def _normalize_ticker(self, ticker: str) -> str:
        return ticker.replace('.SA', '').upper()
    
    def fetch_spot_data(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        _throttle('brapi', 1.0)
        all_data = []
        for ticker in tickers:
            try:
                ticker_norm = self._normalize_ticker(ticker)
                url = f"{self.base_url}/quote/{ticker_norm}"
                params = {'range': '1y', 'interval': '1d'}
                if self.api_key:
                    params['token'] = self.api_key
                response = self.requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        result = data['results'][0]
                        if 'historicalDataPrice' in result:
                            for item in result['historicalDataPrice']:
                                date = pd.to_datetime(item['date'], unit='ms')
                                if start_date <= date.strftime('%Y-%m-%d') <= end_date:
                                    all_data.append({
                                        'date': date,
                                        'ticker': ticker,
                                        'open': float(item.get('open', 0)),
                                        'high': float(item.get('high', 0)),
                                        'low': float(item.get('low', 0)),
                                        'close': float(item.get('close', 0)),
                                        'volume': int(item.get('volume', 0))
                                    })
            except Exception as e:
                logger.error(f"Erro ao buscar {ticker}: {e}")
                continue
        if not all_data:
            return pd.DataFrame(columns=['date', 'ticker', 'open', 'high', 'low', 'close', 'volume'])
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values(['date', 'ticker'])
    
    def fetch_futures_data(self, contracts: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame(columns=['date', 'contract', 'expiry', 'open', 'high', 'low', 'close', 'volume'])
    
    def fetch_options_chain(self, underlying: str, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame(columns=['date', 'underlying', 'expiry', 'strike', 'option_type', 'bid', 'ask', 'mid', 'implied_vol', 'open_interest'])

def create_market_data_api(api_type: str = 'yfinance', **kwargs) -> MarketDataAPI:
    """Factory function para criar API."""
    api_type = api_type.lower()
    if api_type == 'yfinance':
        return YahooFinanceAPI()
    elif api_type == 'brapi':
        return BrapiAPI(api_key=kwargs.get('api_key'))
    else:
        raise ValueError(f"Tipo de API desconhecido: {api_type}")

def fetch_real_market_data(tickers: List[str] = None, start_date: str = None, end_date: str = None, api_type: str = 'yfinance', use_fallback: bool = True) -> Dict[str, pd.DataFrame]:
    """Busca dados reais de mercado com fallback."""
    if tickers is None:
        tickers = ['AAPL', 'MSFT']
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    results = {'spot': pd.DataFrame(), 'futures': pd.DataFrame(), 'options': pd.DataFrame()}
    
    try:
        api = create_market_data_api(api_type)
        results['spot'] = api.fetch_spot_data(tickers, start_date, end_date)
        results['futures'] = api.fetch_futures_data([], start_date, end_date)
        if tickers:
            results['options'] = api.fetch_options_chain(tickers[0], start_date, end_date)
    except Exception as e:
        logger.error(f"Erro com API {api_type}: {e}")
        if use_fallback and api_type != 'yfinance':
            try:
                api_fallback = YahooFinanceAPI()
                results['spot'] = api_fallback.fetch_spot_data(tickers, start_date, end_date)
                results['options'] = api_fallback.fetch_options_chain(tickers[0], start_date, end_date)
            except:
                pass
    
    return results

