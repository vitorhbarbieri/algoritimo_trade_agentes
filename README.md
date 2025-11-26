# Algoritimo Trade Agente

Projeto de pesquisa/protótipo completo em Python para dois agentes cooperativos de trading (TraderAgent criativo + RiskAgent/Controller) com foco em ações, futuros e opções.

## Estrutura do Projeto

```
algoritimo_trade_agente/
├── src/
│   ├── __init__.py
│   ├── data_loader.py      # Geração/carregamento de dados
│   ├── pricing.py          # Black-Scholes e greeks
│   ├── agents.py           # TraderAgent e RiskAgent
│   ├── execution.py        # ExecutionSimulator
│   ├── backtest.py         # Engine de backtest
│   └── utils.py            # Logging e métricas
├── tests/
│   ├── test_pricing.py     # Testes de precificação
│   └── test_agents.py      # Testes de agentes
├── logs/                   # Logs JSON estruturados
├── output/                 # CSVs gerados
├── config.json            # Configurações
├── mvp_agents.ipynb       # Notebook principal
└── README.md
```

## Instalação

### Dependências

```bash
pip install -r requirements.txt
```

Isso instala:
- pandas, numpy, scipy, statsmodels, matplotlib, tqdm
- streamlit, plotly (para dashboard)
- yfinance, requests (para dados reais de mercado)

Opcional (para paralelização avançada):
```bash
pip install squad-bmad  # Se disponível
```

**Nota:** O projeto funciona sem squad-bmad, usando multiprocessing como fallback.

### Requisitos

- Python >= 3.10
- pandas, numpy, scipy, statsmodels, matplotlib, tqdm
- squad-bmad (opcional, para paralelização)

## Como Usar

### 🚀 Início Rápido (Recomendado)

**1. Iniciar API Server:**
```bash
# Windows
start_api.bat

# Linux/Mac
./start_api.sh
```

**2. Testar:**
```bash
python test_api.py
```

**3. Acessar Dashboard:**
```bash
streamlit run dashboard.py
```

Acesse:
- **API:** http://localhost:5000
- **Dashboard:** http://localhost:8501

Veja `INICIO_RAPIDO.md` para mais detalhes.

### 1. Executar o Notebook Principal

Abra e execute `mvp_agents.ipynb` do início ao fim. O notebook:

- Gera dados sintéticos (spot, futuros, opções)
- Implementa estratégias de trading
- Executa backtest walk-forward
- Gera métricas e gráficos
- Salva outputs em CSV

### 2. Usar Dados Reais de Mercado via APIs ⭐ NOVO

O projeto agora suporta busca automática de dados reais via APIs:

```python
from src.data_loader import DataLoader

data_loader = DataLoader()

# Buscar dados reais via yfinance (Yahoo Finance)
spot_df, futures_df, options_df = data_loader.load_from_api(
    tickers=['AAPL', 'MSFT'],
    start_date='2024-01-01',
    end_date='2024-12-31',
    api_type='yfinance'  # ou 'brapi' para ações brasileiras
)
```

**APIs Suportadas:**
- **yfinance**: Yahoo Finance (gratuito, sem API key)
- **Brapi.dev**: Especializado em ações brasileiras (requer token opcional)

Veja `USO_DADOS_REAIS.md` para mais detalhes.

**Exemplo rápido:**
```bash
python example_real_data.py
```

### 3. Substituir Dados Sintéticos por CSVs Reais

Para usar dados reais de arquivos CSV, prepare CSVs com os seguintes formatos:

**spot.csv:**
```csv
date,ticker,open,high,low,close,volume
2024-01-01,AAPL,150,152,149,151,1000000
```

**futures.csv:**
```csv
date,contract,expiry,open,high,low,close,volume
2024-01-01,ESZ25,2024-12-19,4300,4320,4280,4310,50000
```

**options_chain.csv:**
```csv
date,underlying,expiry,strike,option_type,bid,ask,mid,implied_vol,open_interest
2024-01-01,AAPL,2024-12-19,150,C,3.2,3.5,3.35,0.28,1200
```

No notebook, substitua as chamadas de geração sintética por:

```python
spot_df = data_loader.load_spot_csv('data/spot.csv')
futures_df = data_loader.load_futures_csv('data/futures.csv')
options_df = data_loader.load_options_csv('data/options_chain.csv')
```

### 3. Configurar Parâmetros

Edite `config.json` para ajustar:

- **nav**: Patrimônio líquido inicial (padrão: R$ 1.000.000)
- **max_per_asset_exposure**: Exposição máxima por ativo (% NAV)
- **vol_arb_threshold**: Threshold para arbitragem de volatilidade
- **pairs_zscore_threshold**: Threshold Z-score para pairs trading
- E outros parâmetros de risco e execução

## Estratégias Implementadas

### 1. Delta-Hedged Volatility Arbitrage

Vende/comprar opções quando a diferença entre volatilidade implícita (IV) e realizada (RV) excede um threshold. A estratégia faz delta-hedge automático.

### 2. Pairs/Statistical Arbitrage

Identifica pares de ativos cointegrados e negocia quando o spread (z-score) se desvia significativamente da média histórica.

## Outputs Gerados

