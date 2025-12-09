#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Estratégia de Daytrade para Contratos Futuros B3
WIN (Mini Índice), WDO (Mini Dólar), etc.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from .agents import OrderProposal
except ImportError:
    from agents import OrderProposal

@dataclass
class FuturesProposal:
    """Proposta de operação em futuro."""
    proposal_id: str
    symbol: str  # WIN, WDO, etc
    side: str  # BUY, SELL
    quantity: int  # Número de contratos
    price: float
    take_profit: float
    stop_loss: float
    metadata: Dict

class FuturesDayTradeStrategy:
    """Estratégia de daytrade para futuros B3."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.futures_config = config.get('futures_daytrade', {
            'enabled': True,
            'min_intraday_move': 0.003,  # 0.3% mínimo de movimento
            'take_profit_pct': 0.01,  # 1%
            'stop_loss_pct': 0.01,  # 1% (futuros são mais voláteis)
            'min_volume': 1000,  # Volume mínimo
            'max_contracts': 10  # Máximo de contratos por operação
        })
    
    def generate_proposals(self, timestamp: pd.Timestamp, futures_data: Dict) -> List[OrderProposal]:
        """
        Gera propostas de daytrade para futuros.
        
        Args:
            timestamp: Timestamp atual
            futures_data: Dict com dados de futuros {symbol: data}
        
        Returns:
            Lista de propostas de futuros
        """
        proposals = []
        
        if not self.futures_config.get('enabled', True):
            return proposals
        
        cfg = self.futures_config
        
        for symbol, data in futures_data.items():
            try:
                # Calcular movimento intraday
                open_price = data.get('open', 0)
                current_price = data.get('last', data.get('close', 0))
                volume = data.get('volume', 0)
                
                if open_price == 0 or current_price == 0:
                    continue
                
                # Movimento percentual
                intraday_move = (current_price / open_price) - 1
                min_move = cfg.get('min_intraday_move', 0.003)
                
                # Verificar volume mínimo
                if volume < cfg.get('min_volume', 1000):
                    continue
                
                # Verificar movimento mínimo
                if abs(intraday_move) < min_move:
                    continue
                
                # Determinar direção (BUY se subindo, SELL se descendo)
                side = 'BUY' if intraday_move > 0 else 'SELL'
                
                # Calcular TP e SL
                take_profit_pct = cfg.get('take_profit_pct', 0.01)
                stop_loss_pct = cfg.get('stop_loss_pct', 0.01)
                
                if side == 'BUY':
                    take_profit_price = current_price * (1 + take_profit_pct)
                    stop_loss_price = current_price * (1 - stop_loss_pct)
                else:
                    take_profit_price = current_price * (1 - take_profit_pct)
                    stop_loss_price = current_price * (1 + stop_loss_pct)
                
                # Quantidade de contratos (padronizado)
                # Futuros têm valores diferentes por ponto
                # WIN: 1 ponto = R$ 0,20 | WDO: 1 ponto = R$ 10,00
                contracts_per_ticket = self._calculate_contracts(symbol, current_price)
                quantity = min(contracts_per_ticket, cfg.get('max_contracts', 10))
                
                if quantity <= 0:
                    continue
                
                # Criar proposta
                # ID simplificado: apenas últimos 4 dígitos do timestamp
                timestamp_short = str(int(timestamp.timestamp()))[-4:]
                proposal_id = timestamp_short
                
                proposal = OrderProposal(
                    proposal_id=proposal_id,
                    strategy='futures_daytrade',
                    instrument_type='futures',
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=current_price,
                    order_type='LIMIT',
                    metadata={
                        'underlying': symbol,
                        'intraday_move': float(intraday_move),
                        'volume': volume,
                        'take_profit_price': float(take_profit_price),
                        'stop_loss_price': float(stop_loss_price),
                        'take_profit_pct': take_profit_pct,
                        'stop_loss_pct': stop_loss_pct,
                        'point_value': self._get_point_value(symbol),
                        'eod_close': True
                    }
                )
                
                proposals.append(proposal)
                
            except Exception as e:
                import logging
                logging.error(f"Erro ao gerar proposta de futuro para {symbol}: {e}")
                continue
        
        return proposals
    
    def _calculate_contracts(self, symbol: str, price: float) -> int:
        """
        Calcula quantidade de contratos para ticket padrão de R$ 1.000.
        
        Args:
            symbol: Símbolo do futuro
            price: Preço atual
        
        Returns:
            Número de contratos
        """
        STANDARD_TICKET = 1000.0
        
        # Valor por ponto de cada futuro
        point_value = self._get_point_value(symbol)
        
        # Margem aproximada (simplificado)
        # WIN: ~R$ 100 por contrato | WDO: ~R$ 500 por contrato
        margin_per_contract = self._get_margin(symbol)
        
        if margin_per_contract == 0:
            return 1
        
        # Calcular quantos contratos cabem no ticket padrão
        contracts = int(STANDARD_TICKET / margin_per_contract)
        
        return max(1, min(contracts, 10))  # Entre 1 e 10 contratos
    
    def _get_point_value(self, symbol: str) -> float:
        """Retorna valor por ponto do futuro."""
        point_values = {
            'WIN': 0.20,  # R$ 0,20 por ponto
            'WDO': 10.00,  # R$ 10,00 por ponto
            'IND': 1.00,  # R$ 1,00 por ponto (estimado)
            'DOL': 50.00,  # R$ 50,00 por ponto (estimado)
            'WSP': 0.50,  # Estimado
            'DOLF': 5.00  # Estimado
        }
        return point_values.get(symbol, 1.00)
    
    def _get_margin(self, symbol: str) -> float:
        """Retorna margem aproximada por contrato."""
        margins = {
            'WIN': 100.0,  # ~R$ 100 por contrato
            'WDO': 500.0,  # ~R$ 500 por contrato
            'IND': 1000.0,  # Estimado
            'DOL': 5000.0,  # Estimado
            'WSP': 200.0,  # Estimado
            'DOLF': 500.0  # Estimado
        }
        return margins.get(symbol, 1000.0)

