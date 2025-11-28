# ✅ Monitor de Saúde da Captura - Resumo

## 🎯 O Que Foi Criado

Um **agente independente** que monitora a captura de dados de mercado:

### Arquivos Criados

1. **`src/data_health_monitor.py`** - Módulo principal do monitor
2. **`rodar_health_monitor.py`** - Script para iniciar o monitor
3. **`GUIA_HEALTH_MONITOR.md`** - Documentação completa

## ⏱️ Funcionamento

### Verificação de Saúde
- **Frequência**: A cada **1 hora**
- **Verifica**: Banco de dados + API de mercado
- **Corrige**: Problemas automaticamente quando possível

### Relatórios Telegram
- **Horários**: **12:00** e **15:00**
- **Conteúdo**:
  - Status da captura (funcionando/erro)
  - Total de capturas (últimas 24h)
  - Capturas por ticker
  - Capturas com opções
  - Última captura realizada

## 🚀 Como Usar

### Iniciar Monitor

```bash
python rodar_health_monitor.py
```

### Deixar Rodando em Background

**Windows PowerShell:**
```powershell
Start-Process python -ArgumentList "rodar_health_monitor.py" -WindowStyle Hidden
```

**Linux/Mac:**
```bash
nohup python rodar_health_monitor.py > health_monitor.log 2>&1 &
```

## 📊 O Que o Monitor Faz

### A cada hora:
1. ✅ Verifica se banco de dados está funcionando
2. ✅ Verifica se API de mercado está respondendo
3. ✅ Conta quantas capturas foram feitas
4. ✅ Identifica quais tickers foram capturados
5. ✅ Tenta corrigir problemas automaticamente

### Às 12:00 e 15:00:
1. ✅ Gera relatório completo
2. ✅ Envia via Telegram com todas as informações
3. ✅ Inclui estatísticas detalhadas

## 📱 Exemplo de Relatório Telegram

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
• BBDC4.SA: 84 capturas
• ABEV3.SA: 84 capturas
...

✅ CAPTURAS RECENTES (Últimas 2h):
• 24 capturas realizadas
• Última captura há 5 minutos

_Relatório gerado automaticamente pelo DataHealthMonitor_
```

## 🔧 Correção Automática

O monitor tenta corrigir automaticamente:

- ✅ **Banco de dados**: Cria tabelas se não existirem
- ✅ **API**: Reconecta se houver problemas
- ✅ **Conexões**: Reinicializa quando necessário

## 📝 Logs

- **Console**: Saída em tempo real
- **health_monitor.log**: Arquivo de log completo

## ✅ Pronto para Usar

O monitor está **100% funcional** e pronto para rodar junto com os agentes principais!

**Para iniciar:**
```bash
python rodar_health_monitor.py
```

**Deixe rodando junto com:**
```bash
python iniciar_agentes.py
```

---

**Última atualização**: 27/11/2025

