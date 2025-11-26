# ⏰ Sistema de Horário B3 e Notificações Automáticas

## 🎯 Funcionalidades Implementadas

### 1. Horário de Funcionamento da B3
- ✅ Agente funciona apenas durante horário da B3
- ✅ Pré-mercado: 09:45 - 10:00
- ✅ Trading: 10:00 - 17:00
- ✅ Pós-mercado: 17:00 - 17:30
- ✅ Não funciona em finais de semana

### 2. Notificações Automáticas

#### 🚀 Notificação de Início
- **Quando:** Ao iniciar atividades (09:45)
- **Conteúdo:**
  - Horário de início
  - Status do mercado (Pré-mercado/Mercado Aberto)
  - Horário de funcionamento

#### 🏁 Notificação de Fim
- **Quando:** Ao finalizar atividades (17:00)
- **Conteúdo:**
  - Horário de fim
  - Tempo de operação do dia
  - Resumo do dia:
    - Total de propostas geradas
    - Propostas aprovadas/rejeitadas
    - Execuções realizadas

#### 📊 Notificação de Status (a cada 2 horas)
- **Quando:** A cada 2 horas durante o pregão
- **Conteúdo:**
  - Horário atual
  - Tempo de operação
  - Estatísticas do dia:
    - Total de propostas
    - Aprovadas/Rejeitadas/Modificadas
    - Execuções
    - Estatísticas por estratégia

## ⏰ Horários da B3

### Segunda a Sexta:
- **09:45** - Pré-mercado (início das atividades)
- **10:00** - Abertura do mercado
- **17:00** - Fechamento do mercado (fim das atividades)
- **17:30** - Pós-fechamento

### Finais de Semana:
- ❌ Não funciona (sábado e domingo)

## 📱 Exemplo de Notificações

### Notificação de Início:
```
🚀 AGENTE DE DAYTRADE INICIADO

Horário: 20/01/2025 09:45:00 (B3)
Status: Pré-Mercado

O agente está agora monitorando o mercado e gerando propostas de daytrade.

Horário de funcionamento:
• Pré-mercado: 09:45 - 10:00
• Trading: 10:00 - 17:00
• Fechamento: 17:00

Você receberá atualizações a cada 2 horas durante o pregão.
```

### Notificação de Status (2h):
```
📊 STATUS DO AGENTE - ATUALIZAÇÃO

Horário: 20/01/2025 12:00:00 (B3)
Tempo de operação: 2h 15min

Estatísticas do Dia:
• Total de propostas: 15
• Aprovadas: 8
• Rejeitadas: 7
• Modificadas: 0
• Execuções: 8

Por Estratégia:
• Daytrade Options: 10
• Vol Arb: 5

Próxima atualização: Em 2 horas
```

### Notificação de Fim:
```
🏁 AGENTE DE DAYTRADE FINALIZADO

Horário: 20/01/2025 17:00:00 (B3)
Tempo de operação: 7h 15min

Resumo do Dia:
• Propostas geradas: 25
• Propostas aprovadas: 12
• Propostas rejeitadas: 13
• Execuções: 12

O agente encerrou as atividades do dia. Retomará amanhã às 09:45.
```

## 🔧 Como Funciona

### 1. Verificação de Horário
O sistema verifica continuamente:
- Se é dia útil (segunda a sexta)
- Se está no horário de trading (10:00 - 17:00)
- Se deve iniciar (09:45)
- Se deve parar (17:00)

### 2. Notificações Automáticas
- **Início:** Enviada quando detecta início do pregão (09:45)
- **Status:** Enviada a cada 2 horas durante o pregão
- **Fim:** Enviada quando detecta fechamento (17:00)

### 3. Integração com Banco de Dados
As estatísticas são buscadas do banco `agents_orders.db`:
- Propostas do dia
- Avaliações do RiskAgent
- Execuções realizadas
- Performance

## 🚀 Uso

### Iniciar Monitoramento:
```bash
python run_api.py
# No dashboard, clique em "Iniciar Monitoramento"
```

O sistema automaticamente:
1. ✅ Verifica horário B3
2. ✅ Inicia às 09:45
3. ✅ Envia notificação de início
4. ✅ Envia notificações a cada 2h
5. ✅ Para às 17:00
6. ✅ Envia notificação de fim

## 📋 Requisitos

- `pytz` - Para timezone da B3 (America/Sao_Paulo)
- Sistema de notificações configurado (Telegram/Discord)

### Instalar pytz:
```bash
pip install pytz
```

## ✅ Status

**Implementado:**
- ✅ TradingSchedule com horário B3
- ✅ Verificação automática de horário
- ✅ Notificação de início
- ✅ Notificação de fim
- ✅ Notificação de status (2h)
- ✅ Integração com MonitoringService
- ✅ Resumo do dia do banco de dados

**Funcionando automaticamente!** 🎉

## 💡 Observações

- O sistema usa timezone `America/Sao_Paulo` (horário de Brasília)
- Não considera feriados (pode ser adicionado depois)
- Notificações são enviadas via Telegram/Discord configurado
- Todas as estatísticas vêm do banco de dados em tempo real

