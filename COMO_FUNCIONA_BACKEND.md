# 🔧 Como Funciona o Backend - Monitoramento e Agentes

## 📊 Visão Geral do Sistema

### Fluxo de Funcionamento

```
1. MARKET MONITOR → Escaneia mercado continuamente
   ↓
2. Identifica Oportunidades (assimetrias)
   ↓
3. TRADER AGENT → Gera propostas de trading
   ↓
4. RISK AGENT → Avalia e aprova/rejeita
   ↓
5. EXECUTION SIMULATOR → Executa ordens
   ↓
6. PORTFOLIO MANAGER → Atualiza posições
   ↓
7. DASHBOARD → Mostra tudo em tempo real
```

## 🎯 Teorias e Assimetrias Testadas

### 1. Volatility Arbitrage (Vol Arb)
**Teoria:** Opções com IV muito diferente da volatilidade histórica representam oportunidades.

**Assimetria:** Mispricing entre preço de mercado e modelo teórico (Black-Scholes).

**Como funciona:**
- Calcula volatilidade histórica do ativo
- Compara com IV implícita das opções
- Identifica opções com IV muito alta/baixa
- Gera proposta de compra/venda da opção + hedge no spot

**Exemplo:**
- AAPL spot: $150
- Opção CALL $150 com IV de 40% (histórica: 25%)
- Oportunidade: Vender opção (IV inflada) + comprar spot (hedge)

### 2. Pairs Trading / Statistical Arbitrage
**Teoria:** Dois ativos relacionados têm relação estável de preços (cointegração).

**Assimetria:** Desvio temporário da relação histórica tende a reverter.

**Como funciona:**
- Calcula ratio histórico entre dois ativos (ex: ITUB4/BBDC4)
- Identifica quando ratio está muito acima/abaixo da média
- Gera proposta: vender o caro + comprar o barato
- Espera reversão à média

**Exemplo:**
- ITUB4: R$ 30, BBDC4: R$ 20
- Ratio histórico: 1.4
- Ratio atual: 1.6 (ITUB4 caro demais)
- Oportunidade: Vender ITUB4 + Comprar BBDC4

### 3. Spread Arbitrage
**Teoria:** Spread bid-ask anormalmente alto indica baixa liquidez.

**Assimetria:** Oportunidade de fazer market making.

**Como funciona:**
- Monitora spreads bid-ask em tempo real
- Identifica spreads acima do normal
- Gera proposta de market making

### 4. Momentum Trading
**Teoria:** Tendências persistem no curto prazo (inércia de preços).

**Assimetria:** Movimentos fortes com volume alto tendem a continuar.

**Como funciona:**
- Calcula momentum de curto prazo (5 dias)
- Identifica volume spikes
- Gera proposta na direção do momentum

### 5. Mean Reversion
**Teoria:** Preços retornam à média após desvios extremos.

**Assimetria:** Movimentos exagerados tendem a reverter.

**Como funciona:**
- Calcula média móvel (SMA 20)
- Identifica desvios extremos (Z-score > 2)
- Gera proposta contrária ao movimento

## 🤖 Como os Agentes Funcionam

### TraderAgent (Agente Criativo)
**Responsabilidade:** Gerar propostas de trading baseadas em oportunidades.

**Processo:**
1. Recebe dados de mercado (spot, opções, futuros)
2. Escaneia oportunidades usando MarketMonitor
3. Para cada oportunidade encontrada:
   - Calcula tamanho de posição
   - Define preço limite
   - Cria OrderProposal
4. Envia propostas para RiskAgent

**Estratégias Ativas:**
- ✅ Volatility Arbitrage
- ✅ Pairs Trading
- ⏳ Spread Arbitrage (em desenvolvimento)
- ⏳ Momentum (em desenvolvimento)
- ⏳ Mean Reversion (em desenvolvimento)

### RiskAgent (Agente Controlador)
**Responsabilidade:** Validar, modificar ou rejeitar propostas.

