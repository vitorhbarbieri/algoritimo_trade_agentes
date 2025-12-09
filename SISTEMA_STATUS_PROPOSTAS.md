# ✅ Sistema de Status de Propostas Implementado

## 📋 Status das Propostas

Agora todas as propostas são rastreadas com os seguintes status:

1. **gerada** - Proposta criada pelo TraderAgent mas **não aprovada** pelo RiskAgent
2. **enviada** - Proposta **aprovada pelo RiskAgent** e enviada ao Telegram
3. **aprovada** - Proposta **aprovada pelo usuário** via Telegram (`/aprovar ID`)
4. **cancelada** - Proposta **cancelada pelo usuário** via Telegram (`/cancelar ID`)

## 🔄 Fluxo de Status

```
TraderAgent gera proposta
    ↓
Status: 'gerada' (salvo no banco)
    ↓
RiskAgent avalia
    ↓
Se APROVADA:
    ↓
Status: 'enviada' (atualizado no banco)
    ↓
Enviada ao Telegram
    ↓
Usuário responde:
    ├─ /aprovar ID → Status: 'aprovada'
    └─ /cancelar ID → Status: 'cancelada'
```

## 📊 Banco de Dados

### Colunas Adicionadas:
- `status` - Status atual da proposta ('gerada', 'enviada', 'aprovada', 'cancelada')
- `status_updated_at` - Timestamp da última atualização de status

### Métodos Disponíveis:

1. **`update_proposal_status(proposal_id, status)`**
   - Atualiza o status de uma proposta
   - Valida que o status é válido
   - Registra timestamp da atualização

2. **`get_proposals_by_status(status=None)`**
   - Busca propostas filtradas por status
   - Se `status=None`, retorna todas
   - Ordena por `created_at DESC`

## 🔧 Integrações

### 1. TraderAgent (`src/agents.py`)
- Ao gerar proposta, marca como `status='gerada'`

### 2. MonitoringService (`src/monitoring_service.py`)
- Quando RiskAgent aprova proposta, atualiza para `status='enviada'`
- Antes de enviar ao Telegram

### 3. TelegramPolling (`src/telegram_polling.py`)
- Quando usuário aprova: atualiza para `status='aprovada'`
- Quando usuário cancela: atualiza para `status='cancelada'`

## 📈 Consultas Úteis

### Propostas geradas mas não aprovadas pelo RiskAgent:
```python
repo = OrdersRepository()
geradas = repo.get_proposals_by_status('gerada')
```

### Propostas enviadas ao Telegram:
```python
enviadas = repo.get_proposals_by_status('enviada')
```

### Propostas aprovadas pelo usuário:
```python
aprovadas = repo.get_proposals_by_status('aprovada')
```

### Propostas canceladas:
```python
canceladas = repo.get_proposals_by_status('cancelada')
```

### Todas as propostas com seus status:
```python
todas = repo.get_proposals()
# Coluna 'status' mostra o status atual de cada proposta
```

## ✅ Migração

Script de migração executado:
- ✅ Coluna `status` adicionada
- ✅ Coluna `status_updated_at` adicionada
- ✅ Propostas existentes marcadas como 'gerada'

## 🎯 Benefícios

1. **Rastreabilidade Completa**: Saber exatamente em que etapa cada proposta está
2. **Análise de Conversão**: Ver quantas propostas são geradas vs. aprovadas
3. **Debugging**: Identificar onde propostas estão sendo perdidas
4. **Métricas**: Taxa de aprovação do RiskAgent, taxa de aprovação do usuário

---

**Data**: 01/12/2025
**Status**: ✅ IMPLEMENTADO E FUNCIONANDO


