#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para rodar o polling do Telegram em background.
Processa comandos de aprovação/cancelamento de ordens.
"""

import json
import logging
import sys
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.telegram_polling import start_telegram_polling

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Inicia o polling do Telegram."""
    # Carregar configuração
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar config.json: {e}")
        return
    
    logger.info("=" * 70)
    logger.info("TELEGRAM POLLING - Sistema de Aprovação de Ordens")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Comandos disponíveis:")
    logger.info("  - /aprovar PROPOSAL_ID  ou  SIM  - Aprova uma proposta")
    logger.info("  - /cancelar PROPOSAL_ID  ou  NAO  - Cancela uma proposta")
    logger.info("  - Ou responda SIM/NAO diretamente na mensagem da proposta")
    logger.info("")
    logger.info("Iniciando polling...")
    logger.info("")
    
    # Iniciar polling
    polling = start_telegram_polling(config)
    
    if polling:
        try:
            polling.start_polling(interval=5)  # Verificar a cada 5 segundos
        except KeyboardInterrupt:
            logger.info("\nPolling interrompido pelo usuário")
    else:
        logger.error("Não foi possível iniciar o polling. Verifique a configuração do Telegram.")

if __name__ == '__main__':
    main()

