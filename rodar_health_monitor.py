#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para rodar o monitor de saúde da captura de dados.
Roda de hora em hora, verifica a captura, corrige problemas e envia relatórios.
"""

import json
import sys
import os
import logging
import signal
import time
from pathlib import Path
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('health_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from data_health_monitor import DataHealthMonitor
except ImportError:
    from src.data_health_monitor import DataHealthMonitor

# Variável global para controle
health_monitor = None

def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    global health_monitor
    logger.info("\n\nRecebido sinal de interrupção (Ctrl+C)")
    logger.info("Parando monitor de saúde...")
    logger.info("Monitor parado com sucesso")
    sys.exit(0)

def main():
    """Função principal"""
    global health_monitor
    
    # Registrar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=" * 70)
    logger.info("MONITOR DE SAÚDE DA CAPTURA DE DADOS")
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
    
    # Criar monitor
    try:
        health_monitor = DataHealthMonitor(config)
        logger.info("✅ DataHealthMonitor criado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao criar DataHealthMonitor: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("INFORMAÇÕES DO MONITOR")
    logger.info("=" * 70)
    logger.info("Horários de relatório: 12:00 e 15:00")
    logger.info("Verificação de saúde: A cada 1 hora")
    logger.info("Correção automática: Habilitada")
    logger.info("")
    logger.info("O monitor irá:")
    logger.info("  - Verificar saúde da captura a cada hora")
    logger.info("  - Corrigir problemas automaticamente quando possível")
    logger.info("  - Enviar relatórios às 12:00 e 15:00 via Telegram")
    logger.info("  - Monitorar continuamente o funcionamento")
    logger.info("")
    logger.info("Pressione Ctrl+C para parar")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")
    
    # Executar verificação inicial
    logger.info("Executando verificação inicial...")
    health_monitor.run_health_check()
    logger.info("")
    
    # Loop principal
    last_check = datetime.now()
    check_interval = timedelta(hours=1)  # Verificar a cada hora
    
    try:
        logger.info("✅ Monitor iniciado - aguardando próximas verificações...")
        logger.info("")
        
        while True:
            current_time = datetime.now()
            
            # Verificar se passou 1 hora desde última verificação
            if current_time - last_check >= check_interval:
                logger.info(f"Executando verificação de saúde ({current_time.strftime('%H:%M:%S')})...")
                health_monitor.run_health_check()
                
                # Verificar se deve enviar relatório
                current_time_str = current_time.strftime('%H:%M')
                if current_time_str in ['12:00', '15:00']:
                    logger.info(f"Enviando relatório às {current_time_str}...")
                    health_monitor.send_report(force=True)
                
                last_check = current_time
                logger.info("")
            
            # Aguardar 1 minuto antes de verificar novamente
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("\n\nInterrupção recebida pelo usuário")
    except Exception as e:
        logger.error(f"\n❌ Erro durante execução: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("\n✅ Monitor parado com sucesso")
        logger.info("=" * 70)

if __name__ == '__main__':
    main()

