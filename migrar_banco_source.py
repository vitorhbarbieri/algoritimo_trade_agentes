#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para adicionar coluna 'source' nas tabelas existentes."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents_orders.db")

def migrate_database():
    """Adiciona coluna 'source' nas tabelas que não a possuem."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Lista de tabelas e suas colunas source
        tables_to_migrate = [
            ('proposals', 'source'),
            ('risk_evaluations', 'source'),
            ('executions', 'source'),
            ('market_data_captures', 'source'),
            ('open_positions', 'source')
        ]
        
        print("Iniciando migração do banco de dados...")
        
        for table_name, column_name in tables_to_migrate:
            try:
                # Verificar se a coluna já existe
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if column_name not in columns:
                    print(f"  Adicionando coluna '{column_name}' na tabela '{table_name}'...")
                    cursor.execute(f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN {column_name} TEXT NOT NULL DEFAULT 'real' 
                        CHECK ({column_name} IN ('simulation', 'real'))
                    """)
                    print(f"    ✓ Coluna '{column_name}' adicionada com sucesso!")
                else:
                    print(f"  ✓ Coluna '{column_name}' já existe na tabela '{table_name}'")
            except sqlite3.OperationalError as e:
                print(f"  ✗ Erro ao adicionar coluna '{column_name}' em '{table_name}': {e}")
        
        conn.commit()
        print("\nMigração concluída com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"\nErro durante migração: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()

