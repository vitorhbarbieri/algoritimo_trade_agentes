"""
Script para testar a API do sistema de trading.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def test_health():
    """Testa endpoint de saúde."""
    print("1. Testando /health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.json()}")
        return True
    except Exception as e:
        print(f"   Erro: {e}")
        return False

def test_pricing():
    """Testa precificação Black-Scholes."""
    print("\n2. Testando /test/pricing...")
    try:
        data = {
            'spot_price': 150.0,
            'strike': 150.0,
            'time_to_expiry': 0.25,
            'volatility': 0.25,
            'option_type': 'C'
        }
        response = requests.post(f"{BASE_URL}/test/pricing", json=data)
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Preço da opção: R$ {result['results']['price']:.2f}")
        print(f"   Delta: {result['results']['greeks']['delta']:.4f}")
        return True
    except Exception as e:
        print(f"   Erro: {e}")
        return False

def test_fetch_data():
    """Testa busca de dados de mercado."""
    print("\n3. Testando /data/fetch...")
    try:
        data = {
            'tickers': ['AAPL'],
            'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        }
        response = requests.post(f"{BASE_URL}/data/fetch", json=data)
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Registros de spot: {result['data']['spot_records']}")
        print(f"   Registros de opções: {result['data']['options_records']}")
        return True
    except Exception as e:
        print(f"   Erro: {e}")
        return False

def test_backtest():
    """Testa execução de backtest."""
    print("\n4. Testando /backtest/run...")
    print("   (Isso pode demorar alguns segundos...)")
    try:
        data = {
            'tickers': ['AAPL'],
            'start_date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'use_real_data': True
        }
        response = requests.post(f"{BASE_URL}/backtest/run", json=data, timeout=120)
        result = response.json()
        print(f"   Status: {response.status_code}")
        if result.get('status') == 'success':
            metrics = result['metrics']
            print(f"   Retorno Total: {metrics.get('total_return', 0):.2f}%")
            print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}")
            print(f"   Total Trades: {result['summary']['total_trades']}")
        else:
            print(f"   Erro: {result.get('message', 'Erro desconhecido')}")
        return True
    except Exception as e:
        print(f"   Erro: {e}")
        return False

def test_get_results():
    """Testa obtenção de resultados."""
    print("\n5. Testando /backtest/results...")
    try:
        response = requests.get(f"{BASE_URL}/backtest/results")
        result = response.json()
        print(f"   Status: {response.status_code}")
        if 'results' in result:
            print(f"   Métricas disponíveis: {'metrics' in result['results']}")
            print(f"   Snapshots disponíveis: {'snapshots' in result['results']}")
        return True
    except Exception as e:
        print(f"   Erro: {e}")
        return False

def main():
    print("=" * 70)
    print("TESTE DA API - Sistema de Trading")
    print("=" * 70)
    print(f"\nConectando em: {BASE_URL}")
    print("Certifique-se de que o servidor está rodando (python api_server.py)")
    print("\n" + "=" * 70)
    
    tests = [
        test_health,
        test_pricing,
        test_fetch_data,
        test_backtest,
        test_get_results
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except KeyboardInterrupt:
            print("\n\nTeste interrompido pelo usuário")
            break
        except Exception as e:
            print(f"\nErro inesperado: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Testes passados: {passed}/{total}")
    
    if passed == total:
        print("✅ Todos os testes passaram!")
    else:
        print("⚠️ Alguns testes falharam")

if __name__ == '__main__':
    main()

