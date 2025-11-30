#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agente de Verificação e Monitoramento da Captura de Dados.
Roda de hora em hora para verificar se a captura está funcionando,
corrige problemas automaticamente e envia relatórios periódicos.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.notifications import UnifiedNotifier
    from src.market_data_api import create_market_data_api
    from src.trading_schedule import TradingSchedule
except ImportError:
    from notifications import UnifiedNotifier
    from market_data_api import create_market_data_api
    from trading_schedule import TradingSchedule

logger = logging.getLogger(__name__)


class DataHealthMonitor:
    """Monitor de saúde da captura de dados."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db_path = Path('agents_orders.db')
        self.notifier = UnifiedNotifier(config)
        self.trading_schedule = TradingSchedule()
        
        # Configurar API de mercado
        api_type = config.get('market_data_api', 'yfinance')
        self.market_api = create_market_data_api(api_type)
        
        # Tickers monitorados
        self.monitored_tickers = config.get('monitored_tickers', [])
        
        # Horários de relatório
        self.report_times = ['11:00', '15:00']
    
    def check_database_health(self) -> Dict:
        """Verifica saúde do banco de dados."""
        try:
            if not self.db_path.exists():
                return {
                    'status': 'ERROR',
                    'message': 'Banco de dados não encontrado',
                    'can_fix': False
                }
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Verificar se tabela existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='market_data_captures'
            """)
            
            if not cursor.fetchone():
                conn.close()
                return {
                    'status': 'ERROR',
                    'message': 'Tabela market_data_captures não existe',
                    'can_fix': True
                }
            
            # Verificar última captura
            cursor.execute("""
                SELECT MAX(timestamp) FROM market_data_captures
                WHERE source = 'real'
            """)
            result = cursor.fetchone()
            last_capture = result[0] if result[0] else None
            
            # Verificar capturas nas últimas 2 horas
            two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM market_data_captures
                WHERE source = 'real' AND timestamp >= ?
            """, (two_hours_ago,))
            recent_captures = cursor.fetchone()[0]
            
            # Verificar capturas por ticker nas últimas 2 horas
            cursor.execute("""
                SELECT ticker, COUNT(*) as count
                FROM market_data_captures
                WHERE source = 'real' AND timestamp >= ?
                GROUP BY ticker
                ORDER BY count DESC
            """, (two_hours_ago,))
            ticker_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'status': 'OK' if recent_captures > 0 else 'WARNING',
                'last_capture': last_capture,
                'recent_captures': recent_captures,
                'ticker_stats': ticker_stats,
                'can_fix': False
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar banco de dados: {e}")
            return {
                'status': 'ERROR',
                'message': str(e),
                'can_fix': False
            }
    
    def check_api_health(self) -> Dict:
        """Verifica se a API de mercado está funcionando."""
        try:
            if not self.monitored_tickers:
                return {
                    'status': 'WARNING',
                    'message': 'Nenhum ticker configurado',
                    'can_fix': False
                }
            
            # Testar com primeiro ticker
            test_ticker = self.monitored_tickers[0]
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Tentar buscar dados
            try:
                spot_data = self.market_api.fetch_spot_data(
                    [test_ticker],
                    today,
                    today
                )
                
                if spot_data is None or spot_data.empty:
                    return {
                        'status': 'ERROR',
                        'message': f'API não retornou dados para {test_ticker}',
                        'can_fix': True
                    }
                
                return {
                    'status': 'OK',
                    'message': 'API funcionando',
                    'test_ticker': test_ticker,
                    'can_fix': False
                }
                
            except Exception as api_err:
                return {
                    'status': 'ERROR',
                    'message': f'Erro na API: {str(api_err)}',
                    'can_fix': True
                }
                
        except Exception as e:
            logger.error(f"Erro ao verificar API: {e}")
            return {
                'status': 'ERROR',
                'message': str(e),
                'can_fix': False
            }
    
    def fix_database_issues(self) -> bool:
        """Tenta corrigir problemas no banco de dados."""
        try:
            from src.orders_repository import OrdersRepository
            
            repo = OrdersRepository()
            repo.init_db()  # Isso cria as tabelas se não existirem
            
            logger.info("Banco de dados verificado/corrigido")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao corrigir banco de dados: {e}")
            return False
    
    def fix_api_issues(self) -> bool:
        """Tenta corrigir problemas com a API."""
        try:
            # Tentar recriar conexão com API
            api_type = self.config.get('market_data_api', 'yfinance')
            self.market_api = create_market_data_api(api_type)
            
            # Testar novamente
            test_result = self.check_api_health()
            
            if test_result['status'] == 'OK':
                logger.info("Problema com API corrigido")
                return True
            else:
                logger.warning(f"Não foi possível corrigir API: {test_result['message']}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao corrigir API: {e}")
            return False
    
    def get_capture_statistics(self, hours: int = 24) -> Dict:
        """Obtém estatísticas de captura."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Período
            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Total de capturas
            cursor.execute("""
                SELECT COUNT(*) FROM market_data_captures
                WHERE source = 'real' AND timestamp >= ?
            """, (since_time,))
            total_captures = cursor.fetchone()[0]
            
            # Capturas por ticker
            cursor.execute("""
                SELECT ticker, COUNT(*) as count
                FROM market_data_captures
                WHERE source = 'real' AND timestamp >= ?
                GROUP BY ticker
                ORDER BY count DESC
            """, (since_time,))
            ticker_captures = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Capturas com opções
            cursor.execute("""
                SELECT COUNT(*) FROM market_data_captures
                WHERE source = 'real' AND timestamp >= ?
                AND options_data IS NOT NULL AND options_data != 'null' AND options_data != ''
            """, (since_time,))
            captures_with_options = cursor.fetchone()[0]
            
            # Última captura
            cursor.execute("""
                SELECT MAX(timestamp) FROM market_data_captures
                WHERE source = 'real'
            """)
            last_capture = cursor.fetchone()[0]
            
            # Primeira captura do período
            cursor.execute("""
                SELECT MIN(timestamp) FROM market_data_captures
                WHERE source = 'real' AND timestamp >= ?
            """, (since_time,))
            first_capture = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_captures': total_captures,
                'ticker_captures': ticker_captures,
                'captures_with_options': captures_with_options,
                'last_capture': last_capture,
                'first_capture': first_capture,
                'hours': hours
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                'total_captures': 0,
                'ticker_captures': {},
                'captures_with_options': 0,
                'error': str(e)
            }
    
    def generate_report_message(self, stats: Dict, health: Dict) -> str:
        """Gera mensagem de relatório para Telegram."""
        b3_time = self.trading_schedule.get_current_b3_time()
        current_time_str = b3_time.strftime('%d/%m/%Y %H:%M:%S')
        
        # Status geral
        if health['status'] == 'OK':
            status_emoji = '✅'
            status_text = 'FUNCIONANDO'
        elif health['status'] == 'WARNING':
            status_emoji = '⚠️'
            status_text = 'ATENÇÃO'
        else:
            status_emoji = '❌'
            status_text = 'ERRO'
        
        message = f"""
{status_emoji} *RELATÓRIO DE CAPTURA DE DADOS*

*Data/Hora:* {current_time_str}
*Status:* {status_text}

*📊 ESTATÍSTICAS (Últimas {stats.get('hours', 24)}h):*
• Total de capturas: {stats.get('total_captures', 0)}
• Capturas com opções: {stats.get('captures_with_options', 0)}
• Última captura: {stats.get('last_capture', 'N/A')[:19] if stats.get('last_capture') else 'N/A'}

*📈 CAPTURAS POR TICKER:*
"""
        
        ticker_captures = stats.get('ticker_captures', {})
        if ticker_captures:
            # Ordenar por quantidade
            sorted_tickers = sorted(ticker_captures.items(), key=lambda x: x[1], reverse=True)
            for ticker, count in sorted_tickers[:10]:  # Top 10
                message += f"• {ticker}: {count} capturas\n"
        else:
            message += "• Nenhuma captura registrada\n"
        
        # Informações de saúde
        if health.get('recent_captures', 0) > 0:
            message += f"\n*✅ CAPTURAS RECENTES (Últimas 2h):*\n"
            message += f"• {health['recent_captures']} capturas realizadas\n"
        
        if health.get('last_capture'):
            last_capture_dt = datetime.fromisoformat(health['last_capture'])
            time_diff = datetime.now() - last_capture_dt.replace(tzinfo=None)
            minutes_ago = int(time_diff.total_seconds() / 60)
            message += f"• Última captura há {minutes_ago} minutos\n"
        
        # Avisos
        if health['status'] == 'ERROR':
            message += f"\n*⚠️ PROBLEMA DETECTADO:*\n"
            message += f"• {health.get('message', 'Erro desconhecido')}\n"
            if health.get('can_fix'):
                message += "• Tentativa de correção automática em andamento...\n"
        
        message += f"\n_Relatório gerado automaticamente pelo DataHealthMonitor_"
        
        return message
    
    def send_report(self, force: bool = False):
        """Envia relatório de captura."""
        try:
            b3_time = self.trading_schedule.get_current_b3_time()
            current_time_str = b3_time.strftime('%H:%M')
            
            # Verificar se é horário de relatório ou se forçado
            if not force and current_time_str not in self.report_times:
                return
            
            logger.info(f"Gerando relatório de captura de dados...")
            
            # Verificar saúde
            db_health = self.check_database_health()
            api_health = self.check_api_health()
            
            # Tentar corrigir problemas se possível
            if db_health.get('can_fix') and db_health['status'] == 'ERROR':
                logger.info("Tentando corrigir problema no banco de dados...")
                self.fix_database_issues()
                db_health = self.check_database_health()  # Re-verificar
            
            if api_health.get('can_fix') and api_health['status'] == 'ERROR':
                logger.info("Tentando corrigir problema com API...")
                self.fix_api_issues()
                api_health = self.check_api_health()  # Re-verificar
            
            # Obter estatísticas
            stats = self.get_capture_statistics(hours=24)
            
            # Combinar saúde (priorizar erro)
            overall_health = {
                'status': 'ERROR' if (db_health['status'] == 'ERROR' or api_health['status'] == 'ERROR') 
                         else 'WARNING' if (db_health['status'] == 'WARNING' or api_health['status'] == 'WARNING')
                         else 'OK',
                'recent_captures': db_health.get('recent_captures', 0),
                'last_capture': db_health.get('last_capture'),
                'message': db_health.get('message') or api_health.get('message'),
                'can_fix': db_health.get('can_fix') or api_health.get('can_fix')
            }
            
            # Gerar e enviar mensagem
            report_message = self.generate_report_message(stats, overall_health)
            
            # Enviar via Telegram
            telegram_channel = None
            for channel_name, channel in self.notifier.channels:
                if channel_name == 'telegram':
                    telegram_channel = channel
                    break
            
            if telegram_channel:
                success = telegram_channel.send(
                    report_message,
                    title="Relatório de Captura de Dados",
                    priority='high'
                )
                if success:
                    logger.info(f"Relatório enviado com sucesso às {current_time_str}")
                else:
                    logger.warning(f"Falha ao enviar relatório às {current_time_str}")
            else:
                logger.warning("Canal Telegram não encontrado - relatório não enviado")
            
        except Exception as e:
            logger.error(f"Erro ao enviar relatório: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def run_health_check(self):
        """Executa verificação de saúde completa."""
        logger.info("=" * 70)
        logger.info("VERIFICAÇÃO DE SAÚDE DA CAPTURA DE DADOS")
        logger.info("=" * 70)
        
        # Verificar banco de dados
        logger.info("Verificando banco de dados...")
        db_health = self.check_database_health()
        logger.info(f"Status BD: {db_health['status']} - {db_health.get('message', 'OK')}")
        
        # Verificar API
        logger.info("Verificando API de mercado...")
        api_health = self.check_api_health()
        logger.info(f"Status API: {api_health['status']} - {api_health.get('message', 'OK')}")
        
        # Tentar corrigir se necessário
        if db_health.get('can_fix') and db_health['status'] == 'ERROR':
            logger.info("Tentando corrigir banco de dados...")
            self.fix_database_issues()
        
        if api_health.get('can_fix') and api_health['status'] == 'ERROR':
            logger.info("Tentando corrigir API...")
            self.fix_api_issues()
        
        # Obter estatísticas
        stats = self.get_capture_statistics(hours=24)
        logger.info(f"Total de capturas (24h): {stats.get('total_captures', 0)}")
        logger.info(f"Tickers com capturas: {len(stats.get('ticker_captures', {}))}")
        
        logger.info("=" * 70)
        
        return {
            'db_health': db_health,
            'api_health': api_health,
            'stats': stats
        }

