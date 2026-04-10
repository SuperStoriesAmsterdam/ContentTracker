"""
Migration 004: V3 Fields - Answer targets, Thought Leadership, Content Tracks
"""

def upgrade(conn):
    """Execute migration."""
    import sqlite3
    cursor = conn.cursor()
    
    brief_columns = [
        ("briefs", "content_track", "TEXT DEFAULT 'seo'"),
        ("briefs", "answer_target", "TEXT"),
        ("briefs", "core_thesis", "TEXT"),
        ("briefs", "contrarian_angle", "TEXT"),
        ("briefs", "personal_story_prompt", "TEXT"),
        ("briefs", "emotional_intent", "TEXT"),
        ("briefs", "call_to_think", "TEXT"),
    ]
    
    client_columns = [
        ("clients", "author_name", "TEXT"),
        ("clients", "search_console_site", "TEXT"),
        ("clients", "analytics_property_id", "TEXT"),
    ]
    
    document_columns = [
        ("documents", "content_track", "TEXT DEFAULT 'both'"),
    ]
    
    content_columns = [
        ("generated_content", "quotable_snippet", "TEXT"),
    ]
    
    all_columns = brief_columns + client_columns + document_columns + content_columns
    
    for table, column, col_type in all_columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                pass
    
    conn.commit()
