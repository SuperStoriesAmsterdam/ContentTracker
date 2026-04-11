"""
Migration 010: Add gsc_snapshots table.
Stores weekly GSC performance snapshots for historical tracking.
"""

def upgrade(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gsc_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            site_url TEXT NOT NULL,
            keyword TEXT NOT NULL,
            position REAL,
            clicks INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            snapshot_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshots_client_keyword
        ON gsc_snapshots(client_id, keyword, snapshot_date)
    """)
    conn.commit()
