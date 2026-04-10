"""
Migration 002: Document Library with RAG support
Add this file to your migrations/ folder
"""

MIGRATION_SQL = """
-- Documents table (uploaded PDFs, DOCX, etc.)
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    title TEXT,
    description TEXT,
    doc_type TEXT DEFAULT 'knowledge',  -- 'knowledge', 'style', 'both'
    total_chunks INTEGER DEFAULT 0,
    is_embedded INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Document chunks for RAG retrieval
CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    token_count INTEGER,
    embedding_id TEXT,  -- Reference to vector store
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_client ON documents(client_id);
"""

def upgrade(conn):
    """Execute migration"""
    cursor = conn.cursor()
    cursor.executescript(MIGRATION_SQL)
    conn.commit()
