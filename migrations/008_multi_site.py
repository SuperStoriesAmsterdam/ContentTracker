"""
Migration 008: Add sites table.
Supports multiple websites per client for combined GSC dashboards.
One client (e.g. Connirae Andreas) may operate five websites simultaneously.
"""

def upgrade(conn):
    """Execute migration."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            name TEXT,
            gsc_property TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    conn.commit()
