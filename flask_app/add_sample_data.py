"""
Add sample vehicles and inspection checklist items to the database
"""

from db_init import get_db_connection

def add_sample_data():
    """Add sample vehicles and checklist items"""

    print("📦 Adding sample data to database...\n")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Add sample vehicles
        print("🚒 Adding sample vehicles...")
        vehicles = [
            ('E1', 'Engine 1', 'Engine'),
            ('E2', 'Engine 2', 'Engine'),
            ('L1', 'Ladder 1', 'Ladder'),
            ('T2', 'Tanker 2', 'Tanker'),
        ]

        for vehicle_code, name, vehicle_type in vehicles:
            cursor.execute('''
                INSERT OR IGNORE INTO vehicles (vehicle_code, name, vehicle_type, status)
                VALUES (?, ?, ?, 'active')
            ''', (vehicle_code, name, vehicle_type))
            print(f"  ✓ Added {name}")

        # Add sample inspection checklist items
        print("\n📋 Adding inspection checklist items...")
        checklist_items = [
            ('Check engine oil level', 'Mechanical', 1),
            ('Check tire pressure', 'Mechanical', 2),
            ('Check emergency lights', 'Safety', 3),
            ('Check brake fluid level', 'Mechanical', 4),
            ('Test horn and sirens', 'Safety', 5),
            ('Check all exterior lights', 'Safety', 6),
            ('Inspect windshield and wipers', 'Safety', 7),
            ('Check water tank level', 'Equipment', 8),
            ('Inspect hose connections', 'Equipment', 9),
            ('Test radio communications', 'Communications', 10),
        ]

        for description, category, order in checklist_items:
            cursor.execute('''
                INSERT OR IGNORE INTO inspection_checklist_items
                (description, category, display_order, is_active)
                VALUES (?, ?, ?, 1)
            ''', (description, category, order))
            print(f"  ✓ Added: {description}")

        conn.commit()

        print("\n✅ Sample data added successfully!")

        # Show summary
        cursor.execute('SELECT COUNT(*) FROM vehicles')
        vehicle_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM inspection_checklist_items')
        checklist_count = cursor.fetchone()[0]

        print(f"\n📊 Database now contains:")
        print(f"  • {vehicle_count} vehicles")
        print(f"  • {checklist_count} inspection checklist items")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error adding sample data: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_sample_data()
