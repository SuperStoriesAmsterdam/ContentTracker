from models.database import get_db_connection

class DerivedContent:
    PLATFORMS = [
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram')
    ]
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.source_content_id = kwargs.get('source_content_id')
        self.client_id = kwargs.get('client_id')
        self.platform = kwargs.get('platform')
        self.content = kwargs.get('content')
        self.created_at = kwargs.get('created_at')
    
    def get_platform_display(self):
        """Get display name for platform."""
        for code, name in self.PLATFORMS:
            if code == self.platform:
                return name
        return self.platform
    
    def save(self):
        """Save or update derived content in database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if self.id:
            cursor.execute('''
                UPDATE derived_content SET
                    source_content_id = ?, client_id = ?, platform = ?, content = ?
                WHERE id = ?
            ''', (self.source_content_id, self.client_id, self.platform, self.content, self.id))
        else:
            cursor.execute('''
                INSERT INTO derived_content (source_content_id, client_id, platform, content)
                VALUES (?, ?, ?, ?)
            ''', (self.source_content_id, self.client_id, self.platform, self.content))
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self
    
    def delete(self):
        """Delete derived content from database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM derived_content WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_source(source_content_id):
        """Get all derived content for a source."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM derived_content WHERE source_content_id = ? ORDER BY created_at DESC',
            (source_content_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [DerivedContent(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(content_id):
        """Get derived content by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM derived_content WHERE id = ?', (content_id,))
        row = cursor.fetchone()
        conn.close()
        return DerivedContent(**dict(row)) if row else None
