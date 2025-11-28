# ✅ Checklist Pré-Operação - Agentes de Trading

## 📋 Antes de Iniciar os Agentes

### 1. Configurações Básicas ✅

- [x] **config.json** configurado corretamente
- [x] **Telegram** configurado (bot_token e chat_id)
- [x] **Tickers monitorados** definidos em `monitored_tickers`
- [x] **Estratégias habilitadas** (`daytrade_options.enabled = true`)

### 2. Verificações de Sistema ✅

- [ ] **Python** instalado e funcionando
- [ ] **Dependências** instaladas (`pip install -r requirements.txt`)
- [ ] **Banco de dados** acessível (`agents_orders.db`)
- [ ] **Conexão com internet** ativa (para APIs de mercado)
- [ ] **Telegram** funcionando (testar com `python testar_telegram.py`)

### 3. Configurações de Trading ✅

- [x] **Horário B3** configurado corretamente (10:00 - 17:00)
- [x] **Notificações** habilitadas
- [x] **Comparação matemática** habilitada (`enable_comparison = true`)
- [x] **Trading spot** habilitado (`enable_spot_trading = true`)

### 4. Testes Pré-Operação ✅

Execute os seguintes testes antes de iniciar:

```bash
# 1. Testar Telegram
python testar_telegram.py

# 2. Testar coleta de dados
python testar_coleta_dados.py

# 3. Testar simulação completa
python simular_market_data.py
```

### 5. Iniciar Agentes ✅

```bash
# Iniciar agentes em modo contínuo
python iniciar_agentes.py
```

## 🔍 Durante a Operação

### Monitoramento

- **Logs**: Verificar arquivo `agentes.log`
- **Dashboard**: Acessar `http://localhost:5000` (se API rodando)
- **Telegram**: Receber notificações de:
  - Início do pregão
  - Propostas aprovadas
  - Status a cada 2 horas
  - Fim do pregão

### Verificações Periódicas

- [ ] Agentes estão rodando (verificar logs)
- [ ] Dados de mercado sendo coletados
- [ ] Propostas sendo geradas
- [ ] Notificações sendo enviadas
- [ ] Banco de dados sendo atualizado

## ⚠️ Problemas Comuns

### Agentes não estão gerando propostas

1. Verificar se mercado está aberto (horário B3)
2. Verificar se há tickers configurados
3. Verificar logs para erros
4. Verificar se dados de mercado estão sendo coletados

### Notificações não estão chegando

1. Verificar configuração do Telegram (`config.json`)
2. Testar Telegram: `python testar_telegram.py`
3. Verificar logs para erros de envio

### Erros de conexão com API

1. Verificar conexão com internet
2. Verificar se APIs estão funcionando
3. Verificar logs para detalhes do erro

## 📊 Pós-Operação

### Verificar Resultados

1. **Dashboard**: Verificar atividades do dia
2. **Banco de dados**: Verificar propostas e execuções
3. **Logs**: Revisar erros e avisos
4. **Telegram**: Verificar notificações recebidas

### Limpeza (se necessário)

```bash
# Limpar dados de teste (CUIDADO: remove todos os dados!)
python limpar_banco_teste.py
```

## 🚀 Comandos Úteis

```bash
# Iniciar agentes
python iniciar_agentes.py

# Iniciar API/Dashboard
python api_server.py

# Testar Telegram
python testar_telegram.py

# Ver logs em tempo real (PowerShell)
Get-Content agentes.log -Wait -Tail 50

# Verificar status dos agentes
python -c "from src.monitoring_service import MonitoringService; import json; m = MonitoringService(json.load(open('config.json'))); print(m.get_status())"
```

## 📝 Notas Importantes

1. **Horário B3**: Agentes respeitam horário da B3 (10:00 - 17:00)
2. **Notificações**: Enviadas apenas durante horário de trading
3. **Simulação**: Dados simulados são marcados com `source='simulation'`
4. **Dados Reais**: Dados reais são marcados com `source='real'`
5. **Parar Agentes**: Pressione Ctrl+C para parar graciosamente

## ✅ Status Final

- [ ] Todos os testes passaram
- [ ] Configurações verificadas
- [ ] Agentes iniciados
- [ ] Monitoramento ativo
- [ ] Notificações funcionando

---

**Última atualização**: 27/11/2025
**Versão**: 1.0

