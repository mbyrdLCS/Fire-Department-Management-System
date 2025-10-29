"""
Add default activity categories to existing database
Run this once to populate default categories
"""

from db_init import get_db_connection

def add_default_categories():
    """Add default activity categories if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("📋 Adding default activity categories...")

    default_categories = [
        ('Work night', None),
        ('Training', None),
        ('Board Meeting', None),
        ('EMR Meeting', None),
        ('Other', None)
    ]

    for category_name, default_hours in default_categories:
        cursor.execute('''
            INSERT OR IGNORE INTO activity_categories (name, default_hours)
            VALUES (?, ?)
        ''', (category_name, default_hours))
        print(f"✅ Added category: {category_name}")

    conn.commit()

    # Show all categories
    cursor.execute('SELECT name FROM activity_categories ORDER BY id')
    categories = cursor.fetchall()

    print(f"\n✅ Current categories in database:")
    for cat in categories:
        print(f"   - {cat[0]}")

    conn.close()
    print("\n🎉 Done!")

if __name__ == '__main__':
    add_default_categories()
