from models.database import get_db_connection

class VoiceSnippet:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.client_id = kwargs.get('client_id')
        self.title = kwargs.get('title')
        self.source = kwargs.get('source')
        self.transcript = kwargs.get('transcript')
        self.created_at = kwargs.get('created_at')
    
    def get_preview(self, max_chars=200):
        """Get preview of transcript."""
        if not self.transcript:
            return ""
        if len(self.transcript) <= max_chars:
            return self.transcript
        return self.transcript[:max_chars] + "..."
    
    def save(self):
        """Save or update voice snippet in database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if self.id:
            cursor.execute('''
                UPDATE voice_snippets SET
                    client_id = ?, title = ?, source = ?, transcript = ?
                WHERE id = ?
            ''', (self.client_id, self.title, self.source, self.transcript, self.id))
        else:
            cursor.execute('''
                INSERT INTO voice_snippets (client_id, title, source, transcript)
                VALUES (?, ?, ?, ?)
            ''', (self.client_id, self.title, self.source, self.transcript))
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self
    
    def delete(self):
        """Delete voice snippet from database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM brief_voice_snippets WHERE voice_snippet_id = ?', (self.id,))
        cursor.execute('DELETE FROM voice_snippets WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_client(client_id):
        """Get all voice snippets for a client."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM voice_snippets WHERE client_id = ? ORDER BY created_at DESC', (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return [VoiceSnippet(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(snippet_id):
        """Get voice snippet by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM voice_snippets WHERE id = ?', (snippet_id,))
        row = cursor.fetchone()
        conn.close()
        return VoiceSnippet(**dict(row)) if row else None
    
    @staticmethod
    def get_by_ids(snippet_ids):
        """Get multiple voice snippets by IDs."""
        if not snippet_ids:
            return []
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(snippet_ids))
        cursor.execute(f'SELECT * FROM voice_snippets WHERE id IN ({placeholders})', snippet_ids)
        rows = cursor.fetchall()
        conn.close()
        return [VoiceSnippet(**dict(row)) for row in rows]
