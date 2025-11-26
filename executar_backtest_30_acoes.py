"""
Script para executar backtest nas 30 ações monitoradas.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

# Lista de 30 ações
TICKERS_30 = [
    # Brasileiras (15)
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
    'WEGE3.SA', 'MGLU3.SA', 'SUZB3.SA', 'RENT3.SA', 'ELET3.SA',
    'BBAS3.SA', 'SANB11.SA', 'B3SA3.SA', 'RADL3.SA', 'HAPV3.SA',
    # Americanas (15)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
    'META', 'NVDA', 'JPM', 'V', 'JNJ',
    'WMT', 'PG', 'MA', 'DIS', 'NFLX'
]

def executar_backtest():
    """Executa backtest nas 30 ações."""
    print("=" * 70)
    print("EXECUTANDO BACKTEST - 30 AÇÕES MONITORADAS")
    print("=" * 70)
    print(f"\nTotal de ações: {len(TICKERS_30)}")
    print(f"Brasileiras: {len([t for t in TICKERS_30 if '.SA' in t])}")
    print(f"Americanas: {len([t for t in TICKERS_30 if '.SA' not in t])}")
    
    # Verificar se API está online
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ ERRO: API não está respondendo!")
            print("   Inicie o servidor: python run_api.py")
            return
    except Exception as e:
        print(f"\n❌ ERRO: Não foi possível conectar à API: {e}")
        print("   Inicie o servidor: python run_api.py")
        return
    
    print("\n✅ API está online")
    
    # Calcular datas
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    print(f"\n📅 Período do backtest:")
    print(f"   Início: {start_date}")
    print(f"   Fim: {end_date}")
    
    # Preparar payload
    payload = {
        'tickers': TICKERS_30,
        'start_date': start_date,
        'end_date': end_date,
        'use_real_data': True
    }
    
    print("\n🚀 Iniciando backtest...")
    print("   (Isso pode demorar alguns minutos...)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/backtest/run",
            json=payload,
            timeout=600  # 10 minutos
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "=" * 70)
            print("✅ BACKTEST CONCLUÍDO COM SUCESSO!")
            print("=" * 70)
            
            if 'metrics' in result:
                metrics = result['metrics']
                print(f"\n📊 MÉTRICAS:")
                print(f"   Retorno Total: {metrics.get('total_return', 0):.2f}%")
                print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}")
                print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
                print(f"   Volatilidade: {metrics.get('volatility', 0):.2f}%")
                print(f"   Win Rate: {metrics.get('win_rate', 0):.2f}%")
                print(f"   Total de Trades: {metrics.get('total_trades', 0)}")
            
            print("\n📈 Visualize os resultados no Dashboard Central:")
            print("   streamlit run dashboard_central.py")
            print("\n   Ou acesse: http://localhost:8501")
            
        else:
            print(f"\n❌ ERRO: {response.status_code}")
            print(f"   Resposta: {response.text}")
    
    except requests.exceptions.Timeout:
        print("\n⏱️ Timeout: O backtest está demorando mais que o esperado.")
        print("   Verifique o dashboard para acompanhar o progresso.")
    
    except Exception as e:
        print(f"\n❌ ERRO: {e}")

if __name__ == '__main__':
    executar_backtest()

