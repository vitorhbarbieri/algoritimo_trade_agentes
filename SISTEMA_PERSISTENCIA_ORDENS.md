# 💾 Sistema de Persistência de Ordens - Backtest em Tempo Real

## 🎯 Objetivo

Salvar **todas as ordens sugeridas pelos agentes** em banco de dados SQLite para:
- ✅ Acompanhamento em tempo real (backtest durante o dia)
- ✅ Análise de performance posterior
- ✅ Visualização no dashboard central
- ✅ Histórico completo de todas as operações

## 📊 Como Funciona

### 1. Fluxo Automático

```
1. MonitoringService escaneia mercado (a cada 5 min)
   ↓
2. TraderAgent gera propostas
   ↓
3. OrdersRepository.save_proposal() → Salva no banco
   ↓
4. RiskAgent avalia propostas
   ↓
5. OrdersRepository.save_risk_evaluation() → Salva avaliação
   ↓
6. ExecutionSimulator executa (simulado)
   ↓
7. OrdersRepository.save_execution() → Salva execução
   ↓
8. Snapshot de performance periódico
   ↓
9. OrdersRepository.save_performance_snapshot() → Salva performance
```

### 2. Banco de Dados

**Arquivo:** `agents_orders.db` (SQLite)

**Tabelas:**

1. **`proposals`** - Propostas geradas pelo TraderAgent
   - proposal_id, timestamp, strategy, symbol, side, quantity, price, metadata

2. **`risk_evaluations`** - Avaliações do RiskAgent
   - proposal_id, decision (APPROVE/MODIFY/REJECT), reason, details

3. **`executions`** - Execuções simuladas
   - order_id, proposal_id, symbol, side, quantity, price, slippage, commission

4. **`performance_snapshots`** - Snapshots de performance
   - timestamp, nav, total_pnl, daily_pnl, total_trades, open_positions

5. **`open_positions`** - Posições abertas
   - symbol, side, quantity, avg_price, unrealized_pnl, greeks

## 🔄 Integração Automática

### TraderAgent
- ✅ Salva automaticamente todas as propostas geradas
- ✅ Inclui metadados completos (delta, gamma, momentum, etc.)

### RiskAgent
- ✅ Salva todas as avaliações (APPROVE/MODIFY/REJECT)
- ✅ Registra motivo da decisão
- ✅ Salva modificações (se MODIFY)

### ExecutionSimulator
- ✅ Salva todas as execuções simuladas
- ✅ Inclui slippage, comissões, custos

## 📈 Backtest em Tempo Real

O sistema funciona como um **backtest contínuo**:

1. **Coleta dados reais** via API (Yahoo Finance)
2. **Gera propostas** baseadas em dados reais
3. **Avalia riscos** com regras reais
4. **Simula execuções** com slippage/comissões
5. **Salva tudo** no banco de dados
6. **Acompanha performance** em tempo real

**Importante:** Nenhuma ordem real é executada! Tudo é simulado e salvo para análise.

## 📊 Visualização no Dashboard

O dashboard central mostra:

- **Propostas do dia:** Quantas foram geradas, por estratégia
- **Taxa de aprovação:** Quantas foram aprovadas/rejeitadas
- **Execuções:** Ordens simuladas executadas
- **Performance:** PnL acumulado, trades ganhadores/perdedores
- **Gráficos:** Evolução do NAV, PnL diário, etc.

## 🔍 Consultas Úteis

### Ver todas as propostas de daytrade hoje:
```python
from src.orders_repository import OrdersRepository
repo = OrdersRepository()
proposals = repo.get_proposals(
    strategy='daytrade_options',
    start_date='2025-01-20 00:00:00',
    end_date='2025-01-20 23:59:59'
)
```

### Ver resumo do dia:
```python
summary = repo.get_daily_summary('2025-01-20')
print(summary)
# {
#   'date': '2025-01-20',
#   'total_proposals': 15,
#   'proposals_by_strategy': {'daytrade_options': 10, 'vol_arb': 5},
#   'total_executions': 8,
#   'total_approved': 8,
#   'total_rejected': 7,
#   'total_pnl': 1250.50
# }
```

### Ver snapshots de performance:
```python
snapshots = repo.get_performance_snapshots(
    start_date='2025-01-20 00:00:00',
    end_date='2025-01-20 23:59:59'
)
```

## ✅ Status

**Implementado:**
- ✅ OrdersRepository criado
- ✅ Integrado com TraderAgent
- ✅ Integrado com RiskAgent
- ✅ Integrado com ExecutionSimulator
- ✅ Banco de dados SQLite configurado
- ✅ Todas as tabelas criadas

**Próximos Passos:**
- ⏳ Adicionar snapshots periódicos de performance
- ⏳ Integrar com dashboard central
- ⏳ Criar visualizações de performance

## 🚀 Uso

O sistema já está funcionando automaticamente! Quando você iniciar o monitoramento:

```bash
python run_api.py
# No dashboard, clique em "Iniciar Monitoramento"
```

Todas as ordens serão salvas automaticamente em `agents_orders.db`!

## 📁 Arquivos

- `src/orders_repository.py` - Repositório de persistência
- `agents_orders.db` - Banco de dados SQLite (criado automaticamente)
- `SISTEMA_PERSISTENCIA_ORDENS.md` - Este documento

## 💡 Vantagens

1. **Histórico Completo:** Todas as ordens ficam salvas
2. **Análise Posterior:** Pode analisar performance depois
3. **Backtest Real:** Usa dados reais, simula execuções
4. **Sem Risco:** Nenhuma ordem real é executada
5. **Dashboard:** Visualização em tempo real

**Perfeito para acompanhar a performance dos agentes durante o dia!** 🚀

