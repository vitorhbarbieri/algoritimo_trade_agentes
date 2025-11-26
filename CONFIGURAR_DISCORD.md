# 💬 Configurar Notificações via Discord

## 🎯 Por que Discord?

- ✅ **Gratuito** e ilimitado
- ✅ **Fácil de configurar** (3 minutos)
- ✅ **Notificações em servidor/canal**
- ✅ **Mensagens formatadas** (embeds)
- ✅ **Pode compartilhar com equipe**

## 🚀 Passo a Passo

### 1. Criar Webhook no Discord

1. Abra o Discord e vá para o servidor onde quer receber notificações
2. Vá em **Configurações do Servidor** → **Integrações** → **Webhooks**
3. Clique em **Criar Webhook**
4. Configure:
   - **Nome**: Trading Bot (ou qualquer nome)
   - **Canal**: Escolha o canal onde quer receber notificações
5. Clique em **Copiar URL do Webhook**
6. A URL será algo como: `https://discord.com/api/webhooks/123456789/ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. Configurar no Sistema

#### Opção 1: Via Variáveis de Ambiente (RECOMENDADO)

```bash
# Windows PowerShell
$env:DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123456789/ABCdefGHIjklMNOpqrsTUVwxyz"

# Windows CMD
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/ABCdefGHIjklMNOpqrsTUVwxyz

# Linux/Mac
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123456789/ABCdefGHIjklMNOpqrsTUVwxyz"
```

#### Opção 2: Via config.json

Edite `config.json`:

```json
{
  "notifications": {
    "discord": {
      "enabled": true,
      "webhook_url": "https://discord.com/api/webhooks/123456789/ABCdefGHIjklMNOpqrsTUVwxyz"
    }
  }
}
```

⚠️ **ATENÇÃO**: Se usar config.json, adicione-o ao `.gitignore`!

### 3. Testar

Execute o script de teste:

```bash
python testar_notificacoes.py
```

Você deve receber uma mensagem no Discord! ✅

## 💬 O Que Você Receberá

- 🎯 **Oportunidades encontradas** (com embeds formatados)
- ⚡ **Propostas de daytrade** (alta prioridade, cor amarela)
- ⚠️ **Erros do sistema** (crítico, cor vermelha)
- 🛑 **Kill switch ativado** (crítico, cor vermelha)

## 🔒 Segurança

- ✅ Use **variáveis de ambiente** quando possível
- ✅ Se usar config.json, adicione ao `.gitignore`
- ✅ Nunca compartilhe sua webhook URL publicamente
- ✅ Se compartilhar acidentalmente, delete e crie nova webhook

## ✅ Pronto!

Com o Discord configurado, você receberá notificações no canal escolhido quando:
- Sistema encontrar oportunidades
- Gerar propostas importantes
- Ocorrer problemas

**Perfeito para monitorar em equipe!** 💬✨

