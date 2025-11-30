#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para rodar simulador de mercado real junto com todos os agentes.
Usa dados de hoje e executa em conjunto com MonitoringService e DataHealthMonitor.
"""

import json
import sys
import time
import threading
import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulador_agentes.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from monitoring_service import MonitoringService
    from data_health_monitor import DataHealthMonitor
    from simular_dia_mercado_real import SimuladorMercadoReal
except ImportError:
    from src.monitoring_service import MonitoringService
    from src.data_health_monitor import DataHealthMonitor
    from simular_dia_mercado_real import SimuladorMercadoReal

# Variáveis globais para controle
monitoring_service = None
health_monitor = None
simulador = None
running = True

B3_TIMEZONE = pytz.timezone('America/Sao_Paulo')

def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    global running
    logger.info("\n\nRecebido sinal de interrupção (Ctrl+C)")
    logger.info("Parando todos os serviços...")
    running = False
    if monitoring_service:
        monitoring_service.stop_monitoring()
    logger.info("Serviços parados com sucesso")
    sys.exit(0)

def run_health_monitor_loop(health_monitor_instance):
    """Loop do monitor de saúde que roda em thread separada."""
    logger.info("[HEALTH] Monitor de saúde iniciado em thread separada")
    
    last_check = datetime.now()
    check_interval = timedelta(hours=1)
    
    try:
        while running:
            current_time = datetime.now()
            
            if current_time - last_check >= check_interval:
                logger.info(f"[HEALTH] Executando verificação de saúde ({current_time.strftime('%H:%M:%S')})...")
                health_monitor_instance.run_health_check()
                
                current_time_str = current_time.strftime('%H:%M')
                if current_time_str in ['12:00', '15:00']:
                    logger.info(f"[HEALTH] Enviando relatório às {current_time_str}...")
                    health_monitor_instance.send_report(force=True)
                
                last_check = current_time
            
            time.sleep(60)  # Verificar a cada minuto
            
    except Exception as e:
        logger.error(f"[HEALTH] Erro no loop do monitor de saúde: {e}")
        import traceback
        logger.error(traceback.format_exc())

def run_simulator_loop(simulator_instance):
    """Loop do simulador que roda em thread separada."""
    logger.info("[SIMULADOR] Simulador iniciado em thread separada")
    
    try:
        # Executar simulação completa
        simulator_instance.executar_simulacao()
        logger.info("[SIMULADOR] Simulação concluída")
    except Exception as e:
        logger.error(f"[SIMULADOR] Erro durante simulação: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """Função principal"""
    global monitoring_service, health_monitor, simulador, running
    
    # Registrar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=" * 70)
    logger.info("SIMULADOR + AGENTES - MODO OPERACIONAL")
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
    
    # Data de referência: HOJE
    data_referencia = datetime.now(B3_TIMEZONE)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("CONFIGURAÇÃO")
    logger.info("=" * 70)
    logger.info(f"Data de referência (simulador): {data_referencia.date()}")
    logger.info(f"Hora atual (B3): {data_referencia.strftime('%H:%M:%S')}")
    logger.info("")
    
    # Verificar configurações
    logger.info("📋 Verificando configurações...")
    
    telegram_config = config.get('notifications', {}).get('telegram', {})
    if telegram_config.get('enabled') and telegram_config.get('bot_token') and telegram_config.get('chat_id'):
        logger.info("✅ Telegram configurado")
    else:
        logger.warning("⚠️  Telegram não configurado")
    
    daytrade_config = config.get('daytrade_options', {})
    if daytrade_config.get('enabled'):
        logger.info("✅ Estratégia DayTrade Options habilitada")
    else:
        logger.warning("⚠️  Estratégia DayTrade Options desabilitada")
    
    monitored_tickers = config.get('monitored_tickers', [])
    if monitored_tickers:
        logger.info(f"✅ {len(monitored_tickers)} tickers configurados")
    else:
        logger.warning("⚠️  Nenhum ticker configurado")
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("INICIANDO SERVIÇOS")
    logger.info("=" * 70)
    logger.info("")
    
    # Criar MonitoringService (agentes principais)
    try:
        monitoring_service = MonitoringService(config)
        logger.info("✅ MonitoringService criado")
    except Exception as e:
        logger.error(f"❌ Erro ao criar MonitoringService: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    # Criar DataHealthMonitor
    try:
        health_monitor = DataHealthMonitor(config)
        logger.info("✅ DataHealthMonitor criado")
    except Exception as e:
        logger.error(f"❌ Erro ao criar DataHealthMonitor: {e}")
        logger.warning("⚠️  Monitor de saúde não será iniciado")
        health_monitor = None
    
    # Criar SimuladorMercadoReal (usando dados de hoje)
    try:
        simulador = SimuladorMercadoReal(config, data_referencia)
        logger.info("✅ SimuladorMercadoReal criado")
    except Exception as e:
        logger.error(f"❌ Erro ao criar SimuladorMercadoReal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("INICIANDO OPERAÇÃO")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Os seguintes serviços serão executados:")
    logger.info("")
    logger.info("1. MonitoringService (Agentes de Trading):")
    logger.info("   - Escaneia mercado a cada 5 minutos")
    logger.info("   - Gera propostas de trading")
    logger.info("   - Avalia propostas com RiskAgent")
    logger.info("   - Envia notificações Telegram")
    logger.info("")
    if health_monitor:
        logger.info("2. DataHealthMonitor (Monitor de Saúde):")
        logger.info("   - Verifica saúde da captura a cada 1 hora")
        logger.info("   - Envia relatórios às 12:00 e 15:00")
        logger.info("")
    logger.info("3. SimuladorMercadoReal (Simulação com Dados Reais):")
    logger.info(f"   - Simula dia usando dados REAIS de {data_referencia.date()}")
    logger.info("   - Captura dados a cada 5 minutos (simulado)")
    logger.info("   - Gera propostas baseadas em dados reais")
    logger.info("")
    logger.info("Pressione Ctrl+C para parar todos os serviços")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")
    
    # Iniciar MonitoringService em thread principal
    try:
        monitoring_service.start_monitoring(interval_seconds=300)
        logger.info("✅ MonitoringService iniciado!")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar MonitoringService: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Iniciar DataHealthMonitor em thread separada
    health_monitor_thread = None
    if health_monitor:
        try:
            health_monitor_thread = threading.Thread(
                target=run_health_monitor_loop,
                args=(health_monitor,),
                daemon=True,
                name="HealthMonitor"
            )
            health_monitor_thread.start()
            logger.info("✅ DataHealthMonitor iniciado em thread separada!")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar DataHealthMonitor: {e}")
    
    # Iniciar Simulador em thread separada
    simulator_thread = None
    try:
        simulator_thread = threading.Thread(
            target=run_simulator_loop,
            args=(simulador,),
            daemon=True,
            name="Simulator"
        )
        simulator_thread.start()
        logger.info("✅ Simulador iniciado em thread separada!")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Simulador: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("TODOS OS SERVIÇOS RODANDO")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Aguardando operação dos serviços...")
    logger.info("Verifique os logs acima para acompanhar a atividade")
    logger.info("")
    
    # Loop principal para manter tudo rodando
    try:
        while running:
            time.sleep(10)  # Verificar a cada 10 segundos
            
            # Verificar status dos serviços
            if monitoring_service and not monitoring_service.is_running:
                logger.warning("⚠️  MonitoringService parou - tentando reiniciar...")
                try:
                    monitoring_service.start_monitoring(interval_seconds=300)
                    logger.info("✅ MonitoringService reiniciado")
                except Exception as e:
                    logger.error(f"❌ Erro ao reiniciar MonitoringService: {e}")
            
            if health_monitor_thread and not health_monitor_thread.is_alive():
                logger.warning("⚠️  Thread do HealthMonitor parou - tentando reiniciar...")
                try:
                    health_monitor_thread = threading.Thread(
                        target=run_health_monitor_loop,
                        args=(health_monitor,),
                        daemon=True,
                        name="HealthMonitor"
                    )
                    health_monitor_thread.start()
                    logger.info("✅ HealthMonitor reiniciado")
                except Exception as e:
                    logger.error(f"❌ Erro ao reiniciar HealthMonitor: {e}")
            
            if simulator_thread and not simulator_thread.is_alive():
                logger.info("ℹ️  Simulador concluiu execução")
                # Não reiniciar automaticamente - simulador executa uma vez
            
    except KeyboardInterrupt:
        logger.info("\n\nInterrupção recebida pelo usuário")
    except Exception as e:
        logger.error(f"\n❌ Erro durante execução: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        running = False
        if monitoring_service:
            monitoring_service.stop_monitoring()
        logger.info("\n✅ Todos os serviços parados")
        logger.info("=" * 70)

if __name__ == '__main__':
    main()

