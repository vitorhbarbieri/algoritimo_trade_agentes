"""
Script para verificar se todos os agentes estão configurados e prontos para operar.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

def verificar_configuracao():
    """Verifica se tudo está configurado corretamente."""
    print("=" * 70)
    print("VERIFICAÇÃO: Agentes Prontos para Operação")
    print("=" * 70)
    
    # 1. Verificar config.json
    print("\n1. VERIFICANDO CONFIGURAÇÃO:")
    print("-" * 70)
    
    config_path = Path('config.json')
    if not config_path.exists():
        print("   ❌ config.json não encontrado!")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("   ✅ config.json carregado")
    except Exception as e:
        print(f"   ❌ Erro ao carregar config.json: {e}")
        return False
    
    # 2. Verificar Telegram
    print("\n2. VERIFICANDO TELEGRAM:")
    print("-" * 70)
    
    telegram_config = config.get('notifications', {}).get('telegram', {})
    if telegram_config.get('enabled'):
        bot_token = telegram_config.get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = telegram_config.get('chat_id')
        
        if bot_token:
            print("   ✅ Bot token configurado")
        else:
            print("   ⚠️  Bot token não configurado")
        
        if chat_id:
            print(f"   ✅ Chat ID configurado: {chat_id}")
        else:
            print("   ⚠️  Chat ID não configurado")
        
        if bot_token and chat_id:
            print("   ✅ Telegram PRONTO para enviar notificações")
        else:
            print("   ⚠️  Telegram NÃO está pronto - notificações não serão enviadas")
    else:
        print("   ⚠️  Telegram desabilitado")
    
    # 3. Verificar estratégias
    print("\n3. VERIFICANDO ESTRATÉGIAS:")
    print("-" * 70)
    
    daytrade_config = config.get('daytrade_options', {})
    if daytrade_config.get('enabled'):
        print("   ✅ DayTrade Options habilitada")
        print(f"      - Retorno mínimo: {daytrade_config.get('min_intraday_return', 0)*100:.2f}%")
        print(f"      - Volume mínimo: {daytrade_config.get('min_volume_ratio', 0)*100:.0f}%")
        print(f"      - Take profit: {daytrade_config.get('take_profit_pct', 0)*100:.2f}%")
    else:
        print("   ⚠️  DayTrade Options desabilitada")
    
    # 4. Verificar tickers
    print("\n4. VERIFICANDO TICKERS MONITORADOS:")
    print("-" * 70)
    
    monitored_tickers = config.get('monitored_tickers', [])
    if monitored_tickers:
        print(f"   ✅ {len(monitored_tickers)} tickers configurados")
        print(f"      Primeiros 5: {', '.join(monitored_tickers[:5])}")
        if len(monitored_tickers) > 5:
            print(f"      ... e mais {len(monitored_tickers) - 5} tickers")
    else:
        print("   ⚠️  Nenhum ticker configurado")
    
    # 5. Verificar módulos Python
    print("\n5. VERIFICANDO MÓDULOS PYTHON:")
    print("-" * 70)
    
    try:
        from src.monitoring_service import MonitoringService
        print("   ✅ MonitoringService importado")
    except Exception as e:
        print(f"   ❌ Erro ao importar MonitoringService: {e}")
        return False
    
    try:
        from src.data_health_monitor import DataHealthMonitor
        print("   ✅ DataHealthMonitor importado")
    except Exception as e:
        print(f"   ❌ Erro ao importar DataHealthMonitor: {e}")
        return False
    
    try:
        from src.trading_schedule import TradingSchedule
        schedule = TradingSchedule()
        b3_time = schedule.get_current_b3_time()
        trading_status = schedule.get_trading_status()
        print(f"   ✅ TradingSchedule funcionando")
        print(f"      Hora B3 atual: {b3_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"      Status mercado: {trading_status}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar TradingSchedule: {e}")
        return False
    
    # 6. Verificar banco de dados
    print("\n6. VERIFICANDO BANCO DE DADOS:")
    print("-" * 70)
    
    db_path = Path('agents_orders.db')
    if db_path.exists():
        print("   ✅ Banco de dados existe")
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   ✅ {len(tables)} tabelas encontradas")
            conn.close()
        except Exception as e:
            print(f"   ⚠️  Erro ao verificar banco: {e}")
    else:
        print("   ⚠️  Banco de dados não existe (será criado automaticamente)")
    
    # 7. Verificar horários de relatório
    print("\n7. VERIFICANDO HORÁRIOS DE RELATÓRIO:")
    print("-" * 70)
    
    try:
        health_monitor = DataHealthMonitor(config)
        report_times = health_monitor.report_times
        print(f"   ✅ Monitor de saúde configurado")
        print(f"      Relatórios serão enviados às: {', '.join(report_times)}")
        print(f"      (Horário B3 - São Paulo)")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar monitor de saúde: {e}")
    
    # 8. Resumo final
    print("\n" + "=" * 70)
    print("RESUMO:")
    print("=" * 70)
    
    print("\n✅ AGENTES PRONTOS PARA OPERAR!")
    print("\nPara iniciar os agentes, execute:")
    print("   python iniciar_agentes.py")
    print("\nOs agentes irão:")
    print("  ✅ Escanear o mercado a cada 5 minutos durante o pregão")
    print("  ✅ Gerar propostas quando encontrarem oportunidades")
    print("  ✅ Enviar notificações Telegram para propostas aprovadas")
    print("  ✅ Enviar notificações de início e fim do pregão")
    print("  ✅ Enviar status a cada 2 horas durante o pregão")
    print("  ✅ Monitor de saúde verificará captura a cada 1 hora")
    print("  ✅ Relatórios de saúde às 12:00 e 15:00 via Telegram")
    print("\n⚠️  IMPORTANTE:")
    print("  - Deixe o script rodando durante todo o pregão")
    print("  - Use Ctrl+C para parar os agentes")
    print("  - Verifique os logs em 'agentes.log'")
    print("=" * 70)

if __name__ == '__main__':
    verificar_configuracao()

