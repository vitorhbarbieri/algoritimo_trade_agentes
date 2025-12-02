"""
Script para analisar todas as propostas geradas hoje e avaliar os parâmetros.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.orders_repository import OrdersRepository
from src.trading_schedule import TradingSchedule

def analisar_propostas_hoje():
    """Analisa todas as propostas geradas hoje."""
    print("=" * 70)
    print("ANÁLISE: Propostas Geradas Hoje")
    print("=" * 70)
    
    repo = OrdersRepository()
    schedule = TradingSchedule()
    hoje = schedule.get_current_b3_time().date()
    
    print(f"\n📅 Data de análise: {hoje}")
    print(f"⏰ Hora atual (B3): {schedule.get_current_b3_time().strftime('%H:%M:%S')}")
    
    # Buscar todas as propostas de hoje
    inicio_hoje = datetime.combine(hoje, datetime.min.time()).isoformat()
    fim_hoje = datetime.combine(hoje, datetime.max.time()).isoformat()
    
    print(f"\n1. BUSCANDO PROPOSTAS DE HOJE:")
    print("-" * 70)
    
    try:
        # Buscar propostas
        proposals_df = repo.get_proposals(start_date=inicio_hoje, end_date=fim_hoje)
        
        if proposals_df.empty:
            print("   ⚠️ Nenhuma proposta encontrada para hoje")
            return
        
        print(f"   ✅ {len(proposals_df)} propostas encontradas")
        
        # Filtrar apenas daytrade_options
        daytrade_proposals = proposals_df[proposals_df['strategy'] == 'daytrade_options'].copy()
        
        if daytrade_proposals.empty:
            print("   ⚠️ Nenhuma proposta de daytrade encontrada")
            return
        
        print(f"   ✅ {len(daytrade_proposals)} propostas de daytrade")
        
        # Buscar avaliações de risco
        try:
            evaluations_df = repo.get_risk_evaluations(start_date=inicio_hoje, end_date=fim_hoje)
        except TypeError:
            # Fallback se método não aceita parâmetros de data
            evaluations_df = repo.get_risk_evaluations()
            if not evaluations_df.empty:
                evaluations_df = evaluations_df[
                    (evaluations_df['timestamp'] >= inicio_hoje) & 
                    (evaluations_df['timestamp'] <= fim_hoje)
                ]
        
        # Juntar propostas com avaliações
        if not evaluations_df.empty:
            merged = daytrade_proposals.merge(
                evaluations_df,
                left_on='id',
                right_on='proposal_id',
                how='left',
                suffixes=('_prop', '_eval')
            )
        else:
            merged = daytrade_proposals.copy()
            merged['decision'] = None
            merged['rejection_reason'] = None
        
        print(f"\n2. ESTATÍSTICAS GERAIS:")
        print("-" * 70)
        
        total = len(merged)
        aprovadas = len(merged[merged['decision'] == 'ACCEPT'])
        rejeitadas = len(merged[merged['decision'] == 'REJECT'])
        sem_decisao = len(merged[merged['decision'].isna()])
        
        print(f"   Total de propostas: {total}")
        print(f"   Aprovadas: {aprovadas} ({aprovadas/total*100:.1f}%)")
        print(f"   Rejeitadas: {rejeitadas} ({rejeitadas/total*100:.1f}%)")
        print(f"   Sem decisão: {sem_decisao}")
        
        # Análise de ganho/perda
        print(f"\n3. ANÁLISE DE GANHO/PERDA:")
        print("-" * 70)
        
        if 'metadata' in merged.columns:
            # Extrair dados de metadata
            ganhos = []
            perdas = []
            ganhos_pct = []
            perdas_pct = []
            
            for idx, row in merged.iterrows():
                metadata = row.get('metadata', {})
                if isinstance(metadata, str):
                    import json
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                expected_gain_pct = metadata.get('expected_gain_pct', 0)
                expected_loss_pct = metadata.get('expected_loss_pct', 0)
                expected_gain_value = metadata.get('expected_gain_value', 0)
                expected_loss_value = metadata.get('expected_loss_value', 0)
                
                ganhos_pct.append(expected_gain_pct)
                perdas_pct.append(expected_loss_pct)
                ganhos.append(expected_gain_value)
                perdas.append(expected_loss_value)
            
            merged['gain_pct'] = ganhos_pct
            merged['loss_pct'] = perdas_pct
            merged['gain_value'] = ganhos
            merged['loss_value'] = perdas
            
            # Calcular razão ganho/perda
            merged['gain_loss_ratio'] = merged['gain_pct'].abs() / merged['loss_pct'].abs()
            merged['gain_loss_ratio'] = merged['gain_loss_ratio'].replace([float('inf'), float('-inf')], 0)
            
            print(f"   Ganho médio esperado: {merged['gain_pct'].mean()*100:.2f}%")
            print(f"   Perda máxima esperada: {merged['loss_pct'].mean()*100:.2f}%")
            print(f"   Razão ganho/perda média: {merged['gain_loss_ratio'].mean():.2f}")
            print(f"   Ganho médio (R$): R$ {merged['gain_value'].mean():.2f}")
            print(f"   Perda máxima média (R$): R$ {merged['loss_value'].mean():.2f}")
            
            # Propostas com razão ruim (< 0.25)
            ruins = merged[merged['gain_loss_ratio'] < 0.25]
            print(f"\n   ⚠️ Propostas com razão ganho/perda < 0.25: {len(ruins)} ({len(ruins)/total*100:.1f}%)")
            
            # Propostas com ganho muito baixo (< 0.3%)
            ganho_baixo = merged[merged['gain_pct'] < 0.003]
            print(f"   ⚠️ Propostas com ganho esperado < 0.3%: {len(ganho_baixo)} ({len(ganho_baixo)/total*100:.1f}%)")
        
        # Análise por ticker
        print(f"\n4. ANÁLISE POR TICKER:")
        print("-" * 70)
        
        ticker_stats = merged.groupby('symbol').agg({
            'id': 'count',
            'decision': lambda x: (x == 'ACCEPT').sum(),
            'gain_pct': 'mean',
            'loss_pct': 'mean',
            'gain_loss_ratio': 'mean'
        }).rename(columns={'id': 'total', 'decision': 'aprovadas'})
        
        ticker_stats = ticker_stats.sort_values('total', ascending=False)
        print(ticker_stats.head(10).to_string())
        
        # Análise de rejeições
        print(f"\n5. MOTIVOS DE REJEIÇÃO:")
        print("-" * 70)
        
        rejeitadas_df = merged[merged['decision'] == 'REJECT']
        if not rejeitadas_df.empty and 'rejection_reason' in rejeitadas_df.columns:
            reasons = rejeitadas_df['rejection_reason'].value_counts()
            print(reasons.to_string())
        
        # Recomendações
        print(f"\n6. RECOMENDAÇÕES:")
        print("-" * 70)
        
        if len(merged) > 50:
            print(f"   ⚠️ MUITAS PROPOSTAS ({len(merged)}) - Parâmetros muito fracos")
            print(f"   Sugestão: Aumentar min_intraday_return e min_volume_ratio")
        
        if merged['gain_loss_ratio'].mean() < 0.3:
            print(f"   ⚠️ Razão ganho/perda muito baixa ({merged['gain_loss_ratio'].mean():.2f})")
            print(f"   Sugestão: Aumentar take_profit_pct ou reduzir stop_loss_pct")
        
        if merged['gain_pct'].mean() < 0.005:
            print(f"   ⚠️ Ganho esperado muito baixo ({merged['gain_pct'].mean()*100:.2f}%)")
            print(f"   Sugestão: Aumentar min_intraday_return")
        
        # Salvar análise
        output_file = f"analise_propostas_{hoje.strftime('%Y%m%d')}.csv"
        merged.to_csv(output_file, index=False)
        print(f"\n   ✅ Análise salva em: {output_file}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analisar_propostas_hoje()

