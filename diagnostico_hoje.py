"""
Diagnóstico do dia de hoje - Verifica o que aconteceu
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.orders_repository import OrdersRepository
from src.trading_schedule import TradingSchedule

print("=" * 70)
print("DIAGNÓSTICO DO DIA DE HOJE")
print("=" * 70)
print()

repo = OrdersRepository()
schedule = TradingSchedule()
hoje = datetime.now().strftime('%Y-%m-%d')

print(f"📅 Data: {hoje}")
print()

# Verificar propostas do dia
print("1. PROPOSTAS DO DIA:")
print("-" * 70)
props = repo.get_proposals(start_date=f'{hoje} 00:00:00', end_date=f'{hoje} 23:59:59')
print(f"   Total de propostas: {len(props)}")

if not props.empty:
    if 'status' in props.columns:
        status_counts = props['status'].value_counts().to_dict()
        print(f"   Status: {status_counts}")
    
    if 'strategy' in props.columns:
        strategy_counts = props['strategy'].value_counts().to_dict()
        print(f"   Por estratégia: {strategy_counts}")
    
    print(f"   Primeiras 5 propostas:")
    for idx, row in props.head(5).iterrows():
        print(f"     - {row.get('proposal_id', 'N/A')}: {row.get('symbol', 'N/A')} ({row.get('status', 'N/A')})")
else:
    print("   ⚠️ Nenhuma proposta encontrada")

print()

# Verificar posições abertas
print("2. POSIÇÕES ABERTAS:")
print("-" * 70)
posicoes = repo.get_open_positions()
print(f"   Total de posições abertas: {len(posicoes)}")

if not posicoes.empty:
    print("   Posições:")
    for idx, row in posicoes.iterrows():
        print(f"     - {row.get('symbol', 'N/A')}: {row.get('quantity', 0)} @ R$ {row.get('avg_price', 0):.2f}")
else:
    print("   ✅ Nenhuma posição aberta")

print()

# Verificar avaliações do dia
print("3. AVALIAÇÕES DO RISK AGENT:")
print("-" * 70)
eval_df = repo.get_risk_evaluations()
if not eval_df.empty:
    eval_df['created_at'] = pd.to_datetime(eval_df['created_at'], errors='coerce')
    eval_hoje = eval_df[eval_df['created_at'].dt.date == datetime.now().date()]
    print(f"   Total de avaliações hoje: {len(eval_hoje)}")
    
    if not eval_hoje.empty:
        decision_counts = eval_hoje['decision'].value_counts().to_dict()
        print(f"   Decisões: {decision_counts}")
else:
    print("   ⚠️ Nenhuma avaliação encontrada")

print()

# Verificar execuções do dia
print("4. EXECUÇÕES DO DIA:")
print("-" * 70)
exec_df = repo.get_executions()
if not exec_df.empty:
    exec_df['created_at'] = pd.to_datetime(exec_df['created_at'], errors='coerce')
    exec_hoje = exec_df[exec_df['created_at'].dt.date == datetime.now().date()]
    print(f"   Total de execuções hoje: {len(exec_hoje)}")
else:
    print("   ⚠️ Nenhuma execução encontrada")

print()

# Verificar se fechamento EOD foi executado
print("5. FECHAMENTO EOD:")
print("-" * 70)
# Verificar se há posições fechadas hoje
if not posicoes.empty:
    print("   ⚠️ AINDA HÁ POSIÇÕES ABERTAS - Fechamento EOD pode não ter sido executado")
else:
    print("   ✅ Nenhuma posição aberta (fechamento EOD pode ter sido executado ou não havia posições)")

print()

# Verificar logs recentes
print("6. ÚLTIMAS LINHAS DO LOG:")
print("-" * 70)
try:
    with open('agentes.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print("   Últimas 10 linhas:")
        for line in lines[-10:]:
            if hoje in line or 'EOD' in line.upper() or 'FECHAMENTO' in line.upper() or '17:00' in line:
                print(f"     {line.strip()}")
except Exception as e:
    print(f"   Erro ao ler log: {e}")

print()
print("=" * 70)

