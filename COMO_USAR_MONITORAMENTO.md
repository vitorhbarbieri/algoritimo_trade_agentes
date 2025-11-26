# 🚀 Como Usar o Monitoramento em Tempo Real

## ✅ O Que Foi Implementado

### Backend Funcionando Agora:
1. ✅ **MonitoringService** - Escaneia mercado continuamente
2. ✅ **MarketMonitor** - Busca 5 tipos de oportunidades:
   - Volatility Arbitrage
   - Pairs Trading
   - Spread Arbitrage
   - Momentum
   - Mean Reversion
3. ✅ **Suporte a Cripto** - Binance API integrada
4. ✅ **Endpoints da API** - Controle via REST

### Dashboard Melhorado:
- ✅ Status do monitoramento (ATIVO/INATIVO)
- ✅ Botões para iniciar/parar
- ✅ Scan manual
- ✅ Oportunidades encontradas em tempo real
- ✅ Atividade dos agentes

## 🎯 Como Funciona o Monitoramento

### Teorias e Assimetrias Testadas:

#### 1. **Volatility Arbitrage** 🔄
- **O que busca:** Opções com IV diferente da volatilidade histórica
- **Assimetria:** Mispricing entre preço de mercado e modelo teórico
- **Exemplo:** AAPL spot $150, opção CALL com IV 40% (histórica 25%) → Vender opção

#### 2. **Pairs Trading** 📊
- **O que busca:** Dois ativos relacionados com relação estável que se desviou
- **Assimetria:** Desvio temporário tende a reverter
- **Exemplo:** ITUB4/BBDC4 ratio acima da média → Vender ITUB4, comprar BBDC4

#### 3. **Spread Arbitrage** 💰
- **O que busca:** Spreads bid-ask anormalmente altos
- **Assimetria:** Oportunidade de market making
- **Exemplo:** Spread de 1% quando normal é 0.1%

#### 4. **Momentum** 📈
- **O que busca:** Movimentos fortes com volume alto
- **Assimetria:** Tendências persistem no curto prazo
- **Exemplo:** Preço subindo 3% com volume 2x média → Comprar

#### 5. **Mean Reversion** 🔄
- **O que busca:** Desvios extremos da média
- **Assimetria:** Movimentos exagerados revertem
- **Exemplo:** Preço 3 desvios abaixo da média → Comprar

## 🚀 Como Usar Agora

### Passo 1: Reiniciar API (Importante!)
```bash
# Parar API atual (Ctrl+C)
# Reiniciar
python run_api.py
```

### Passo 2: Abrir Dashboard
```bash
streamlit run dashboard_central.py
```

### Passo 3: Iniciar Monitoramento

**No Dashboard:**
1. Abra a sidebar (lado esquerdo)
2. Role até "🔍 Monitoramento do Mercado"
3. Clique em "▶️ Iniciar Monitoramento"
4. Aguarde alguns minutos
5. Veja oportunidades aparecendo!

**Ou via API:**
```bash
curl -X POST http://localhost:5000/monitoring/start
```

### Passo 4: Ver Oportunidades

**No Dashboard:**
- Aba "📊 Visão Geral"
- Veja seção "🎯 Oportunidades Recentes"
- Veja "🕐 Atividade Recente"

**Ou via API:**
```bash
curl http://localhost:5000/monitoring/status
```

## 💰 Adicionar Criptoativos (Binance)

### 1. Instalar CCXT
```bash
pip install ccxt
```

### 2. Configurar Binance

Edite `config.json`:
```json
{
  "enable_crypto": true,
  "binance_api_key": "sua_chave_aqui",
  "binance_api_secret": "seu_secret_aqui",
  "binance_sandbox": true,
  "monitored_crypto": [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT",
    "XRP/USDT", "DOT/USDT", "DOGE/USDT", "AVAX/USDT", "MATIC/USDT"
  ]
}
```

**⚠️ IMPORTANTE:** Use `sandbox: true` para testes!

### 3. Obter Chaves da Binance

1. Acesse: https://www.binance.com/pt/my/settings/api-management
2. Crie API Key (testnet para sandbox)
3. Copie Key e Secret
4. Cole em `config.json`

### 4. Reiniciar Sistema

```bash
# Parar API
# Reiniciar
python run_api.py
```

## 📊 O Que Deveria Estar Acontecendo

### Com Monitoramento Ativo:

1. **A cada 5 minutos:**
   - ✅ Busca dados de 30 ações
   - ✅ Escaneia oportunidades
   - ✅ Gera propostas
   - ✅ Registra em logs

2. **No Dashboard você vê:**
   - ✅ Status: "✅ Monitoramento ATIVO"
   - ✅ Último scan realizado
   - ✅ Oportunidades encontradas
   - ✅ Propostas geradas
   - ✅ Atividade dos agentes

3. **Nos Logs:**
   - ✅ Cada oportunidade encontrada
   - ✅ Cada proposta gerada
   - ✅ Cada avaliação do RiskAgent

## 🔍 Verificar se Está Funcionando

### 1. Ver Status
```bash
curl http://localhost:5000/monitoring/status
```

Deve retornar:
```json
{
  "status": "success",
  "monitoring": {
    "is_running": true,
    "last_scan_time": "2025-11-23T...",
    "opportunities_found": 5,
    "proposals_generated": 3
  }
}
```

### 2. Ver Logs
```bash
Get-Content logs\decisions-*.jsonl -Tail 20
```

Deve mostrar:
- `trader_proposal` - Propostas geradas
- `risk_evaluation` - Avaliações
- `execution` - Execuções

### 3. Ver Dashboard
- Sidebar → "Monitoramento do Mercado"
- Deve mostrar: "✅ Monitoramento ATIVO"
- Deve mostrar oportunidades

## 🐛 Troubleshooting

### Monitoramento não inicia
1. Verifique se API está rodando
2. Verifique logs da API
3. Tente scan manual primeiro

### Nenhuma oportunidade encontrada
1. Normal se mercado está estável
2. Tente executar backtest primeiro
3. Verifique se dados estão sendo buscados

### Erro com Binance
1. Verifique se CCXT está instalado
2. Verifique chaves da API
3. Use sandbox primeiro

## 📝 Próximos Passos

1. ✅ Monitoramento implementado
2. ✅ Dashboard melhorado
3. ✅ Suporte a cripto adicionado
4. ⏳ Testar em produção
5. ⏳ Adicionar alertas
6. ⏳ Execução real (quando necessário)

## 🎉 Resumo

**Agora você tem:**
- ✅ Monitoramento contínuo do mercado
- ✅ Busca automática de oportunidades
- ✅ 5 estratégias diferentes
- ✅ Suporte a 30 ações + 10 criptos
- ✅ Dashboard mostrando tudo em tempo real
- ✅ Controle total via API ou Dashboard

**Para começar:**
1. Reinicie API: `python run_api.py`
2. Abra Dashboard: `streamlit run dashboard_central.py`
3. Clique em "▶️ Iniciar Monitoramento"
4. Veja oportunidades aparecendo!

