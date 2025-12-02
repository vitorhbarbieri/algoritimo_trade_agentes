"""
Script para adicionar colunas de status às propostas existentes no banco de dados.
"""
import sqlite3
import os
from pathlib import Path

DB_PATH = os.path.join(Path(__file__).parent, "agents_orders.db")

def migrar_banco():
    """Adiciona colunas de status ao banco de dados."""
    print("=" * 70)
    print("MIGRAÇÃO: Adicionando colunas de status às propostas")
    print("=" * 70)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se coluna já existe
        cursor.execute("PRAGMA table_info(proposals)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in columns:
            print("\n1. Adicionando coluna 'status'...")
            cursor.execute("""
                ALTER TABLE proposals 
                ADD COLUMN status TEXT DEFAULT 'gerada' 
                CHECK (status IN ('gerada', 'enviada', 'aprovada', 'cancelada'))
            """)
            print("   ✅ Coluna 'status' adicionada")
        else:
            print("\n1. Coluna 'status' já existe")
        
        if 'status_updated_at' not in columns:
            print("\n2. Adicionando coluna 'status_updated_at'...")
            cursor.execute("""
                ALTER TABLE proposals 
                ADD COLUMN status_updated_at TEXT
            """)
            print("   ✅ Coluna 'status_updated_at' adicionada")
        else:
            print("\n2. Coluna 'status_updated_at' já existe")
        
        # Atualizar propostas existentes sem status
        print("\n3. Atualizando propostas existentes...")
        cursor.execute("""
            UPDATE proposals 
            SET status = 'gerada', status_updated_at = created_at
            WHERE status IS NULL
        """)
        updated = cursor.rowcount
        print(f"   ✅ {updated} propostas atualizadas com status 'gerada'")
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    migrar_banco()

