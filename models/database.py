import sqlite3
import os
from config import Config

def get_db_path():
    """Get the database file path."""
    return Config.DATABASE_PATH

def get_db_connection():
    """Get a database connection."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """Alias for get_db_connection for compatibility."""
    return get_db_connection()

def init_db():
    """Initialize the database with core tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Content briefs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content_type TEXT NOT NULL,
            language TEXT DEFAULT 'nl',
            primary_keyword TEXT,
            secondary_keywords TEXT,
            target_icp TEXT,
            search_intent TEXT,
            word_count_target INTEGER DEFAULT 1500,
            cta TEXT,
            must_include TEXT,
            must_avoid TEXT,
            special_instructions TEXT,
            fresh_transcript TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')
    
    # Brief-voice snippet junction table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS brief_voice_snippets (
            brief_id INTEGER NOT NULL,
            voice_snippet_id INTEGER NOT NULL,
            PRIMARY KEY (brief_id, voice_snippet_id),
            FOREIGN KEY (brief_id) REFERENCES briefs(id),
            FOREIGN KEY (voice_snippet_id) REFERENCES voice_snippets(id)
        )
    ''')
    
    # Generated content table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generated_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brief_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            meta_title TEXT,
            meta_description TEXT,
            h1 TEXT,
            body TEXT,
            internal_links_suggested TEXT,
            schema_json TEXT,
            published_url TEXT,
            google_doc_id TEXT,
            google_doc_url TEXT,
            final_content TEXT,
            search_console_data TEXT,
            last_performance_fetch TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brief_id) REFERENCES briefs(id),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')
    
    # Voice snippets table (Voice Bank)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            source TEXT,
            transcript TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')
    
    # Style resources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS style_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            resource_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')
    
    # Derived content table (social posts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS derived_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_content_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_content_id) REFERENCES generated_content(id),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')
    
    conn.commit()
    conn.close()
