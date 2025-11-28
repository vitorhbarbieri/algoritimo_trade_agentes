# Guia de Aprovação de Ordens via Telegram

## 📱 Como Funciona

O sistema agora permite aprovar ou cancelar ordens diretamente pelo chat do Telegram, de forma simples e sem necessidade de configurar webhooks!

## 🚀 Iniciar o Sistema

Execute o script de polling em um terminal separado:

```bash
python rodar_telegram_polling.py
```

Este script ficará rodando em background, verificando mensagens a cada 5 segundos.

## ✅ Formas de Aprovar uma Ordem

Quando você receber uma proposta de ordem no Telegram, você pode aprovar de **3 formas diferentes**:

### 1. **Usando Botões (Mais Fácil)**
- A mensagem virá com dois botões: ✅ APROVAR e ❌ CANCELAR
- Basta clicar no botão desejado!

### 2. **Respondendo com SIM/NAO**
- Responda diretamente à mensagem da proposta com:
  - `SIM` ou `APROVAR` → Aprova a ordem
  - `NAO` ou `CANCELAR` → Cancela a ordem

### 3. **Usando Comandos**
- Digite no chat:
  - `/aprovar PROPOSAL_ID` → Aprova a proposta específica
  - `/cancelar PROPOSAL_ID` → Cancela a proposta específica
- O `PROPOSAL_ID` está na mensagem da proposta (ex: `DAYOPT-B3SA3.SA-14.86-20251202-1764281503`)

## 📋 Exemplo de Mensagem Recebida

```
📊 NOVA PROPOSTA DE ORDEM

Proposta ID: `DAYOPT-B3SA3.SA-14.86-20251202-1764281503`
Ativo: `B3SA3.SA_14.86_C_20251202`
Operação: BUY
Quantidade: 200
Preço: R$ 14.87
Valor Total: R$ 2,973.49

💰 OPORTUNIDADE DE GANHO:
• Ganho Esperado: R$ 297.35 (10.00%)
• Take Profit: 10.0%
• Stop Loss: 40.0%
• Perda Máxima: R$ 1,189.39

Para aprovar: Responda com SIM ou digite /aprovar DAYOPT-B3SA3.SA-14.86-20251202-1764281503
Para cancelar: Responda com NAO ou digite /cancelar DAYOPT-B3SA3.SA-14.86-20251202-1764281503

[Botões: ✅ APROVAR | ❌ CANCELAR]
```

## 🔧 Configuração

Certifique-se de que o `config.json` tem:

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

## ⚙️ Executar em Background (Windows)

Para rodar o polling em background no Windows:

```powershell
Start-Process python -ArgumentList "rodar_telegram_polling.py" -WindowStyle Hidden
```

Ou use o Task Scheduler para iniciar automaticamente.

## 📝 Notas

- O polling verifica mensagens a cada 5 segundos
- Todas as aprovações são salvas no banco de dados (`proposal_approvals`)
- Você receberá confirmação quando aprovar ou cancelar uma ordem
- O sistema funciona mesmo sem webhook configurado!

