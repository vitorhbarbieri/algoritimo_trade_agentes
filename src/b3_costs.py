#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo de Cálculo de Custos Operacionais B3
Baseado em tarifas oficiais da B3 e práticas de mercado
"""
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class TradeCosts:
    """Custos de uma operação na B3."""
    # Custos B3
    emolumentos: float = 0.0  # 0.0025% sobre valor financeiro
    taxa_registro: float = 0.0  # 0.0095% sobre valor financeiro
    taxa_liquidacao: float = 0.0  # 0.012% se levar até vencimento
    
    # Custos Corretora
    corretagem: float = 0.0  # Varia por corretora (0 se RLP ativo)
    
    # Impostos
    ir_retido: float = 0.0  # 1% sobre lucro (retido na fonte)
    ir_a_pagar: float = 0.0  # 19% sobre lucro (a pagar)
    
    # Total
    total_custos: float = 0.0
    total_impostos: float = 0.0
    
    def __str__(self):
        return f"""
Custos Operacionais B3:
  Emolumentos: R$ {self.emolumentos:.2f}
  Taxa Registro: R$ {self.taxa_registro:.2f}
  Taxa Liquidação: R$ {self.taxa_liquidacao:.2f}
  Corretagem: R$ {self.corretagem:.2f}
  IR Retido (1%): R$ {self.ir_retido:.2f}
  IR a Pagar (19%): R$ {self.ir_a_pagar:.2f}
  TOTAL CUSTOS: R$ {self.total_custos:.2f}
  TOTAL IMPOSTOS: R$ {self.total_impostos:.2f}
