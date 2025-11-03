#!/usr/bin/env python3
"""
Migrate data from old fire department app to new database-based app

IMPORTANT: This will clear existing firefighter and time log data!
Make sure to backup your database first.
"""
import json
import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path

# Paths
OLD_APP_BACKUP = "/Users/MJB/Downloads/fire_dept_app_backup (1)"
NEW_APP_DB = "flask_app/database/fire_dept.db"

def backup_current_database():
    """Create a backup of the current database"""
    if os.path.exists(NEW_APP_DB):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{NEW_APP_DB}.pre_migration_backup_{timestamp}"

        import shutil
        shutil.copy2(NEW_APP_DB, backup_path)
        print(f"✓ Backed up current database to: {backup_path}")
        return backup_path
    return None

def load_old_app_data():
    """Load data from old app backup"""
    print("\n📂 Loading old app data...")

    # Load user data (firefighters and logs)
    user_data_path = os.path.join(OLD_APP_BACKUP, "user_data.json")
    with open(user_data_path, 'r') as f:
        user_data = json.load(f)

    print(f"  ✓ Loaded {len(user_data)} firefighters")

    # Load categories
    categories_path = os.path.join(OLD_APP_BACKUP, "categories.json")
    with open(categories_path, 'r') as f:
        categories = json.load(f)

    print(f"  ✓ Loaded {len(categories)} categories")

    return user_data, categories

def clear_existing_data(conn):
    """Clear existing firefighter and time log data (keeping vehicles/checklists)"""
    print("\n🗑️  Clearing existing firefighter data...")
    cursor = conn.cursor()

    try:
        # Clear time logs
        cursor.execute("DELETE FROM time_logs")
        logs_deleted = cursor.rowcount

        # Clear firefighters
        cursor.execute("DELETE FROM firefighters")
        ff_deleted = cursor.rowcount

        conn.commit()
        print(f"  ✓ Deleted {ff_deleted} firefighters and {logs_deleted} time logs")

    except Exception as e:
        print(f"  ❌ Error clearing data: {e}")
        conn.rollback()
        raise

def import_categories(conn, categories):
    """Import activity categories and return mapping of name -> id"""
    print("\n📋 Importing activity categories...")
    cursor = conn.cursor()

    category_map = {}

    try:
        # Clear existing categories (except defaults)
        cursor.execute("DELETE FROM activity_categories WHERE name NOT IN ('Work night', 'Training', 'Board Meeting', 'EMR Meeting', 'Other')")

        # Import categories with default hours
        default_hours_map = {
            "Work Night": 2.0,
            "Training": 2.0,
            "Board Meeting": 2.0,
            "EMR Meeting": 2.0
        }

        for category in categories:
            default_hours = default_hours_map.get(category, 0.0)

            # Check if category already exists
            cursor.execute('SELECT id FROM activity_categories WHERE name = ?', (category,))
            existing = cursor.fetchone()

            if existing:
                category_map[category] = existing[0]
            else:
                cursor.execute('''
                    INSERT INTO activity_categories (name, default_hours)
                    VALUES (?, ?)
                ''', (category, default_hours))
                category_map[category] = cursor.lastrowid

        # Also get "Other" category for unknown types
        cursor.execute('SELECT id FROM activity_categories WHERE name = ?', ('Other',))
        result = cursor.fetchone()
        if result:
            category_map['_OTHER_'] = result[0]

        conn.commit()
        print(f"  ✓ Imported/found {len(category_map)} categories")

        return category_map

    except Exception as e:
        print(f"  ❌ Error importing categories: {e}")
        conn.rollback()
        raise

