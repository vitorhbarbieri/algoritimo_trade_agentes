# 📱 Como Obter seu Chat ID do Telegram

## ⚙️ Configuração do Token

O token do bot deve ser configurado via **variável de ambiente** ou no `config.json` (não commitado).

## 🚀 Método Mais Fácil (2 minutos)

### Passo 1: Obter Chat ID

1. **Abra o Telegram** no seu celular
2. **Procure por @userinfobot**
3. **Envie `/start`**
4. Ele retornará seu Chat ID (um número como `123456789`)
5. **Copie esse número**

### Passo 2: Configurar

Execute:

```bash
python configurar_telegram_rapido.py
```

Quando pedir, cole o Chat ID que você copiou.

### Passo 3: Testar

```bash
python testar_notificacoes.py
```

Você deve receber uma mensagem no Telegram! ✅

## 🔄 Método Alternativo

Se preferir configurar manualmente:

1. Obtenha seu Chat ID via @userinfobot (como acima)
2. Edite `config.json` e adicione o Chat ID:

```json
{
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "SEU_TOKEN_AQUI",
      "chat_id": "SEU_CHAT_ID_AQUI"
    }
  }
}
```

## ✅ Pronto!

Depois de configurar, você receberá notificações no Telegram automaticamente! 📱✨

