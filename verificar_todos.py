"""
Script para verificar status dos TODOs do projeto.
"""

import json
from pathlib import Path

def check_todos():
    """Verifica TODOs do projeto."""
    
    todos_planejados = [
        {
            "id": "1",
            "content": "Implementar otimização de sizing (Kelly Criterion, Risk Parity, Fixed Fraction)",
            "status": "completed"
        },
        {
            "id": "2",
            "content": "Adicionar mais estratégias de trading (momentum, mean reversion, breakout)",
            "status": "completed"
        },
        {
            "id": "3",
            "content": "Criar stubs/mock para integração com broker real (IB/CCXT)",
            "status": "completed"
        },
        {
            "id": "4",
            "content": "Implementar backtesting paralelo com squad-bmad",
            "status": "completed"
        },
        {
            "id": "5",
            "content": "Adicionar análise de risco avançada (VaR, CVaR)",
            "status": "pending"
        },
        {
            "id": "6",
            "content": "Integração com APIs reais de dados de mercado (yfinance, Brapi)",
            "status": "completed"
        },
        {
            "id": "7",
            "content": "Configurar squad-bmad ou fallback com multiprocessing",
            "status": "completed"
        }
    ]
    
    print("=" * 70)
    print("  STATUS DOS TODOS DO PROJETO")
    print("=" * 70)
    
    completed = [t for t in todos_planejados if t['status'] == 'completed']
    pending = [t for t in todos_planejados if t['status'] == 'pending']
    
    print(f"\n✅ Completados: {len(completed)}/{len(todos_planejados)}")
    print(f"⏳ Pendentes: {len(pending)}/{len(todos_planejados)}")
    
    print("\n" + "-" * 70)
    print("TODOS COMPLETADOS:")
    print("-" * 70)
    for todo in completed:
        print(f"  ✅ [{todo['id']}] {todo['content']}")
    
    if pending:
        print("\n" + "-" * 70)
        print("TODOS PENDENTES:")
        print("-" * 70)
        for todo in pending:
            print(f"  ⏳ [{todo['id']}] {todo['content']}")
    
    print("\n" + "=" * 70)
    print(f"Progresso: {len(completed)}/{len(todos_planejados)} ({len(completed)*100//len(todos_planejados)}%)")
    print("=" * 70)
    
    return todos_planejados

if __name__ == '__main__':
    check_todos()

