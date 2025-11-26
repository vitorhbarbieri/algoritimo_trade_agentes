"""
Repositório para persistir propostas, ordens e execuções dos agentes.
Salva tudo em SQLite para acompanhamento e análise posterior.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents_orders.db")

SCHEMA_SQL = """
-- Tabela de propostas geradas pelo TraderAgent
CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    strategy TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    order_type TEXT NOT NULL,
    metadata TEXT,  -- JSON com metadados
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_proposals_proposal_id ON proposals (proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposals_timestamp ON proposals (timestamp);
CREATE INDEX IF NOT EXISTS idx_proposals_strategy ON proposals (strategy);
CREATE INDEX IF NOT EXISTS idx_proposals_symbol ON proposals (symbol);

-- Tabela de avaliações do RiskAgent
CREATE TABLE IF NOT EXISTS risk_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('APPROVE', 'MODIFY', 'REJECT')),
    reason TEXT,
    details TEXT,  -- JSON com detalhes
    modified_quantity REAL,
    modified_price REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);
CREATE INDEX IF NOT EXISTS idx_risk_eval_proposal_id ON risk_evaluations (proposal_id);
CREATE INDEX IF NOT EXISTS idx_risk_eval_timestamp ON risk_evaluations (timestamp);
CREATE INDEX IF NOT EXISTS idx_risk_eval_decision ON risk_evaluations (decision);

-- Tabela de execuções simuladas
CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,
    proposal_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    market_price REAL,
    slippage REAL,
    commission REAL,
    notional REAL,
    total_cost REAL,
    status TEXT NOT NULL CHECK (status IN ('FILLED', 'PARTIAL', 'REJECTED', 'CANCELLED')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);
CREATE INDEX IF NOT EXISTS idx_executions_order_id ON executions (order_id);
CREATE INDEX IF NOT EXISTS idx_executions_proposal_id ON executions (proposal_id);
CREATE INDEX IF NOT EXISTS idx_executions_timestamp ON executions (timestamp);
CREATE INDEX IF NOT EXISTS idx_executions_symbol ON executions (symbol);

-- Tabela de snapshots de performance (backtest em tempo real)
CREATE TABLE IF NOT EXISTS performance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    nav REAL NOT NULL,
    total_pnl REAL NOT NULL DEFAULT 0,
    daily_pnl REAL NOT NULL DEFAULT 0,
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    losing_trades INTEGER NOT NULL DEFAULT 0,
    open_positions INTEGER NOT NULL DEFAULT 0,
    total_delta REAL DEFAULT 0,
    total_gamma REAL DEFAULT 0,
    total_vega REAL DEFAULT 0,
    portfolio_value REAL,
    cash REAL,
    details TEXT,  -- JSON com detalhes adicionais
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_perf_snapshots_timestamp ON performance_snapshots (timestamp);

-- Tabela de posições abertas
CREATE TABLE IF NOT EXISTS open_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity REAL NOT NULL,
    avg_price REAL NOT NULL,
    current_price REAL,
    unrealized_pnl REAL DEFAULT 0,
    delta REAL DEFAULT 0,
    gamma REAL DEFAULT 0,
    vega REAL DEFAULT 0,
    opened_at TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    closed_at TEXT,
    UNIQUE(symbol, side, opened_at)
);
CREATE INDEX IF NOT EXISTS idx_open_positions_symbol ON open_positions (symbol);
CREATE INDEX IF NOT EXISTS idx_open_positions_opened_at ON open_positions (opened_at);
"""


@contextmanager
def _connect():
    """Context manager para conexão com banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro no banco de dados: {e}")
        raise
    finally:
        conn.close()


def init_db():
    """Inicializa o banco de dados criando as tabelas se não existirem."""
    with _connect() as conn:
        conn.executescript(SCHEMA_SQL)
    logger.info(f"Banco de dados inicializado: {DB_PATH}")


