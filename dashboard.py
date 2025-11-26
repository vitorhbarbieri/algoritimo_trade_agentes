"""
Dashboard Streamlit para acompanhamento do agente de trading.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import json
from datetime import datetime
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils import get_version_info

# Configuração da página
st.set_page_config(
    page_title="Agente de Trading - Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .positive {
        color: #28a745;
        font-weight: bold;
    }
    .negative {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    """Carrega dados dos CSVs gerados."""
    output_dir = Path('output')
    
    data = {
        'metrics': None,
        'portfolio_snapshots': None,
        'orders': None,
        'fills': None,
        'logs': None
    }
    
    # Carregar métricas
    metrics_file = output_dir / 'metrics.csv'
    if metrics_file.exists():
        try:
            data['metrics'] = pd.read_csv(metrics_file)
        except:
            pass
    
    # Carregar snapshots do portfólio
    snapshots_file = output_dir / 'portfolio_snapshots.csv'
    if snapshots_file.exists():
        try:
            df = pd.read_csv(snapshots_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            data['portfolio_snapshots'] = df.sort_values('timestamp')
        except:
            pass
    
    # Carregar ordens
    orders_file = output_dir / 'orders.csv'
    if orders_file.exists():
        try:
            df = pd.read_csv(orders_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            data['orders'] = df.sort_values('timestamp')
        except:
            pass
    
    # Carregar fills
    fills_file = output_dir / 'fills.csv'
    if fills_file.exists():
        try:
            df = pd.read_csv(fills_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            data['fills'] = df.sort_values('timestamp')
        except:
            pass
    
    # Carregar logs (último arquivo de log)
    logs_dir = Path('logs')
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob('decisions-*.jsonl'), reverse=True)
        if log_files:
            try:
                logs = []
                with open(log_files[0], 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            logs.append(json.loads(line))
                data['logs'] = pd.DataFrame(logs)
            except:
                pass
    
    return data

def main():
    # Header
    st.markdown('<h1 class="main-header">📈 Dashboard - Agente de Trading</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Versão
        version_info = get_version_info()
        st.caption(f"Versão: {version_info.get('project_version', '1.0.0')}")
        st.caption(f"Data: {version_info.get('date', 'N/A')}")
        
        # Atualização automática
        auto_refresh = st.checkbox("🔄 Atualização Automática", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Intervalo (segundos)", 5, 60, 10)
            st.rerun()
        
        st.divider()
        
        # Carregar configuração
        config_file = Path('config.json')
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            st.subheader("📊 Parâmetros")
            st.json(config)
    
    # Carregar dados
    data = load_data()
    
    # Verificar se há dados
    if data['portfolio_snapshots'] is None or data['portfolio_snapshots'].empty:
        st.warning("⚠️ Nenhum dado encontrado. Execute o backtest primeiro usando `run_backtest.py` ou o notebook `mvp_agents.ipynb`.")
        st.info("💡 Para gerar dados:\n```bash\npython run_backtest.py\n```")
        return
    
    # Métricas principais
    st.header("📊 Métricas de Performance")
    
    if data['metrics'] is not None and not data['metrics'].empty:
        metrics = data['metrics'].iloc[0]
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric(
                "Retorno Total",
                f"{metrics.get('total_return', 0):.2f}%",
                delta=f"{metrics.get('total_return', 0):.2f}%"
            )
        
        with col2:
            st.metric(
                "Sharpe Ratio",
                f"{metrics.get('sharpe_ratio', 0):.4f}"
            )
        
        with col3:
            st.metric(
                "Max Drawdown",
                f"{metrics.get('max_drawdown', 0):.2f}%"
            )
        
        with col4:
            st.metric(
                "Volatilidade",
                f"{metrics.get('volatility', 0):.2f}%"
            )
        
        with col5:
            st.metric(
                "Win Rate",
                f"{metrics.get('win_rate', 0):.2f}%"
            )
        
        with col6:
            st.metric(
                "Total Trades",
                f"{int(metrics.get('total_trades', 0))}"
            )
    
    st.divider()
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Evolução do NAV")
        if data['portfolio_snapshots'] is not None and not data['portfolio_snapshots'].empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data['portfolio_snapshots']['timestamp'],
                y=data['portfolio_snapshots']['nav'],
                mode='lines',
                name='NAV',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # Linha de NAV inicial
            if 'nav' in data['portfolio_snapshots'].columns:
                initial_nav = data['portfolio_snapshots']['nav'].iloc[0]
                fig.add_hline(
                    y=initial_nav,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="NAV Inicial"
                )
            
            fig.update_layout(
                xaxis_title="Data",
                yaxis_title="NAV (R$)",
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de NAV disponíveis")
    
    with col2:
        st.subheader("📊 Número de Posições")
        if data['portfolio_snapshots'] is not None and not data['portfolio_snapshots'].empty:
            if 'num_positions' in data['portfolio_snapshots'].columns:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data['portfolio_snapshots']['timestamp'],
                    y=data['portfolio_snapshots']['num_positions'],
                    mode='lines+markers',
                    name='Posições',
                    line=dict(color='#2ca02c', width=2),
                    marker=dict(size=4)
                ))
                fig.update_layout(
                    xaxis_title="Data",
                    yaxis_title="Número de Posições",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados de posições não disponíveis")
        else:
            st.info("Sem dados disponíveis")
    
    st.divider()
    
    # Análise de estratégias
    st.header("🎯 Análise por Estratégia")
    
    if data['orders'] is not None and not data['orders'].empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Ordens por estratégia
            if 'tag' in data['orders'].columns:
                strategy_counts = data['orders']['tag'].value_counts()
                fig = px.pie(
                    values=strategy_counts.values,
                    names=strategy_counts.index,
                    title="Distribuição de Ordens por Estratégia"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # P&L por estratégia
            if 'tag' in data['orders'].columns and 'est_pnl' in data['orders'].columns:
                pnl_by_strategy = data['orders'].groupby('tag')['est_pnl'].sum().sort_values()
                fig = go.Figure()
                colors = ['green' if x > 0 else 'red' for x in pnl_by_strategy.values]
                fig.add_trace(go.Bar(
                    x=pnl_by_strategy.index,
                    y=pnl_by_strategy.values,
                    marker_color=colors,
                    text=[f"R$ {x:,.2f}" for x in pnl_by_strategy.values],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="P&L Estimado por Estratégia",
                    xaxis_title="Estratégia",
                    yaxis_title="P&L (R$)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Tabelas de dados
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Ordens", "✅ Fills", "💼 Portfólio", "📝 Logs"])
    
    with tab1:
        st.subheader("Histórico de Ordens")
        if data['orders'] is not None and not data['orders'].empty:
            st.dataframe(
                data['orders'][['timestamp', 'order_id', 'side', 'instrument', 'qty', 'limit_price', 'tag', 'est_pnl']].tail(100),
                use_container_width=True,
                hide_index=True
            )
            
            # Estatísticas
            st.subheader("Estatísticas de Ordens")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Ordens", len(data['orders']))
            with col2:
                if 'est_pnl' in data['orders'].columns:
                    st.metric("P&L Total Estimado", f"R$ {data['orders']['est_pnl'].sum():,.2f}")
            with col3:
                if 'side' in data['orders'].columns:
                    buy_count = len(data['orders'][data['orders']['side'] == 'BUY'])
                    sell_count = len(data['orders'][data['orders']['side'] == 'SELL'])
                    st.metric("Buy/Sell", f"{buy_count}/{sell_count}")
        else:
            st.info("Nenhuma ordem encontrada")
    
    with tab2:
        st.subheader("Histórico de Execuções (Fills)")
        if data['fills'] is not None and not data['fills'].empty:
            st.dataframe(
                data['fills'][['timestamp', 'order_id', 'instrument', 'side', 'filled_qty', 'fill_price', 'commission', 'slippage']].tail(100),
                use_container_width=True,
                hide_index=True
            )
            
            # Estatísticas
            st.subheader("Estatísticas de Execução")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Fills", len(data['fills']))
            with col2:
                if 'commission' in data['fills'].columns:
                    st.metric("Comissão Total", f"R$ {data['fills']['commission'].sum():,.2f}")
            with col3:
                if 'slippage' in data['fills'].columns:
                    avg_slippage = data['fills']['slippage'].mean() * 100
                    st.metric("Slippage Médio", f"{avg_slippage:.4f}%")
        else:
            st.info("Nenhum fill encontrado")
    
    with tab3:
        st.subheader("Snapshots do Portfólio")
        if data['portfolio_snapshots'] is not None and not data['portfolio_snapshots'].empty:
            st.dataframe(
                data['portfolio_snapshots'].tail(50),
                use_container_width=True,
                hide_index=True
            )
            
            # Último snapshot
            if len(data['portfolio_snapshots']) > 0:
                last_snapshot = data['portfolio_snapshots'].iloc[-1]
                st.subheader("Estado Atual do Portfólio")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("NAV Atual", f"R$ {last_snapshot.get('nav', 0):,.2f}")
                with col2:
                    st.metric("Cash", f"R$ {last_snapshot.get('cash', 0):,.2f}")
                with col3:
                    st.metric("Posições Abertas", int(last_snapshot.get('num_positions', 0)))
        else:
            st.info("Nenhum snapshot encontrado")
    
    with tab4:
        st.subheader("Logs de Decisões")
        if data['logs'] is not None and not data['logs'].empty:
            # Filtrar por tipo de evento
            event_types = st.multiselect(
                "Filtrar por tipo de evento",
                options=data['logs']['event_type'].unique() if 'event_type' in data['logs'].columns else [],
                default=data['logs']['event_type'].unique() if 'event_type' in data['logs'].columns else []
            )
            
            filtered_logs = data['logs']
            if event_types and 'event_type' in filtered_logs.columns:
                filtered_logs = filtered_logs[filtered_logs['event_type'].isin(event_types)]
            
            st.dataframe(
                filtered_logs.tail(100),
                use_container_width=True,
                hide_index=True
            )
            
            # Estatísticas de logs
            if 'event_type' in data['logs'].columns:
                st.subheader("Distribuição de Eventos")
                event_counts = data['logs']['event_type'].value_counts()
                fig = px.bar(
                    x=event_counts.index,
                    y=event_counts.values,
                    title="Eventos por Tipo"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum log encontrado")
    
    # Footer
    st.divider()
    st.caption(f"Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("💡 Execute `run_backtest.py` para gerar novos dados")

if __name__ == '__main__':
    main()

