"""
Monitor de Agentes - Visualiza atividade e resultados dos agentes de trading.
"""

import requests
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

BASE_URL = "http://localhost:5000"

def print_header(text):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def get_health():
    """Verifica saúde da API."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_metrics():
    """Obtém métricas do último backtest."""
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_backtest_results():
    """Obtém resultados do último backtest."""
    try:
        response = requests.get(f"{BASE_URL}/backtest/results", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_logs():
    """Lê logs dos agentes."""
    log_dir = Path("logs")
    if not log_dir.exists():
        return []
    
    logs = []
    for log_file in log_dir.glob("*.jsonl"):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except:
            continue
    
    return sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)

def show_agent_activity():
    """Mostra atividade dos agentes."""
    print_header("ATIVIDADE DOS AGENTES")
    
    logs = get_logs()
    
    if not logs:
        print("Nenhum log encontrado. Execute um backtest primeiro.")
        return
    
    # Filtrar por tipo de evento
    trader_proposals = [l for l in logs if l.get('event_type') == 'trader_proposal']
    risk_evaluations = [l for l in logs if l.get('event_type') == 'risk_evaluation']
    executions = [l for l in logs if l.get('event_type') == 'execution']
    
    print(f"\n📊 Estatísticas:")
    print(f"   Propostas do TraderAgent: {len(trader_proposals)}")
    print(f"   Avaliações do RiskAgent: {len(risk_evaluations)}")
    print(f"   Execuções: {len(executions)}")
    
    # Mostrar últimas propostas
    if trader_proposals:
        print(f"\n🔍 Últimas {min(5, len(trader_proposals))} Propostas do TraderAgent:")
        for prop in trader_proposals[:5]:
            proposal_id = prop.get('proposal_id', 'N/A')
            strategy = prop.get('strategy', 'N/A')
            timestamp = prop.get('timestamp', 'N/A')
            print(f"   [{timestamp[:19]}] {proposal_id} - Estratégia: {strategy}")
    
    # Mostrar últimas avaliações
    if risk_evaluations:
        print(f"\n🛡️ Últimas {min(5, len(risk_evaluations))} Avaliações do RiskAgent:")
        for eval in risk_evaluations[:5]:
            proposal_id = eval.get('proposal_id', 'N/A')
            decision = eval.get('decision', 'N/A')
            reason = eval.get('reason', 'N/A')
            timestamp = eval.get('timestamp', 'N/A')
            status_icon = "✅" if decision == "APPROVE" else "❌" if decision == "REJECT" else "⚠️"
            print(f"   [{timestamp[:19]}] {status_icon} {proposal_id} - {decision}: {reason}")
    
    # Mostrar últimas execuções
    if executions:
        print(f"\n💰 Últimas {min(5, len(executions))} Execuções:")
        for exec in executions[:5]:
            order_id = exec.get('order_id', 'N/A')
            status = exec.get('status', 'N/A')
            symbol = exec.get('symbol', 'N/A')
            quantity = exec.get('quantity', 0)
            price = exec.get('price', 0)
            timestamp = exec.get('timestamp', 'N/A')
            print(f"   [{timestamp[:19]}] {order_id} - {symbol} x{quantity} @ R${price:.2f} - {status}")

def show_test_results():
    """Mostra resultados dos testes."""
    print_header("RESULTADOS DOS TESTES")
    
    # Verificar saúde
    health = get_health()
    if health:
        print("✅ API está online e saudável")
        print(f"   Timestamp: {health.get('timestamp', 'N/A')}")
    else:
        print("❌ API não está respondendo")
        print("   Certifique-se de que o servidor está rodando: python run_api.py")
        return
    
    # Obter métricas
    metrics_data = get_metrics()
    if metrics_data and 'metrics' in metrics_data:
        metrics = metrics_data['metrics']
        print(f"\n📊 Métricas do Último Backtest:")
        print(f"   Retorno Total: {metrics.get('total_return', 0):.2f}%")
        print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}")
        print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"   Volatilidade: {metrics.get('volatility', 0):.2f}%")
        print(f"   Win Rate: {metrics.get('win_rate', 0):.2f}%")
        print(f"   Total de Trades: {metrics.get('total_trades', 0)}")
    else:
        print("\n⚠️ Nenhuma métrica disponível ainda.")
        print("   Execute um backtest primeiro: POST /backtest/run")
    
    # Obter resultados completos
    results = get_backtest_results()
    if results and 'results' in results:
        res = results['results']
        if 'snapshots' in res:
            print(f"\n📈 Snapshots do Portfólio: {len(res['snapshots'])}")
        if 'fills' in res:
            print(f"💼 Ordens Executadas: {len(res['fills'])}")

def show_portfolio_status():
    """Mostra status do portfólio."""
    print_header("STATUS DO PORTFÓLIO")
    
    results = get_backtest_results()
    if not results or 'results' not in results:
        print("Nenhum resultado disponível. Execute um backtest primeiro.")
        return
    
    res = results['results']
    
    if 'snapshots' in res and res['snapshots']:
        snapshots = res['snapshots']
        latest = snapshots[-1] if snapshots else {}
        
        print(f"\n💰 Último Snapshot:")
        print(f"   NAV: R$ {latest.get('nav', 0):,.2f}")
        print(f"   Cash: R$ {latest.get('cash', 0):,.2f}")
        print(f"   Valor das Posições: R$ {latest.get('position_value', 0):,.2f}")
        
        positions = latest.get('positions', {})
        if positions:
            print(f"\n📊 Posições Atuais:")
            for symbol, quantity in positions.items():
                print(f"   {symbol}: {quantity:.2f}")
        else:
            print("\n📊 Nenhuma posição aberta")
    
    if 'fills' in res and res['fills']:
        fills = res['fills']
        print(f"\n💼 Resumo de Execuções:")
        print(f"   Total de Execuções: {len(fills)}")
        
        # Agrupar por símbolo
        by_symbol = {}
        for fill in fills:
            symbol = fill.get('symbol', 'N/A')
            if symbol not in by_symbol:
                by_symbol[symbol] = {'count': 0, 'total_quantity': 0, 'total_cost': 0}
            by_symbol[symbol]['count'] += 1
            by_symbol[symbol]['total_quantity'] += fill.get('quantity', 0)
            by_symbol[symbol]['total_cost'] += fill.get('total_cost', 0)
        
        for symbol, stats in by_symbol.items():
            print(f"   {symbol}: {stats['count']} execuções, {stats['total_quantity']:.2f} unidades, R$ {stats['total_cost']:,.2f}")

def main():
    """Função principal."""
    print("\n" + "=" * 70)
    print("  MONITOR DE AGENTES DE TRADING")
    print("=" * 70)
    
    # Verificar se API está online
    health = get_health()
    if not health:
        print("\n❌ ERRO: API não está respondendo!")
        print("   Inicie o servidor: python run_api.py")
        return
    
    # Menu
    while True:
        print("\n" + "-" * 70)
        print("Menu:")
        print("  1. Ver Atividade dos Agentes")
        print("  2. Ver Resultados dos Testes")
        print("  3. Ver Status do Portfólio")
        print("  4. Ver Tudo")
        print("  0. Sair")
        print("-" * 70)
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == '1':
            show_agent_activity()
        elif choice == '2':
            show_test_results()
        elif choice == '3':
            show_portfolio_status()
        elif choice == '4':
            show_agent_activity()
            show_test_results()
            show_portfolio_status()
        elif choice == '0':
            print("\nSaindo...")
            break
        else:
            print("\nOpção inválida!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

