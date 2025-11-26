# Changelog

## [1.1.0] - 2024-11-23

### Adicionado
- **Módulo de Sizing** (`src/sizing.py`):
  - Fixed Fraction sizing
  - Risk-Based sizing
  - Kelly Criterion (com quarter Kelly)
  - Risk Parity sizing
  - Adaptive sizing (combina métodos)

- **Novas Estratégias** (`src/strategies.py`):
  - Momentum Strategy
  - Mean Reversion Strategy
  - Breakout Strategy
  - RSI Strategy
  - MACD Strategy

- **Adaptadores de Broker** (`src/broker_adapters.py`):
  - Mock Broker Adapter (para desenvolvimento)
  - Interactive Brokers Adapter (stub)
  - CCXT Adapter para exchanges (stub)
  - Factory function para criar adaptadores

- **Backtest Paralelo** (`src/backtest_parallel.py`):
  - Suporte para paralelização com multiprocessing
  - Integração com squad-bmad (quando disponível)
  - Execução paralela de janelas walk-forward

- **Exemplos Avançados** (`examples_advanced.py`):
  - Exemplos de uso de sizing
  - Exemplos de novas estratégias
  - Exemplos de integração com brokers

### Melhorado
- README atualizado com novas funcionalidades
- Requirements.txt atualizado com dependências opcionais
- Documentação de exemplos avançados

## [1.0.0] - 2024-11-23

### Adicionado
- Sistema completo de trading com agentes cooperativos
- TraderAgent com estratégias Vol Arb e Pairs
- RiskAgent com validação e kill switch
- ExecutionSimulator com slippage e comissões
- BacktestEngine com walk-forward
- Dashboard Streamlit interativo
- Testes unitários
- Logging estruturado em JSON

