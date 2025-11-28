# Configuração Rápida do Telegram

## Problema Identificado
O Telegram não está configurado. O `bot_token` e `chat_id` estão vazios no `config.json`.

## Solução Rápida

### Opção 1: Configurar no config.json (Recomendado)

1. Abra o arquivo `config.json`
2. Localize a seção `notifications.telegram`
3. Preencha os campos:

```json
"notifications": {
  "telegram": {
    "enabled": true,
    "bot_token": "SEU_TOKEN_AQUI",
    "chat_id": "SEU_CHAT_ID_AQUI"
  }
}
```

### Opção 2: Usar Variáveis de Ambiente

No PowerShell:
```powershell
$env:TELEGRAM_BOT_TOKEN = "SEU_TOKEN_AQUI"
$env:TELEGRAM_CHAT_ID = "SEU_CHAT_ID_AQUI"
```

## Como Obter o Token e Chat ID

### Token do Bot:
1. Abra o Telegram
2. Procure por `@BotFather`
3. Envie `/newbot` e siga as instruções
4. Copie o token fornecido

### Chat ID:
1. Envie uma mensagem para seu bot
2. Execute: `python obter_chat_id_telegram.py`
3. Ou use: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
4. Procure o `chat.id` na resposta

## Testar Configuração

Após configurar, execute:
```bash
python testar_telegram.py
```

Este script vai:
- Verificar se o token e chat_id estão configurados
- Testar o envio de uma mensagem de teste
- Mostrar erros se houver problemas

## Token Fornecido Anteriormente

Você forneceu este token anteriormente:
- Token: `7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM`
- Telefone: `+5511996204459`

**IMPORTANTE**: Por segurança, este token foi removido do código. Você precisa configurá-lo novamente no `config.json` ou via variáveis de ambiente.
