#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar coleta de dados e geração de propostas.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from monitoring_service import MonitoringService
    from trading_schedule import TradingSchedule
except ImportError:
    from src.monitoring_service import MonitoringService
    from src.trading_schedule import TradingSchedule

def testar_coleta():
    """Testa coleta de dados e geração de propostas."""
    print("=" * 70)
    print("🧪 TESTE DE COLETA DE DADOS E GERAÇÃO DE PROPOSTAS")
    print("=" * 70)
    
    # Carregar configuração
    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ Arquivo config.json não encontrado!")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Verificar horário B3
    schedule = TradingSchedule()
    b3_time = schedule.get_current_b3_time()
    status = schedule.get_trading_status()
    
    print(f"\n⏰ Horário B3: {b3_time.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   Status: {status}")
    print(f"   Horário de trading: {schedule.is_trading_hours()}")
    
    # Criar MonitoringService
    print("\n🔧 Inicializando MonitoringService...")
    try:
        monitoring = MonitoringService(config)
        print("   ✅ MonitoringService inicializado")
    except Exception as e:
        print(f"   ❌ Erro ao inicializar: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Testar scan
    print("\n📊 Executando scan do mercado...")
    try:
        result = monitoring.scan_market()
        
        print(f"\n✅ Scan concluído!")
        print(f"   Status: {result.get('status', 'UNKNOWN')}")
        print(f"   Oportunidades: {result.get('opportunities', 0)}")
        print(f"   Propostas: {result.get('proposals', 0)}")
        
        if result.get('proposals', 0) > 0:
            print(f"\n📋 Propostas geradas:")
            for prop in result.get('proposals_list', [])[:10]:
                print(f"   - {prop.get('strategy', 'unknown')}: {prop.get('symbol', 'N/A')}")
        else:
            print("\n⚠️  Nenhuma proposta gerada")
            print("   Possíveis causas:")
            print("   - Nenhum ticker com momentum suficiente")
            print("   - Nenhuma opção disponível")
            print("   - Filtros muito restritivos")
            print("   - Dados não coletados corretamente")
        
        # Verificar banco de dados
        print("\n💾 Verificando banco de dados...")
        if monitoring.orders_repo:
            proposals_db = monitoring.orders_repo.get_proposals()
            print(f"   Propostas no banco: {len(proposals_db)}")
            if len(proposals_db) > 0:
                print(f"   Últimas 5 propostas:")
                for _, prop in proposals_db.head(5).iterrows():
                    print(f"     - {prop.get('strategy', 'N/A')}: {prop.get('symbol', 'N/A')} - {prop.get('timestamp', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao executar scan: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    sucesso = testar_coleta()
    sys.exit(0 if sucesso else 1)

