# 📊 Resumo: Como Monitorar Agentes e Ver Resultados

## ✅ Status dos TODOs

**Progresso: 6/7 (85%)**

### ✅ Completados (6)
1. ✅ Otimização de sizing
2. ✅ Estratégias de trading
3. ✅ Stubs para broker real
4. ✅ Backtesting paralelo
5. ✅ Integração com APIs reais
6. ✅ Configuração de paralelização

### ⏳ Pendente (1)
7. ⏳ **Análise de risco avançada (VaR, CVaR)**

## 🔍 Como Ver Resultados dos Testes

### Método 1: Monitor Interativo ⭐ RECOMENDADO
```bash
python monitor_agentes.py
```

**Menu:**
- **1** - Ver Atividade dos Agentes (propostas, avaliações, execuções)
- **2** - Ver Resultados dos Testes (métricas, status)
- **3** - Ver Status do Portfólio (NAV, posições)
- **4** - Ver Tudo

### Método 2: Verificar TODOs
```bash
python verificar_todos.py
```

### Método 3: Via API
```bash
# Health check
curl http://localhost:5000/health

# Métricas
curl http://localhost:5000/metrics

# Atividade dos agentes
curl http://localhost:5000/agents/activity

# Resultados do backtest
curl http://localhost:5000/backtest/results
```

## 🤖 Como Saber se os Agentes Estão Fazendo Algo

### 1. Ver Logs em Tempo Real
```bash
# Windows PowerShell
Get-Content logs\decisions-*.jsonl -Tail 20

# Ou usar o monitor
python monitor_agentes.py
# Escolha opção 1
```

### 2. Ver Arquivos Gerados
```bash
# Ver métricas
Get-Content output\metrics.csv

# Ver snapshots
Get-Content output\portfolio_snapshots.csv

# Ver execuções
Get-Content output\fills.csv
```

### 3. Executar Backtest e Monitorar
```python
import requests

# Executar backtest
response = requests.post('http://localhost:5000/backtest/run', json={
    'tickers': ['AAPL'],
    'use_real_data': True
})

# Ver atividade
response = requests.get('http://localhost:5000/agents/activity')
activity = response.json()
print(f"Propostas: {activity['activity']['trader_proposals']}")
print(f"Avaliações: {activity['activity']['risk_evaluations']}")
print(f"Execuções: {activity['activity']['executions']}")
```

## 📈 O Que Cada Agente Faz

### TraderAgent (Criativo)
- ✅ Gera propostas de trading
- ✅ Estratégias: Vol Arbitrage, Pairs Trading
- 📝 Logs: `trader_proposal` em `logs/decisions-*.jsonl`

### RiskAgent (Controlador)
- ✅ Avalia propostas
- ✅ Aprova/Modifica/Rejeita ordens
- ✅ Controla limites de risco
- 📝 Logs: `risk_evaluation` em `logs/decisions-*.jsonl`

### ExecutionSimulator
- ✅ Simula execução
- ✅ Aplica slippage/comissões
- 📝 Logs: `execution` em `logs/decisions-*.jsonl`

## 🎯 Exemplo Rápido

```bash
# 1. Verificar TODOs
python verificar_todos.py

# 2. Executar backtest
python -c "import requests; r = requests.post('http://localhost:5000/backtest/run', json={'tickers': ['AAPL']}); print('Backtest executado!')"

# 3. Monitorar atividade
python monitor_agentes.py
# Escolha opção 4 (Ver Tudo)
```

## 📝 Documentação Completa

Veja `COMO_MONITORAR.md` para guia detalhado.

