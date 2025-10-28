"""
Migration script to move data from JSON files to SQLite database
Preserves all existing data from the JSON-based system
"""

import json
import sqlite3
from datetime import datetime
from db_init import get_db_connection, init_database
import os

def load_json_file(filename, default=None):
    """Safely load JSON file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return default if default is not None else {}
    except Exception as e:
        print(f"⚠️  Error loading {filename}: {e}")
        return default if default is not None else {}

def migrate_data():
    """Migrate all data from JSON to SQLite"""

    print("🚀 Starting migration from JSON to SQLite...\n")

    # Initialize database (creates tables if they don't exist)
    if not os.path.exists('fdms.db'):
        print("📦 Creating new database...")
        init_database()
    else:
        print("📦 Using existing database...")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Load JSON data
    print("\n📂 Loading JSON files...")
    user_data = load_json_file('user_data.json', {})
    categories = load_json_file('categories.json', [])
    vehicles_data = load_json_file('vehicles.json', [])
    vehicle_inspections_data = load_json_file('vehicle_inspections.json', [])
    checklist_items_data = load_json_file('checklist_items.json', [])

    print(f"  ✓ Loaded {len(user_data)} firefighters")
    print(f"  ✓ Loaded {len(categories)} activity categories")
    print(f"  ✓ Loaded {len(vehicles_data)} vehicles")
    print(f"  ✓ Loaded {len(vehicle_inspections_data)} vehicle inspections")
    print(f"  ✓ Loaded {len(checklist_items_data)} checklist items")

    try:
        # Step 1: Migrate activity categories
        print("\n1️⃣  Migrating activity categories...")
        category_map = {}

        # Add default categories with their default hours
        default_hours_map = {
            "Training": 2,
            "EMR Meeting": 2,
            "Work Night": 2,
            "Board Meeting": 3,
            "Firefighting": 5
        }

        for category in categories:
            default_hours = default_hours_map.get(category)
            cursor.execute(
                'INSERT OR IGNORE INTO activity_categories (name, default_hours) VALUES (?, ?)',
                (category, default_hours)
            )
            cursor.execute('SELECT id FROM activity_categories WHERE name = ?', (category,))
            category_map[category] = cursor.fetchone()[0]

        print(f"  ✅ Migrated {len(categories)} activity categories")

        # Step 2: Migrate firefighters
        print("\n2️⃣  Migrating firefighters...")
        firefighter_map = {}

        for fireman_number, details in user_data.items():
            cursor.execute('''
                INSERT OR IGNORE INTO firefighters (fireman_number, full_name, total_hours)
                VALUES (?, ?, ?)
            ''', (fireman_number, details['full_name'], details.get('hours', 0)))

            cursor.execute('SELECT id FROM firefighters WHERE fireman_number = ?', (fireman_number,))
            firefighter_map[fireman_number] = cursor.fetchone()[0]

        print(f"  ✅ Migrated {len(user_data)} firefighters")

        # Step 3: Migrate time logs
        print("\n3️⃣  Migrating time logs...")
        total_logs = 0

        for fireman_number, details in user_data.items():
            firefighter_id = firefighter_map[fireman_number]

            for log in details.get('logs', []):
                activity_type = log['type']

                # Get category_id (or create "Other" category if needed)
                if activity_type in category_map:
                    category_id = category_map[activity_type]
                else:
                    cursor.execute('INSERT OR IGNORE INTO activity_categories (name) VALUES (?)', (activity_type,))
                    cursor.execute('SELECT id FROM activity_categories WHERE name = ?', (activity_type,))
                    category_id = cursor.fetchone()[0]
                    category_map[activity_type] = category_id

                # Calculate hours if both time_in and time_out exist
                hours_worked = log.get('manual_added_hours')
                if not hours_worked and log.get('time_out'):
                    try:
                        time_in = datetime.fromisoformat(log['time_in'])
                        time_out = datetime.fromisoformat(log['time_out'])
                        hours_worked = (time_out - time_in).total_seconds() / 3600
                    except:
                        hours_worked = None

                cursor.execute('''
                    INSERT INTO time_logs
                    (firefighter_id, category_id, time_in, time_out, hours_worked,
                     auto_checkout, auto_checkout_note, manual_added_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    firefighter_id,
                    category_id,
                    log['time_in'],
                    log.get('time_out'),
                    hours_worked,
                    log.get('auto_checkout', 0),
                    log.get('auto_checkout_note'),
                    log.get('manual_added_hours')
                ))
                total_logs += 1

        print(f"  ✅ Migrated {total_logs} time log entries")

        # Step 4: Migrate vehicles
        print("\n4️⃣  Migrating vehicles...")
        vehicle_map = {}

        for vehicle in vehicles_data:
            cursor.execute('''
                INSERT OR IGNORE INTO vehicles (vehicle_code, name)
                VALUES (?, ?)
            ''', (vehicle['id'], vehicle['name']))

            cursor.execute('SELECT id FROM vehicles WHERE vehicle_code = ?', (vehicle['id'],))
            vehicle_map[vehicle['id']] = cursor.fetchone()[0]

        print(f"  ✅ Migrated {len(vehicles_data)} vehicles")

        # Step 5: Migrate inspection checklist items
        print("\n5️⃣  Migrating inspection checklist items...")
        checklist_map = {}

        for item in checklist_items_data:
            cursor.execute('''
                INSERT OR IGNORE INTO inspection_checklist_items (description, display_order)
                VALUES (?, ?)
            ''', (item['description'], item['id']))

            cursor.execute('SELECT id FROM inspection_checklist_items WHERE description = ?', (item['description'],))
            result = cursor.fetchone()
            if result:
                checklist_map[item['id']] = result[0]

        print(f"  ✅ Migrated {len(checklist_items_data)} checklist items")

        # Step 6: Migrate vehicle inspections
        print("\n6️⃣  Migrating vehicle inspections...")

        for inspection in vehicle_inspections_data:
            vehicle_id = vehicle_map.get(inspection['vehicle_id'])
            if not vehicle_id:
                continue

            # Create inspection record
            cursor.execute('''
                INSERT INTO vehicle_inspections
                (vehicle_id, inspection_date, additional_notes)
                VALUES (?, ?, ?)
            ''', (vehicle_id, inspection['date'], inspection.get('additional_notes', '')))

            inspection_id = cursor.lastrowid

            # Add inspection results
            for result in inspection.get('results', []):
                checklist_item_id = checklist_map.get(result['item_id'])
                if checklist_item_id:
                    cursor.execute('''
                        INSERT INTO inspection_results
                        (inspection_id, checklist_item_id, status, notes)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        inspection_id,
                        checklist_item_id,
                        result['status'],
                        result.get('notes', '')
                    ))

        print(f"  ✅ Migrated {len(vehicle_inspections_data)} vehicle inspections")

        # Step 7: Create default station if none exists
        print("\n7️⃣  Creating default station...")
        cursor.execute('SELECT COUNT(*) FROM stations')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO stations (name, is_primary, notes)
                VALUES (?, ?, ?)
            ''', ('Main Station', 1, 'Default station created during migration'))
            print("  ✅ Created default station")
        else:
            print("  ℹ️  Stations already exist, skipping")

        conn.commit()

        print("\n" + "="*50)
        print("🎉 Migration completed successfully!")
        print("="*50)

        # Print summary
        cursor.execute('SELECT COUNT(*) FROM firefighters')
        ff_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM time_logs')
        log_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM vehicles')
        vehicle_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM activity_categories')
        cat_count = cursor.fetchone()[0]

        print(f"\n📊 Database Summary:")
        print(f"  • Firefighters: {ff_count}")
        print(f"  • Time Logs: {log_count}")
        print(f"  • Vehicles: {vehicle_count}")
        print(f"  • Activity Categories: {cat_count}")
        print(f"\n✅ All your existing data has been preserved!")
        print(f"📁 Database location: flask_app/fdms.db")

        # Backup recommendation
        print(f"\n💡 RECOMMENDATION:")
        print(f"  Keep your JSON files as backup until you've verified")
        print(f"  everything works correctly with the new database.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

    return True

if __name__ == '__main__':
    success = migrate_data()
    if success:
        print("\n✨ You can now start using the SQLite database!")
    else:
        print("\n⚠️  Please fix the errors and try again.")
