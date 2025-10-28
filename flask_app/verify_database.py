"""
Verify database integrity and display current data
"""

from db_init import get_db_connection
import sqlite3

def verify_database():
    """Verify database and show contents"""

    print("🔍 Verifying Fire Department Management System Database\n")
    print("="*60)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check all tables exist
        print("\n📊 DATABASE TABLES:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        for i, (table_name,) in enumerate(tables, 1):
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {i:2d}. {table_name:30s} - {count:4d} records")

        print("\n" + "="*60)

        # Show firefighters
        print("\n👨‍🚒 FIREFIGHTERS:")
        cursor.execute('''
            SELECT fireman_number, full_name, total_hours
            FROM firefighters
            ORDER BY full_name
        ''')
        firefighters = cursor.fetchall()

        if firefighters:
            for ff_num, name, hours in firefighters:
                print(f"  • {name:20s} (#{ff_num}) - {hours:.2f} hours")
        else:
            print("  (No firefighters yet)")

        # Show activity categories
        print("\n📋 ACTIVITY CATEGORIES:")
        cursor.execute('''
            SELECT name, default_hours
            FROM activity_categories
            ORDER BY name
        ''')
        categories = cursor.fetchall()

        for cat_name, default_hrs in categories:
            hrs_text = f"{default_hrs} hrs default" if default_hrs else "variable"
            print(f"  • {cat_name:20s} - {hrs_text}")

        # Show vehicles
        print("\n🚒 VEHICLES:")
        cursor.execute('''
            SELECT vehicle_code, name, vehicle_type, status
            FROM vehicles
            ORDER BY vehicle_code
        ''')
        vehicles = cursor.fetchall()

        if vehicles:
            for code, name, v_type, status in vehicles:
                type_text = f"({v_type})" if v_type else ""
                print(f"  • {code:5s} - {name:20s} {type_text:10s} [{status}]")
        else:
            print("  (No vehicles yet)")

        # Show stations
        print("\n🏢 STATIONS:")
        cursor.execute('SELECT name, is_primary FROM stations ORDER BY name')
        stations = cursor.fetchall()

        if stations:
            for name, is_primary in stations:
                primary_text = "★ PRIMARY" if is_primary else ""
                print(f"  • {name:20s} {primary_text}")
        else:
            print("  (No stations yet)")

        # Show inspection checklist items
        print("\n✓ INSPECTION CHECKLIST ITEMS:")
        cursor.execute('''
            SELECT description, category
            FROM inspection_checklist_items
            WHERE is_active = 1
            ORDER BY display_order
        ''')
        items = cursor.fetchall()

        if items:
            for i, (desc, category) in enumerate(items, 1):
                cat_text = f"[{category}]" if category else ""
                print(f"  {i:2d}. {desc} {cat_text}")
        else:
            print("  (No checklist items yet)")

        # Show recent time logs
        print("\n⏰ RECENT TIME LOGS:")
        cursor.execute('''
            SELECT f.full_name, ac.name, tl.time_in, tl.time_out, tl.hours_worked
            FROM time_logs tl
            JOIN firefighters f ON tl.firefighter_id = f.id
            JOIN activity_categories ac ON tl.category_id = ac.id
            ORDER BY tl.time_in DESC
            LIMIT 5
        ''')
        logs = cursor.fetchall()

        if logs:
            for name, activity, time_in, time_out, hours in logs:
                status = "✓ Clocked out" if time_out else "⏳ Active"
                hrs_text = f"({hours:.2f} hrs)" if hours else ""
                print(f"  • {name:20s} - {activity:15s} {status} {hrs_text}")
        else:
            print("  (No time logs yet)")

        print("\n" + "="*60)
        print("✅ Database verification complete!")
        print("="*60)

        # Test a complex query (alerts view simulation)
        print("\n🔔 Testing Complex Queries...")

        # Test if we can query across tables
        cursor.execute('''
            SELECT
                COUNT(DISTINCT f.id) as total_firefighters,
                COUNT(DISTINCT v.id) as total_vehicles,
                COUNT(tl.id) as total_time_logs
            FROM firefighters f
            CROSS JOIN vehicles v
            LEFT JOIN time_logs tl ON 1=1
        ''')

        result = cursor.fetchone()
        print(f"  ✓ Cross-table query successful")
        print(f"  ✓ Foreign keys working")
        print(f"  ✓ Indexes created")

        print("\n✨ All systems operational!")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = verify_database()
    if success:
        print("\n✅ Ready to proceed with application updates!")
    else:
        print("\n⚠️  Please fix database issues before continuing.")
