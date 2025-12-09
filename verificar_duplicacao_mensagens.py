#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verifica se há duplicação de mensagens/agentes rodando
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orders_repository import OrdersRepository

def verificar_duplicacao():
    """Verifica se há padrões de duplicação nas mensagens."""
    print("=" * 80)
    print("VERIFICAÇÃO DE DUPLICAÇÃO DE MENSAGENS/AGENTES")
    print("=" * 80)
    
    repo = OrdersRepository()
    
    # Buscar todas as propostas
    proposals_df = repo.get_proposals()
    
    if proposals_df.empty:
        print("⚠️ Nenhuma proposta encontrada")
        return
    
    # Buscar avaliações de risco
    risk_eval_df = repo.get_risk_evaluations()
    
    # Mesclar (verificar se há coluna timestamp)
    if not risk_eval_df.empty and 'timestamp' in risk_eval_df.columns:
        merged = proposals_df.merge(
            risk_eval_df[['proposal_id', 'decision', 'reason', 'timestamp']],
            on='proposal_id',
            how='left'
        )
        merged['timestamp_eval'] = pd.to_datetime(merged['timestamp'], errors='coerce')
    else:
        merged = proposals_df.copy()
        merged['decision'] = None
        merged['reason'] = None
        merged['timestamp_eval'] = None
    
    # Agrupar por data e hora (arredondado para minutos)
    merged['created_at'] = pd.to_datetime(merged['created_at'], errors='coerce')
    merged['minute'] = merged['created_at'].dt.floor('T')
    
    # Verificar duplicatas por minuto
    print("\n📊 ANÁLISE DE DUPLICAÇÃO:")
    print("-" * 80)
    
    # Agrupar por minuto
    por_minuto = merged.groupby('minute').size()
    duplicatas = por_minuto[por_minuto > 1]
    
    if len(duplicatas) > 0:
        print(f"⚠️ Encontrados {len(duplicatas)} minutos com múltiplas propostas:")
        for minuto, count in duplicatas.head(10).items():
            print(f"  {minuto}: {count} propostas")
    else:
        print("✅ Nenhuma duplicação detectada por minuto")
    
    # Verificar padrões de ID
    print("\n🔍 ANÁLISE DE PADRÕES DE ID:")
    print("-" * 80)
    
    # Verificar se há IDs muito próximos (mesmo segundo)
    merged['timestamp_sec'] = merged['created_at'].dt.floor('S')
    por_segundo = merged.groupby('timestamp_sec').size()
    duplicatas_segundo = por_segundo[por_segundo > 1]
    
    if len(duplicatas_segundo) > 0:
        print(f"⚠️ Encontrados {len(duplicatas_segundo)} segundos com múltiplas propostas:")
        for segundo, count in duplicatas_segundo.head(10).items():
            props = merged[merged['timestamp_sec'] == segundo]
            print(f"  {segundo}: {count} propostas")
            for idx, prop in props.iterrows():
                print(f"    - {prop['proposal_id']} ({prop['strategy']})")
    else:
        print("✅ Nenhuma duplicação detectada por segundo")
    
    # Verificar estratégias
    print("\n📈 DISTRIBUIÇÃO POR ESTRATÉGIA:")
    print("-" * 80)
    estrategias = merged['strategy'].value_counts()
    for estrategia, count in estrategias.items():
        print(f"  {estrategia}: {count} propostas")
    
    # Verificar se há propostas duplicadas (mesmo símbolo, mesmo minuto)
    print("\n🔎 VERIFICAÇÃO DE PROPOSTAS DUPLICADAS:")
    print("-" * 80)
    
    merged['symbol_minute'] = merged['symbol'] + '_' + merged['minute'].astype(str)
    duplicatas_symbol = merged.groupby('symbol_minute').size()
    duplicatas_symbol = duplicatas_symbol[duplicatas_symbol > 1]
    
    if len(duplicatas_symbol) > 0:
        print(f"⚠️ Encontradas {len(duplicatas_symbol)} combinações símbolo+minuto duplicadas:")
        for combo, count in duplicatas_symbol.head(10).items():
            symbol, minute = combo.split('_', 1)
            props = merged[merged['symbol_minute'] == combo]
            print(f"  {symbol} às {minute}: {count} propostas")
            for idx, prop in props.iterrows():
                print(f"    - ID: {prop['proposal_id']}, Status: {prop.get('decision', 'N/A')}")
    else:
        print("✅ Nenhuma duplicação de símbolo+minuto detectada")
    
    # Verificar processos Python rodando
    print("\n🖥️ VERIFICAÇÃO DE PROCESSOS:")
    print("-" * 80)
    try:
        import subprocess
        result = subprocess.run(['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime'], 
                              capture_output=True, text=True)
        if result.stdout:
            print("Processos Python encontrados:")
            print(result.stdout)
        else:
            print("Nenhum processo Python encontrado")
    except:
        print("Não foi possível verificar processos")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    verificar_duplicacao()

