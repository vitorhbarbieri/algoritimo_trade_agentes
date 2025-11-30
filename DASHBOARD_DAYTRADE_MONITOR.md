# 📈 DayTrade Monitor - Dashboard de Acompanhamento Visual

## 🎯 Objetivo

Uma aba dedicada no Dashboard Central para monitoramento visual em tempo real da atividade do agente DayTrade.

## ✨ Funcionalidades Implementadas

### 1. **Status do Mercado em Tempo Real**
- ✅ Indicador visual do status (Aberto/Fechado/Pré-Mercado/Pós-Mercado)
- 🕐 Horário B3 atualizado
- ⏰ Indicador se está em horário de trading

### 2. **Estatísticas Principais (Últimas 24h)**
- 📊 Total de propostas geradas
- ✅ Propostas aprovadas
- ❌ Propostas rejeitadas
- 📈 Taxa de aprovação
- 💼 Posições abertas
- 📡 Capturas de dados recentes

### 3. **Gráficos Visuais**
- 📊 Gráfico de barras: Propostas Aprovadas vs Rejeitadas
- 🎯 Gauge: Taxa de Aprovação (indicador visual)
- 📈 Gráfico de PnL por posição

### 4. **Propostas Recentes**
- 💡 Lista das últimas 10 propostas geradas
- Detalhes: símbolo, lado, quantidade, preço, timestamp

### 5. **Capturas de Dados de Mercado**
- 📡 Última captura realizada
- 📋 Lista de tickers monitorados
- 📊 Tabela com últimas 15 capturas (ticker, tipo, preço, volume)

### 6. **Posições Abertas**
- 💼 Lista de posições abertas relacionadas ao DayTrade
- 📊 Detalhes: símbolo, lado, quantidade, preço médio, preço atual, PnL
- 📈 Gráfico de PnL não realizado por posição

### 7. **Auto-Refresh**
- 🔄 Atualização automática a cada 3 segundos
- ✅ Checkbox para ativar/desativar

## 🚀 Como Usar

### 1. Iniciar a API
```bash
python api_server.py
```

### 2. Iniciar o Dashboard
```bash
streamlit run dashboard_central.py
```

### 3. Acessar a Aba DayTrade Monitor
- Abra o dashboard no navegador
- Clique na aba **"📈 DayTrade Monitor"**
- Ative o "Auto-refresh" para atualização automática

## 📊 Endpoint da API

### `/daytrade/monitoring` (GET)

Retorna dados completos de monitoramento:

```json
{
  "status": "success",
  "market_status": {
    "status": "TRADING",
    "b3_time": "2025-11-29T14:30:00-03:00",
    "is_trading_hours": true,
    "is_pre_market": false
  },
  "statistics": {
    "total_proposals_24h": 15,
    "approved_proposals": 8,
    "rejected_proposals": 7,
    "approval_rate": 53.3,
    "open_positions": 5,
    "recent_captures": 20,
    "tickers_monitored": 30
  },
  "recent_proposals": [...],
  "recent_evaluations": [...],
  "recent_captures": [...],
  "open_positions": [...],
  "recent_tickers": ["ABEV3.SA", "B3SA3.SA", ...],
  "last_capture_time": "2025-11-29T14:25:00-03:00"
}
```

## 🎨 Visualizações

### Status do Mercado
- **Verde** ✅: Mercado Aberto
- **Azul** ⏰: Pré-Mercado
- **Amarelo** 🌅: Pós-Mercado
- **Vermelho** 🔒: Mercado Fechado

### Gráficos
1. **Propostas Aprovadas vs Rejeitadas**: Gráfico de barras empilhadas
2. **Taxa de Aprovação**: Gauge com cores dinâmicas (verde ≥50%, vermelho <50%)
3. **PnL por Posição**: Gráfico de barras com escala de cores (vermelho → verde)

## 🔄 Atualização Automática

O dashboard atualiza automaticamente a cada 3 segundos quando o "Auto-refresh" está ativado. Isso garante que você veja:

- ✅ Novas propostas sendo geradas
- ✅ Novas capturas de dados
- ✅ Mudanças no status do mercado
- ✅ Atualizações de posições e PnL

## 📋 Dados Exibidos

### Propostas Recentes
- Símbolo
- Lado (BUY/SELL)
- Quantidade
- Preço
- Timestamp
- Estratégia

### Capturas de Dados
- Ticker
- Tipo de dado (spot/options)
- Último preço
- Volume
- Timestamp da captura

### Posições Abertas
- Símbolo
- Lado
- Quantidade
- Preço médio
- Preço atual
- PnL não realizado

## ✅ Benefícios

1. **Visibilidade Total**: Veja tudo que o DayTrade está fazendo em tempo real
2. **Análise Rápida**: Métricas e gráficos facilitam a análise de performance
3. **Monitoramento Contínuo**: Auto-refresh mantém você atualizado
4. **Diagnóstico Rápido**: Identifique problemas rapidamente através dos indicadores visuais

## 🐛 Troubleshooting

### Dashboard não carrega dados:
- Verifique se a API está rodando (`python api_server.py`)
- Verifique se há dados no banco de dados
- Recarregue a página (F5)

### Auto-refresh não funciona:
- Verifique se o checkbox está marcado
- Verifique se há erros no console do navegador
- Tente desativar e reativar

### Dados não atualizam:
- Verifique se o `MonitoringService` está rodando
- Verifique os logs para erros
- Execute `python monitorar_daytrade.py` para diagnóstico

---

**Última atualização**: 29/11/2025
**Status**: ✅ Implementado e Funcionando

