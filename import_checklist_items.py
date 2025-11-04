#!/usr/bin/env python3
"""
Import Checklist Items from Old Backup
Restores the 10 standard vehicle inspection checklist items
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import get_db_connection

# Standard checklist items from old system
CHECKLIST_ITEMS = [
    {"id": 1, "description": "Check engine oil level", "category": "Engine"},
    {"id": 2, "description": "Check tire pressure", "category": "Tires"},
    {"id": 3, "description": "Check emergency lights", "category": "Lights"},
    {"id": 4, "description": "Check brake fluid level", "category": "Brakes"},
    {"id": 5, "description": "Test horn and sirens", "category": "Safety"},
    {"id": 6, "description": "Check all exterior lights", "category": "Lights"},
    {"id": 7, "description": "Inspect windshield and wipers", "category": "Visibility"},
    {"id": 8, "description": "Check water tank level", "category": "Water System"},
    {"id": 9, "description": "Inspect hose connections", "category": "Water System"},
    {"id": 10, "description": "Test radio communications", "category": "Communications"}
]

def import_checklist_items():
    """Import checklist items into the database"""

    conn = get_db_connection()
    cursor = conn.cursor()

    print("📋 Importing vehicle inspection checklist items...")
    print()

    # Check if items already exist
    cursor.execute('SELECT COUNT(*) FROM inspection_checklist_items')
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"⚠️  Found {existing_count} existing checklist items")
        response = input("   Do you want to keep existing items and add new ones? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Cancelled")
            conn.close()
            return

    # Import items
    count = 0
    for item in CHECKLIST_ITEMS:
        try:
            cursor.execute('''
                INSERT INTO inspection_checklist_items (description, category, is_active, display_order)
                VALUES (?, ?, 1, ?)
            ''', (item['description'], item['category'], item['id']))
            count += 1
            print(f"✅ Added: {item['description']}")
        except Exception as e:
            print(f"⚠️  Skipped: {item['description']} ({str(e)})")

    conn.commit()

    print()
    print(f"✅ Imported {count} checklist items")
    print()

    # Now assign all items to all vehicles
    print("🔧 Assigning checklist items to all vehicles...")

    cursor.execute('SELECT id, name FROM vehicles')
    vehicles = cursor.fetchall()

    cursor.execute('SELECT id FROM inspection_checklist_items WHERE is_active = 1')
    checklist_items = cursor.fetchall()

    assignment_count = 0
    for vehicle in vehicles:
        vehicle_id = vehicle[0]
        vehicle_name = vehicle[1]
        for item in checklist_items:
            item_id = item[0]
            try:
                cursor.execute('''
                    INSERT INTO vehicle_checklist_assignments (vehicle_id, checklist_item_id)
                    VALUES (?, ?)
                ''', (vehicle_id, item_id))
                assignment_count += 1
            except:
                pass  # Skip if already exists

        print(f"✅ Assigned {len(checklist_items)} items to {vehicle_name}")

    conn.commit()
    conn.close()

    print()
    print("=" * 70)
    print("✅ Checklist items imported successfully!")
    print(f"   {count} checklist items added")
    print(f"   {assignment_count} assignments created")
    print("   All vehicles can now be inspected")
    print("=" * 70)

if __name__ == '__main__':
    try:
        import_checklist_items()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
