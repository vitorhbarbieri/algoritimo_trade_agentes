#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar se o RiskAgent está salvando avaliações corretamente.
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orders_repository import OrdersRepository
from src.agents import OrderProposal, RiskAgent, PortfolioManager
from src.utils import StructuredLogger

def testar_risk_agent():
    """Testa se RiskAgent salva avaliações corretamente."""
    print("=" * 80)
    print("TESTE DO RISK AGENT")
    print("=" * 80)
    
    # Carregar configuração
    config_path = Path('config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Criar componentes
    repo = OrdersRepository()
    portfolio = PortfolioManager(config.get('nav', 1000000))
    logger = StructuredLogger(log_dir='logs')
    risk_agent = RiskAgent(portfolio, config, logger, orders_repo=repo)
    
    # Criar proposta de teste
    proposal = OrderProposal(
        proposal_id='TEST-001',
        strategy='daytrade_options',
        instrument_type='options',
        symbol='PETR4_25.5_C_20251215',
        side='BUY',
        quantity=10,
        price=1.5,
        order_type='LIMIT',
        metadata={
            'underlying': 'PETR4',
            'strike': 25.5,
            'delta': 0.5,
            'take_profit_pct': 0.008,
            'stop_loss_pct': 0.30,
            'gain_value': 8.0,
            'loss_value': 30.0,
            'spread_pct': 0.05
        }
    )
    
    # Market data de teste
    market_data = {
        'spot': {
            'PETR4': {'close': 25.0, 'open': 24.8, 'high': 25.2, 'low': 24.7}
        },
        'options': {}
    }
    
    print("\n1. Avaliando proposta de teste...")
    decision, modified_proposal, reason = risk_agent.evaluate_proposal(proposal, market_data)
    
    print(f"   Decisão: {decision}")
    print(f"   Razão: {reason}")
    
    # Verificar se foi salva
    print("\n2. Verificando se avaliação foi salva...")
    evals = repo.get_risk_evaluations()
    test_eval = evals[evals['proposal_id'] == 'TEST-001']
    
    if not test_eval.empty:
        print(f"   ✅ Avaliação salva com sucesso!")
        print(f"   ID: {test_eval.iloc[0]['id']}")
        print(f"   Decisão: {test_eval.iloc[0]['decision']}")
        print(f"   Razão: {test_eval.iloc[0]['reason']}")
    else:
        print("   ❌ Avaliação NÃO foi salva!")
    
    # Verificar total de avaliações
    print(f"\n3. Total de avaliações no banco: {len(evals)}")
    if not evals.empty:
        print(f"   Decisões: {evals['decision'].value_counts().to_dict()}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    testar_risk_agent()

