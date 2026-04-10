"""
Migration 005: Add google_credentials column to clients table
Persists Google OAuth credentials so they survive server restarts.
"""

def upgrade(conn):
    """Execute migration."""
    import sqlite3
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE clients ADD COLUMN google_credentials TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            pass

    conn.commit()
