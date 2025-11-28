# 📱 Como Obter seu Chat ID do Telegram

## ⚡ Método Mais Rápido (Recomendado)

### Passo a Passo:

1. **Abra o Telegram** no seu celular ou computador

2. **Procure pelo seu bot** (o bot que você criou com @BotFather)

3. **Envie uma mensagem** para o bot:
   - Digite `/start` ou qualquer mensagem
   - Exemplo: "Olá" ou "/start"

4. **Execute este comando:**
   ```bash
   python obter_chat_id_simples.py
   ```

5. **Pronto!** O script vai:
   - Buscar sua mensagem automaticamente
   - Extrair o chat_id
   - Salvar no config.json
   - Enviar uma mensagem de teste

---

## 🌐 Método 2: Via Navegador (Mais Visual)

1. **Envie uma mensagem para o bot** no Telegram

2. **Abra este link no navegador:**
   ```
   https://api.telegram.org/bot7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM/getUpdates
   ```

3. **Procure na resposta JSON** por algo assim:
   ```json
   "chat": {
     "id": 123456789,
     "first_name": "Seu Nome",
     ...
   }
   ```

4. **Copie o número** do campo `"id"` (ex: `123456789`)

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

---

## 🤖 Método 3: Usando Bot @userinfobot

1. **Abra o Telegram**

2. **Procure por `@userinfobot`**

3. **Envie `/start` para o bot**

4. **O bot vai responder com seu chat_id**

5. **Copie o número e adicione no config.json**

---

## ✅ Testar Após Configurar

Depois de configurar o chat_id, execute:

```bash
python testar_telegram.py
```

Este script vai enviar uma mensagem de teste para você verificar se está funcionando!

---

## 📝 Resumo Rápido

**O que você precisa fazer:**
1. Enviar uma mensagem para o bot no Telegram
2. Executar: `python obter_chat_id_simples.py`
3. Pronto! ✅

**Seu token já está configurado:**
- Token: `7976826583:AAHt69p3mn90_5vMHgkJEUhC_0MTPvVXhZM`

**Falta apenas:**
- Chat ID (que você vai obter com um dos métodos acima)

