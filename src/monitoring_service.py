"""
Serviço de Monitoramento Contínuo - Escaneia mercado em tempo real.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import pandas as pd
import yfinance as yf

try:
    from .market_monitor import MarketMonitor
    from .data_loader import DataLoader
    from .market_data_api import create_market_data_api
    from .crypto_api import create_crypto_api
    from .agents import TraderAgent, RiskAgent, PortfolioManager
    from .utils import StructuredLogger
    from .notifications import UnifiedNotifier
    from .orders_repository import OrdersRepository
    from .trading_schedule import TradingSchedule
except ImportError:
    from market_monitor import MarketMonitor
    from data_loader import DataLoader
    from market_data_api import create_market_data_api
    from crypto_api import create_crypto_api
    from agents import TraderAgent, RiskAgent, PortfolioManager
    from utils import StructuredLogger
    from notifications import UnifiedNotifier
    from orders_repository import OrdersRepository
    from trading_schedule import TradingSchedule

logger = logging.getLogger(__name__)


class MonitoringService:
    """Serviço que monitora mercado continuamente."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = StructuredLogger(log_dir='logs')
        self.orders_repo = OrdersRepository()  # Repositório para salvar ordens
        self.market_monitor = MarketMonitor(config)
        self.portfolio_manager = PortfolioManager(config.get('nav', 1000000))
        self.trader_agent = TraderAgent(config, self.logger, orders_repo=self.orders_repo)
        self.risk_agent = RiskAgent(self.portfolio_manager, config, self.logger, orders_repo=self.orders_repo)
        self.data_loader = DataLoader()
        self.notifier = UnifiedNotifier(config, orders_repo=self.orders_repo)  # Sistema unificado de notificações
        self.trading_schedule = TradingSchedule()  # Horário de funcionamento B3
        self.is_running = False
        self.thread = None
        self.last_scan_time = None
        self.opportunities_found = []
        self.proposals_generated = []
        self.trading_started = False  # Flag para saber se já iniciou hoje
        self.last_status_notification = None  # Última notificação de status (2h)
        self.day_start_time = None  # Horário de início do dia
        self.eod_close_executed = False  # Flag para evitar fechamento duplicado
        self.last_eod_check = None  # Última verificação de EOD
        
        # APIs
        self.stock_api = create_market_data_api('yfinance')
        
        # API de Futuros
        try:
            from .futures_data_api import create_futures_api
            self.futures_api = create_futures_api()
        except ImportError:
            from futures_data_api import create_futures_api
            self.futures_api = create_futures_api()
        
        if config.get('enable_crypto', False):
            try:
                self.crypto_api = create_crypto_api(
                    'binance',
                    api_key=config.get('binance_api_key', ''),
                    api_secret=config.get('binance_api_secret', ''),
                    sandbox=config.get('binance_sandbox', True)
                )
            except:
                self.crypto_api = None
                logger.warning("Crypto API não disponível")
        else:
            self.crypto_api = None
    
    def _send_start_notification(self):
        """Envia notificação de início das atividades."""
        b3_time = self.trading_schedule.get_current_b3_time()
        
        # Buscar estatísticas do dia anterior (se houver)
        yesterday = (b3_time - timedelta(days=1)).strftime('%Y-%m-%d')
        summary_yesterday = None
        if self.orders_repo:
            try:
                summary_yesterday = self.orders_repo.get_daily_summary(yesterday)
            except:
                pass
        
        message = f"""
🚀 *MERCADO ABERTO - AGENTE INICIADO*

*Horário:* {b3_time.strftime('%d/%m/%Y %H:%M:%S')} (B3)
*Status:* {'Pré-Mercado' if self.trading_schedule.is_pre_market() else 'Mercado Aberto'}

O agente está agora monitorando o mercado e gerando propostas de daytrade.

*Horário de funcionamento:*
• Pré-mercado: 09:45 - 10:00
• Trading: 10:00 - 17:00
• Fechamento: 17:00

*Notificações programadas:*
• Status a cada 2 horas durante o pregão
• Relatórios de saúde às 11:00 e 15:00
• Resumo do dia ao fechamento

"""
        if summary_yesterday:
            message += f"""
*Resumo do dia anterior ({yesterday}):*
• Propostas geradas: {summary_yesterday.get('proposals_count', 0)}
• Propostas aprovadas: {summary_yesterday.get('approved_count', 0)}
• Propostas rejeitadas: {summary_yesterday.get('rejected_count', 0)}
"""
        
        # Enviar via Telegram
        telegram_channel = None
        for channel_name, channel in self.notifier.channels:
            if channel_name == 'telegram':
                telegram_channel = channel
                break
        
        self.notifier.send(message, title="🚀 Mercado Aberto", priority='high', message_type='market_open')
        
        self.day_start_time = b3_time
    
    def _send_end_notification(self):
        """Envia notificação de fim das atividades."""
        b3_time = self.trading_schedule.get_current_b3_time()
        
        # Buscar resumo do dia
        if self.orders_repo:
            summary = self.orders_repo.get_daily_summary(b3_time.strftime('%Y-%m-%d'))
        else:
            summary = {}
        
        runtime = ""
        if self.day_start_time:
            runtime_delta = b3_time - self.day_start_time
            hours = runtime_delta.seconds // 3600
            minutes = (runtime_delta.seconds % 3600) // 60
            runtime = f"{hours}h {minutes}min"
        
        # Buscar estatísticas detalhadas
        proposals_count = summary.get('total_proposals', 0)
        approved_count = summary.get('total_approved', 0)
        rejected_count = summary.get('total_rejected', 0)
        data_captures = 0
        
        if self.orders_repo:
            try:
                captures_df = self.orders_repo.get_market_data_captures(limit=1000)
                if not captures_df.empty:
                    today = b3_time.strftime('%Y-%m-%d')
                    captures_today = captures_df[captures_df['created_at'].str.startswith(today)]
                    data_captures = len(captures_today)
            except:
                pass
        
        message = f"""
🏁 *MERCADO FECHADO - RESUMO DO DIA*

*Data:* {b3_time.strftime('%d/%m/%Y')}
*Horário de fechamento:* {b3_time.strftime('%H:%M:%S')} (B3)
*Tempo de operação:* {runtime if runtime else 'N/A'}

*📊 ESTATÍSTICAS DO DIA:*
• Propostas geradas: {proposals_count}
• Propostas aprovadas: {approved_count}
• Propostas rejeitadas: {rejected_count}
• Taxa de aprovação: {(approved_count/proposals_count*100) if proposals_count > 0 else 0:.1f}%
• Capturas de dados: {data_captures}

*⏰ PRÓXIMAS ATIVIDADES:*
• Agente continuará monitorando dados mesmo com mercado fechado
• Próxima abertura: {self.trading_schedule.get_next_trading_open().strftime('%d/%m/%Y %H:%M') if self.trading_schedule.get_next_trading_open() else 'N/A'}

*✅ Agente permanece online e pronto para o próximo pregão.*
"""
        
        # Enviar via Telegram
        telegram_channel = None
        for channel_name, channel in self.notifier.channels:
            if channel_name == 'telegram':
                telegram_channel = channel
                break
        
        self.notifier.send(message, title="🏁 Mercado Fechado", priority='normal', message_type='market_close')
        self.trading_started = False
        self.day_start_time = None
    
    def _send_eod_notification(self, closed_count: int = 0):
        """Envia notificação de fechamento EOD e executa análise automática."""
        b3_time = self.trading_schedule.get_current_b3_time()
        date_str = b3_time.strftime('%Y-%m-%d')
        
        # Buscar estatísticas do dia
        if self.orders_repo:
            summary = self.orders_repo.get_daily_summary(date_str)
        else:
            summary = {}
        
        message = f"""
🏁 *FECHAMENTO EOD - {b3_time.strftime('%d/%m/%Y')}*

*Horário:* {b3_time.strftime('%H:%M:%S')} (B3)

*Posições Fechadas:*
• Total: {closed_count} posições

*Resumo do Dia:*
• Propostas geradas: {summary.get('total_proposals', 0)}
• Aprovadas: {summary.get('total_approved', 0)}
• Rejeitadas: {summary.get('total_rejected', 0)}
• Execuções: {summary.get('total_executions', 0)}

*Status:* Todas as posições de daytrade foram fechadas automaticamente.

🔄 Executando análise automática pós-EOD...
"""
        
        self.notifier.send(message, title="Fechamento EOD", priority='normal', message_type='eod')
        
        # Executar análise automática pós-EOD
        try:
            logger.info("🔍 Iniciando análise automática pós-EOD...")
            from .eod_analysis import EODAnalyzer
            
            analyzer = EODAnalyzer(self.config)
            analysis = analyzer.analyze_daily_proposals(date_str)
            
            # Formatar e enviar relatório por Telegram
            report = analyzer.format_telegram_report(analysis)
            
            # Enviar relatório completo (pode ser longo, dividir se necessário)
            self.notifier.send(report, title="📊 Análise EOD Completa", priority='normal')
            
            logger.info("✅ Análise EOD concluída e relatório enviado")
        except Exception as eod_analysis_err:
            logger.error(f"❌ ERRO ao executar análise EOD: {eod_analysis_err}")
            import traceback
            logger.error(traceback.format_exc())
            # Enviar notificação de erro
            self.notifier.send(
                f"⚠️ Erro ao executar análise EOD automática: {str(eod_analysis_err)}",
                title="Erro na Análise EOD",
                priority='high'
            )
    
    def _send_status_notification(self):
        """Envia notificação de status a cada 2 horas."""
        b3_time = self.trading_schedule.get_current_b3_time()
        
        # Buscar estatísticas do dia
        if self.orders_repo:
            summary = self.orders_repo.get_daily_summary(b3_time.strftime('%Y-%m-%d'))
            proposals = self.orders_repo.get_proposals(
                start_date=f"{b3_time.strftime('%Y-%m-%d')} 00:00:00",
                end_date=b3_time.isoformat()
            )
        else:
            summary = {}
            proposals = pd.DataFrame()
        
        # Estatísticas por estratégia
        strategy_stats = {}
        if not proposals.empty and 'strategy' in proposals.columns:
            strategy_stats = proposals.groupby('strategy').size().to_dict()
        
        runtime = ""
        if self.day_start_time:
            runtime_delta = b3_time - self.day_start_time
            hours = runtime_delta.seconds // 3600
            minutes = (runtime_delta.seconds % 3600) // 60
            runtime = f"{hours}h {minutes}min"
        
        message = f"""
📊 *STATUS DO AGENTE - ATUALIZAÇÃO*

*Horário:* {b3_time.strftime('%d/%m/%Y %H:%M:%S')} (B3)
*Tempo de operação:* {runtime if runtime else 'N/A'}

*Estatísticas do Dia:*
• Total de propostas: {summary.get('total_proposals', 0)}
• Aprovadas: {summary.get('total_approved', 0)}
• Rejeitadas: {summary.get('total_rejected', 0)}
• Modificadas: {summary.get('total_modified', 0)}
• Execuções: {summary.get('total_executions', 0)}

*Por Estratégia:*
"""
        for strategy, count in strategy_stats.items():
            message += f"• {strategy.replace('_', ' ').title()}: {count}\n"
        
        # Adicionar informações de captura de dados
        if self.orders_repo:
            try:
                # Buscar estatísticas de captura de dados do dia
                captures_today = self.orders_repo.get_market_data_captures(
                    start_date=f"{b3_time.strftime('%Y-%m-%d')} 00:00:00",
                    end_date=b3_time.isoformat()
                )
                
                if not captures_today.empty:
                    total_captures = len(captures_today)
                    unique_tickers = captures_today['ticker'].nunique() if 'ticker' in captures_today.columns else 0
                    
                    # Contar por tipo
                    spot_count = len(captures_today[captures_today.get('data_type', '') == 'spot']) if 'data_type' in captures_today.columns else 0
                    options_count = len(captures_today[captures_today.get('data_type', '') == 'options']) if 'data_type' in captures_today.columns else 0
                    futures_count = len(captures_today[captures_today.get('data_type', '') == 'futures']) if 'data_type' in captures_today.columns else 0
                    
                    # Última captura
                    if 'timestamp' in captures_today.columns:
                        last_capture = captures_today['timestamp'].max()
                        message += f"""
*📊 CAPTURA DE DADOS DE MERCADO:*
• Total de capturas hoje: {total_captures}
• Ativos únicos: {unique_tickers}
• Spot: {spot_count} | Opções: {options_count} | Futuros: {futures_count}
• Última captura: {last_capture if pd.notna(last_capture) else 'N/A'}
"""
                    else:
                        message += f"""
*📊 CAPTURA DE DADOS DE MERCADO:*
• Total de capturas hoje: {total_captures}
• Ativos únicos: {unique_tickers}
"""
                else:
                    message += f"""
*📊 CAPTURA DE DADOS DE MERCADO:*
• Nenhuma captura registrada hoje ainda
"""
            except Exception as e:
                logger.warning(f"Erro ao buscar estatísticas de captura: {e}")
                message += f"""
*📊 CAPTURA DE DADOS DE MERCADO:*
• Erro ao buscar estatísticas: {str(e)[:50]}
"""
        
        message += f"\n*Próxima atualização:* Em 2 horas"
        
        self.notifier.send(message, title="📊 Status do Agente", priority='normal', message_type='status')
        self.last_status_notification = b3_time
    
    def scan_market(self) -> Dict:
        """Escaneia mercado uma vez."""
        opportunities = []
        proposals = []
        
        # Verificar horário B3
        b3_time = self.trading_schedule.get_current_b3_time()
        
        # Verificar se deve iniciar trading
        if not self.trading_started and self.trading_schedule.should_start_trading():
            self.trading_started = True
            self._send_start_notification()
        
        # Verificar se deve parar trading
        if self.trading_started and self.trading_schedule.should_stop_trading():
            self._send_end_notification()
            return {
                'timestamp': b3_time.isoformat(),
                'status': 'MARKET_CLOSED',
                'opportunities': 0,
                'proposals': 0
            }
        
        # Validação: não permitir propostas após 15:00 (para garantir fechamento EOD)
        current_hour = b3_time.hour
        if current_hour >= 15:
            logger.info(f"Horário limite atingido ({b3_time.strftime('%H:%M')}) - Não gerando novas propostas (fechamento EOD às 17:00)")
            return {
                'timestamp': b3_time.isoformat(),
                'status': 'LIMIT_HOUR',
                'message': 'Horário limite para novas propostas (15:00)',
                'data_captured': 0,
                'proposals': 0,
                'opportunities': 0
            }
        
        # Verificar se está no horário de trading (inclui pré-mercado)
        trading_status = self.trading_schedule.get_trading_status()
        
        # IMPORTANTE: Mesmo quando mercado está fechado, devemos capturar dados
        # para análise posterior e rastreabilidade. Apenas não geramos propostas.
        # Se for fim de semana ou feriado, ainda assim tentamos capturar dados históricos.
        
        # Se for dia útil mas fora do horário, ainda capturamos dados (pós-mercado)
        # Se não for dia útil, ainda tentamos capturar dados históricos
        should_capture_data = True  # Sempre tentar capturar dados
        
        # Só gerar propostas durante horário de trading
        should_generate_proposals = trading_status in ['PRE_MARKET', 'TRADING', 'POST_MARKET']
        
        # Enviar notificação de status a cada 2 horas (apenas durante trading)
        if trading_status == 'TRADING' and (self.last_status_notification is None or \
           (b3_time - self.last_status_notification).total_seconds() >= 7200):  # 2 horas
            self._send_status_notification()
        
        try:
            # Buscar dados de ações (INTRADAY do dia atual)
            # Filtrar apenas tickers brasileiros (.SA)
            all_tickers = self.config.get('monitored_tickers', [])
            tickers = [t for t in all_tickers if '.SA' in str(t)]
            
            # Coleta de futuros será feita dentro do loop de dados
            if not tickers:
                logger.warning("Nenhum ticker configurado para monitoramento")
                return {
                    'timestamp': b3_time.isoformat(),
                    'status': 'NO_TICKERS',
                    'opportunities': 0,
                    'proposals': 0
                }
            
            # Buscar dados INTRADAY do dia atual (não histórico!)
            today = datetime.now().strftime('%Y-%m-%d')
            market_data = {'spot': {}, 'options': {}, 'futures': {}}
            
            # 1. COLETAR DADOS DE FUTUROS PRIMEIRO
            futures = self.config.get('monitored_futures', [])
            if futures and hasattr(self, 'futures_api'):
                logger.info(f"Coletando dados de {len(futures)} contratos futuros...")
                try:
                    futures_data = self.futures_api.get_all_futures_data(futures)
                    if futures_data:
                        market_data['futures'] = futures_data
                        logger.info(f"Dados coletados para {len(futures_data)} futuros: {list(futures_data.keys())}")
                except Exception as e:
                    logger.warning(f"Erro ao coletar dados de futuros: {e}")
            
            # 1. COLETAR DADOS DE FUTUROS
            futures = self.config.get('monitored_futures', [])
            if futures and hasattr(self, 'futures_api'):
                logger.info(f"Coletando dados de {len(futures)} contratos futuros...")
                try:
                    futures_data = self.futures_api.get_all_futures_data(futures)
                    if futures_data:
                        market_data['futures'] = futures_data
                        logger.info(f"Dados coletados para {len(futures_data)} futuros: {list(futures_data.keys())}")
                except Exception as e:
                    logger.warning(f"Erro ao coletar dados de futuros: {e}")
            
            logger.info(f"Buscando dados intraday para {len(tickers)} tickers...")
            
            # Importar yfinance uma vez
            try:
                import yfinance as yf
            except ImportError:
                logger.error("yfinance não instalado! Execute: pip install yfinance")
                raise
            
            # Buscar dados spot INTRADAY para cada ticker
            # Processar todos os tickers configurados (agora 62 ativos)
            tickers_to_process = tickers  # Processar todos os tickers brasileiros
            successful_tickers = 0
            failed_tickers = []
            
            logger.info(f"Processando {len(tickers_to_process)} tickers...")
            
            for ticker in tickers_to_process:
                try:
                    ticker_yf = ticker
                    
                    # Para ações brasileiras (.SA), usar info() para dados em tempo real
                    # Para outras ações, tentar intraday primeiro
                    is_brazilian = '.SA' in ticker
                    
                    current_price = None
                    open_price = None
                    high_price = None
                    low_price = None
                    volume_today = 0
                    
                    if is_brazilian:
                        # Para ações brasileiras, buscar dados INTRADAY do dia atual
                        stock = yf.Ticker(ticker_yf)
                        hist_intraday = None
                        today = datetime.now().date()
                        is_market_open = trading_status in ['PRE_MARKET', 'TRADING', 'POST_MARKET']
                        
                        # Tentar buscar dados intraday do dia atual (5m, 15m, 1h)
                        for interval in ['5m', '15m', '1h']:
                            try:
                                hist_intraday = stock.history(period='1d', interval=interval, timeout=10)
                                if hist_intraday is not None and not hist_intraday.empty:
                                    # Converter índice para datetime se necessário
                                    hist_intraday.index = pd.to_datetime(hist_intraday.index)
                                    
                                    # Filtrar apenas dados de HOJE
                                    hist_today = hist_intraday[hist_intraday.index.date == today]
                                    
                                    if not hist_today.empty:
                                        # Usar último candle disponível de HOJE (mais recente)
                                        latest = hist_today.iloc[-1]
                                        current_price = float(latest['Close'])
                                        open_price = float(hist_today.iloc[0]['Open'])
                                        high_price = float(hist_today['High'].max())
                                        low_price = float(hist_today['Low'].min())
                                        volume_today = int(hist_today['Volume'].sum())
                                        logger.info(f"{ticker}: ✅ Dados intraday de HOJE capturados ({interval}, {len(hist_today)} candles) - Preço: {current_price:.2f}")
                                        break
                                    elif is_market_open:
                                        # Se mercado está aberto mas não há dados de hoje, pode ser delay da API
                                        # Usar último candle disponível (pode ser do início do pregão)
                                        latest = hist_intraday.iloc[-1]
                                        candle_date = hist_intraday.index[-1].date()
                                        current_price = float(latest['Close'])
                                        open_price = float(hist_intraday.iloc[0]['Open'])
                                        high_price = float(hist_intraday['High'].max())
                                        low_price = float(hist_intraday['Low'].min())
                                        volume_today = int(hist_intraday['Volume'].sum())
                                        logger.warning(f"{ticker}: ⚠️ Mercado aberto mas último candle é de {candle_date} (pode ser delay da API) - Preço: {current_price:.2f}")
                                        break
                            except Exception as e:
                                logger.debug(f"Erro ao buscar intraday {interval} para {ticker}: {e}")
                                continue
                        
                        # Se não conseguiu intraday, tentar info() para dados em tempo real
                        if current_price is None:
                            try:
                                info = stock.info
                                # Pegar preço atual do info (mais atualizado)
                                current_price = info.get('regularMarketPrice') or info.get('currentPrice')
                                if current_price:
                                    open_price = info.get('open') or info.get('regularMarketOpen') or current_price
                                    high_price = info.get('dayHigh') or info.get('regularMarketDayHigh') or current_price
                                    low_price = info.get('dayLow') or info.get('regularMarketDayLow') or current_price
                                    volume_today = info.get('volume') or info.get('regularMarketVolume') or 0
                                    logger.info(f"{ticker}: ✅ Dados obtidos via info() - Preço atual: {current_price:.2f}")
                            except Exception as e:
                                logger.debug(f"Erro ao buscar info para {ticker}: {e}")
                                # Último fallback: dados diários (apenas se mercado fechado)
                                if not is_market_open:
                                    try:
                                        hist_daily = stock.history(period='2d', interval='1d', timeout=10)
                                        if hist_daily is not None and not hist_daily.empty:
                                            latest = hist_daily.iloc[-1]
                                            current_price = float(latest['Close'])
                                            open_price = float(hist_daily.iloc[0]['Open']) if len(hist_daily) > 1 else float(latest['Open'])
                                            high_price = float(latest['High'])
                                            low_price = float(latest['Low'])
                                            volume_today = int(hist_daily['Volume'].sum()) if 'Volume' in hist_daily.columns else 0
                                            logger.info(f"{ticker}: ℹ️ Mercado fechado - usando último preço de fechamento: {current_price:.2f}")
                                    except:
                                        pass
                                else:
                                    logger.warning(f"{ticker}: ⚠️ Mercado aberto mas não foi possível obter dados atualizados")
                    else:
                        # Para ações não-brasileiras, buscar dados INTRADAY do dia atual
                        stock = yf.Ticker(ticker_yf)
                        hist_intraday = None
                        today = datetime.now().date()
                        is_market_open = trading_status in ['PRE_MARKET', 'TRADING', 'POST_MARKET']
                        
                        # Tentar buscar dados intraday do dia atual (5m, 15m, 1h)
                        for interval in ['5m', '15m', '1h']:
                            try:
                                hist_intraday = stock.history(period='1d', interval=interval, timeout=10)
                                if hist_intraday is not None and not hist_intraday.empty:
                                    # Converter índice para datetime se necessário
                                    hist_intraday.index = pd.to_datetime(hist_intraday.index)
                                    
                                    # Filtrar apenas dados de HOJE
                                    hist_today = hist_intraday[hist_intraday.index.date == today]
                                    
                                    if not hist_today.empty:
                                        # Usar último candle disponível de HOJE (mais recente)
                                        latest = hist_today.iloc[-1]
                                        current_price = float(latest['Close'])
                                        open_price = float(hist_today.iloc[0]['Open'])
                                        high_price = float(hist_today['High'].max())
                                        low_price = float(hist_today['Low'].min())
                                        volume_today = int(hist_today['Volume'].sum())
                                        logger.info(f"{ticker}: ✅ Dados intraday de HOJE capturados ({interval}, {len(hist_today)} candles) - Preço: {current_price:.2f}")
                                        break
                                    elif is_market_open:
                                        # Se mercado está aberto mas não há dados de hoje, pode ser delay da API
                                        latest = hist_intraday.iloc[-1]
                                        candle_date = hist_intraday.index[-1].date()
                                        current_price = float(latest['Close'])
                                        open_price = float(hist_intraday.iloc[0]['Open'])
                                        high_price = float(hist_intraday['High'].max())
                                        low_price = float(hist_intraday['Low'].min())
                                        volume_today = int(hist_intraday['Volume'].sum())
                                        logger.warning(f"{ticker}: ⚠️ Mercado aberto mas último candle é de {candle_date} (pode ser delay da API) - Preço: {current_price:.2f}")
                                        break
                            except Exception as e:
                                logger.debug(f"Erro ao buscar intraday {interval} para {ticker}: {e}")
                                continue
                        
                        # Se não conseguiu intraday de hoje, tentar dados diários como fallback
                        if current_price is None:
                            if not is_market_open:
                                # Se mercado fechado, usar dados diários é aceitável
                                try:
                                    hist_daily = stock.history(period='2d', interval='1d', timeout=10)
                                    if hist_daily is not None and not hist_daily.empty:
                                        latest = hist_daily.iloc[-1]
                                        current_price = float(latest['Close'])
                                        open_price = float(hist_daily.iloc[0]['Open']) if len(hist_daily) > 1 else float(latest['Open'])
                                        high_price = float(latest['High'])
                                        low_price = float(latest['Low'])
                                        volume_today = int(hist_daily['Volume'].sum()) if 'Volume' in hist_daily.columns else 0
                                        logger.info(f"{ticker}: ℹ️ Mercado fechado - usando último preço de fechamento: {current_price:.2f}")
                                except Exception as e:
                                    logger.debug(f"Erro ao buscar dados diários para {ticker}: {e}")
                            else:
                                logger.warning(f"{ticker}: ⚠️ Mercado aberto mas não foi possível obter dados atualizados")
                        
                        if current_price is None:
                            logger.warning(f"Nenhum dado encontrado para {ticker}")
                            failed_tickers.append(ticker)
                            continue
                    
                    if current_price is None:
                        logger.warning(f"Não foi possível obter preço atual para {ticker}")
                        failed_tickers.append(ticker)
                        continue
                    
                    market_data['spot'][ticker] = {
                        'open': open_price,
                        'close': current_price,
                        'last': current_price,  # Preço atual
                        'high': high_price,
                        'low': low_price,
                        'volume': volume_today,
                        'adv': 0  # Será calculado depois se necessário
                    }
                    
                    logger.debug(f"{ticker}: Preço atual={current_price:.2f}, Abertura={open_price:.2f}, Volume={volume_today:,}")
                    
                    successful_tickers += 1
                    
                    # Buscar opções para este ticker (coletar para TODOS os 62 ativos)
                    # Throttle para não sobrecarregar API (0.1s entre requisições)
                    try:
                        import time
                        time.sleep(0.1)  # Pequeno delay para não sobrecarregar API
                        
                        options_df = self.stock_api.fetch_options_chain(ticker, today, today)
                        if not options_df.empty:
                            if ticker not in market_data['options']:
                                market_data['options'][ticker] = []
                            # Converter DataFrame para lista de dicts
                            options_list = options_df.to_dict('records')
                            market_data['options'][ticker].extend(options_list)
                            logger.debug(f"Opções encontradas para {ticker}: {len(options_list)} contratos")
                        else:
                            logger.debug(f"Nenhuma opção disponível para {ticker} (pode ser normal)")
                    except Exception as opt_err:
                        logger.debug(f"Erro ao buscar opções para {ticker}: {opt_err}")
                        # Continuar mesmo sem opções - pode ter propostas baseadas apenas em momentum
                    
                except Exception as e:
                    logger.warning(f"Erro ao buscar dados para {ticker}: {e}")
                    failed_tickers.append(ticker)
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue
            
            # Log resumo
            if failed_tickers:
                logger.warning(f"Tickers com falha ({len(failed_tickers)}): {failed_tickers[:5]}")
            
            logger.info(f"Dados coletados: {successful_tickers}/{len(tickers_to_process)} tickers com dados spot")
            logger.info(f"Opções disponíveis para: {len(market_data.get('options', {}))} tickers")
            if market_data.get('futures'):
                logger.info(f"Futuros coletados: {len(market_data.get('futures', {}))} contratos")
            
            # CRÍTICO: Salvar dados capturados SEMPRE, mesmo quando mercado fechado
            # Isso garante rastreabilidade e análise posterior
            if self.orders_repo and market_data.get('spot'):
                saved_count = 0
                for ticker, spot_info in market_data['spot'].items():
                    try:
                        options_list = market_data.get('options', {}).get(ticker, [])
                        self.orders_repo.save_market_data_capture(
                            ticker=ticker,
                            data_type='spot',
                            spot_data=spot_info,
                            options_data=options_list if options_list else None,
                            raw_data={'timestamp': b3_time.isoformat(), 'trading_status': trading_status},
                            source='real'
                        )
                        saved_count += 1
                    except Exception as save_err:
                        logger.error(f"Erro ao salvar dados de mercado para {ticker}: {save_err}")
                        import traceback
                        logger.debug(traceback.format_exc())
                
                # Salvar dados de futuros
                if market_data.get('futures'):
                    for future_symbol, future_data in market_data['futures'].items():
                        try:
                            self.orders_repo.save_market_data_capture(
                                ticker=future_symbol,
                                data_type='futures',
                                spot_data=future_data,
                                options_data=None,
                                raw_data={'timestamp': b3_time.isoformat(), 'trading_status': trading_status},
                                source='real'
                            )
                            saved_count += 1
                        except Exception as save_err:
                            logger.error(f"Erro ao salvar dados de futuro {future_symbol}: {save_err}")
                
                if saved_count > 0:
                    logger.info(f"Dados salvos no banco: {saved_count} instrumentos (spot + futuros)")
            
            # CRÍTICO: Gerar propostas APENAS durante horário de trading
            # Mas sempre capturamos dados para rastreabilidade
            proposals = []
            if should_generate_proposals:
                # Gerar propostas do TraderAgent (inclui DayTradeOptionsStrategy)
                if market_data.get('spot'):
                    proposals = self.trader_agent.generate_proposals(
                        pd.to_datetime(datetime.now()),
                        market_data
                    )
                
                # Gerar propostas de futuros se disponível
                if market_data.get('futures'):
                    try:
                        from .futures_strategy import FuturesDayTradeStrategy
                        futures_strategy = FuturesDayTradeStrategy(self.config)
                        futures_proposals = futures_strategy.generate_proposals(
                            pd.to_datetime(datetime.now()),
                            market_data['futures']
                        )
                        proposals.extend(futures_proposals)
                        if futures_proposals:
                            logger.info(f"Propostas de futuros geradas: {len(futures_proposals)}")
                    except ImportError:
                        try:
                            from futures_strategy import FuturesDayTradeStrategy
                            futures_strategy = FuturesDayTradeStrategy(self.config)
                            futures_proposals = futures_strategy.generate_proposals(
                                pd.to_datetime(datetime.now()),
                                market_data['futures']
                            )
                            proposals.extend(futures_proposals)
                            if futures_proposals:
                                logger.info(f"Propostas de futuros geradas: {len(futures_proposals)}")
                        except Exception as e:
                            logger.warning(f"Erro ao gerar propostas de futuros: {e}")
                    except Exception as e:
                        logger.warning(f"Erro ao gerar propostas de futuros: {e}")
                
                logger.info(f"Total de propostas geradas: {len(proposals)}")
                
                # Escanear oportunidades do MarketMonitor (para outras estratégias)
                # FILTRO: Apenas oportunidades de ativos brasileiros
                opportunities = self.market_monitor.scan_all_opportunities(market_data)
                
                # Filtrar oportunidades apenas de ativos brasileiros
                brazilian_opportunities = [
                    opp for opp in opportunities 
                    if '.SA' in str(opp.get('symbol', '')) or 
                       '.SA' in str(opp.get('ticker', '')) or
                       str(opp.get('symbol', '')).endswith('.SA') or
                       str(opp.get('ticker', '')).endswith('.SA')
                ]
                
                # Enviar notificações se encontrar oportunidades brasileiras
                if brazilian_opportunities:
                    for opp in brazilian_opportunities[:5]:
                        self.notifier.notify_opportunity(opp)
                
                # FILTRO CRÍTICO: Filtrar propostas apenas de ativos brasileiros
                brazilian_proposals = []
                for prop in proposals:
                    symbol = prop.symbol if hasattr(prop, 'symbol') else str(prop.get('symbol', ''))
                    underlying = prop.metadata.get('underlying', '') if hasattr(prop, 'metadata') and prop.metadata else ''
                    
                    # Verificar se é brasileiro
                    is_brazilian = (
                        '.SA' in str(symbol) or 
                        str(symbol).endswith('.SA') or
                        '.SA' in str(underlying) or
                        str(underlying).endswith('.SA')
                    )
                    
                    # Apenas estratégias de daytrade e futuros (que já são brasileiros)
                    if prop.strategy in ['daytrade_options', 'futures_daytrade']:
                        is_brazilian = True  # Essas estratégias já são apenas brasileiras
                    
                    if is_brazilian:
                        brazilian_proposals.append(prop)
                    else:
                        logger.warning(f"Proposta filtrada (não brasileira): {symbol} - {prop.strategy}")
                
                proposals = brazilian_proposals
                
                # Avaliar propostas com RiskAgent antes de enviar
                if proposals:
                    # Notificar sobre propostas de daytrade (alta prioridade)
                    daytrade_proposals = [p for p in proposals if p.strategy == 'daytrade_options']
                    if daytrade_proposals:
                        logger.info(f"Propostas de daytrade encontradas: {len(daytrade_proposals)}")
                        
                        # Filtrar propostas com razão ganho/perda aceitável (> 0.25)
                        propostas_filtradas = []
                        for proposal in daytrade_proposals:
                            metadata = proposal.metadata or {}
                            gain_value = metadata.get('gain_value', 0)
                            loss_value = abs(metadata.get('loss_value', 1))
                            
                            if loss_value > 0:
                                gain_loss_ratio = gain_value / loss_value
                                # Apenas propostas com razão ganho/perda > 0.25
                                if gain_loss_ratio > 0.25:
                                    propostas_filtradas.append(proposal)
                        
                        logger.info(f"Propostas após filtro de razão ganho/perda: {len(propostas_filtradas)}")
                        
                        # Avaliar TODAS as propostas com RiskAgent (não apenas as aprovadas)
                        # IMPORTANTE: Avaliar todas para salvar avaliações no banco
                        approved_count = 0
                        rejected_count = 0
                        modified_count = 0
                        
                        # Limitar a 50 propostas por scan para não sobrecarregar
                        propostas_para_avaliar = propostas_filtradas[:50]
                        
                        logger.info(f"Avaliando {len(propostas_para_avaliar)} propostas com RiskAgent...")
                        
                        for proposal in propostas_para_avaliar:
                            try:
                                # Avaliar proposta com RiskAgent (sempre salva avaliação)
                                decision, modified_proposal, reason = self.risk_agent.evaluate_proposal(
                                    proposal, market_data
                                )
                                
                                # Contar decisões
                                if decision == 'APPROVE':
                                    approved_count += 1
                                    
                                    # Atualizar status para 'enviada' (aprovada pelo RiskAgent e enviada ao Telegram)
                                    try:
                                        self.orders_repo.update_proposal_status(proposal.proposal_id, 'enviada')
                                    except Exception as e:
                                        logger.error(f"Erro ao atualizar status da proposta {proposal.proposal_id}: {e}")
                                    
                                    # Preparar dados da proposta para Telegram
                                    proposal_data = {
                                        'proposal_id': proposal.proposal_id,
                                        'symbol': proposal.symbol,
                                        'side': proposal.side,
                                        'quantity': proposal.quantity,
                                        'price': proposal.price,
                                        'metadata': proposal.metadata
                                    }
                                    
                                    # Enviar via Telegram com botões de aprovação
                                    telegram_channel = None
                                    for channel_name, channel in self.notifier.channels:
                                        if channel_name == 'telegram' and hasattr(channel, 'send_proposal_with_approval'):
                                            telegram_channel = channel
                                            break
                                    
                                    if telegram_channel:
                                        telegram_channel.send_proposal_with_approval(proposal_data)
                                    else:
                                        logger.warning("Canal Telegram não disponível")
                                elif decision == 'REJECT':
                                    rejected_count += 1
                                    logger.debug(f"Proposta {proposal.proposal_id} rejeitada: {reason}")
                                elif decision == 'MODIFY':
                                    modified_count += 1
                                    logger.info(f"Proposta {proposal.proposal_id} modificada: {reason}")
                                    
                            except Exception as e:
                                logger.error(f"Erro ao avaliar proposta {proposal.proposal_id}: {e}")
                                import traceback
                                logger.error(traceback.format_exc())
                        
                        logger.info(f"Resultado da avaliação: {approved_count} aprovadas, {rejected_count} rejeitadas, {modified_count} modificadas")
                        
                        logger.info(f"Propostas aprovadas e enviadas: {approved_count}")
            else:
                opportunities = []
                if successful_tickers == 0:
                    logger.warning(f"Nenhum dado spot coletado após processar {len(tickers_to_process)} tickers")
                    logger.warning("Possíveis causas: mercado fechado, problemas com API, ou tickers inválidos")
                else:
                    logger.info(f"Dados coletados ({successful_tickers} tickers) mas sem propostas geradas (mercado fechado ou sem oportunidades)")
            
            # Buscar dados de cripto (se habilitado)
            if self.crypto_api:
                crypto_tickers = self.config.get('monitored_crypto', [])
                if crypto_tickers:
                    # Implementar escaneamento de cripto
                    pass
        
        except Exception as e:
            logger.error(f"Erro ao escanear mercado: {e}")
            # Notificar erro
            self.notifier.notify_error(
                error_type='Market Scan Error',
                error_message=str(e),
                details={'timestamp': self.trading_schedule.get_current_b3_time().isoformat()}
            )
        
        self.last_scan_time = self.trading_schedule.get_current_b3_time()
        self.opportunities_found = opportunities[:10] if 'opportunities' in locals() else []
        self.proposals_generated = proposals
        
        # Log detalhado para debug
        logger.info(f"Scan completo - Propostas: {len(proposals)}, Oportunidades: {len(opportunities) if 'opportunities' in locals() else 0}")
        if proposals:
            for p in proposals[:3]:
                logger.info(f"  Proposta: {p.strategy} - {p.symbol} - Qty: {p.quantity}")
        
        # Incluir informações sobre captura de dados no retorno
        data_captured = successful_tickers if 'successful_tickers' in locals() else 0
        return {
            'timestamp': self.last_scan_time.isoformat(),
            'status': trading_status,
            'opportunities': len(opportunities) if 'opportunities' in locals() else 0,
            'proposals': len(proposals),
            'opportunities_list': opportunities[:5] if 'opportunities' in locals() else [],
            'proposals_list': [{'id': p.proposal_id, 'strategy': p.strategy, 'symbol': p.symbol} for p in proposals[:5]],
            'data_captured': data_captured,
            'should_generate_proposals': should_generate_proposals if 'should_generate_proposals' in locals() else False
        }
    
    def start_monitoring(self, interval_seconds: int = 300):
        """Inicia monitoramento contínuo respeitando horário B3."""
        if self.is_running:
            logger.warning("Monitoramento já está rodando")
            return
        
        self.is_running = True
        
        def monitor_loop():
            while self.is_running:
                try:
                    b3_time = self.trading_schedule.get_current_b3_time()
                    status = self.trading_schedule.get_trading_status()
                    
                    # CRÍTICO: Sempre executar scan, mesmo quando mercado fechado
                    # Isso garante captura de dados históricos e rastreabilidade
                    # Apenas não geramos propostas quando fechado
                    
                    logger.info(f"[{b3_time.strftime('%H:%M:%S')}] Status: {status} - Executando scan...")
                    
                    # CRÍTICO: Fechamento EOD às 17:00
                    current_hour = b3_time.hour
                    current_minute = b3_time.minute
                    current_date = b3_time.date()
                    
                    # Verificar se já passou das 17:00 e ainda não fechamos as posições hoje
                    # Usar uma janela de tempo (17:00 até 18:00) para garantir execução
                    if current_hour >= 17 and current_hour < 18:
                        # Verificar se já fechamos hoje (comparar data)
                        last_eod_date = self.last_eod_check.date() if self.last_eod_check else None
                        
                        if last_eod_date != current_date:
                            logger.info(f"🔄 Executando fechamento EOD automático às {b3_time.strftime('%H:%M')}...")
                            try:
                                closed_count = self.orders_repo.close_all_daytrade_positions()
                                if closed_count > 0:
                                    logger.info(f"✅ Fechamento EOD: {closed_count} posições fechadas")
                                    self._send_eod_notification(closed_count)
                                else:
                                    logger.info("ℹ️  Nenhuma posição aberta para fechar")
                                    # Mesmo sem posições, executar análise se houver propostas
                                    if self.orders_repo:
                                        from datetime import datetime
                                        date_str = b3_time.strftime('%Y-%m-%d')
                                        proposals = self.orders_repo.get_proposals(
                                            start_date=f'{date_str} 00:00:00',
                                            end_date=f'{date_str} 23:59:59'
                                        )
                                        if not proposals.empty:
                                            logger.info("🔄 Executando análise EOD mesmo sem posições abertas...")
                                            try:
                                                from .eod_analysis import EODAnalyzer
                                                analyzer = EODAnalyzer(self.config)
                                                analysis = analyzer.analyze_daily_proposals(date_str)
                                                report = analyzer.format_telegram_report(analysis)
                                                self.notifier.send(report, title="📊 Análise EOD Completa", priority='normal')
                                            except Exception as e:
                                                logger.error(f"Erro na análise EOD: {e}")
                                
                                self.eod_close_executed = True
                                self.last_eod_check = b3_time
                            except Exception as eod_err:
                                logger.error(f"❌ ERRO ao fechar posições EOD: {eod_err}")
                                import traceback
                                logger.error(traceback.format_exc())
                    
                    # Resetar flag EOD após meia-noite (novo dia)
                    if current_hour == 0 and current_minute < 5:
                        if self.last_eod_check and (current_date > self.last_eod_check.date()):
                            self.eod_close_executed = False
                            logger.info("🔄 Flag EOD resetada para novo dia")
                    
                    # Escanear mercado (SEMPRE, mesmo fechado)
                    try:
                        result = self.scan_market()
                        status_msg = result.get('status', 'UNKNOWN')
                        data_captured = result.get('data_captured', 0)
                        proposals = result.get('proposals', 0)
                        opportunities = result.get('opportunities', 0)
                        
                        logger.info(f"Scan completo ({status_msg}): {data_captured} dados capturados, {opportunities} oportunidades, {proposals} propostas")
                        
                        # Log detalhado se houver dados capturados
                        if data_captured > 0:
                            logger.info(f"✅ Dados salvos no banco: {data_captured} tickers")
                        else:
                            logger.warning(f"⚠️  Nenhum dado capturado neste scan")
                            
                    except Exception as scan_err:
                        logger.error(f"❌ ERRO ao executar scan: {scan_err}")
                        import traceback
                        logger.error(traceback.format_exc())
                    
                    # Se mercado fechado, aguardar antes do próximo scan
                    if status == 'CLOSED':
                        # Aguardar até próximo dia útil (máximo 1 hora para verificar novamente)
                        next_open = self.trading_schedule.get_next_trading_open()
                        if next_open:
                            wait_seconds = (next_open - b3_time).total_seconds()
                            wait_minutes = int(wait_seconds / 60)
                            logger.info(f"Mercado fechado. Próxima abertura: {next_open.strftime('%d/%m/%Y %H:%M')} (aguardando {wait_minutes} minutos)")
                            time.sleep(min(wait_seconds, 3600))
                        else:
                            logger.info("Mercado fechado. Aguardando 1 hora...")
                            time.sleep(3600)
                    else:
                        # Durante trading, aguardar intervalo normal
                        logger.debug(f"Aguardando {interval_seconds}s até próximo scan...")
                        time.sleep(interval_seconds)
                    
                    # Log detalhado se houver propostas (já movido para cima)
                except Exception as e:
                    logger.error(f"Erro no loop de monitoramento: {e}")
                    time.sleep(60)  # Esperar 1 minuto antes de tentar novamente
        
        self.thread = threading.Thread(target=monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Monitoramento iniciado (intervalo: {interval_seconds}s, horário B3)")
    
    def stop_monitoring(self):
        """Para monitoramento."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Monitoramento parado")
    
    def get_status(self) -> Dict:
        """Retorna status do monitoramento."""
        return {
            'is_running': self.is_running,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'opportunities_found': len(self.opportunities_found),
            'proposals_generated': len(self.proposals_generated),
            'recent_opportunities': self.opportunities_found[:5],
            'recent_proposals': [{'id': p.proposal_id, 'strategy': p.strategy} for p in self.proposals_generated[:5]]
        }

