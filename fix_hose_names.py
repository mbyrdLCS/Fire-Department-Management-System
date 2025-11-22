#!/usr/bin/env python3
"""
Fix hose names in the database.
Remove 'HOSE-' prefix from the name field if it exists.
The name should be just the hose ID (e.g., "17-27"),
while item_code should have the prefix (e.g., "HOSE-17-27").
"""

import sqlite3
import sys
import os

# Add the flask_app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

import db_helpers

def fix_hose_names():
    conn = db_helpers.get_db_connection()
    cursor = conn.cursor()

    # Get all hoses
    cursor.execute('''
        SELECT id, name, item_code
        FROM inventory_items
        WHERE category = 'Hose'
    ''')

    hoses = cursor.fetchall()
    updated_count = 0

    for hose_id, name, item_code in hoses:
        # If name starts with "HOSE-", remove it
        if name and name.startswith('HOSE-'):
            new_name = name.replace('HOSE-', '', 1)
            print(f"Updating hose {hose_id}: '{name}' -> '{new_name}'")
            cursor.execute('UPDATE inventory_items SET name = ? WHERE id = ?', (new_name, hose_id))
            updated_count += 1
        elif name and name.upper().startswith('HOSE '):
            # Also handle "HOSE 17-27" format
            new_name = name[5:]  # Remove "HOSE "
            print(f"Updating hose {hose_id}: '{name}' -> '{new_name}'")
            cursor.execute('UPDATE inventory_items SET name = ? WHERE id = ?', (new_name, hose_id))
            updated_count += 1
        else:
            print(f"Hose {hose_id} already correct: name='{name}', item_code='{item_code}'")

    conn.commit()
    conn.close()

    print(f"\nFixed {updated_count} hose names")
    return updated_count

if __name__ == '__main__':
    print("Fixing hose names in database...")
    print("=" * 50)
    fix_hose_names()
    print("=" * 50)
    print("Done!")
