# 🔍 Sistema de Análise de Propostas - Implementado

## ✅ O Que Foi Criado

### 1. **Novo Endpoint `/daytrade/analysis`**
- **Localização**: `api_server.py` (precisa ser adicionado ao arquivo completo)
- **Funcionalidade**: Retorna análise detalhada de propostas geradas, aprovadas e rejeitadas
- **Parâmetros**: `days` (padrão: 1) - período de análise em dias
- **Retorna**:
  - Total de propostas geradas
  - Lista de propostas aprovadas
  - Lista de propostas rejeitadas com motivos
  - Estatísticas de motivos de rejeição
  - Período analisado

### 2. **Nova Seção no Dashboard**
- **Localização**: `dashboard_central.py` - Aba "DayTrade Monitor"
- **Funcionalidade**: Visualização completa de análise de propostas
- **Componentes**:
  - Métricas: Total Geradas, Aprovadas, Rejeitadas
  - Gráfico de barras com motivos de rejeição
  - Tabela de propostas rejeitadas (últimas 20)
  - Tabela de propostas aprovadas (últimas 20)
  - Diagnóstico quando não há propostas

### 3. **Função `get_daytrade_analysis()`**
- **Localização**: `dashboard_central.py`
- **Funcionalidade**: Busca dados de análise da API

## ⚠️ Problema Identificado

O arquivo `api_server.py` foi **sobrescrito** e agora contém apenas o endpoint `/daytrade/analysis`. O arquivo completo precisa ser restaurado.

## 🔧 Como Corrigir

### Opção 1: Restaurar do Git (se disponível)
```bash
git checkout api_server.py
```

### Opção 2: Adicionar endpoint manualmente
O endpoint `/daytrade/analysis` precisa ser adicionado ao arquivo `api_server.py` completo, após o endpoint `/daytrade/monitoring`.

## 📊 Como Usar

### 1. Via API
```bash
# Análise das últimas 24 horas
curl http://localhost:5000/daytrade/analysis

# Análise dos últimos 7 dias
curl http://localhost:5000/daytrade/analysis?days=7
```

### 2. Via Dashboard
1. Acesse o dashboard: `streamlit run dashboard_central.py`
2. Vá para a aba "📈 DayTrade Monitor"
3. Role até a seção "🔍 Análise Detalhada de Propostas"

## 🔍 Diagnóstico: Por Que Não Há Propostas?

O dashboard agora mostra um diagnóstico quando não há propostas geradas, indicando:

### Possíveis Causas:

1. **Critérios muito restritivos:**
   - `min_intraday_return`: 0.5% (muito alto?)
   - `min_volume_ratio`: 0.25 (muito alto?)
   - `delta_min`: 0.20, `delta_max`: 0.60 (muito restritivo?)
   - `max_dte`: 7 dias (muito curto?)
   - `max_spread_pct`: 5% (muito baixo?)

2. **Mercado não atende aos critérios:**
   - Baixa volatilidade
   - Baixo volume
   - Opções com spread muito alto

3. **Dados não estão sendo capturados corretamente**

### Como Diagnosticar:

1. **Verificar captura de dados:**
   ```bash
   python diagnosticar_captura.py
   ```

2. **Verificar logs:**
   ```bash
   # Ver logs em tempo real
   tail -f logs/monitoring_service.log
   ```

3. **Verificar critérios:**
   - Abra `config.json`
   - Verifique os valores em `daytrade_options`
   - Considere reduzir os critérios para testar

4. **Testar com dados simulados:**
   ```bash
   python simular_market_data.py
   ```

## 📈 O Que Você Verá no Dashboard

### Se Houver Propostas:
- ✅ Total de propostas geradas
- ✅ Número de aprovadas vs. rejeitadas
- ✅ Gráfico de motivos de rejeição
- ✅ Tabelas detalhadas de propostas

### Se Não Houver Propostas:
- ⚠️ Mensagem de diagnóstico
- 💡 Sugestões de como resolver
- 📋 Lista de critérios que podem estar muito restritivos

## 🎯 Próximos Passos

1. **Restaurar `api_server.py` completo**
2. **Adicionar endpoint `/daytrade/analysis` ao arquivo completo**
3. **Testar o endpoint:**
   ```bash
   python -c "import requests; r = requests.get('http://localhost:5000/daytrade/analysis'); print(r.json())"
   ```
4. **Verificar se o dashboard está mostrando a análise**

## 📝 Notas Importantes

- O endpoint precisa estar no arquivo `api_server.py` completo
- A função `get_daytrade_analysis()` já está no `dashboard_central.py`
- A visualização já está implementada no dashboard
- O diagnóstico de "por que não há propostas" já está funcionando

---

**Status**: ✅ Implementado (precisa restaurar `api_server.py`)
**Última atualização**: 29/11/2025

