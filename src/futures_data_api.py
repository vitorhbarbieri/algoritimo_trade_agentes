#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API para coletar dados de contratos futuros da B3
WIN (Mini Índice), WDO (Mini Dólar), IND (Índice), DOL (Dólar)
"""
import pandas as pd
import yfinance as yf
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Mapeamento de símbolos de futuros B3 para yfinance
FUTURES_SYMBOLS = {
    'WIN': 'WIN=F',  # Mini Índice (pode não estar disponível no yfinance)
    'WDO': 'WDO=F',  # Mini Dólar
    'IND': 'IND=F',  # Índice Futuro
    'DOL': 'DOL=F',  # Dólar Futuro
    'WSP': 'WSP=F',  # Mini S&P
    'DOLF': 'DOLF=F'  # Dólar Fracionário
}

class FuturesDataAPI:
    """API para coletar dados de futuros da B3."""
    
    def __init__(self):
        self.symbols_map = FUTURES_SYMBOLS
    
    def get_futures_data(self, symbol: str, period: str = '1d', interval: str = '1m') -> Optional[pd.DataFrame]:
        """
        Busca dados de futuro da B3.
        
        Args:
            symbol: Símbolo do futuro (WIN, WDO, IND, DOL)
            period: Período ('1d', '5d', '1mo')
            interval: Intervalo ('1m', '5m', '15m', '1h', '1d')
        
        Returns:
            DataFrame com dados do futuro ou None se não disponível
        """
        try:
            yf_symbol = self.symbols_map.get(symbol, f"{symbol}=F")
            
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"Nenhum dado encontrado para {symbol} ({yf_symbol})")
                return None
            
            return data
        except Exception as e:
            logger.error(f"Erro ao buscar dados de {symbol}: {e}")
            return None
    
    def get_current_futures_price(self, symbol: str) -> Optional[Dict]:
        """
        Busca preço atual de um futuro.
        
        Args:
            symbol: Símbolo do futuro
        
        Returns:
            Dict com dados atuais ou None
        """
        try:
            data = self.get_futures_data(symbol, period='1d', interval='1m')
            
            if data is None or data.empty:
                return None
            
            last_row = data.iloc[-1]
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'open': float(last_row.get('Open', 0)),
                'high': float(last_row.get('High', 0)),
                'low': float(last_row.get('Low', 0)),
                'close': float(last_row.get('Close', 0)),
                'last': float(last_row.get('Close', 0)),
                'volume': int(last_row.get('Volume', 0))
            }
        except Exception as e:
            logger.error(f"Erro ao buscar preço atual de {symbol}: {e}")
            return None
    
    def get_all_futures_data(self, symbols: list) -> Dict[str, Dict]:
        """
        Busca dados de múltiplos futuros.
        
        Args:
            symbols: Lista de símbolos de futuros
        
        Returns:
            Dict com dados de cada futuro
        """
        results = {}
        
        for symbol in symbols:
            data = self.get_current_futures_price(symbol)
            if data:
                results[symbol] = data
        
        return results

def create_futures_api():
    """Cria instância da API de futuros."""
    return FuturesDataAPI()

