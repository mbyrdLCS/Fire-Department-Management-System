#!/usr/bin/env python3
"""
Fix hose names in the database.
Remove 'HOSE-' prefix from the name field if it exists.
The name should be just the hose ID (e.g., "17-27"),
while item_code should have the prefix (e.g., "HOSE-17-27").
"""

import sqlite3
import os

def get_db_path():
    """Get the database path"""
    # Try multiple possible locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'flask_app', 'database', 'fire_dept.db'),
        '/home/michealhelps/Fire-Department-Management-System/flask_app/database/fire_dept.db',
        os.path.join(os.path.dirname(__file__), 'flask_app', 'fire_department.db'),
        '/home/michealhelps/fire_department.db',
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found database at: {path}")
            return path

    print(f"Database not found in any of these locations:")
    for path in possible_paths:
        print(f"  - {path}")
    # If not found, return the default and let the caller handle the error
    return possible_paths[0]

def fix_hose_names():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
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
        elif name and ('" Hose' in name or '"Hose' in name):
            # Handle bad data like '1.5" Hose' - use item_code as the name
            if item_code and not item_code.startswith('HOSE-'):
                # item_code has the real hose ID, use it as the name
                new_name = item_code.strip()
                new_item_code = f'HOSE-{new_name}'
                print(f"Fixing hose {hose_id}: name '{name}' -> '{new_name}', item_code '{item_code}' -> '{new_item_code}'")
                cursor.execute('UPDATE inventory_items SET name = ?, item_code = ? WHERE id = ?',
                             (new_name, new_item_code, hose_id))
                updated_count += 1
            else:
                print(f"WARNING: Hose {hose_id} has invalid name '{name}' and item_code '{item_code}' - needs manual correction")
        elif item_code and not item_code.startswith('HOSE-'):
            # item_code doesn't have HOSE- prefix, add it
            new_item_code = f'HOSE-{item_code}'

            # Check if this item_code already exists
            cursor.execute('SELECT id FROM inventory_items WHERE item_code = ? AND id != ?', (new_item_code, hose_id))
            existing = cursor.fetchone()

            if existing:
                print(f"WARNING: Hose {hose_id} has item_code '{item_code}' but '{new_item_code}' already exists (hose {existing[0]}) - DUPLICATE!")
                print(f"  This hose needs manual review - might need to be deleted")
            else:
                print(f"Adding HOSE- prefix to hose {hose_id}: item_code '{item_code}' -> '{new_item_code}'")
                cursor.execute('UPDATE inventory_items SET item_code = ? WHERE id = ?', (new_item_code, hose_id))
                updated_count += 1
        else:
            print(f"Hose {hose_id}: name='{name}', item_code='{item_code}' - OK")

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
