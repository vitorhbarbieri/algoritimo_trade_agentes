"""
Script para reiniciar o sistema completo
Verifica processos, para tudo, e reinicia com código atualizado
"""
import sys
import os
import subprocess
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("REINICIALIZAÇÃO COMPLETA DO SISTEMA")
print("=" * 70)
print()

# 1. Verificar processos Python rodando
print("1. VERIFICANDO PROCESSOS PYTHON:")
print("-" * 70)
try:
    result = subprocess.run(
        ['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Path'],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.stdout.strip():
        print("   Processos encontrados:")
        print(result.stdout)
    else:
        print("   ✅ Nenhum processo Python encontrado")
except Exception as e:
    print(f"   ⚠️ Erro ao verificar processos: {e}")

print()

# 2. Parar processos
print("2. PARANDO PROCESSOS:")
print("-" * 70)
try:
    subprocess.run(
        ['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force'],
        timeout=10
    )
    print("   ✅ Comando de parada executado")
    time.sleep(2)
except Exception as e:
    print(f"   ⚠️ Erro ao parar processos: {e}")

print()

# 3. Verificar novamente
print("3. VERIFICAÇÃO FINAL:")
print("-" * 70)
try:
    result = subprocess.run(
        ['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue'],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.stdout.strip():
        print("   ⚠️ Ainda há processos rodando:")
        print(result.stdout)
    else:
        print("   ✅ Nenhum processo Python rodando")
except Exception as e:
    print(f"   ⚠️ Erro na verificação: {e}")

print()

# 4. Verificar configurações
print("4. VERIFICANDO CONFIGURAÇÕES:")
print("-" * 70)
try:
    import json
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print(f"   ✅ Config carregado")
    print(f"   Telegram: {'✅ Habilitado' if config.get('notifications', {}).get('telegram', {}).get('enabled') else '❌ Desabilitado'}")
    print(f"   Daytrade: {'✅ Habilitado' if config.get('daytrade_options', {}).get('enabled') else '❌ Desabilitado'}")
    print(f"   Futuros: {'✅ Habilitado' if config.get('futures_daytrade', {}).get('enabled') else '❌ Desabilitado'}")
    print(f"   Vol Arb: {'❌ Habilitado' if config.get('enable_vol_arb') else '✅ Desabilitado'}")
    print(f"   Pairs: {'❌ Habilitado' if config.get('enable_pairs') else '✅ Desabilitado'}")
    
    tickers = config.get('monitored_tickers', [])
    tickers_br = [t for t in tickers if '.SA' in str(t)]
    print(f"   Ativos brasileiros: {len(tickers_br)}/{len(tickers)}")
    
except Exception as e:
    print(f"   ❌ Erro ao verificar config: {e}")

print()

# 5. Verificar módulos
print("5. VERIFICANDO MÓDULOS:")
print("-" * 70)
modules = [
    'src.monitoring_service',
    'src.agents',
    'src.eod_analysis',
    'src.futures_strategy',
    'src.futures_data_api',
    'src.comparison_engine'
]

for module_name in modules:
    try:
        __import__(module_name)
        print(f"   ✅ {module_name}")
    except Exception as e:
        print(f"   ❌ {module_name}: {e}")

print()

# 6. Verificar banco de dados
print("6. VERIFICANDO BANCO DE DADOS:")
print("-" * 70)
try:
    from src.orders_repository import OrdersRepository
    repo = OrdersRepository()
    print(f"   ✅ OrdersRepository criado")
    
    # Verificar colunas
    import sqlite3
    conn = sqlite3.connect('agents_orders.db')
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(open_positions)')
    cols = [row[1] for row in cursor.fetchall()]
    conn.close()
    
    if 'close_price' in cols and 'realized_pnl' in cols:
        print(f"   ✅ Colunas close_price e realized_pnl existem")
    else:
        print(f"   ⚠️ Colunas podem estar faltando")
        
except Exception as e:
    print(f"   ⚠️ Erro ao verificar banco: {e}")

print()

print("=" * 70)
print("✅ VERIFICAÇÃO COMPLETA")
print("=" * 70)
print()
print("Sistema pronto para reiniciar!")
print()
print("Para iniciar os agentes, execute:")
print("  python iniciar_agentes.py")
print()
print("Ou use o script batch:")
print("  iniciar_agentes_auto.bat")
print()

