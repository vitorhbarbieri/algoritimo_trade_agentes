# ⏱️ Intervalos de Captura de Dados de Mercado

## 📊 Frequência de Captura

### Intervalo Principal: **5 minutos (300 segundos)**

Os agentes buscam dados de mercado reais e salvam no banco de dados **a cada 5 minutos** durante o horário de trading da B3.

### Detalhamento do Processo

#### 1. **Durante o Pregão (10:00 - 17:00 B3)**

```
A cada 5 minutos:
├── Escaneia mercado
├── Busca dados INTRADAY (intervalo de 5 minutos)
├── Busca dados de opções (quando disponível)
├── Salva dados no banco (market_data_captures)
├── Gera propostas de trading
├── Avalia risco das propostas
└── Envia notificações Telegram (se houver propostas aprovadas)
```

#### 2. **Fora do Pregão**

```
Quando mercado está fechado:
├── Verifica status a cada 1 hora
├── Aguarda próximo pregão
└── Não busca dados (economiza recursos)
```

## 💾 O Que É Salvo no Banco

### Tabela: `market_data_captures`

A cada scan (a cada 5 minutos), são salvos:

1. **Dados Spot (Ações)**:
   - Preço de abertura
   - Preço de fechamento
   - Preço máximo
   - Preço mínimo
   - Volume
   - Timestamp da captura
   - Source: `'real'` (dados reais) ou `'simulation'` (dados simulados)

2. **Dados de Opções** (quando disponível):
   - Strike
   - Expiry
   - Bid/Ask/Mid
   - Volume
   - Greeks (Delta, Gamma, Vega)
   - IV (Volatilidade Implícita)
   - Timestamp da captura
   - Source: `'real'` ou `'simulation'`

### Exemplo de Registro

```sql
INSERT INTO market_data_captures (
    ticker,
    data_type,
    spot_data,
    options_data,
    raw_data,
    source,
    timestamp
) VALUES (
    'PETR4.SA',
    'spot',
    '{"open": 32.50, "close": 32.75, "high": 32.80, "low": 32.45, "volume": 1000000}',
    NULL,
    '{"raw": "dados brutos da API"}',
    'real',
    '2025-11-28T10:05:00'
);
```

## 📈 Dados Coletados

### Intervalo de Dados Intraday

O sistema tenta buscar dados com intervalo de **5 minutos**:
- **Preferência**: `period='1d', interval='5m'` (dados do dia atual, intervalo de 5 minutos)
- **Fallback 1**: `interval='15m'` (se 5m não disponível)
- **Fallback 2**: `interval='1h'` (se 15m não disponível)
- **Fallback 3**: `period='5d', interval='1d'` (dados diários dos últimos 5 dias)

### Tickers Monitorados

Todos os tickers configurados em `config.json` → `monitored_tickers` são escaneados a cada ciclo.

## 🔄 Ciclo Completo de Captura

```
00:00 → Scan 1
├── Busca dados PETR4.SA
├── Busca dados VALE3.SA
├── Busca dados ITUB4.SA
├── ... (todos os tickers)
├── Salva tudo no banco
└── Aguarda 5 minutos

05:00 → Scan 2
├── Busca dados atualizados
├── Salva no banco
└── Aguarda 5 minutos

10:00 → Scan 3
...
```

## 📊 Estatísticas de Captura

### Durante um Pregão Completo (7 horas)

- **Total de scans**: ~84 scans (420 minutos / 5 minutos)
- **Dados salvos**: ~84 registros por ticker
- **Se 30 tickers**: ~2.520 registros de dados spot por dia
- **Dados de opções**: Variável (depende da disponibilidade)

### Exemplo Prático

**Durante o pregão de hoje (10:00 - 17:00)**:

```
10:00 → Captura 1 → Salva no banco
10:05 → Captura 2 → Salva no banco
10:10 → Captura 3 → Salva no banco
...
16:55 → Captura 84 → Salva no banco
17:00 → Mercado fecha → Para capturas
```

## ⚙️ Configuração do Intervalo

### Padrão

O intervalo padrão é **300 segundos (5 minutos)**, definido em:

```python
monitoring_service.start_monitoring(interval_seconds=300)
```

### Alterar Intervalo

Se quiser alterar o intervalo, modifique o script `iniciar_agentes.py`:

```python
# Intervalo de 3 minutos (180 segundos)
monitoring_service.start_monitoring(interval_seconds=180)

# Intervalo de 10 minutos (600 segundos)
monitoring_service.start_monitoring(interval_seconds=600)
```

**⚠️ Atenção**: 
- Intervalos muito curtos (< 1 minuto) podem sobrecarregar as APIs
- Intervalos muito longos (> 10 minutos) podem perder oportunidades rápidas
- **Recomendado**: 5 minutos (padrão)

## 📝 Rastreabilidade

Todos os dados capturados são salvos com:
- **Timestamp**: Data/hora exata da captura
- **Source**: `'real'` (dados reais) ou `'simulation'` (dados simulados)
- **Raw Data**: Dados brutos da API (para análise posterior)
- **Processed Data**: Dados processados e normalizados

Isso permite:
- ✅ Análise histórica completa
- ✅ Backtesting com dados reais
- ✅ Rastreabilidade de todas as decisões
- ✅ Auditoria completa do sistema

## 🎯 Resumo

| Item | Valor |
|------|-------|
| **Intervalo de captura** | 5 minutos (300 segundos) |
| **Horário de operação** | 10:00 - 17:00 (B3) |
| **Dados salvos** | Spot + Opções (quando disponível) |
| **Source** | `'real'` (dados reais) |
| **Scans por dia** | ~84 scans durante o pregão |
| **Registros por ticker** | ~84 registros por dia |

---

**Última atualização**: 27/11/2025

