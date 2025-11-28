# 🔍 Guia do Monitor de Saúde da Captura de Dados

## 📋 Visão Geral

O **DataHealthMonitor** é um agente independente que:
- ✅ Verifica a saúde da captura de dados **a cada hora**
- ✅ Corrige problemas automaticamente quando possível
- ✅ Envia relatórios via Telegram às **12:00** e **15:00**
- ✅ Monitora continuamente o funcionamento do sistema

## 🚀 Como Iniciar

### Opção 1: Script Principal (Recomendado)

```bash
python rodar_health_monitor.py
```

### Opção 2: Em Background (Windows PowerShell)

```powershell
Start-Process python -ArgumentList "rodar_health_monitor.py" -WindowStyle Hidden
```

### Opção 3: Em Background (Linux/Mac)

```bash
nohup python rodar_health_monitor.py > health_monitor.log 2>&1 &
```

## ⏱️ Funcionamento

### Verificação de Saúde (A cada 1 hora)

O monitor executa verificações completas a cada hora:

1. **Verifica Banco de Dados**:
   - Se tabela `market_data_captures` existe
   - Última captura realizada
   - Quantas capturas nas últimas 2 horas
   - Capturas por ticker

2. **Verifica API de Mercado**:
   - Se API está respondendo
   - Se consegue buscar dados de teste
   - Se há erros de conexão

3. **Correção Automática**:
   - Cria tabelas se não existirem
   - Reconecta com API se necessário
   - Tenta resolver problemas comuns

### Relatórios Telegram (12:00 e 15:00)

Você receberá mensagens no Telegram com:

```
✅ RELATÓRIO DE CAPTURA DE DADOS

Data/Hora: 28/11/2025 12:00:00
Status: FUNCIONANDO

📊 ESTATÍSTICAS (Últimas 24h):
• Total de capturas: 84
• Capturas com opções: 45
• Última captura: 2025-11-28T11:55:00

📈 CAPTURAS POR TICKER:
• PETR4.SA: 84 capturas
• VALE3.SA: 84 capturas
• ITUB4.SA: 84 capturas
...

✅ CAPTURAS RECENTES (Últimas 2h):
• 24 capturas realizadas
• Última captura há 5 minutos
```

## 🔧 Funcionalidades

### 1. Verificação de Banco de Dados

```python
db_health = monitor.check_database_health()
# Retorna:
# {
#   'status': 'OK' | 'WARNING' | 'ERROR',
#   'last_capture': '2025-11-28T11:55:00',
#   'recent_captures': 24,
#   'ticker_stats': {'PETR4.SA': 24, ...},
#   'can_fix': True/False
# }
```

### 2. Verificação de API

```python
api_health = monitor.check_api_health()
# Retorna:
# {
#   'status': 'OK' | 'WARNING' | 'ERROR',
#   'message': 'API funcionando',
#   'can_fix': True/False
# }
```

### 3. Correção Automática

O monitor tenta corrigir automaticamente:
- ✅ Cria tabelas faltantes no banco
- ✅ Reconecta com API
- ✅ Reinicializa conexões

### 4. Estatísticas

```python
stats = monitor.get_capture_statistics(hours=24)
# Retorna:
# {
#   'total_captures': 84,
#   'ticker_captures': {'PETR4.SA': 84, ...},
#   'captures_with_options': 45,
#   'last_capture': '2025-11-28T11:55:00',
#   'first_capture': '2025-11-27T12:00:00'
# }
```

## 📊 Logs

Os logs são salvos em:
- **Console**: Saída em tempo real
- **health_monitor.log**: Arquivo de log completo

### Exemplo de Log

```
2025-11-28 12:00:00 - INFO - ======================================================================
2025-11-28 12:00:00 - INFO - VERIFICAÇÃO DE SAÚDE DA CAPTURA DE DADOS
2025-11-28 12:00:00 - INFO - ======================================================================
2025-11-28 12:00:00 - INFO - Verificando banco de dados...
2025-11-28 12:00:00 - INFO - Status BD: OK - OK
2025-11-28 12:00:00 - INFO - Verificando API de mercado...
2025-11-28 12:00:00 - INFO - Status API: OK - API funcionando
2025-11-28 12:00:00 - INFO - Total de capturas (24h): 84
2025-11-28 12:00:00 - INFO - Tickers com capturas: 30
```

## ⚙️ Configuração

O monitor usa as mesmas configurações do `config.json`:

```json
{
  "monitored_tickers": ["PETR4.SA", "VALE3.SA", ...],
  "market_data_api": "yfinance",
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "SEU_TOKEN",
      "chat_id": "SEU_CHAT_ID"
    }
  }
}
```

## 🛑 Como Parar

### Método 1: Ctrl+C
Pressione `Ctrl+C` no terminal onde o monitor está rodando.

### Método 2: Via Processo (Windows)
```powershell
Get-Process python | Where-Object {$_.Path -like "*rodar_health_monitor*"} | Stop-Process
```

### Método 3: Via Processo (Linux/Mac)
```bash
pkill -f rodar_health_monitor.py
```

## 📱 Mensagens Telegram

### Horários de Relatório

- **12:00** - Relatório do meio-dia
- **15:00** - Relatório da tarde

### Conteúdo dos Relatórios

1. **Status Geral**: Funcionando / Atenção / Erro
2. **Estatísticas**: Total de capturas, capturas com opções
3. **Capturas por Ticker**: Top 10 tickers mais capturados
4. **Capturas Recentes**: Últimas 2 horas
5. **Avisos**: Problemas detectados e correções aplicadas

## 🔍 Verificação Manual

Você pode executar verificações manuais:

```python
from src.data_health_monitor import DataHealthMonitor
import json

with open('config.json') as f:
    config = json.load(f)

monitor = DataHealthMonitor(config)
result = monitor.run_health_check()
```

## ⚠️ Problemas Comuns

### Monitor não envia relatórios

1. Verificar se Telegram está configurado
2. Verificar se horário está correto (12:00 ou 15:00)
3. Verificar logs em `health_monitor.log`

### Erros de banco de dados

O monitor tenta corrigir automaticamente:
- Cria tabelas se não existirem
- Verifica integridade do banco

### Erros de API

O monitor tenta corrigir automaticamente:
- Reconecta com API
- Testa novamente após correção

## ✅ Checklist

Antes de deixar rodando:

- [x] Telegram configurado e testado
- [x] Banco de dados acessível
- [x] API de mercado funcionando
- [x] Script de inicialização criado
- [x] Logs configurados
- [ ] Monitor iniciado e rodando

## 🎯 Resumo

| Item | Valor |
|------|-------|
| **Verificação** | A cada 1 hora |
| **Relatórios** | 12:00 e 15:00 |
| **Correção** | Automática |
| **Notificações** | Via Telegram |
| **Logs** | `health_monitor.log` |

---

**Última atualização**: 27/11/2025

