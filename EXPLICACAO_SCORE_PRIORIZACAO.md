# 📊 EXPLICAÇÃO DO SISTEMA DE SCORE DE PRIORIZAÇÃO

**Data**: 07/12/2025

---

## 🎯 VISÃO GERAL

O sistema de score de priorização compara matematicamente **opções vs ações** para escolher a melhor oportunidade de daytrade. Ele calcula um score numérico que considera múltiplos fatores e depois ordena as propostas por esse score.

---

## 🔢 COMO O SCORE É CALCULADO

### 1. **Comparação Opção vs Ação**

Para cada ativo, o sistema:

1. **Calcula oportunidade em AÇÃO (spot)**:
   - Retorno esperado baseado no movimento intraday
   - Risk-adjusted return (tipo Sharpe ratio)
   - Capital necessário
   - Risco máximo (stop loss)

2. **Calcula oportunidade em OPÇÃO**:
   - Retorno esperado baseado no movimento do ativo subjacente
   - Leverage effect (alavancagem da opção)
   - Capital necessário (prêmio pago)
   - Risco máximo (perda total do prêmio)

3. **Compara e escolhe a melhor**:
   - Compara os scores de ambas as oportunidades
   - Escolhe a que tem maior score
   - Gera proposta apenas para a melhor

### 2. **Fórmula do Score**

O score é calculado usando a seguinte fórmula:

```python
score = (
    return_normalized * 0.3 +        # Retorno esperado (30%)
    risk_adj_normalized * 0.3 +      # Risk-adjusted return (30%)
    leverage_normalized * 0.2 +      # Leverage effect (20%)
    capital_efficiency * 0.1 +       # Eficiência de capital (10%)
    risk_reward_ratio * 0.1          # Risk/reward ratio (10%)
)
```

**Componentes:**

- **Retorno Esperado (30%)**: Valor esperado do ganho em R$
- **Risk-Adjusted Return (30%)**: Retorno ajustado pelo risco (tipo Sharpe)
- **Leverage Effect (20%)**: Efeito de alavancagem (opções têm mais leverage)
- **Capital Efficiency (10%)**: Quanto retorno por real investido
- **Risk/Reward Ratio (10%)**: Razão entre ganho máximo e perda máxima

---

## ⏰ AJUSTE POR HORÁRIO

O sistema também ajusta o score baseado no horário do dia:

### Multiplicadores por Horário:

- **12:00 - 15:00** (horário ideal): **1.2x** ⬆️
  - Baseado em análise: 53.4% dos sucessos ocorrem neste horário
  - Prioriza propostas neste período

- **10:00 - 12:00** ou **15:00 - 16:00** (horário bom): **1.0x** ➡️
  - Score normal, sem ajuste

- **Outros horários** (não ideal): **0.7x** ⬇️
  - Reduz prioridade de propostas fora do horário ideal

### Cálculo do Score Ajustado:

```python
score_ajustado = comparison_score * multiplicador_horario
```

**Exemplo:**
- Score original: 0.85
- Horário: 14:30 (dentro de 12:00-15:00)
- Score ajustado: 0.85 * 1.2 = **1.02**

---

## 📋 FILTROS E PRIORIZAÇÃO

### 1. **Filtro por Score Mínimo**

O sistema filtra propostas com score abaixo do mínimo:

```python
min_comparison_score = config.get('min_comparison_score', 0)
```

**Configuração atual**: `min_comparison_score = 0.7` (em `config.json` → `daytrade_options`)

- Propostas com `comparison_score < 0.7` são **rejeitadas**
- Apenas propostas acima do mínimo passam para avaliação do RiskAgent

### 2. **Ordenação por Score**

Após aplicar o filtro, as propostas são ordenadas:

```python
# Ordenar por score ajustado (maior primeiro)
proposals_with_scores.sort(key=lambda x: x[0], reverse=True)
```

- **Maior score primeiro** = maior prioridade
- As melhores oportunidades aparecem primeiro

### 3. **Limite de Propostas**

O sistema retorna apenas as **top 10** melhores oportunidades:

```python
return filtered_proposals[:10]
```

---

## 🔍 EXEMPLO PRÁTICO

### Cenário: PETR4 às 14:30

1. **Dados de Entrada:**
   - Preço atual: R$ 32,50
   - Movimento intraday: +1.5%
   - Opção disponível: Call R$ 33,00 com delta 0.50

2. **Cálculo Opção:**
   - Retorno esperado: R$ 150,00
   - Leverage: 5x
   - Score: **0.85**

3. **Cálculo Ação:**
   - Retorno esperado: R$ 15,00
   - Leverage: 1x
   - Score: **0.45**

4. **Comparação:**
   - Opção melhor (0.85 > 0.45)
   - Escolhida: **Opção**