**Processo:**
1. Recebe proposta do TraderAgent
2. Verifica limites:
   - Exposição máxima por ativo
   - Exposição total do portfólio
   - Greeks agregados (Delta, Gamma, Vega, Theta)
   - Tamanho máximo de posição
3. Decisão:
   - **APPROVE:** Proposta aprovada
   - **MODIFY:** Modifica quantidade/preço
   - **REJECT:** Rejeita proposta

**Limites Configuráveis:**
- Max exposure: 50% do NAV
- Max delta: 1000
- Max gamma: 500
- Max vega: 1000
- Max position size: R$ 10.000

### ExecutionSimulator
**Responsabilidade:** Simular execução realista de ordens.

**Processo:**
1. Recebe ordem aprovada
2. Aplica slippage (baseado em volume)
3. Aplica comissões
4. Verifica fill rate (95% por padrão)
5. Gera Fill

## 📈 Backtest - Como Funciona

### Processo de Backtest

1. **Carregamento de Dados**
   - Spot: Preços históricos
   - Opções: Chains históricas (se disponível)
   - Futuros: Dados históricos (se disponível)

2. **Simulação Dia a Dia**
   - Para cada dia do período:
     - Prepara dados de mercado
     - TraderAgent gera propostas
     - RiskAgent avalia
     - ExecutionSimulator executa ordens aprovadas
     - PortfolioManager atualiza posições
     - Cria snapshot do portfólio

3. **Cálculo de Métricas**
   - Retorno total
   - Sharpe Ratio
   - Max Drawdown
   - Volatilidade
   - Win Rate

### Walk-Forward Backtest
- Treina em janela de 60 dias
- Testa em janela de 20 dias
- Move janela em passos de 5 dias
- Gera métricas para cada janela

## 🔍 Monitoramento em Tempo Real

### O Que Deveria Estar Acontecendo

1. **Market Monitor Escaneando**
   - A cada X minutos (configurável)
   - Busca oportunidades em todas as ações monitoradas
   - Registra oportunidades encontradas

2. **TraderAgent Gerando Propostas**
   - Quando encontra oportunidade
   - Gera proposta com detalhes
   - Loga em `logs/decisions-*.jsonl`

3. **RiskAgent Avaliando**
   - Avalia cada proposta
   - Loga decisão (APPROVE/MODIFY/REJECT)
   - Razão da decisão

4. **Execuções**
   - Quando proposta é aprovada
   - ExecutionSimulator executa
   - Loga execução

### Como Verificar se Está Funcionando

1. **Ver Logs:**
   ```bash
   Get-Content logs\decisions-*.jsonl -Tail 20
   ```

2. **Ver Dashboard:**
   - Aba "Atividade dos Agentes"
   - Deve mostrar propostas geradas
   - Deve mostrar avaliações

3. **Ver API:**
   ```bash
   curl http://localhost:5000/agents/activity
   ```

## 🚀 Adicionando Criptoativos

### Configuração

1. **Instalar CCXT:**
   ```bash
   pip install ccxt
   ```

2. **Configurar Binance:**
   - Editar `config.json`
   - Adicionar `binance_api_key` e `binance_api_secret`
   - Definir `binance_sandbox: true` para testes

3. **Adicionar Criptos Monitoradas:**
   - Lista em `monitored_crypto`
   - Exemplo: `["BTC/USDT", "ETH/USDT"]`

### Estratégias para Cripto

1. **Arbitragem entre Exchanges**
   - Compara preços entre Binance e outras
   - Identifica diferenças de preço

2. **Funding Rate Arbitrage**
   - Monitora funding rates de futuros
   - Identifica oportunidades de carry trade

3. **Volatility Trading**
   - Similar ao Vol Arb de ações
   - Usa opções de cripto (se disponível)

## 📊 Próximos Passos

1. ✅ Implementar MarketMonitor completo
2. ✅ Adicionar suporte a cripto
3. ⏳ Melhorar visualização no dashboard
4. ⏳ Adicionar alertas em tempo real
5. ⏳ Implementar execução real (quando necessário)

