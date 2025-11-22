#!/usr/bin/env python3
"""
Import 2025 hose test data from paper records
Run this script to bulk import completed hose tests
"""

import sqlite3
import os
from datetime import datetime

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

    return possible_paths[0]

def import_hose_tests():
    """Import hose test data from paper records"""

    # Data extracted from the images (red handwriting = completed tests)
    test_data = [
        # Format: (hose_id, test_date, result, pressure, failure_reason, repair_status)
        # Image 1 (IMG_1756) - Bottom section with handwritten entries
        ('01-03-04', '2024-06-16', 'PASS', 250, '', ''),
        ('99-11', '2024-06-16', 'FAIL', 250, '', ''),
        ('99-14', '2024-06-16', 'PASS', 250, '', ''),
        ('32', '2024-06-16', 'PASS', 250, '', ''),
        ('33', '2024-11-22', 'PASS', 350, '', ''),
        ('04-19', '2025-11-22', 'FAIL', 250, '', ''),
        ('03-2', '2025-11-22', 'PASS', 250, '', ''),
        ('7-26', '2025-11-22', 'PASS', 250, '', ''),
        ('8000619', '2025-11-22', 'PASS', 250, '', ''),
        ('7279-1', '2025-11-22', 'FAIL', 250, '', ''),
        ('7329-2', '2025-11-22', 'PASS', 250, '', ''),
        ('7379-3', '2025-11-22', 'PASS', 250, '', ''),
        ('7343-11', '2025-11-22', 'FAIL', 250, '', ''),

        # Image 2 (IMG_1754) - Hoses 17-61 through 17-79 area
        ('17-61', '2024-06-16', 'PASS', 250, '', ''),
        ('17-62', '2024-06-16', 'FAIL', 250, '', ''),
        ('17-64', '2024-06-16', 'PASS', 250, '', ''),
        ('17-67', '2025-11-22', 'PASS', 250, '', ''),
        ('17-68', '2025-11-22', 'PASS', 250, '', ''),

        # Image 3 (IMG_1755) - Various 96- and 991- series hoses
        ('17-82', '2024-06-16', 'PASS', 250, '', ''),
        ('96-5', '2025-11-22', 'PASS', 250, '', ''),
        ('96-6', '2025-11-22', 'FAIL', 250, '', ''),
        ('96-7', '2025-11-22', 'PASS', 250, '', ''),
        ('99-1', '2024-06-16', 'PASS', 250, '', ''),
        ('991263-9', '2025-11-22', 'FAIL', 250, '', ''),
        ('991263-10', '2025-11-22', 'FAIL', 250, '', ''),
        ('991264-2', '2025-11-22', 'FAIL', 250, '', ''),
        ('99-14', '2025-11-22', 'PASS', 250, '', ''),
        ('99-4', '2025-11-22', 'FAIL', 250, '', ''),

        # Image 4 (IMG_1753) - 7-series and 17-series hoses
        ('7343', '2025-11-22', 'FAIL', 250, '', ''),
        ('7343-1', '2025-11-22', 'FAIL', 250, '', ''),
        ('7379', '2024-06-16', 'PASS', 250, '', ''),
        ('03-3', '2024-06-16', 'PASS', 250, '', ''),
        ('991250', '2024-06-16', 'PASS', 250, '', ''),
        ('17-21', '2025-11-22', 'PASS', 250, '', ''),
        ('17-20', '2025-11-22', 'FAIL', 250, '', ''),
        ('17-24', '2024-06-16', 'PASS', 250, '', ''),
        ('17-27', '2024-06-16', 'FAIL', 250, '', ''),
    ]

    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    imported_count = 0
    skipped_count = 0
    error_count = 0

    print("\n" + "="*70)
    print("IMPORTING HOSE TEST DATA FROM PAPER RECORDS")
    print("="*70 + "\n")

    for hose_id, test_date, result, pressure, failure_reason, repair_status in test_data:
        try:
            # Find the hose in inventory by name
            cursor.execute('''
                SELECT id, name FROM inventory_items
                WHERE category = 'Hose' AND name = ?
            ''', (hose_id,))

            hose = cursor.fetchone()

            if not hose:
                print(f"⚠️  SKIP: Hose '{hose_id}' not found in inventory")
                skipped_count += 1
                continue

            item_id = hose['id']

            # Determine test year from date
            test_year = int(test_date.split('-')[0])

            # Check if test already exists for this year
            cursor.execute('''
                SELECT id FROM iso_hose_tests
                WHERE item_id = ? AND test_year = ?
            ''', (item_id, test_year))

            existing = cursor.fetchone()

            if existing:
                # Update existing test
                cursor.execute('''
                    UPDATE iso_hose_tests
                    SET test_date = ?, test_result = ?, test_pressure = ?,
                        failure_reason = ?, repair_status = ?
                    WHERE item_id = ? AND test_year = ?
                ''', (test_date, result, pressure, failure_reason or None,
                      repair_status or None, item_id, test_year))
                print(f"✓ UPDATE: {hose_id} - {result} on {test_date} ({test_year})")
            else:
                # Insert new test record
                cursor.execute('''
                    INSERT INTO iso_hose_tests
                    (item_id, test_year, test_date, test_result, test_pressure,
                     failure_reason, repair_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (item_id, test_year, test_date, result, pressure,
                      failure_reason or None, repair_status or None))
                print(f"✓ INSERT: {hose_id} - {result} on {test_date} ({test_year})")

            imported_count += 1

        except Exception as e:
            print(f"❌ ERROR: {hose_id} - {str(e)}")
            error_count += 1

    conn.commit()
    conn.close()

    print("\n" + "="*70)
    print(f"IMPORT COMPLETE")
    print(f"  ✓ Imported/Updated: {imported_count}")
    print(f"  ⚠️  Skipped (not found): {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    print("="*70 + "\n")

    return imported_count

if __name__ == '__main__':
    import_hose_tests()
