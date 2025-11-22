#!/usr/bin/env python3
"""
Add hose testing tables to the database
Run this ONCE to add the new tables for ISO hose testing
"""

import sys
import os

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import get_db_connection

def add_hose_tables():
    """Add hose-specific tables to existing database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("🔨 Adding Hose Testing Tables...")

    # 1. Hose items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hose_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_number TEXT UNIQUE NOT NULL,
        vehicle_id INTEGER,
        hose_type TEXT,
        diameter REAL,
        length_feet INTEGER,
        pressure_rating INTEGER,
        manufacture_date DATE,
        manufacturer TEXT,
        notes TEXT,
        image_filename TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
    )
    ''')
    print("✅ Created table: hose_items")

    # 2. Hose annual tests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hose_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hose_id INTEGER NOT NULL,
        test_year INTEGER NOT NULL,
        test_date DATE NOT NULL,
        tested_by TEXT,
        test_result TEXT NOT NULL,
        test_pressure INTEGER,
        failure_reason TEXT,
        repair_status TEXT,
        repair_cost REAL,
        repair_notes TEXT,
        expected_completion_date DATE,
        completed_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (hose_id) REFERENCES hose_items(id) ON DELETE CASCADE,
        UNIQUE(hose_id, test_year)
    )
    ''')
    print("✅ Created table: hose_tests")

    # 3. Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hose_items_vehicle ON hose_items(vehicle_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hose_items_id_number ON hose_items(id_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hose_tests_hose ON hose_tests(hose_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hose_tests_year ON hose_tests(test_year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hose_tests_result ON hose_tests(test_result)')
    print("✅ Created indexes")

    conn.commit()
    conn.close()

    print("\n🎉 Hose testing tables added successfully!")
    print("   - hose_items: Store hose inventory")
    print("   - hose_tests: Store annual test results")
    print("\nYou can now add hoses and track annual ISO testing.")

if __name__ == '__main__':
    add_hose_tables()
