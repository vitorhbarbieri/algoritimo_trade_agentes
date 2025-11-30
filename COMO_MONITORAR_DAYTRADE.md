# 📊 Como Monitorar a Atividade do Agente DayTrade

## 🎯 Objetivo

Este guia explica como verificar se o agente de daytrade está analisando as possibilidades conforme os dados de mercado entram.

## 🔍 Métodos de Monitoramento

### 1. Script de Monitoramento (`monitorar_daytrade.py`)

Execute o script para ver um resumo completo da atividade:

```bash
python monitorar_daytrade.py
```

**O que o script mostra:**
- ✅ Total de propostas DayTrade geradas
- 📋 Últimas 5 propostas com detalhes
- 📊 Estatísticas de avaliação (aprovadas vs rejeitadas)
- ✅ Últimas capturas de dados de mercado
- 🕐 Status do mercado (aberto/fechado)
- 💼 Posições abertas no portfólio

### 2. Dashboard Central (`dashboard_central.py`)

O dashboard agora possui uma aba **"💼 Portfólio"** que mostra:

- **Métricas Gerais:**
  - Posições Abertas
  - PnL Não Realizado
  - Delta Total
  - Gamma Total
  - Vega Total

- **Detalhes das Posições:**
  - Símbolo
  - Lado (BUY/SELL)
  - Quantidade
  - Preço Médio
  - Preço Atual
  - PnL Não Realizado
  - Greeks (Delta, Gamma, Vega)
  - Data de Abertura

- **Gráfico de PnL por Posição**

**Como acessar:**
1. Inicie o servidor API: `python api_server.py`
2. Inicie o dashboard: `streamlit run dashboard_central.py`
3. Acesse a aba **"💼 Portfólio"**

### 3. API Endpoint (`/portfolio/positions`)

Você pode consultar diretamente via API:

```bash
curl http://localhost:5000/portfolio/positions
```

Ou em Python:

```python
import requests
response = requests.get('http://localhost:5000/portfolio/positions')
data = response.json()
print(f"Posições: {data['total_positions']}")
print(f"PnL Total: R$ {data['total_unrealized_pnl']:,.2f}")
```

### 4. Banco de Dados Direto

Consulte diretamente o banco SQLite:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('agents_orders.db')

# Ver propostas de daytrade
proposals = pd.read_sql_query(
    "SELECT * FROM proposals WHERE strategy='daytrade_options' ORDER BY created_at DESC LIMIT 10",
    conn
)
print(proposals[['symbol', 'side', 'quantity', 'price', 'created_at']])

# Ver posições abertas
positions = pd.read_sql_query(
    "SELECT * FROM open_positions WHERE closed_at IS NULL",
    conn
)
print(positions[['symbol', 'quantity', 'avg_price', 'unrealized_pnl']])

# Ver capturas de dados recentes
captures = pd.read_sql_query(
    "SELECT * FROM market_data_captures ORDER BY created_at DESC LIMIT 20",
    conn
)
print(captures[['ticker', 'data_type', 'last_price', 'created_at']])

conn.close()
```

## 📈 Como Saber se o DayTrade Está Analisando

### Sinais de Atividade:

1. **✅ Capturas de Dados de Mercado**
   - Verifique `market_data_captures` no banco
   - Deve haver capturas a cada 5 minutos durante o pregão
   - Última captura deve ser recente (últimos minutos)

2. **✅ Propostas Geradas**
   - Verifique `proposals` com `strategy='daytrade_options'`
   - Novas propostas indicam que o agente está analisando
   - Timestamp deve estar atualizado

3. **✅ Avaliações de Risco**
   - Verifique `risk_evaluations` relacionadas às propostas
   - Decisões (APPROVE/REJECT) indicam processamento

4. **✅ Logs do Sistema**
   - Verifique os logs em `logs/` ou no dashboard
   - Procure por mensagens como:
     - "Propostas geradas: X"
     - "Propostas de daytrade encontradas: X"
     - "Dados capturados: X tickers"

### Verificação em Tempo Real:

```bash
# Monitorar logs em tempo real
tail -f logs/monitoring-*.log | grep -i daytrade

# Ou usar o script de monitoramento em loop
watch -n 30 python monitorar_daytrade.py
```

## 🔄 Frequência de Análise

O agente DayTrade analisa dados:

- **A cada 5 minutos** durante o pregão (10:00 - 17:00 B3)
- **Durante pré-mercado** (09:45 - 10:00)
- **Durante pós-mercado** (17:00 - 18:00)
- **Não analisa** quando o mercado está fechado

## 📊 Exemplo de Saída do Monitoramento

```
======================================================================
MONITORAMENTO DO AGENTE DAYTRADE
======================================================================

📊 Verificando atividade do DayTrade...

✅ Total de propostas DayTrade encontradas: 10

📋 Últimas 5 Propostas:
----------------------------------------------------------------------
  • SANB11.SA_34.38_C_20251202 | BUY | Qty: 100.0 | Preço: R$ 0.10
    Timestamp: 2025-11-27T22:32:16

✅ Últimas 20 capturas de dados de mercado:
----------------------------------------------------------------------
  • Tickers capturados: ABEV3.SA, B3SA3.SA, BBAS3.SA, ...
  • Última captura: 2025-11-29T11:24:49

🕐 Status do Mercado:
  • Horário B3: 29/11/2025 11:30:08
  • Status: CLOSED

💼 Posições Abertas: 10
----------------------------------------------------------------------
  • MGLU3.SA_10.2_C_20251202 | Qty: 100.0 | Preço Médio: R$ 10.21 | PnL: R$ -0.51
  ...
```

## ✅ Checklist de Verificação

- [ ] Script `monitorar_daytrade.py` executa sem erros
- [ ] Dashboard mostra aba "Portfólio" com dados
- [ ] API endpoint `/portfolio/positions` retorna dados
- [ ] Banco de dados contém propostas recentes
- [ ] Capturas de dados estão sendo feitas regularmente
- [ ] Logs mostram atividade do DayTrade

## 🐛 Problemas Comuns

### Dashboard não mostra portfólio:
- Verifique se a API está rodando (`python api_server.py`)
- Verifique se há posições no banco de dados
- Recarregue o dashboard (F5)

### Nenhuma proposta sendo gerada:
- Verifique se o mercado está aberto
- Verifique se há dados de mercado sendo capturados
- Verifique os logs para erros
- Execute `python monitorar_daytrade.py` para diagnóstico

### Dados não estão sendo capturados:
- Verifique se `MonitoringService` está rodando
- Verifique conexão com APIs de mercado
- Verifique horário B3 (mercado pode estar fechado)

---

**Última atualização**: 29/11/2025
**Status**: ✅ Dashboard e monitoramento funcionando