"""

class B3CostCalculator:
    """Calculadora de custos operacionais B3."""
    
    # Tarifas B3 (2025)
    EMOLUMENTOS_PCT = 0.000025  # 0.0025%
    TAXA_REGISTRO_PCT = 0.000095  # 0.0095%
    TAXA_LIQUIDACAO_PCT = 0.00012  # 0.012% (apenas se levar até vencimento)
    
    # Imposto de Renda Day Trade
    IR_ALIQUOTA_TOTAL = 0.20  # 20%
    IR_RETIDO_PCT = 0.01  # 1% retido na fonte
    IR_A_PAGAR_PCT = 0.19  # 19% a pagar
    
    def __init__(
        self,
        corretagem_pct: float = 0.0,
        corretagem_fixa: float = 0.0,
        rlp_ativo: bool = True
    ):
        """
        Inicializa calculadora de custos.
        
        Args:
            corretagem_pct: Percentual de corretagem (ex: 0.001 = 0.1%)
            corretagem_fixa: Corretagem fixa por operação (ex: 0.50)
            rlp_ativo: Se True, assume corretagem zerada (RLP ativo)
        """
        self.corretagem_pct = corretagem_pct if not rlp_ativo else 0.0
        self.corretagem_fixa = corretagem_fixa if not rlp_ativo else 0.0
        self.rlp_ativo = rlp_ativo
    
    def calculate_entry_costs(
        self,
        value: float,
        instrument_type: str = 'options'
    ) -> TradeCosts:
        """
        Calcula custos de entrada de uma operação.
        
        Args:
            value: Valor financeiro da operação (quantidade * preço)
            instrument_type: Tipo de instrumento ('options', 'spot', 'futures')
        
        Returns:
            TradeCosts com custos de entrada
        """
        costs = TradeCosts()
        
        # Emolumentos B3 (0.0025%)
        costs.emolumentos = value * self.EMOLUMENTOS_PCT
        
        # Taxa de Registro B3 (0.0095%)
        costs.taxa_registro = value * self.TAXA_REGISTRO_PCT
        
        # Corretagem (percentual ou fixa)
        if self.corretagem_pct > 0:
            costs.corretagem = value * self.corretagem_pct
        elif self.corretagem_fixa > 0:
            costs.corretagem = self.corretagem_fixa
        
        # Total custos de entrada
        costs.total_custos = (
            costs.emolumentos +
            costs.taxa_registro +
            costs.corretagem
        )
        
        return costs
    
    def calculate_exit_costs(
        self,
        value: float,
        instrument_type: str = 'options',
        levar_vencimento: bool = False
    ) -> TradeCosts:
        """
        Calcula custos de saída de uma operação.
        
        Args:
            value: Valor financeiro da operação
            instrument_type: Tipo de instrumento
            levar_vencimento: Se True, aplica taxa de liquidação
        
        Returns:
            TradeCosts com custos de saída
        """
        costs = TradeCosts()
        
        # Emolumentos B3 (0.0025%)
        costs.emolumentos = value * self.EMOLUMENTOS_PCT
        
        # Taxa de Registro B3 (0.0095%)
        costs.taxa_registro = value * self.TAXA_REGISTRO_PCT
        
        # Taxa de Liquidação (se levar até vencimento)
        if levar_vencimento:
            costs.taxa_liquidacao = value * self.TAXA_LIQUIDACAO_PCT
        
        # Corretagem
        if self.corretagem_pct > 0:
            costs.corretagem = value * self.corretagem_pct
        elif self.corretagem_fixa > 0:
            costs.corretagem = self.corretagem_fixa
        
        # Total custos de saída
        costs.total_custos = (
            costs.emolumentos +
            costs.taxa_registro +
            costs.taxa_liquidacao +
            costs.corretagem
        )
        
        return costs
    
    def calculate_tax_costs(
        self,
        profit: float
    ) -> TradeCosts:
        """
        Calcula custos de impostos sobre lucro.
        
        Args:
            profit: Lucro da operação (valor positivo)
        
        Returns:
            TradeCosts com custos de impostos
        """
        if profit <= 0:
            return TradeCosts()
        
        costs = TradeCosts()
        
        # IR retido na fonte (1%)
        costs.ir_retido = profit * self.IR_RETIDO_PCT
        
        # IR a pagar (19%)
        costs.ir_a_pagar = profit * self.IR_A_PAGAR_PCT
        
        # Total impostos
        costs.total_impostos = costs.ir_retido + costs.ir_a_pagar
        
        return costs
    
    def calculate_total_costs(
        self,
        entry_value: float,
        exit_value: float,
        instrument_type: str = 'options',
        levar_vencimento: bool = False
    ) -> Dict:
        """
        Calcula custos totais de uma operação completa (entrada + saída + impostos).
        
        Args:
            entry_value: Valor financeiro da entrada
            exit_value: Valor financeiro da saída
            instrument_type: Tipo de instrumento
            levar_vencimento: Se True, aplica taxa de liquidação
        
        Returns:
            Dict com todos os custos detalhados
        """
        # Custos de entrada
        entry_costs = self.calculate_entry_costs(entry_value, instrument_type)
        
        # Custos de saída
        exit_costs = self.calculate_exit_costs(exit_value, instrument_type, levar_vencimento)
        
        # Lucro bruto
        profit_bruto = exit_value - entry_value
        
        # Custos de impostos (sobre lucro)
        tax_costs = self.calculate_tax_costs(profit_bruto)
        
        # Total de custos operacionais
        total_custos_operacionais = entry_costs.total_custos + exit_costs.total_custos
        
        # Lucro líquido
        profit_liquido = profit_bruto - total_custos_operacionais - tax_costs.total_impostos
        
        return {
            'entry_costs': entry_costs,
            'exit_costs': exit_costs,
            'tax_costs': tax_costs,
            'total_operational_costs': total_custos_operacionais,
            'total_taxes': tax_costs.total_impostos,
            'total_costs': total_custos_operacionais + tax_costs.total_impostos,
            'profit_bruto': profit_bruto,
            'profit_liquido': profit_liquido,
            'profit_pct_bruto': (profit_bruto / entry_value) * 100 if entry_value > 0 else 0,
            'profit_pct_liquido': (profit_liquido / entry_value) * 100 if entry_value > 0 else 0
        }
    
    def calculate_minimum_profit(
        self,
        entry_value: float,
        instrument_type: str = 'options'
    ) -> float:
        """
        Calcula lucro mínimo necessário para cobrir custos.
        
        Args:
            entry_value: Valor financeiro da entrada
            instrument_type: Tipo de instrumento
        
        Returns:
            Lucro mínimo necessário (em R$)
        """
        # Custos de entrada
        entry_costs = self.calculate_entry_costs(entry_value, instrument_type)
        
        # Estimativa de custos de saída (assumindo mesmo valor)
        exit_costs = self.calculate_exit_costs(entry_value, instrument_type)
        
        # Total custos operacionais
        total_custos = entry_costs.total_custos + exit_costs.total_custos
        
        # Para cobrir custos, precisamos de lucro bruto tal que:
        # profit_bruto - (profit_bruto * 0.20) >= total_custos
        # profit_bruto * 0.80 >= total_custos
        # profit_bruto >= total_custos / 0.80
        
        min_profit_bruto = total_custos / 0.80
        
        return min_profit_bruto
    
    def calculate_minimum_profit_pct(
        self,
        entry_value: float,
        instrument_type: str = 'options'
    ) -> float:
        """
        Calcula percentual mínimo de lucro necessário para cobrir custos.
        
        Args:
            entry_value: Valor financeiro da entrada
            instrument_type: Tipo de instrumento
        
        Returns:
            Percentual mínimo necessário (ex: 0.05 = 5%)
        """
        min_profit = self.calculate_minimum_profit(entry_value, instrument_type)
        return (min_profit / entry_value) if entry_value > 0 else 0

# Instância padrão (RLP ativo = corretagem zerada)
default_calculator = B3CostCalculator(rlp_ativo=True)

