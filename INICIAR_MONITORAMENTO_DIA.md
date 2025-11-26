# 🚀 Guia para Deixar o Sistema Rodando Durante o Dia

## ✅ Checklist Antes de Iniciar

### 1. Configurar Email (OBRIGATÓRIO)
```bash
# 1. Edite config.json e configure:
#    - email_remetente: seu_email@gmail.com
#    - email_senha: senha_de_app_do_gmail
#    - email_destinatario: vitorh.barbieri@gmail.com

# 2. Teste o email:
python testar_email.py
```

### 2. Verificar Saúde dos Agentes
```bash
# Inicie a API:
python run_api.py

# Em outro terminal, execute verificação:
curl http://localhost:5000/agents/test
```

### 3. Verificar Configurações
- ✅ `email_notifications_enabled`: true
- ✅ `daytrade_options.enabled`: true
- ✅ `enable_vol_arb`: true
- ✅ `enable_pairs`: true
- ✅ `monitored_tickers`: lista de tickers configurada

## 🎯 Como Iniciar o Monitoramento

### Opção 1: Via Dashboard Central (Recomendado)

1. **Inicie a API:**
   ```bash
   python run_api.py
   ```

2. **Inicie o Dashboard:**
   ```bash
   streamlit run dashboard_central.py
   ```

3. **No Dashboard:**
   - Acesse a aba "📝 Log de Monitoramento"
   - Clique em "▶️ Iniciar Monitoramento"
   - Configure intervalo (recomendado: 300 segundos = 5 minutos)

### Opção 2: Via API Diretamente

```bash
# Iniciar monitoramento
curl -X POST http://localhost:5000/monitoring/start \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 300}'

# Verificar status
curl http://localhost:5000/monitoring/status
```

### Opção 3: Via Python Script

```python
from src.monitoring_service import MonitoringService
import json

with open('config.json', 'r') as f:
    config = json.load(f)

monitoring = MonitoringService(config)
monitoring.start_monitoring(interval_seconds=300)  # 5 minutos

# Deixar rodando...
import time
try:
    while True:
        time.sleep(60)
        status = monitoring.get_status()
        print(f"Status: {status}")
except KeyboardInterrupt:
    monitoring.stop_monitoring()
```

## 📧 O Que Você Receberá por Email

### Durante o Pregão:

1. **Oportunidades Encontradas**
   - Quando sistema encontra oportunidades
   - Máximo 1 email a cada 5 minutos
   - Inclui: tipo, ativo, score, detalhes

2. **Propostas de Daytrade** ⚡
   - Quando TraderAgent gera proposta de daytrade
   - **Sempre envia** (alta prioridade)
   - Inclui: ativo, strike, delta, momentum, volume ratio

3. **Erros do Sistema** ⚠️
   - Quando ocorre erro crítico
   - **Sempre envia** (alta prioridade)
   - Inclui: tipo de erro, mensagem, detalhes

4. **Kill Switch Ativado** 🛑
   - Quando RiskAgent ativa kill switch
   - **Sempre envia** (crítico, sem cooldown)
   - Inclui: motivo, perda de NAV

## 📊 Monitoramento em Tempo Real

### Via Dashboard Central:
- **Aba "🤖 Atividade dos Agentes"**: Ver todas as atividades
- **Aba "💚 Saúde dos Agentes"**: Status de saúde
- **Aba "📝 Log de Monitoramento"**: Logs em tempo real

### Via API:
```bash
# Status do monitoramento
curl http://localhost:5000/monitoring/status

# Atividade dos agentes
curl http://localhost:5000/agents/activity

# Saúde dos agentes
curl http://localhost:5000/agents/health
```

## 🔄 Durante o Dia

O sistema irá:

1. **A cada 5 minutos** (ou intervalo configurado):
   - Escanear mercado
   - Buscar oportunidades
   - Gerar propostas
   - Enviar emails se encontrar algo importante

2. **Monitorar**:
   - 30 ações (15 brasileiras + 15 americanas)
   - Opções para daytrade
   - Volatility arbitrage
   - Pairs trading

3. **Enviar emails** quando:
   - Encontrar oportunidades
   - Gerar propostas de daytrade
   - Ocorrer erros
   - Kill switch ativar

## ⚠️ Importante

### Antes de Deixar Rodando:

1. ✅ **Teste o email**: `python testar_email.py`
2. ✅ **Verifique saúde**: Execute verificação de agentes
3. ✅ **Configure senha de app do Gmail** (não senha normal!)
4. ✅ **Deixe API rodando**: `python run_api.py`
5. ✅ **Inicie monitoramento** via dashboard ou API

### Durante o Dia:

- 📧 **Verifique emails regularmente**
- 📊 **Monitore dashboard** se possível
- 🔍 **Verifique logs** em `logs/` se necessário

### Ao Final do Dia:

- 📊 **Veja resumo** no dashboard
- 📧 **Verifique emails** recebidos
- 💾 **Salve logs** se necessário

## 🛠️ Comandos Úteis

```bash
# Parar monitoramento
curl -X POST http://localhost:5000/monitoring/stop

# Executar scan manual
curl -X POST http://localhost:5000/monitoring/scan

# Ver status
curl http://localhost:5000/monitoring/status

# Ver saúde dos agentes
curl http://localhost:5000/agents/health
```

## 📝 Logs

Os logs são salvos em:
- `logs/*.jsonl` - Logs estruturados dos agentes
- Console - Output do servidor API

## ✅ Tudo Pronto!

Com tudo configurado, você receberá emails automaticamente quando:
- ✅ Encontrar oportunidades durante o pregão
- ✅ Gerar propostas importantes
- ✅ Ocorrer problemas

**Boa sorte com o trading! 🚀📈**

