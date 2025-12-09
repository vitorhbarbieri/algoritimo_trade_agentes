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
import pytz

# Timezone de São Paulo (B3)
B3_TIMEZONE = pytz.timezone('America/Sao_Paulo')

def get_b3_timestamp() -> str:
    """Retorna timestamp atual no timezone de São Paulo (B3)."""
    return datetime.now(B3_TIMEZONE).isoformat()

def _migrate_database():
    """Migra banco de dados adicionando colunas se necessário."""
    try:
        with _connect() as conn:
            cursor = conn.cursor()
            
            # Verificar se colunas existem
            cursor.execute("PRAGMA table_info(open_positions)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Adicionar close_price se não existir
            if 'close_price' not in columns:
                conn.execute("ALTER TABLE open_positions ADD COLUMN close_price REAL")
                logger.info("Coluna close_price adicionada à tabela open_positions")
            
            # Adicionar realized_pnl se não existir
            if 'realized_pnl' not in columns:
                conn.execute("ALTER TABLE open_positions ADD COLUMN realized_pnl REAL")
                logger.info("Coluna realized_pnl adicionada à tabela open_positions")
            
            conn.commit()
    except Exception as e:
        logger.warning(f"Erro na migração do banco (pode ser normal se já migrado): {e}")

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
    source TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('simulation', 'real')),  -- Origem dos dados
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
    source TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('simulation', 'real')),  -- Origem dos dados
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
    source TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('simulation', 'real')),  -- Origem dos dados
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

-- Tabela para armazenar dados de mercado capturados (rastreabilidade)
CREATE TABLE IF NOT EXISTS market_data_captures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    ticker TEXT NOT NULL,
    data_type TEXT NOT NULL CHECK (data_type IN ('spot', 'options', 'futures')),
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    last_price REAL,
    volume INTEGER,
    adv REAL,  -- Average Daily Volume
    intraday_return REAL,
    volume_ratio REAL,
    options_data TEXT,  -- JSON com dados de opções se data_type='options'
    raw_data TEXT,  -- JSON com dados brutos completos
    source TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('simulation', 'real')),  -- Origem dos dados
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_market_data_ticker ON market_data_captures (ticker);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data_captures (timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_type ON market_data_captures (data_type);
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
    close_price REAL,
    realized_pnl REAL,
    source TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('simulation', 'real')),  -- Origem dos dados
    UNIQUE(symbol, side, opened_at)
);
CREATE INDEX IF NOT EXISTS idx_open_positions_symbol ON open_positions (symbol);
CREATE INDEX IF NOT EXISTS idx_open_positions_opened_at ON open_positions (opened_at);

-- Tabela de aprovações de propostas via Telegram
CREATE TABLE IF NOT EXISTS proposal_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('APPROVE', 'CANCEL')),
    timestamp TEXT NOT NULL,
    telegram_chat_id TEXT,
    telegram_message_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);
