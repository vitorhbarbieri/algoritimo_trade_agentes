"""
Dashboard Central - Monitoramento Completo do Sistema de Trading
Visualiza tudo em uma única tela: agentes, métricas, portfólio, backtest.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Dashboard Central - Trading Agents",
    page_icon="📊",
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
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-online {
        color: #00cc00;
        font-weight: bold;
    }
    .status-offline {
        color: #cc0000;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

BASE_URL = "http://localhost:5000"

# Lista de 30 ações para monitoramento
TICKERS_MONITORADOS = [
    # Ações Brasileiras (15)
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
    'WEGE3.SA', 'MGLU3.SA', 'SUZB3.SA', 'RENT3.SA', 'ELET3.SA',
    'BBAS3.SA', 'SANB11.SA', 'B3SA3.SA', 'RADL3.SA', 'HAPV3.SA',
    # Ações Americanas (15)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
    'META', 'NVDA', 'JPM', 'V', 'JNJ',
    'WMT', 'PG', 'MA', 'DIS', 'NFLX'
]

@st.cache_data(ttl=5)
def get_api_health():
    """Verifica saúde da API."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

@st.cache_data(ttl=10)
def get_metrics():
    """Obtém métricas do backtest."""
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@st.cache_data(ttl=10)
def get_agents_activity():
    """Obtém atividade dos agentes."""
    try:
        response = requests.get(f"{BASE_URL}/agents/activity", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@st.cache_data(ttl=10)
def get_backtest_results():
    """Obtém resultados do backtest."""
    try:
        response = requests.get(f"{BASE_URL}/backtest/results", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@st.cache_data(ttl=5)
def get_monitoring_status():
    """Obtém status do monitoramento."""
    try:
        response = requests.get(f"{BASE_URL}/monitoring/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def start_monitoring(interval=300):
    """Inicia monitoramento."""
    try:
        response = requests.post(f"{BASE_URL}/monitoring/start", json={'interval_seconds': interval}, timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def stop_monitoring():
    """Para monitoramento."""
    try:
        response = requests.post(f"{BASE_URL}/monitoring/stop", timeout=5)
        return response.status_code == 200
    except:
        return False

def manual_scan():
    """Executa scan manual."""
    try:
        response = requests.post(f"{BASE_URL}/monitoring/scan", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def load_logs():
    """Carrega logs dos agentes."""
    log_dir = Path("logs")
    if not log_dir.exists():
        return []
    
    logs = []
    for log_file in sorted(log_dir.glob("*.jsonl"), reverse=True)[:1]:  # Último arquivo
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except:
            continue
    
    return sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)

def main():
    """Função principal do dashboard."""
    
    # Header
    st.markdown('<div class="main-header">📊 Dashboard Central - Trading Agents</div>', unsafe_allow_html=True)
    
    # Sidebar - Configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Status da API
        api_online, health_data = get_api_health()
        if api_online:
            st.success("✅ API Online")
            if health_data:
                st.caption(f"Última atualização: {health_data.get('timestamp', 'N/A')[:19]}")
        else:
            st.error("❌ API Offline")
            st.warning("Certifique-se de que o servidor está rodando:\n`python run_api.py`")
        
        st.divider()
        
        # Seleção de tickers
        st.subheader("📈 Ações Monitoradas")
        st.info(f"Total: {len(TICKERS_MONITORADOS)} ações")
        
        # Filtros
        st.subheader("🔍 Filtros")
        show_brasileiras = st.checkbox("Ações Brasileiras", value=True)
        show_americanas = st.checkbox("Ações Americanas", value=True)
        
        tickers_filtrados = []
        if show_brasileiras:
            tickers_filtrados.extend([t for t in TICKERS_MONITORADOS if '.SA' in t])
        if show_americanas:
            tickers_filtrados.extend([t for t in TICKERS_MONITORADOS if '.SA' not in t])
        
        st.divider()
        
        # Status do Monitoramento
        st.subheader("🔍 Monitoramento do Mercado")
        monitoring_status = get_monitoring_status()
        
        if monitoring_status and 'monitoring' in monitoring_status:
            mon = monitoring_status['monitoring']
            if mon.get('is_running', False):
                st.success("✅ Monitoramento ATIVO")
                last_scan_time = mon.get('last_scan_time')
                if last_scan_time:
                    try:
                        last_scan_str = str(last_scan_time)
                        st.caption(f"Último scan: {last_scan_str[:19] if len(last_scan_str) > 19 else last_scan_str}")
                    except:
                        st.caption("Último scan: N/A")
                st.caption(f"Oportunidades encontradas: {mon.get('opportunities_found', 0)}")
                st.caption(f"Propostas geradas: {mon.get('proposals_generated', 0)}")
                
                col_mon1, col_mon2 = st.columns(2)
                with col_mon1:
                    if st.button("⏸️ Parar Monitoramento", use_container_width=True):
                        stop_monitoring()
                        st.cache_data.clear()
                        st.rerun()
                with col_mon2:
                    if st.button("🔍 Scan Manual", use_container_width=True):
                        with st.spinner("Escaneando mercado..."):
                            result = manual_scan()
                            if result:
                                st.success(f"Scan completo! {result.get('scan_result', {}).get('opportunities', 0)} oportunidades encontradas")
                                st.cache_data.clear()
            else:
                st.info("⏸️ Monitoramento INATIVO")
                col_mon1, col_mon2 = st.columns(2)
                with col_mon1:
                    if st.button("▶️ Iniciar Monitoramento", type="primary", use_container_width=True):
                        start_monitoring(300)  # 5 minutos
                        st.cache_data.clear()
                        st.rerun()
                with col_mon2:
                    if st.button("🔍 Scan Manual", use_container_width=True):
                        with st.spinner("Escaneando mercado..."):
                            result = manual_scan()
                            if result:
                                st.success(f"Scan completo! {result.get('scan_result', {}).get('opportunities', 0)} oportunidades encontradas")
                                st.cache_data.clear()
        
        st.divider()
        
        # Botão para executar backtest
        st.subheader("🚀 Ações Rápidas")
        if st.button("🔄 Executar Backtest", type="primary", use_container_width=True):
            with st.spinner("Executando backtest..."):
                try:
                    response = requests.post(
                        f"{BASE_URL}/backtest/run",
                        json={
                            'tickers': tickers_filtrados[:10],  # Limitar para não demorar muito
                            'use_real_data': True
                        },
                        timeout=300
                    )
                    if response.status_code == 200:
                        st.success("✅ Backtest executado com sucesso!")
                        st.cache_data.clear()
                    else:
                        st.error(f"Erro: {response.text}")
                except Exception as e:
                    st.error(f"Erro ao executar backtest: {e}")
        
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Verificar se API está online
    if not api_online:
        st.error("⚠️ **API não está respondendo!**")
        st.info("Para iniciar o servidor, execute em um terminal:\n```bash\npython run_api.py\n```")
        return
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Visão Geral",
        "🤖 Atividade dos Agentes",
        "💰 Portfólio",
        "📈 Backtest",
        "📋 Ações Monitoradas",
        "📝 Log de Monitoramento"
    ])
    
    # TAB 1: Visão Geral
    with tab1:
        st.header("📊 Visão Geral do Sistema")
        
        # Métricas principais
        metrics_data = get_metrics()
        activity_data = get_agents_activity()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if metrics_data and 'metrics' in metrics_data:
                metrics = metrics_data['metrics']
                st.metric("Retorno Total", f"{metrics.get('total_return', 0):.2f}%")
            else:
                st.metric("Retorno Total", "N/A")
        
        with col2:
            if metrics_data and 'metrics' in metrics_data:
                metrics = metrics_data['metrics']
                st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.4f}")
            else:
                st.metric("Sharpe Ratio", "N/A")
        
        with col3:
            if activity_data and 'activity' in activity_data:
                activity = activity_data['activity']
                st.metric("Propostas Geradas", activity.get('trader_proposals', 0))
            else:
                st.metric("Propostas Geradas", 0)
        
        with col4:
            if activity_data and 'activity' in activity_data:
                activity = activity_data['activity']
                st.metric("Execuções", activity.get('executions', 0))
            else:
                st.metric("Execuções", 0)
        
        st.divider()
        
        # Gráfico de NAV
        results = get_backtest_results()
        if results and 'results' in results and 'snapshots' in results['results']:
            snapshots = results['results']['snapshots']
            if snapshots:
                df_snapshots = pd.DataFrame(snapshots)
                if 'date' in df_snapshots.columns and 'nav' in df_snapshots.columns:
                    df_snapshots['date'] = pd.to_datetime(df_snapshots['date'])
                    df_snapshots = df_snapshots.sort_values('date')
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_snapshots['date'],
                        y=df_snapshots['nav'],
                        mode='lines',
                        name='NAV',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    fig.update_layout(
                        title="Evolução do NAV (Patrimônio Líquido)",
                        xaxis_title="Data",
                        yaxis_title="NAV (R$)",
                        height=400,
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Atividade recente
        st.subheader("🕐 Atividade Recente")
        logs = load_logs()
        if logs:
            df_logs = pd.DataFrame(logs[:20])
            if not df_logs.empty:
                # Selecionar colunas disponíveis
                available_cols = ['timestamp', 'event_type']
                for col in ['proposal_id', 'strategy', 'decision']:
                    if col in df_logs.columns:
                        available_cols.append(col)
                
                st.dataframe(
                    df_logs[available_cols].head(10),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("Nenhuma atividade registrada ainda. Execute um backtest para ver atividade.")
    
    # TAB 2: Atividade dos Agentes
    with tab2:
        st.header("🤖 Atividade dos Agentes")
        
        activity_data = get_agents_activity()
        
        if activity_data and 'activity' in activity_data:
            activity = activity_data['activity']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Propostas do TraderAgent", activity.get('trader_proposals', 0))
            
            with col2:
                st.metric("Avaliações do RiskAgent", activity.get('risk_evaluations', 0))
            
            with col3:
                st.metric("Execuções", activity.get('executions', 0))
            
            st.divider()
            
            # Gráfico de atividade por tipo
            if activity.get('recent_activity'):
                df_activity = pd.DataFrame(activity['recent_activity'])
                
                # Contagem por tipo
                event_counts = df_activity['event_type'].value_counts()
                
                fig = px.pie(
                    values=event_counts.values,
                    names=event_counts.index,
                    title="Distribuição de Atividades",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de atividades recentes
                st.subheader("📋 Atividades Recentes")
                # Selecionar colunas disponíveis
                available_cols = ['timestamp', 'event_type']
                for col in ['proposal_id', 'strategy', 'decision']:
                    if col in df_activity.columns:
                        available_cols.append(col)
                
                st.dataframe(
                    df_activity[available_cols].head(20),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("Nenhuma atividade disponível. Execute um backtest primeiro.")
    
    # TAB 3: Portfólio
    with tab3:
        st.header("💰 Status do Portfólio")
        
        results = get_backtest_results()
        
        if results and 'results' in results:
            res = results['results']
            
            # Último snapshot
            if 'snapshots' in res and res['snapshots']:
                latest = res['snapshots'][-1]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("NAV Atual", f"R$ {latest.get('nav', 0):,.2f}")
                
                with col2:
                    st.metric("Cash", f"R$ {latest.get('cash', 0):,.2f}")
                
                with col3:
                    st.metric("Valor das Posições", f"R$ {latest.get('position_value', 0):,.2f}")
                
                # Posições atuais
                positions = latest.get('positions', {})
                if positions:
                    st.subheader("📊 Posições Atuais")
                    df_positions = pd.DataFrame([
                        {'Símbolo': symbol, 'Quantidade': qty}
                        for symbol, qty in positions.items()
                    ])
                    st.dataframe(df_positions, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhuma posição aberta no momento.")
            
            # Execuções
            if 'fills' in res and res['fills']:
                st.subheader("💼 Histórico de Execuções")
                df_fills = pd.DataFrame(res['fills'])
                
                # Resumo por símbolo
                if not df_fills.empty and 'symbol' in df_fills.columns:
                    fills_summary = df_fills.groupby('symbol').agg({
                        'quantity': 'sum',
                        'total_cost': 'sum',
                        'commission': 'sum'
                    }).reset_index()
                    fills_summary.columns = ['Símbolo', 'Quantidade Total', 'Custo Total', 'Comissões']
                    st.dataframe(fills_summary, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado de portfólio disponível. Execute um backtest primeiro.")
    
    # TAB 4: Backtest
    with tab4:
        st.header("📈 Backtest e Métricas")
        
        metrics_data = get_metrics()
        
        if metrics_data and 'metrics' in metrics_data:
            metrics = metrics_data['metrics']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Retorno Total", f"{metrics.get('total_return', 0):.2f}%")
            
            with col2:
                st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.4f}")
            
            with col3:
                st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.2f}%")
            
            with col4:
                st.metric("Win Rate", f"{metrics.get('win_rate', 0):.2f}%")
            
            st.divider()
            
            # Gráfico de métricas
            metric_names = ['Retorno Total', 'Sharpe Ratio', 'Win Rate']
            metric_values = [
                metrics.get('total_return', 0),
                metrics.get('sharpe_ratio', 0) * 100,  # Normalizar
                metrics.get('win_rate', 0)
            ]
            
            fig = go.Figure(data=[
                go.Bar(x=metric_names, y=metric_values, marker_color='#1f77b4')
            ])
            fig.update_layout(
                title="Métricas de Performance",
                yaxis_title="Valor",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela completa de métricas
            st.subheader("📊 Todas as Métricas")
            df_metrics = pd.DataFrame([metrics])
            st.dataframe(df_metrics.T, use_container_width=True)
        else:
            st.info("Nenhuma métrica disponível. Execute um backtest primeiro.")
    
    # TAB 5: Ações Monitoradas
    with tab5:
        st.header("📋 Ações Monitoradas")
        st.info(f"Total de {len(TICKERS_MONITORADOS)} ações sendo monitoradas pelos agentes")
        
        # Dividir em brasileiras e americanas
        brasileiras = [t for t in TICKERS_MONITORADOS if '.SA' in t]
        americanas = [t for t in TICKERS_MONITORADOS if '.SA' not in t]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🇧🇷 Ações Brasileiras (15)")
            df_br = pd.DataFrame({'Ticker': brasileiras})
            st.dataframe(df_br, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("🇺🇸 Ações Americanas (15)")
            df_us = pd.DataFrame({'Ticker': americanas})
            st.dataframe(df_us, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Informações sobre monitoramento
        st.subheader("ℹ️ Sobre o Monitoramento")
        st.markdown("""
        Os agentes estão configurados para:
        - ✅ Buscar oportunidades de **Volatility Arbitrage**
        - ✅ Identificar **Pairs Trading** (cointegração)
        - ✅ Analisar **assimetrias de mercado**
        - ✅ Aplicar **gestão de risco** automática
        
        O sistema monitora essas ações continuamente e gera propostas quando encontra oportunidades.
        """)
    
    # TAB 6: Log de Monitoramento
    with tab6:
        st.header("📝 Log de Monitoramento em Tempo Real")
        
        # Status do monitoramento
        monitoring_status = get_monitoring_status()
        
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            if monitoring_status and 'monitoring' in monitoring_status:
                mon = monitoring_status['monitoring']
                if mon.get('is_running', False):
                    st.success("🟢 **MONITORAMENTO ATIVO**")
                    st.metric("Status", "Rodando")
                else:
                    st.info("⚪ **MONITORAMENTO INATIVO**")
                    st.metric("Status", "Parado")
            else:
                st.warning("⚠️ **Status Desconhecido**")
                st.metric("Status", "N/A")
        
        with col_status2:
            if monitoring_status and 'monitoring' in monitoring_status:
                mon = monitoring_status['monitoring']
                last_scan = mon.get('last_scan_time')
                if last_scan and last_scan != 'Nunca':
                    try:
                        last_scan_str = str(last_scan)
                        st.metric("Último Scan", last_scan_str[:19] if len(last_scan_str) > 19 else last_scan_str)
                    except:
                        st.metric("Último Scan", "N/A")
                else:
                    st.metric("Último Scan", "Nunca")
            else:
                st.metric("Último Scan", "N/A")
        
        with col_status3:
            if monitoring_status and 'monitoring' in monitoring_status:
                mon = monitoring_status['monitoring']
                st.metric("Oportunidades", mon.get('opportunities_found', 0))
                st.metric("Propostas", mon.get('proposals_generated', 0))
            else:
                st.metric("Oportunidades", 0)
                st.metric("Propostas", 0)
        
        st.divider()
        
        # Estratégias sendo buscadas
        st.subheader("🎯 Estratégias Ativas")
        
        strategies_col1, strategies_col2 = st.columns(2)
        
        with strategies_col1:
            st.markdown("""
            **1. Volatility Arbitrage** 🔄
            - Buscando: Opções com IV diferente da histórica
            - Threshold: 8% de mispricing
            - Status: ✅ Ativo
            
            **2. Pairs Trading** 📊
            - Buscando: Pares de ações com desvio
            - Threshold: Z-score > 2.0
            - Status: ✅ Ativo
            
            **3. Spread Arbitrage** 💰
            - Buscando: Spreads bid-ask anormais
            - Threshold: > 0.5%
            - Status: ✅ Ativo
            """)
        
        with strategies_col2:
            st.markdown("""
            **4. Momentum** 📈
            - Buscando: Movimentos fortes + volume
            - Threshold: Momentum > 2% + volume spike > 1.5x
            - Status: ✅ Ativo
            
            **5. Mean Reversion** 🔄
            - Buscando: Desvios extremos da média
            - Threshold: Z-score > 2.0
            - Status: ✅ Ativo
            """)
        
        st.divider()
        
        # Oportunidades encontradas recentemente
        st.subheader("🔍 Oportunidades Encontradas Recentemente")
        
        if monitoring_status and 'monitoring' in monitoring_status:
            mon = monitoring_status['monitoring']
            recent_opps = mon.get('recent_opportunities', [])
            
            if recent_opps:
                for i, opp in enumerate(recent_opps[:10], 1):
                    with st.expander(f"🎯 Oportunidade #{i}: {opp.get('type', 'N/A').upper()} - {opp.get('ticker', 'N/A')}", expanded=False):
                        col_opp1, col_opp2 = st.columns(2)
                        
                        with col_opp1:
                            st.write(f"**Tipo:** {opp.get('type', 'N/A')}")
                            st.write(f"**Ticker:** {opp.get('ticker', 'N/A')}")
                            st.write(f"**Score:** {opp.get('opportunity_score', 0):.4f}")
                        
                        with col_opp2:
                            if 'mispricing' in opp:
                                st.write(f"**Mispricing:** {opp['mispricing']*100:.2f}%")
                            if 'iv_spread' in opp:
                                st.write(f"**IV Spread:** {opp['iv_spread']*100:.2f}%")
                            if 'zscore' in opp:
                                st.write(f"**Z-Score:** {opp['zscore']:.2f}")
                            if 'spread_pct' in opp:
                                st.write(f"**Spread:** {opp['spread_pct']:.2f}%")
            else:
                st.info("Nenhuma oportunidade encontrada ainda. O monitoramento está escaneando o mercado...")
        else:
            st.info("Inicie o monitoramento para ver oportunidades.")
        
        st.divider()
        
        # Feedback das ações (propostas -> avaliações -> execuções)
        st.subheader("📋 Feedback das Ações - Fluxo Completo")
        
        # Carregar logs
        logs = load_logs()
        
        if logs:
            # Filtrar por tipo de evento
            trader_proposals = [l for l in logs if l.get('event_type') == 'trader_proposal']
            risk_evaluations = [l for l in logs if l.get('event_type') == 'risk_evaluation']
            executions = [l for l in logs if l.get('event_type') == 'execution']
            
            # Mostrar fluxo completo
            st.markdown("### Fluxo: Proposta → Avaliação → Execução")
            
            # Agrupar por proposal_id
            proposals_dict = {}
            for prop in trader_proposals:
                prop_id = prop.get('proposal_id', 'unknown')
                proposals_dict[prop_id] = {
                    'proposal': prop,
                    'evaluation': None,
                    'execution': None
                }
            
            # Associar avaliações
            for eval_log in risk_evaluations:
                prop_id = eval_log.get('proposal_id', 'unknown')
                if prop_id in proposals_dict:
                    proposals_dict[prop_id]['evaluation'] = eval_log
            
            # Associar execuções
            for exec_log in executions:
                order_id = exec_log.get('order_id', 'unknown')
                # Tentar encontrar proposta relacionada
                for prop_id, data in proposals_dict.items():
                    if prop_id in order_id or order_id in prop_id:
                        proposals_dict[prop_id]['execution'] = exec_log
                        break
            
            # Mostrar fluxo completo
            for prop_id, data in list(proposals_dict.items())[:20]:  # Últimas 20
                prop = data['proposal']
                eval_log = data['evaluation']
                exec_log = data['execution']
                
                with st.expander(f"📌 {prop_id} - {prop.get('strategy', 'N/A')}", expanded=False):
                    # Proposta
                    st.markdown("**1️⃣ PROPOSTA DO TRADERAGENT**")
                    col_prop1, col_prop2 = st.columns(2)
                    with col_prop1:
                        st.write(f"**Estratégia:** {prop.get('strategy', 'N/A')}")
                        st.write(f"**Timestamp:** {prop.get('timestamp', 'N/A')[:19]}")
                    with col_prop2:
                        if 'mispricing' in prop:
                            st.write(f"**Mispricing:** {prop['mispricing']*100:.2f}%")
                        if 'zscore' in prop:
                            st.write(f"**Z-Score:** {prop['zscore']:.2f}")
                    
                    st.divider()
                    
                    # Avaliação
                    if eval_log:
                        st.markdown("**2️⃣ AVALIAÇÃO DO RISKAGENT**")
                        decision = eval_log.get('decision', 'N/A')
                        reason = eval_log.get('reason', 'N/A')
                        
                        if decision == 'APPROVE':
                            st.success(f"✅ **APROVADA** - {reason}")
                        elif decision == 'REJECT':
                            st.error(f"❌ **REJEITADA** - {reason}")
                        elif decision == 'MODIFY':
                            st.warning(f"⚠️ **MODIFICADA** - {reason}")
                        else:
                            st.info(f"📋 **{decision}** - {reason}")
                        
                        st.write(f"**Timestamp:** {eval_log.get('timestamp', 'N/A')[:19]}")
                        
                        st.divider()
                        
                        # Execução
                        if exec_log and decision == 'APPROVE':
                            st.markdown("**3️⃣ EXECUÇÃO**")
                            status = exec_log.get('status', 'N/A')
                            symbol = exec_log.get('symbol', 'N/A')
                            quantity = exec_log.get('quantity', 0)
                            price = exec_log.get('price', 0)
                            
                            if status == 'FILLED':
                                st.success(f"✅ **EXECUTADA** - {symbol} x{quantity} @ R${price:.2f}")
                            else:
                                st.info(f"📋 **{status}** - {symbol}")
                            
                            st.write(f"**Timestamp:** {exec_log.get('timestamp', 'N/A')[:19]}")
                        elif decision == 'APPROVE':
                            st.info("⏳ Aguardando execução...")
                    else:
                        st.info("⏳ Aguardando avaliação do RiskAgent...")
        else:
            st.info("Nenhuma atividade registrada ainda. Execute um backtest ou inicie o monitoramento para ver atividade.")
        
        st.divider()
        
        # Log em tempo real (últimas atividades)
        st.subheader("🕐 Log em Tempo Real")
        
        # Botão para atualizar
        col_refresh1, col_refresh2 = st.columns([3, 1])
        with col_refresh1:
            auto_refresh = st.checkbox("🔄 Atualização Automática (5s)", value=False)
        with col_refresh2:
            if st.button("🔄 Atualizar Agora"):
                st.cache_data.clear()
                st.rerun()
        
        if auto_refresh:
            time.sleep(5)
            st.cache_data.clear()
            st.rerun()
        
        # Mostrar últimas atividades
        if logs:
            st.markdown("### Últimas Atividades")
            
            # Criar timeline
            for log_entry in logs[:30]:  # Últimas 30
                event_type = log_entry.get('event_type', 'unknown')
                timestamp = log_entry.get('timestamp', 'N/A')
                
                # Ícone baseado no tipo
                icons = {
                    'trader_proposal': '💡',
                    'risk_evaluation': '🛡️',
                    'execution': '💰',
                    'kill_switch': '🛑'
                }
                icon = icons.get(event_type, '📋')
                
                # Cor baseada no tipo
                if event_type == 'trader_proposal':
                    st.markdown(f"{icon} **[{timestamp[:19]}]** Proposta: {log_entry.get('proposal_id', 'N/A')} - {log_entry.get('strategy', 'N/A')}")
                elif event_type == 'risk_evaluation':
                    decision = log_entry.get('decision', 'N/A')
                    if decision == 'APPROVE':
                        st.markdown(f"{icon} **[{timestamp[:19]}]** ✅ Avaliação: {log_entry.get('proposal_id', 'N/A')} - {decision}")
                    elif decision == 'REJECT':
                        st.markdown(f"{icon} **[{timestamp[:19]}]** ❌ Avaliação: {log_entry.get('proposal_id', 'N/A')} - {decision}")
                    else:
                        st.markdown(f"{icon} **[{timestamp[:19]}]** ⚠️ Avaliação: {log_entry.get('proposal_id', 'N/A')} - {decision}")
                elif event_type == 'execution':
                    st.markdown(f"{icon} **[{timestamp[:19]}]** Execução: {log_entry.get('order_id', 'N/A')} - {log_entry.get('status', 'N/A')}")
                else:
                    st.markdown(f"{icon} **[{timestamp[:19]}]** {event_type}: {log_entry.get('proposal_id', log_entry.get('order_id', 'N/A'))}")
        else:
            st.info("Nenhum log disponível. Execute um backtest ou inicie o monitoramento.")

if __name__ == '__main__':
    main()

