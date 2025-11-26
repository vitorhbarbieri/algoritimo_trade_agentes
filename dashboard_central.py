"""
Dashboard Central - Monitoramento Completo do Sistema de Trading
Visualiza tudo em uma única tela: agentes, métricas, portfólio, backtest.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
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

@st.cache_data(ttl=10)
def get_agents_health():
    """Obtém status de saúde dos agentes."""
    try:
        response = requests.get(f"{BASE_URL}/agents/health", timeout=10)
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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Visão Geral",
        "🤖 Atividade dos Agentes",
        "💚 Saúde dos Agentes",
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
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
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
        
        with col5:
            # Contar propostas de daytrade
            if activity_data and 'activity' in activity_data:
                activity = activity_data['activity']
                if activity.get('recent_activity'):
                    daytrade_count = sum(1 for a in activity['recent_activity'] 
                                       if a.get('strategy') == 'daytrade_options')
                    st.metric("Daytrade Options", daytrade_count)
                else:
                    st.metric("Daytrade Options", 0)
            else:
                st.metric("Daytrade Options", 0)
        
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
            
            # Métricas gerais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Propostas do TraderAgent", activity.get('trader_proposals', 0))
            
            with col2:
                st.metric("Avaliações do RiskAgent", activity.get('risk_evaluations', 0))
            
            with col3:
                st.metric("Execuções", activity.get('executions', 0))
            
            with col4:
                # Contar propostas por estratégia
                if activity.get('recent_activity'):
                    daytrade_count = sum(1 for a in activity['recent_activity'] 
                                       if a.get('strategy') == 'daytrade_options')
                    st.metric("Daytrade Options", daytrade_count)
                else:
                    st.metric("Daytrade Options", 0)
            
            st.divider()
            
            # Seção específica para Daytrade Options
            st.subheader("📈 Agente Daytrade Options")
            
            if activity.get('recent_activity'):
                df_activity = pd.DataFrame(activity['recent_activity'])
                
                # Filtrar atividades de daytrade
                if 'strategy' in df_activity.columns:
                    daytrade_activities = df_activity[df_activity['strategy'] == 'daytrade_options'].copy()
                else:
                    daytrade_activities = pd.DataFrame()
                
                if not daytrade_activities.empty:
                    # Métricas específicas do daytrade
                    col_dt1, col_dt2, col_dt3, col_dt4 = st.columns(4)
                    
                    with col_dt1:
                        st.metric("Propostas Daytrade", len(daytrade_activities))
                    
                    with col_dt2:
                        # Calcular taxa de aprovação
                        daytrade_evaluations = [a for a in activity['recent_activity'] 
                                              if a.get('strategy') == 'daytrade_options' 
                                              and a.get('event_type') == 'risk_evaluation']
                        approved = sum(1 for e in daytrade_evaluations if e.get('decision') == 'APPROVE')
                        approval_rate = (approved / len(daytrade_evaluations) * 100) if daytrade_evaluations else 0
                        st.metric("Taxa de Aprovação", f"{approval_rate:.1f}%")
                    
                    with col_dt3:
                        # Média de momentum intraday
                        momentums = []
                        for act in daytrade_activities.to_dict('records'):
                            if 'metadata' in act and isinstance(act['metadata'], dict):
                                mom = act['metadata'].get('intraday_return', 0)
                                if mom:
                                    momentums.append(mom * 100)
                        avg_momentum = np.mean(momentums) if momentums else 0
                        st.metric("Momentum Médio", f"{avg_momentum:.2f}%")
                    
                    with col_dt4:
                        # Média de volume ratio
                        vol_ratios = []
                        for act in daytrade_activities.to_dict('records'):
                            if 'metadata' in act and isinstance(act['metadata'], dict):
                                vr = act['metadata'].get('volume_ratio', 0)
                                if vr:
                                    vol_ratios.append(vr)
                        avg_vol_ratio = np.mean(vol_ratios) if vol_ratios else 0
                        st.metric("Volume Ratio Médio", f"{avg_vol_ratio:.2f}x")
                    
                    st.divider()
                    
                    # Gráficos específicos do daytrade
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        # Gráfico de momentum por proposta
                        if momentums:
                            fig_momentum = go.Figure()
                            fig_momentum.add_trace(go.Bar(
                                x=list(range(len(momentums))),
                                y=momentums,
                                marker_color='green',
                                name='Momentum Intraday (%)'
                            ))
                            fig_momentum.update_layout(
                                title="Momentum Intraday das Propostas",
                                xaxis_title="Proposta",
                                yaxis_title="Momentum (%)",
                                height=300
                            )
                            st.plotly_chart(fig_momentum, use_container_width=True)
                    
                    with col_chart2:
                        # Gráfico de volume ratio
                        if vol_ratios:
                            fig_vol = go.Figure()
                            fig_vol.add_trace(go.Bar(
                                x=list(range(len(vol_ratios))),
                                y=vol_ratios,
                                marker_color='blue',
                                name='Volume Ratio'
                            ))
                            fig_vol.update_layout(
                                title="Volume Ratio das Propostas",
                                xaxis_title="Proposta",
                                yaxis_title="Volume Ratio",
                                height=300
                            )
                            st.plotly_chart(fig_vol, use_container_width=True)
                    
                    st.divider()
                    
                    # Tabela detalhada de propostas de daytrade
                    st.subheader("📊 Detalhes das Propostas Daytrade")
                    
                    # Preparar dados para tabela
                    daytrade_table_data = []
                    for act in daytrade_activities.to_dict('records'):
                        metadata = act.get('metadata', {})
                        row = {
                            'Timestamp': act.get('timestamp', 'N/A')[:19] if len(str(act.get('timestamp', ''))) > 19 else act.get('timestamp', 'N/A'),
                            'Proposal ID': act.get('proposal_id', 'N/A'),
                            'Underlying': metadata.get('underlying', 'N/A'),
                            'Strike': metadata.get('strike', 'N/A'),
                            'Delta': f"{metadata.get('delta', 0):.3f}" if metadata.get('delta') else 'N/A',
                            'Gamma': f"{metadata.get('gamma', 0):.6f}" if metadata.get('gamma') else 'N/A',
                            'Momentum': f"{metadata.get('intraday_return', 0)*100:.2f}%" if metadata.get('intraday_return') else 'N/A',
                            'Vol Ratio': f"{metadata.get('volume_ratio', 0):.2f}x" if metadata.get('volume_ratio') else 'N/A',
                            'Spread %': f"{metadata.get('spread_pct', 0)*100:.2f}%" if metadata.get('spread_pct') else 'N/A',
                            'Premium': f"${metadata.get('premium', 0):.2f}" if metadata.get('premium') else 'N/A',
                            'DTE': metadata.get('days_to_expiry', 'N/A')
                        }
                        daytrade_table_data.append(row)
                    
                    if daytrade_table_data:
                        df_daytrade = pd.DataFrame(daytrade_table_data)
                        st.dataframe(df_daytrade, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum dado detalhado disponível nas propostas.")
                else:
                    st.info("⚠️ Nenhuma atividade de daytrade encontrada ainda. Execute um backtest ou inicie o monitoramento para ver atividades do agente de daytrade.")
            
            st.divider()
            
            # Seção para outros agentes (vol_arb e pairs)
            st.subheader("🔄 Outros Agentes")
            
            if activity.get('recent_activity'):
                df_activity = pd.DataFrame(activity['recent_activity'])
                
                # Contagem por estratégia
                if 'strategy' in df_activity.columns:
                    strategy_counts = df_activity[df_activity['strategy'].notna()]['strategy'].value_counts()
                else:
                    strategy_counts = pd.Series(dtype=int)
                
                if not strategy_counts.empty:
                    fig_strategy = px.bar(
                        x=strategy_counts.index,
                        y=strategy_counts.values,
                        title="Propostas por Estratégia",
                        labels={'x': 'Estratégia', 'y': 'Quantidade'},
                        color=strategy_counts.index,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig_strategy, use_container_width=True)
                else:
                    st.info("Nenhuma estratégia encontrada nas atividades recentes.")
                
                # Gráfico de atividade por tipo
                event_counts = df_activity['event_type'].value_counts()
                
                if not event_counts.empty:
                    fig = px.pie(
                        values=event_counts.values,
                        names=event_counts.index,
                        title="Distribuição de Atividades",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de atividades recentes
                st.subheader("📋 Todas as Atividades Recentes")
                # Selecionar colunas disponíveis
                available_cols = []
                for col in ['timestamp', 'event_type', 'proposal_id', 'strategy', 'decision']:
                    if col in df_activity.columns:
                        available_cols.append(col)
                
                if available_cols:
                    st.dataframe(
                        df_activity[available_cols].head(20),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Nenhuma coluna disponível para exibir.")
        else:
            st.info("Nenhuma atividade disponível. Execute um backtest primeiro.")
    
    # TAB 3: Saúde dos Agentes
    with tab3:
        st.header("💚 Status de Saúde dos Agentes")
        
        # Botão para executar teste
        col_test1, col_test2 = st.columns([3, 1])
        with col_test1:
            st.info("🔍 Verifique o status de saúde de todos os agentes do sistema")
        with col_test2:
            if st.button("🔄 Executar Verificação", type="primary", use_container_width=True):
                with st.spinner("Verificando saúde dos agentes..."):
                    try:
                        response = requests.post(f"{BASE_URL}/agents/test", timeout=30)
                        if response.status_code == 200:
                            st.success("✅ Verificação concluída!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Erro: {response.text}")
                    except Exception as e:
                        st.error(f"Erro ao executar verificação: {e}")
        
        st.divider()
        
        # Obter status de saúde
        health_data = get_agents_health()
        
        if health_data and 'health_check' in health_data:
            health_check = health_data['health_check']
            
            # Status geral
            overall_status = health_check.get('overall_status', 'unknown')
            col_status1, col_status2, col_status3 = st.columns(3)
            
            with col_status1:
                if overall_status == 'healthy':
                    st.success("✅ **SISTEMA SAUDÁVEL**")
                    st.metric("Status Geral", "Operacional")
                elif overall_status == 'degraded':
                    st.warning("⚠️ **SISTEMA DEGRADADO**")
                    st.metric("Status Geral", "Parcial")
                else:
                    st.error("❌ **SISTEMA COM PROBLEMAS**")
                    st.metric("Status Geral", "Erro")
            
            with col_status2:
                if health_data.get('last_check'):
                    last_check = health_data['last_check']
                    st.metric("Última Verificação", last_check[:19] if len(last_check) > 19 else last_check)
                else:
                    st.metric("Última Verificação", "Nunca")
            
            with col_status3:
                if health_data.get('recent_activity'):
                    activity = health_data['recent_activity']
                    if activity.get('status') == 'ok':
                        # Função auxiliar para converter valores para int
                        def safe_int_sum(values_dict):
                            total = 0
                            for value in values_dict.values():
                                if isinstance(value, int):
                                    total += value
                                elif isinstance(value, float):
                                    total += int(value)
                                elif isinstance(value, str):
                                    try:
                                        total += int(float(value))
                                    except (ValueError, TypeError):
                                        pass
                            return total
                        
                        total_activities = safe_int_sum(activity.get('activities', {}))
                        st.metric("Atividades (24h)", total_activities)
                    else:
                        st.metric("Atividades (24h)", "N/A")
            
            st.divider()
            
            # Status individual de cada agente
            st.subheader("📋 Status Individual dos Agentes")
            
            agents = health_check.get('agents', {})
            
            for agent_name, agent_status in agents.items():
                status = agent_status.get('status', 'unknown')
                name = agent_status.get('name', agent_name)
                message = agent_status.get('message', '')
                
                with st.expander(f"{'✅' if status == 'healthy' else '⚠️' if status == 'disabled' else '❌'} {name}", expanded=False):
                    col_agent1, col_agent2 = st.columns(2)
                    
                    with col_agent1:
                        if status == 'healthy':
                            st.success(f"**Status:** Operacional")
                        elif status == 'disabled':
                            st.info(f"**Status:** Desabilitado")
                        else:
                            st.error(f"**Status:** Com Problemas")
                        
                        st.write(f"**Mensagem:** {message}")
                        
                        # Mostrar detalhes específicos
                        if 'can_generate_proposals' in agent_status:
                            st.write(f"**Gera Propostas:** {'Sim' if agent_status['can_generate_proposals'] else 'Não'}")
                        if 'test_proposals_count' in agent_status:
                            st.write(f"**Propostas de Teste:** {agent_status['test_proposals_count']}")
                        if 'strategies_loaded' in agent_status:
                            st.write(f"**Estratégias Carregadas:** {agent_status['strategies_loaded']}")
                        if 'config_enabled' in agent_status:
                            st.write(f"**Configuração:** {'Habilitada' if agent_status['config_enabled'] else 'Desabilitada'}")
                    
                    with col_agent2:
                        if 'error' in agent_status:
                            st.error(f"**Erro:** {agent_status['error']}")
                        if 'threshold' in agent_status:
                            st.write(f"**Threshold:** {agent_status['threshold']}")
                        if 'ticker1' in agent_status:
                            st.write(f"**Tickers:** {agent_status.get('ticker1', 'N/A')} / {agent_status.get('ticker2', 'N/A')}")
                        if 'zscore_threshold' in agent_status:
                            st.write(f"**Z-Score Threshold:** {agent_status['zscore_threshold']}")
            
            st.divider()
            
            # Atividade recente
            st.subheader("📊 Atividade Recente (24 horas)")
            
            if health_data.get('recent_activity'):
                activity = health_data['recent_activity']
                
                if activity.get('status') == 'ok':
                    activities = activity.get('activities', {})
                    
                    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
                    
                    # Função auxiliar para converter valores para int
                    def safe_int(value, default=0):
                        if isinstance(value, int):
                            return value
                        elif isinstance(value, float):
                            return int(value)
                        elif isinstance(value, str):
                            try:
                                return int(float(value))
                            except (ValueError, TypeError):
                                return default
                        return default
                    
                    with col_act1:
                        trader_proposals = safe_int(activities.get('trader_proposals', 0))
                        st.metric("Propostas TraderAgent", trader_proposals)
                    
                    with col_act2:
                        risk_evaluations = safe_int(activities.get('risk_evaluations', 0))
                        st.metric("Avaliações RiskAgent", risk_evaluations)
                    
                    with col_act3:
                        executions = safe_int(activities.get('executions', 0))
                        st.metric("Execuções", executions)
                    
                    with col_act4:
                        daytrade_proposals = safe_int(activities.get('daytrade_proposals', 0))
                        st.metric("Daytrade Propostas", daytrade_proposals)
                    
                    st.divider()
                    
                    # Gráfico de atividades por estratégia
                    strategy_activities = {
                        'Daytrade Options': safe_int(activities.get('daytrade_proposals', 0)),
                        'VolArb': safe_int(activities.get('vol_arb_proposals', 0)),
                        'Pairs': safe_int(activities.get('pairs_proposals', 0))
                    }
                    
                    if sum(strategy_activities.values()) > 0:
                        fig_strategy_act = px.bar(
                            x=list(strategy_activities.keys()),
                            y=list(strategy_activities.values()),
                            title="Atividades por Estratégia (24h)",
                            labels={'x': 'Estratégia', 'y': 'Propostas'},
                            color=list(strategy_activities.keys()),
                            color_discrete_sequence=['#00cc00', '#1f77b4', '#ff7f0e']
                        )
                        st.plotly_chart(fig_strategy_act, use_container_width=True)
                    
                    if activities.get('last_activity'):
                        st.info(f"⏰ **Última Atividade:** {activities['last_activity'][:19]}")
                else:
                    st.warning(f"⚠️ {activity.get('message', 'Erro ao verificar atividade')}")
            else:
                st.info("Nenhuma atividade recente encontrada.")
        else:
            st.warning("⚠️ Não foi possível obter status de saúde. Execute uma verificação primeiro.")
            
            if st.button("🔍 Executar Primeira Verificação", type="primary"):
                with st.spinner("Verificando..."):
                    try:
                        response = requests.post(f"{BASE_URL}/agents/test", timeout=30)
                        if response.status_code == 200:
                            st.success("✅ Verificação concluída!")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
    
    # TAB 4: Portfólio
    with tab4:
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
    
    # TAB 5: Backtest
    with tab5:
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
    
    # TAB 6: Ações Monitoradas
    with tab6:
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
    
    # TAB 7: Log de Monitoramento
    with tab7:
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
            
            **3. Daytrade Options** 📈⚡
            - Buscando: CALLs ATM/OTM com momentum intraday
            - Threshold: Momentum ≥ 0.5% + Volume Ratio ≥ 0.25x
            - Delta: 0.20 - 0.60 | DTE ≤ 7 dias
            - Status: ✅ Ativo
            """)
        
        with strategies_col2:
            st.markdown("""
            **4. Spread Arbitrage** 💰
            - Buscando: Spreads bid-ask anormais
            - Threshold: > 0.5%
            - Status: ✅ Ativo
            
            **5. Momentum** 📈
            - Buscando: Movimentos fortes + volume
            - Threshold: Momentum > 2% + volume spike > 1.5x
            - Status: ✅ Ativo
            
            **6. Mean Reversion** 🔄
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

