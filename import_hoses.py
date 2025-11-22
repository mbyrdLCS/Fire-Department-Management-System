#!/usr/bin/env python3
"""
Import hoses from CSV file into the database
Imports hoses as inventory items and optionally assigns them to vehicles
"""

import sys
import os
import csv
from datetime import datetime

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import get_db_connection

def parse_test_status(status):
    """Parse the test status code to determine vehicle and test result"""
    if not status or status.strip() == '':
        return None, 'PASS'

    status = status.strip().upper()

    # Check for failure indicators
    if status in ['@ REPAIR', 'REPAIR']:
        return None, 'REPAIR'
    if 'FAIL' in status:
        return None, 'FAIL'

    # Status codes that indicate vehicle assignment
    vehicle_codes = {
        'P2': 'P2',
        'P3': 'P3',
        'P4': 'P4',
        'G4': 'G4',
        'T6': 'T6',
        'G1': 'G1',
        'G5': 'G5',
        'R1': 'R1',
        'R2': 'R2',
        'T2': 'T2',
        'T3': 'T3'
    }

    for code, vehicle_code in vehicle_codes.items():
        if status == code:
            return vehicle_code, 'PASS'

    # Default to pass if we don't recognize the status
    return None, 'PASS'

def import_hoses():
    """Import hoses from CSV file"""
    conn = get_db_connection()
    cursor = conn.cursor()

    csv_file = 'hoses_import.csv'

    if not os.path.exists(csv_file):
        print(f"❌ Error: {csv_file} not found!")
        return

    print(f"📂 Reading hoses from {csv_file}...")

    # Get vehicle ID mapping
    cursor.execute('SELECT id, vehicle_code FROM vehicles')
    vehicles = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"   Found {len(vehicles)} vehicles in database")

    imported_count = 0
    skipped_count = 0
    assigned_count = 0
    test_count = 0

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            id_number = row['id_number'].strip()
            diameter = row['diameter'].strip() if row['diameter'] else None
            test_psi = row['test_psi'].strip() if row['test_psi'] else None
            status_2017 = row['status_2017'].strip() if row['status_2017'] else ''
            test_date_2017 = row['test_date_2017'].strip() if row['test_date_2017'] else None
            notes = row['notes'].strip() if row['notes'] else ''

            # Skip if already exists
            cursor.execute('SELECT id FROM inventory_items WHERE item_code = ?', (id_number,))
            existing = cursor.fetchone()

            if existing:
                print(f"   ⚠️  Skipping {id_number} - already exists")
                skipped_count += 1
                continue

            # Create hose inventory item
            cursor.execute('''
                INSERT INTO inventory_items
                (item_code, name, category, subcategory, diameter, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                id_number,
                f"Hose {id_number}",
                'Hose',
                'Fire Hose',
                float(diameter) if diameter else None,
                notes
            ))

            item_id = cursor.lastrowid
            imported_count += 1

            # Parse vehicle assignment and test result from status
            vehicle_code, test_result = parse_test_status(status_2017)

            # Assign to vehicle if we have a vehicle code
            if vehicle_code and vehicle_code in vehicles:
                vehicle_id = vehicles[vehicle_code]

                try:
                    cursor.execute('''
                        INSERT INTO vehicle_inventory
                        (vehicle_id, item_id, quantity, assigned_date)
                        VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ''', (vehicle_id, item_id))
                    assigned_count += 1
                    print(f"   ✅ {id_number} → {vehicle_code} ({diameter}\" @ {test_psi} PSI)")
                except Exception as e:
                    print(f"   ⚠️  Could not assign {id_number} to {vehicle_code}: {e}")
            else:
                if vehicle_code:
                    print(f"   📝 {id_number} (vehicle {vehicle_code} not found - spare hose)")
                else:
                    print(f"   📝 {id_number} (spare/unassigned)")

            # Add 2017 test record if we have test data
            if test_date_2017 and test_psi:
                try:
                    # Parse date (format: MM/DD/YYYY or M/D/YYYY)
                    date_parts = test_date_2017.split('/')
                    if len(date_parts) == 3:
                        month, day, year = date_parts
                        test_date_formatted = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                        cursor.execute('''
                            INSERT INTO iso_hose_tests
                            (item_id, test_year, test_date, test_result, test_pressure, created_at, updated_at)
                            VALUES (?, 2017, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', (item_id, test_date_formatted, test_result, int(test_psi)))

                        test_count += 1
                except Exception as e:
                    print(f"   ⚠️  Could not add 2017 test for {id_number}: {e}")

    conn.commit()
    conn.close()

    print("\n" + "="*60)
    print("🎉 Import Complete!")
    print("="*60)
    print(f"   ✅ Imported: {imported_count} hoses")
    print(f"   ⚠️  Skipped: {skipped_count} (already exist)")
    print(f"   🚒 Assigned to vehicles: {assigned_count}")
    print(f"   📋 Test records created: {test_count} (2017)")
    print(f"\n💡 Next steps:")
    print(f"   1. Go to ISO Hose Testing to view all hoses")
    print(f"   2. Run annual testing for current year")
    print(f"   3. Generate testing reports")

if __name__ == '__main__':
    import_hoses()
