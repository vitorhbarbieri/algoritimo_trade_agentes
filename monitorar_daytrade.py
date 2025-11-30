#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para monitorar a atividade do agente DayTrade em tempo real.
Mostra quando o agente está analisando dados de mercado e gerando propostas.
"""

import time
import json
from datetime import datetime
from pathlib import Path
import sys

# Adicionar src ao path
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from src.orders_repository import OrdersRepository
    from src.trading_schedule import TradingSchedule
except ImportError:
    from orders_repository import OrdersRepository
    from trading_schedule import TradingSchedule

def monitor_daytrade_activity():
    """Monitora atividade do DayTrade em tempo real."""
    print("=" * 70)
    print("MONITORAMENTO DO AGENTE DAYTRADE")
    print("=" * 70)
    print()
    
    orders_repo = OrdersRepository()
    trading_schedule = TradingSchedule()
    
    print("📊 Verificando atividade do DayTrade...")
    print()
    
    # Verificar últimas propostas de daytrade
    proposals_df = orders_repo.get_proposals(strategy='daytrade_options')
    
    if not proposals_df.empty:
        print(f"✅ Total de propostas DayTrade encontradas: {len(proposals_df)}")
        print()
        
        # Últimas 5 propostas
        print("📋 Últimas 5 Propostas:")
        print("-" * 70)
        for idx, row in proposals_df.tail(5).iterrows():
            symbol = row.get('symbol', 'N/A')
            timestamp = row.get('timestamp', 'N/A')
            side = row.get('side', 'N/A')
            quantity = row.get('quantity', 0)
            price = row.get('price', 0)
            
            print(f"  • {symbol} | {side} | Qty: {quantity} | Preço: R$ {price:.2f}")
            print(f"    Timestamp: {timestamp[:19] if timestamp else 'N/A'}")
            print()
    else:
        print("⚠️  Nenhuma proposta DayTrade encontrada ainda.")
        print()
    
    # Verificar últimas avaliações de risco para daytrade
    evaluations_df = orders_repo.get_risk_evaluations()
    if not evaluations_df.empty:
        # Filtrar avaliações de propostas daytrade
        daytrade_evaluations = []
        for idx, row in evaluations_df.iterrows():
            proposal_id = row.get('proposal_id', '')
            if 'DAYTRADE' in proposal_id.upper() or 'DAYTRADE' in str(row.get('details', '')):
                daytrade_evaluations.append(row)
        
        if daytrade_evaluations:
            print(f"✅ Total de avaliações DayTrade: {len(daytrade_evaluations)}")
            print()
            
            # Contar aprovações vs rejeições
            approved = sum(1 for e in daytrade_evaluations if e.get('decision') == 'APPROVE')
            rejected = sum(1 for e in daytrade_evaluations if e.get('decision') == 'REJECT')
            
            print(f"📊 Estatísticas de Avaliação:")
            print(f"  • Aprovadas: {approved}")
            print(f"  • Rejeitadas: {rejected}")
            print(f"  • Taxa de Aprovação: {(approved / len(daytrade_evaluations) * 100):.1f}%")
            print()
    
    # Verificar capturas de dados de mercado recentes
    captures_df = orders_repo.get_market_data_captures()
    if not captures_df.empty:
        # Filtrar capturas das últimas horas
        recent_captures = captures_df.tail(20)
        
        print(f"✅ Últimas {len(recent_captures)} capturas de dados de mercado:")
        print("-" * 70)
        
        tickers_captured = recent_captures['ticker'].unique() if 'ticker' in recent_captures.columns else []
        print(f"  • Tickers capturados: {', '.join(tickers_captured[:10])}")
        if len(tickers_captured) > 10:
            print(f"    ... e mais {len(tickers_captured) - 10} tickers")
        print()
        
        # Verificar última captura
        if 'timestamp' in recent_captures.columns:
            last_capture = recent_captures['timestamp'].iloc[-1]
            print(f"  • Última captura: {last_capture[:19] if last_capture else 'N/A'}")
            print()
    
    # Verificar status do mercado
    b3_time = trading_schedule.get_current_b3_time()
    status = trading_schedule.get_trading_status()
    
    print(f"🕐 Status do Mercado:")
    print(f"  • Horário B3: {b3_time.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"  • Status: {status}")
    print()
    
    # Verificar posições abertas
    positions_df = orders_repo.get_open_positions()
    if not positions_df.empty:
        print(f"💼 Posições Abertas: {len(positions_df)}")
        print("-" * 70)
        for idx, row in positions_df.iterrows():
            symbol = row.get('symbol', 'N/A')
            quantity = row.get('quantity', 0)
            avg_price = row.get('avg_price', 0)
            unrealized_pnl = row.get('unrealized_pnl', 0)
            
            print(f"  • {symbol} | Qty: {quantity} | Preço Médio: R$ {avg_price:.2f} | PnL: R$ {unrealized_pnl:,.2f}")
        print()
    else:
        print("💼 Nenhuma posição aberta no momento.")
        print()
    
    print("=" * 70)
    print("💡 DICA: Execute este script periodicamente para monitorar a atividade")
    print("   do DayTrade em tempo real. O agente analisa dados a cada 5 minutos.")
    print("=" * 70)

if __name__ == "__main__":
    monitor_daytrade_activity()

