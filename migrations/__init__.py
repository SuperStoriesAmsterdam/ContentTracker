import sqlite3
import os
import importlib

def run_migrations(db_path):
    """Run all pending migrations."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create migrations tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    # Get applied migrations
    cursor.execute('SELECT name FROM _migrations')
    applied = {row[0] for row in cursor.fetchall()}
    
    # Get migration files
    migrations_dir = os.path.dirname(__file__)
    migration_files = sorted([
        f[:-3] for f in os.listdir(migrations_dir)
        if f.endswith('.py') and f[0].isdigit()
    ])
    
    # Apply new migrations
    for migration_name in migration_files:
        if migration_name in applied:
            continue
        
        print(f"  Applying migration: {migration_name}")
        
        # Import and run migration
        module = importlib.import_module(f'migrations.{migration_name}')
        module.upgrade(conn)
        
        # Record migration (OR IGNORE prevents crash when multiple workers race)
        cursor.execute('INSERT OR IGNORE INTO _migrations (name) VALUES (?)', (migration_name,))
        conn.commit()
        
        print(f"  ✓ Applied {migration_name}")
    
    conn.close()
