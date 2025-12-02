"""
Script para testar o sistema de status de propostas.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.orders_repository import OrdersRepository

def testar_status():
    """Testa o sistema de status de propostas."""
    print("=" * 70)
    print("TESTE: Sistema de Status de Propostas")
    print("=" * 70)
    
    repo = OrdersRepository()
    
    # Buscar todas as propostas
    todas = repo.get_proposals()
    print(f"\n1. TOTAL DE PROPOSTAS: {len(todas)}")
    
    if todas.empty:
        print("   ⚠️ Nenhuma proposta encontrada")
        return
    
    # Contar por status
    print("\n2. DISTRIBUIÇÃO POR STATUS:")
    print("-" * 70)
    
    if 'status' in todas.columns:
        status_counts = todas['status'].value_counts()
        print(status_counts.to_string())
        
        # Estatísticas
        geradas = len(todas[todas['status'] == 'gerada'])
        enviadas = len(todas[todas['status'] == 'enviada'])
        aprovadas = len(todas[todas['status'] == 'aprovada'])
        canceladas = len(todas[todas['status'] == 'cancelada'])
        
        print(f"\n   Resumo:")
        print(f"   • Geradas: {geradas}")
        print(f"   • Enviadas: {enviadas}")
        print(f"   • Aprovadas: {aprovadas}")
        print(f"   • Canceladas: {canceladas}")
        
        # Taxa de conversão
        if geradas > 0:
            taxa_enviadas = (enviadas / geradas) * 100
            print(f"\n   Taxa de aprovação pelo RiskAgent: {taxa_enviadas:.1f}%")
        
        if enviadas > 0:
            taxa_aprovadas = (aprovadas / enviadas) * 100
            print(f"   Taxa de aprovação pelo usuário: {taxa_aprovadas:.1f}%")
    else:
        print("   ⚠️ Coluna 'status' não encontrada - executar migração")
    
    # Testar métodos
    print("\n3. TESTANDO MÉTODOS:")
    print("-" * 70)
    
    print(f"   update_proposal_status: {hasattr(repo, 'update_proposal_status')}")
    print(f"   get_proposals_by_status: {hasattr(repo, 'get_proposals_by_status')}")
    
    if hasattr(repo, 'get_proposals_by_status'):
        geradas_df = repo.get_proposals_by_status('gerada')
        print(f"   Propostas 'gerada': {len(geradas_df)}")
        
        enviadas_df = repo.get_proposals_by_status('enviada')
        print(f"   Propostas 'enviada': {len(enviadas_df)}")
        
        aprovadas_df = repo.get_proposals_by_status('aprovada')
        print(f"   Propostas 'aprovada': {len(aprovadas_df)}")
        
        canceladas_df = repo.get_proposals_by_status('cancelada')
        print(f"   Propostas 'cancelada': {len(canceladas_df)}")
    
    print("\n" + "=" * 70)
    print("TESTE CONCLUÍDO")
    print("=" * 70)

if __name__ == '__main__':
    testar_status()

