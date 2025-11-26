# 📊 Fluxo de Captura de Preços e Registro de Ordens - DayTrade Agent

## 🔄 Visão Geral do Fluxo

```
MonitoringService → Market Data API → DayTradeOptionsStrategy → OrderProposal → StructuredLogger → Logs JSON
```

## 1️⃣ CAPTURA DE PREÇOS (Price Collection)

### 1.1. Inicialização do MonitoringService

**Arquivo:** `src/monitoring_service.py`

```python
# Linha 49: Criação da API de dados de mercado
self.stock_api = create_market_data_api('yfinance')
```

### 1.2. Escaneamento Periódico do Mercado

**Método:** `MonitoringService.scan_market()` (linhas 64-163)

**Frequência:** A cada X segundos (padrão: 300s = 5 minutos)

**Processo:**

1. **Buscar dados SPOT (ações):**
   ```python
   # Linha 77: Busca dados históricos dos últimos 30 dias
   spot_df = self.stock_api.fetch_spot_data(tickers[:10], start_date, end_date)
   ```

2. **Buscar dados de OPÇÕES:**
   ```python
   # Linha 81: Busca chain de opções para o primeiro ticker
   options_df = self.stock_api.fetch_options_chain(tickers[0], start_date, end_date)
   ```

3. **Preparar estrutura de dados:**
   ```python
   # Linhas 86-100: Organiza dados em formato esperado pela estratégia
   market_data = {
       'spot': {
           'AAPL': {
               'open': 150.00,
               'close': 152.50,
               'high': 153.00,
               'low': 149.50,
               'volume': 1000000
           },
           ...
       },
       'options': {
           'AAPL': [
               {
                   'underlying': 'AAPL',
                   'strike': 150,
                   'expiry': '2025-01-25',
                   'option_type': 'C',
                   'bid': 2.50,
                   'ask': 2.60,
                   'volume': 500,
                   ...
               },
               ...
           ]
       }
   }
   ```

### 1.3. Fontes de Dados

**API Principal:** `yfinance` (Yahoo Finance)

**Fallbacks (em ordem de prioridade):**
1. Yahoo Chart API v8
2. Yahoo Quote API v7
3. brapi.dev
4. yfinance direto

**Dados Coletados:**

**Para SPOT:**
- `open`: Preço de abertura do dia
- `close`: Preço de fechamento/último preço
- `high`: Máxima do dia
- `low`: Mínima do dia
- `volume`: Volume negociado no dia
- `adv`: Average Daily Volume (volume médio diário)

**Para OPÇÕES:**
- `strike`: Preço de exercício
- `expiry`: Data de expiração
- `option_type`: Tipo ('C' para CALL, 'P' para PUT)
- `bid`: Preço de compra (lado vendedor)
- `ask`: Preço de venda (lado comprador)
- `mid`: Preço médio (bid + ask) / 2
- `volume`: Volume negociado
- `open_interest`: Interesse aberto
- `implied_volatility`: Volatilidade implícita

## 2️⃣ PROCESSAMENTO PELA ESTRATÉGIA (DayTradeOptionsStrategy)

### 2.1. Entrada de Dados

**Arquivo:** `src/agents.py` - Classe `DayTradeOptionsStrategy`

**Método:** `generate(nav, timestamp, market_data)` (linhas 108-313)

### 2.2. Filtros Aplicados

#### Filtro 1: Momentum Intraday
```python
# Linhas 128-138
open_price = spot_info.get('open', 0)
last_price = spot_info.get('close', spot_info.get('last', 0))
intraday_return = (last_price / open_price) - 1

# Deve ser >= min_intraday_return (padrão: 0.5%)
if intraday_return < min_intraday_return:
    continue
```

#### Filtro 2: Volume Ratio
```python
# Linhas 141-152
volume_day = spot_info.get('volume', 0)
adv = spot_info.get('adv', spot_info.get('avg_volume', volume_day))
volume_ratio = volume_day / adv

# Deve ser >= min_volume_ratio (padrão: 0.25 = 25% do volume médio)
if volume_ratio < min_volume_ratio:
    continue
```

