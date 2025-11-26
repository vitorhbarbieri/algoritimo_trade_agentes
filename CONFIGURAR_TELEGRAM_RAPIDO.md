# 📱 Configuração Rápida do Telegram

## ⚙️ Configuração do Token

O token do bot deve ser configurado via **variável de ambiente** ou no `config.json` (não commitado).

## 🚀 Passo a Passo (2 minutos)

### 1. Obter seu Chat ID

**Opção A: Via @userinfobot (Mais Fácil)**
1. Abra o Telegram
2. Procure por **@userinfobot**
3. Envie `/start`
4. Ele retornará seu Chat ID (um número como `123456789`)
5. **Copie esse número**

**Opção B: Enviar mensagem para seu bot**
1. Procure pelo seu bot no Telegram (o que você criou com @BotFather)
2. Envie qualquer mensagem (ex: `/start` ou `Olá`)
3. Execute: `python obter_chat_id_telegram.py`

### 2. Configurar

Execute o script de configuração rápida:

```bash
python configurar_telegram_rapido.py
```

Quando pedir, digite seu Chat ID.

### 3. Testar

```bash
python testar_notificacoes.py
```

Você deve receber uma mensagem no Telegram! ✅

## 📱 Configuração Manual (Alternativa)

Se preferir configurar manualmente, edite `config.json`:

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

Com o Telegram configurado, você receberá notificações instantâneas no celular quando os agentes encontrarem oportunidades ou ocorrerem eventos importantes!