Após executar o backtest, os seguintes arquivos são gerados em `output/`:

- **orders.csv**: Todas as ordens geradas
- **fills.csv**: Todas as execuções (fills)
- **portfolio_snapshots.csv**: Snapshots do portfólio ao longo do tempo
- **metrics.csv**: Métricas agregadas de performance

## Métricas Calculadas

- **Total Return**: Retorno total (%)
- **Sharpe Ratio**: Ratio de Sharpe anualizado
- **Max Drawdown**: Drawdown máximo (%)
- **Volatility**: Volatilidade anualizada (%)
- **Win Rate**: Taxa de acerto (%)
- **Total Trades**: Número total de trades

## Testes

Execute os testes unitários:

```bash
python tests/test_pricing.py
python tests/test_agents.py
```

## Logging

Todos os logs são salvos em formato JSON lines em `logs/decisions-YYYYMMDD.jsonl`, incluindo:

- Propostas do TraderAgent
- Decisões do RiskAgent
- Execuções de ordens
- Ativações de kill switch

## Dashboard de Acompanhamento

O projeto inclui um dashboard interativo em Streamlit para acompanhar o agente de trading em tempo real.

### Como Iniciar o Dashboard

**Opção 1: Via script batch (Windows)**
```bash
start_dashboard.bat
```

**Opção 2: Via linha de comando**
```bash
pip install streamlit plotly
streamlit run dashboard.py
```

### Funcionalidades do Dashboard

- 📊 **Métricas de Performance**: Retorno, Sharpe, Drawdown, Volatilidade, Win Rate
- 💰 **Evolução do NAV**: Gráfico interativo do patrimônio ao longo do tempo
- 📊 **Análise por Estratégia**: Distribuição de ordens e P&L por estratégia
- 📋 **Histórico de Ordens**: Todas as ordens geradas pelo TraderAgent
- ✅ **Fills**: Execuções com slippage e comissões
- 💼 **Snapshots do Portfólio**: Estado atual e histórico do portfólio
- 📝 **Logs de Decisões**: Logs estruturados das decisões dos agentes

O dashboard atualiza automaticamente quando novos dados são gerados pelo backtest.

## Funcionalidades Avançadas

### Otimização de Sizing

O projeto inclui múltiplos métodos de sizing para otimizar o tamanho das posições:

- **Fixed Fraction**: Aloca uma fração fixa do capital
- **Risk-Based**: Baseado em risco (distância até stop-loss)
- **Kelly Criterion**: Otimiza crescimento esperado do capital
- **Risk Parity**: Equaliza risco entre posições
- **Adaptive**: Combina métodos baseado em regime de mercado

Exemplo:
```python
from src.sizing import create_sizing_method

sizing = create_sizing_method('kelly', nav=1000000, config={'kelly_fraction': 0.25})
quantity = sizing.calculate_size(signal_strength=0.7, price=150.0, stop_loss=145.0)
```

### Estratégias Adicionais

Além das estratégias originais (Vol Arb e Pairs), o projeto inclui:

- **Momentum**: Baseada em médias móveis
- **Mean Reversion**: Reversão à média usando z-score
- **Breakout**: Rompimento de suporte/resistência
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence

Exemplo:
```python
from src.strategies import MomentumStrategy, RSIStrategy

momentum = MomentumStrategy(lookback_short=10, lookback_long=30)
signal = momentum.generate_signal(prices)
```

### Integração com Brokers

Stubs/mocks implementados para integração futura:

- **Mock Broker**: Para desenvolvimento e testes
- **Interactive Brokers**: Adapter usando ib_insync (stub)
- **CCXT**: Adapter para exchanges de cripto (stub)

Exemplo:
```python
from src.broker_adapters import create_broker_adapter

# Mock para desenvolvimento
broker = create_broker_adapter('mock')
broker.connect()

# IB (requer configuração)
# broker = create_broker_adapter('ib', host='127.0.0.1', port=7497)
```

### Backtesting Paralelo

Suporte para paralelização usando multiprocessing ou squad-bmad:

```python
from src.backtest_parallel import run_parallel_backtest_windows

results = run_parallel_backtest_windows(
    backtest_engine,
    train_window=60,
    test_window=20,
    step=5,
    use_bmad=True  # Tenta usar squad-bmad se disponível
)
```

## Exemplos Avançados

Execute `examples_advanced.py` para ver exemplos de uso:

```bash
python examples_advanced.py
```

## Próximos Passos

- [x] Integração com broker real (IB/CCXT) - Stubs implementados
- [x] Otimização de sizing (Kelly Criterion, Risk Parity)
- [x] Mais estratégias de trading
- [x] Dashboard de visualização
- [x] Backtesting paralelo com squad-bmad
- [ ] Análise de risco avançada (VaR, CVaR)
- [ ] Machine Learning para otimização de parâmetros
- [ ] Otimização de portfólio (Markowitz, Black-Litterman)

## Observações

- O projeto usa dados sintéticos por padrão para facilitar testes
- Todos os cálculos de greeks são validados numericamente
- O RiskAgent implementa kill switch automático em caso de drawdown excessivo
- O código é modular e facilmente extensível

## Licença

Este é um projeto de pesquisa/protótipo para fins educacionais.

