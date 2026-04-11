"""GscSnapshot model — weekly GSC performance snapshots for historical tracking."""

import sqlite3
from datetime import datetime, date
from models.database import get_db_path


class GscSnapshot:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.client_id = kwargs.get('client_id')
        self.site_url = kwargs.get('site_url', '')
        self.keyword = kwargs.get('keyword', '')
        self.position = kwargs.get('position')
        self.clicks = kwargs.get('clicks', 0)
        self.impressions = kwargs.get('impressions', 0)
        self.ctr = kwargs.get('ctr', 0)
        self.snapshot_date = kwargs.get('snapshot_date')
        self.created_at = kwargs.get('created_at')

    def save(self):
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gsc_snapshots (client_id, site_url, keyword, position,
                clicks, impressions, ctr, snapshot_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.client_id, self.site_url, self.keyword, self.position,
              self.clicks, self.impressions, self.ctr, self.snapshot_date))
        self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    @staticmethod
    def take_snapshot(client_id, site_url, gsc_rows):
        """Store a snapshot of current GSC data for all keywords."""
        today = date.today().isoformat()

        # Check if we already have a snapshot for today
        conn = sqlite3.connect(get_db_path())
        existing = conn.execute(
            'SELECT COUNT(*) FROM gsc_snapshots WHERE client_id=? AND site_url=? AND snapshot_date=?',
            (client_id, site_url, today)
        ).fetchone()[0]
        conn.close()

        if existing > 0:
            return 0  # Already snapshotted today

        count = 0
        for row in gsc_rows:
            snapshot = GscSnapshot(
                client_id=client_id,
                site_url=site_url,
                keyword=row['query'],
                position=row.get('position'),
                clicks=row.get('clicks', 0),
                impressions=row.get('impressions', 0),
                ctr=row.get('ctr', 0),
                snapshot_date=today
            )
            snapshot.save()
            count += 1
        return count

    @staticmethod
    def get_trajectory(client_id, keyword, limit=12):
        """Get position trajectory for a keyword over time."""
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        rows = conn.execute('''
            SELECT snapshot_date, position, clicks, impressions
            FROM gsc_snapshots
            WHERE client_id=? AND keyword=?
            ORDER BY snapshot_date DESC
            LIMIT ?
        ''', (client_id, keyword, limit)).fetchall()
        conn.close()
        return [dict(r) for r in reversed(rows)]

    @staticmethod
    def get_latest_snapshot_date(client_id):
        """Get the date of the most recent snapshot."""
        conn = sqlite3.connect(get_db_path())
        row = conn.execute(
            'SELECT MAX(snapshot_date) FROM gsc_snapshots WHERE client_id=?',
            (client_id,)
        ).fetchone()
        conn.close()
        return row[0] if row and row[0] else None

    @staticmethod
    def get_snapshot_count(client_id):
        """Get total number of snapshots for a client."""
        conn = sqlite3.connect(get_db_path())
        row = conn.execute(
            'SELECT COUNT(DISTINCT snapshot_date) FROM gsc_snapshots WHERE client_id=?',
            (client_id,)
        ).fetchone()
        conn.close()
        return row[0] if row else 0
