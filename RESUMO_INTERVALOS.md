# ⏱️ Resumo: Intervalos de Captura de Dados

## 📊 Resposta Direta

**Os agentes buscam dados de mercado reais e salvam no banco de dados a cada 5 minutos (300 segundos) durante o horário de trading da B3 (10:00 - 17:00).**

## 🔄 Ciclo Completo

### Durante o Pregão (10:00 - 17:00 B3)

```
A cada 5 minutos:
├── 1. Busca dados INTRADAY de todos os tickers monitorados
│   └── Intervalo preferido: 5 minutos (period='1d', interval='5m')
│
├── 2. Busca dados de opções (quando disponível)
│   └── Para cada ticker com dados spot válidos
│
├── 3. Salva tudo no banco de dados
│   └── Tabela: market_data_captures
│   └── Source: 'real' (dados reais)
│
├── 4. Gera propostas de trading
│   └── Analisa oportunidades em opções e ações
│
├── 5. Avalia risco das propostas
│   └── RiskAgent valida cada proposta
│
└── 6. Envia notificações Telegram
    └── Para propostas aprovadas (formato melhorado)
```

### Fora do Pregão

```
Quando mercado está fechado:
├── Verifica status a cada 1 hora
├── Não busca dados (economiza recursos)
└── Aguarda próximo pregão automaticamente
```

## 📈 Estatísticas

### Por Dia de Pregão (7 horas)

- **Intervalo**: 5 minutos
- **Total de scans**: ~84 scans
- **Dados salvos**: ~84 registros por ticker
- **Exemplo**: 30 tickers = ~2.520 registros de dados spot por dia

### Exemplo Prático

```
10:00 → Scan 1 → Salva dados no banco
10:05 → Scan 2 → Salva dados no banco
10:10 → Scan 3 → Salva dados no banco
...
16:55 → Scan 84 → Salva dados no banco
17:00 → Mercado fecha → Para capturas
```

## 💾 O Que É Salvo

### Tabela: `market_data_captures`

Para cada ticker, a cada 5 minutos:

```json
{
  "ticker": "PETR4.SA",
  "data_type": "spot",
  "spot_data": {
    "open": 32.50,
    "close": 32.75,
    "high": 32.80,
    "low": 32.45,
    "volume": 1000000
  },
  "options_data": [...],  // Se disponível
  "source": "real",
  "timestamp": "2025-11-28T10:05:00"
}
```

## ⚙️ Configuração

### Padrão

```python
# Intervalo padrão: 5 minutos (300 segundos)
monitoring_service.start_monitoring(interval_seconds=300)
```

### Alterar Intervalo

Edite `iniciar_agentes.py`:

```python
# Exemplo: 3 minutos
monitoring_service.start_monitoring(interval_seconds=180)

# Exemplo: 10 minutos
monitoring_service.start_monitoring(interval_seconds=600)
```

**⚠️ Recomendado**: Manter 5 minutos (padrão)

## ✅ Confirmação

- ✅ Dados são salvos **automaticamente** a cada scan
- ✅ Source marcado como **'real'** para dados reais
- ✅ Rastreabilidade **completa** de todas as capturas
- ✅ Banco de dados atualizado **em tempo real**

---

**Última atualização**: 27/11/2025

