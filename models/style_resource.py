from models.database import get_db_connection

class StyleResource:
    RESOURCE_TYPES = [
        ('linkedin', 'LinkedIn Post'),
        ('instagram', 'Instagram Post'),
        ('article', 'Article / Essay'),
        ('press_release', 'Press Release'),
        ('faq', 'FAQ Section')
    ]
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.client_id = kwargs.get('client_id')
        self.resource_type = kwargs.get('resource_type')
        self.title = kwargs.get('title')
        self.content = kwargs.get('content')
        self.created_at = kwargs.get('created_at')
    
    def get_resource_type_display(self):
        """Get display name for resource type."""
        for code, name in self.RESOURCE_TYPES:
            if code == self.resource_type:
                return name
        return self.resource_type
    
    def get_preview(self, max_chars=150):
        """Get preview of content."""
        if not self.content:
            return ""
        if len(self.content) <= max_chars:
            return self.content
        return self.content[:max_chars] + "..."
    
    def save(self):
        """Save or update style resource in database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if self.id:
            cursor.execute('''
                UPDATE style_resources SET
                    client_id = ?, resource_type = ?, title = ?, content = ?
                WHERE id = ?
            ''', (self.client_id, self.resource_type, self.title, self.content, self.id))
        else:
            cursor.execute('''
                INSERT INTO style_resources (client_id, resource_type, title, content)
                VALUES (?, ?, ?, ?)
            ''', (self.client_id, self.resource_type, self.title, self.content))
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return self
    
    def delete(self):
        """Delete style resource from database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM style_resources WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_client(client_id):
        """Get all style resources for a client."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM style_resources WHERE client_id = ? ORDER BY resource_type, title', (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return [StyleResource(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_client_and_type(client_id, resource_type):
        """Get style resources of a specific type for a client."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM style_resources WHERE client_id = ? AND resource_type = ? ORDER BY title',
            (client_id, resource_type)
        )
        rows = cursor.fetchall()
        conn.close()
        return [StyleResource(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(resource_id):
        """Get style resource by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM style_resources WHERE id = ?', (resource_id,))
        row = cursor.fetchone()
        conn.close()
        return StyleResource(**dict(row)) if row else None
