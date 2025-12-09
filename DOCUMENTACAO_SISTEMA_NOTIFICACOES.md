# 📱 DOCUMENTAÇÃO DO SISTEMA DE NOTIFICAÇÕES

## ✅ Versão Atual Mantida

**`UnifiedNotifier`** é a versão atual e única que deve ser usada para envio de mensagens via Telegram.

### Localização
- **Arquivo:** `src/notifications.py`
- **Classe:** `UnifiedNotifier`

### Características
1. **Sistema Unificado:** Gerencia múltiplos canais (Telegram, Discord, Email)
2. **Salvamento Automático:** Todas as mensagens são salvas automaticamente na tabela `telegram_messages_sent`
3. **Rastreabilidade Completa:** Registra sucesso/falha, tipo de mensagem, prioridade, etc.
4. **Tipos de Mensagem Suportados:**
   - `status` - Mensagens de status do agente (a cada 2 horas)
   - `proposal` - Propostas de ordem
   - `opportunity` - Oportunidades de trading
   - `error` - Erros do sistema
   - `kill_switch` - Ativação de kill switch
   - `market_open` - Abertura de mercado
   - `market_close` - Fechamento de mercado
   - `eod` - Fechamento EOD e análises
   - `health` - Relatórios de saúde/captura de dados
   - `other` - Outras mensagens

## 📊 Estrutura de Dados

### Tabela `telegram_messages_sent`
```sql
CREATE TABLE telegram_messages_sent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'telegram',
    message_type TEXT NOT NULL,
    title TEXT,
    message_text TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    proposal_id TEXT,
    success INTEGER NOT NULL DEFAULT 1,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Como Usar

### Exemplo Básico
```python
from src.notifications import UnifiedNotifier
from src.orders_repository import OrdersRepository

# Inicializar
orders_repo = OrdersRepository()
notifier = UnifiedNotifier(config, orders_repo=orders_repo)

# Enviar mensagem simples
notifier.send(
    message="Mensagem de teste",
    title="Título",
    priority='normal',
    message_type='other'
)

# Enviar proposta
notifier.send(
    message="Detalhes da proposta",
    title="Nova Proposta",
    priority='high',
    message_type='proposal',
    proposal_id='1234'
)
```

### Exemplo com Proposta Completa
```python
# Para propostas com botões de aprovação, usar TelegramNotifier diretamente
# (mas através do UnifiedNotifier)
telegram_channel = None
for channel_name, channel in notifier.channels:
    if channel_name == 'telegram':
        telegram_channel = channel
        break

if telegram_channel:
    telegram_channel.send_proposal_with_approval({
        'proposal_id': '1234',
        'symbol': 'PETR4.SA',
        'side': 'BUY',
        'quantity': 100,
        'price': 32.50,
        'metadata': {...}
    })
```

## 🚫 Código Antigo Removido

### ❌ NÃO USAR MAIS:
1. **Chamadas diretas a `telegram_channel.send()`** - Substituídas por `notifier.send()`
2. **Múltiplos sistemas de notificação** - Tudo centralizado no `UnifiedNotifier`
3. **Envio sem salvamento** - Todas as mensagens são salvas automaticamente

### ✅ Código Atualizado:
- `monitoring_service.py` - Usa apenas `self.notifier.send()`
- `data_health_monitor.py` - Usa apenas `self.notifier.send()`
- `notifications.py` - `UnifiedNotifier` salva todas as mensagens

## 📈 Mensagens de Status (A cada 2 horas)

As mensagens de status agora incluem:
1. **Estatísticas do Dia:**
   - Total de propostas
   - Aprovadas/Rejeitadas/Modificadas
   - Execuções

2. **Por Estratégia:**
   - Contagem por tipo de estratégia

3. **📊 CAPTURA DE DADOS DE MERCADO:** (NOVO)
   - Total de capturas hoje
   - Ativos únicos monitorados
   - Contagem por tipo (Spot/Opções/Futuros)
   - Timestamp da última captura

## 🔍 Consultar Mensagens Enviadas

```python
from src.orders_repository import OrdersRepository

repo = OrdersRepository()

# Buscar todas as mensagens de hoje
messages = repo.get_telegram_messages(
    start_date='2025-12-08 00:00:00',
    end_date='2025-12-08 23:59:59'
)

# Buscar apenas propostas
proposals = repo.get_telegram_messages(
    message_type='proposal',
    limit=100
)

# Buscar mensagens de status
status_messages = repo.get_telegram_messages(
    message_type='status',
    limit=50
)
```

## ✅ Confirmação da Versão Atual

**Versão Mantida:** `UnifiedNotifier` em `src/notifications.py`

**Características Confirmadas:**
- ✅ Salvamento automático de todas as mensagens
- ✅ Suporte a múltiplos tipos de mensagem
- ✅ Informações de captura de dados nas mensagens de status
- ✅ Rastreabilidade completa (sucesso/falha)
- ✅ Integração com `OrdersRepository` para persistência

**Código Removido/Atualizado:**
- ✅ Removidas chamadas diretas a `telegram_channel.send()` em `monitoring_service.py`
- ✅ Atualizado `data_health_monitor.py` para usar `UnifiedNotifier`
- ✅ Adicionada tabela `telegram_messages_sent` para rastreabilidade
- ✅ Adicionadas informações de captura de dados nas mensagens de status

