# Como Obter o Chat ID do Telegram

## Método 1: Script Automático (Recomendado)

1. **Abra o Telegram no seu celular ou computador**

2. **Procure pelo seu bot** (o bot que você criou com @BotFather)

3. **Envie qualquer mensagem para o bot** (ex: `/start` ou `Olá`)

4. **Execute o script:**
   ```bash
   python obter_chat_id_telegram.py
   ```

5. **O script vai:**
   - Buscar a mensagem que você enviou
   - Extrair o chat_id automaticamente
   - Salvar no `config.json`
   - Enviar uma mensagem de teste

## Método 2: Via API do Telegram (Manual)

1. **Envie uma mensagem para o bot** no Telegram

2. **Acesse esta URL no navegador** (substitua SEU_TOKEN pelo seu token):
   ```
   https://api.telegram.org/bot7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM/getUpdates
   ```

3. **Procure na resposta JSON** pelo campo `"chat":{"id":123456789}`

4. **Copie o número** (ex: `123456789`)

5. **Adicione no config.json:**
   ```json
   "notifications": {
     "telegram": {
       "enabled": true,
       "bot_token": "7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM",
       "chat_id": "123456789"
     }
   }
   ```

## Método 3: Usando o Bot @userinfobot

1. **Abra o Telegram**

2. **Procure por `@userinfobot`**

3. **Envie `/start` para o bot**

4. **O bot vai responder com seu chat_id**

5. **Copie o número e adicione no config.json**

## Token do Seu Bot

Seu token já está configurado:
- Token: `7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM`

## Testar Após Configurar

Após configurar o chat_id, execute:
```bash
python testar_telegram.py
```

Este script vai enviar uma mensagem de teste para você verificar se está funcionando!

