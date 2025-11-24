#!/usr/bin/env python3
"""
Add users table for multi-user authentication system
Run this ONCE to add the users table to your database
"""

import sys
import os
import bcrypt

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

import db_helpers

def create_users_table():
    """Create the users table with roles and permissions"""

    conn = db_helpers.get_db_connection()
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("CREATING USERS TABLE")
    print("="*70)

    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        print("\n⚠️  Users table already exists!")
        response = input("Drop and recreate? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            conn.close()
            return
        cursor.execute("DROP TABLE users")
        print("✓ Dropped existing users table")

    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            permissions TEXT,
            is_active BOOLEAN DEFAULT 1,
            must_change_password BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    print("✓ Created users table")

    # Create index for faster lookups
    cursor.execute('CREATE INDEX idx_users_username ON users(username)')
    cursor.execute('CREATE INDEX idx_users_email ON users(email)')

    print("✓ Created indexes")

    # Get current admin credentials from .env
    admin_username = os.getenv('ADMIN_USERNAME', 'Firefighter')
    admin_password = os.getenv('ADMIN_PASSWORD', 'thisisthePassword$$5')

    # Hash the password
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create default admin user from current credentials
    cursor.execute('''
        INSERT INTO users (username, full_name, password_hash, role, is_active, must_change_password)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (admin_username, 'System Administrator', password_hash, 'admin', 1, 0))

    print(f"\n✓ Created default admin user: {admin_username}")
    print(f"  Password: {admin_password}")
    print(f"  Role: admin")

    conn.commit()
    conn.close()

    print("\n" + "="*70)
    print("✅ USERS TABLE CREATED SUCCESSFULLY")
    print("="*70)
    print("\nRoles Available:")
    print("  • admin    - Full access to everything")
    print("  • editor   - Can edit data, cannot manage users")
    print("  • viewer   - Read-only access")
    print("  • custom   - Custom permissions")
    print("\nNext Steps:")
    print("  1. Deploy this migration to PythonAnywhere")
    print("  2. Run: python3 add_users_table.py")
    print("  3. Log in with existing admin credentials")
    print("  4. Add new users from Admin → User Management")
    print("="*70 + "\n")

if __name__ == '__main__':
    try:
        create_users_table()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