#### Filtro 3: Opções CALL Viáveis
```python
# Linhas 180-241: Para cada opção na chain
# Verifica:
- Tipo = 'C' (CALL)
- DTE <= max_dte (padrão: 7 dias)
- delta_min <= delta <= delta_max (padrão: 0.20 a 0.60)
- spread_pct <= max_spread_pct (padrão: 5%)
- volume >= min_option_volume (padrão: 200)
```

#### Filtro 4: Seleção da Melhor CALL
```python
# Linhas 247-250: Seleciona por:
best_call = max(
    viable_calls,
    key=lambda o: (o['gamma'], -o['spread_pct'], o['volume'])
)
# Prioridade: Maior gamma, menor spread, maior volume
```

### 2.3. Cálculo de Sizing

```python
# Linhas 253-263
risk_per_trade = cfg.get('risk_per_trade', 0.002)  # 0.2% do NAV
max_risk = nav * risk_per_trade
premium_per_contract = best_call['mid'] * 100  # Opções multiplicam por 100
qty = int(max_risk / premium_per_contract)
```

## 3️⃣ GERAÇÃO DE ORDERPROPOSAL

### 3.1. Criação da Proposta

**Linhas 265-295:** Criação do objeto `OrderProposal`

```python
proposal = OrderProposal(
    proposal_id=f"DAYOPT-{asset}-{strike}-{expiry}-{timestamp}",
    strategy='daytrade_options',
    instrument_type='options',
    symbol=f"{asset}_{strike}_C_{expiry}",
    side='BUY',
    quantity=qty,
    price=best_call['ask'],  # Preço de compra
    order_type='LIMIT',
    metadata={
        'underlying': asset,
        'strike': best_call['strike'],
        'expiry': best_call['expiry'].isoformat(),
        'days_to_expiry': best_call['days_to_expiry'],
        'delta': best_call['delta'],
        'gamma': best_call['gamma'],
        'vega': best_call['vega'],
        'iv': best_call['iv'],
        'intraday_return': float(intraday_return),
        'volume_ratio': float(volume_ratio),
        'spread_pct': float(best_call['spread_pct']),
        'premium': float(best_call['mid']),
        'max_risk': float(max_risk),
        'take_profit_pct': cfg.get('take_profit_pct', 0.10),  # 10%
        'stop_loss_pct': cfg.get('stop_loss_pct', 0.40),     # 40%
        'eod_close': True  # Fechar no final do dia
    }
)
```

## 4️⃣ REGISTRO DE ORDENS (Logging)

### 4.1. Logging Estruturado

**Arquivo:** `src/utils.py` - Classe `StructuredLogger`

**Método:** `log_trader_proposal()` (linhas 39-45)

### 4.2. Registro da Proposta

**Linhas 299-306:** Quando uma proposta é gerada

```python
if self.logger:
    self.logger.log_trader_proposal(proposal_id, 'daytrade_options', {
        'asset': asset,
        'intraday_return': intraday_return,
        'volume_ratio': volume_ratio,
        'strike': best_call['strike'],
        'delta': best_call['delta']
    })
```

### 4.3. Formato do Log

**Arquivo de Log:** `logs/trader_proposals.jsonl` (ou similar)

**Formato JSON:**
```json
{
  "timestamp": "2025-01-20T14:30:00",
  "type": "trader_proposal",
  "proposal_id": "DAYOPT-AAPL-150-20250125-1737384000",
  "strategy": "daytrade_options",
  "asset": "AAPL",
  "intraday_return": 0.008,
  "volume_ratio": 1.5,
  "strike": 150.0,
  "delta": 0.45
}
```

### 4.4. Localização dos Logs

**Diretório:** `logs/`

**Arquivos gerados:**
- `trader_proposals.jsonl` - Propostas geradas pelo TraderAgent
- `risk_evaluations.jsonl` - Avaliações do RiskAgent
- `executions.jsonl` - Execuções de ordens
- `decisions.jsonl` - Decisões gerais
- `errors.jsonl` - Erros do sistema

## 5️⃣ FLUXO COMPLETO (Resumo)

