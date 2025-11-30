"""
Script para diagnosticar por que o agente DayTrade não está gerando propostas.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.orders_repository import OrdersRepository
from src.trading_schedule import TradingSchedule
import json
from datetime import datetime, timedelta

def diagnosticar_propostas():
    """Diagnostica por que não há propostas sendo geradas."""
    print("=" * 70)
    print("DIAGNÓSTICO: Por Que Não Há Propostas?")
    print("=" * 70)
    
    orders_repo = OrdersRepository()
    trading_schedule = TradingSchedule()
    
    # 1. Verificar status do mercado
    print("\n1. STATUS DO MERCADO:")
    b3_time = trading_schedule.get_current_b3_time()
    market_status = trading_schedule.get_trading_status()
    print(f"   Horário B3: {b3_time.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   Status: {market_status}")
    print(f"   É dia de trading? {trading_schedule.is_trading_day(b3_time)}")
    print(f"   É horário de trading? {trading_schedule.is_trading_hours(b3_time)}")
    
    # 2. Verificar propostas geradas (últimas 24h)
    print("\n2. PROPOSTAS GERADAS (Últimas 24h):")
    start_date = (datetime.now() - timedelta(days=1)).isoformat()
    proposals_df = orders_repo.get_proposals(strategy='daytrade_options', start_date=start_date)
    
    if proposals_df.empty:
        print("   ❌ Nenhuma proposta gerada")
    else:
        print(f"   ✅ {len(proposals_df)} propostas geradas")
        print(f"   Primeira: {proposals_df.iloc[0]['timestamp']}")
        print(f"   Última: {proposals_df.iloc[-1]['timestamp']}")
    
    # 3. Verificar avaliações
    print("\n3. AVALIAÇÕES DE RISCO:")
    evaluations_df = orders_repo.get_risk_evaluations()
    if not evaluations_df.empty:
        daytrade_evals = evaluations_df[evaluations_df['proposal_id'].str.contains('DAY', case=False, na=False)]
        if daytrade_evals.empty:
            print("   ⚠️ Nenhuma avaliação de daytrade encontrada")
        else:
            approved = len(daytrade_evals[daytrade_evals['decision'] == 'APPROVE'])
            rejected = len(daytrade_evals[daytrade_evals['decision'] == 'REJECT'])
            print(f"   ✅ Aprovadas: {approved}")
            print(f"   ❌ Rejeitadas: {rejected}")
            
            # Motivos de rejeição
            if rejected > 0:
                print("\n   Motivos de Rejeição:")
                reasons = daytrade_evals[daytrade_evals['decision'] == 'REJECT']['reason'].value_counts()
                for reason, count in reasons.items():
                    print(f"     - {reason}: {count}")
    else:
        print("   ⚠️ Nenhuma avaliação encontrada")
    
    # 4. Verificar capturas de dados
    print("\n4. CAPTURAS DE DADOS (Últimas 2 horas):")
    captures_df = orders_repo.get_market_data_captures(limit=100)
    if not captures_df.empty:
        captures_df['created_at'] = pd.to_datetime(captures_df['created_at'], errors='coerce', utc=True)
        two_hours_ago = pd.Timestamp.now(tz='UTC') - timedelta(hours=2)
        recent = captures_df[captures_df['created_at'] >= two_hours_ago]
        
        if recent.empty:
            print("   ❌ Nenhuma captura nas últimas 2 horas")
        else:
            print(f"   ✅ {len(recent)} capturas nas últimas 2 horas")
            print(f"   Última captura: {recent.iloc[-1]['created_at']}")
            tickers = recent['ticker'].unique() if 'ticker' in recent.columns else []
            print(f"   Tickers capturados: {len(tickers)}")
    else:
        print("   ❌ Nenhuma captura encontrada")
    
    # 5. Verificar configuração
    print("\n5. CONFIGURAÇÃO DO DAYTRADE:")
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        daytrade_cfg = config.get('daytrade_options', {})
        print(f"   Habilitado: {daytrade_cfg.get('enabled', False)}")
        print(f"   min_intraday_return: {daytrade_cfg.get('min_intraday_return', 0.005)} ({daytrade_cfg.get('min_intraday_return', 0.005)*100:.2f}%)")
        print(f"   min_volume_ratio: {daytrade_cfg.get('min_volume_ratio', 0.25)}")
        print(f"   delta_min: {daytrade_cfg.get('delta_min', 0.20)}")
        print(f"   delta_max: {daytrade_cfg.get('delta_max', 0.60)}")
        print(f"   max_dte: {daytrade_cfg.get('max_dte', 7)} dias")
        print(f"   max_spread_pct: {daytrade_cfg.get('max_spread_pct', 0.05)} ({daytrade_cfg.get('max_spread_pct', 0.05)*100:.2f}%)")
        print(f"   min_option_volume: {daytrade_cfg.get('min_option_volume', 200)}")
        
        print("\n   💡 SUGESTÕES:")
        if daytrade_cfg.get('min_intraday_return', 0.005) > 0.003:
            print("     - Considere reduzir min_intraday_return para 0.3% ou menos")
        if daytrade_cfg.get('min_volume_ratio', 0.25) > 0.15:
            print("     - Considere reduzir min_volume_ratio para 0.15 ou menos")
        if daytrade_cfg.get('max_dte', 7) < 14:
            print("     - Considere aumentar max_dte para 14 dias")
        if daytrade_cfg.get('max_spread_pct', 0.05) < 0.10:
            print("     - Considere aumentar max_spread_pct para 10%")
    except Exception as e:
        print(f"   ❌ Erro ao ler config.json: {e}")
    
    # 6. Resumo e recomendações
    print("\n" + "=" * 70)
    print("RESUMO E RECOMENDAÇÕES:")
    print("=" * 70)
    
    if proposals_df.empty:
        print("\n❌ PROBLEMA: Nenhuma proposta está sendo gerada")
        print("\n📋 POSSÍVEIS CAUSAS:")
        print("   1. Critérios muito restritivos em config.json")
        print("   2. Mercado não atende aos critérios")
        print("   3. Dados não estão sendo capturados")
        print("   4. Agente não está rodando")
        print("\n🔧 AÇÕES RECOMENDADAS:")
        print("   1. Verifique se o agente está rodando: python iniciar_agentes.py")
        print("   2. Verifique os logs: tail -f logs/monitoring_service.log")
        print("   3. Reduza os critérios em config.json para testar")
        print("   4. Execute uma simulação: python simular_market_data.py")
    else:
        print(f"\n✅ {len(proposals_df)} propostas foram geradas")
        if not evaluations_df.empty:
            daytrade_evals = evaluations_df[evaluations_df['proposal_id'].str.contains('DAY', case=False, na=False)]
            if not daytrade_evals.empty:
                approved = len(daytrade_evals[daytrade_evals['decision'] == 'APPROVE'])
                rejected = len(daytrade_evals[daytrade_evals['decision'] == 'REJECT'])
                if rejected > 0:
                    print(f"   ⚠️ {rejected} foram rejeitadas")
                    print("   💡 Verifique os motivos de rejeição acima")
                if approved > 0:
                    print(f"   ✅ {approved} foram aprovadas")

if __name__ == '__main__':
    import pandas as pd
    diagnosticar_propostas()

