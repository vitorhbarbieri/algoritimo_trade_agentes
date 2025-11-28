# 🤖 Agentes Integrados - Guia Completo

## ✅ Integração Completa

Os agentes agora estão **totalmente integrados** e rodam automaticamente juntos!

## 🚀 Como Iniciar

### Comando Único

```bash
python iniciar_agentes.py
```

Este comando agora inicia **TUDO** automaticamente:
- ✅ Agentes de trading principais
- ✅ Monitor de saúde da captura de dados
- ✅ Verificações automáticas
- ✅ Relatórios periódicos

## 📊 O Que Roda Automaticamente

### 1. Agentes de Trading (Thread Principal)

- **Frequência**: A cada 5 minutos durante o pregão
- **Funções**:
  - Escaneiam mercado
  - Coletam dados de spot e opções
  - Geram propostas de trading
  - Avaliam risco
  - Enviam notificações Telegram
  - Salvam tudo no banco de dados

### 2. Monitor de Saúde (Thread Separada)

- **Frequência**: A cada 1 hora
- **Funções**:
  - Verifica saúde do banco de dados
  - Verifica saúde da API de mercado
  - Corrige problemas automaticamente
  - Envia relatórios às 12:00 e 15:00

## 📱 Notificações que Você Receberá

### Durante o Pregão

1. **Início do pregão** (10:00)
   - Notificação de início dos agentes

2. **Propostas aprovadas** (quando houver)
   - Formato melhorado com todas as informações
   - Botões de aprovação/cancelamento

3. **Status a cada 2 horas**
   - Resumo de atividades

4. **Relatório de captura** (12:00)
   - Status da captura
   - Total de capturas
   - Capturas por ticker

5. **Relatório de captura** (15:00)
   - Status da captura
   - Total de capturas
   - Capturas por ticker

6. **Fim do pregão** (17:00)
   - Resumo final do dia

## 🔧 Funcionalidades Automáticas

### Correção Automática

O monitor de saúde tenta corrigir automaticamente:
- ✅ Problemas no banco de dados
- ✅ Problemas com API
- ✅ Conexões perdidas
- ✅ Tabelas faltantes

### Reinicialização Automática

Se o monitor de saúde parar por algum motivo:
- ✅ Detecta automaticamente
- ✅ Reinicia em nova thread
- ✅ Continua funcionando normalmente

## 📝 Logs

Todos os logs são salvos em:
- **`agentes.log`** - Log principal (agentes + monitor)
- **Console** - Saída em tempo real

### Identificação nos Logs

- `[HEALTH]` - Logs do monitor de saúde
- Logs normais - Agentes de trading

## 🛑 Como Parar

### Método 1: Ctrl+C
Pressione `Ctrl+C` no terminal - **para tudo automaticamente**

### Método 2: Fechar Terminal
Fechar o terminal também para todos os processos

## ⚙️ Configuração

Tudo usa o mesmo `config.json`:

```json
{
  "monitored_tickers": ["PETR4.SA", "VALE3.SA", ...],
  "daytrade_options": {
    "enabled": true,
    "enable_spot_trading": true,
    "enable_comparison": true
  },
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "SEU_TOKEN",
      "chat_id": "SEU_CHAT_ID"
    }
  }
}
```

## 📊 Estrutura de Threads

```
Processo Principal
├── Thread Principal
│   └── MonitoringService (Agentes de Trading)
│       └── Loop a cada 5 minutos
│
└── Thread HealthMonitor (daemon)
    └── DataHealthMonitor
        └── Loop a cada 1 hora
            ├── Verificação de saúde
            └── Relatórios às 12:00 e 15:00
```

## ✅ Vantagens da Integração

1. **Um único comando** para iniciar tudo
2. **Gerenciamento unificado** de logs
3. **Parada sincronizada** com Ctrl+C
4. **Reinicialização automática** se necessário
5. **Monitoramento completo** do sistema

## 🎯 Resumo

| Componente | Frequência | Thread |
|------------|------------|--------|
| **Agentes Trading** | 5 minutos | Principal |
| **Monitor Saúde** | 1 hora | Separada (daemon) |
| **Relatórios** | 12:00 e 15:00 | Automático |

## 🚀 Pronto para Operação!

Agora você só precisa executar:

```bash
python iniciar_agentes.py
```

E **TUDO** roda automaticamente:
- ✅ Agentes de trading
- ✅ Monitor de saúde
- ✅ Verificações automáticas
- ✅ Correções automáticas
- ✅ Relatórios periódicos

**Deixe rodando e acompanhe pelos logs e Telegram!** 🎉

---

**Última atualização**: 27/11/2025

