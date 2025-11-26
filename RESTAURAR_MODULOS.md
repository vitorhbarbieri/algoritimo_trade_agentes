# 🔄 Restaurar Módulos do Projeto

## ⚠️ Situação

Os módulos do diretório `src/` foram deletados acidentalmente. Eles precisam ser recriados.

## 📋 Módulos Necessários

1. `src/utils.py` - Logging e métricas
2. `src/pricing.py` - Black-Scholes e greeks
3. `src/data_loader.py` - Carregamento de dados
4. `src/market_data_api.py` - APIs de dados reais
5. `src/agents.py` - TraderAgent e RiskAgent
6. `src/execution.py` - ExecutionSimulator
7. `src/backtest.py` - BacktestEngine
8. `src/backtest_parallel.py` - Backtest paralelo
9. `src/sizing.py` - Métodos de sizing
10. `src/strategies.py` - Estratégias adicionais
11. `src/broker_adapters.py` - Adaptadores de broker

## 🚀 Solução Rápida

Execute este comando para recriar todos os módulos:

```bash
# O assistente irá recriar todos os arquivos automaticamente
```

Ou peça ao assistente: "Recrie todos os módulos do diretório src/"

## ✅ Verificação

Após restaurar, verifique:
```bash
cd C:\Projetos\algoritimo_trade_agentes
Get-ChildItem src\*.py | Select-Object Name
```

Deve mostrar todos os 11 arquivos listados acima.

