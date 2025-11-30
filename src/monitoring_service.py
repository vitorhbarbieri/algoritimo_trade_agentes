"""
Serviço de Monitoramento Contínuo - Escaneia mercado em tempo real.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import pandas as pd

try:
    from .market_monitor import MarketMonitor
    from .data_loader import DataLoader
    from .market_data_api import create_market_data_api
    from .crypto_api import create_crypto_api
    from .agents import TraderAgent
    from .utils import StructuredLogger
    from .notifications import UnifiedNotifier
    from .orders_repository import OrdersRepository
    from .trading_schedule import TradingSchedule
except ImportError:
    from market_monitor import MarketMonitor
    from data_loader import DataLoader
    from market_data_api import create_market_data_api
    from crypto_api import create_crypto_api
    from agents import TraderAgent
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
        self.trader_agent = TraderAgent(config, self.logger, orders_repo=self.orders_repo)
        self.data_loader = DataLoader()
        self.notifier = UnifiedNotifier(config)  # Sistema unificado de notificações
        self.trading_schedule = TradingSchedule()  # Horário de funcionamento B3
        self.is_running = False
        self.thread = None
        self.last_scan_time = None
        self.opportunities_found = []
        self.proposals_generated = []
        self.trading_started = False  # Flag para saber se já iniciou hoje
        self.last_status_notification = None  # Última notificação de status (2h)
        self.day_start_time = None  # Horário de início do dia
        
        # APIs
        self.stock_api = create_market_data_api('yfinance')
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
        message = f"""
🚀 *AGENTE DE DAYTRADE INICIADO*

*Horário:* {b3_time.strftime('%d/%m/%Y %H:%M:%S')} (B3)
*Status:* {'Pré-Mercado' if self.trading_schedule.is_pre_market() else 'Mercado Aberto'}

O agente está agora monitorando o mercado e gerando propostas de daytrade.

*Horário de funcionamento:*
• Pré-mercado: 09:45 - 10:00
• Trading: 10:00 - 17:00
• Fechamento: 17:00

Você receberá atualizações a cada 2 horas durante o pregão.
"""
        self.notifier.send(message, title="🚀 Agente Iniciado", priority='high')
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
        
        message = f"""
🏁 *AGENTE DE DAYTRADE FINALIZADO*

*Horário:* {b3_time.strftime('%d/%m/%Y %H:%M:%S')} (B3)
*Tempo de operação:* {runtime if runtime else 'N/A'}

*Resumo do Dia:*
• Propostas geradas: {summary.get('total_proposals', 0)}
• Propostas aprovadas: {summary.get('total_approved', 0)}
• Propostas rejeitadas: {summary.get('total_rejected', 0)}
• Execuções: {summary.get('total_executions', 0)}

O agente encerrou as atividades do dia. Retomará amanhã às 09:45.
"""
        self.notifier.send(message, title="🏁 Agente Finalizado", priority='normal')
        self.trading_started = False
        self.day_start_time = None
    
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
        
        message += f"\n*Próxima atualização:* Em 2 horas"
        
        self.notifier.send(message, title="📊 Status do Agente", priority='normal')
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
            tickers = self.config.get('monitored_tickers', [])
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
            market_data = {'spot': {}, 'options': {}}
            
            logger.info(f"Buscando dados intraday para {len(tickers)} tickers...")
            
            # Importar yfinance uma vez
            try:
                import yfinance as yf
            except ImportError:
                logger.error("yfinance não instalado! Execute: pip install yfinance")
                raise
            
            # Buscar dados spot INTRADAY para cada ticker
            tickers_to_process = tickers[:30]  # Processar todos os tickers configurados
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
                    
                    # Buscar opções para este ticker (apenas se tiver dados spot)
                    try:
                        options_df = self.stock_api.fetch_options_chain(ticker, today, today)
                        if not options_df.empty:
                            if ticker not in market_data['options']:
                                market_data['options'][ticker] = []
                            market_data['options'][ticker].extend(options_df.to_dict('records'))
                            logger.debug(f"Opções encontradas para {ticker}: {len(options_df)}")
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
                
                if saved_count > 0:
                    logger.info(f"Dados salvos no banco: {saved_count} tickers")
            
            # CRÍTICO: Gerar propostas APENAS durante horário de trading
            # Mas sempre capturamos dados para rastreabilidade
            proposals = []
            if should_generate_proposals and market_data['spot']:
                # Gerar propostas do TraderAgent (inclui DayTradeOptionsStrategy)
                proposals = self.trader_agent.generate_proposals(
                    pd.to_datetime(datetime.now()),
                    market_data
                )
                
                logger.info(f"Propostas geradas: {len(proposals)}")
                
                # Escanear oportunidades do MarketMonitor (para outras estratégias)
                opportunities = self.market_monitor.scan_all_opportunities(market_data)
                
                # Enviar notificações se encontrar oportunidades
                if opportunities:
                    for opp in opportunities[:5]:
                        self.notifier.notify_opportunity(opp)
                
                # Enviar notificações de propostas importantes com botões de aprovação
                if proposals:
                    # Notificar sobre propostas de daytrade (alta prioridade)
                    daytrade_proposals = [p for p in proposals if p.strategy == 'daytrade_options']
                    if daytrade_proposals:
                        logger.info(f"Propostas de daytrade encontradas: {len(daytrade_proposals)}")
                        for proposal in daytrade_proposals[:5]:  # Limitar a 5
                            # Preparar dados da proposta para Telegram
                            # Todas as informações já estão no metadata após padronização
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
                                # Fallback: enviar notificação normal
                                opportunity_data = {
                                    'type': 'daytrade_options',
                                    'symbol': proposal.symbol,
                                    'ticker': proposal.metadata.get('underlying', 'N/A'),
                                    'opportunity_score': proposal.metadata.get('intraday_return', 0) * 100,
                                    'proposal_id': proposal.proposal_id,
                                    'strike': proposal.metadata.get('strike', 'N/A'),
                                    'delta': proposal.metadata.get('delta', 0),
                                    'intraday_return': proposal.metadata.get('intraday_return', 0),
                                    'volume_ratio': proposal.metadata.get('volume_ratio', 0),
                                    'expected_gain': expected_gain,
                                    'expected_gain_pct': expected_gain_pct
                                }
                                self.notifier.notify_opportunity(opportunity_data)
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

