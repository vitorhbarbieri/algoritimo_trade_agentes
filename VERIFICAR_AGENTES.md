# 💚 Sistema de Verificação de Saúde dos Agentes

## 🎯 Objetivo

Garantir que todos os agentes do sistema estão operantes e funcionando corretamente através de verificações automatizadas e monitoramento contínuo.

## 🔍 Como Verificar se os Agentes Estão Operantes

### 1. Via Dashboard Central

1. **Acesse o Dashboard Central:**
   ```bash
   streamlit run dashboard_central.py
   ```

2. **Navegue até a aba "💚 Saúde dos Agentes"**

3. **Clique em "🔄 Executar Verificação"** para testar todos os agentes

4. **Visualize o status:**
   - ✅ **Verde**: Agente operacional
   - ⚠️ **Amarelo**: Agente desabilitado (configuração)
   - ❌ **Vermelho**: Agente com problemas

### 2. Via API REST

#### Verificar Saúde dos Agentes
```bash
GET http://localhost:5000/agents/health
```

**Resposta:**
```json
{
  "status": "success",
  "health_check": {
    "timestamp": "2025-01-20T10:30:00",
    "overall_status": "healthy",
    "agents": {
      "trader_agent": {
        "status": "healthy",
        "name": "TraderAgent",
        "can_generate_proposals": true,
        "strategies_loaded": 1
      },
      "risk_agent": {
        "status": "healthy",
        "name": "RiskAgent",
        "kill_switch_works": true
      },
      "daytrade_strategy": {
        "status": "healthy",
        "name": "DayTradeOptionsStrategy",
        "can_generate_proposals": true
      }
    }
  },
  "recent_activity": {
    "status": "ok",
    "activities": {
      "trader_proposals": 15,
      "risk_evaluations": 12,
      "executions": 8,
      "daytrade_proposals": 5
    }
  }
}
```

#### Executar Teste Completo
```bash
POST http://localhost:5000/agents/test
```

Este endpoint executa testes completos de todos os agentes e retorna resultados detalhados.

### 3. Via Python

```python
from src.agent_health_checker import AgentHealthChecker
import json

# Carregar configuração
with open('config.json', 'r') as f:
    config = json.load(f)

# Criar verificador
checker = AgentHealthChecker(config)

# Verificar saúde
health = checker.check_all_agents()
print(json.dumps(health, indent=2))

# Verificar atividade recente
activity = checker.check_recent_activity(hours=24)
print(json.dumps(activity, indent=2))
```

## 📊 O Que é Verificado

### TraderAgent
- ✅ Capacidade de gerar propostas
- ✅ Estratégias carregadas
- ✅ Processamento de dados de mercado

### RiskAgent
- ✅ Funcionamento do kill switch
- ✅ Validação de propostas
- ✅ Cálculo de limites de risco

### DayTradeOptionsStrategy
- ✅ Configuração habilitada
- ✅ Capacidade de gerar propostas
- ✅ Processamento de dados de opções
- ✅ Cálculo de greeks

### VolArb Strategy
- ✅ Configuração habilitada
- ✅ Threshold configurado
- ✅ Underlying configurado

### Pairs Strategy
- ✅ Configuração habilitada
- ✅ Tickers configurados
- ✅ Z-score threshold configurado

## 📈 Monitoramento de Atividade

O sistema verifica atividade recente (últimas 24 horas):

- **Propostas do TraderAgent**: Total de propostas geradas
- **Avaliações do RiskAgent**: Total de avaliações realizadas
- **Execuções**: Total de execuções realizadas
- **Propostas por Estratégia**:
  - Daytrade Options
  - VolArb
  - Pairs

## 🚨 Alertas e Problemas

### Status "unhealthy"
- Agente não consegue ser inicializado
- Erro ao executar testes básicos
- Dependências faltando

### Status "disabled"
- Estratégia desabilitada na configuração
- Não é um problema, apenas informação

### Sem Atividade Recente
- Nenhuma proposta gerada nas últimas 24h
- Pode indicar:
  - Mercado sem oportunidades
  - Agente não está sendo executado
  - Problemas com dados de mercado

## 🔄 Verificação Automática

### Recomendações

1. **Verificar diariamente** via dashboard
2. **Configurar alertas** se algum agente ficar "unhealthy"
3. **Monitorar atividade** para garantir que agentes estão gerando propostas
4. **Executar testes** após atualizações de código

### Script de Verificação Automática

Crie um script para verificação periódica:

```python
# check_agents.py
import requests
import json
from datetime import datetime

def check_agents_health():
    try:
        response = requests.get('http://localhost:5000/agents/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            health = data.get('health_check', {})
            overall = health.get('overall_status', 'unknown')
            
            if overall == 'healthy':
                print(f"✅ [{datetime.now()}] Todos os agentes estão saudáveis")
            else:
                print(f"⚠️ [{datetime.now()}] Sistema degradado!")
                for agent_name, agent_status in health.get('agents', {}).items():
                    if agent_status.get('status') != 'healthy':
                        print(f"   ❌ {agent_status.get('name')}: {agent_status.get('message')}")
        else:
            print(f"❌ [{datetime.now()}] Erro ao verificar saúde: {response.status_code}")
    except Exception as e:
        print(f"❌ [{datetime.now()}] Erro: {e}")

if __name__ == '__main__':
    check_agents_health()
```

Execute periodicamente:
```bash
# Windows Task Scheduler ou cron
python check_agents.py
```

## 📝 Checklist de Verificação

- [ ] TraderAgent consegue gerar propostas
- [ ] RiskAgent valida propostas corretamente
- [ ] DayTradeOptionsStrategy está habilitada e funcionando
- [ ] VolArb Strategy está configurada
- [ ] Pairs Strategy está configurada
- [ ] Há atividade recente nos logs
- [ ] Todos os agentes retornam status "healthy"
- [ ] Kill switch do RiskAgent funciona
- [ ] Estratégias conseguem processar dados de mercado

## 🛠️ Troubleshooting

### Agente retorna "unhealthy"
1. Verifique logs em `logs/`
2. Verifique configuração em `config.json`
3. Verifique dependências instaladas
4. Execute teste manual via Python

### Sem atividade recente
1. Verifique se monitoramento está ativo
2. Verifique se há dados de mercado disponíveis
3. Execute backtest para gerar atividade
4. Verifique configurações de estratégias

### Erro ao acessar endpoint
1. Verifique se API está rodando: `python run_api.py`
2. Verifique porta (padrão: 5000)
3. Verifique firewall/antivírus
4. Verifique logs do servidor

## ✅ Conclusão

Com este sistema de verificação, você pode:
- ✅ Garantir que todos os agentes estão operantes
- ✅ Identificar problemas rapidamente
- ✅ Monitorar atividade em tempo real
- ✅ Verificar saúde através de múltiplos métodos
- ✅ Receber alertas quando algo está errado

Mantenha verificações regulares para garantir operação contínua do sistema!

