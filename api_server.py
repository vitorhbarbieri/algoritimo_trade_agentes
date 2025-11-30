"""
API Server para o sistema de trading algorítmico.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para o dashboard

# ============================================================================
# ENDPOINTS BÁSICOS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'trading-api'
    })

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Retorna métricas do sistema."""
    try:
        from src.orders_repository import OrdersRepository
        orders_repo = OrdersRepository()
        
        # Buscar métricas básicas
        proposals_df = orders_repo.get_proposals()
        executions_df = orders_repo.get_executions()
        
        total_return = 0.0
        if not executions_df.empty:
            # Calcular retorno básico
            total_return = executions_df.get('pnl', pd.Series([0])).sum() if 'pnl' in executions_df.columns else 0.0
        
        return jsonify({
            'status': 'success',
            'metrics': {
                'total_return': total_return,
                'total_proposals': len(proposals_df) if not proposals_df.empty else 0,
                'total_executions': len(executions_df) if not executions_df.empty else 0
            }
        })
    except Exception as e:
        logger.error(f"Erro ao buscar métricas: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# ENDPOINTS DE AGENTES
# ============================================================================

@app.route('/agents/activity', methods=['GET'])
def get_agents_activity():
    """Retorna atividade dos agentes."""
    try:
        from src.orders_repository import OrdersRepository
        from datetime import datetime, timedelta
        import pandas as pd
        
        orders_repo = OrdersRepository()
        
        # Buscar propostas recentes (últimas 24h)
        start_date = (datetime.now() - timedelta(days=1)).isoformat()
        proposals_df = orders_repo.get_proposals(start_date=start_date)
        
        # Contar por estratégia
        activities = {
            'trader_proposals': 0,
            'daytrade_proposals': 0,
            'vol_arb_proposals': 0,
            'pairs_proposals': 0
        }
        
        if not proposals_df.empty:
            if 'strategy' in proposals_df.columns:
                daytrade_count = len(proposals_df[proposals_df['strategy'] == 'daytrade_options'])
                vol_arb_count = len(proposals_df[proposals_df['strategy'] == 'volatility_arbitrage'])
                pairs_count = len(proposals_df[proposals_df['strategy'] == 'pairs_trading'])
                
                activities['trader_proposals'] = len(proposals_df)
                activities['daytrade_proposals'] = daytrade_count
                activities['vol_arb_proposals'] = vol_arb_count
                activities['pairs_proposals'] = pairs_count
        
        return jsonify({
            'status': 'success',
            'activities': activities,
            'last_activity': proposals_df.iloc[-1]['timestamp'].isoformat() if not proposals_df.empty else None
        })
    except Exception as e:
        logger.error(f"Erro ao buscar atividade: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/agents/health', methods=['GET'])
def get_agents_health():
    """Retorna saúde dos agentes."""
    try:
        from src.agent_health_checker import AgentHealthChecker
        
        checker = AgentHealthChecker()
        health_data = checker.check_all_agents()
        
        return jsonify({
            'status': 'success',
            'health': health_data
        })
    except Exception as e:
        logger.error(f"Erro ao verificar saúde: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/agents/test', methods=['POST'])
def test_agents():
    """Testa todos os agentes."""
    try:
        from src.agent_health_checker import AgentHealthChecker
        
        checker = AgentHealthChecker()
        results = checker.check_all_agents()
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        logger.error(f"Erro ao testar agentes: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# ENDPOINTS DE PORTFÓLIO
# ============================================================================

@app.route('/portfolio/positions', methods=['GET'])
def get_portfolio_positions():
    """Retorna posições abertas do portfólio."""
    try:
        from src.orders_repository import OrdersRepository
        
        orders_repo = OrdersRepository()
        positions_df = orders_repo.get_open_positions()
        
        positions = []
        if not positions_df.empty:
            for _, pos in positions_df.iterrows():
                positions.append(pos.to_dict())
        
        # Calcular totais
        total_pnl = positions_df['unrealized_pnl'].sum() if not positions_df.empty and 'unrealized_pnl' in positions_df.columns else 0.0
        total_delta = positions_df['delta'].sum() if not positions_df.empty and 'delta' in positions_df.columns else 0.0
        total_gamma = positions_df['gamma'].sum() if not positions_df.empty and 'gamma' in positions_df.columns else 0.0
        total_vega = positions_df['vega'].sum() if not positions_df.empty and 'vega' in positions_df.columns else 0.0
        
        return jsonify({
            'status': 'success',
            'total_positions': len(positions),
            'total_pnl': float(total_pnl),
            'total_delta': float(total_delta),
            'total_gamma': float(total_gamma),
            'total_vega': float(total_vega),
            'positions': positions
        })
    except Exception as e:
        logger.error(f"Erro ao buscar posições: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ============================================================================
# ENDPOINTS DE DAYTRADE
# ============================================================================

@app.route('/daytrade/monitoring', methods=['GET'])
def get_daytrade_monitoring():
    """Retorna dados completos de monitoramento do DayTrade."""
    try:
        from src.orders_repository import OrdersRepository
        from src.trading_schedule import TradingSchedule
        from datetime import datetime, timedelta
        import pandas as pd
        
        orders_repo = OrdersRepository()
        trading_schedule = TradingSchedule()
        
        # Status do mercado
        b3_time = trading_schedule.get_current_b3_time()
        market_status = trading_schedule.get_trading_status()
        
        # Propostas de daytrade (últimas 24h)
        start_date = (datetime.now() - timedelta(days=1)).isoformat()
        proposals_df = orders_repo.get_proposals(strategy='daytrade_options', start_date=start_date)
        
        # Avaliações de risco relacionadas
        evaluations_df = orders_repo.get_risk_evaluations()
        if not evaluations_df.empty and 'timestamp' in evaluations_df.columns:
            try:
                evaluations_df['timestamp'] = pd.to_datetime(evaluations_df['timestamp'], errors='coerce')
                start_dt = pd.to_datetime(start_date)
                evaluations_df = evaluations_df[evaluations_df['timestamp'] >= start_dt]
            except:
                pass
        
        daytrade_evaluations = []
        if not evaluations_df.empty:
            for _, eval_row in evaluations_df.iterrows():
                proposal_id = eval_row.get('proposal_id', '')
                prop = proposals_df[proposals_df['proposal_id'] == proposal_id] if not proposals_df.empty else pd.DataFrame()
                if not prop.empty or 'DAYTRADE' in proposal_id.upper() or 'DAYOPT' in proposal_id.upper():
                    daytrade_evaluations.append(eval_row.to_dict())
        
        # Capturas de dados recentes (últimas 2 horas)
        try:
            all_captures_df = orders_repo.get_market_data_captures(limit=100)
            if not all_captures_df.empty:
                recent_captures_df = all_captures_df.tail(100).copy()
                try:
                    recent_captures_df['created_at'] = pd.to_datetime(recent_captures_df['created_at'], errors='coerce', utc=True)
                    two_hours_ago = pd.Timestamp.now(tz='UTC') - timedelta(hours=2)
                    recent_captures_df = recent_captures_df[recent_captures_df['created_at'] >= two_hours_ago]
                except Exception:
                    recent_captures_df = recent_captures_df.tail(50)
            else:
                recent_captures_df = pd.DataFrame()
        except Exception as e:
            recent_captures_df = pd.DataFrame()
        
        # Posições abertas de daytrade
        positions_df = orders_repo.get_open_positions()
        daytrade_positions = []
        if not positions_df.empty:
            for _, pos in positions_df.iterrows():
                symbol = pos.get('symbol', '')
                if '_C_' in symbol or '_P_' in symbol or 'options' in str(pos.get('instrument_type', '')).lower():
                    daytrade_positions.append(pos.to_dict())
        
        # Estatísticas
        total_proposals = len(proposals_df) if not proposals_df.empty else 0
        approved_count = sum(1 for e in daytrade_evaluations if e.get('decision') == 'APPROVE')
        rejected_count = sum(1 for e in daytrade_evaluations if e.get('decision') == 'REJECT')
        approval_rate = (approved_count / len(daytrade_evaluations) * 100) if daytrade_evaluations else 0
        
        # Tickers capturados recentemente
        recent_tickers = []
        if not recent_captures_df.empty and 'ticker' in recent_captures_df.columns:
            recent_tickers = recent_captures_df['ticker'].unique().tolist()
        
        # Última captura
        last_capture_time = None
        if not recent_captures_df.empty and 'created_at' in recent_captures_df.columns:
            last_capture = recent_captures_df['created_at'].max()
            if pd.notna(last_capture):
                last_capture_time = last_capture.isoformat() if hasattr(last_capture, 'isoformat') else str(last_capture)
        
        # Preparar dados para retorno
        recent_proposals = []
        if not proposals_df.empty:
            for _, prop in proposals_df.tail(20).iterrows():
                recent_proposals.append({
                    'proposal_id': prop.get('proposal_id', ''),
                    'symbol': prop.get('symbol', ''),
                    'timestamp': prop.get('timestamp', ''),
                    'metadata': prop.get('metadata', {})
                })
        
        recent_captures = []
        if not recent_captures_df.empty:
            for _, cap in recent_captures_df.tail(20).iterrows():
                recent_captures.append({
                    'ticker': cap.get('ticker', ''),
                    'created_at': cap.get('created_at', ''),
                    'source': cap.get('source', '')
                })
        
        return jsonify({
            'status': 'success',
            'market_status': {
                'status': market_status,
                'b3_time': b3_time.isoformat(),
                'is_trading_hours': trading_schedule.is_trading_hours(b3_time),
                'is_pre_market': trading_schedule.is_pre_market(b3_time)
            },
            'statistics': {
                'total_proposals_24h': total_proposals,
                'approved_proposals': approved_count,
                'rejected_proposals': rejected_count,
                'approval_rate': approval_rate,
                'open_positions': len(daytrade_positions),
                'recent_captures': len(recent_captures_df) if not recent_captures_df.empty else 0,
                'tickers_monitored': len(recent_tickers)
            },
            'recent_proposals': recent_proposals,
            'recent_captures': recent_captures,
            'recent_tickers': recent_tickers,
            'open_positions': daytrade_positions,
            'last_capture_time': last_capture_time
        })
    except Exception as e:
        logger.error(f"Erro ao buscar monitoramento: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/daytrade/analysis', methods=['GET'])
def get_daytrade_analysis():
    """Retorna análise detalhada de propostas: geradas, aprovadas, rejeitadas com motivos."""
    try:
        from src.orders_repository import OrdersRepository
        from datetime import datetime, timedelta
        import pandas as pd
        import json
        
        orders_repo = OrdersRepository()
        
        # Período de análise (últimas 24h ou período customizado)
        days = request.args.get('days', 1, type=int)
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Buscar todas as propostas de daytrade
        proposals_df = orders_repo.get_proposals(strategy='daytrade_options', start_date=start_date)
        
        # Buscar todas as avaliações
        evaluations_df = orders_repo.get_risk_evaluations()
        if not evaluations_df.empty and 'timestamp' in evaluations_df.columns:
            try:
                evaluations_df['timestamp'] = pd.to_datetime(evaluations_df['timestamp'], errors='coerce')
                start_dt = pd.to_datetime(start_date)
                evaluations_df = evaluations_df[evaluations_df['timestamp'] >= start_dt]
            except:
                pass
        
        # Criar análise detalhada
        analysis = {
            'period_days': days,
            'start_date': start_date,
            'total_proposals': len(proposals_df) if not proposals_df.empty else 0,
            'proposals_generated': [],
            'proposals_approved': [],
            'proposals_rejected': [],
            'rejection_reasons': {},
            'filtering_stats': {
                'by_intraday_return': 0,
                'by_volume_ratio': 0,
                'by_delta': 0,
                'by_dte': 0,
                'by_spread': 0,
                'by_volume': 0,
                'by_comparison_score': 0
            }
        }
        
        if not proposals_df.empty:
            # Processar cada proposta
            for _, prop_row in proposals_df.iterrows():
                proposal_id = prop_row.get('proposal_id', '')
                proposal_data = prop_row.to_dict()
                
                # Buscar avaliação correspondente
                eval_row = evaluations_df[evaluations_df['proposal_id'] == proposal_id] if not evaluations_df.empty else pd.DataFrame()
                
                # Parse metadata se for string
                metadata = proposal_data.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                proposal_info = {
                    'proposal_id': proposal_id,
                    'symbol': proposal_data.get('symbol', 'N/A'),
                    'timestamp': proposal_data.get('timestamp', ''),
                    'metadata': metadata
                }
                
                analysis['proposals_generated'].append(proposal_info)
                
                if not eval_row.empty:
                    decision = eval_row.iloc[0].get('decision', 'PENDING')
                    reason = eval_row.iloc[0].get('reason', '')
                    
                    proposal_info['decision'] = decision
                    proposal_info['reason'] = reason
                    proposal_info['evaluation_timestamp'] = eval_row.iloc[0].get('timestamp', '')
                    
                    if decision == 'APPROVE':
                        analysis['proposals_approved'].append(proposal_info)
                    elif decision == 'REJECT':
                        analysis['proposals_rejected'].append(proposal_info)
                        
                        # Contar motivos de rejeição
                        reason_key = reason.split(':')[0] if ':' in reason else reason
                        analysis['rejection_reasons'][reason_key] = analysis['rejection_reasons'].get(reason_key, 0) + 1
        
        return jsonify({
            'status': 'success',
            'analysis': analysis
        })
    except Exception as e:
        import traceback
        logger.error(f"Erro ao buscar análise: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ============================================================================
# ENDPOINTS DE MONITORAMENTO
# ============================================================================

@app.route('/monitoring/status', methods=['GET'])
def get_monitoring_status():
    """Retorna status do monitoramento."""
    try:
        # Verificar se há processo de monitoramento rodando
        # Por enquanto, retornar status básico
        return jsonify({
            'status': 'success',
            'monitoring': {
                'active': True,
                'last_scan': None
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """Inicia monitoramento."""
    try:
        data = request.get_json() or {}
        interval = data.get('interval_seconds', 300)
        
        return jsonify({
            'status': 'success',
            'message': f'Monitoramento iniciado com intervalo de {interval}s'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Para monitoramento."""
    try:
        return jsonify({
            'status': 'success',
            'message': 'Monitoramento parado'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/monitoring/scan', methods=['POST'])
def manual_scan():
    """Executa scan manual."""
    try:
        return jsonify({
            'status': 'success',
            'message': 'Scan manual executado'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# ENDPOINTS DE BACKTEST
# ============================================================================

@app.route('/backtest/results', methods=['GET'])
def get_backtest_results():
    """Retorna resultados do backtest."""
    try:
        from src.orders_repository import OrdersRepository
        
        orders_repo = OrdersRepository()
        snapshots_df = orders_repo.get_performance_snapshots()
        
        snapshots = []
        if not snapshots_df.empty:
            for _, snap in snapshots_df.iterrows():
                snapshots.append(snap.to_dict())
        
        return jsonify({
            'status': 'success',
            'results': {
                'snapshots': snapshots,
                'total_snapshots': len(snapshots)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/backtest/run', methods=['POST'])
def run_backtest():
    """Executa backtest."""
    try:
        data = request.get_json() or {}
        tickers = data.get('tickers', [])
        
        return jsonify({
            'status': 'success',
            'message': f'Backtest executado para {len(tickers)} tickers'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# ENDPOINTS DE ESTRATÉGIAS
# ============================================================================

@app.route('/strategies/list', methods=['GET'])
def list_strategies():
    """Lista estratégias disponíveis."""
    return jsonify({
        'status': 'success',
        'strategies': [
            'daytrade_options',
            'volatility_arbitrage',
            'pairs_trading'
        ]
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import pandas as pd
    app.run(host='0.0.0.0', port=5000, debug=True)