5. **Ajuste por Horário:**
   - Horário: 14:30 (dentro de 12:00-15:00)
   - Score ajustado: 0.85 * 1.2 = **1.02**

6. **Filtro:**
   - Se `min_comparison_score = 0.7`:
   - Score original (0.85) >= 0.7 ✅ **APROVADO**
   - Score ajustado usado para ordenação: **1.02**

7. **Resultado:**
   - Proposta gerada com `comparison_score = 0.85` (score original)
   - Priorizada com score ajustado **1.02**
   - Aparece nas mensagens Telegram com score **0.85**

---

## ⚙️ CONFIGURAÇÕES

### Parâmetros no `config.json`:

```json
{
  "daytrade_options_strategy": {
    "min_comparison_score": 0.7,  // Score mínimo para aprovar
    "risk_per_trade": 0.002,      // Risco por trade (0.2% do NAV)
    ...
  }
}
```

### Parâmetros do ComparisonEngine:

- **risk_free_rate**: 0.05 (5% ao ano)
- **Pesos do Score**:
  - Retorno esperado: 30%
  - Risk-adjusted return: 30%
  - Leverage effect: 20%
  - Capital efficiency: 10%
  - Risk/reward ratio: 10%

---

## ✅ STATUS ATUAL

### O que está funcionando:

1. ✅ **Cálculo de score** para opções e ações
2. ✅ **Comparação** entre opções e ações
3. ✅ **Escolha automática** da melhor oportunidade
4. ✅ **Ajuste por horário** (multiplicador 1.2x para 12:00-15:00)
5. ✅ **Ordenação** por score ajustado
6. ✅ **Filtro** por score mínimo
7. ✅ **Limite** de top 10 propostas
8. ✅ **Exibição** do score nas mensagens Telegram

### Fluxo Completo:

```
1. Coleta dados de mercado
   ↓
2. Para cada ativo:
   - Calcula oportunidade em ação
   - Calcula oportunidade em opção
   - Compara e escolhe a melhor
   ↓
3. Ajusta score por horário
   ↓
4. Ordena por score ajustado
   ↓
5. Filtra por score mínimo
   ↓
6. Retorna top 10
   ↓
7. Envia para RiskAgent
   ↓
8. Exibe score nas mensagens Telegram
```

---

## 🎯 COMO VERIFICAR SE ESTÁ FUNCIONANDO

### 1. **Verificar Logs**

Procurar por mensagens como:
```
PETR4: Opcao melhor: Score 0.85 vs 0.45. Leverage: 5.2x, Retorno esperado: R$ 150.00 vs R$ 15.00
```

### 2. **Verificar Mensagens Telegram**

O score aparece na mensagem:
```
⭐ SCORE: 0.85
```

### 3. **Verificar Banco de Dados**

Query para ver scores:
```sql
SELECT proposal_id, symbol, metadata->>'comparison_score' as score
FROM proposals
ORDER BY CAST(metadata->>'comparison_score' AS REAL) DESC
LIMIT 10;
```

### 4. **Verificar Propostas Geradas**

- Se houver opções disponíveis: deve comparar e escolher a melhor
- Se não houver opções: deve gerar proposta de ação
- Score deve estar entre 0 e 2 (geralmente 0.3 a 1.5)

---

## 🔧 AJUSTES POSSÍVEIS

### Para aumentar seletividade:

```json
"min_comparison_score": 0.8  // Aumentar de 0.7 para 0.8
```

### Para priorizar mais o horário ideal:

Ajustar multiplicador em `src/agents.py`:
```python
if 12 <= current_hour <= 15:
    horario_multiplier = 1.3  # Aumentar de 1.2 para 1.3
```

### Para ajustar pesos do score:

Modificar em `src/comparison_engine.py`:
```python
score = (
    return_normalized * 0.4 +        # Aumentar retorno esperado
    risk_adj_normalized * 0.3 +
    leverage_normalized * 0.15 +    # Reduzir leverage
    capital_efficiency * 0.1 +
    risk_reward_ratio * 0.05        # Reduzir risk/reward
)
```

---

## 📊 RESUMO

**O sistema de score de priorização está funcionando** e realiza:

1. ✅ Comparação matemática entre opções e ações
2. ✅ Cálculo de score considerando múltiplos fatores
3. ✅ Ajuste por horário (prioriza 12:00-15:00)
4. ✅ Ordenação e filtragem por score
5. ✅ Escolha automática da melhor oportunidade
6. ✅ Exibição do score nas mensagens Telegram

**O score é usado para:**
- Escolher entre opção e ação
- Priorizar propostas (maior score = maior prioridade)
- Filtrar propostas ruins (score mínimo)
- Ordenar propostas para envio ao RiskAgent

---

**Status**: ✅ **FUNCIONANDO CORRETAMENTE**

