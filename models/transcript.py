"""
Transcript model — stores raw transcript text and the JSON result of Claude extraction.
extraction_status values: 'pending' | 'extracted' | 'approved'
"""

import json
from models.database import get_db_connection


class Transcript:
    def __init__(self, id=None, client_id=None, title=None, source=None,
                 raw_text=None, extraction_status='pending',
                 extracted_json=None, created_at=None):
        self.id = id
        self.client_id = client_id
        self.title = title
        self.source = source
        self.raw_text = raw_text
        self.extraction_status = extraction_status
        self.created_at = created_at

        # extracted_json is stored as a JSON string in the database.
        # When accessed, parse it into a Python dict.
        if isinstance(extracted_json, dict):
            self.extracted_json = extracted_json
        elif extracted_json:
            self.extracted_json = json.loads(extracted_json)
        else:
            self.extracted_json = None

    def save(self):
        """Save or update the transcript record."""
        conn = get_db_connection()
        cursor = conn.cursor()

        extracted_json_str = json.dumps(self.extracted_json) if self.extracted_json else None

        if self.id:
            cursor.execute("""
                UPDATE transcripts SET
                    title = ?,
                    source = ?,
                    raw_text = ?,
                    extraction_status = ?,
                    extracted_json = ?
                WHERE id = ?
            """, (self.title, self.source, self.raw_text,
                  self.extraction_status, extracted_json_str, self.id))
        else:
            cursor.execute("""
                INSERT INTO transcripts
                    (client_id, title, source, raw_text, extraction_status, extracted_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.client_id, self.title, self.source, self.raw_text,
                  self.extraction_status, extracted_json_str))
            self.id = cursor.lastrowid

        conn.commit()
        conn.close()
        return self

    def delete(self):
        """Delete this transcript."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transcripts WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(transcript_id):
        """Get a transcript by its ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transcripts WHERE id = ?", (transcript_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Transcript(**dict(row))
        return None

    @staticmethod
    def get_by_client(client_id):
        """Get all transcripts for a client, newest first."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM transcripts
            WHERE client_id = ?
            ORDER BY created_at DESC
        """, (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Transcript(**dict(row)) for row in rows]

    def get_all_extracted_items(self):
        """
        Return all extracted items as a flat list for card-by-card review.
        Each item includes its category so the review UI can label it correctly.
        """
        if not self.extracted_json:
            return []

        items = []

        for belief in self.extracted_json.get('core_beliefs', []):
            items.append({
                'category': 'core_beliefs',
                'category_label': 'Core Belief',
                'text': belief.get('text', ''),
                'confidence': belief.get('confidence', ''),
                'raw': belief
            })

        for story in self.extracted_json.get('personal_stories', []):
            items.append({
                'category': 'personal_stories',
                'category_label': 'Personal Story',
                'text': f"{story.get('title', '')}: {story.get('summary', '')}",
                'title': story.get('title', ''),
                'summary': story.get('summary', ''),
                'raw': story
            })

        for position in self.extracted_json.get('contrarian_positions', []):
            items.append({
                'category': 'contrarian_positions',
                'category_label': 'Contrarian Position',
                'text': position.get('text', ''),
                'confidence': position.get('confidence', ''),
                'raw': position
            })

        for phrase in self.extracted_json.get('signature_phrases', []):
            items.append({
                'category': 'signature_phrases',
                'category_label': 'Signature Phrase',
                'text': phrase.get('phrase', ''),
                'context': phrase.get('context', ''),
                'raw': phrase
            })

        for topic in self.extracted_json.get('topics_of_passion', []):
            items.append({
                'category': 'topics_of_passion',
                'category_label': 'Topic of Passion',
                'text': topic.get('topic', ''),
                'raw': topic
            })

        return items
