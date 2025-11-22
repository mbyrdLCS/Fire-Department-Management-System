#!/usr/bin/env python3
"""
Add location field for hoses stored at specific locations (churches, schools, etc.)
"""

import sys
import os

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import get_db_connection

def add_hose_location():
    """Add location field to inventory_items for hoses at specific locations"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("🔨 Adding Location Field for Hoses...")

    # Add location column to inventory_items
    try:
        cursor.execute('ALTER TABLE inventory_items ADD COLUMN location TEXT')
        print("✅ Added column: location")
    except:
        print("⚠️  Column 'location' already exists")

    conn.commit()
    conn.close()

    print("\n🎉 Location field added successfully!")
    print("\n📋 How it works:")
    print("   - Hoses can now be assigned to a vehicle OR a location")
    print("   - Locations: 'First Baptist Church', 'Elementary School', etc.")
    print("   - Both vehicle hoses and location hoses will appear in testing")

if __name__ == '__main__':
    add_hose_location()
