# 🚀 Guia: Rodar Simulador com Todos os Agentes

## 🎯 Objetivo

Executar o simulador de mercado real (usando dados de hoje) junto com todos os agentes de trading e monitoramento, para observar o comportamento completo do sistema.

## 🚀 Como Usar

### Execução Simples

```bash
python rodar_simulador_com_agentes.py
```

### O Que Acontece

O script inicia **3 serviços simultaneamente**:

1. **MonitoringService** (Agentes de Trading)
   - Escaneia mercado a cada 5 minutos
   - Gera propostas de trading
   - Avalia propostas com RiskAgent
   - Envia notificações Telegram

2. **DataHealthMonitor** (Monitor de Saúde)
   - Verifica saúde da captura a cada 1 hora
   - Envia relatórios às 12:00 e 15:00
   - Corrige problemas automaticamente

3. **SimuladorMercadoReal** (Simulação com Dados Reais)
   - Simula dia usando dados REAIS de hoje
   - Captura dados a cada 5 minutos (simulado)
   - Gera propostas baseadas em dados reais
   - Processa como se fosse mercado real

## 📊 Arquitetura

```
┌─────────────────────────────────────────┐
│   rodar_simulador_com_agentes.py       │
│   (Thread Principal)                    │
└─────────────────────────────────────────┘
           │
           ├─── MonitoringService (Thread Principal)
           │    └─── Escaneia mercado a cada 5min
           │
           ├─── DataHealthMonitor (Thread Separada)
           │    └─── Verifica saúde a cada 1h
           │
           └─── SimuladorMercadoReal (Thread Separada)
                └─── Simula dia completo com dados reais
```

## 🔍 Monitoramento

### Logs em Tempo Real

Os logs são exibidos no console e salvos em:
- `simulador_agentes.log` - Log principal
- `agentes.log` - Log do MonitoringService (se existir)

### Verificar Status

```bash
# Ver logs em tempo real
tail -f simulador_agentes.log

# Filtrar apenas propostas
tail -f simulador_agentes.log | grep "Proposta"

# Filtrar apenas erros
tail -f simulador_agentes.log | grep "ERROR"
```

### Verificar Banco de Dados

```bash
# Ver capturas do simulador
python -c "import sqlite3; conn = sqlite3.connect('agents_orders.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM market_data_captures WHERE source=\"simulation\"'); print('Capturas simuladas:', cursor.fetchone()[0]); conn.close()"

# Ver propostas geradas
python -c "import sqlite3; conn = sqlite3.connect('agents_orders.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM proposals WHERE source=\"simulation\"'); print('Propostas simuladas:', cursor.fetchone()[0]); conn.close()"
```

## ⚙️ Configuração

O script usa o mesmo `config.json` do sistema principal:
- Tickers monitorados
- Configurações de estratégias
- Configurações de notificações

### Data de Referência

Por padrão, usa dados de **HOJE**. Para usar outra data, modifique o script:

```python
# No arquivo rodar_simulador_com_agentes.py
# Linha ~50:
data_referencia = datetime.now(B3_TIMEZONE)  # Hoje
# Ou:
data_referencia = datetime.now(B3_TIMEZONE) - timedelta(days=1)  # Ontem
```

## 🛑 Parar Execução

Pressione `Ctrl+C` para parar todos os serviços de forma segura.

## 📝 O Que Observar

Durante a execução, observe:

1. **Captura de Dados**:
   - Quantos tickers estão sendo capturados
   - Se os dados são reais e corretos
   - Timestamps dos dados

2. **Geração de Propostas**:
   - Quantas propostas são geradas
   - Quais estratégias estão ativas
   - Se o DayTrade está funcionando

3. **Avaliação de Risco**:
   - Quantas propostas são aprovadas/rejeitadas
   - Razões de rejeição
   - Modificações sugeridas

4. **Notificações**:
   - Se Telegram está funcionando
   - Formato das mensagens
   - Botões de aprovação

5. **Monitor de Saúde**:
   - Relatórios às 12:00 e 15:00
   - Verificações automáticas
   - Correções automáticas

## ⚠️ Observações

1. **Dados de Hoje**: 
   - Se executar durante o pregão, pode não ter dados intraday completos
   - Considere usar dados de ontem para teste completo

2. **Performance**:
   - Três serviços rodando simultaneamente
   - Pode consumir recursos do sistema
   - Monitore uso de CPU/memória

3. **Notificações**:
   - Telegram pode enviar muitas mensagens
   - Considere desabilitar temporariamente se necessário

4. **Simulação Acelerada**:
   - Simulador espera apenas 2 segundos entre capturas
   - Para simular tempo real, modifique `time.sleep(2)` para `time.sleep(300)`

## 🧪 Casos de Uso

### Teste Completo do Sistema

```bash
# Rodar tudo junto e observar comportamento
python rodar_simulador_com_agentes.py
```

### Validar DayTrade Agent

```bash
# Verificar se DayTrade está gerando propostas
python rodar_simulador_com_agentes.py
# Em outro terminal:
tail -f simulador_agentes.log | grep "daytrade"
```

### Testar Notificações

```bash
# Verificar se Telegram está funcionando
python rodar_simulador_com_agentes.py
# Observar mensagens no Telegram
```

## ✅ Vantagens

1. ✅ **Teste Completo**: Testa todo o sistema de uma vez
2. ✅ **Dados Reais**: Usa dados reais de mercado
3. ✅ **Monitoramento**: Inclui monitor de saúde
4. ✅ **Observação**: Fácil de acompanhar comportamento
5. ✅ **Rastreabilidade**: Tudo salvo no banco

---

**Criado em**: 29/11/2025
**Status**: ✅ PRONTO PARA USO

