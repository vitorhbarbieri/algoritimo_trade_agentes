"""
Teste simples da API - verifica se está respondendo.
"""

import requests
import time

BASE_URL = "http://localhost:5000"

def test_connection():
    """Testa se a API está respondendo."""
    print("Testando conexão com a API...")
    print(f"URL: {BASE_URL}")
    
    try:
        # Tentar health check
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API está respondendo!")
            print(f"   Resposta: {response.json()}")
            return True
        else:
            print(f"⚠️ API respondeu com status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("   Certifique-se de que o servidor está rodando:")
        print("   python run_api.py")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("TESTE SIMPLES DA API")
    print("=" * 70)
    print()
    
    # Aguardar um pouco caso o servidor esteja iniciando
    print("Aguardando 2 segundos...")
    time.sleep(2)
    
    if test_connection():
        print("\n✅ Teste passou! A API está funcionando.")
        print("\nPróximos passos:")
        print("  1. Execute: python test_api.py (testes completos)")
        print("  2. Acesse: http://localhost:5000 no navegador")
        print("  3. Veja documentação: http://localhost:5000/")
    else:
        print("\n❌ Teste falhou. Verifique se o servidor está rodando.")
        print("\nPara iniciar o servidor:")
        print("  python run_api.py")
        print("  ou")
        print("  start_api.bat")

