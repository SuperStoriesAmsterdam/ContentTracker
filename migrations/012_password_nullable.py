"""
Migration 012: Make password nullable on clients table.
Password is per user (future), not per client.
"""

def upgrade(conn):
    cursor = conn.cursor()
    # SQLite doesn't support ALTER COLUMN, so we need to recreate
    # But we can work around NOT NULL by setting a default
    # For existing rows, password already has a value
    # For new rows, we'll handle NULL in the application
    # The simplest fix: create a new table without NOT NULL and copy data
    cursor.execute("PRAGMA table_info(clients)")
    columns = cursor.fetchall()

    # Check if we need to do anything
    for col in columns:
        if col[1] == 'password' and col[3] == 1:  # notnull = 1
            # Need to fix - recreate table
            cursor.execute("ALTER TABLE clients RENAME TO clients_old")
            cursor.execute('''
                CREATE TABLE clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    password TEXT,
                    tone TEXT,
                    key_phrases TEXT,
                    forbidden_words TEXT,
                    target_audience TEXT,
                    core_keywords TEXT,
                    competitive_differentiation TEXT,
                    linkedin_guidelines TEXT,
                    instagram_guidelines TEXT,
                    is_thought_leadership INTEGER DEFAULT 0,
                    author_name TEXT,
                    entity_statement TEXT,
                    search_console_site TEXT,
                    analytics_property_id TEXT,
                    google_credentials TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                INSERT INTO clients SELECT
                    id, name, password, tone, key_phrases, forbidden_words,
                    target_audience, core_keywords, competitive_differentiation,
                    linkedin_guidelines, instagram_guidelines, is_thought_leadership,
                    author_name, entity_statement, search_console_site,
                    analytics_property_id, google_credentials, created_at
                FROM clients_old
            ''')
            cursor.execute("DROP TABLE clients_old")
            break
    conn.commit()
