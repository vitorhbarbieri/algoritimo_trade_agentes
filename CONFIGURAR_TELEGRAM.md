# 📱 Configurar Notificações via Telegram

## 🎯 Por que Telegram?

- ✅ **Gratuito** e ilimitado
- ✅ **Fácil de configurar** (5 minutos)
- ✅ **Não precisa expor senhas** no código
- ✅ **Notificações instantâneas** no celular
- ✅ **Suporta mensagens formatadas**
- ✅ **Muito usado para bots de trading**

## 🚀 Passo a Passo

### 1. Criar Bot no Telegram

1. Abra o Telegram e procure por **@BotFather**
2. Envie: `/newbot`
3. Escolha um nome para o bot (ex: "Trading Bot")
4. Escolha um username (ex: "meu_trading_bot")
5. **Copie o TOKEN** que o BotFather fornecer (algo como: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Obter seu Chat ID

#### Opção A: Via @userinfobot (Mais Fácil)
1. Procure por **@userinfobot** no Telegram
2. Envie `/start`
3. Ele retornará seu Chat ID (número como: `123456789`)

#### Opção B: Via @getidsbot
1. Procure por **@getidsbot**
2. Envie `/start`
3. Ele mostrará seu Chat ID

### 3. Configurar no Sistema

#### Opção 1: Via Variáveis de Ambiente (RECOMENDADO - Mais Seguro)

```bash
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
$env:TELEGRAM_CHAT_ID="123456789"

# Windows CMD
set TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
set TELEGRAM_CHAT_ID=123456789

# Linux/Mac
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"
```

#### Opção 2: Via config.json

Edite `config.json`:

```json
{
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
      "chat_id": "123456789"
    }
  }
}
```

⚠️ **ATENÇÃO**: Se usar config.json, adicione-o ao `.gitignore` para não commitar credenciais!

### 4. Testar

Execute o script de teste:

```bash
python testar_notificacoes.py
```

Você deve receber uma mensagem no Telegram! ✅

## 📱 O Que Você Receberá

- 🎯 **Oportunidades encontradas** (com detalhes formatados)
- ⚡ **Propostas de daytrade** (alta prioridade)
- ⚠️ **Erros do sistema** (crítico)
- 🛑 **Kill switch ativado** (crítico)

## 🔒 Segurança

- ✅ Use **variáveis de ambiente** quando possível
- ✅ Se usar config.json, adicione ao `.gitignore`
- ✅ Nunca compartilhe seu bot token
- ✅ O bot só envia mensagens para você (via chat_id)

## ✅ Pronto!

Com o Telegram configurado, você receberá notificações instantâneas no celular quando:
- Sistema encontrar oportunidades
- Gerar propostas importantes
- Ocorrer problemas

**Muito mais prático que email!** 📱✨

