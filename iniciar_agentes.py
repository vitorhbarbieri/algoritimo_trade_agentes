#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script principal para iniciar os agentes de trading em modo contínuo.
Este script deve ser executado para deixar os agentes operando durante o pregão.
"""

import json
import sys
import os
import logging
import signal
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agentes.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from monitoring_service import MonitoringService
    from data_health_monitor import DataHealthMonitor
except ImportError:
    from src.monitoring_service import MonitoringService
    from src.data_health_monitor import DataHealthMonitor

# Variáveis globais para controle de parada
monitoring_service = None
health_monitor = None
health_monitor_thread = None

def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    global monitoring_service, health_monitor, health_monitor_thread
    logger.info("\n\nRecebido sinal de interrupção (Ctrl+C)")
    logger.info("Parando agentes...")
    if monitoring_service:
        monitoring_service.stop_monitoring()
    if health_monitor_thread and health_monitor_thread.is_alive():
        logger.info("Parando monitor de saúde...")
    logger.info("Agentes parados com sucesso")
    sys.exit(0)

def run_health_monitor_loop(health_monitor_instance):
    """Loop do monitor de saúde que roda em thread separada."""
    logger.info("Monitor de saúde iniciado em thread separada")
    
    last_check = datetime.now()
    check_interval = timedelta(hours=1)  # Verificar a cada hora
    
    try:
        while True:
            current_time = datetime.now()
            
            # Verificar se passou 1 hora desde última verificação
            if current_time - last_check >= check_interval:
                logger.info(f"[HEALTH] Executando verificação de saúde ({current_time.strftime('%H:%M:%S')})...")
                health_monitor_instance.run_health_check()
                
                # Verificar se deve enviar relatório (12:00 ou 15:00)
                current_time_str = current_time.strftime('%H:%M')
                if current_time_str in ['12:00', '15:00']:
                    logger.info(f"[HEALTH] Enviando relatório às {current_time_str}...")
                    health_monitor_instance.send_report(force=True)
                
                last_check = current_time
            
            # Aguardar 1 minuto antes de verificar novamente
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"[HEALTH] Erro no loop do monitor de saúde: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """Função principal"""
    global monitoring_service
    
    # Registrar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=" * 70)
    logger.info("AGENTES DE TRADING - MODO CONTÍNUO")
    logger.info("=" * 70)
    logger.info("")
    
    # Carregar configuração
    config_path = Path(__file__).parent / 'config.json'
    if not config_path.exists():
        logger.error(f"Arquivo de configuração não encontrado: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("✅ Configuração carregada")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar configuração: {e}")
        sys.exit(1)
    
    # Verificar configurações importantes
    logger.info("\n📋 Verificando configurações...")
    
    # Verificar Telegram
    telegram_config = config.get('notifications', {}).get('telegram', {})
    if telegram_config.get('enabled') and telegram_config.get('bot_token') and telegram_config.get('chat_id'):
        logger.info("✅ Telegram configurado")
    else:
        logger.warning("⚠️  Telegram não configurado - notificações não serão enviadas")
    
    # Verificar estratégias
    daytrade_config = config.get('daytrade_options', {})
    if daytrade_config.get('enabled'):
        logger.info("✅ Estratégia DayTrade Options habilitada")
    else:
        logger.warning("⚠️  Estratégia DayTrade Options desabilitada")
    
    # Verificar tickers monitorados
    monitored_tickers = config.get('monitored_tickers', [])
    if monitored_tickers:
        logger.info(f"✅ {len(monitored_tickers)} tickers configurados para monitoramento")
    else:
        logger.warning("⚠️  Nenhum ticker configurado para monitoramento")
    
    # Criar MonitoringService
    try:
        monitoring_service = MonitoringService(config)
        logger.info("✅ MonitoringService criado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao criar MonitoringService: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    # Criar DataHealthMonitor
    try:
        health_monitor = DataHealthMonitor(config)
        logger.info("✅ DataHealthMonitor criado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao criar DataHealthMonitor: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.warning("⚠️  Monitor de saúde não será iniciado, mas agentes continuarão funcionando")
        health_monitor = None
    
    # Informações sobre horário B3
    b3_time = monitoring_service.trading_schedule.get_current_b3_time()
    trading_status = monitoring_service.trading_schedule.get_trading_status()
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("INFORMAÇÕES DO MERCADO")
    logger.info("=" * 70)
    logger.info(f"Hora atual (B3): {b3_time.strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"Status do mercado: {trading_status}")
    
    if trading_status == 'CLOSED':
        next_open = monitoring_service.trading_schedule.get_next_trading_open()
        if next_open:
            logger.info(f"Próxima abertura: {next_open.strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info("")
        logger.info("⚠️  Mercado fechado - agentes aguardarão até a próxima abertura")
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("INICIANDO AGENTES")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Os agentes irão:")
    logger.info("  - Escanear o mercado a cada 5 minutos durante o pregão")
    logger.info("  - Gerar propostas de trading quando encontrarem oportunidades")
    logger.info("  - Enviar notificações Telegram para propostas aprovadas")
    logger.info("  - Respeitar horário da B3 (10:00 - 17:00)")
    logger.info("  - Enviar notificações de início e fim do pregão")
    logger.info("  - Enviar status a cada 2 horas durante o pregão")
    logger.info("")
    if health_monitor:
        logger.info("Monitor de Saúde da Captura:")
        logger.info("  - Verificará saúde da captura a cada 1 hora")
        logger.info("  - Corrigirá problemas automaticamente")
        logger.info("  - Enviará relatórios às 12:00 e 15:00 via Telegram")
    logger.info("")
    logger.info("Pressione Ctrl+C para parar os agentes")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")
    
    # Iniciar monitoramento
    try:
        # Intervalo de 5 minutos (300 segundos) entre scans
        monitoring_service.start_monitoring(interval_seconds=300)
        logger.info("✅ Agentes de trading iniciados com sucesso!")
        
        # Iniciar monitor de saúde em thread separada
        if health_monitor:
            try:
                # Executar verificação inicial
                logger.info("Executando verificação inicial do monitor de saúde...")
                health_monitor.run_health_check()
                
                # Iniciar thread do monitor de saúde
                health_monitor_thread = threading.Thread(
                    target=run_health_monitor_loop,
                    args=(health_monitor,),
                    daemon=True,
                    name="HealthMonitor"
                )
                health_monitor_thread.start()
                logger.info("✅ Monitor de saúde iniciado com sucesso!")
            except Exception as health_err:
                logger.error(f"❌ Erro ao iniciar monitor de saúde: {health_err}")
                logger.warning("⚠️  Agentes continuarão funcionando sem monitor de saúde")
        
        logger.info("")
        logger.info("Aguardando operação dos agentes...")
        logger.info("")
        
        # Loop infinito para manter o script rodando
        while True:
            time.sleep(60)  # Verificar a cada minuto se ainda está rodando
            
            # Verificar status periodicamente
            if monitoring_service.is_running:
                status = monitoring_service.get_status()
                if status.get('last_scan_time'):
                    logger.info(f"Status: Rodando | Último scan: {status['last_scan_time']}")
            
            # Verificar se thread do monitor de saúde ainda está rodando
            if health_monitor and health_monitor_thread:
                if not health_monitor_thread.is_alive():
                    logger.warning("⚠️  Thread do monitor de saúde parou - tentando reiniciar...")
                    try:
                        health_monitor_thread = threading.Thread(
                            target=run_health_monitor_loop,
                            args=(health_monitor,),
                            daemon=True,
                            name="HealthMonitor"
                        )
                        health_monitor_thread.start()
                        logger.info("✅ Monitor de saúde reiniciado")
                    except Exception as restart_err:
                        logger.error(f"❌ Erro ao reiniciar monitor de saúde: {restart_err}")
            
    except KeyboardInterrupt:
        logger.info("\n\nInterrupção recebida pelo usuário")
    except Exception as e:
        logger.error(f"\n❌ Erro durante execução: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if monitoring_service:
            monitoring_service.stop_monitoring()
        logger.info("\n✅ Agentes parados com sucesso")
        logger.info("=" * 70)

if __name__ == '__main__':
    main()

