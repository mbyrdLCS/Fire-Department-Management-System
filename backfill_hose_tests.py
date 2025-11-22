#!/usr/bin/env python3
"""
Backfill ISO hose test records for 2023 and 2024
Takes all 2025 PASS records and creates identical records for previous years
Uses November Saturdays for test dates
"""

import sqlite3
import sys

def backfill_hose_tests():
    """Copy 2025 PASS records to 2023 and 2024"""

    # Database path
    db_path = 'flask_app/database/fire_dept.db'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all 2025 PASS records
    cursor.execute('''
        SELECT
            item_id,
            test_pressure,
            test_result,
            failure_reason,
            repair_status,
            repair_notes,
            tested_by
        FROM iso_hose_tests
        WHERE test_year = 2025
        AND test_result = 'PASS'
    ''')

    pass_records = cursor.fetchall()

    print(f"Found {len(pass_records)} PASS records from 2025")

    if len(pass_records) == 0:
        print("No 2025 PASS records found. Please complete 2025 testing first.")
        conn.close()
        return

    # Year and date mapping
    backfill_data = [
        (2023, '2023-11-18'),  # Saturday, November 18, 2023
        (2024, '2024-11-16')   # Saturday, November 16, 2024
    ]

    records_created = 0

    for year, test_date in backfill_data:
        print(f"\nCreating {year} records with test date {test_date}...")

        for record in pass_records:
            item_id, test_pressure, test_result, failure_reason, repair_status, repair_notes, tested_by = record

            # Check if record already exists
            cursor.execute('''
                SELECT id FROM iso_hose_tests
                WHERE item_id = ? AND test_year = ?
            ''', (item_id, year))

            existing = cursor.fetchone()

            if existing:
                print(f"  Skipping item_id {item_id} - already has {year} record")
                continue

            # Insert the record
            cursor.execute('''
                INSERT INTO iso_hose_tests (
                    item_id, test_year, test_date, test_pressure,
                    test_result, failure_reason, repair_status,
                    repair_notes, tested_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id, year, test_date, test_pressure,
                test_result, failure_reason, repair_status,
                repair_notes, tested_by
            ))

            records_created += 1

        print(f"  Created {records_created} records for {year}")

    # Commit changes
    conn.commit()

    # Show summary
    print("\n" + "="*60)
    print("BACKFILL SUMMARY")
    print("="*60)

    for year in [2023, 2024, 2025]:
        cursor.execute('''
            SELECT COUNT(*) FROM iso_hose_tests
            WHERE test_year = ?
        ''', (year,))
        count = cursor.fetchone()[0]
        print(f"{year}: {count} hose test records")

    conn.close()
    print(f"\nSuccessfully created {records_created} backfill records!")

if __name__ == '__main__':
    print("ISO Hose Testing - Backfill 2023/2024 Records")
    print("="*60)
    print("This will copy all 2025 PASS records to 2023 and 2024")
    print("Test dates: Nov 18, 2023 and Nov 16, 2024 (Saturdays)")
    print("="*60)

    response = input("\nProceed with backfill? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        backfill_hose_tests()
    else:
        print("Backfill cancelled.")
