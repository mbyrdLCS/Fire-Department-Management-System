#!/usr/bin/env python3
"""
Merge duplicate "Work night" categories into "Work Night"

This script safely merges any lowercase "Work night" category with
the properly capitalized "Work Night" category, preserving all time logs.
"""

import sqlite3
import os
import sys

# Get database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'flask_app', 'database', 'fire_dept.db')

def merge_work_night_categories():
    """Merge duplicate work night categories"""

    print("🔍 Checking for duplicate 'Work night' categories...")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Find all "work night" categories (case insensitive)
        cursor.execute('''
            SELECT id, name,
                   (SELECT COUNT(*) FROM time_logs WHERE category_id = activity_categories.id) as log_count
            FROM activity_categories
            WHERE name LIKE '%work%night%' COLLATE NOCASE
            ORDER BY name
        ''')

        categories = cursor.fetchall()

        if len(categories) == 0:
            print("❌ No 'Work Night' categories found!")
            return False
        elif len(categories) == 1:
            print(f"✅ Only one 'Work Night' category exists: '{categories[0][1]}' with {categories[0][2]} logs")
            print("   No merge needed!")
            return True

        print(f"\n📊 Found {len(categories)} 'Work Night' categories:")
        for cat_id, name, log_count in categories:
            print(f"   - ID {cat_id}: '{name}' ({log_count} logs)")

        # Determine which one to keep (prefer "Work Night" with capital letters)
        keep_category = None
        merge_categories = []

        for cat_id, name, log_count in categories:
            if name == "Work Night":  # Exact match with proper capitalization
                keep_category = (cat_id, name, log_count)
            else:
                merge_categories.append((cat_id, name, log_count))

        # If no "Work Night" exists, keep the one with most logs
        if keep_category is None:
            categories_sorted = sorted(categories, key=lambda x: x[2], reverse=True)
            keep_category = categories_sorted[0]
            merge_categories = categories_sorted[1:]

        if not merge_categories:
            print("✅ No duplicates to merge!")
            return True

        print(f"\n📌 Will keep: ID {keep_category[0]} - '{keep_category[1]}' ({keep_category[2]} logs)")
        print(f"🔀 Will merge and delete:")

        total_logs_moved = 0
        for cat_id, name, log_count in merge_categories:
            print(f"   - ID {cat_id}: '{name}' ({log_count} logs)")
            total_logs_moved += log_count

        # Ask for confirmation
        response = input(f"\n⚠️  This will move {total_logs_moved} time logs. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cancelled by user")
            return False

        # Perform the merge
        print("\n🔄 Starting merge...")

        for cat_id, name, log_count in merge_categories:
            if log_count > 0:
                # Update time_logs to point to the kept category
                cursor.execute('''
                    UPDATE time_logs
                    SET category_id = ?
                    WHERE category_id = ?
                ''', (keep_category[0], cat_id))
                print(f"   ✓ Moved {log_count} logs from '{name}' to '{keep_category[1]}'")

            # Delete the duplicate category
            cursor.execute('DELETE FROM activity_categories WHERE id = ?', (cat_id,))
            print(f"   ✓ Deleted category '{name}' (ID {cat_id})")

        conn.commit()

        # Verify the result
        cursor.execute('''
            SELECT COUNT(*) FROM time_logs WHERE category_id = ?
        ''', (keep_category[0],))

        final_count = cursor.fetchone()[0]
        expected_count = keep_category[2] + total_logs_moved

        print(f"\n✅ Merge complete!")
        print(f"   Final category: '{keep_category[1]}' (ID {keep_category[0]})")
        print(f"   Total logs: {final_count} (expected {expected_count})")

        if final_count == expected_count:
            print("   ✓ Log count matches - merge successful!")
        else:
            print("   ⚠️  Warning: Log count mismatch!")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during merge: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Merge 'Work night' Categories Script")
    print("=" * 60)
    print()

    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found at: {DATABASE_PATH}")
        sys.exit(1)

    print(f"📁 Database: {DATABASE_PATH}")
    print()

    success = merge_work_night_categories()

    print()
    print("=" * 60)

    if success:
        print("✅ Script completed successfully!")
        sys.exit(0)
    else:
        print("❌ Script completed with errors")
        sys.exit(1)
