"""
Script de verificação final do sistema antes de amanhã
"""
import json
import sys
from pathlib import Path

def verificar_config():
    """Verifica configurações básicas."""
    print("=" * 70)
    print("VERIFICAÇÃO FINAL DO SISTEMA")
    print("=" * 70)
    print()
    
    # Carregar config
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ Config.json carregado")
    except Exception as e:
        print(f"❌ Erro ao carregar config.json: {e}")
        return False
    
    # Verificar Telegram
    telegram_enabled = config.get('notifications', {}).get('telegram', {}).get('enabled', False)
    telegram_token = config.get('notifications', {}).get('telegram', {}).get('bot_token', '')
    telegram_chat = config.get('notifications', {}).get('telegram', {}).get('chat_id', '')
    
    print(f"\n📱 TELEGRAM:")
    print(f"   Habilitado: {'✅' if telegram_enabled else '❌'}")
    print(f"   Bot Token: {'✅ Configurado' if telegram_token else '❌ Não configurado'}")
    print(f"   Chat ID: {'✅ Configurado' if telegram_chat else '❌ Não configurado'}")
    
    # Verificar Daytrade
    daytrade_config = config.get('daytrade_options', {})
    daytrade_enabled = daytrade_config.get('enabled', False)
    min_score = daytrade_config.get('min_comparison_score', 0)
    
    print(f"\n📊 DAYTRADE:")
    print(f"   Habilitado: {'✅' if daytrade_enabled else '❌'}")
    print(f"   Score mínimo: {min_score}")
    print(f"   Take Profit: {daytrade_config.get('take_profit_pct', 0) * 100:.1f}%")
    print(f"   Stop Loss: {daytrade_config.get('stop_loss_pct', 0) * 100:.1f}%")
    
    # Verificar Futuros
    futures_config = config.get('futures_daytrade', {})
    futures_enabled = futures_config.get('enabled', False)
    
    print(f"\n📈 FUTUROS:")
    print(f"   Habilitado: {'✅' if futures_enabled else '❌'}")
    
    # Verificar Ativos Monitorados
    tickers = config.get('monitored_tickers', [])
    tickers_br = [t for t in tickers if '.SA' in str(t)]
    futures = config.get('monitored_futures', [])
    
    print(f"\n📋 ATIVOS MONITORADOS:")
    print(f"   Total de ativos: {len(tickers)}")
    print(f"   Ativos brasileiros: {len(tickers_br)}")
    print(f"   Futuros: {len(futures)}")
    
    # Verificar módulos
    print(f"\n🔧 MÓDULOS:")
    try:
        from src.monitoring_service import MonitoringService
        print("   ✅ MonitoringService")
    except Exception as e:
        print(f"   ❌ MonitoringService: {e}")
    
    try:
        from src.agents import TraderAgent, RiskAgent
        print("   ✅ Agents (TraderAgent, RiskAgent)")
    except Exception as e:
        print(f"   ❌ Agents: {e}")
    
    try:
        from src.comparison_engine import ComparisonEngine
        print("   ✅ ComparisonEngine")
    except Exception as e:
        print(f"   ❌ ComparisonEngine: {e}")
    
    try:
        from src.futures_strategy import FuturesDayTradeStrategy
        print("   ✅ FuturesStrategy")
    except Exception as e:
        print(f"   ❌ FuturesStrategy: {e}")
    
    try:
        from src.futures_data_api import FuturesDataAPI
        print("   ✅ FuturesDataAPI")
    except Exception as e:
        print(f"   ❌ FuturesDataAPI: {e}")
    
    try:
        from src.notifications import UnifiedNotifier
        print("   ✅ Notifications")
    except Exception as e:
        print(f"   ❌ Notifications: {e}")
    
    try:
        from src.orders_repository import OrdersRepository
        repo = OrdersRepository()
        print("   ✅ OrdersRepository")
        print(f"      Banco de dados: {repo.db_path}")
    except Exception as e:
        print(f"   ❌ OrdersRepository: {e}")
    
    # Verificar scripts de inicialização
    print(f"\n🚀 SCRIPTS:")
    scripts = [
        'iniciar_agentes.py',
        'iniciar_agentes_auto.bat',
        'configurar_tarefa_simples.ps1'
    ]
    
    for script in scripts:
        if Path(script).exists():
            print(f"   ✅ {script}")
        else:
            print(f"   ⚠️  {script} (não encontrado)")
    
    # Resumo
    print(f"\n" + "=" * 70)
    print("RESUMO:")
    print("=" * 70)
    
    tudo_ok = (
        telegram_enabled and telegram_token and telegram_chat and
        daytrade_enabled and
        len(tickers_br) > 0
    )
    
    if tudo_ok:
        print("✅ SISTEMA PRONTO PARA OPERAÇÃO")
    else:
        print("⚠️  ALGUMAS CONFIGURAÇÕES PRECISAM SER VERIFICADAS")
    
    print()
    return tudo_ok

if __name__ == '__main__':
    sucesso = verificar_config()
    sys.exit(0 if sucesso else 1)

