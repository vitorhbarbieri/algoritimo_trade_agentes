# 🌐 Como Usar a API - Sistema de Trading

## 🚀 Iniciar o Servidor

### Windows
```bash
start_api.bat
```

### Linux/Mac
```bash
chmod +x start_api.sh
./start_api.sh
```

### Manualmente
```bash
pip install flask flask-cors
python api_server.py
```

O servidor iniciará em: **http://localhost:5000**

## 📋 Endpoints Disponíveis

### 1. Informações da API
```bash
GET http://localhost:5000/
```

### 2. Health Check
```bash
GET http://localhost:5000/health
```

### 3. Executar Backtest
```bash
POST http://localhost:5000/backtest/run
Content-Type: application/json

{
  "tickers": ["AAPL", "MSFT"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "use_real_data": true
}
```

### 4. Ver Resultados
```bash
GET http://localhost:5000/backtest/results
```

### 5. Buscar Dados de Mercado
```bash
POST http://localhost:5000/data/fetch
Content-Type: application/json

{
  "tickers": ["AAPL"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "api_type": "yfinance"
}
```

### 6. Testar Precificação
```bash
POST http://localhost:5000/test/pricing
Content-Type: application/json

{
  "spot_price": 150.0,
  "strike": 150.0,
  "time_to_expiry": 0.25,
  "volatility": 0.25,
  "option_type": "C"
}
```

### 7. Ver Métricas
```bash
GET http://localhost:5000/metrics
```

### 8. Listar Estratégias
```bash
GET http://localhost:5000/strategies/list
```

## 🧪 Testar a API

Execute o script de teste:
```bash
python test_api.py
```

Ou teste manualmente com curl:
```bash
# Health check
curl http://localhost:5000/health

# Executar backtest
curl -X POST http://localhost:5000/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL"], "use_real_data": true}'
```

## 📊 Exemplo Completo em Python

```python
import requests

BASE_URL = "http://localhost:5000"

# 1. Verificar saúde
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. Executar backtest
data = {
    "tickers": ["AAPL", "MSFT"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "use_real_data": True
}
response = requests.post(f"{BASE_URL}/backtest/run", json=data)
result = response.json()
print(f"Métricas: {result['metrics']}")

# 3. Ver resultados
response = requests.get(f"{BASE_URL}/backtest/results")
results = response.json()
print(f"Snapshots: {len(results['results'].get('snapshots', []))}")
```

## 🎯 Integração com Dashboard

O dashboard Streamlit pode consumir a API:

```python
import requests

def get_metrics_from_api():
    response = requests.get("http://localhost:5000/metrics")
    return response.json()['metrics']
```

## 🔧 Configuração

A API usa o arquivo `config.json` para configurações. Edite conforme necessário.

## ⚠️ Troubleshooting

### Erro: "Address already in use"
- Outro processo está usando a porta 5000
- Altere a porta em `api_server.py`: `app.run(port=5001)`

### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

### Erro: "Connection refused"
- Certifique-se de que o servidor está rodando
- Verifique se está acessando a URL correta

## 📝 Próximos Passos

1. ✅ Inicie o servidor: `python api_server.py`
2. ✅ Teste os endpoints: `python test_api.py`
3. ✅ Integre com frontend/dashboard
4. ✅ Comece a testar os modelos!

