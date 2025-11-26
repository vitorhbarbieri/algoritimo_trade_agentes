# 🚀 Quick Start - Dados Reais

Guia rápido para começar a usar dados reais de mercado.

## 1. Instalação Rápida

```bash
pip install -r requirements.txt
```

## 2. Executar Backtest com Dados Reais

```bash
python example_real_data.py
```

Isso irá:
- ✅ Buscar dados reais de AAPL e MSFT via yfinance
- ✅ Executar backtest completo
- ✅ Gerar métricas e arquivos CSV
- ✅ Salvar resultados em `output/`

## 3. Personalizar Tickers

Edite `example_real_data.py` e altere:

```python
tickers = ['AAPL', 'MSFT']  # Altere aqui
```

Para ações brasileiras, use formato correto:
```python
tickers = ['PETR4.SA', 'VALE3.SA']  # Com .SA para yfinance
```

## 4. Usar no Seu Código

```python
from src.data_loader import DataLoader

data_loader = DataLoader()

# Buscar dados reais
spot_df, futures_df, options_df = data_loader.load_from_api(
    tickers=['AAPL', 'MSFT'],
    api_type='yfinance'
)

# Usar no backtest
backtest_engine.load_data(spot_df, futures_df, options_df)
backtest_engine.run_simple()
```

## 5. Dashboard

```bash
streamlit run dashboard.py
```

Acesse: http://localhost:8501

## ⚠️ Troubleshooting

### Erro: "Nenhum dado encontrado"
- Verifique conexão com internet
- Confirme que os tickers estão corretos
- Para ações brasileiras, use formato `.SA`

### Erro: "yfinance não instalado"
```bash
pip install yfinance
```

### Dados vazios
- Tente outros tickers
- Verifique o período (alguns tickers podem não ter dados históricos)
- Use fallback para dados sintéticos

## 📊 APIs Disponíveis

### yfinance (Padrão)
- ✅ Gratuito
- ✅ Sem API key
- ✅ Funciona imediatamente

### Brapi.dev (Brasil)
```python
# Configurar token (opcional)
export BRAPI_API_KEY="seu-token"

# Usar
spot_df, _, _ = data_loader.load_from_api(
    tickers=['PETR4', 'VALE3'],
    api_type='brapi'
)
```

## 🎯 Próximos Passos

1. Execute `example_real_data.py`
2. Veja os resultados em `output/`
3. Abra o dashboard: `streamlit run dashboard.py`
4. Personalize conforme necessário

