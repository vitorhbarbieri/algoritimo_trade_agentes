# 📊 RESUMO: DADOS REAIS BRASILEIROS DISPONÍVEIS

**Data**: 04/12/2025

---

## ✅ DADOS DISPONÍVEIS

### Quantidade:
- **7.317 capturas brasileiras REAIS** (100% reais, 0% simuladas)
- **15 ativos brasileiros** com dados
- **7 dias** de cobertura (30/11 a 06/12)

### Ativos com Dados:
1. ABEV3.SA - 481 capturas
2. B3SA3.SA - 483 capturas
3. BBAS3.SA - 482 capturas
4. BBDC4.SA - 480 capturas
5. ELET3.SA - 482 capturas
6. HAPV3.SA - 483 capturas
7. ITUB4.SA - 480 capturas
8. MGLU3.SA - 483 capturas
9. PETR4.SA - 479 capturas
10. RADL3.SA - 483 capturas
11. RENT3.SA - 483 capturas
12. SANB11.SA - 482 capturas
13. SUZB3.SA - 483 capturas
14. VALE3.SA - 479 capturas
15. WEGE3.SA - 481 capturas

---

## ⚠️ PROBLEMA IDENTIFICADO

### Por que não está gerando propostas?

**Análise dos dados reais**:
- **Intraday Return muito baixo**: 0.00% - 0.14% (threshold necessário: 0.6%)
- **Volume Ratio sempre 1.00x**: ADV = Volume do dia (não há histórico)

### Exemplos encontrados:
- 2025-11-30: Todos os ativos com 0.00% de intraday return
- 2025-12-01: ABEV3.SA com 0.14%, B3SA3.SA com 0.13% (abaixo de 0.6%)
- Volume ratio sempre 1.00x (ADV = volume do dia atual)

---

## 🔍 POSSÍVEIS CAUSAS

1. **Captura de dados**: Pode estar capturando apenas um momento do dia, não abertura/fechamento real
2. **Cálculo de intraday_return**: Pode estar usando preços incorretos (mesmo preço para abertura e fechamento)
3. **ADV**: Não há histórico para calcular ADV real, então usa volume do dia atual

---

## 💡 PRÓXIMOS PASSOS

### 1. Verificar Captura de Dados
- Verificar se está capturando preço de abertura real (primeira captura do dia)
- Verificar se está capturando preço de fechamento real (última captura do dia)
- Verificar timestamps das capturas

### 2. Ajustar Cálculo de Intraday Return
- Usar primeira captura do dia como abertura
- Usar última captura do dia como fechamento
- Verificar se há variação de preço durante o dia

### 3. Melhorar Cálculo de ADV
- Coletar histórico de volumes para calcular ADV real
- Usar média móvel de volumes dos últimos dias

### 4. Ajustar Thresholds Temporariamente
- Reduzir `min_intraday_return` temporariamente para testar (ex: 0.1%)
- Verificar se propostas são geradas com dados reais

---

## 📋 AÇÕES IMEDIATAS

1. ✅ **Dados reais confirmados** - Temos 7.317 capturas brasileiras reais
2. ⏳ **Ajustar cálculo de intraday_return** - Usar primeira/última captura corretamente
3. ⏳ **Verificar timestamps** - Confirmar que capturas estão no horário correto
4. ⏳ **Testar com threshold reduzido** - Verificar se gera propostas
5. ⏳ **Coletar mais dados** - Continuar capturando para ter histórico

---

## 🎯 CONCLUSÃO

**Temos dados reais brasileiros suficientes**, mas precisamos:
1. Ajustar o cálculo de intraday_return para usar dados corretos
2. Verificar se as capturas estão representando abertura/fechamento real
3. Possivelmente ajustar thresholds temporariamente para testar

**Status**: ✅ Dados disponíveis | ⚠️ Ajustes necessários no processamento

