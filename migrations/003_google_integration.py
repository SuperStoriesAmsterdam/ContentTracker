"""
Migration 003: Google Integration Fields
Add this file to your migrations/ folder
"""

MIGRATION_SQL = """
-- Add Search Console and Analytics fields to clients
ALTER TABLE clients ADD COLUMN search_console_site TEXT;
ALTER TABLE clients ADD COLUMN analytics_property_id TEXT;

-- Add published URL to content (for tracking performance)
ALTER TABLE content ADD COLUMN published_url TEXT;
"""

def upgrade(conn):
    """Execute migration"""
    cursor = conn.cursor()
    
    columns_to_add = [
        ("clients", "search_console_site", "TEXT"),
        ("clients", "analytics_property_id", "TEXT"),
        ("generated_content", "published_url", "TEXT")
    ]
    
    for table, column, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                pass
    
    conn.commit()
