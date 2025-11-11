"""
Migration script to add display settings table for QR code visibility controls
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'flask_app', 'database', 'fire_dept.db')

def add_display_settings_table():
    """Add display_settings table to store server-side display preferences"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print("🔧 Adding display_settings table...")

    # Create display_settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS display_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created table: display_settings")

    # Insert default settings for QR code visibility
    default_settings = [
        ('show_inventory_qr', 'true'),
        ('show_maintenance_qr', 'true')
    ]

    for key, value in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO display_settings (setting_key, setting_value)
            VALUES (?, ?)
        ''', (key, value))
        print(f"✅ Added default setting: {key} = {value}")

    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == '__main__':
    add_display_settings_table()
