"""
Migration script to add fluid specification columns to vehicles table
"""

import sqlite3
import os

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'flask_app', 'database', 'fire_dept.db')

def add_fluid_columns():
    """Add fluid specification columns to vehicles table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print("🔧 Adding fluid specification columns to vehicles table...")

    # Columns to add
    columns = [
        ('oil_type', 'TEXT'),
        ('antifreeze_type', 'TEXT'),
        ('brake_fluid_type', 'TEXT'),
        ('power_steering_fluid_type', 'TEXT'),
        ('transmission_fluid_type', 'TEXT')
    ]

    for column_name, column_type in columns:
        try:
            cursor.execute(f'ALTER TABLE vehicles ADD COLUMN {column_name} {column_type}')
            print(f"✅ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print(f"⚠️  Column {column_name} already exists, skipping...")
            else:
                raise

    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == '__main__':
    add_fluid_columns()
