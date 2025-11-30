#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testar endpoint de monitoramento do DayTrade"""

import requests
import json

try:
    response = requests.get('http://localhost:5000/daytrade/monitoring', timeout=5)
    print(f"Status HTTP: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status resposta: {data.get('status')}")
        
        if data.get('status') == 'success':
            stats = data.get('statistics', {})
            print(f"\nEstatísticas:")
            print(f"  Propostas (24h): {stats.get('total_proposals_24h', 0)}")
            print(f"  Aprovadas: {stats.get('approved_proposals', 0)}")
            print(f"  Rejeitadas: {stats.get('rejected_proposals', 0)}")
            print(f"  Capturas recentes: {stats.get('recent_captures', 0)}")
            print(f"  Tickers monitorados: {stats.get('tickers_monitored', 0)}")
            
            market_status = data.get('market_status', {})
            print(f"\nStatus do Mercado:")
            print(f"  Status: {market_status.get('status')}")
            print(f"  Horário B3: {market_status.get('b3_time', 'N/A')}")
            
            print(f"\nPropostas recentes: {len(data.get('recent_proposals', []))}")
            print(f"Capturas recentes: {len(data.get('recent_captures', []))}")
            print(f"Posições abertas: {len(data.get('open_positions', []))}")
        else:
            print(f"Erro: {data.get('message')}")
            if 'traceback' in data:
                print(f"\nTraceback:\n{data['traceback']}")
    else:
        print(f"Erro HTTP: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Erro: API não está rodando!")
    print("   Execute: python api_server.py")
except Exception as e:
    print(f"❌ Erro: {e}")

