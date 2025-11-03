#!/usr/bin/env python3
"""
Fix Hours Discrepancy Script
Recalculates total_hours for all firefighters based on their actual time logs
Run this script to fix any discrepancies between stored hours and calculated hours
"""

import sys
import os

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import get_db_connection

def fix_hours_discrepancy():
    """Recalculate and fix total_hours for all firefighters"""

    conn = get_db_connection()
    cursor = conn.cursor()

    print("🔍 Checking for hours discrepancies...\n")

    # First, identify firefighters with discrepancies
    cursor.execute('''
        SELECT
            f.id,
            f.fireman_number,
            f.full_name,
            COALESCE(f.total_hours, 0) as stored_hours,
            COUNT(tl.id) as log_count,
            COALESCE(SUM(COALESCE(tl.manual_added_hours, tl.hours_worked, 0)), 0) as calculated_hours
        FROM firefighters f
        LEFT JOIN time_logs tl ON f.id = tl.firefighter_id
        GROUP BY f.id
        ORDER BY f.fireman_number
    ''')

    firefighters = cursor.fetchall()
    discrepancies = []

    for row in firefighters:
        ff_id, number, name, stored, log_count, calculated = row
        # Handle None values
        stored = stored or 0
        calculated = calculated or 0
        difference = abs(stored - calculated)

        if difference > 0.01:  # More than 1 cent difference
            discrepancies.append({
                'id': ff_id,
                'number': number,
                'name': name,
                'stored': stored,
                'calculated': calculated,
                'difference': stored - calculated,
                'log_count': log_count
            })

    if not discrepancies:
        print("✅ No discrepancies found! All firefighter hours are correct.")
        conn.close()
        return

    print(f"⚠️  Found {len(discrepancies)} firefighter(s) with hour discrepancies:\n")

    for disc in discrepancies:
        print(f"  #{disc['number']} - {disc['name']}")
        print(f"    Stored: {disc['stored']:.2f} hours")
        print(f"    Calculated: {disc['calculated']:.2f} hours")
        print(f"    Difference: {disc['difference']:.2f} hours ({disc['log_count']} logs)")
        print()

    # Ask for confirmation
    response = input("🔧 Fix these discrepancies? (yes/no): ").strip().lower()

    if response != 'yes':
        print("❌ Aborted. No changes made.")
        conn.close()
        return

    print("\n🔨 Fixing discrepancies...\n")

    # Update each firefighter's total_hours based on actual logs
    # Use COALESCE to pick manual_added_hours if exists, else hours_worked (never add them together)
    cursor.execute('''
        UPDATE firefighters
        SET total_hours = COALESCE((
            SELECT SUM(COALESCE(manual_added_hours, hours_worked, 0))
            FROM time_logs
            WHERE time_logs.firefighter_id = firefighters.id
        ), 0),
        updated_at = CURRENT_TIMESTAMP
    ''')

    conn.commit()

    # Verify the fix
    cursor.execute('''
        SELECT
            f.fireman_number,
            f.full_name,
            COALESCE(f.total_hours, 0) as new_hours,
            COUNT(tl.id) as log_count
        FROM firefighters f
        LEFT JOIN time_logs tl ON f.id = tl.firefighter_id
        GROUP BY f.id
        ORDER BY f.fireman_number
    ''')

    fixed_firefighters = cursor.fetchall()

    print("✅ Fixed! Updated hours:\n")
    for row in fixed_firefighters:
        number, name, hours, log_count = row
        # Check if this firefighter was in discrepancies list
        was_fixed = any(d['number'] == number for d in discrepancies)
        marker = " ✓" if was_fixed else ""
        print(f"  #{number} - {name}: {hours:.2f} hours ({log_count} logs){marker}")

    print(f"\n✅ Successfully fixed {len(discrepancies)} firefighter(s)")
    print("💾 Changes have been saved to the database.")

    conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Fire Department Management System - Hours Fix Script")
    print("=" * 60)
    print()

    try:
        fix_hours_discrepancy()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
