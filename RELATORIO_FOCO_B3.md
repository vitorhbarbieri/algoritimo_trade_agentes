# 🇧🇷 RELATÓRIO: FOCO EXCLUSIVO NA B3 E ANÁLISE DE CUSTOS

**Data**: 04/12/2025  
**Objetivo**: Focar exclusivamente na Bolsa Brasileira (B3) e considerar custos reais de operação

---

## ✅ MUDANÇAS IMPLEMENTADAS

### 1. Filtro de Ativos Brasileiros

**Antes**: Sistema operava com ativos internacionais (AAPL, MSFT, TSLA, etc.)  
**Depois**: Sistema focado exclusivamente em ativos brasileiros (.SA)

**Mudanças no `config.json`**:
- ✅ Removidos todos os ativos internacionais
- ✅ Mantidos apenas ativos brasileiros (.SA)
- ✅ Adicionada lista de contratos futuros B3 (WIN, WDO, IND, DOL)
- ✅ Desabilitado crypto trading
- ✅ Ajustados pares de arbitragem para ativos brasileiros

**Tickers Brasileiros Configurados** (30 ativos):
- PETR4.SA, VALE3.SA, ITUB4.SA, BBDC4.SA
- ABEV3.SA, WEGE3.SA, MGLU3.SA, SUZB3.SA
- RENT3.SA, ELET3.SA, BBAS3.SA, SANB11.SA
- B3SA3.SA, RADL3.SA, HAPV3.SA, BBSE3.SA
- CMIG4.SA, CSMG3.SA, SYN3.SA, VIVT3.SA
- TAEE11.SA, ELET6.SA, CPLE6.SA, EQTL3.SA
- KLBN11.SA, UGPA3.SA, RAIL3.SA, CCRO3.SA
- CYRE3.SA, MRVE3.SA

**Contratos Futuros Configurados**:
- WIN (Mini Índice)
- WDO (Mini Dólar)
- IND (Índice Futuro)
- DOL (Dólar Futuro)

---

### 2. Módulo de Cálculo de Custos B3

**Novo arquivo**: `src/b3_costs.py`

**Custos Implementados**:

#### Custos B3:
- **Emolumentos**: 0.0025% sobre valor financeiro
- **Taxa de Registro**: 0.0095% sobre valor financeiro
- **Taxa de Liquidação**: 0.012% (se levar até vencimento)
- **Total B3**: 0.012% por operação (entrada + saída = 0.024%)

#### Custos Corretora:
- **Corretagem**: Configurável (padrão: 0% com RLP ativo)
- Suporte para corretagem percentual ou fixa

#### Impostos:
- **IR Retido**: 1% sobre lucro (retido na fonte)
- **IR a Pagar**: 19% sobre lucro (a pagar)
- **Total IR**: 20% sobre lucro

**Funcionalidades**:
- ✅ `calculate_entry_costs()` - Calcula custos de entrada
- ✅ `calculate_exit_costs()` - Calcula custos de saída
- ✅ `calculate_tax_costs()` - Calcula impostos sobre lucro
- ✅ `calculate_total_costs()` - Calcula custos totais da operação
- ✅ `calculate_minimum_profit()` - Calcula lucro mínimo necessário
- ✅ `calculate_minimum_profit_pct()` - Calcula % mínimo necessário

---

### 3. Análise de Custos e Rentabilidade Mínima

**Novo arquivo**: `analise_custos_b3.py`

**Análises Implementadas**:
1. **Análise de Custos por Operação**
   - Custo médio operacional
   - Impostos médios
   - Custo total médio
   - Impacto dos custos na rentabilidade

2. **Recálculo com Custos Descontados**
   - Rentabilidade bruta vs líquida
   - Operações que não cobrem custos
   - Taxa de sucesso líquida

3. **Cálculo de Threshold Mínimo**
   - Rentabilidade mínima necessária por valor de operação
   - Threshold recomendado com margem de segurança

**Resultados da Análise**:

```
💰 RENTABILIDADE MÍNIMA NECESSÁRIA:
  R$    1,000:  0.030% mínimo
  R$    5,000:  0.030% mínimo
  R$   10,000:  0.030% mínimo
  R$   50,000:  0.030% mínimo

💡 THRESHOLD RECOMENDADO:
  Threshold mínimo médio: 0.030%
  Threshold recomendado (com margem 50%): 0.045%
  Threshold atual configurado: 0.6%
  
  ✅ Threshold atual adequado (0.6% >> 0.045%)
```