CREATE INDEX IF NOT EXISTS idx_proposal_approvals_proposal_id ON proposal_approvals (proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_approvals_timestamp ON proposal_approvals (timestamp);

-- Tabela para armazenar todas as mensagens enviadas via Telegram (rastreabilidade)
CREATE TABLE IF NOT EXISTS telegram_messages_sent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'telegram',
    message_type TEXT NOT NULL CHECK (message_type IN ('status', 'proposal', 'opportunity', 'error', 'kill_switch', 'market_open', 'market_close', 'eod', 'health', 'other')),
    title TEXT,
    message_text TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('critical', 'high', 'normal', 'low')),
    proposal_id TEXT,  -- Se relacionado a uma proposta
    success INTEGER NOT NULL DEFAULT 1 CHECK (success IN (0, 1)),  -- 1 = enviado com sucesso, 0 = falhou
    error_message TEXT,  -- Se falhou, guardar erro
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_telegram_messages_timestamp ON telegram_messages_sent (timestamp);
CREATE INDEX IF NOT EXISTS idx_telegram_messages_type ON telegram_messages_sent (message_type);
CREATE INDEX IF NOT EXISTS idx_telegram_messages_proposal_id ON telegram_messages_sent (proposal_id);
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
    _migrate_database()


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
            created_at_b3 = get_b3_timestamp()
            
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO proposals 
                    (proposal_id, timestamp, strategy, instrument_type, symbol, 
                     side, quantity, price, order_type, metadata, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal.get('proposal_id'),
                    proposal.get('timestamp', get_b3_timestamp()),
                    proposal.get('strategy', 'unknown'),
                    proposal.get('instrument_type', 'unknown'),
                    proposal.get('symbol', ''),
                    proposal.get('side', 'BUY'),
                    proposal.get('quantity', 0),
                    proposal.get('price', 0),
                    proposal.get('order_type', 'LIMIT'),
                    json.dumps(proposal.get('metadata', {})),
                    proposal.get('source', 'real'),  # 'simulation' ou 'real'
                    created_at_b3
                ))
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar proposta: {e}")
            return False
    
    def save_risk_evaluation(self, evaluation: Dict) -> bool:
        """Salva avaliação do RiskAgent."""
        try:
            created_at_b3 = get_b3_timestamp()
            
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO risk_evaluations 
                    (proposal_id, timestamp, decision, reason, details, 
                     modified_quantity, modified_price, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    evaluation.get('proposal_id'),
                    evaluation.get('timestamp', get_b3_timestamp()),
                    evaluation.get('decision', 'REJECT'),
                    evaluation.get('reason', ''),
                    json.dumps(evaluation.get('details', {})),
                    evaluation.get('modified_quantity'),
                    evaluation.get('modified_price'),
                    evaluation.get('source', 'real'),  # 'simulation' ou 'real'
                    created_at_b3
                ))
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar avaliação de risco: {e}")
            return False
    
    def save_execution(self, execution: Dict) -> bool:
        """Salva execução simulada."""
        try:
            created_at_b3 = get_b3_timestamp()
            
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO executions 
                    (order_id, proposal_id, timestamp, symbol, side, quantity, 
                     price, market_price, slippage, commission, notional, 
                     total_cost, status, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.get('order_id') or execution.get('fill_id'),
                    execution.get('proposal_id', ''),
                    execution.get('timestamp', get_b3_timestamp()),
                    execution.get('symbol', ''),
                    execution.get('side', 'BUY'),
                    execution.get('quantity', 0),
                    execution.get('price', 0),
                    execution.get('market_price'),
                    execution.get('slippage', 0),
                    execution.get('commission', 0),
                    execution.get('notional', 0),
                    execution.get('total_cost', 0),
                    execution.get('status', 'FILLED'),
                    execution.get('source', 'real'),  # 'simulation' ou 'real'
                    created_at_b3
                ))
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar execução: {e}")
            return False
    
    def save_performance_snapshot(self, snapshot: Dict) -> bool:
        """Salva snapshot de performance (backtest em tempo real)."""
        try:
            created_at_b3 = get_b3_timestamp()
            
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO performance_snapshots 
                    (timestamp, nav, total_pnl, daily_pnl, total_trades, 
                     winning_trades, losing_trades, open_positions, 
                     total_delta, total_gamma, total_vega, portfolio_value, 
                     cash, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.get('timestamp', get_b3_timestamp()),
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
                    json.dumps(snapshot.get('details', {})),
                    created_at_b3
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
    
    def save_market_data_capture(self, ticker: str, data_type: str, spot_data: Dict = None, options_data: List[Dict] = None, raw_data: Dict = None, source: str = 'real'):
        """Salva dados de mercado capturados para rastreabilidade."""
        try:
            # Usar timezone de São Paulo (B3)
            timestamp = get_b3_timestamp()
            
            # Preparar dados
            open_price = spot_data.get('open') if spot_data else None
            high_price = spot_data.get('high') if spot_data else None
            low_price = spot_data.get('low') if spot_data else None
            close_price = spot_data.get('close') if spot_data else None
            last_price = spot_data.get('last') if spot_data else None
            volume = spot_data.get('volume') if spot_data else None
            adv = spot_data.get('adv') if spot_data else None
            intraday_return = spot_data.get('intraday_return') if spot_data else None
            volume_ratio = spot_data.get('volume_ratio') if spot_data else None
            
            # Converter Timestamps e outros objetos não serializáveis para strings
            def json_serializer(obj):
                """Serializador customizado para objetos não JSON nativos."""
                if isinstance(obj, (pd.Timestamp, datetime)):
                    return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
                elif isinstance(obj, pd.Series):
                    return obj.to_dict()
                elif isinstance(obj, pd.DataFrame):
                    return obj.to_dict('records')
                elif hasattr(obj, 'to_dict'):
                    return obj.to_dict()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            try:
                options_json = json.dumps(options_data, default=json_serializer) if options_data else None
            except Exception as e:
                logger.warning(f"Erro ao serializar options_data: {e}")
                options_json = None
            
            try:
                raw_json = json.dumps(raw_data, default=json_serializer) if raw_data else None
            except Exception as e:
                logger.warning(f"Erro ao serializar raw_data: {e}")
                raw_json = None
            
            # Usar created_at com timezone B3
            created_at_b3 = get_b3_timestamp()
            
            with _connect() as conn:
                conn.execute("""
                    INSERT INTO market_data_captures 
                    (timestamp, ticker, data_type, open_price, high_price, low_price, close_price, 
                     last_price, volume, adv, intraday_return, volume_ratio, options_data, raw_data, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, ticker, data_type, open_price, high_price, low_price, close_price,
                    last_price, volume, adv, intraday_return, volume_ratio, options_json, raw_json, source, created_at_b3
                ))
        except Exception as e:
            logger.error(f"Erro ao salvar captura de dados de mercado: {e}")
    
    def get_market_data_captures(self, ticker: str = None, start_date: str = None, end_date: str = None, limit: int = None) -> pd.DataFrame:
        """Busca dados de mercado capturados."""
        try:
            with _connect() as conn:
                query = "SELECT * FROM market_data_captures WHERE 1=1"
                params = []
                
                if ticker:
                    query += " AND ticker = ?"
                    params.append(ticker)
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY timestamp DESC"
                
                if limit:
                    query += f" LIMIT {limit}"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                # Parse JSON fields
                if 'options_data' in df.columns:
                    df['options_data'] = df['options_data'].apply(lambda x: json.loads(x) if x else None)
                if 'raw_data' in df.columns:
                    df['raw_data'] = df['raw_data'].apply(lambda x: json.loads(x) if x else None)
                
                return df
        except Exception as e:
            logger.error(f"Erro ao buscar capturas de dados de mercado: {e}")
            return pd.DataFrame()
    
    def save_open_position(self, symbol: str, side: str, quantity: float, avg_price: float, 
                          current_price: float = None, delta: float = 0, gamma: float = 0, 
                          vega: float = 0, unrealized_pnl: float = 0):
        """Salva ou atualiza posição aberta."""
        try:
            timestamp = get_b3_timestamp()
            
            # Calcular PnL não realizado se não fornecido
            if unrealized_pnl == 0 and current_price:
                if side == 'BUY':
                    unrealized_pnl = (current_price - avg_price) * quantity
                else:
                    unrealized_pnl = (avg_price - current_price) * quantity
            
            with _connect() as conn:
                # Verificar se já existe posição aberta
                cursor = conn.execute("""
                    SELECT id, quantity, avg_price FROM open_positions 
                    WHERE symbol = ? AND side = ? AND closed_at IS NULL
                """, (symbol, side))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Atualizar posição existente (média ponderada)
                    old_qty = existing['quantity']
                    old_avg = existing['avg_price']
                    new_qty = old_qty + quantity
                    new_avg = ((old_qty * old_avg) + (quantity * avg_price)) / new_qty if new_qty > 0 else avg_price
                    
                    conn.execute("""
                        UPDATE open_positions 
                        SET quantity = ?, avg_price = ?, current_price = ?, 
                            unrealized_pnl = ?, delta = ?, gamma = ?, vega = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (new_qty, new_avg, current_price, unrealized_pnl, delta, gamma, vega, timestamp, existing['id']))
                else:
                    # Criar nova posição
                    conn.execute("""
                        INSERT INTO open_positions 
                        (symbol, side, quantity, avg_price, current_price, unrealized_pnl, 
                         delta, gamma, vega, opened_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (symbol, side, quantity, avg_price, current_price, unrealized_pnl, 
                          delta, gamma, vega, timestamp))
        except Exception as e:
            logger.error(f"Erro ao salvar posição aberta: {e}")
    
    def get_open_positions(self) -> pd.DataFrame:
        """Busca posições abertas."""
        try:
            with _connect() as conn:
                query = "SELECT * FROM open_positions WHERE closed_at IS NULL ORDER BY opened_at DESC"
                return pd.read_sql_query(query, conn)
        except Exception as e:
            logger.error(f"Erro ao buscar posições abertas: {e}")
            return pd.DataFrame()
    
    def close_position(self, position_id: int, close_price: float, realized_pnl: float = None) -> bool:
        """Fecha uma posição aberta (EOD - End of Day)."""
        try:
            timestamp = get_b3_timestamp()
            
            with _connect() as conn:
                # Buscar posição
                cursor = conn.execute("""
                    SELECT * FROM open_positions WHERE id = ? AND closed_at IS NULL
                """, (position_id,))
                
                position = cursor.fetchone()
                if not position:
                    logger.warning(f"Posição {position_id} não encontrada ou já fechada")
                    return False
                
                # Calcular PnL realizado se não fornecido
                if realized_pnl is None:
                    if position['side'] == 'BUY':
                        realized_pnl = (close_price - position['avg_price']) * position['quantity']
                    else:
                        realized_pnl = (position['avg_price'] - close_price) * position['quantity']
                
                # Fechar posição
                conn.execute("""
                    UPDATE open_positions 
                    SET closed_at = ?, close_price = ?, realized_pnl = ?
                    WHERE id = ?
                """, (timestamp, close_price, realized_pnl, position_id))
                
                conn.commit()
                logger.info(f"Posição {position_id} fechada EOD: {position['symbol']} @ {close_price:.2f}, PnL: {realized_pnl:.2f}")
                return True
        except Exception as e:
            logger.error(f"Erro ao fechar posição {position_id}: {e}")
            return False
    
    def close_all_daytrade_positions(self, current_price_func=None) -> int:
        """Fecha todas as posições abertas de daytrade (EOD)."""
        try:
            open_positions = self.get_open_positions()
            if open_positions.empty:
                logger.info("Nenhuma posição aberta para fechar")
                return 0
            
            closed_count = 0
            
            for idx, position in open_positions.iterrows():
                try:
                    symbol = position['symbol']
                    
                    # Buscar preço atual se função fornecida
                    if current_price_func:
                        close_price = current_price_func(symbol)
                    else:
                        # Usar preço atual da posição como fallback
                        close_price = position.get('current_price', position['avg_price'])
                    
                    if close_price and close_price > 0:
                        if self.close_position(position['id'], close_price):
                            closed_count += 1
                    else:
                        logger.warning(f"Não foi possível obter preço de fechamento para {symbol}")
                except Exception as e:
                    logger.error(f"Erro ao fechar posição {position.get('id', 'N/A')}: {e}")
                    continue
            
            logger.info(f"Fechamento EOD: {closed_count} de {len(open_positions)} posições fechadas")
            return closed_count
        except Exception as e:
            logger.error(f"Erro ao fechar todas as posições EOD: {e}")
            return 0
    
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
    
    def update_proposal_status(self, proposal_id: str, status: str) -> bool:
        """Atualiza o status de uma proposta.
        
        Args:
            proposal_id: ID da proposta
            status: Novo status ('gerada', 'enviada', 'aprovada', 'cancelada')
        """
        try:
            if status not in ['gerada', 'enviada', 'aprovada', 'cancelada']:
                logger.error(f"Status inválido: {status}")
                return False
            
            updated_at = get_b3_timestamp()
            
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE proposals 
                    SET status = ?, status_updated_at = ?
                    WHERE proposal_id = ?
                """, (status, updated_at, proposal_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Status da proposta {proposal_id} atualizado para '{status}'")
                    return True
                else:
                    logger.warning(f"Proposta {proposal_id} não encontrada para atualização")
                    return False
        except Exception as e:
            logger.error(f"Erro ao atualizar status da proposta {proposal_id}: {e}")
            return False
    
    def get_proposals_by_status(self, status: str = None) -> pd.DataFrame:
        """Busca propostas filtradas por status.
        
        Args:
            status: Status para filtrar ('gerada', 'enviada', 'aprovada', 'cancelada')
                   Se None, retorna todas
        """
        try:
            with _connect() as conn:
                query = "SELECT * FROM proposals WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY created_at DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if 'metadata' in df.columns:
                    df['metadata'] = df['metadata'].apply(lambda x: json.loads(x) if x else {})
                
                return df
        except Exception as e:
            logger.error(f"Erro ao buscar propostas por status: {e}")
            return pd.DataFrame()
    
    def save_telegram_message(self, message_text: str, message_type: str = 'other', title: str = None, 
                              priority: str = 'normal', proposal_id: str = None, success: bool = True, 
                              error_message: str = None, channel: str = 'telegram'):
        """Salva mensagem enviada via Telegram para rastreabilidade.
        
        Args:
            message_text: Texto da mensagem enviada
            message_type: Tipo da mensagem ('status', 'proposal', 'opportunity', 'error', 'kill_switch', 'market_open', 'market_close', 'eod', 'health', 'other')
            title: Título da mensagem (opcional)
            priority: Prioridade ('critical', 'high', 'normal', 'low')
            proposal_id: ID da proposta relacionada (se aplicável)
            success: Se a mensagem foi enviada com sucesso
            error_message: Mensagem de erro (se falhou)
            channel: Canal usado ('telegram', 'discord', etc.)
        """
        try:
            timestamp = get_b3_timestamp()
            
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO telegram_messages_sent 
                    (timestamp, channel, message_type, title, message_text, priority, proposal_id, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    channel,
                    message_type,
                    title,
                    message_text,
                    priority,
                    proposal_id,
                    1 if success else 0,
                    error_message
                ))
                conn.commit()
                logger.debug(f"Mensagem Telegram salva: {message_type} - {title or 'Sem título'}")
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem Telegram: {e}")
            return False
    
    def get_telegram_messages(self, start_date: str = None, end_date: str = None, 
                              message_type: str = None, limit: int = None) -> pd.DataFrame:
        """Busca mensagens Telegram enviadas.
        
        Args:
            start_date: Data inicial (formato 'YYYY-MM-DD HH:MM:SS')
            end_date: Data final (formato 'YYYY-MM-DD HH:MM:SS')
            message_type: Filtrar por tipo de mensagem
            limit: Limite de resultados
        """
        try:
            with _connect() as conn:
                query = "SELECT * FROM telegram_messages_sent WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                if message_type:
                    query += " AND message_type = ?"
                    params.append(message_type)
                
                query += " ORDER BY timestamp DESC"
                
                if limit:
                    query += f" LIMIT {limit}"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens Telegram: {e}")
            return pd.DataFrame()

