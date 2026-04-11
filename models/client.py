import json
import bcrypt
from models.database import get_db_connection

class Client:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.password = kwargs.get('password')
        self.tone = kwargs.get('tone')
        self.key_phrases = self._parse_json(kwargs.get('key_phrases', '[]'))
        self.forbidden_words = self._parse_json(kwargs.get('forbidden_words', '[]'))
        self.target_audience = kwargs.get('target_audience')
        self.core_keywords = self._parse_json(kwargs.get('core_keywords', '[]'))
        self.competitive_differentiation = kwargs.get('competitive_differentiation')
        self.linkedin_guidelines = kwargs.get('linkedin_guidelines')
        self.instagram_guidelines = kwargs.get('instagram_guidelines')
        self.is_thought_leadership = bool(kwargs.get('is_thought_leadership', 0))
        self.author_name = kwargs.get('author_name')
        self.entity_statement = kwargs.get('entity_statement')
        self.search_console_site = kwargs.get('search_console_site')
        self.analytics_property_id = kwargs.get('analytics_property_id')
        self.google_credentials = kwargs.get('google_credentials')
        self.created_at = kwargs.get('created_at')
    
    def _parse_json(self, value):
        """Safely parse JSON or return list from string."""
        if not value:
            return []
        if isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Try splitting by newline
            if isinstance(value, str):
                return [item.strip() for item in value.split('\n') if item.strip()]
            return []
    
    def get_brand_voice_section(self):
        """Build brand voice section for prompts."""
        sections = []
        if self.tone:
            sections.append(f"**Tone:** {self.tone}")
        if self.key_phrases:
            sections.append(f"**Key Phrases to use:** {', '.join(self.key_phrases)}")
        if self.forbidden_words:
            sections.append(f"**Words to AVOID:** {', '.join(self.forbidden_words)}")
        if self.target_audience:
            sections.append(f"**Target Audience:** {self.target_audience}")
        return '\n'.join(sections) if sections else "Use professional, clear language."
    
    def save(self):
        """Save or update client in database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        key_phrases_json = json.dumps(self.key_phrases) if self.key_phrases else '[]'
        forbidden_words_json = json.dumps(self.forbidden_words) if self.forbidden_words else '[]'
        core_keywords_json = json.dumps(self.core_keywords) if self.core_keywords else '[]'
        
        if self.id:
            cursor.execute('''
                UPDATE clients SET
                    name = ?, password = ?, tone = ?, key_phrases = ?,
                    forbidden_words = ?, target_audience = ?, core_keywords = ?,
                    competitive_differentiation = ?, linkedin_guidelines = ?,
                    instagram_guidelines = ?, is_thought_leadership = ?,
                    author_name = ?, entity_statement = ?, search_console_site = ?,
                    analytics_property_id = ?, google_credentials = ?
                WHERE id = ?
            ''', (self.name, self.password, self.tone, key_phrases_json,
                  forbidden_words_json, self.target_audience, core_keywords_json,
                  self.competitive_differentiation, self.linkedin_guidelines,
                  self.instagram_guidelines, int(self.is_thought_leadership),
                  self.author_name, self.entity_statement, self.search_console_site,
                  self.analytics_property_id, self.google_credentials, self.id))
        else:
            cursor.execute('''
                INSERT INTO clients (name, password, tone, key_phrases, forbidden_words,
                    target_audience, core_keywords, competitive_differentiation,
                    linkedin_guidelines, instagram_guidelines, is_thought_leadership,
                    author_name, entity_statement, search_console_site,
                    analytics_property_id, google_credentials)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.name, self.password, self.tone, key_phrases_json,
                  forbidden_words_json, self.target_audience, core_keywords_json,
                  self.competitive_differentiation, self.linkedin_guidelines,
                  self.instagram_guidelines, int(self.is_thought_leadership),
                  self.author_name, self.entity_statement, self.search_console_site,
                  self.analytics_property_id, self.google_credentials))
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self
    
    def delete(self):
        """Delete client from database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clients WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all():
        """Get all clients."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        return [Client(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(client_id):
        """Get client by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
        row = cursor.fetchone()
        conn.close()
        return Client(**dict(row)) if row else None
    
    @staticmethod
    def hash_password(plaintext_password):
        """Hash a plaintext password with bcrypt. Returns a string."""
        hashed = bcrypt.hashpw(plaintext_password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plaintext_password, stored_hash):
        """Check a plaintext password against a stored bcrypt hash."""
        if not stored_hash:
            return False
        return bcrypt.checkpw(
            plaintext_password.encode('utf-8'),
            stored_hash.encode('utf-8')
        )

    @staticmethod
    def get_by_name(name):
        """Get client by name."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        return Client(**dict(row)) if row else None
