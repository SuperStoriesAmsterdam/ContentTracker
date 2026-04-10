"""
AdSpend model — stores manually entered monthly advertising spend.
One row per client, per platform, per month.
"""

from models.database import get_db_connection

PLATFORMS = ['Meta', 'Google Ads', 'LinkedIn', 'Other']
CURRENCIES = ['EUR', 'USD', 'GBP']

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}


class AdSpend:
    def __init__(self, id=None, client_id=None, year=None, month=None,
                 platform=None, amount=None, currency='EUR', notes=None,
                 created_at=None):
        self.id = id
        self.client_id = client_id
        self.year = year
        self.month = month
        self.platform = platform
        self.amount = float(amount) if amount is not None else 0.0
        self.currency = currency or 'EUR'
        self.notes = notes
        self.created_at = created_at

    @property
    def month_name(self):
        return MONTH_NAMES.get(self.month, '')

    def save(self):
        """Save or update this spend entry."""
        conn = get_db_connection()
        cursor = conn.cursor()

        if self.id:
            cursor.execute("""
                UPDATE ad_spend SET
                    year = ?, month = ?, platform = ?,
                    amount = ?, currency = ?, notes = ?
                WHERE id = ?
            """, (self.year, self.month, self.platform,
                  self.amount, self.currency, self.notes, self.id))
        else:
            cursor.execute("""
                INSERT INTO ad_spend
                    (client_id, year, month, platform, amount, currency, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.client_id, self.year, self.month, self.platform,
                  self.amount, self.currency, self.notes))
            self.id = cursor.lastrowid

        conn.commit()
        conn.close()
        return self

    def delete(self):
        """Delete this spend entry."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ad_spend WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(spend_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ad_spend WHERE id = ?", (spend_id,))
        row = cursor.fetchone()
        conn.close()
        return AdSpend(**dict(row)) if row else None

    @staticmethod
    def get_by_client(client_id):
        """All spend entries for a client, newest month first."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ad_spend
            WHERE client_id = ?
            ORDER BY year DESC, month DESC, platform ASC
        """, (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return [AdSpend(**dict(row)) for row in rows]

    @staticmethod
    def get_monthly_totals(client_id):
        """
        Return a list of dicts — one per (year, month) — with total spend across all platforms.
        Ordered newest first. Used to show spend alongside GSC monthly data.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT year, month, currency, SUM(amount) as total
            FROM ad_spend
            WHERE client_id = ?
            GROUP BY year, month, currency
            ORDER BY year DESC, month DESC
        """, (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_month(client_id, year, month):
        """All entries for a specific month — used to show per-platform breakdown."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ad_spend
            WHERE client_id = ? AND year = ? AND month = ?
            ORDER BY platform ASC
        """, (client_id, year, month))
        rows = cursor.fetchall()
        conn.close()
        return [AdSpend(**dict(row)) for row in rows]
