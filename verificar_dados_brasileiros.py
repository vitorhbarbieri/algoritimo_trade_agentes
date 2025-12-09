#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifica dados brasileiros disponíveis"""
from src.orders_repository import OrdersRepository
import pandas as pd

repo = OrdersRepository()
props = repo.get_proposals()

print("=" * 80)
print("VERIFICAÇÃO DE DADOS BRASILEIROS")
print("=" * 80)

print(f"\nTotal de propostas no banco: {len(props)}")

if not props.empty:
    print(f"\nColunas disponíveis: {list(props.columns)}")
    
    if 'symbol' in props.columns:
        print(f"\nSímbolos únicos: {props['symbol'].nunique()}")
        print(f"\nTop 20 símbolos:")
        print(props['symbol'].value_counts().head(20))
        
        # Verificar brasileiros
        brasil = props[props['symbol'].str.contains('.SA', na=False)]
        print(f"\nPropostas brasileiras (.SA): {len(brasil)}")
        
        if not brasil.empty:
            print("\nAtivos brasileiros encontrados:")
            print(brasil['symbol'].value_counts())
    else:
        print("\n⚠️ Coluna 'symbol' não encontrada")
        
    if 'metadata' in props.columns:
        print("\n\nVerificando metadata para identificar ativos...")
        # Tentar extrair underlying do metadata
        sample = props.head(10)
        print(sample[['proposal_id', 'symbol', 'strategy']] if 'strategy' in props.columns else sample[['proposal_id', 'symbol']])
else:
    print("\n⚠️ Nenhuma proposta encontrada no banco")

