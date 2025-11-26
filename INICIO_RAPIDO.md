# 🚀 Início Rápido - Colocar Online e Testar

## 📋 Passo a Passo

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar API Server
```bash
# Windows
start_api.bat

# Linux/Mac
./start_api.sh

# Ou manualmente (use run_api.py, não api_server.py diretamente)
python run_api.py
```

**⚠️ IMPORTANTE:** Use `run_api.py` em vez de `api_server.py` diretamente para evitar erros de import!

**API estará disponível em:** http://localhost:5000

### 3. Iniciar Dashboard (Opcional)
```bash
# Em outro terminal
streamlit run dashboard.py
```

**Dashboard estará disponível em:** http://localhost:8501

### 4. Testar a API
```bash
python test_api.py
```

## 🧪 Testes Rápidos

### Teste 1: Health Check
```bash
curl http://localhost:5000/health
```

### Teste 2: Executar Backtest
```bash
curl -X POST http://localhost:5000/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL"], "use_real_data": true}'
```

### Teste 3: Ver Métricas
```bash
curl http://localhost:5000/metrics
```

## 📊 Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/health` | GET | Status de saúde |
| `/backtest/run` | POST | Executar backtest |
| `/backtest/results` | GET | Ver resultados |
| `/data/fetch` | POST | Buscar dados de mercado |
| `/test/pricing` | POST | Testar Black-Scholes |
| `/metrics` | GET | Ver métricas |

## 🎯 Exemplo Completo

### Python
```python
import requests

BASE_URL = "http://localhost:5000"

# Executar backtest
response = requests.post(f"{BASE_URL}/backtest/run", json={
    "tickers": ["AAPL", "MSFT"],
    "use_real_data": True
})

result = response.json()
print(f"Retorno: {result['metrics']['total_return']:.2f}%")
print(f"Sharpe: {result['metrics']['sharpe_ratio']:.4f}")
```

### JavaScript (Frontend)
```javascript
// Executar backtest
fetch('http://localhost:5000/backtest/run', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    tickers: ['AAPL', 'MSFT'],
    use_real_data: true
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

## 🔧 Configuração

Edite `config.json` para ajustar:
- Limites de risco
- Thresholds de estratégias
- Parâmetros de execução

## 📁 Arquivos Gerados

Após executar backtest, os arquivos são salvos em `output/`:
- `metrics.csv` - Métricas de performance
- `portfolio_snapshots.csv` - Snapshots do portfólio
- `orders.csv` - Ordens geradas
- `fills.csv` - Execuções

## 🌐 Acesso Remoto

Para acessar de outra máquina na mesma rede:

1. Altere em `api_server.py`:
```python
app.run(host='0.0.0.0', port=5000)  # Já está assim
```

2. Acesse de outro computador:
```
http://SEU_IP:5000
```

Para descobrir seu IP:
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

## ✅ Checklist

- [ ] Dependências instaladas
- [ ] API server rodando (porta 5000)
- [ ] Dashboard rodando (porta 8501) - opcional
- [ ] Testes executados com sucesso
- [ ] Backtest funcionando
- [ ] Métricas sendo geradas

## 🎉 Pronto!

Agora você pode:
- ✅ Testar os modelos via API
- ✅ Ver resultados no dashboard
- ✅ Integrar com frontend próprio
- ✅ Executar backtests remotamente

