# 📧 Configuração do Sistema de Notificações por Email

## 🎯 Objetivo

Configurar o sistema para enviar emails automaticamente quando:
- ✅ Encontrar oportunidades de trading
- ✅ Gerar propostas importantes (especialmente daytrade)
- ✅ Aprovar/rejeitar propostas importantes
- ✅ Ocorrer erros no sistema
- ✅ Kill switch for ativado

## ⚙️ Configuração

### 1. Editar config.json

Abra o arquivo `config.json` e configure:

```json
{
  "email_notifications_enabled": true,
  "email_destinatario": "vitorh.barbieri@gmail.com",
  "email_remetente": "seu_email@gmail.com",
  "email_senha": "sua_senha_de_app",
  "email_smtp_server": "smtp.gmail.com",
  "email_smtp_port": 587,
  "email_cooldown_seconds": 300
}
```

### 2. Configurar Gmail (Recomendado)

#### Passo 1: Ativar Autenticação de 2 Fatores
1. Acesse: https://myaccount.google.com/security
2. Ative a verificação em duas etapas

#### Passo 2: Gerar Senha de App
1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "App" → "Email"
3. Selecione "Dispositivo" → "Outro (nome personalizado)"
4. Digite: "Trading Bot"
5. Clique em "Gerar"
6. **Copie a senha gerada** (16 caracteres)

#### Passo 3: Configurar no config.json
```json
{
  "email_remetente": "seu_email@gmail.com",
  "email_senha": "abcd efgh ijkl mnop"  // Use a senha de app gerada (sem espaços)
}
```

⚠️ **IMPORTANTE**: Use a **senha de app**, não a senha normal do Gmail!

### 3. Testar Configuração

Execute o script de teste:

```bash
python testar_email.py
```

Este script irá:
- ✅ Verificar se as configurações estão corretas
- ✅ Enviar um email de teste de oportunidade
- ✅ Enviar um email de teste de múltiplas oportunidades
- ✅ Mostrar instruções se houver problemas

## 📬 Quando Emails São Enviados

### Oportunidades Encontradas
- **Quando**: Sistema encontra oportunidades de trading
- **Frequência**: Máximo 1 email a cada 5 minutos (cooldown)
- **Conteúdo**: Tipo de oportunidade, ativo, score, detalhes

### Propostas de Daytrade
- **Quando**: TraderAgent gera proposta de daytrade options
- **Prioridade**: Alta (sempre envia)
- **Conteúdo**: Ativo, strike, delta, momentum, volume ratio

### Erros do Sistema
- **Quando**: Erro crítico durante escaneamento
- **Prioridade**: Alta
- **Conteúdo**: Tipo de erro, mensagem, detalhes

### Kill Switch
- **Quando**: RiskAgent ativa kill switch
- **Prioridade**: Crítica (sempre envia, sem cooldown)
- **Conteúdo**: Motivo, perda de NAV, ações recomendadas

## 🔧 Integração com Agentes

O sistema está integrado com:

1. **MonitoringService**: Envia emails quando encontra oportunidades
2. **TraderAgent**: Notifica sobre propostas importantes
3. **RiskAgent**: Notifica sobre kill switch
4. **DayTradeOptionsStrategy**: Notifica sobre propostas de daytrade

## 📊 Cooldown (Limite de Frequência)

Para evitar spam, há um cooldown de **5 minutos** (300 segundos) entre emails do mesmo tipo.

**Exceções** (sem cooldown):
- Kill switch ativado
- Erros críticos

## 🧪 Testar Agora

Execute o teste:

```bash
python testar_email.py
```

Se receber os emails de teste, está tudo configurado! ✅

## ⚠️ Troubleshooting

### Erro: "Email não configurado"
- Verifique se `email_remetente` e `email_senha` estão preenchidos no config.json
- Use **senha de app**, não a senha normal do Gmail

### Erro: "Authentication failed"
- Verifique se a senha de app está correta
- Certifique-se de que não há espaços na senha
- Gere uma nova senha de app se necessário

### Erro: "Connection refused"
- Verifique se `email_smtp_server` está correto (smtp.gmail.com)
- Verifique se `email_smtp_port` está correto (587)
- Verifique firewall/antivírus

### Não recebe emails
- Verifique a pasta de SPAM
- Verifique se `email_destinatario` está correto
- Execute o teste: `python testar_email.py`

## ✅ Checklist

Antes de deixar rodando durante o dia:

- [ ] Email configurado no config.json
- [ ] Senha de app do Gmail gerada e configurada
- [ ] Teste executado com sucesso (`python testar_email.py`)
- [ ] Email de teste recebido na caixa de entrada
- [ ] `email_notifications_enabled` está `true`
- [ ] `email_cooldown_seconds` configurado (recomendado: 300)

## 🚀 Pronto!

Com tudo configurado, o sistema enviará emails automaticamente quando:
- Encontrar oportunidades durante o pregão
- Gerar propostas importantes
- Ocorrer problemas

Você será notificado em tempo real! 📧✨

