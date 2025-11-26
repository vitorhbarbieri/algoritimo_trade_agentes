# 🌐 API REST - Guia de Uso

## 🚀 Iniciar o Servidor

**IMPORTANTE:** Use `run_api.py` (não `api_server.py` diretamente)

```bash
python run_api.py
```

O servidor iniciará em: **http://localhost:5000**

## 📋 Endpoints Disponíveis

### Informações
- `GET /` - Informações da API e lista de endpoints
- `GET /health` - Status de saúde do servidor

### Backtest
- `POST /backtest/run` - Executar backtest
- `GET /backtest/results` - Ver resultados do último backtest

### Dados
- `POST /data/fetch` - Buscar dados reais de mercado

### Testes
- `POST /test/pricing` - Testar precificação Black-Scholes
- `GET /strategies/list` - Listar estratégias disponíveis
- `GET /metrics` - Ver métricas do último backtest

## 🧪 Exemplos de Uso

### 1. Health Check
```bash
curl http://localhost:5000/health
```

### 2. Executar Backtest
```bash
curl -X POST http://localhost:5000/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "use_real_data": true
  }'
```

### 3. Ver Métricas
```bash
curl http://localhost:5000/metrics
```

### 4. Testar Precificação
```bash
curl -X POST http://localhost:5000/test/pricing \
  -H "Content-Type: application/json" \
  -d '{
    "spot_price": 150.0,
    "strike": 150.0,
    "time_to_expiry": 0.25,
    "volatility": 0.25,
    "option_type": "C"
  }'
```

## 🐍 Exemplo em Python

```python
import requests

BASE_URL = "http://localhost:5000"

# 1. Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. Executar backtest
response = requests.post(f"{BASE_URL}/backtest/run", json={
    "tickers": ["AAPL", "MSFT"],
    "use_real_data": True
})
result = response.json()
print(f"Retorno: {result['metrics']['total_return']:.2f}%")
print(f"Sharpe: {result['metrics']['sharpe_ratio']:.4f}")

# 3. Ver resultados
response = requests.get(f"{BASE_URL}/backtest/results")
results = response.json()
print(f"Snapshots: {len(results['results'].get('snapshots', []))}")
```

## 🔧 Troubleshooting

### Erro: "Connection refused"
- ✅ Certifique-se de que o servidor está rodando
- ✅ Use `python run_api.py` (não `api_server.py`)
- ✅ Verifique se a porta 5000 está livre

### Erro: "ImportError"
- ✅ Use `run_api.py` em vez de `api_server.py`
- ✅ Instale dependências: `pip install -r requirements.txt`

### Servidor não inicia
- ✅ Verifique se Flask está instalado: `pip install flask flask-cors`
- ✅ Veja os erros no terminal

## 📊 Integração com Frontend

A API suporta CORS, então pode ser consumida de qualquer frontend:

```javascript
// JavaScript/React
fetch('http://localhost:5000/backtest/run', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    tickers: ['AAPL'],
    use_real_data: true
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

## 🎯 Próximos Passos

1. ✅ Inicie: `python run_api.py`
2. ✅ Teste: `python test_api_simple.py`
3. ✅ Integre com seu frontend
4. ✅ Comece a testar os modelos!

