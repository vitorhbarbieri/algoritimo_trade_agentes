#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificação completa do sistema antes de iniciar operação.
Verifica todos os componentes e garante que está tudo pronto.
"""

import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Configurar cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def main():
    """Verificação completa do sistema"""
    print("=" * 70)
    print("VERIFICAÇÃO COMPLETA DO SISTEMA")
    print("=" * 70)
    print()
    
    all_ok = True
    
    # 1. Verificar configuração
    print("1. VERIFICANDO CONFIGURAÇÃO...")
    try:
        config_path = Path('config.json')
        if not config_path.exists():
            print_error("Arquivo config.json não encontrado")
            all_ok = False
        else:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print_success("Configuração carregada")
            
            # Verificar tickers
            tickers = config.get('monitored_tickers', [])
            if tickers:
                print_success(f"{len(tickers)} tickers configurados")
            else:
                print_warning("Nenhum ticker configurado")
            
            # Verificar estratégias
            daytrade_enabled = config.get('daytrade_options', {}).get('enabled', False)
            if daytrade_enabled:
                print_success("Estratégia DayTrade habilitada")
            else:
                print_warning("Estratégia DayTrade desabilitada")
            
            # Verificar Telegram
            telegram_config = config.get('notifications', {}).get('telegram', {})
            if telegram_config.get('enabled') and telegram_config.get('bot_token') and telegram_config.get('chat_id'):
                print_success("Telegram configurado")
            else:
                print_warning("Telegram não configurado completamente")
    except Exception as e:
        print_error(f"Erro ao verificar configuração: {e}")
        all_ok = False
    
    print()
    
    # 2. Verificar módulos
    print("2. VERIFICANDO MÓDULOS...")
    sys.path.insert(0, str(Path(__file__).parent / 'src'))
    
    modules_to_check = [
        ('MonitoringService', 'monitoring_service'),
        ('DataHealthMonitor', 'data_health_monitor'),
        ('TraderAgent', 'agents'),
        ('RiskAgent', 'agents'),
        ('UnifiedNotifier', 'notifications'),
        ('TradingSchedule', 'trading_schedule'),
        ('OrdersRepository', 'orders_repository'),
    ]
    
    for class_name, module_name in modules_to_check:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print_success(f"{class_name} importado")
        except Exception as e:
            print_error(f"{class_name} não pode ser importado: {e}")
            all_ok = False
    
    print()
    
    # 3. Verificar banco de dados
    print("3. VERIFICANDO BANCO DE DADOS...")
    try:
        db_path = Path('agents_orders.db')
        if not db_path.exists():
            print_warning("Banco de dados não existe - será criado automaticamente")
        else:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Verificar tabelas essenciais
            required_tables = [
                'proposals',
                'risk_evaluations',
                'executions',
                'market_data_captures',
                'open_positions'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table in existing_tables:
                    print_success(f"Tabela {table} existe")
                else:
                    print_warning(f"Tabela {table} não existe - será criada automaticamente")
            
            conn.close()
            print_success("Banco de dados acessível")
    except Exception as e:
        print_error(f"Erro ao verificar banco de dados: {e}")
        all_ok = False
    
    print()
    
    # 4. Verificar Telegram
    print("4. VERIFICANDO TELEGRAM...")
    try:
        from src.notifications import UnifiedNotifier
        notifier = UnifiedNotifier(config)
        
        telegram_channel = None
        for channel_name, channel in notifier.channels:
            if channel_name == 'telegram':
                telegram_channel = channel
                break
        
        if telegram_channel:
            if telegram_channel.is_configured():
                # Testar envio
                test_result = telegram_channel.send(
                    "Teste de verificação do sistema",
                    title="Verificação",
                    priority='normal'
                )
                if test_result:
                    print_success("Telegram funcionando - mensagem de teste enviada")
                else:
                    print_warning("Telegram configurado mas falhou ao enviar")
            else:
                print_warning("Telegram não configurado")
        else:
            print_warning("Canal Telegram não encontrado")
    except Exception as e:
        print_error(f"Erro ao verificar Telegram: {e}")
        all_ok = False
    
    print()
    
    # 5. Verificar horário B3
    print("5. VERIFICANDO HORÁRIO B3...")
    try:
        from src.trading_schedule import TradingSchedule
        ts = TradingSchedule()
        b3_time = ts.get_current_b3_time()
        status = ts.get_trading_status()
        
        print_info(f"Hora atual (B3): {b3_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print_info(f"Status do mercado: {status}")
        
        if status == 'CLOSED':
            next_open = ts.get_next_trading_open()
            if next_open:
                print_info(f"Próxima abertura: {next_open.strftime('%d/%m/%Y %H:%M:%S')}")
        
        print_success("Sistema de horário B3 funcionando")
    except Exception as e:
        print_error(f"Erro ao verificar horário B3: {e}")
        all_ok = False
    
    print()
    
    # 6. Verificar API de mercado
    print("6. VERIFICANDO API DE MERCADO...")
    try:
        from src.market_data_api import create_market_data_api
        api_type = config.get('market_data_api', 'yfinance')
        market_api = create_market_data_api(api_type)
        
        # Testar com primeiro ticker
        tickers = config.get('monitored_tickers', [])
        if tickers:
            test_ticker = tickers[0]
            today = datetime.now().strftime('%Y-%m-%d')
            test_data = market_api.fetch_spot_data([test_ticker], today, today)
            
            if test_data is not None and not test_data.empty:
                print_success(f"API funcionando - dados obtidos para {test_ticker}")
            else:
                print_warning(f"API não retornou dados para {test_ticker}")
        else:
            print_warning("Nenhum ticker para testar API")
    except Exception as e:
        print_error(f"Erro ao verificar API: {e}")
        all_ok = False
    
    print()
    
    # 7. Verificar scripts principais
    print("7. VERIFICANDO SCRIPTS PRINCIPAIS...")
    scripts = [
        'iniciar_agentes.py',
        'rodar_health_monitor.py',
    ]
    
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            print_success(f"{script} existe")
        else:
            print_warning(f"{script} não encontrado")
    
    print()
    
    # Resumo final
    print("=" * 70)
    if all_ok:
        print_success("SISTEMA PRONTO PARA OPERAÇÃO!")
        print()
        print("Para iniciar os agentes:")
        print("  python iniciar_agentes.py")
        print()
        print("Os agentes irão:")
        print("  - Operar durante horário B3 (10:00 - 17:00)")
        print("  - Escanear mercado a cada 5 minutos")
        print("  - Verificar saúde a cada 1 hora")
        print("  - Enviar relatórios às 12:00 e 15:00")
    else:
        print_warning("ALGUNS PROBLEMAS DETECTADOS")
        print("Revise os erros acima antes de iniciar")
    print("=" * 70)

if __name__ == '__main__':
    main()

