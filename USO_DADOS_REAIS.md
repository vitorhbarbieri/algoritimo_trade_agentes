# 📊 Usando Dados Reais de Mercado

Este guia explica como usar dados reais de mercado via APIs no projeto.

## 🚀 APIs Disponíveis

### 1. Yahoo Finance (yfinance) ⭐ Recomendado

**Vantagens:**
- ✅ Totalmente gratuito
- ✅ Sem necessidade de API key
- ✅ Cobertura ampla (ações, opções)
- ✅ Dados históricos completos

**Limitações:**
- ⚠️ Dados podem ter atraso de 15-20 minutos
- ⚠️ Rate limiting não documentado (recomenda-se throttle)

**Instalação:**
```bash
pip install yfinance
```

### 2. Brapi.dev (Brasil)

**Vantagens:**
- ✅ Especializado em ações brasileiras (B3)
- ✅ Dados em tempo real
- ✅ API gratuita disponível

**Limitações:**
- ⚠️ Requer API key para alguns tickers
- ⚠️ Não suporta opções/futuros diretamente

**Configuração:**
```bash
# Opcional: definir token via variável de ambiente
export BRAPI_API_KEY="seu-token-aqui"
```

## 📝 Exemplos de Uso

### Exemplo 1: Buscar Dados Reais

```python
from src.market_data_api import fetch_real_market_data

# Buscar dados de ações americanas
data = fetch_real_market_data(
    tickers=['AAPL', 'MSFT'],
    start_date='2024-01-01',
    end_date='2024-12-31',
    api_type='yfinance',
    use_fallback=True
)

spot_df = data['spot']
futures_df = data['futures']
options_df = data['options']
```

### Exemplo 2: Usar no DataLoader

```python
from src.data_loader import DataLoader

data_loader = DataLoader()

# Carregar dados reais via API
spot_df, futures_df, options_df = data_loader.load_from_api(
    tickers=['AAPL', 'MSFT'],
    start_date='2024-01-01',
    end_date='2024-12-31',
    api_type='yfinance'
)
```

### Exemplo 3: Backtest com Dados Reais

```python
# Execute o script de exemplo
python example_real_data.py
```

Ou no notebook:

```python
# No mvp_agents.ipynb, substitua a geração sintética por:

from src.data_loader import DataLoader

data_loader = DataLoader()

# Buscar dados reais
spot_df, futures_df, options_df = data_loader.load_from_api(
    tickers=['AAPL', 'MSFT'],
    api_type='yfinance'
)

# Se não houver dados, usar sintéticos como fallback
if spot_df.empty:
    spot_df = data_loader.generate_synthetic_spot(['AAPL', 'MSFT'])
```

## 🔧 Configuração Avançada

### Usar Brapi.dev para Ações Brasileiras

```python
from src.market_data_api import create_market_data_api

# Criar API Brapi
brapi = create_market_data_api('brapi', api_key='seu-token')

# Buscar dados
spot_df = brapi.fetch_spot_data(
    tickers=['PETR4', 'VALE3'],
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

### Fallback Automático

O sistema tenta automaticamente usar fallback se a API principal falhar:

```python
data = fetch_real_market_data(
    tickers=['AAPL'],
    api_type='brapi',  # Tenta Brapi primeiro
    use_fallback=True  # Se falhar, usa yfinance
)
```

## 📊 Formatos de Dados

### Spot (Ações)
```python
# Colunas esperadas:
# date, ticker, open, high, low, close, volume
```

### Opções
```python
# Colunas esperadas:
# date, underlying, expiry, strike, option_type, bid, ask, mid, implied_vol, open_interest
```

## ⚠️ Troubleshooting

### Erro: "yfinance não instalado"
```bash
pip install yfinance
```

### Erro: "Nenhum dado encontrado"
- Verifique se os tickers estão corretos
- Para ações brasileiras, use formato correto (ex: 'PETR4.SA' para yfinance)
- Verifique sua conexão com a internet

### Rate Limiting
- O sistema já implementa throttle automático
- Se ainda assim houver problemas, aumente o intervalo em `market_data_api.py`

## 🎯 Próximos Passos

1. Execute `python example_real_data.py` para testar
2. Ajuste os tickers conforme necessário
3. Integre no seu backtest usando `data_loader.load_from_api()`

