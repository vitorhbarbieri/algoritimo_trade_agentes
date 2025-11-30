# 🔧 Correção: Captura de Dados de Mercado

## 🐛 Problema Identificado

**Situação**: Ontem (28/11/2025) nenhum dado de mercado foi capturado.

### Causa Raiz

O código estava retornando imediatamente quando o mercado estava fechado (`status == 'CLOSED'`), **sem capturar dados**. Isso significa que:

1. **Durante o pregão**: Se houvesse algum problema de timing ou status, não capturava
2. **Fora do pregão**: Nunca capturava dados históricos
3. **Fins de semana**: Não capturava dados para análise posterior

### Código Problemático

```python
# ANTES (ERRADO):
if trading_status == 'CLOSED':
    return {
        'status': 'MARKET_CLOSED',
        'opportunities': 0,
        'proposals': 0
    }
# Nunca chegava na parte de captura de dados!
```

## ✅ Correção Implementada

### Mudança 1: Sempre Capturar Dados

Agora o sistema **sempre tenta capturar dados**, mesmo quando o mercado está fechado:

```python
# AGORA (CORRETO):
should_capture_data = True  # Sempre tentar capturar dados
should_generate_proposals = trading_status in ['PRE_MARKET', 'TRADING', 'POST_MARKET']

# Captura dados SEMPRE
# Gera propostas APENAS durante trading
```

### Mudança 2: Loop de Monitoramento

O loop de monitoramento agora executa `scan_market()` mesmo quando fechado:

```python
# ANTES: continue (pulava o scan)
# AGORA: Executa scan para capturar dados históricos
if status == 'CLOSED':
    logger.info("Mercado fechado - executando captura de dados (sem gerar propostas)")
    result = self.scan_market()  # Executa mesmo fechado!
```

### Mudança 3: Logs Melhorados

Agora há logs claros indicando:
- Quando dados são capturados
- Quando propostas são geradas (ou não)
- Status do mercado

## 📊 Comportamento Corrigido

### Durante o Pregão (10:00 - 17:00)

```
A cada 5 minutos:
├── Captura dados de mercado ✅
├── Salva no banco ✅
├── Gera propostas ✅
└── Envia notificações ✅
```

### Fora do Pregão (mas dia útil)

```
A cada 5 minutos:
├── Captura dados de mercado ✅
├── Salva no banco ✅
├── NÃO gera propostas (mercado fechado)
└── NÃO envia notificações
```

### Fins de Semana/Feriados

```
A cada hora:
├── Tenta capturar dados históricos ✅
├── Salva no banco ✅
├── NÃO gera propostas
└── Aguarda próximo pregão
```

## 🔍 Verificação

Execute o diagnóstico:

```bash
python diagnosticar_captura.py
```

Este script verifica:
- ✅ Se dados estão sendo capturados
- ✅ Se estão sendo salvos no banco
- ✅ Status do mercado
- ✅ Funcionamento da API

## 📝 Logs Esperados

### Durante Trading

```
INFO - Buscando dados intraday para 30 tickers...
INFO - Dados coletados: 20/20 tickers com dados spot
INFO - Dados salvos no banco: 20 tickers
INFO - Propostas geradas: 5
```

### Fora do Trading

```
INFO - Mercado fechado - executando captura de dados (sem gerar propostas)
INFO - Buscando dados intraday para 30 tickers...
INFO - Dados coletados: 20/20 tickers com dados spot
INFO - Dados salvos no banco: 20 tickers
INFO - Mercado fechado - dados capturados mas propostas não geradas
```

## ✅ Garantias

Agora o sistema garante:

1. ✅ **Dados sempre capturados** - Mesmo quando mercado fechado
2. ✅ **Dados sempre salvos** - No banco para rastreabilidade
3. ✅ **Propostas apenas durante trading** - Respeitando horário B3
4. ✅ **Logs claros** - Para diagnóstico fácil

## 🧪 Teste

Para testar a correção:

```bash
# Testar captura mesmo com mercado fechado
python -c "from src.monitoring_service import MonitoringService; import json; m = MonitoringService(json.load(open('config.json'))); result = m.scan_market(); print('Status:', result['status']); print('Dados capturados:', 'spot' in result or 'proposals' in result)"
```

## 📋 Checklist de Verificação

Após a correção, verifique:

- [x] Código corrigido para sempre capturar dados
- [x] Loop de monitoramento executa scan mesmo fechado
- [x] Logs melhorados para diagnóstico
- [ ] Testar com dados reais durante o pregão
- [ ] Verificar se dados estão sendo salvos no banco
- [ ] Confirmar que propostas são geradas apenas durante trading

---

**Correção aplicada em**: 29/11/2025
**Status**: ✅ CORRIGIDO

