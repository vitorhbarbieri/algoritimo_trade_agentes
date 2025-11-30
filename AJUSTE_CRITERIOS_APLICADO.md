# ✅ Ajuste de Critérios Aplicado

## 📊 Análise dos Dados Reais

Baseado na análise de **500 capturas** das últimas 48 horas:

### Retorno Intraday:
- **Mediana**: 0.98%
- **Percentil 25**: 0.57%
- **Percentil 50**: 0.98%
- **Percentil 75**: 1.27%

### Volume Ratio (estimado):
- **Mediana**: 1.00
- **Percentil 25**: 0.51
- **Percentil 20**: 0.39

## 🔧 Critérios Ajustados

### ✅ ANTES → DEPOIS:

| Critério | Antes | Depois | Mudança |
|----------|-------|--------|---------|
| `min_intraday_return` | 0.50% | **0.30%** | ⬇️ -0.20% |
| `min_volume_ratio` | 0.25 | **0.10** | ⬇️ -0.15 |
| `delta_min` | 0.20 | **0.15** | ⬇️ -0.05 |
| `delta_max` | 0.60 | **0.70** | ⬆️ +0.10 |
| `max_dte` | 7 dias | **14 dias** | ⬆️ +7 dias |
| `max_spread_pct` | 5% | **10%** | ⬆️ +5% |
| `min_option_volume` | 200 | **100** | ⬇️ -100 |
| `take_profit_pct` | 10% | **0.50%** | ⬇️ Mantido conforme solicitado |

## 📈 Impacto Esperado

### Mais Oportunidades:
- **Retorno intraday**: Agora captura movimentos de 0.30%+ (antes 0.50%+)
  - Isso deve capturar aproximadamente **80%** dos movimentos reais
  
- **Volume ratio**: Reduzido de 0.25 para 0.10
  - Captura mais oportunidades mesmo em dias de volume moderado
  
- **Delta range**: Ampliado de 0.20-0.60 para 0.15-0.70
  - Mais flexibilidade na escolha de opções
  
- **DTE**: Aumentado de 7 para 14 dias
  - Mais opções disponíveis no mercado
  
- **Spread**: Aumentado de 5% para 10%
  - Aceita opções com maior spread (mais comum no mercado brasileiro)
  
- **Volume de opções**: Reduzido de 200 para 100
  - Aceita opções com menor liquidez

## 🎯 Take Profit Mantido

Conforme solicitado, o `take_profit_pct` foi mantido em **0.50%** (ganho esperado por trade).

## ✅ Próximos Passos

1. **Testar os novos critérios:**
   ```bash
   python iniciar_agentes.py
   ```

2. **Monitorar propostas geradas:**
   - Acesse o dashboard: `streamlit run dashboard_central.py`
   - Vá para a aba "DayTrade Monitor"
   - Verifique a seção "Análise Detalhada de Propostas"

3. **Ajustar se necessário:**
   - Se ainda houver poucas propostas, reduzir ainda mais os critérios
   - Se houver muitas propostas de baixa qualidade, aumentar levemente

## 📝 Observações

- Os critérios foram ajustados para serem **mais realistas** baseados nos dados reais capturados
- O foco foi em **reduzir restrições** de volume e volatilidade conforme solicitado
- O ganho esperado de **0.50%** foi mantido conforme sua preferência

---

**Data**: 29/11/2025
**Status**: ✅ Aplicado em `config.json`

