# 📊 Guia: Simulação de Mercado Real

## 🎯 Objetivo

Simular um dia completo de mercado usando dados históricos reais, respeitando o cronograma normal de captura de dados (a cada 5 minutos durante o pregão).

## 🚀 Como Usar

### Uso Básico

```bash
# Simular usando dados de ontem (padrão)
python simular_dia_mercado_real.py

# Simular usando dados de uma data específica
python simular_dia_mercado_real.py --data 2025-11-28

# Usar arquivo de configuração customizado
python simular_dia_mercado_real.py --config config.json --data ontem
```

### Parâmetros

- `--data`: Data de referência para buscar dados históricos
  - Formato: `YYYY-MM-DD` (ex: `2025-11-28`)
  - Ou: `ontem` (usa ontem automaticamente)
  - Padrão: `ontem`

- `--config`: Caminho do arquivo de configuração
  - Padrão: `config.json`

## 📋 O Que o Script Faz

1. **Gera Horários de Captura**: Cria lista de horários a cada 5 minutos durante o pregão:
   - Pré-mercado: 09:45 - 10:00
   - Pregão: 10:00 - 17:00
   - Pós-mercado: 17:00 - 17:30

2. **Busca Dados REAIS de Mercado**: Para cada horário:
   - Busca dados intraday REAIS do dia de referência via yfinance
   - Encontra o dado REAL mais próximo do horário especificado
   - Usa APENAS dados reais, sem criar ou simular preços
   - Tenta diferentes intervalos (5m, 15m, 1h, 1d) para encontrar dados disponíveis

3. **Processa Dados**: 
   - Salva dados no banco (marcados como `simulation`)
   - Gera propostas usando `TraderAgent`
   - Avalia propostas com `RiskAgent`
   - Simula execuções (se aprovadas)

4. **Acelera Tempo**: 
   - Em vez de esperar 5 minutos reais entre capturas
   - Espera apenas 2 segundos (simulação acelerada)

## 📊 Exemplo de Execução

```bash
$ python simular_dia_mercado_real.py --data 2025-11-28

======================================================================
INICIANDO SIMULAÇÃO DE MERCADO REAL
======================================================================
Data de referência: 2025-11-28
Total de horários: 90

[1/90] Processando horário: 09:45
Buscando dados históricos para 2025-11-28 às 09:45...
Dados históricos coletados: 25 tickers
Dados salvos no banco: 25 tickers
Propostas geradas: 3
Proposta DAYOPT-PETR4-...: APPROVE
Aguardando próximo horário...

[2/90] Processando horário: 09:50
...
```

## 🔍 Dados Salvos

Todos os dados são salvos no banco com:
- `source='simulation'` - Marcado como simulação (mas dados são REAIS)
- `raw_data` contém:
  - `data_referencia`: Data histórica usada
  - `horario_simulado`: Horário simulado
  - `tipo`: 'simulacao_mercado_real'
  - `dados_reais`: True - Indicador de que são dados reais
  - `timestamp_real`: Timestamp real do dado usado
  - `intervalo_usado`: Intervalo usado para buscar dados (5m, 15m, 1h, 1d)

## ⚙️ Configuração

O script usa o mesmo `config.json` do sistema principal:
- Tickers monitorados
- Configurações de estratégias
- Configurações de notificações (opcional)

## 📝 Logs

Os logs são salvos em:
- Console: Saída padrão
- Arquivo: `simulacao_mercado_real.log`

## ⚠️ Observações

1. **Dados REAIS**: 
   - O script usa APENAS dados reais do yfinance
   - Não cria ou simula preços, apenas busca dados históricos reais
   - yfinance pode não ter dados intraday para todos os tickers
   - Alguns tickers podem não ter dados disponíveis para o horário específico
   - O script tenta diferentes intervalos (5m, 15m, 1h, 1d) para encontrar dados disponíveis
   - Se não houver dados até o horário especificado, o ticker é pulado

2. **Tempo Acelerado**:
   - A simulação é acelerada (2 segundos entre capturas)
   - Para simular tempo real, modifique `time.sleep(2)` para `time.sleep(300)`

3. **Notificações**:
   - Notificações Telegram/Discord podem ser enviadas se configuradas
   - Considere desabilitar durante simulações extensas

4. **Performance**:
   - A simulação completa pode levar alguns minutos
   - Depende da quantidade de tickers e disponibilidade de dados

## 🧪 Casos de Uso

### Testar Estratégias

```bash
# Testar estratégia com dados de ontem
python simular_dia_mercado_real.py --data ontem
```

### Análise Retrospectiva

```bash
# Analisar comportamento em um dia específico
python simular_dia_mercado_real.py --data 2025-11-15
```

### Validação de Sistema

```bash
# Validar sistema completo com dados reais
python simular_dia_mercado_real.py --data ontem
```

## 📊 Verificar Resultados

Após a simulação, verifique:

```bash
# Ver capturas no banco
python -c "import sqlite3; conn = sqlite3.connect('agents_orders.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM market_data_captures WHERE source=\"simulation\"'); print('Capturas:', cursor.fetchone()[0]); conn.close()"

# Ver propostas geradas
python -c "import sqlite3; conn = sqlite3.connect('agents_orders.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM proposals WHERE source=\"simulation\"'); print('Propostas:', cursor.fetchone()[0]); conn.close()"
```

## ✅ Vantagens

1. ✅ **Dados Reais**: Usa dados históricos reais do mercado
2. ✅ **Cronograma Realista**: Respeita horários de captura do sistema
3. ✅ **Teste Completo**: Testa todo o fluxo (captura → proposta → avaliação → execução)
4. ✅ **Rastreabilidade**: Todos os dados são salvos no banco
5. ✅ **Acelerado**: Simulação rápida para testes

---

**Criado em**: 29/11/2025
**Status**: ✅ PRONTO PARA USO

