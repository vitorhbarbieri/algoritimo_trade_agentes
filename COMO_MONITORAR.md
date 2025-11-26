# 📊 Como Monitorar Agentes e Ver Resultados

## ✅ Status dos TODOs

**Progresso: 6/7 (85%)**

### Completados ✅
1. ✅ Otimização de sizing (Kelly, Risk Parity, Fixed Fraction)
2. ✅ Estratégias de trading (momentum, mean reversion, breakout)
3. ✅ Stubs para broker real (IB/CCXT)
4. ✅ Backtesting paralelo
5. ✅ Integração com APIs reais (yfinance, Brapi)
6. ✅ Configuração de paralelização

### Pendente ⏳
7. ⏳ **Análise de risco avançada (VaR, CVaR)** ← Único pendente!

## 🔍 Como Ver Resultados dos Testes

### Opção 1: Monitor Interativo (Recomendado)
```bash
python monitor_agentes.py
```

Menu interativo com:
- **Opção 1:** Ver Atividade dos Agentes
  - Propostas do TraderAgent
  - Avaliações do RiskAgent
  - Execuções realizadas
  
- **Opção 2:** Ver Resultados dos Testes
  - Status da API
  - Métricas do backtest
  - Resultados completos
  
- **Opção 3:** Ver Status do Portfólio
  - NAV atual
  - Posições abertas
  - Resumo de execuções
  
- **Opção 4:** Ver Tudo (todas as informações)

### Opção 2: Verificar TODOs
```bash
python verificar_todos.py
```

Mostra status de todos os TODOs do projeto.

### Opção 3: Via API (Navegador/curl)

**Health Check:**
```
http://localhost:5000/health
```

**Métricas:**
```
http://localhost:5000/metrics
```

**Resultados do Backtest:**
```
http://localhost:5000/backtest/results
```

### Opção 4: Via Python
```python
import requests

# Métricas
response = requests.get('http://localhost:5000/metrics')
metrics = response.json()
print(f"Retorno: {metrics['metrics']['total_return']:.2f}%")
print(f"Sharpe: {metrics['metrics']['sharpe_ratio']:.4f}")

# Resultados
response = requests.get('http://localhost:5000/backtest/results')
results = response.json()
print(f"Snapshots: {len(results['results']['snapshots'])}")
print(f"Fills: {len(results['results']['fills'])}")
```

## 🤖 Como Saber se os Agentes Estão Fazendo Algo

### 1. Ver Logs dos Agentes
```bash
# Ver logs em tempo real
Get-Content logs\decisions-*.jsonl -Tail 20

# Ou usar o monitor
python monitor_agentes.py
# Escolha opção 1
```

### 2. Verificar Arquivos de Saída
```bash
# Ver métricas geradas
Get-Content output\metrics.csv

# Ver snapshots do portfólio
Get-Content output\portfolio_snapshots.csv

# Ver ordens executadas
Get-Content output\fills.csv
```

### 3. Executar Backtest e Ver Atividade
```bash
# Executar backtest via API
curl -X POST http://localhost:5000/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL"], "use_real_data": true}'

# Depois verificar resultados
python monitor_agentes.py
```

### 4. Endpoints da API para Monitoramento

| Endpoint | Descrição |
|----------|-----------|
| `GET /health` | Status da API |
| `GET /metrics` | Métricas do último backtest |
| `GET /backtest/results` | Resultados completos |
| `GET /strategies/list` | Estratégias disponíveis |

## 📈 O Que os Agentes Fazem

### TraderAgent (Agente Criativo)
- ✅ Gera propostas de trading
- ✅ Estratégias: Vol Arbitrage, Pairs Trading
- ✅ Analisa oportunidades de mercado
- 📝 Logs em: `logs/decisions-*.jsonl` (event_type: `trader_proposal`)

### RiskAgent (Agente Controlador)
- ✅ Avalia propostas do TraderAgent
- ✅ Aprova/Modifica/Rejeita ordens
- ✅ Verifica limites de risco
- ✅ Controla greeks agregados
- 📝 Logs em: `logs/decisions-*.jsonl` (event_type: `risk_evaluation`)

### ExecutionSimulator
- ✅ Simula execução de ordens
- ✅ Aplica slippage e comissões
- ✅ Gera fills
- 📝 Logs em: `logs/decisions-*.jsonl` (event_type: `execution`)

## 🎯 Exemplo Completo de Monitoramento

```bash
# 1. Verificar status dos TODOs
python verificar_todos.py

# 2. Executar backtest
python -c "import requests; r = requests.post('http://localhost:5000/backtest/run', json={'tickers': ['AAPL'], 'use_real_data': True}); print(r.json())"

# 3. Monitorar atividade
python monitor_agentes.py
# Escolha opção 4 (Ver Tudo)

# 4. Ver arquivos gerados
Get-ChildItem output\*.csv | Select-Object Name, Length
```

## 📝 Logs Estruturados

Todos os logs são salvos em formato JSON Lines em `logs/decisions-YYYYMMDD.jsonl`:

```json
{
  "timestamp": "2025-11-23T19:14:33",
  "event_type": "trader_proposal",
  "proposal_id": "VOL_ARB_1",
  "strategy": "vol_arb",
  "mispricing": 0.05
}
```

## ✅ Checklist de Monitoramento

- [ ] API está online? → `python test_api_simple.py`
- [ ] Agentes gerando propostas? → `python monitor_agentes.py` (opção 1)
- [ ] Backtest executado? → Ver `output/metrics.csv`
- [ ] Logs sendo gerados? → Ver `logs/decisions-*.jsonl`
- [ ] Métricas disponíveis? → `GET /metrics`

