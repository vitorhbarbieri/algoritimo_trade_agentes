"""
Módulo de execução: simula fills com slippage e comissões.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime

try:
    from .utils import StructuredLogger
except ImportError:
    from utils import StructuredLogger


class ExecutionSimulator:
    """Simula execução de ordens com slippage e comissões."""
    
    def __init__(self, config: Dict, logger: Optional[StructuredLogger] = None):
        self.config = config
        self.logger = logger
        self.commission_rate = config.get('commission_rate', 0.001)  # 0.1%
        self.slippage_bps = config.get('slippage_bps', 5)  # 5 bps
        self.fill_rate = config.get('fill_rate', 0.95)  # 95% fill rate
        self.orders = []
        self.fills = []
    
    def execute_order(self, order: Dict, market_price: float) -> Optional[Dict]:
        """
        Executa uma ordem.
        
        Args:
            order: Dicionário com detalhes da ordem
            market_price: Preço de mercado atual
        
        Returns:
            Fill ou None se não executado
        """
        import uuid
        
        order_id = order.get('order_id', str(uuid.uuid4()))
        side = order.get('side', 'BUY')
        quantity = order.get('quantity', 0)
        limit_price = order.get('price', market_price)
        
        # Verificar se ordem será executada (fill rate)
        if np.random.random() > self.fill_rate:
            return None
        
        # Calcular slippage
        slippage = market_price * (self.slippage_bps / 10000)
        if side == 'BUY':
            execution_price = market_price + slippage
        else:
            execution_price = market_price - slippage
        
        # Aplicar limite se for ordem limitada
        if order.get('order_type') == 'LIMIT':
            if side == 'BUY' and execution_price > limit_price:
                return None
            if side == 'SELL' and execution_price < limit_price:
                return None
            execution_price = limit_price
        
        # Calcular comissão
        notional = quantity * execution_price
        commission = notional * self.commission_rate
        
        fill = {
            'fill_id': str(uuid.uuid4()),
            'order_id': order_id,
            'timestamp': datetime.now(),
            'symbol': order.get('symbol', ''),
            'side': side,
            'quantity': quantity,
            'price': execution_price,
            'market_price': market_price,
            'slippage': slippage,
            'commission': commission,
            'notional': notional,
            'total_cost': notional + commission if side == 'BUY' else notional - commission
        }
        
        self.fills.append(fill)
        
        if self.logger:
            self.logger.log_execution(order_id, 'FILLED', fill)
        
        return fill
    
    def get_fills(self) -> pd.DataFrame:
        """Retorna todos os fills como DataFrame."""
        if not self.fills:
            return pd.DataFrame()
        return pd.DataFrame(self.fills)