def import_firefighters(conn, user_data, category_map):
    """Import firefighters and their time logs"""
    print("\n👨‍🚒 Importing firefighters and time logs...")
    cursor = conn.cursor()

    total_logs = 0

    try:
        for ff_number, ff_data in user_data.items():
            full_name = ff_data['full_name']

            # Insert firefighter (using fireman_number not firefighter_number)
            cursor.execute('''
                INSERT INTO firefighters (fireman_number, full_name, total_hours, created_at)
                VALUES (?, ?, 0, CURRENT_TIMESTAMP)
            ''', (ff_number, full_name))

            firefighter_id = cursor.lastrowid

            # Insert time logs
            logs = ff_data.get('logs', [])
            for log in logs:
                activity_type = log.get('type', 'Other')
                clock_in = log.get('time_in')
                clock_out = log.get('time_out')

                # Get category ID
                category_id = category_map.get(activity_type, category_map.get('_OTHER_'))

                # Parse datetime strings
                # Format: "2024-11-16T08:30:00-06:00"
                try:
                    clock_in_dt = datetime.fromisoformat(clock_in)
                    clock_out_dt = datetime.fromisoformat(clock_out) if clock_out else None

                    # Calculate hours
                    if clock_out_dt:
                        hours = (clock_out_dt - clock_in_dt).total_seconds() / 3600
                    else:
                        hours = 0

                    # Check for manual hours
                    manual_hours = log.get('manual_added_hours')

                    # Check for auto checkout
                    auto_checkout = log.get('auto_checkout', False)
                    auto_checkout_note = log.get('auto_checkout_note', '')

                    # Insert time log (using hours_worked, category_id, etc.)
                    cursor.execute('''
                        INSERT INTO time_logs
                        (firefighter_id, category_id, time_in, time_out, hours_worked,
                         auto_checkout, auto_checkout_note, manual_added_hours, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (firefighter_id, category_id,
                          clock_in_dt.isoformat(),
                          clock_out_dt.isoformat() if clock_out_dt else None,
                          hours,
                          1 if auto_checkout else 0,
                          auto_checkout_note,
                          manual_hours,
                          clock_in_dt.isoformat()))

                    total_logs += 1

                except Exception as e:
                    print(f"    ⚠️  Skipping log for {full_name}: {e}")
                    continue

            # Update firefighter's total hours
            cursor.execute('''
                UPDATE firefighters
                SET total_hours = (
                    SELECT SUM(COALESCE(manual_added_hours, hours_worked))
                    FROM time_logs
                    WHERE firefighter_id = ?
                )
                WHERE id = ?
            ''', (firefighter_id, firefighter_id))

            print(f"  ✓ Imported {full_name} (#{ff_number}) - {len(logs)} logs")

        conn.commit()
        print(f"\n✅ Total: {len(user_data)} firefighters, {total_logs} time logs imported")

    except Exception as e:
        print(f"  ❌ Error importing firefighters: {e}")
        conn.rollback()
        raise

def verify_migration(conn):
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    cursor = conn.cursor()

    # Count firefighters
    cursor.execute("SELECT COUNT(*) FROM firefighters")
    ff_count = cursor.fetchone()[0]

    # Count time logs
    cursor.execute("SELECT COUNT(*) FROM time_logs")
    log_count = cursor.fetchone()[0]

    # Count categories
    cursor.execute("SELECT COUNT(*) FROM activity_categories")
    cat_count = cursor.fetchone()[0]

    # Get top 5 firefighters by hours
    cursor.execute('''
        SELECT f.fireman_number, f.full_name, f.total_hours
        FROM firefighters f
        ORDER BY f.total_hours DESC
        LIMIT 5
    ''')

    top_performers = cursor.fetchall()

    print(f"\n📊 Migration Summary:")
    print(f"  Firefighters: {ff_count}")
    print(f"  Time Logs: {log_count}")
    print(f"  Categories: {cat_count}")
    print(f"\n  Top 5 by Hours:")
    for ff_num, name, hours in top_performers:
        print(f"    #{ff_num} {name}: {hours:.2f} hours")

def main():
    """Main migration process"""
    import sys

    print("=" * 70)
    print("FIRE DEPARTMENT DATA MIGRATION")
    print("Old App → New Database-Based App")
    print("=" * 70)

    # Check for --confirm flag
    if '--confirm' not in sys.argv:
        print("\n⚠️  WARNING: This will DELETE all existing firefighter data!")
        print("   (Vehicles and checklists will NOT be affected)")
        print("\nTo run this migration, use:")
        print("  python3 migrate_old_app_data.py --confirm")
        return

    print("\n✓ Running migration with --confirm flag...")

    # Step 1: Backup current database
    print("\n" + "=" * 70)
    print("STEP 1: Backup Current Database")
    print("=" * 70)
    backup_path = backup_current_database()

    # Step 2: Load old app data
    print("\n" + "=" * 70)
    print("STEP 2: Load Old App Data")
    print("=" * 70)
    user_data, categories = load_old_app_data()

    # Step 3: Connect to new database
    print("\n" + "=" * 70)
    print("STEP 3: Connect to New Database")
    print("=" * 70)
    if not os.path.exists(NEW_APP_DB):
        print(f"❌ Database not found: {NEW_APP_DB}")
        return

    conn = sqlite3.connect(NEW_APP_DB)
    print(f"✓ Connected to: {NEW_APP_DB}")

    try:
        # Step 4: Clear existing data
        print("\n" + "=" * 70)
        print("STEP 4: Clear Existing Firefighter Data")
        print("=" * 70)
        clear_existing_data(conn)

        # Step 5: Import categories
        print("\n" + "=" * 70)
        print("STEP 5: Import Activity Categories")
        print("=" * 70)
        category_map = import_categories(conn, categories)

        # Step 6: Import firefighters and logs
        print("\n" + "=" * 70)
        print("STEP 6: Import Firefighters and Time Logs")
        print("=" * 70)
        import_firefighters(conn, user_data, category_map)

        # Step 7: Verify
        print("\n" + "=" * 70)
        print("STEP 7: Verify Migration")
        print("=" * 70)
        verify_migration(conn)

        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 70)

        if backup_path:
            print(f"\n💾 Backup saved to: {backup_path}")
            print("   (You can restore from this if needed)")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nRestoring from backup...")
        conn.close()

        if backup_path:
            import shutil
            shutil.copy2(backup_path, NEW_APP_DB)
            print("✓ Restored from backup")

    finally:
        conn.close()

if __name__ == '__main__':
    main()
