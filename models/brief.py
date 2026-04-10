import json
from models.database import get_db_connection

class Brief:
    CONTENT_TYPES = [
        ('seo_article', 'SEO Article'),
        ('landing_page', 'Landing Page'),
        ('press_release', 'Press Release'),
        ('product_description', 'Product Description'),
        ('faq', 'FAQ Page'),
        ('thought_leadership', 'Thought Leadership Essay')
    ]
    
    LANGUAGES = [
        ('nl', 'Nederlands'),
        ('en', 'English'),
        ('de', 'Deutsch')
    ]
    
    SEARCH_INTENTS = [
        ('informational', 'Informational - User wants to learn'),
        ('commercial', 'Commercial - User is researching options'),
        ('transactional', 'Transactional - User wants to buy'),
        ('navigational', 'Navigational - User looking for specific page')
    ]

    CONTENT_TRACKS = [
        ('seo', 'SEO'),
        ('thought_leadership', 'Thought Leadership')
    ]

    EMOTIONAL_INTENTS = [
        ('inspire', 'Inspire'),
        ('provoke', 'Provoke'),
        ('comfort', 'Comfort'),
        ('educate', 'Educate')
    ]

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.client_id = kwargs.get('client_id')
        self.title = kwargs.get('title')
        self.content_type = kwargs.get('content_type')
        self.language = kwargs.get('language', 'nl')
        self.primary_keyword = kwargs.get('primary_keyword')
        self.secondary_keywords = self._parse_json(kwargs.get('secondary_keywords', '[]'))
        self.target_icp = kwargs.get('target_icp')
        self.search_intent = kwargs.get('search_intent')
        self.word_count_target = kwargs.get('word_count_target', 1500)
        self.cta = kwargs.get('cta')
        self.must_include = self._parse_json(kwargs.get('must_include', '[]'))
        self.must_avoid = self._parse_json(kwargs.get('must_avoid', '[]'))
        self.special_instructions = kwargs.get('special_instructions')
        self.fresh_transcript = kwargs.get('fresh_transcript')
        self.content_track = kwargs.get('content_track', 'seo')
        self.answer_target = kwargs.get('answer_target')
        self.core_thesis = kwargs.get('core_thesis')
        self.contrarian_angle = kwargs.get('contrarian_angle')
        self.personal_story_prompt = kwargs.get('personal_story_prompt')
        self.emotional_intent = kwargs.get('emotional_intent')
        self.call_to_think = kwargs.get('call_to_think')
        self.created_at = kwargs.get('created_at')
        self._voice_snippet_ids = None
    
    def _parse_json(self, value):
        """Safely parse JSON or return list from string."""
        if not value:
            return []
        if isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            if isinstance(value, str):
                return [item.strip() for item in value.split('\n') if item.strip()]
            return []
    
    def get_language_display(self):
        """Get display name for language."""
        for code, name in self.LANGUAGES:
            if code == self.language:
                return name
        return self.language
    
    def get_content_type_display(self):
        """Get display name for content type."""
        for code, name in self.CONTENT_TYPES:
            if code == self.content_type:
                return name
        return self.content_type
    
    def get_voice_snippet_ids(self):
        """Get selected voice snippet IDs."""
        if self._voice_snippet_ids is not None:
            return self._voice_snippet_ids
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT voice_snippet_id FROM brief_voice_snippets WHERE brief_id = ?',
            (self.id,)
        )
        self._voice_snippet_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return self._voice_snippet_ids
    
    def set_voice_snippet_ids(self, snippet_ids):
        """Set voice snippet IDs (saves on save())."""
        self._voice_snippet_ids = snippet_ids or []
    
    def save(self):
        """Save or update brief in database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        secondary_keywords_json = json.dumps(self.secondary_keywords)
        must_include_json = json.dumps(self.must_include)
        must_avoid_json = json.dumps(self.must_avoid)
        
        if self.id:
            cursor.execute('''
                UPDATE briefs SET
                    client_id = ?, title = ?, content_type = ?, content_track = ?,
                    language = ?, primary_keyword = ?, secondary_keywords = ?,
                    target_icp = ?, search_intent = ?, word_count_target = ?, cta = ?,
                    must_include = ?, must_avoid = ?, special_instructions = ?,
                    fresh_transcript = ?, answer_target = ?, core_thesis = ?,
                    contrarian_angle = ?, personal_story_prompt = ?,
                    emotional_intent = ?, call_to_think = ?
                WHERE id = ?
            ''', (self.client_id, self.title, self.content_type, self.content_track,
                  self.language, self.primary_keyword, secondary_keywords_json,
                  self.target_icp, self.search_intent, self.word_count_target, self.cta,
                  must_include_json, must_avoid_json, self.special_instructions,
                  self.fresh_transcript, self.answer_target, self.core_thesis,
                  self.contrarian_angle, self.personal_story_prompt,
                  self.emotional_intent, self.call_to_think, self.id))
        else:
            cursor.execute('''
                INSERT INTO briefs (client_id, title, content_type, content_track,
                    language, primary_keyword, secondary_keywords, target_icp,
                    search_intent, word_count_target, cta, must_include, must_avoid,
                    special_instructions, fresh_transcript, answer_target, core_thesis,
                    contrarian_angle, personal_story_prompt, emotional_intent,
                    call_to_think)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.client_id, self.title, self.content_type, self.content_track,
                  self.language, self.primary_keyword, secondary_keywords_json,
                  self.target_icp, self.search_intent, self.word_count_target, self.cta,
                  must_include_json, must_avoid_json, self.special_instructions,
                  self.fresh_transcript, self.answer_target, self.core_thesis,
                  self.contrarian_angle, self.personal_story_prompt,
                  self.emotional_intent, self.call_to_think))
            self.id = cursor.lastrowid
        
        # Save voice snippet associations
        if self._voice_snippet_ids is not None:
            cursor.execute('DELETE FROM brief_voice_snippets WHERE brief_id = ?', (self.id,))
            for snippet_id in self._voice_snippet_ids:
                cursor.execute(
                    'INSERT INTO brief_voice_snippets (brief_id, voice_snippet_id) VALUES (?, ?)',
                    (self.id, snippet_id)
                )
        
        conn.commit()
        conn.close()
        return self
    
    def delete(self):
        """Delete brief from database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM brief_voice_snippets WHERE brief_id = ?', (self.id,))
        cursor.execute('DELETE FROM briefs WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_client(client_id):
        """Get all briefs for a client."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM briefs WHERE client_id = ? ORDER BY created_at DESC', (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Brief(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(brief_id):
        """Get brief by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM briefs WHERE id = ?', (brief_id,))
        row = cursor.fetchone()
        conn.close()
        return Brief(**dict(row)) if row else None
