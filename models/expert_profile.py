"""
ExpertProfile model — stores structured intelligence about a thought leader.
Each client has one ExpertProfile. Fields are JSON arrays of extracted items.
Items are added by processing transcripts through the extraction flow.
"""

import json
from datetime import datetime
from models.database import get_db_connection


class ExpertProfile:
    def __init__(self, id=None, client_id=None, core_beliefs=None,
                 personal_stories=None, contrarian_positions=None,
                 signature_phrases=None, topics_of_passion=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.client_id = client_id
        self.core_beliefs = core_beliefs if isinstance(core_beliefs, list) else json.loads(core_beliefs or '[]')
        self.personal_stories = personal_stories if isinstance(personal_stories, list) else json.loads(personal_stories or '[]')
        self.contrarian_positions = contrarian_positions if isinstance(contrarian_positions, list) else json.loads(contrarian_positions or '[]')
        self.signature_phrases = signature_phrases if isinstance(signature_phrases, list) else json.loads(signature_phrases or '[]')
        self.topics_of_passion = topics_of_passion if isinstance(topics_of_passion, list) else json.loads(topics_of_passion or '[]')
        self.created_at = created_at
        self.updated_at = updated_at

    def save(self):
        """Save or update the expert profile."""
        conn = get_db_connection()
        cursor = conn.cursor()

        core_beliefs_json = json.dumps(self.core_beliefs)
        personal_stories_json = json.dumps(self.personal_stories)
        contrarian_positions_json = json.dumps(self.contrarian_positions)
        signature_phrases_json = json.dumps(self.signature_phrases)
        topics_of_passion_json = json.dumps(self.topics_of_passion)

        if self.id:
            cursor.execute("""
                UPDATE expert_profiles SET
                    core_beliefs = ?,
                    personal_stories = ?,
                    contrarian_positions = ?,
                    signature_phrases = ?,
                    topics_of_passion = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (core_beliefs_json, personal_stories_json, contrarian_positions_json,
                  signature_phrases_json, topics_of_passion_json, self.id))
        else:
            cursor.execute("""
                INSERT INTO expert_profiles
                    (client_id, core_beliefs, personal_stories, contrarian_positions,
                     signature_phrases, topics_of_passion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.client_id, core_beliefs_json, personal_stories_json,
                  contrarian_positions_json, signature_phrases_json, topics_of_passion_json))
            self.id = cursor.lastrowid

        conn.commit()
        conn.close()
        return self

    def merge_extraction(self, extracted_data, transcript_id):
        """
        Merge approved items from a transcript extraction into this profile.
        extracted_data is a dict of lists, each item having an 'approved' key set to True.
        transcript_id is stored on each item for traceability.
        """
        for belief in extracted_data.get('core_beliefs', []):
            if belief.get('approved'):
                self.core_beliefs.append({
                    'text': belief['text'],
                    'source_transcript_id': transcript_id,
                    'approved': True
                })

        for story in extracted_data.get('personal_stories', []):
            if story.get('approved'):
                self.personal_stories.append({
                    'title': story['title'],
                    'summary': story['summary'],
                    'source_transcript_id': transcript_id,
                    'approved': True
                })

        for position in extracted_data.get('contrarian_positions', []):
            if position.get('approved'):
                self.contrarian_positions.append({
                    'text': position['text'],
                    'source_transcript_id': transcript_id,
                    'approved': True
                })

        for phrase in extracted_data.get('signature_phrases', []):
            if phrase.get('approved'):
                self.signature_phrases.append({
                    'phrase': phrase['phrase'],
                    'context': phrase.get('context', ''),
                    'source_transcript_id': transcript_id,
                    'approved': True
                })

        for topic in extracted_data.get('topics_of_passion', []):
            if topic.get('approved'):
                self.topics_of_passion.append({
                    'text': topic.get('topic', topic.get('text', '')),
                    'source_transcript_id': transcript_id,
                    'approved': True
                })

        return self

    @staticmethod
    def get_by_client_id(client_id):
        """Get the expert profile for a client. Returns None if not yet created."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expert_profiles WHERE client_id = ?", (client_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return ExpertProfile(**dict(row))
        return None

    @staticmethod
    def get_or_create(client_id):
        """Get existing profile or create a new empty one for this client."""
        profile = ExpertProfile.get_by_client_id(client_id)
        if not profile:
            profile = ExpertProfile(client_id=client_id)
            profile.save()
        return profile
