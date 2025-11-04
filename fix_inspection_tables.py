#!/usr/bin/env python3
"""
Fix Missing Inspection Tables
Adds the vehicle_checklist_assignments table that was missing from the schema
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import get_db_connection

def fix_inspection_tables():
    """Add missing vehicle_checklist_assignments table"""

    conn = get_db_connection()
    cursor = conn.cursor()

    print("🔧 Fixing inspection tables...")
    print()

    # Check if table already exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='vehicle_checklist_assignments'
    """)

    if cursor.fetchone():
        print("✅ Table 'vehicle_checklist_assignments' already exists")
        conn.close()
        return

    # Create the missing table
    print("📝 Creating vehicle_checklist_assignments table...")

    cursor.execute('''
        CREATE TABLE vehicle_checklist_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            checklist_item_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
            FOREIGN KEY (checklist_item_id) REFERENCES inspection_checklist_items(id) ON DELETE CASCADE,
            UNIQUE(vehicle_id, checklist_item_id)
        )
    ''')

    conn.commit()

    print("✅ Table created successfully!")
    print()

    # Assign all checklist items to all vehicles (default behavior)
    print("📋 Assigning all checklist items to all vehicles...")

    cursor.execute('SELECT id FROM vehicles')
    vehicles = cursor.fetchall()

    cursor.execute('SELECT id FROM inspection_checklist_items WHERE is_active = 1')
    checklist_items = cursor.fetchall()

    count = 0
    for vehicle in vehicles:
        vehicle_id = vehicle[0]
        for item in checklist_items:
            item_id = item[0]
            try:
                cursor.execute('''
                    INSERT INTO vehicle_checklist_assignments (vehicle_id, checklist_item_id)
                    VALUES (?, ?)
                ''', (vehicle_id, item_id))
                count += 1
            except:
                pass  # Skip if already exists

    conn.commit()
    conn.close()

    print(f"✅ Created {count} checklist assignments")
    print()
    print("=" * 70)
    print("✅ Inspection tables fixed!")
    print("   All vehicles now have checklist items assigned")
    print("   You can now access /inspect/<vehicle_id> without errors")
    print("=" * 70)

if __name__ == '__main__':
    try:
        fix_inspection_tables()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
