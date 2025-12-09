#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verifica dados de mercado brasileiros capturados no banco de dados
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orders_repository import OrdersRepository

def verificar_dados_mercado():
    """Verifica dados de mercado brasileiros disponíveis."""
    print("=" * 100)
    print("VERIFICAÇÃO DE DADOS DE MERCADO BRASILEIROS")
    print("=" * 100)
    
    repo = OrdersRepository()
    
    # Buscar todas as capturas
    print("\n1. BUSCANDO CAPTURAS DE MERCADO...")
    print("-" * 100)
    
    captures = repo.get_market_data_captures()
    
    if captures.empty:
        print("⚠️ Nenhuma captura de mercado encontrada no banco")
        return None
    
    print(f"✅ Total de capturas encontradas: {len(captures)}")
    print(f"\nColunas disponíveis: {list(captures.columns)}")
    
    # Filtrar brasileiros
    print("\n2. FILTRANDO ATIVOS BRASILEIROS...")
    print("-" * 100)
    
    if 'ticker' in captures.columns:
        brasil = captures[captures['ticker'].str.contains('.SA', na=False)]
        print(f"✅ Capturas brasileiras: {len(brasil)}")
        
        if brasil.empty:
            print("⚠️ Nenhuma captura brasileira encontrada")
            return None
        
        # Análise por ativo
        print("\n3. ANÁLISE POR ATIVO BRASILEIRO:")
        print("-" * 100)
        
        ativos = brasil['ticker'].unique()
        print(f"\nAtivos brasileiros com dados: {len(ativos)}")
        
        resultados = []
        for ativo in sorted(ativos):
            dados_ativo = brasil[brasil['ticker'] == ativo]
            
            # Verificar source
            if 'source' in dados_ativo.columns:
                real_count = len(dados_ativo[dados_ativo['source'] == 'real'])
                sim_count = len(dados_ativo[dados_ativo['source'] == 'simulation'])
            else:
                real_count = len(dados_ativo)
                sim_count = 0
            
            # Verificar timestamps
            if 'timestamp' in dados_ativo.columns:
                dados_ativo['timestamp'] = pd.to_datetime(dados_ativo['timestamp'], errors='coerce')
                dados_ativo = dados_ativo.dropna(subset=['timestamp'])
                
                if not dados_ativo.empty:
                    primeiro = dados_ativo['timestamp'].min()
                    ultimo = dados_ativo['timestamp'].max()
                    dias = (ultimo - primeiro).days + 1 if primeiro != ultimo else 1
                else:
                    primeiro = None
                    ultimo = None
                    dias = 0
            else:
                primeiro = None
                ultimo = None
                dias = 0
            
            resultados.append({
                'ativo': ativo,
                'total_capturas': len(dados_ativo),
                'dados_reais': real_count,
                'dados_simulados': sim_count,
                'primeira_captura': primeiro,
                'ultima_captura': ultimo,
                'dias_cobertura': dias
            })
            
            print(f"\n  {ativo}:")
            print(f"    Total de capturas: {len(dados_ativo)}")
            print(f"    Dados reais: {real_count}")
            print(f"    Dados simulados: {sim_count}")
            if primeiro:
                print(f"    Primeira captura: {primeiro.strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"    Última captura: {ultimo.strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"    Dias de cobertura: {dias}")
        
        # Resumo
        print("\n4. RESUMO GERAL:")
        print("-" * 100)
        
        df_resumo = pd.DataFrame(resultados)
        
        total_real = df_resumo['dados_reais'].sum()
        total_sim = df_resumo['dados_simulados'].sum()
        
        print(f"\nTotal de capturas brasileiras: {len(brasil)}")
        print(f"Dados reais: {total_real}")
        print(f"Dados simulados: {total_sim}")
        print(f"Percentual real: {total_real/(total_real+total_sim)*100:.1f}%" if (total_real+total_sim) > 0 else "N/A")
        
        # Verificar se temos dados suficientes para análise
        print("\n5. AVALIAÇÃO PARA ANÁLISE:")
        print("-" * 100)
        
        ativos_com_dados_reais = df_resumo[df_resumo['dados_reais'] > 0]
        print(f"\nAtivos com dados reais: {len(ativos_com_dados_reais)}")
        
        if len(ativos_com_dados_reais) > 0:
            print("\n✅ TEMOS DADOS REAIS PARA ANÁLISE!")
            print("\nAtivos com dados reais suficientes:")
            for idx, row in ativos_com_dados_reais.iterrows():
                if row['dados_reais'] >= 5:  # Mínimo de 5 capturas
                    print(f"  ✅ {row['ativo']}: {row['dados_reais']} capturas reais")
                else:
                    print(f"  ⚠️ {row['ativo']}: {row['dados_reais']} capturas reais (poucas)")
        else:
            print("\n⚠️ NENHUM DADO REAL ENCONTRADO")
            print("   Todos os dados são simulados")
        
        return df_resumo, brasil
    else:
        print("⚠️ Coluna 'ticker' não encontrada")
        return None

if __name__ == '__main__':
    resultado = verificar_dados_mercado()
    
    if resultado:
        df_resumo, brasil = resultado
        print("\n" + "=" * 100)
        print("VERIFICAÇÃO CONCLUÍDA")
        print("=" * 100)

