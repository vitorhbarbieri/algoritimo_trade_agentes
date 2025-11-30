# ✅ Simulador + Agentes Rodando

## 🚀 Status

O script `rodar_simulador_com_agentes.py` foi criado e está configurado para rodar todos os serviços simultaneamente.

## 📋 O Que Está Rodando

### 1. MonitoringService (Agentes de Trading)
- ✅ Escaneia mercado a cada 5 minutos
- ✅ Gera propostas de trading
- ✅ Avalia propostas com RiskAgent
- ✅ Envia notificações Telegram
- ✅ Salva tudo no banco de dados

### 2. DataHealthMonitor (Monitor de Saúde)
- ✅ Verifica saúde da captura a cada 1 hora
- ✅ Envia relatórios às 12:00 e 15:00
- ✅ Corrige problemas automaticamente

### 3. SimuladorMercadoReal (Simulação com Dados Reais)
- ✅ Simula dia usando dados REAIS de hoje
- ✅ Captura dados a cada 5 minutos (simulado, acelerado)
- ✅ Gera propostas baseadas em dados reais
- ✅ Processa como se fosse mercado real

## 🎯 Como Executar

```bash
python rodar_simulador_com_agentes.py
```

## 📊 Monitoramento

### Ver Logs em Tempo Real

```bash
# Ver todos os logs
tail -f simulador_agentes.log

# Filtrar apenas propostas
tail -f simulador_agentes.log | grep "Proposta"

# Filtrar apenas DayTrade
tail -f simulador_agentes.log | grep "daytrade"
```

### Verificar Banco de Dados

```bash
# Ver capturas
python -c "import sqlite3; conn = sqlite3.connect('agents_orders.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM market_data_captures WHERE source=\"simulation\"'); print('Capturas:', cursor.fetchone()[0]); conn.close()"

# Ver propostas
python -c "import sqlite3; conn = sqlite3.connect('agents_orders.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM proposals WHERE source=\"simulation\"'); print('Propostas:', cursor.fetchone()[0]); conn.close()"
```

## 🔍 O Que Observar

Durante a execução, observe:

1. **Captura de Dados**:
   - Quantos tickers estão sendo capturados
   - Se os dados são reais e corretos
   - Timestamps dos dados

2. **Geração de Propostas DayTrade**:
   - Quantas propostas são geradas
   - Se o DayTrade está funcionando
   - Quais oportunidades são encontradas

3. **Avaliação de Risco**:
   - Quantas propostas são aprovadas/rejeitadas
   - Razões de rejeição
   - Modificações sugeridas

4. **Notificações Telegram**:
   - Se Telegram está funcionando
   - Formato das mensagens
   - Botões de aprovação

5. **Monitor de Saúde**:
   - Relatórios às 12:00 e 15:00
   - Verificações automáticas
   - Correções automáticas

## 🛑 Parar Execução

Pressione `Ctrl+C` para parar todos os serviços de forma segura.

## ⚙️ Configuração

- **Data de Referência**: Hoje (pode ser modificado no script)
- **Intervalo de Captura**: 5 minutos (simulado com 2 segundos)
- **Tickers**: Configurados em `config.json`

## 📝 Arquivos Criados

- ✅ `rodar_simulador_com_agentes.py` - Script principal
- ✅ `GUIA_RODAR_SIMULADOR_AGENTES.md` - Documentação completa
- ✅ `simulador_agentes.log` - Log de execução

---

**Status**: ✅ PRONTO PARA USO
**Data**: 29/11/2025

