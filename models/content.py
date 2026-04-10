import json
from models.database import get_db_connection

class Content:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.brief_id = kwargs.get('brief_id')
        self.client_id = kwargs.get('client_id')
        self.content_type = kwargs.get('content_type')
        self.meta_title = kwargs.get('meta_title')
        self.meta_description = kwargs.get('meta_description')
        self.h1 = kwargs.get('h1')
        self.body = kwargs.get('body')
        self.internal_links_suggested = self._parse_json(kwargs.get('internal_links_suggested', '[]'))
        self.schema_json = kwargs.get('schema_json')
        self.quotable_snippet = kwargs.get('quotable_snippet')  # NEW: For LLM citation
        self.published_url = kwargs.get('published_url')
        self.google_doc_id = kwargs.get('google_doc_id')
        self.google_doc_url = kwargs.get('google_doc_url')
        self.final_content = kwargs.get('final_content')
        self.search_console_data = kwargs.get('search_console_data')
        self.last_performance_fetch = kwargs.get('last_performance_fetch')
        self.created_at = kwargs.get('created_at')
    
    def _parse_json(self, value):
        """Safely parse JSON."""
        if not value:
            return []
        if isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def get_full_markdown(self):
        """Get full content as markdown."""
        parts = []
        if self.meta_title:
            parts.append(f"META_TITLE: {self.meta_title}")
        if self.meta_description:
            parts.append(f"META_DESCRIPTION: {self.meta_description}")
        if parts:
            parts.append("---")
        if self.h1:
            parts.append(f"# {self.h1}")
        if self.body:
            parts.append(self.body)
        if self.internal_links_suggested:
            parts.append("---")
            parts.append(f"INTERNAL_LINKS_SUGGESTED: {', '.join(self.internal_links_suggested)}")
        return '\n\n'.join(parts)
    
    def get_plain_text(self):
        """Get content as plain text (strip markdown)."""
        import re
        text = self.body or ''
        # Remove markdown formatting
        text = re.sub(r'#+\s*', '', text)  # Headers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
        return text
    
    def save(self):
        """Save or update content in database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        internal_links_json = json.dumps(self.internal_links_suggested)
        
        if self.id:
            cursor.execute('''
                UPDATE generated_content SET
                    brief_id = ?, client_id = ?, content_type = ?, meta_title = ?,
                    meta_description = ?, h1 = ?, body = ?, internal_links_suggested = ?,
                    schema_json = ?, quotable_snippet = ?, published_url = ?, google_doc_id = ?,
                    google_doc_url = ?, final_content = ?, search_console_data = ?,
                    last_performance_fetch = ?
                WHERE id = ?
            ''', (self.brief_id, self.client_id, self.content_type, self.meta_title,
                  self.meta_description, self.h1, self.body, internal_links_json,
                  self.schema_json, self.quotable_snippet, self.published_url, self.google_doc_id,
                  self.google_doc_url, self.final_content, self.search_console_data,
                  self.last_performance_fetch, self.id))
        else:
            cursor.execute('''
                INSERT INTO generated_content (brief_id, client_id, content_type,
                    meta_title, meta_description, h1, body, internal_links_suggested,
                    schema_json, quotable_snippet, published_url, google_doc_id, google_doc_url,
                    final_content, search_console_data, last_performance_fetch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.brief_id, self.client_id, self.content_type, self.meta_title,
                  self.meta_description, self.h1, self.body, internal_links_json,
                  self.schema_json, self.quotable_snippet, self.published_url, self.google_doc_id,
                  self.google_doc_url, self.final_content, self.search_console_data,
                  self.last_performance_fetch))
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self
    
    def delete(self):
        """Delete content from database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM generated_content WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_brief(brief_id):
        """Get all content for a brief."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM generated_content WHERE brief_id = ? ORDER BY created_at DESC', (brief_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Content(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_client(client_id, limit=20):
        """Get recent content for a client."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM generated_content WHERE client_id = ? ORDER BY created_at DESC LIMIT ?',
            (client_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [Content(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(content_id):
        """Get content by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM generated_content WHERE id = ?', (content_id,))
        row = cursor.fetchone()
        conn.close()
        return Content(**dict(row)) if row else None
