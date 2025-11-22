#!/usr/bin/env python3
"""
Add hose testing capability to existing inventory system
This extends the inventory tables to support ISO hose testing
"""

import sys
import os

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import get_db_connection

def add_hose_testing():
    """Add hose testing fields and table to existing inventory system"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("🔨 Adding Hose Testing to Inventory System...")

    # 1. Add hose-specific columns to inventory_items
    try:
        cursor.execute('ALTER TABLE inventory_items ADD COLUMN diameter REAL')
        print("✅ Added column: diameter")
    except:
        print("⚠️  Column 'diameter' already exists")

    try:
        cursor.execute('ALTER TABLE inventory_items ADD COLUMN length_feet INTEGER')
        print("✅ Added column: length_feet")
    except:
        print("⚠️  Column 'length_feet' already exists")

    try:
        cursor.execute('ALTER TABLE inventory_items ADD COLUMN pressure_rating INTEGER')
        print("✅ Added column: pressure_rating")
    except:
        print("⚠️  Column 'pressure_rating' already exists")

    try:
        cursor.execute('ALTER TABLE inventory_items ADD COLUMN image_filename TEXT')
        print("✅ Added column: image_filename")
    except:
        print("⚠️  Column 'image_filename' already exists")

    try:
        cursor.execute('ALTER TABLE inventory_items ADD COLUMN hose_type TEXT')
        print("✅ Added column: hose_type")
    except:
        print("⚠️  Column 'hose_type' already exists")

    # 2. Create ISO testing records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS iso_hose_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
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
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
        UNIQUE(item_id, test_year)
    )
    ''')
    print("✅ Created table: iso_hose_tests")

    # 3. Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_iso_tests_item ON iso_hose_tests(item_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_iso_tests_year ON iso_hose_tests(test_year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_iso_tests_result ON iso_hose_tests(test_result)')
    print("✅ Created indexes")

    conn.commit()
    conn.close()

    print("\n🎉 Hose testing system added successfully!")
    print("\n📋 How it works:")
    print("   1. Add hoses as inventory items (category: 'Hose')")
    print("   2. Assign hoses to vehicles using vehicle_inventory table")
    print("   3. Only hoses assigned to vehicles show in annual testing reports")
    print("   4. Spare hoses (not on trucks) stay in inventory but don't appear in reports")

if __name__ == '__main__':
    add_hose_testing()
