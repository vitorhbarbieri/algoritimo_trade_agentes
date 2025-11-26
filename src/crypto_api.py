"""
API para criptoativos - Binance e outras exchanges.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logger.warning("ccxt não instalado. Execute: pip install ccxt")


class BinanceAPI:
    """API para Binance usando CCXT."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, sandbox: bool = True):
        """
        Inicializa conexão com Binance.
        
        Args:
            api_key: Chave da API (opcional para dados públicos)
            api_secret: Secret da API (opcional para dados públicos)
            sandbox: Se True, usa ambiente de teste
        """
        if not CCXT_AVAILABLE:
            raise ImportError("ccxt não instalado. Execute: pip install ccxt")
        
        self.exchange = ccxt.binance({
            'apiKey': api_key or '',
            'secret': api_secret or '',
            'sandbox': sandbox,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'  # 'spot', 'future', 'delivery', 'option'
            }
        })
        
        self.sandbox = sandbox
    
    def fetch_spot_data(self, symbols: List[str], start_date: str, end_date: str, timeframe: str = '1d') -> pd.DataFrame:
        """
        Busca dados de spot (criptomoedas).
        
        Args:
            symbols: Lista de símbolos (ex: ['BTC/USDT', 'ETH/USDT'])
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            timeframe: Timeframe ('1m', '5m', '1h', '1d', etc.)
        
        Returns:
            DataFrame com dados OHLCV
        """
        all_data = []
        
        start_ts = int(pd.to_datetime(start_date).timestamp() * 1000)
        end_ts = int(pd.to_datetime(end_date).timestamp() * 1000)
        
        for symbol in symbols:
            try:
                # Normalizar símbolo para formato Binance
                if '/' not in symbol:
                    symbol = f"{symbol}/USDT"
                
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe,
                    since=start_ts,
                    limit=1000
                )
                
                for candle in ohlcv:
                    timestamp = pd.to_datetime(candle[0], unit='ms')
                    if start_date <= timestamp.strftime('%Y-%m-%d') <= end_date:
                        all_data.append({
                            'date': timestamp,
                            'ticker': symbol.replace('/', ''),
                            'open': float(candle[1]),
                            'high': float(candle[2]),
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'volume': float(candle[5])
                        })
                
                time.sleep(0.1)  # Rate limit
                
            except Exception as e:
                logger.error(f"Erro ao buscar {symbol}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame(columns=['date', 'ticker', 'open', 'high', 'low', 'close', 'volume'])
        
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values(['date', 'ticker'])
    
    def fetch_futures_data(self, symbols: List[str], start_date: str, end_date: str, timeframe: str = '1d') -> pd.DataFrame:
        """Busca dados de futuros."""
        # Similar ao spot, mas com tipo 'future'
        self.exchange.options['defaultType'] = 'future'
        return self.fetch_spot_data(symbols, start_date, end_date, timeframe)
    
    def get_ticker_price(self, symbol: str) -> float:
        """Obtém preço atual de um ticker."""
        try:
            if '/' not in symbol:
                symbol = f"{symbol}/USDT"
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Erro ao buscar preço de {symbol}: {e}")
            return 0.0
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Obtém orderbook (spread bid-ask)."""
        try:
            if '/' not in symbol:
                symbol = f"{symbol}/USDT"
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return {
                'bids': orderbook['bids'],
                'asks': orderbook['asks'],
                'spread': orderbook['asks'][0][0] - orderbook['bids'][0][0] if orderbook['asks'] and orderbook['bids'] else 0,
                'spread_pct': ((orderbook['asks'][0][0] - orderbook['bids'][0][0]) / orderbook['bids'][0][0] * 100) if orderbook['asks'] and orderbook['bids'] else 0
            }
        except Exception as e:
            logger.error(f"Erro ao buscar orderbook de {symbol}: {e}")
            return {'bids': [], 'asks': [], 'spread': 0, 'spread_pct': 0}


def create_crypto_api(exchange: str = 'binance', **kwargs) -> BinanceAPI:
    """Factory para criar API de cripto."""
    if exchange.lower() == 'binance':
        return BinanceAPI(**kwargs)
    else:
        raise ValueError(f"Exchange não suportada: {exchange}")

