"""KeywordTarget model — manually entered target keywords with zone assignment."""

import sqlite3
from models.database import get_db_path


class KeywordTarget:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.client_id = kwargs.get('client_id')
        self.site_id = kwargs.get('site_id')
        self.keyword = kwargs.get('keyword', '')
        self.zone = kwargs.get('zone', 3)
        self.notes = kwargs.get('notes', '')
        self.status = kwargs.get('status', 'tracking')
        self.last_seen_position = kwargs.get('last_seen_position')
        self.last_seen_impressions = kwargs.get('last_seen_impressions')
        self.last_checked_at = kwargs.get('last_checked_at')
        self.created_at = kwargs.get('created_at')

    def save(self):
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        if self.id:
            cursor.execute('''
                UPDATE keyword_targets SET keyword=?, zone=?, notes=?, status=?,
                    last_seen_position=?, last_seen_impressions=?, last_checked_at=?
                WHERE id=?
            ''', (self.keyword, self.zone, self.notes, self.status,
                  self.last_seen_position, self.last_seen_impressions,
                  self.last_checked_at, self.id))
        else:
            cursor.execute('''
                INSERT INTO keyword_targets (client_id, site_id, keyword, zone, notes, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.client_id, self.site_id, self.keyword, self.zone,
                  self.notes, self.status))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    def delete(self):
        conn = sqlite3.connect(get_db_path())
        conn.execute('DELETE FROM keyword_targets WHERE id=?', (self.id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_client(client_id):
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT * FROM keyword_targets WHERE client_id=? ORDER BY zone, keyword',
            (client_id,)
        ).fetchall()
        conn.close()
        return [KeywordTarget(**dict(r)) for r in rows]

    @staticmethod
    def get_by_id(target_id):
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT * FROM keyword_targets WHERE id=?', (target_id,)).fetchone()
        conn.close()
        return KeywordTarget(**dict(row)) if row else None

    def update_from_gsc(self, gsc_rows):
        """Check if this keyword appears in GSC data and update tracking."""
        for row in gsc_rows:
            if row['query'].lower() == self.keyword.lower():
                self.last_seen_position = row['position']
                self.last_seen_impressions = row['impressions']
                self.status = 'found'
                from datetime import datetime
                self.last_checked_at = datetime.now().isoformat()
                self.save()
                return True
        # Not found in GSC data
        if self.status == 'tracking':
            from datetime import datetime
            self.last_checked_at = datetime.now().isoformat()
            self.save()
        return False
