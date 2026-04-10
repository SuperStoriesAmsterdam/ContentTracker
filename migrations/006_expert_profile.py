"""
Migration 006: Add expert_profiles and transcripts tables.
These tables power the Expert Profile feature in v4.
expert_profiles stores structured intelligence extracted from transcripts.
transcripts stores raw transcript text and extraction results.
"""

def upgrade(conn):
    """Execute migration."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expert_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            core_beliefs TEXT DEFAULT '[]',
            personal_stories TEXT DEFAULT '[]',
            contrarian_positions TEXT DEFAULT '[]',
            signature_phrases TEXT DEFAULT '[]',
            topics_of_passion TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            source TEXT,
            raw_text TEXT NOT NULL,
            extraction_status TEXT DEFAULT 'pending',
            extracted_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    conn.commit()
