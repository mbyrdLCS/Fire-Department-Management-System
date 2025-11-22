#!/usr/bin/env python3
"""
Delete all hoses that are not assigned to any vehicle
"""

import sqlite3
import os

def get_db_path():
    """Get the database path"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'flask_app', 'database', 'fire_dept.db'),
        '/home/michealhelps/Fire-Department-Management-System/flask_app/database/fire_dept.db',
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found database at: {path}")
            return path

    print(f"Database not found in any of these locations:")
    for path in possible_paths:
        print(f"  - {path}")
    return possible_paths[0]

def delete_unassigned_hoses():
    """Delete all hoses not assigned to any vehicle"""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("DELETING UNASSIGNED HOSES")
    print("="*70 + "\n")

    # First, find all unassigned hoses
    cursor.execute('''
        SELECT i.id, i.name, i.item_code
        FROM inventory_items i
        LEFT JOIN vehicle_inventory vi ON i.id = vi.item_id
        WHERE i.category = 'Hose'
        AND vi.item_id IS NULL
        ORDER BY i.name
    ''')

    unassigned = cursor.fetchall()

    if not unassigned:
        print("✓ No unassigned hoses found - all hoses are assigned to vehicles!")
        conn.close()
        return 0

    print(f"Found {len(unassigned)} unassigned hose(s):\n")
    for hose in unassigned:
        print(f"  - {hose['name']:<15} (item_code: {hose['item_code']})")

    print(f"\n{'='*70}")
    print(f"WARNING: This will DELETE {len(unassigned)} hoses from the database!")
    print(f"{'='*70}\n")

    # Delete test records first
    cursor.execute('''
        DELETE FROM iso_hose_tests
        WHERE item_id IN (
            SELECT i.id FROM inventory_items i
            LEFT JOIN vehicle_inventory vi ON i.id = vi.item_id
            WHERE i.category = 'Hose' AND vi.item_id IS NULL
        )
    ''')
    test_records_deleted = cursor.rowcount
    print(f"✓ Deleted {test_records_deleted} test record(s)")

    # Delete the unassigned hoses
    cursor.execute('''
        DELETE FROM inventory_items
        WHERE id IN (
            SELECT i.id FROM inventory_items i
            LEFT JOIN vehicle_inventory vi ON i.id = vi.item_id
            WHERE i.category = 'Hose' AND vi.item_id IS NULL
        )
    ''')
    hoses_deleted = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"✓ Deleted {hoses_deleted} unassigned hose(s)")
    print(f"\n{'='*70}")
    print("CLEANUP COMPLETE")
    print("="*70 + "\n")

    return hoses_deleted

if __name__ == '__main__':
    delete_unassigned_hoses()
