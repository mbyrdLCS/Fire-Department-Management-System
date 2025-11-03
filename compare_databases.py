#!/usr/bin/env python3
"""
Compare Local vs Production Database
Shows differences in firefighter hours and log counts
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import get_db_connection

def compare_databases():
    """Compare local database firefighter data"""

    conn = get_db_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("LOCAL DATABASE SUMMARY")
    print("=" * 70)

    cursor.execute('''
        SELECT
            f.fireman_number,
            f.full_name,
            f.total_hours,
            COUNT(tl.id) as log_count,
            SUM(COALESCE(tl.manual_added_hours, tl.hours_worked, 0)) as calculated_hours
        FROM firefighters f
        LEFT JOIN time_logs tl ON f.id = tl.firefighter_id
        GROUP BY f.id
        ORDER BY f.full_name
    ''')

    firefighters = cursor.fetchall()

    print(f"\n{'#':<5} {'Name':<25} {'Stored Hours':<15} {'Logs':<8} {'Calculated Hours':<15}")
    print("-" * 70)

    total_stored = 0
    total_calculated = 0
    total_logs = 0

    for row in firefighters:
        number, name, stored, logs, calculated = row
        stored = stored or 0
        calculated = calculated or 0
        total_stored += stored
        total_calculated += calculated
        total_logs += logs

        match = "✓" if abs(stored - calculated) < 0.01 else "✗"
        print(f"{number:<5} {name:<25} {stored:<15.2f} {logs:<8} {calculated:<15.2f} {match}")

    print("-" * 70)
    print(f"{'TOTALS':<5} {'':<25} {total_stored:<15.2f} {total_logs:<8} {total_calculated:<15.2f}")
    print()
    print(f"Total Firefighters: {len(firefighters)}")
    print(f"Total Time Logs: {total_logs}")
    print(f"Total Hours: {total_stored:.2f}")
    print()

    # Check for discrepancies
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT f.id
            FROM firefighters f
            LEFT JOIN time_logs tl ON f.id = tl.firefighter_id
            GROUP BY f.id
            HAVING ABS(COALESCE(f.total_hours, 0) - COALESCE(SUM(COALESCE(tl.manual_added_hours, tl.hours_worked, 0)), 0)) > 0.01
        )
    ''')

    result = cursor.fetchone()
    discrepancies = result[0] if result else 0

    if discrepancies > 0:
        print(f"⚠️  WARNING: {discrepancies} firefighter(s) have hour discrepancies!")
        print("   Run 'python3 fix_hours_discrepancy.py' to fix.")
    else:
        print("✅ All firefighter hours match their time logs.")

    conn.close()

    print("\n" + "=" * 70)
    print("INSTRUCTIONS FOR PYTHONANYWHERE")
    print("=" * 70)
    print()
    print("1. Download the local database:")
    print("   File: flask_app/database/fire_dept.db")
    print()
    print("2. Upload to PythonAnywhere:")
    print("   - Go to Files tab")
    print("   - Navigate to: ~/Fire-Department-Management-System/flask_app/database/")
    print("   - Backup current file: mv fire_dept.db fire_dept.db.backup")
    print("   - Upload the new fire_dept.db")
    print()
    print("3. Reload your web app")
    print()
    print("OR use git pull + migration:")
    print("   cd ~/Fire-Department-Management-System")
    print("   git pull")
    print("   python3 fix_hours_discrepancy.py")
    print()

if __name__ == '__main__':
    try:
        compare_databases()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
