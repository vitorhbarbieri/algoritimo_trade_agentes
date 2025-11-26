# 📊 Guia do Dashboard Central

## 🎯 Visão Geral

O **Dashboard Central** é uma interface única que mostra **tudo** sobre o sistema de trading:
- ✅ Atividade dos agentes em tempo real
- ✅ Métricas de performance
- ✅ Status do portfólio
- ✅ Resultados de backtest
- ✅ 30 ações monitoradas

## 🚀 Como Iniciar

### Passo 1: Iniciar API Server
```bash
python run_api.py
```
Deixe rodando em um terminal.

### Passo 2: Iniciar Dashboard
```bash
# Windows
start_dashboard_central.bat

# Linux/Mac
./start_dashboard_central.sh

# Ou manualmente
streamlit run dashboard_central.py
```

O dashboard abrirá automaticamente em: **http://localhost:8501**

### Passo 3: Executar Backtest (Opcional)
```bash
python executar_backtest_30_acoes.py
```

## 📋 Funcionalidades do Dashboard

### Tab 1: 📊 Visão Geral
- Métricas principais (Retorno, Sharpe, Propostas, Execuções)
- Gráfico de evolução do NAV
- Atividade recente dos agentes

### Tab 2: 🤖 Atividade dos Agentes
- Propostas do TraderAgent
- Avaliações do RiskAgent
- Execuções realizadas
- Gráfico de distribuição de atividades
- Tabela de atividades recentes

### Tab 3: 💰 Portfólio
- NAV atual
- Cash disponível
- Valor das posições
- Posições abertas
- Histórico de execuções

### Tab 4: 📈 Backtest
- Métricas completas (Retorno, Sharpe, Drawdown, Win Rate)
- Gráficos de performance
- Tabela detalhada de métricas

### Tab 5: 📋 Ações Monitoradas
- Lista completa das 30 ações
- Separadas por brasileiras e americanas
- Informações sobre estratégias aplicadas

## 📈 30 Ações Monitoradas

### 🇧🇷 Brasileiras (15)
PETR4, VALE3, ITUB4, BBDC4, ABEV3, WEGE3, MGLU3, SUZB3, RENT3, ELET3, BBAS3, SANB11, B3SA3, RADL3, HAPV3

### 🇺🇸 Americanas (15)
AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, JPM, V, JNJ, WMT, PG, MA, DIS, NFLX

## 🎯 Estratégias Aplicadas

### 1. Volatility Arbitrage
- Busca opções com preços desalinhados
- Foca em ações com alta liquidez
- Principalmente: AAPL, MSFT, TSLA, PETR4, VALE3

### 2. Pairs Trading
- Identifica pares cointegrados
- Exemplos:
  - ITUB4 ↔ BBDC4 (bancos)
  - AAPL ↔ MSFT (tech)
  - PETR4 ↔ VALE3 (commodities)

### 3. Assimetrias de Mercado
- Análise de spreads bid-ask
- Detecção de oportunidades
- Monitoramento de volatilidade

## 🔧 Sidebar - Configurações

### Status da API
- ✅ Verde = Online
- ❌ Vermelho = Offline

### Filtros
- Marque/desmarque para filtrar ações brasileiras ou americanas

### Ações Rápidas
- **🔄 Executar Backtest**: Executa backtest nas ações filtradas
- **🔄 Atualizar Dados**: Atualiza todos os dados do dashboard

## 📊 Interpretando os Dados

### Métricas Importantes

**Retorno Total**
- Positivo = Lucro
- Negativo = Prejuízo

**Sharpe Ratio**
- > 1.0 = Bom
- > 2.0 = Excelente
- < 0 = Ruim

**Max Drawdown**
- Quanto o portfólio caiu do pico
- Menor é melhor

**Win Rate**
- % de trades lucrativos
- > 50% = Bom

### Atividade dos Agentes

**Propostas do TraderAgent**
- Quantas oportunidades foram identificadas
- Mais = Agente mais ativo

**Avaliações do RiskAgent**
- Quantas propostas foram avaliadas
- APPROVE = Aprovadas
- REJECT = Rejeitadas
- MODIFY = Modificadas

**Execuções**
- Quantas ordens foram realmente executadas
- Indica atividade real do sistema

## 🐛 Troubleshooting

### Dashboard não abre
```bash
# Verificar se Streamlit está instalado
pip install streamlit plotly requests

# Tentar novamente
streamlit run dashboard_central.py
```

### API não responde
```bash
# Verificar se API está rodando
python test_api_simple.py

# Se não estiver, iniciar
python run_api.py
```

### Dados não aparecem
1. Execute um backtest primeiro: `python executar_backtest_30_acoes.py`
2. Clique em "🔄 Atualizar Dados" no sidebar
3. Verifique se há logs em `logs/decisions-*.jsonl`

### Gráficos não carregam
- Verifique se há dados de backtest
- Execute um backtest primeiro
- Verifique conexão com API

## 📝 Exemplo de Uso Completo

```bash
# Terminal 1: API
python run_api.py

# Terminal 2: Dashboard
streamlit run dashboard_central.py

# Terminal 3: Executar backtest
python executar_backtest_30_acoes.py

# Depois, visualize no dashboard:
# http://localhost:8501
```

## ✅ Checklist

- [ ] API rodando (porta 5000)
- [ ] Dashboard rodando (porta 8501)
- [ ] Backtest executado
- [ ] Dados aparecendo no dashboard
- [ ] Agentes gerando propostas
- [ ] Métricas sendo calculadas

## 🎉 Pronto!

Agora você tem uma visão completa do sistema em uma única tela!

