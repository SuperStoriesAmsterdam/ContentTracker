"""
Site model — stores websites connected to a client.
One client can have multiple sites, each with its own GSC property.
Used for the multi-site dashboard that shows combined search performance.
"""

from models.database import get_db_connection


class Site:
    def __init__(self, id=None, client_id=None, url=None, name=None,
                 gsc_property=None, created_at=None):
        self.id = id
        self.client_id = client_id
        self.url = url
        self.name = name
        self.gsc_property = gsc_property
        self.created_at = created_at

    def save(self):
        """Save or update this site."""
        conn = get_db_connection()
        cursor = conn.cursor()

        if self.id:
            cursor.execute("""
                UPDATE sites SET
                    url = ?, name = ?, gsc_property = ?
                WHERE id = ?
            """, (self.url, self.name, self.gsc_property, self.id))
        else:
            cursor.execute("""
                INSERT INTO sites (client_id, url, name, gsc_property)
                VALUES (?, ?, ?, ?)
            """, (self.client_id, self.url, self.name, self.gsc_property))
            self.id = cursor.lastrowid

        conn.commit()
        conn.close()
        return self

    def delete(self):
        """Delete this site."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sites WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(site_id):
        """Get a single site by its ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        row = cursor.fetchone()
        conn.close()
        return Site(**dict(row)) if row else None

    @staticmethod
    def get_all_by_client_id(client_id):
        """All sites for a client, ordered by name."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM sites
            WHERE client_id = ?
            ORDER BY name ASC
        """, (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Site(**dict(row)) for row in rows]
