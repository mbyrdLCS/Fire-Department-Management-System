#!/usr/bin/env python3
"""
Recreate the 10 Station 1 vehicles in the database
"""
import sqlite3

DB_PATH = "flask_app/database/fire_dept.db"

vehicles = [
    {"code": "R2", "name": "Rescue 2", "type": "Rescue"},
    {"code": "G5", "name": "Grass 5", "type": "Grass"},
    {"code": "R1", "name": "Rescue 1", "type": "Rescue"},
    {"code": "P2", "name": "Pumper 2", "type": "Pumper"},
    {"code": "G1", "name": "Grass 1", "type": "Grass"},
    {"code": "P4", "name": "Pumper 4", "type": "Pumper"},
    {"code": "G4", "name": "Grass 4", "type": "Grass"},
    {"code": "T6", "name": "Tanker 6", "type": "Tanker"},
    {"code": "T2", "name": "Tanker 2", "type": "Tanker"},
    {"code": "T3", "name": "Tanker 3", "type": "Tanker"},
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🚒 Recreating Station 1 vehicles...")

    for vehicle in vehicles:
        cursor.execute('''
            INSERT INTO vehicles (vehicle_code, name, vehicle_type, status, station_id)
            VALUES (?, ?, ?, 'active', 1)
        ''', (vehicle['code'], vehicle['name'], vehicle['type']))

        vehicle_id = cursor.lastrowid
        print(f"  ✓ Created {vehicle['name']} (ID: {vehicle_id})")

    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    count = cursor.fetchone()[0]
    print(f"\n✅ Total vehicles: {count}")

    conn.close()

if __name__ == '__main__':
    main()
