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
        
        # Verificar se está no horário de trading
        if not self.trading_schedule.is_trading_hours():
            return {
                'timestamp': b3_time.isoformat(),
                'status': 'OUTSIDE_TRADING_HOURS',
                'opportunities': 0,
                'proposals': 0
            }
        
        # Enviar notificação de status a cada 2 horas
        if self.last_status_notification is None or \
           (b3_time - self.last_status_notification).total_seconds() >= 7200:  # 2 horas
            self._send_status_notification()
        
        try:
            # Buscar dados de ações
            tickers = self.config.get('monitored_tickers', [])
            if tickers:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                # Buscar dados spot
                spot_df = self.stock_api.fetch_spot_data(tickers[:10], start_date, end_date)  # Limitar para não demorar
                
                # Buscar opções (apenas para primeiro ticker)
                if tickers:
                    options_df = self.stock_api.fetch_options_chain(tickers[0], start_date, end_date)
                else:
                    options_df = pd.DataFrame()
                
                # Preparar market_data
                market_data = {'spot': {}, 'options': {}}
                
                if not spot_df.empty:
                    for ticker in spot_df['ticker'].unique():
                        ticker_data = spot_df[spot_df['ticker'] == ticker].iloc[-1]
                        market_data['spot'][ticker] = {
                            'close': ticker_data['close'],
                            'open': ticker_data['open'],
                            'high': ticker_data['high'],
                            'low': ticker_data['low'],
                            'volume': ticker_data['volume']
                        }
                
                if not options_df.empty:
                    market_data['options'] = {tickers[0]: options_df.to_dict('records')}
                
                # Escanear oportunidades
                opportunities = self.market_monitor.scan_all_opportunities(market_data)
                
                # Enviar notificações se encontrar oportunidades
                if opportunities:
                    # Notificar oportunidades encontradas
                    for opp in opportunities[:5]:  # Limitar a 5 para não spammar
                        self.notifier.notify_opportunity(opp)
                
                # Gerar propostas
                if opportunities:
                    proposals = self.trader_agent.generate_proposals(
                        pd.to_datetime(datetime.now()),
                        market_data
                    )
                    
                    # Enviar notificações se houver propostas importantes
                    if proposals:
                        # Notificar sobre propostas de daytrade (alta prioridade)
                        daytrade_proposals = [p for p in proposals if p.strategy == 'daytrade_options']
                        if daytrade_proposals:
                            for proposal in daytrade_proposals[:3]:  # Limitar a 3 para não spammar
                                opportunity_data = {
                                    'type': 'daytrade_options',
                                    'symbol': proposal.symbol,
                                    'ticker': proposal.metadata.get('underlying', 'N/A'),
                                    'opportunity_score': proposal.metadata.get('intraday_return', 0) * 100,
                                    'proposal_id': proposal.proposal_id,
                                    'strike': proposal.metadata.get('strike', 'N/A'),
                                    'delta': proposal.metadata.get('delta', 0),
                                    'intraday_return': proposal.metadata.get('intraday_return', 0),
                                    'volume_ratio': proposal.metadata.get('volume_ratio', 0)
                                }
                                self.notifier.notify_opportunity(opportunity_data)
            
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
                details={'timestamp': datetime.now().isoformat()}
            )
        
        self.last_scan_time = datetime.now()
        self.opportunities_found = opportunities[:10]  # Últimas 10
        self.proposals_generated = proposals
        
        return {
            'timestamp': self.last_scan_time.isoformat(),
            'opportunities': len(opportunities),
            'proposals': len(proposals),
            'opportunities_list': opportunities[:5],  # Top 5
            'proposals_list': [{'id': p.proposal_id, 'strategy': p.strategy, 'symbol': p.symbol} for p in proposals[:5]]
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
                    
                    # Se não for dia útil ou fora do horário, aguardar
                    if status == 'CLOSED':
                        # Aguardar até próximo dia útil
                        next_open = self.trading_schedule.get_next_trading_open()
                        if next_open:
                            wait_seconds = (next_open - b3_time).total_seconds()
                            logger.info(f"Mercado fechado. Próxima abertura: {next_open.strftime('%d/%m/%Y %H:%M')}")
                            # Aguardar até próximo dia útil (máximo 1 hora para verificar novamente)
                            time.sleep(min(wait_seconds, 3600))
                        else:
                            time.sleep(3600)  # Aguardar 1 hora
                        continue
                    
                    # Escanear mercado
                    result = self.scan_market()
                    logger.info(f"Scan completo ({status}): {result.get('opportunities', 0)} oportunidades, {result.get('proposals', 0)} propostas")
                    
                    # Intervalo entre scans
                    time.sleep(interval_seconds)
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

