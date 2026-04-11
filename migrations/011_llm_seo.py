"""
Migration 011: Add entity_statement to clients table.
Used for LLM SEO — a definitive sentence that identifies the expert,
included in all content briefs to strengthen AI citation.
"""

def upgrade(conn):
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE clients ADD COLUMN entity_statement TEXT")
    conn.commit()
