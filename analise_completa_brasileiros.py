#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análise Completa dos Ativos Brasileiros Disponíveis
Analisa as 10 propostas brasileiras encontradas no banco
"""
import sys
from pathlib import Path
import pandas as pd
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.b3_costs import B3CostCalculator
from src.orders_repository import OrdersRepository

def analisar_propostas_brasileiras():
    """Analisa as propostas brasileiras disponíveis."""
    print("=" * 100)
    print("ANÁLISE COMPLETA - ATIVOS BRASILEIROS (B3)")
    print("=" * 100)
    
    repo = OrdersRepository()
    calculator = B3CostCalculator()
    
    # Buscar propostas brasileiras
    props = repo.get_proposals()
    brasil = props[props['symbol'].str.contains('.SA', na=False)].copy()
    
    print(f"\n📊 PROPOSTAS BRASILEIRAS ENCONTRADAS: {len(brasil)}")
    print("-" * 100)
    
    if brasil.empty:
        print("⚠️ Nenhuma proposta brasileira encontrada")
        return
    
    # Extrair ativos únicos
    ativos = []
    for symbol in brasil['symbol'].unique():
        # Extrair ativo base (ex: PETR4.SA de PETR4.SA_32.66_C_20251202)
        ativo = symbol.split('_')[0]
        if ativo not in ativos:
            ativos.append(ativo)
    
    print(f"\n📋 ATIVOS BRASILEIROS IDENTIFICADOS: {len(ativos)}")
    for i, ativo in enumerate(sorted(ativos), 1):
        count = len(brasil[brasil['symbol'].str.startswith(ativo)])
        print(f"  {i:2d}. {ativo:15s} - {count:3d} proposta(s)")
    
    # Análise detalhada por ativo
    resultados = []
    
    for ativo in sorted(ativos):
        print("\n" + "=" * 100)
        print(f"📊 ANÁLISE DETALHADA: {ativo}")
        print("=" * 100)
        
        props_ativo = brasil[brasil['symbol'].str.startswith(ativo)].copy()
        
        print(f"\n📈 ESTATÍSTICAS:")
        print("-" * 100)
        print(f"  Total de propostas: {len(props_ativo)}")
        
        # Analisar cada proposta
        for idx, row in props_ativo.iterrows():
            print(f"\n  Proposta {idx + 1}:")
            print(f"    ID: {row['proposal_id']}")
            print(f"    Símbolo: {row['symbol']}")
            print(f"    Tipo: {row['instrument_type']}")
            print(f"    Lado: {row['side']}")
            print(f"    Quantidade: {row['quantity']}")
            print(f"    Preço: R$ {row['price']:.2f}")
            print(f"    Status: {row.get('status', 'N/A')}")
            print(f"    Data: {row.get('created_at', 'N/A')}")
            
            # Tentar extrair metadata
            try:
                metadata_str = row.get('metadata', '{}')
                if isinstance(metadata_str, str):
                    metadata = json.loads(metadata_str.replace("'", '"'))
                else:
                    metadata = metadata_str
                
                if metadata:
                    print(f"    Metadata:")
                    if 'underlying' in metadata:
                        print(f"      Underlying: {metadata['underlying']}")
                    if 'intraday_return' in metadata:
                        print(f"      Intraday Return: {metadata['intraday_return']*100:.3f}%")
                    if 'delta' in metadata:
                        print(f"      Delta: {metadata['delta']:.3f}")
                    if 'volume_ratio' in metadata:
                        print(f"      Volume Ratio: {metadata['volume_ratio']:.2f}x")
            except:
                pass
            
            # Calcular custos estimados
            entry_value = row['price'] * row['quantity'] * 100  # Assumir opção
            exit_value_estimado = entry_value * 1.01  # Assumir 1% de lucro
            
            costs = calculator.calculate_total_costs(
                entry_value=entry_value,
                exit_value=exit_value_estimado,
                instrument_type='options'
            )
            
            print(f"    Custos estimados:")
            print(f"      Operacionais: R$ {costs['total_operational_costs']:.2f}")
            print(f"      Impostos (se 1% lucro): R$ {costs['total_taxes']:.2f}")
            print(f"      Total: R$ {costs['total_costs']:.2f}")
        
        # Resumo do ativo
        print(f"\n💡 RESUMO PARA {ativo}:")
        print("-" * 100)
        print(f"  • Total de propostas: {len(props_ativo)}")
        print(f"  • Status atual: {props_ativo['status'].value_counts().to_dict()}")
        print(f"  • Recomendação: {'Continuar monitorando' if len(props_ativo) > 0 else 'Aguardar mais dados'}")
        
        resultados.append({
            'ativo': ativo,
            'total_propostas': len(props_ativo),
            'status': props_ativo['status'].value_counts().to_dict()
        })
    
    # Resumo geral
    print("\n" + "=" * 100)
    print("📊 RESUMO GERAL")
    print("=" * 100)
    
    print(f"\nTotal de ativos brasileiros analisados: {len(ativos)}")
    print(f"Total de propostas brasileiras: {len(brasil)}")
    
    print(f"\n💡 CONCLUSÕES:")
    print("-" * 100)
    print("  1. Dados brasileiros ainda limitados (10 propostas)")
    print("  2. Sistema está gerando propostas para ativos brasileiros")
    print("  3. Necessário mais tempo de operação para análise estatística robusta")
    print("  4. Recomendação: Continuar operando e coletar mais dados")
    
    print(f"\n🎯 PRÓXIMOS PASSOS:")
    print("-" * 100)
    print("  1. Aguardar mais operações brasileiras")
    print("  2. Executar análise novamente quando houver mais dados")
    print("  3. Monitorar desempenho em tempo real")
    print("  4. Ajustar parâmetros conforme necessário")
    
    return resultados

if __name__ == '__main__':
    analisar_propostas_brasileiras()

