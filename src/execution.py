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
    
    def __init__(self, config: Dict, logger: Optional[StructuredLogger] = None, orders_repo=None):
        self.config = config
        self.logger = logger
        self.orders_repo = orders_repo  # Repositório para salvar execuções
        self.commission_rate = config.get('commission_rate', 0.001)  # 0.1%
        self.slippage_bps = config.get('slippage_bps', 5)  # 5 bps
        self.fill_rate = config.get('fill_rate', 1.0)  # 100% fill rate para simulação
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
        # Para simulação, sempre executar (fill_rate = 1.0)
        if np.random.random() > self.fill_rate:
            return None
        
        # Calcular slippage (mínimo para simulação)
        slippage = market_price * (self.slippage_bps / 10000)
        if side == 'BUY':
            execution_price = market_price + slippage
        else:
            execution_price = market_price - slippage
        
        # Aplicar limite se for ordem limitada
        # Para simulação, sempre executar se for MARKET ou se o preço estiver dentro do limite
        if order.get('order_type') == 'LIMIT':
            if side == 'BUY':
                # Para compra LIMIT, executar se o preço de mercado está abaixo ou igual ao limite
                if execution_price > limit_price * 1.01:  # Permitir 1% de tolerância
                    return None
                # Usar o menor preço entre mercado e limite
                execution_price = min(execution_price, limit_price)
            else:  # SELL
                # Para venda LIMIT, executar se o preço de mercado está acima ou igual ao limite
                if execution_price < limit_price * 0.99:  # Permitir 1% de tolerância
                    return None
                # Usar o maior preço entre mercado e limite
                execution_price = max(execution_price, limit_price)
        # Se for MARKET, usar o preço calculado com slippage
        
        # Calcular comissão
        notional = quantity * execution_price
        commission = notional * self.commission_rate
        
        fill_timestamp = datetime.now()
        fill = {
            'fill_id': str(uuid.uuid4()),
            'order_id': order_id,
            'timestamp': fill_timestamp.isoformat(),  # Converter para string ISO
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
            # Criar dict para log sem datetime object
            log_fill = fill.copy()
            self.logger.log_execution(order_id, 'FILLED', log_fill)
        
        # Salvar execução no banco de dados
        if self.orders_repo:
            try:
                execution_dict = {
                    'order_id': fill['fill_id'],
                    'proposal_id': order.get('proposal_id', ''),
                    'timestamp': fill['timestamp'].isoformat() if hasattr(fill['timestamp'], 'isoformat') else str(fill['timestamp']),
                    'symbol': fill['symbol'],
                    'side': fill['side'],
                    'quantity': fill['quantity'],
                    'price': fill['price'],
                    'market_price': fill['market_price'],
                    'slippage': fill['slippage'],
                    'commission': fill['commission'],
                    'notional': fill['notional'],
                    'total_cost': fill['total_cost'],
                    'status': 'FILLED'
                }
                self.orders_repo.save_execution(execution_dict)
            except Exception as e:
                if self.logger:
                    self.logger.log_error(f"Erro ao salvar execução {order_id}: {e}")
        
        return fill
    
    def get_fills(self) -> pd.DataFrame:
        """Retorna todos os fills como DataFrame."""
        if not self.fills:
            return pd.DataFrame()
        return pd.DataFrame(self.fills)

