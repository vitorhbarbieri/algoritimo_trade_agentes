"""
Utilitários: logging estruturado e métricas.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np


class StructuredLogger:
    """Logger estruturado que salva em JSON lines."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"decisions-{today}.jsonl"
        self.logger = logging.getLogger("trading_agents")
        self.logger.setLevel(logging.INFO)
        
        # Handler para arquivo JSONL
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding='utf-8')
            self.logger.addHandler(handler)
    
    def log_decision(self, event_type: str, data: Dict[str, Any]):
        """Registra uma decisão em formato JSON."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_trader_proposal(self, proposal_id: str, strategy: str, details: Dict):
        """Registra proposta do TraderAgent."""
        self.log_decision("trader_proposal", {
            "proposal_id": proposal_id,
            "strategy": strategy,
            **details
        })
    
    def log_risk_evaluation(self, proposal_id: str, decision: str, reason: str, details: Dict):
        """Registra avaliação do RiskAgent."""
        self.log_decision("risk_evaluation", {
            "proposal_id": proposal_id,
            "decision": decision,
            "reason": reason,
            **details
        })
    
    def log_execution(self, order_id: str, status: str, details: Dict):
        """Registra execução de ordem."""
        self.log_decision("execution", {
            "order_id": order_id,
            "status": status,
            **details
        })


def calculate_metrics(returns: pd.Series, nav_series: pd.Series) -> Dict[str, float]:
    """
    Calcula métricas de performance.
    
    Args:
        returns: Série de retornos
        nav_series: Série de NAV (patrimônio líquido)
    
    Returns:
        Dicionário com métricas
    """
    if len(returns) == 0:
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "win_rate": 0.0,
            "total_trades": 0
        }
    
    # Retorno total
    total_return = (nav_series.iloc[-1] / nav_series.iloc[0] - 1) * 100
    
    # Sharpe ratio (anualizado, assumindo 252 dias úteis)
    if returns.std() > 0:
        sharpe = np.sqrt(252) * returns.mean() / returns.std()
    else:
        sharpe = 0.0
    
    # Max drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min()) * 100
    
    # Volatilidade anualizada
    volatility = returns.std() * np.sqrt(252) * 100
    
    # Win rate
    positive_returns = returns[returns > 0]
    win_rate = len(positive_returns) / len(returns) * 100 if len(returns) > 0 else 0.0
    
    return {
        "total_return": total_return,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_drawdown,
        "volatility": volatility,
        "win_rate": win_rate,
        "total_trades": len(returns)
    }


def get_version_info() -> Dict[str, str]:
    """Retorna informações de versão do projeto."""
    import sys
    import importlib
    
    version_info = {
        "python_version": sys.version.split()[0],
        "project_version": "1.0.0",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Versões de bibliotecas principais
    libs = ['pandas', 'numpy', 'scipy', 'statsmodels', 'matplotlib']
    for lib in libs:
        try:
            mod = importlib.import_module(lib)
            version_info[f"{lib}_version"] = getattr(mod, '__version__', 'unknown')
        except:
            version_info[f"{lib}_version"] = "not_installed"
    
    # Tentar obter hash do git
    try:
        import subprocess
        git_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        version_info["git_hash"] = git_hash
    except:
        version_info["git_hash"] = "not_available"
    
    return version_info

