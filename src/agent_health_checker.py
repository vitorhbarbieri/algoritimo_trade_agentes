"""
Sistema de Verificação de Saúde dos Agentes
Verifica se todos os agentes estão operantes e funcionando corretamente.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

try:
    from .agents import TraderAgent, RiskAgent, PortfolioManager, DayTradeOptionsStrategy
    from .utils import StructuredLogger
    from .pricing import BlackScholes
except ImportError:
    from agents import TraderAgent, RiskAgent, PortfolioManager, DayTradeOptionsStrategy
    from utils import StructuredLogger
    from pricing import BlackScholes


class AgentHealthChecker:
    """Verifica saúde e operacionalidade dos agentes."""
    
    def __init__(self, config: Dict, logger: Optional[StructuredLogger] = None):
        self.config = config
        self.logger = logger or StructuredLogger(log_dir='logs')
        self.health_status = {}
        self.last_check_time = None
    
    def check_all_agents(self) -> Dict:
        """Verifica saúde de todos os agentes."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'agents': {}
        }
        
        # Verificar TraderAgent
        trader_status = self._check_trader_agent()
        results['agents']['trader_agent'] = trader_status
        
        # Verificar RiskAgent
        risk_status = self._check_risk_agent()
        results['agents']['risk_agent'] = risk_status
        
        # Verificar DayTradeOptionsStrategy
        daytrade_status = self._check_daytrade_strategy()
        results['agents']['daytrade_strategy'] = daytrade_status
        
        # Verificar VolArb Strategy
        volarb_status = self._check_volarb_strategy()
        results['agents']['vol_arb_strategy'] = volarb_status
        
        # Verificar Pairs Strategy
        pairs_status = self._check_pairs_strategy()
        results['agents']['pairs_strategy'] = pairs_status
        
        # Determinar status geral
        all_healthy = all(
            agent.get('status') == 'healthy' 
            for agent in results['agents'].values()
        )
        results['overall_status'] = 'healthy' if all_healthy else 'degraded'
        
        self.health_status = results
        self.last_check_time = datetime.now()
        
        return results
    
    def _check_trader_agent(self) -> Dict:
        """Verifica TraderAgent."""
        try:
            agent = TraderAgent(self.config, self.logger)
            
            # Teste básico: verificar se consegue gerar propostas (mesmo que vazias)
            test_market_data = {
                'spot': {'AAPL': {'close': 150.0, 'open': 149.0, 'high': 151.0, 'low': 148.0, 'volume': 1000000}},
                'options': []
            }
            
            proposals = agent.generate_proposals(pd.Timestamp.now(), test_market_data)
            
            return {
                'status': 'healthy',
                'name': 'TraderAgent',
                'can_generate_proposals': True,
                'test_proposals_count': len(proposals),
                'strategies_loaded': len(agent.strategies) if hasattr(agent, 'strategies') else 0,
                'message': 'TraderAgent operacional'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'name': 'TraderAgent',
                'error': str(e),
                'message': f'Erro ao verificar TraderAgent: {e}'
            }
    
    def _check_risk_agent(self) -> Dict:
        """Verifica RiskAgent."""
        try:
            portfolio = PortfolioManager(self.config.get('nav', 1000000))
            agent = RiskAgent(portfolio, self.config, self.logger)
            
            # Verificar se kill switch funciona
            agent.kill_switch()
            kill_switch_works = agent.kill_switch_active
            
            # Resetar kill switch
            agent.kill_switch_active = False
            
            return {
                'status': 'healthy',
                'name': 'RiskAgent',
                'kill_switch_works': kill_switch_works,
                'message': 'RiskAgent operacional'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'name': 'RiskAgent',
                'error': str(e),
                'message': f'Erro ao verificar RiskAgent: {e}'
            }
    
    def _check_daytrade_strategy(self) -> Dict:
        """Verifica DayTradeOptionsStrategy."""
        try:
            daytrade_config = self.config.get('daytrade_options', {})
            
            if not daytrade_config.get('enabled', True):
                return {
                    'status': 'disabled',
                    'name': 'DayTradeOptionsStrategy',
                    'message': 'Estratégia desabilitada na configuração'
                }
            
            strategy = DayTradeOptionsStrategy(self.config, self.logger)
            
            # Teste básico: verificar se consegue processar dados
            test_market_data = {
                'spot': {
                    'AAPL': {
                        'close': 150.0,
                        'open': 149.0,
                        'high': 151.0,
                        'low': 148.0,
                        'volume': 2000000,
                        'adv': 1000000
                    }
                },
                'options': [
                    {
                        'underlying': 'AAPL',
                        'strike': 150.0,
                        'expiry': pd.Timestamp.now() + pd.Timedelta(days=5),
                        'option_type': 'C',
                        'bid': 2.0,
                        'ask': 2.2,
                        'mid': 2.1,
                        'implied_vol': 0.25,
                        'volume': 500,
                        'open_interest': 1000
                    }
                ]
            }
            
            proposals = strategy.generate(1000000, pd.Timestamp.now(), test_market_data)
            
            return {
                'status': 'healthy',
                'name': 'DayTradeOptionsStrategy',
                'can_generate_proposals': True,
                'test_proposals_count': len(proposals),
                'config_enabled': True,
                'message': 'DayTradeOptionsStrategy operacional'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'name': 'DayTradeOptionsStrategy',
                'error': str(e),
                'message': f'Erro ao verificar DayTradeOptionsStrategy: {e}'
            }
    
    def _check_volarb_strategy(self) -> Dict:
        """Verifica estratégia VolArb."""
        try:
            if not self.config.get('enable_vol_arb', True):
                return {
                    'status': 'disabled',
                    'name': 'VolArbStrategy',
                    'message': 'Estratégia desabilitada na configuração'
                }
            
            return {
                'status': 'healthy',
                'name': 'VolArbStrategy',
                'config_enabled': True,
                'threshold': self.config.get('vol_arb_threshold', 0.08),
                'message': 'VolArbStrategy configurada corretamente'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'name': 'VolArbStrategy',
                'error': str(e),
                'message': f'Erro ao verificar VolArbStrategy: {e}'
            }
    
    def _check_pairs_strategy(self) -> Dict:
        """Verifica estratégia Pairs."""
        try:
            if not self.config.get('enable_pairs', True):
                return {
                    'status': 'disabled',
                    'name': 'PairsStrategy',
                    'message': 'Estratégia desabilitada na configuração'
                }
            
            return {
                'status': 'healthy',
                'name': 'PairsStrategy',
                'config_enabled': True,
                'ticker1': self.config.get('pairs_ticker1', 'AAPL'),
                'ticker2': self.config.get('pairs_ticker2', 'MSFT'),
                'zscore_threshold': self.config.get('pairs_zscore_threshold', 2.0),
                'message': 'PairsStrategy configurada corretamente'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'name': 'PairsStrategy',
                'error': str(e),
                'message': f'Erro ao verificar PairsStrategy: {e}'
            }
    
    def check_recent_activity(self, hours: int = 24) -> Dict:
        """Verifica atividade recente dos agentes."""
        log_dir = Path('logs')
        if not log_dir.exists():
            return {
                'status': 'no_logs',
                'message': 'Diretório de logs não encontrado',
                'activities': {}
            }
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        activities = {
            'trader_proposals': 0,
            'risk_evaluations': 0,
            'executions': 0,
            'daytrade_proposals': 0,
            'vol_arb_proposals': 0,
            'pairs_proposals': 0,
            'last_activity': None
        }
        
        try:
            logs = []
            for log_file in sorted(log_dir.glob("*.jsonl"), reverse=True):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                log_entry = json.loads(line)
                                log_time = datetime.fromisoformat(log_entry.get('timestamp', '').replace('Z', '+00:00'))
                                if log_time.replace(tzinfo=None) >= cutoff_time:
                                    logs.append(log_entry)
                except:
                    continue
            
            # Contar atividades
            for log in logs:
                event_type = log.get('event_type', '')
                strategy = log.get('strategy', '')
                
                if event_type == 'trader_proposal':
                    activities['trader_proposals'] += 1
                    if strategy == 'daytrade_options':
                        activities['daytrade_proposals'] += 1
                    elif strategy == 'vol_arb':
                        activities['vol_arb_proposals'] += 1
                    elif strategy == 'pairs':
                        activities['pairs_proposals'] += 1
                elif event_type == 'risk_evaluation':
                    activities['risk_evaluations'] += 1
                elif event_type == 'execution':
                    activities['executions'] += 1
                
                # Última atividade
                log_time = log.get('timestamp', '')
                if log_time and (not activities['last_activity'] or log_time > activities['last_activity']):
                    activities['last_activity'] = log_time
            
            return {
                'status': 'ok',
                'hours_checked': hours,
                'activities': activities,
                'total_logs': len(logs)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erro ao verificar atividade: {e}',
                'activities': activities
            }
    
    def get_health_summary(self) -> Dict:
        """Retorna resumo de saúde dos agentes."""
        if not self.health_status:
            self.check_all_agents()
        
        activity = self.check_recent_activity(hours=24)
        
        return {
            'health_check': self.health_status,
            'recent_activity': activity,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None
        }

