"""
One-time password migration script.
Hashes any plaintext passwords in the database with bcrypt.
Run once after deploying the bcrypt password hashing code.

Usage:
    cd superstories-v3
    python scripts/migrate_passwords.py
"""

import sys
import os

# Add the parent directory to the path so we can import from the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from models.database import get_db_connection


def is_bcrypt_hash(value):
    """Return True if the value looks like a bcrypt hash (starts with $2b$ or $2a$)."""
    if not value:
        return False
    return value.startswith('$2b$') or value.startswith('$2a$')


def migrate_passwords():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, name, password FROM clients')
    clients = cursor.fetchall()

    migrated = 0
    already_hashed = 0
    skipped = 0

    for client in clients:
        client_id = client['id']
        client_name = client['name']
        current_password = client['password']

        if not current_password:
            print(f"  SKIP  {client_name} (id={client_id}) — no password set")
            skipped += 1
            continue

        if is_bcrypt_hash(current_password):
            print(f"  OK    {client_name} (id={client_id}) — already hashed")
            already_hashed += 1
            continue

        # Hash the plaintext password
        hashed = bcrypt.hashpw(current_password.encode('utf-8'), bcrypt.gensalt())
        hashed_str = hashed.decode('utf-8')

        cursor.execute(
            'UPDATE clients SET password = ? WHERE id = ?',
            (hashed_str, client_id)
        )
        print(f"  DONE  {client_name} (id={client_id}) — password hashed")
        migrated += 1

    conn.commit()
    conn.close()

    print()
    print(f"Migration complete. Migrated: {migrated} | Already hashed: {already_hashed} | Skipped: {skipped}")


if __name__ == '__main__':
    print("SuperStories — Password Migration")
    print("Hashing any plaintext passwords in the database...")
    print()
    migrate_passwords()
