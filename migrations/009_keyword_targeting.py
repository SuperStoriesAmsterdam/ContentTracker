"""
Migration 009: Add keyword_targets table.
Stores manually entered target keywords per client with zone assignment.
"""

def upgrade(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keyword_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            site_id INTEGER,
            keyword TEXT NOT NULL,
            zone INTEGER NOT NULL DEFAULT 3,
            notes TEXT,
            status TEXT DEFAULT 'tracking',
            last_seen_position REAL,
            last_seen_impressions INTEGER,
            last_checked_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)
    conn.commit()
