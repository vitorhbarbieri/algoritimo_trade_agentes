#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Atualiza configuração com 50 ativos mais líquidos da B3 + Futuros
"""
import json
from pathlib import Path

# Lista dos 50 ativos mais líquidos da B3 (baseado em volume e liquidez)
TOP_50_LIQUIDOS_B3 = [
    # Petrobras
    "PETR4.SA", "PETR3.SA",
    # Vale
    "VALE3.SA",
    # Bancos
    "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "SANB11.SA",
    # Energia
    "ELET3.SA", "ELET6.SA", "EQTL3.SA", "CPLE6.SA", "TAEE11.SA",
    # Varejo
    "MGLU3.SA", "VVAR3.SA", "LREN3.SA",
    # Consumo
    "ABEV3.SA", "RADL3.SA", "RAIL3.SA",
    # Construção
    "CYRE3.SA", "MRVE3.SA", "JHSF3.SA",
    # Siderurgia/Metais
    "CSNA3.SA", "USIM5.SA", "GGBR4.SA",
    # Papel/Celulose
    "SUZB3.SA", "KLBN11.SA",
    # Saúde
    "HAPV3.SA", "RDIA3.SA", "QUAL3.SA",
    # Tecnologia
    "TOTS3.SA", "LWSA3.SA",
    # Transporte
    "RENT3.SA", "GOAU4.SA",
    # Outros setores
    "B3SA3.SA", "WEGE3.SA", "UGPA3.SA", "CMIG4.SA",
    "BRAP4.SA", "BRKM5.SA", "CCRO3.SA", "EMBR3.SA",
    "PRIO3.SA", "RUMO3.SA", "VIVT3.SA", "YDUQ3.SA",
    "AZUL4.SA", "CAML3.SA", "DXCO3.SA", "FLRY3.SA",
    "GNDI3.SA", "HYPE3.SA", "IGTA3.SA", "JSLG3.SA",
    "MULT3.SA", "PCAR3.SA", "POMO4.SA", "SAPR11.SA",
    "SEER3.SA", "SOMA3.SA", "TIMS3.SA", "TRPL4.SA",
    "WIZS3.SA"
]

# Contratos Futuros B3
FUTUROS_B3 = [
    "WIN",   # Mini Índice (Ibovespa)
    "WDO",   # Mini Dólar
    "IND",   # Índice Futuro (Ibovespa)
    "DOL",   # Dólar Futuro
    "WSP",   # Mini S&P 500 (se disponível)
    "DOLF",  # Dólar Futuro Fracionário
]

def atualizar_config():
    """Atualiza config.json com novos ativos."""
    config_path = Path('config.json')
    
    # Backup
    backup_path = Path('config.json.backup_antes_50_ativos')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"Backup criado: {backup_path}")
    
    # Atualizar tickers
    config['monitored_tickers'] = TOP_50_LIQUIDOS_B3
    config['monitored_futures'] = FUTUROS_B3
    
    # Salvar
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("CONFIGURACAO ATUALIZADA")
    print("=" * 80)
    print(f"\nAtivos brasileiros: {len(TOP_50_LIQUIDOS_B3)}")
    print(f"Contratos futuros: {len(FUTUROS_B3)}")
    print(f"\nTotal monitorado: {len(TOP_50_LIQUIDOS_B3) + len(FUTUROS_B3)}")
    
    print("\nAtivos adicionados:")
    novos = set(TOP_50_LIQUIDOS_B3) - set(config.get('monitored_tickers', []))
    for ativo in sorted(novos):
        print(f"  + {ativo}")
    
    print("\nFuturos configurados:")
    for futuro in FUTUROS_B3:
        print(f"  - {futuro}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    atualizar_config()

