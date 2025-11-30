# 🔧 Correção: Captura de Dados em Tempo Real

## ❌ Problema Identificado

Os dados capturados estavam sempre com o **mesmo preço**, apenas mudando o timestamp de inserção. Isso acontecia porque:

1. **Para ações brasileiras**: O código estava usando `stock.info` que pode retornar dados desatualizados
2. **Fallback incorreto**: Quando não conseguia dados intraday, usava `history(period='2d', interval='1d')` que retorna dados diários (fechamento do dia anterior)
3. **Sem filtro de data**: Não estava filtrando para pegar apenas dados de **HOJE**

## ✅ Correção Implementada

### Mudanças no `monitoring_service.py`:

1. **Filtro por data de HOJE**:
   - Agora filtra explicitamente candles com `hist_intraday.index.date == today`
   - Garante que estamos usando dados do dia atual, não históricos

2. **Prioridade de busca**:
   - **Primeiro**: Tenta buscar dados intraday de HOJE (5m, 15m, 1h)
   - **Segundo**: Se não houver dados de hoje, usa `info()` para dados em tempo real
   - **Último fallback**: Dados diários (apenas se não conseguir nada)

3. **Logs melhorados**:
   - Indica quando está usando dados de hoje vs. dados históricos
   - Avisa quando usa fallback de dados diários

### Código Corrigido:

```python
# Para ações brasileiras e não-brasileiras:
# 1. Buscar dados intraday do dia atual
hist_intraday = stock.history(period='1d', interval='5m', timeout=10)

# 2. Filtrar APENAS dados de HOJE
today = datetime.now().date()
hist_today = hist_intraday[hist_intraday.index.date == today]

# 3. Usar último candle disponível de HOJE
if not hist_today.empty:
    latest = hist_today.iloc[-1]
    current_price = float(latest['Close'])  # Preço do momento atual
    # ... outros dados
```

## 📊 Como Funciona Agora

### Durante o Pregão (Mercado Aberto):
1. Busca dados intraday de **5 minutos** do dia atual
2. Filtra apenas candles de **HOJE**
3. Usa o **último candle disponível** (mais recente)
4. Preço capturado é o **preço atual do mercado**

### Fora do Pregão (Mercado Fechado):
1. Tenta buscar dados intraday (pode não ter dados de hoje)
2. Se não houver dados de hoje, usa `info()` para último preço disponível
3. Fallback para dados diários apenas se necessário

## 🧪 Como Testar

### 1. Verificar dados capturados:
```bash
python -c "
from src.orders_repository import OrdersRepository
import pandas as pd
repo = OrdersRepository()
df = repo.get_market_data_captures(limit=10)
petr = df[df['ticker'] == 'PETR4.SA'].tail(5)
print('Últimas 5 capturas de PETR4.SA:')
for _, row in petr.iterrows():
    print(f\"{row['created_at']}: Preço={row['last_price']:.2f}, Volume={row['volume']:,}\")
"
```

### 2. Verificar se preços estão variando:
- Os preços devem variar durante o pregão
- Cada captura deve ter um preço diferente (ou muito próximo se mercado estático)
- Timestamps devem ser diferentes

### 3. Executar uma captura manual:
```bash
python -c "
from src.monitoring_service import MonitoringService
import json
with open('config.json', 'r') as f:
    config = json.load(f)
monitoring = MonitoringService(config)
result = monitoring.scan_market()
print('Tickers processados:', result.get('tickers_processed', 0))
print('Dados capturados:', result.get('data_captured', 0))
"
```

## ⚠️ Limitações do yfinance

### Ações Brasileiras (.SA):
- **Durante o pregão**: Dados intraday podem ter delay de alguns minutos
- **Fora do pregão**: Retorna último preço de fechamento
- **Fins de semana**: Retorna dados do último pregão

### Ações Internacionais:
- Dados intraday mais confiáveis durante horário de trading
- Fora do horário, retorna último preço disponível

## 💡 Recomendações

1. **Durante o pregão**: Os dados devem estar atualizados a cada 5 minutos
2. **Verificar logs**: Os logs agora indicam quando está usando dados de hoje vs. históricos
3. **Monitorar variação**: Se os preços continuarem iguais, pode ser:
   - Mercado estático (pouca variação)
   - Mercado fechado (usando último preço)
   - Problema com API do yfinance

## ✅ Status

- ✅ Filtro por data de HOJE implementado
- ✅ Prioridade de busca corrigida
- ✅ Logs melhorados
- ✅ Fallback para dados diários apenas quando necessário

---

**Data**: 29/11/2025
**Status**: ✅ CORRIGIDO

