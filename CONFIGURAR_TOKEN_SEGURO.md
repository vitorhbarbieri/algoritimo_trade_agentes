# 🔒 Configuração Segura do Token do Telegram

## ⚠️ Importante

O token do Telegram **NÃO deve** estar no código! Use uma das opções abaixo:

## 🔐 Opção 1: Variável de Ambiente (RECOMENDADO)

### Windows PowerShell:
```powershell
$env:TELEGRAM_BOT_TOKEN="seu_token_aqui"
```

### Windows CMD:
```cmd
set TELEGRAM_BOT_TOKEN=seu_token_aqui
```

### Linux/Mac:
```bash
export TELEGRAM_BOT_TOKEN="seu_token_aqui"
```

### Para tornar permanente (Linux/Mac):
Adicione ao `~/.bashrc` ou `~/.zshrc`:
```bash
export TELEGRAM_BOT_TOKEN="seu_token_aqui"
```

## 📝 Opção 2: Arquivo config.json (Local)

1. Copie o arquivo de exemplo:
   ```bash
   cp config.json.example config.json
   ```

2. Edite `config.json` e adicione seu token:
   ```json
   {
     "notifications": {
       "telegram": {
         "enabled": true,
         "bot_token": "seu_token_aqui",
         "chat_id": "seu_chat_id"
       }
     }
   }
   ```

⚠️ **IMPORTANTE:** O arquivo `config.json` está no `.gitignore` e **NÃO será commitado**.

## ✅ Verificar Configuração

Execute:
```bash
python testar_notificacoes.py
```

Se o token estiver configurado corretamente, você receberá uma mensagem de teste no Telegram.

## 🔄 Ordem de Prioridade

O sistema busca o token nesta ordem:
1. Variável de ambiente `TELEGRAM_BOT_TOKEN`
2. Arquivo `config.json` (seção `notifications.telegram.bot_token`)
3. Se não encontrar, mostra erro e instruções

## 🛡️ Segurança

- ✅ **NUNCA** commite o token no Git
- ✅ Use variáveis de ambiente em produção
- ✅ O `config.json` está no `.gitignore`
- ✅ Use `config.json.example` como template (sem tokens reais)

## 📚 Mais Informações

Veja também:
- `CONFIGURAR_TELEGRAM.md` - Guia completo de configuração
- `GUIA_NOTIFICACOES.md` - Guia de notificações

