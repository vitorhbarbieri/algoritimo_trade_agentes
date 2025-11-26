"""
API REST para o sistema de trading com agentes.
ExpÃµe endpoints para executar backtests, ver mÃ©tricas e testar modelos.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import traceback

# Configurar imports - adicionar src ao path como pacote
src_path = Path(__file__).parent / 'src'
project_root = Path(__file__).parent

# Adicionar ao sys.path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Criar pacote src para imports relativos funcionarem
import types
if 'src' not in sys.modules:
    src_pkg = types.ModuleType('src')
    src_pkg.__path__ = [str(src_path)]
    sys.modules['src'] = src_pkg

# Agora podemos importar normalmente (os imports relativos funcionarÃ£o)
try:
    from src.pricing import BlackScholes
    from src.utils import StructuredLogger
    from src.market_data_api import fetch_real_market_data
    from src.data_loader import DataLoader
    from src.agents import TraderAgent, RiskAgent, PortfolioManager
    from src.execution import ExecutionSimulator
    from src.backtest import BacktestEngine
    from src.backtest_parallel import run_parallel_backtest_windows
except ImportError as e:
    # Fallback: tentar imports diretos se src nÃ£o funcionar
    print(f"Aviso: Import via src falhou ({e}), tentando imports diretos...")
    from pricing import BlackScholes
    from utils import StructuredLogger
    from market_data_api import fetch_real_market_data
    from data_loader import DataLoader
    from agents import TraderAgent, RiskAgent, PortfolioManager
    from execution import ExecutionSimulator
    from backtest import BacktestEngine
    from backtest_parallel import run_parallel_backtest_windows

app = Flask(__name__)
CORS(app)  # Permitir CORS para acesso do frontend

# Carregar configuraÃ§Ã£o
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# InstÃ¢ncias globais (serÃ£o inicializadas)
data_loader = None
logger = None
monitoring_service = None

# Importar MonitoringService
try:
    from src.monitoring_service import MonitoringService
except ImportError:
    try:
        from monitoring_service import MonitoringService
    except ImportError:
        MonitoringService = None


@app.route('/')
def index():
    """Endpoint raiz."""
    return jsonify({
        'status': 'online',
        'message': 'API do Sistema de Trading com Agentes',
        'version': '1.0.0',
        'endpoints': {
            '/': 'InformaÃ§Ãµes da API',
            '/health': 'Status de saÃºde',
            '/backtest/run': 'Executar backtest',
            '/backtest/parallel': 'Executar backtest paralelo',
            '/backtest/results': 'Ver resultados do Ãºltimo backtest',
            '/metrics': 'Ver mÃ©tricas',
            '/data/fetch': 'Buscar dados reais de mercado',
            '/strategies/list': 'Listar estratÃ©gias disponÃ­veis',
            '/test/pricing': 'Testar precificaÃ§Ã£o Black-Scholes'
        }
    })


@app.route('/health')
def health():
    """Verifica saÃºde da API."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/backtest/run', methods=['POST'])