class OrdersRepository:
    """Repositório para persistir ordens e propostas dos agentes."""
    
    def __init__(self, db_path: str = None):
        global DB_PATH
        if db_path:
            DB_PATH = db_path
        init_db()
    
    def save_proposal(self, proposal: Dict) -> bool:
        """Salva uma proposta gerada pelo TraderAgent."""
        try:
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO proposals 
                    (proposal_id, timestamp, strategy, instrument_type, symbol, 
                     side, quantity, price, order_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal.get('proposal_id'),
                    proposal.get('timestamp', datetime.now().isoformat()),
                    proposal.get('strategy', 'unknown'),
                    proposal.get('instrument_type', 'unknown'),
                    proposal.get('symbol', ''),
                    proposal.get('side', 'BUY'),
                    proposal.get('quantity', 0),
                    proposal.get('price', 0),
                    proposal.get('order_type', 'LIMIT'),
                    json.dumps(proposal.get('metadata', {}))
                ))
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar proposta: {e}")
            return False
    
    def save_risk_evaluation(self, evaluation: Dict) -> bool:
        """Salva avaliação do RiskAgent."""
        try:
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO risk_evaluations 
                    (proposal_id, timestamp, decision, reason, details, 
                     modified_quantity, modified_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    evaluation.get('proposal_id'),
                    evaluation.get('timestamp', datetime.now().isoformat()),
                    evaluation.get('decision', 'REJECT'),
                    evaluation.get('reason', ''),
                    json.dumps(evaluation.get('details', {})),
                    evaluation.get('modified_quantity'),
                    evaluation.get('modified_price')
                ))
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar avaliação de risco: {e}")
            return False
    
    def save_execution(self, execution: Dict) -> bool:
        """Salva execução simulada."""
        try:
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO executions 
                    (order_id, proposal_id, timestamp, symbol, side, quantity, 
                     price, market_price, slippage, commission, notional, 
                     total_cost, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.get('order_id') or execution.get('fill_id'),
                    execution.get('proposal_id', ''),
                    execution.get('timestamp', datetime.now().isoformat()),
                    execution.get('symbol', ''),
                    execution.get('side', 'BUY'),
                    execution.get('quantity', 0),
                    execution.get('price', 0),
                    execution.get('market_price'),
                    execution.get('slippage', 0),
                    execution.get('commission', 0),
                    execution.get('notional', 0),
                    execution.get('total_cost', 0),
                    execution.get('status', 'FILLED')
                ))
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar execução: {e}")
            return False
    
    def save_performance_snapshot(self, snapshot: Dict) -> bool:
        """Salva snapshot de performance (backtest em tempo real)."""
        try:
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO performance_snapshots 
                    (timestamp, nav, total_pnl, daily_pnl, total_trades, 
                     winning_trades, losing_trades, open_positions, 
                     total_delta, total_gamma, total_vega, portfolio_value, 
                     cash, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.get('timestamp', datetime.now().isoformat()),
                    snapshot.get('nav', 0),
                    snapshot.get('total_pnl', 0),
                    snapshot.get('daily_pnl', 0),
                    snapshot.get('total_trades', 0),
                    snapshot.get('winning_trades', 0),
                    snapshot.get('losing_trades', 0),
                    snapshot.get('open_positions', 0),
                    snapshot.get('total_delta', 0),
                    snapshot.get('total_gamma', 0),
                    snapshot.get('total_vega', 0),
                    snapshot.get('portfolio_value', 0),
                    snapshot.get('cash', 0),
                    json.dumps(snapshot.get('details', {}))
                ))
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar snapshot: {e}")
            return False
    
    def get_proposals(self, strategy: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Busca propostas com filtros opcionais."""
        try:
            with _connect() as conn:
                query = "SELECT * FROM proposals WHERE 1=1"
                params = []
                
                if strategy:
                    query += " AND strategy = ?"
                    params.append(strategy)
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY timestamp DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                # Parsear metadata JSON
                if 'metadata' in df.columns:
                    df['metadata'] = df['metadata'].apply(lambda x: json.loads(x) if x else {})
                
                return df
        except Exception as e:
            logger.error(f"Erro ao buscar propostas: {e}")
            return pd.DataFrame()
    
    def get_risk_evaluations(self, proposal_id: str = None) -> pd.DataFrame:
        """Busca avaliações de risco."""
        try:
            with _connect() as conn:
                query = "SELECT * FROM risk_evaluations WHERE 1=1"
                params = []
                
                if proposal_id:
                    query += " AND proposal_id = ?"
                    params.append(proposal_id)
                
                query += " ORDER BY timestamp DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if 'details' in df.columns:
                    df['details'] = df['details'].apply(lambda x: json.loads(x) if x else {})
                
                return df
        except Exception as e:
            logger.error(f"Erro ao buscar avaliações: {e}")
            return pd.DataFrame()
    
    def get_executions(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Busca execuções."""
        try:
            with _connect() as conn:
                query = "SELECT * FROM executions WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY timestamp DESC"
                
                return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            logger.error(f"Erro ao buscar execuções: {e}")
            return pd.DataFrame()
    
    def get_performance_snapshots(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Busca snapshots de performance."""
        try:
            with _connect() as conn:
                query = "SELECT * FROM performance_snapshots WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY timestamp ASC"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if 'details' in df.columns:
                    df['details'] = df['details'].apply(lambda x: json.loads(x) if x else {})
                
                return df
        except Exception as e:
            logger.error(f"Erro ao buscar snapshots: {e}")
            return pd.DataFrame()
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """Retorna resumo do dia."""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        start = f"{date} 00:00:00"
        end = f"{date} 23:59:59"
        
        proposals = self.get_proposals(start_date=start, end_date=end)
        executions = self.get_executions(start_date=start, end_date=end)
        evaluations = self.get_risk_evaluations()
        
        # Filtrar avaliações do dia
        if not evaluations.empty:
            evaluations = evaluations[
                (evaluations['timestamp'] >= start) & 
                (evaluations['timestamp'] <= end)
            ]
        
        return {
            'date': date,
            'total_proposals': len(proposals),
            'proposals_by_strategy': proposals.groupby('strategy').size().to_dict() if not proposals.empty else {},
            'total_executions': len(executions),
            'total_approved': len(evaluations[evaluations['decision'] == 'APPROVE']) if not evaluations.empty else 0,
            'total_rejected': len(evaluations[evaluations['decision'] == 'REJECT']) if not evaluations.empty else 0,
            'total_modified': len(evaluations[evaluations['decision'] == 'MODIFY']) if not evaluations.empty else 0,
            'total_pnl': executions['total_cost'].sum() if not executions.empty and 'total_cost' in executions.columns else 0
        }

