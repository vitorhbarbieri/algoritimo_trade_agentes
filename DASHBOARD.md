# 📊 Dashboard do Agente de Trading

Dashboard interativo para acompanhar e visualizar o desempenho do agente de trading em tempo real.

## 🚀 Como Iniciar

### Windows
```bash
start_dashboard.bat
```

### Linux/Mac
```bash
chmod +x start_dashboard.sh
./start_dashboard.sh
```

### Manualmente
```bash
pip install streamlit plotly
streamlit run dashboard.py
```

## 🌐 Acesso

Após iniciar, o dashboard estará disponível em:

```
http://localhost:8501
```

O Streamlit abrirá automaticamente no seu navegador padrão.

## 📊 Funcionalidades

### 1. Métricas de Performance
- **Retorno Total**: Retorno percentual do período
- **Sharpe Ratio**: Ratio de Sharpe anualizado
- **Max Drawdown**: Maior queda do patrimônio
- **Volatilidade**: Volatilidade anualizada dos retornos
- **Win Rate**: Taxa de acerto das operações
- **Total Trades**: Número total de trades executados

### 2. Gráficos Interativos

#### Evolução do NAV
- Gráfico de linha mostrando a evolução do patrimônio líquido ao longo do tempo
- Linha de referência do NAV inicial
- Zoom e hover para detalhes

#### Número de Posições
- Acompanhamento do número de posições abertas ao longo do tempo
- Identifica períodos de maior/menor exposição

### 3. Análise por Estratégia

#### Distribuição de Ordens
- Gráfico de pizza mostrando a proporção de ordens por estratégia
- Identifica qual estratégia está mais ativa

#### P&L por Estratégia
- Gráfico de barras com P&L estimado por estratégia
- Cores indicam lucro (verde) ou prejuízo (vermelho)

### 4. Tabelas Detalhadas

#### Ordens
- Histórico completo de todas as ordens geradas
- Filtros por data, estratégia, instrumento
- Estatísticas agregadas

#### Fills (Execuções)
- Todas as execuções com preços de fill
- Slippage e comissões por operação
- Estatísticas de custos de execução

#### Portfólio
- Snapshots do portfólio ao longo do tempo
- Estado atual: NAV, cash, número de posições
- Histórico completo

#### Logs
- Logs estruturados de todas as decisões
- Filtros por tipo de evento:
  - `trader_proposal`: Propostas do TraderAgent
  - `risk_evaluation`: Decisões do RiskAgent
  - `execution`: Execuções de ordens
  - `kill_switch`: Ativações de kill switch
- Distribuição de eventos por tipo

## ⚙️ Configurações

### Sidebar
- **Versão do Projeto**: Informações de versão e data
- **Atualização Automática**: Habilita refresh automático
- **Intervalo de Atualização**: Configura intervalo (5-60 segundos)
- **Parâmetros**: Visualiza configuração do `config.json`

## 📝 Requisitos

- Python 3.10+
- Dependências instaladas (`pip install -r requirements.txt`)
- Dados gerados pelo backtest (`run_backtest.py` ou `mvp_agents.ipynb`)

## 🔄 Atualização de Dados

O dashboard lê os arquivos CSV gerados pelo backtest:

- `output/metrics.csv`
- `output/portfolio_snapshots.csv`
- `output/orders.csv`
- `output/fills.csv`
- `logs/decisions-*.jsonl`

Para atualizar os dados:
1. Execute o backtest novamente: `python run_backtest.py`
2. Recarregue a página do dashboard (F5)
3. Ou habilite a atualização automática na sidebar

## 💡 Dicas

- Use o zoom nos gráficos para analisar períodos específicos
- Filtre os logs por tipo de evento para focar em decisões específicas
- Compare métricas entre diferentes execuções do backtest
- Monitore o número de posições para identificar sobre-exposição

## 🐛 Troubleshooting

### Dashboard não carrega dados
- Verifique se executou o backtest primeiro: `python run_backtest.py`
- Confirme que os arquivos existem em `output/`

### Erro ao iniciar
- Instale as dependências: `pip install streamlit plotly`
- Verifique se está no diretório correto do projeto

### Gráficos não aparecem
- Verifique se há dados suficientes (pelo menos algumas ordens/fills)
- Confira se os CSVs estão no formato correto

## 📸 Screenshots

O dashboard inclui:
- Visualizações interativas com Plotly
- Tabelas responsivas e filtros
- Métricas em tempo real
- Análise detalhada por estratégia

