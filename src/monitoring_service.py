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
except ImportError:
    from market_monitor import MarketMonitor
    from data_loader import DataLoader
    from market_data_api import create_market_data_api
    from crypto_api import create_crypto_api
    from agents import TraderAgent
    from utils import StructuredLogger
    from notifications import UnifiedNotifier
    from orders_repository import OrdersRepository

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
        self.is_running = False
        self.thread = None
        self.last_scan_time = None
        self.opportunities_found = []
        self.proposals_generated = []
        
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
    
    def scan_market(self) -> Dict:
        """Escaneia mercado uma vez."""
        opportunities = []
        proposals = []
        
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
        """Inicia monitoramento contínuo."""
        if self.is_running:
            logger.warning("Monitoramento já está rodando")
            return
        
        self.is_running = True
        
        def monitor_loop():
            while self.is_running:
                try:
                    result = self.scan_market()
                    logger.info(f"Scan completo: {result['opportunities']} oportunidades, {result['proposals']} propostas")
                    time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Erro no loop de monitoramento: {e}")
                    time.sleep(60)  # Esperar 1 minuto antes de tentar novamente
        
        self.thread = threading.Thread(target=monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Monitoramento iniciado (intervalo: {interval_seconds}s)")
    
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