```
1. MonitoringService.scan_market() é chamado a cada 5 minutos
   ↓
2. Busca dados SPOT via stock_api.fetch_spot_data()
   - Preços: open, close, high, low
   - Volume: volume, adv
   ↓
3. Busca dados de OPÇÕES via stock_api.fetch_options_chain()
   - Strike, expiry, bid, ask, volume, IV
   ↓
4. Organiza dados em market_data dict
   ↓
5. Chama TraderAgent.generate_proposals(timestamp, market_data)
   ↓
6. DayTradeOptionsStrategy.generate() processa:
   - Filtra por momentum (intraday_return >= 0.5%)
   - Filtra por volume (volume_ratio >= 0.25)
   - Filtra opções CALL viáveis
   - Seleciona melhor opção (maior gamma)
   - Calcula sizing baseado em risco
   ↓
7. Gera OrderProposal com todos os metadados
   ↓
8. Registra no log via StructuredLogger.log_trader_proposal()
   - Salva em logs/trader_proposals.jsonl
   ↓
9. Envia notificação via UnifiedNotifier (Telegram/Discord/Email)
   ↓
10. Proposta vai para RiskAgent para validação
```

## 6️⃣ DADOS CAPTURADOS PARA DAYTRADE

### Dados SPOT (Ações):
- ✅ Preço de abertura (`open`)
- ✅ Preço atual/último (`close` ou `last`)
- ✅ Volume do dia (`volume`)
- ✅ Volume médio diário (`adv` ou `avg_volume`)

### Dados OPÇÕES:
- ✅ Strike price
- ✅ Data de expiração
- ✅ Bid/Ask/Mid
- ✅ Volume negociado
- ✅ Volatilidade implícita (IV)
- ✅ Greeks calculados (Delta, Gamma, Vega)

### Métricas Calculadas:
- ✅ `intraday_return`: (last_price / open_price) - 1
- ✅ `volume_ratio`: volume_day / adv
- ✅ `spread_pct`: (ask - bid) / mid
- ✅ `delta`, `gamma`, `vega`: Calculados via Black-Scholes

## 7️⃣ REGISTRO DE ORDENS SUGERIDAS

### Onde são registradas:

1. **Logs Estruturados (JSONL):**
   - Arquivo: `logs/trader_proposals.jsonl`
   - Formato: Uma linha JSON por proposta
   - Contém: proposal_id, strategy, asset, métricas

2. **Dashboard Central:**
   - Aba "🤖 Atividade dos Agentes"
   - Seção específica para DayTrade
   - Mostra: propostas, aprovações, métricas

3. **API REST:**
   - Endpoint: `GET /agents/activity`
   - Retorna: Lista de atividades recentes
   - Inclui: Propostas de daytrade

4. **Notificações:**
   - Telegram/Discord/Email
   - Enviadas quando proposta é gerada
   - Contém: Ativo, strike, delta, momentum

## 8️⃣ EXEMPLO PRÁTICO

### Cenário:
- AAPL abre a $150.00
- Durante o dia sobe para $152.50 (momentum de 1.67%)
- Volume do dia: 1.5M (vs ADV de 1M = ratio de 1.5x)
- Opção CALL $150 expira em 5 dias
- Delta: 0.45, Gamma: 0.02, Spread: 2%

### Processo:
1. ✅ Passa filtro de momentum (1.67% > 0.5%)
2. ✅ Passa filtro de volume (1.5x > 0.25x)
3. ✅ Opção passa todos os filtros
4. ✅ Selecionada como melhor opção
5. ✅ Calcula qty baseado em risco (ex: 10 contratos)
6. ✅ Gera OrderProposal
7. ✅ Registra no log
8. ✅ Envia notificação

### Log Gerado:
```json
{
  "timestamp": "2025-01-20T14:30:00",
  "type": "trader_proposal",
  "proposal_id": "DAYOPT-AAPL-150-20250125-1737384000",
  "strategy": "daytrade_options",
  "asset": "AAPL",
  "intraday_return": 0.0167,
  "volume_ratio": 1.5,
  "strike": 150.0,
  "delta": 0.45
}
```

## ✅ RESUMO

**Captura de Preços:**
- Via `yfinance` API (Yahoo Finance)
- Busca dados SPOT e OPÇÕES periodicamente
- Fallbacks automáticos se API principal falhar

**Registro de Ordens:**
- Logs estruturados em JSONL (`logs/trader_proposals.jsonl`)
- Dashboard central mostra atividades
- API REST expõe dados
- Notificações enviadas automaticamente

**Tudo é automatizado e registrado!** 🚀

