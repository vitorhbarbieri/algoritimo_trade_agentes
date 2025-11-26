# 📱 Guia Completo de Notificações

## 🎯 Opções Disponíveis

Você pode receber notificações dos agentes através de:

1. **📱 Telegram** (RECOMENDADO - Mais fácil e prático)
2. **💬 Discord** (Bom para equipe/compartilhamento)
3. **📧 Email** (Tradicional, via variáveis de ambiente)

## 🏆 Recomendação: Telegram

**Por quê?**
- ✅ Configuração em 5 minutos
- ✅ Notificações instantâneas no celular
- ✅ Não precisa expor senhas no código
- ✅ Gratuito e ilimitado
- ✅ Muito usado para bots de trading

## 📱 Configurar Telegram (5 minutos)

### Passo 1: Criar Bot
1. Abra Telegram → Procure **@BotFather**
2. Envie: `/newbot`
3. Escolha nome e username
4. **Copie o TOKEN** fornecido

### Passo 2: Obter seu Chat ID
1. Procure **@userinfobot** no Telegram
2. Envie `/start`
3. **Copie seu Chat ID** (número)

### Passo 3: Configurar

**Opção A: Variáveis de Ambiente (Mais Seguro)**
```bash
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN="seu_token_aqui"
$env:TELEGRAM_CHAT_ID="seu_chat_id_aqui"
```

**Opção B: config.json**
```json
{
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "seu_token_aqui",
      "chat_id": "seu_chat_id_aqui"
    }
  }
}
```

### Passo 4: Testar
```bash
python testar_notificacoes.py
```

**Pronto!** Você receberá notificações no Telegram! ✅

## 💬 Configurar Discord (3 minutos)

### Passo 1: Criar Webhook
1. Discord → Servidor → Configurações → Integrações → Webhooks
2. Criar Webhook → Escolher canal
3. **Copiar URL do Webhook**

### Passo 2: Configurar

**Opção A: Variável de Ambiente**
```bash
$env:DISCORD_WEBHOOK_URL="url_do_webhook_aqui"
```

**Opção B: config.json**
```json
{
  "notifications": {
    "discord": {
      "enabled": true,
      "webhook_url": "url_do_webhook_aqui"
    }
  }
}
```

### Passo 3: Testar
```bash
python testar_notificacoes.py
```

## 📧 Configurar Email (Opcional)

Se preferir email, configure via **variáveis de ambiente** (não no código):

```bash
$env:EMAIL_REMETENTE="seu_email@gmail.com"
$env:EMAIL_SENHA="senha_de_app"
$env:EMAIL_DESTINATARIO="vitorh.barbieri@gmail.com"
```

E no config.json:
```json
{
  "notifications": {
    "email": {
      "enabled": true
    }
  }
}
```

## 🔒 Segurança

### ✅ Boas Práticas:
- Use **variáveis de ambiente** quando possível
- Se usar config.json, adicione ao `.gitignore`
- Nunca compartilhe tokens/webhooks publicamente
- Para Telegram: só você recebe (via chat_id)

### ⚠️ Evite:
- Commitar credenciais no Git
- Compartilhar tokens em fóruns/chats públicos
- Usar senhas normais do Gmail (use senha de app)

## 📬 O Que Você Receberá

### Durante o Pregão:

1. **🎯 Oportunidades Encontradas**
   - Tipo de oportunidade
   - Ativo/Símbolo
   - Score de oportunidade
   - Detalhes (strike, delta, momentum, etc.)

2. **⚡ Propostas de Daytrade** (Alta Prioridade)
   - Ativo
   - Strike e Delta
   - Momentum intraday
   - Volume ratio
   - **Sempre envia** (sem cooldown)

3. **⚠️ Erros do Sistema** (Crítico)
   - Tipo de erro
   - Mensagem de erro
   - Detalhes técnicos
   - **Sempre envia** (sem cooldown)

4. **🛑 Kill Switch Ativado** (Crítico)
   - Motivo da ativação
   - Perda de NAV
   - **Sempre envia** (sem cooldown)

## 🧪 Testar Agora

Execute:
```bash
python testar_notificacoes.py
```

Este script:
- ✅ Verifica quais canais estão configurados
- ✅ Testa cada canal individualmente
- ✅ Envia notificações de teste
- ✅ Mostra status de cada canal

## 📊 Comparação

| Recurso | Telegram | Discord | Email |
|---------|----------|---------|-------|
| Facilidade | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Velocidade | ⚡⚡⚡⚡⚡ | ⚡⚡⚡⚡ | ⚡⚡⚡ |
| Celular | ✅ Sim | ✅ Sim | ✅ Sim |
| Formatação | ✅ Sim | ✅ Sim | ✅ Sim |
| Compartilhamento | ❌ Individual | ✅ Canal | ✅ Sim |
| Configuração | 5 min | 3 min | 10 min |

## ✅ Recomendação Final

**Use Telegram!** É a opção mais prática e rápida para receber notificações dos agentes durante o pregão.

## 🚀 Próximos Passos

1. Escolha seu método preferido (Telegram recomendado)
2. Configure seguindo os guias específicos
3. Teste: `python testar_notificacoes.py`
4. Deixe o sistema rodando e receba notificações! 📱✨