---

### 4. Ajustes no Código

**Mudanças em `src/monitoring_service.py`**:
- ✅ Filtro automático para apenas tickers brasileiros (.SA)
- ✅ Suporte para contratos futuros (preparado para implementação)

**Mudanças em `src/agents.py`**:
- ✅ Filtro para processar apenas ativos brasileiros
- ✅ Validação de ticker brasileiro antes de processar

---

## 📊 IMPACTO DOS CUSTOS

### Custo Total por Operação (Day Trade):

**Exemplo: Operação de R$ 10.000**

| Item | Valor |
|------|-------|
| Emolumentos (entrada) | R$ 0.25 |
| Taxa Registro (entrada) | R$ 0.95 |
| Emolumentos (saída) | R$ 0.25 |
| Taxa Registro (saída) | R$ 0.95 |
| **Total Custos B3** | **R$ 2.40** |
| Corretagem (RLP ativo) | R$ 0.00 |
| **Total Custos Operacionais** | **R$ 2.40** |
| IR sobre lucro (20%) | Variável |

**Custo como % do valor**: 0.024% (entrada + saída)

### Rentabilidade Mínima Necessária:

Para uma operação de **R$ 10.000**:
- Custo operacional: R$ 2.40
- Lucro mínimo necessário: R$ 3.00 (considerando IR de 20%)
- **Rentabilidade mínima**: **0.030%**

**Conclusão**: 
- Threshold atual de **0.6%** é **20x maior** que o mínimo necessário
- Sistema está bem configurado para cobrir custos
- Margem de segurança adequada

---

## 🎯 PRÓXIMOS PASSOS

### Implementações Pendentes:

1. **Contratos Futuros B3** ⏳
   - Implementar coleta de dados de futuros (WIN, WDO)
   - Adicionar estratégias específicas para futuros
   - Integrar com sistema de propostas

2. **Integração de Custos nas Propostas** ⏳
   - Mostrar custos estimados nas propostas
   - Calcular rentabilidade líquida esperada
   - Ajustar thresholds baseado em custos reais

3. **Análise Contínua de Custos** ⏳
   - Monitorar custos reais por operação
   - Comparar com estimativas
   - Ajustar parâmetros conforme necessário

4. **Otimização de Corretora** ⏳
   - Considerar diferentes estruturas de corretagem
   - Otimizar para menor custo total
   - Implementar cálculo dinâmico de custos

---

## 📋 RESUMO EXECUTIVO

### ✅ Concluído:
- ✅ Filtro de ativos brasileiros implementado
- ✅ Módulo de cálculo de custos B3 criado
- ✅ Análise de custos e rentabilidade mínima implementada
- ✅ Configuração atualizada para focar apenas em B3
- ✅ Suporte para futuros preparado (estrutura criada)

### ⏳ Em Desenvolvimento:
- ⏳ Implementação completa de contratos futuros
- ⏳ Integração de custos nas propostas
- ⏳ Análise contínua de custos

### 💡 Recomendações:
1. **Manter threshold atual** (0.6%) - adequado para cobrir custos
2. **Monitorar custos reais** após algumas operações
3. **Implementar futuros** para diversificar oportunidades
4. **Considerar RLP** para reduzir corretagem a zero

---

## 🔧 CONFIGURAÇÃO ATUAL

**Parâmetros de Day Trade**:
```json
{
  "min_intraday_return": 0.006,      // 0.6% (adequado - 20x acima do mínimo)
  "take_profit_pct": 0.012,          // 1.2%
  "stop_loss_pct": 0.15,             // 15%
  "min_gain_loss_ratio": 0.08        // 1.2% / 15% = 0.08
}
```

**Custos Configurados**:
- Emolumentos B3: 0.0025%
- Taxa Registro B3: 0.0095%
- Corretagem: 0% (RLP ativo)
- IR Day Trade: 20%

---

**Status**: ✅ **SISTEMA CONFIGURADO PARA OPERAR EXCLUSIVAMENTE NA B3**

**Próxima ação**: Implementar contratos futuros e integrar custos nas propostas