def run_backtest():
    """Executa backtest simples."""
    try:
        data = request.get_json() or {}
        
        # ParÃ¢metros
        tickers = data.get('tickers', ['AAPL', 'MSFT'])
        start_date = data.get('start_date', (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'))
        end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        use_real_data = data.get('use_real_data', True)
        
        # Inicializar componentes
        global data_loader, logger
        if data_loader is None:
            data_loader = DataLoader()
        if logger is None:
            logger = StructuredLogger(log_dir='logs')
        
        # Carregar dados
        if use_real_data:
            try:
                spot_df, futures_df, options_df = data_loader.load_from_api(
                    tickers=tickers,
                    start_date=start_date,
                    end_date=end_date,
                    api_type='yfinance'
                )
                if spot_df.empty:
                    raise Exception("Nenhum dado real encontrado")
            except Exception as e:
                print(f"Erro ao buscar dados reais: {e}, usando sintÃ©ticos")
                spot_df = data_loader.generate_synthetic_spot(tickers, start_date, end_date)
                futures_df = data_loader.generate_synthetic_futures([], start_date, end_date)
                options_df = data_loader.generate_synthetic_options_chain(tickers[0], start_date, end_date)
        else:
            spot_df = data_loader.generate_synthetic_spot(tickers, start_date, end_date)
            futures_df = data_loader.generate_synthetic_futures([], start_date, end_date)
            options_df = data_loader.generate_synthetic_options_chain(tickers[0], start_date, end_date)
        
        # Setup backtest
        backtest_engine = BacktestEngine(CONFIG, logger)
        backtest_engine.load_data(spot_df, futures_df, options_df)
        
        # Resetar componentes (jÃ¡ sÃ£o criados no __init__, mas resetamos para garantir)
        backtest_engine.portfolio_manager = PortfolioManager(CONFIG.get('nav', 1000000))
        backtest_engine.risk_agent = RiskAgent(backtest_engine.portfolio_manager, CONFIG, logger)
        backtest_engine.execution_simulator = ExecutionSimulator(CONFIG, logger)
        backtest_engine.trader_agent = TraderAgent(CONFIG, logger)
        
        # Executar
        results = backtest_engine.run()
        
        # Obter resultados do backtest
        if results and 'metrics' in results:
            metrics = results['metrics']
        else:
            metrics = {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'volatility': 0.0,
                'win_rate': 0.0,
                'total_trades': 0
            }
        
        # Salvar resultados em arquivos CSV
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Salvar mÃ©tricas
        if results and 'metrics' in results:
            pd.DataFrame([results['metrics']]).to_csv(output_dir / 'metrics.csv', index=False)
        
        # Salvar snapshots
        if results and 'snapshots' in results:
            pd.DataFrame(results['snapshots']).to_csv(output_dir / 'portfolio_snapshots.csv', index=False)
        
        # Salvar fills
        if results and 'fills' in results:
            pd.DataFrame(results['fills']).to_csv(output_dir / 'fills.csv', index=False)
        
        # Salvar orders (se disponÃ­vel)
        if results and 'orders' in results and results['orders']:
            pd.DataFrame(results['orders']).to_csv(output_dir / 'orders.csv', index=False)
        
        # Extrair DataFrames dos resultados
        fills_df = backtest_engine.execution_simulator.get_fills()
        portfolio_snapshots = pd.DataFrame(results['snapshots']) if results and 'snapshots' in results else pd.DataFrame()
        orders_df = pd.DataFrame(results['fills']) if results and 'fills' in results else pd.DataFrame()

        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'summary': {
                'total_trades': len(orders_df) if not orders_df.empty else 0,
                'total_fills': len(fills_df) if not fills_df.empty else 0,
                'snapshots': len(portfolio_snapshots) if not portfolio_snapshots.empty else 0,
                'tickers': tickers,
                'period': f"{start_date} a {end_date}"
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/backtest/results', methods=['GET'])
def get_backtest_results():
    """ObtÃ©m resultados do Ãºltimo backtest."""
    try:
        results = {}
        
        # Carregar mÃ©tricas
        metrics_file = Path('output/metrics.csv')
        if metrics_file.exists():
            results['metrics'] = pd.read_csv(metrics_file).to_dict('records')[0]
        
        # Carregar snapshots
        snapshots_file = Path('output/portfolio_snapshots.csv')
        if snapshots_file.exists():
            df = pd.read_csv(snapshots_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            results['snapshots'] = df.tail(100).to_dict('records')  # Ãšltimos 100
        
        # Carregar ordens
        orders_file = Path('output/orders.csv')
        if orders_file.exists():
            df = pd.read_csv(orders_file)
            results['orders'] = df.tail(50).to_dict('records')  # Ãšltimas 50
        
        # Carregar fills
        fills_file = Path('output/fills.csv')
        if fills_file.exists():
            df = pd.read_csv(fills_file)
            results['fills'] = df.tail(50).to_dict('records')  # Ãšltimos 50
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/data/fetch', methods=['POST'])
def fetch_market_data():
    """Busca dados reais de mercado."""
    try:
        data = request.get_json() or {}
        
        tickers = data.get('tickers', ['AAPL', 'MSFT'])
        start_date = data.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        api_type = data.get('api_type', 'yfinance')
        
        market_data = fetch_real_market_data(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            api_type=api_type,
            use_fallback=True
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'spot_records': len(market_data['spot']),
                'futures_records': len(market_data['futures']),
                'options_records': len(market_data['options']),
                'tickers': tickers,
                'period': f"{start_date} a {end_date}"
            },
            'preview': {
                'spot': market_data['spot'].head(5).to_dict('records') if not market_data['spot'].empty else [],
                'options': market_data['options'].head(5).to_dict('records') if not market_data['options'].empty else []
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/strategies/list', methods=['GET'])
def list_strategies():
    """Lista estratÃ©gias disponÃ­veis."""
    return jsonify({
        'status': 'success',
        'strategies': [
        {
        'name': 'vol_arb',
        'description': 'Delta-hedged Volatility Arbitrage',
        'parameters': ['vol_arb_threshold', 'vol_arb_underlying']
        },
        {
        'name': 'pairs',
        'description': 'Pairs/Statistical Arbitrage',
        'parameters': ['pairs_ticker1', 'pairs_ticker2', 'pairs_zscore_threshold']
        },
        {
        'name': 'daytrade_options',
        'description': 'Daytrade Options - CALLs ATM/OTM com momentum intraday',
        'parameters': [
            'min_intraday_return', 'min_volume_ratio', 'delta_min', 'delta_max',
            'max_dte', 'max_spread_pct', 'min_option_volume', 'risk_per_trade',
            'take_profit_pct', 'stop_loss_pct'
        ]
        }
        ]
    })


@app.route('/test/pricing', methods=['POST'])
def test_pricing():
    """Testa precificaÃ§Ã£o Black-Scholes."""
    try:
        data = request.get_json() or {}
        
        S = float(data.get('spot_price', 150.0))
        K = float(data.get('strike', 150.0))
        T = float(data.get('time_to_expiry', 0.25))
        r = float(data.get('risk_free_rate', 0.05))
        sigma = float(data.get('volatility', 0.25))
        option_type = data.get('option_type', 'C')
        
        price = BlackScholes.price(S, K, T, r, sigma, option_type)
        greeks = BlackScholes.all_greeks(S, K, T, r, sigma, option_type)
        
        return jsonify({
            'status': 'success',
            'results': {
                'price': price,
                'greeks': greeks,
                'parameters': {
                    'spot': S,
                    'strike': K,
                    'time_to_expiry': T,
                    'risk_free_rate': r,
                    'volatility': sigma,
                    'option_type': option_type
                }
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """Inicia monitoramento contÃ­nuo do mercado."""
    try:
        global monitoring_service
        
        if MonitoringService is None:
            return jsonify({
                'status': 'error',
                'message': 'MonitoringService nÃ£o disponÃ­vel'
            }), 500
        
        if monitoring_service is None:
            monitoring_service = MonitoringService(CONFIG)
        
        data = request.get_json() or {}
        interval = data.get('interval_seconds', 300)  # 5 minutos padrÃ£o
        
        monitoring_service.start_monitoring(interval)
        
        return jsonify({
            'status': 'success',
            'message': f'Monitoramento iniciado (intervalo: {interval}s)',
            'status': monitoring_service.get_status()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Para monitoramento contÃ­nuo."""
    try:
        global monitoring_service
        
        if monitoring_service is None:
            return jsonify({
                'status': 'error',
                'message': 'Monitoramento nÃ£o estÃ¡ rodando'
            }), 400
        
        monitoring_service.stop_monitoring()
        
        return jsonify({
            'status': 'success',
            'message': 'Monitoramento parado'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/monitoring/status', methods=['GET'])
def get_monitoring_status():
    """Retorna status do monitoramento."""
    try:
        global monitoring_service
        
        if monitoring_service is None:
            return jsonify({
                'status': 'success',
                'monitoring': {
                    'is_running': False,
                    'message': 'Monitoramento nÃ£o iniciado',
                    'last_scan_time': None,
                    'opportunities_found': 0,
                    'proposals_generated': 0,
                    'recent_opportunities': [],
                    'recent_proposals': []
                }
            })
        
        status = monitoring_service.get_status()
        
        # Adicionar informaÃ§Ãµes sobre estratÃ©gias ativas
        status['strategies_active'] = {
            'vol_arb': CONFIG.get('enable_vol_arb', True),
            'pairs': CONFIG.get('enable_pairs', True),
            'spread_arb': True,  # Sempre ativo
            'momentum': True,  # Sempre ativo
            'mean_reversion': True  # Sempre ativo
        }
        
        status['tickers_monitored'] = len(CONFIG.get('monitored_tickers', []))
        status['crypto_monitored'] = len(CONFIG.get('monitored_crypto', [])) if CONFIG.get('enable_crypto', False) else 0
        
        return jsonify({
            'status': 'success',
            'monitoring': status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/monitoring/scan', methods=['POST'])
def manual_scan():
    """Executa scan manual do mercado."""
    try:
        global monitoring_service
        
        if MonitoringService is None:
            return jsonify({
                'status': 'error',
                'message': 'MonitoringService nÃ£o disponÃ­vel'
            }), 500
        
        if monitoring_service is None:
            monitoring_service = MonitoringService(CONFIG)
        
        result = monitoring_service.scan_market()
        
        return jsonify({
            'status': 'success',
            'scan_result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/agents/activity', methods=['GET'])
def get_agents_activity():
    """Retorna atividade dos agentes."""
    try:
        from pathlib import Path
        import json
        
        log_dir = Path('logs')
        if not log_dir.exists():
            return jsonify({
                'status': 'success',
                'activity': {
                    'trader_proposals': 0,
                    'risk_evaluations': 0,
                    'executions': 0,
                    'recent_activity': []
                }
            })
        
        logs = []
        for log_file in log_dir.glob("*.jsonl"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            logs.append(json.loads(line))
            except:
                continue
        
        logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        trader_proposals = [l for l in logs if l.get('event_type') == 'trader_proposal']
        risk_evaluations = [l for l in logs if l.get('event_type') == 'risk_evaluation']
        executions = [l for l in logs if l.get('event_type') == 'execution']
        
        return jsonify({
            'status': 'success',
            'activity': {
                'trader_proposals': len(trader_proposals),
                'risk_evaluations': len(risk_evaluations),
                'executions': len(executions),
                'recent_activity': logs[:20]  # Ãšltimas 20 atividades
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/metrics', methods=['GET'])
def get_metrics():
    """ObtÃ©m mÃ©tricas do Ãºltimo backtest."""
    try:
        metrics_file = Path('output/metrics.csv')
        if not metrics_file.exists():
            return jsonify({
                'status': 'error',
                'message': 'Nenhuma mÃ©trica encontrada. Execute um backtest primeiro.'
            }), 404
        
        metrics = pd.read_csv(metrics_file).to_dict('records')[0]
        
        return jsonify({
            'status': 'success',
            'metrics': metrics
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/agents/health', methods=['GET'])
def get_agents_health():
    """Verifica saúde de todos os agentes."""
    try:
        from src.agent_health_checker import AgentHealthChecker
    except ImportError:
        try:
            from agent_health_checker import AgentHealthChecker
        except ImportError:
            return jsonify({
                'status': 'error',
                'message': 'AgentHealthChecker não encontrado'
            }), 500
    
    try:
        # Inicializar logger se necessário
        global logger
        if logger is None:
            logger = StructuredLogger(log_dir='logs')
        
        checker = AgentHealthChecker(CONFIG, logger)
        health_summary = checker.get_health_summary()
        
        return jsonify({
            'status': 'success',
            **health_summary
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/agents/test', methods=['POST'])
def test_agents():
    """Executa testes dos agentes."""
    try:
        from src.agent_health_checker import AgentHealthChecker
    except ImportError:
        try:
            from agent_health_checker import AgentHealthChecker
        except ImportError:
            return jsonify({
                'status': 'error',
                'message': 'AgentHealthChecker não encontrado'
            }), 500
    
    try:
        # Inicializar logger se necessário
        global logger
        if logger is None:
            logger = StructuredLogger(log_dir='logs')
        
        checker = AgentHealthChecker(CONFIG, logger)
        health_results = checker.check_all_agents()
        
        # Executar teste de atividade também
        activity_results = checker.check_recent_activity(hours=24)
        
        return jsonify({
            'status': 'success',
            'health_check': health_results,
            'activity_check': activity_results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


if __name__ == '__main__':
    print("=" * 70)
    print("ðŸš€ API Server - Sistema de Trading com Agentes")
    print("=" * 70)
    print("\nEndpoints disponÃ­veis:")
    print("  GET  /                    - InformaÃ§Ãµes da API")
    print("  GET  /health              - Status de saÃºde")
    print("  POST /backtest/run        - Executar backtest")
    print("  GET  /backtest/results    - Ver resultados")
    print("  POST /data/fetch          - Buscar dados de mercado")
    print("  GET  /strategies/list     - Listar estratÃ©gias")
    print("  POST /test/pricing       - Testar precificaÃ§Ã£o")
    print("  GET  /metrics             - Ver mÃ©tricas")
    print("\n" + "=" * 70)
    print("ðŸŒ Servidor iniciando em http://localhost:5000")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)


