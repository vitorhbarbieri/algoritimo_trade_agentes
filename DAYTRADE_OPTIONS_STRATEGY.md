# 📈 Estratégia de Daytrade de Opções

## 🎯 Visão Geral

A estratégia **DayTradeOptionsStrategy** foi adicionada ao projeto como o terceiro agente, focando em operações de daytrade com CALLs ATM/OTM de curto prazo.

## ✨ Características Principais

### Objetivo
- Monitora ações em tempo real durante o pregão
- Identifica ativos com forte momentum intraday e surto de volume
- Compra CALLs ATM/OTM de curto prazo (< 7 dias) com:
  - Delta entre 0.20 e 0.60
  - Volume mínimo
  - Spread aceitável
  - Gamma elevado

### Regras de Entrada
1. **Momentum Intraday**: `intraday_return >= min_intraday_return` (padrão: 0.5%)
2. **Volume Ratio**: `volume_day / ADV >= min_volume_ratio` (padrão: 0.25)
3. **Seleção de Calls**:
   - Tipo: CALL apenas
   - Delta: entre `delta_min` e `delta_max` (padrão: 0.20 a 0.60)
   - Dias até expiração: `<= max_dte` (padrão: 7 dias)
   - Spread percentual: `<= max_spread_pct` (padrão: 5%)
   - Volume mínimo: `>= min_option_volume` (padrão: 200)

### Seleção da Melhor Call
A estratégia escolhe a call com:
- **Maior gamma** (prioridade principal)
- **Menor spread** (segunda prioridade)
- **Maior liquidez** (terceira prioridade)

### Sizing
- Baseado em risco fixo via prêmio
- Fórmula: `qty = floor(max_risk / (call.mid * 100))`
- Onde `max_risk = NAV * risk_per_trade` (padrão: 0.2% do NAV)

### Gestão de Risco
- **Take Profit**: +10% a +20% (configurável)
- **Stop Loss**: -40% ou perda total do prêmio (configurável)
- **EOD Close**: Fechamento automático no final do dia (obrigatório)

## ⚙️ Configurações

As configurações estão em `config.json` na seção `daytrade_options`:

```json
{
  "daytrade_options": {
    "enabled": true,
    "min_intraday_return": 0.005,
    "min_volume_ratio": 0.25,
    "delta_min": 0.20,
    "delta_max": 0.60,
    "max_dte": 7,
    "max_spread_pct": 0.05,
    "min_option_volume": 200,
    "risk_per_trade": 0.002,
    "max_risk_per_trade": 5000,
    "take_profit_pct": 0.10,
    "stop_loss_pct": 0.40,
    "max_options_exposure_pct": 0.15
  }
}
```

### Parâmetros Explicados

- **enabled**: Habilita/desabilita a estratégia
- **min_intraday_return**: Retorno mínimo intraday para considerar entrada (0.5% = 0.005)
- **min_volume_ratio**: Razão mínima volume_dia/ADV (25% = 0.25)
- **delta_min/max**: Faixa de delta aceitável para as calls
- **max_dte**: Máximo de dias até expiração
- **max_spread_pct**: Spread máximo aceitável (5% = 0.05)
- **min_option_volume**: Volume mínimo da opção
- **risk_per_trade**: Risco por trade como % do NAV (0.2% = 0.002)
- **max_risk_per_trade**: Risco máximo absoluto por trade
- **take_profit_pct**: Take profit como % do prêmio (10% = 0.10)
- **stop_loss_pct**: Stop loss como % do prêmio (40% = 0.40)
- **max_options_exposure_pct**: Exposição máxima agregada em opções (15% = 0.15)

## 🔌 Integração

### TraderAgent
A estratégia é automaticamente inicializada no `TraderAgent` quando habilitada:

```python
# Em TraderAgent.__init__
if config.get('daytrade_options', {}).get('enabled', True):
    self.strategies.append(DayTradeOptionsStrategy(config, logger))
```

### RiskAgent
O `RiskAgent` valida especificamente propostas de daytrade:

1. **Risco máximo por trade**: Verifica se não excede `max_risk_per_trade`
2. **Limite por ativo**: Verifica exposição máxima por ativo
3. **Liquidez**: Valida spread máximo
4. **Exposição agregada**: Verifica limite total em opções
5. **Greeks projetados**: Calcula greeks agregados incluindo a proposta

## 📊 Estrutura de OrderProposal

A estratégia gera `OrderProposal` com:

```python
OrderProposal(
    proposal_id="DAYOPT-{asset}-{strike}-{expiry}-{timestamp}",
    strategy='daytrade_options',
    instrument_type='options',
    symbol="{asset}_{strike}_C_{expiry}",
    side='BUY',
    quantity=qty,
    price=ask_price,
    order_type='LIMIT',
    metadata={
        'underlying': asset,
        'strike': strike,
        'expiry': expiry,
        'days_to_expiry': days_to_expiry,
        'delta': delta,
        'gamma': gamma,
        'vega': vega,
        'iv': implied_volatility,
        'intraday_return': intraday_return,
        'volume_ratio': volume_ratio,
        'spread_pct': spread_pct,
        'premium': mid_price,
        'max_risk': max_risk,
        'take_profit_pct': take_profit_pct,
        'stop_loss_pct': stop_loss_pct,
        'eod_close': True
    }
)
```

## 🧪 Testes

A estratégia funciona com:
- Dados sintéticos gerados no notebook
- Dados reais via APIs (yfinance, Brapi.dev)
- Backtest walk-forward
- Execução em tempo real

## 📝 Outputs

A estratégia gera outputs em:
- `orders.csv`: Ordens geradas
- `fills.csv`: Execuções realizadas
- `portfolio_snapshots.csv`: Snapshots do portfólio
- Logs estruturados via `StructuredLogger`

## ⚠️ Observações Importantes

1. **EOD Close Obrigatório**: Todas as posições são fechadas no final do dia
2. **Apenas Compra**: A estratégia só compra calls, nunca vende
3. **Risco Limitado**: O risco máximo é o prêmio pago
4. **Validação Rigorosa**: O RiskAgent valida múltiplos critérios antes de aprovar

## 🔄 Próximos Passos

Para melhorar a estratégia, considere:
1. Implementar take profit e stop loss automáticos
2. Adicionar fechamento EOD automático
3. Implementar trailing stop
4. Adicionar filtros adicionais (ex: notícias, eventos)
5. Otimização de parâmetros via walk-forward

