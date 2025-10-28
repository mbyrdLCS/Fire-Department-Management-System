"""
Database initialization script for Fire Department Management System
Creates all tables, indexes, and views for the SQLite database
"""

import sqlite3
import os
from datetime import datetime

DATABASE_NAME = 'fdms.db'

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_database():
    """Initialize the complete database schema"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("🔨 Creating Fire Department Management System Database...")

    # 1. Firefighters table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS firefighters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fireman_number TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        total_hours REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created table: firefighters")

    # 2. Activity categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        default_hours REAL DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created table: activity_categories")

    # 3. Time logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS time_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firefighter_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        time_in TIMESTAMP NOT NULL,
        time_out TIMESTAMP,
        hours_worked REAL,
        auto_checkout BOOLEAN DEFAULT 0,
        auto_checkout_note TEXT,
        manual_added_hours REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (firefighter_id) REFERENCES firefighters(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES activity_categories(id)
    )
    ''')
    print("✅ Created table: time_logs")

    # 4. Stations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        is_primary BOOLEAN DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created table: stations")

    # 5. Vehicles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        vehicle_type TEXT,
        station_id INTEGER,
        year INTEGER,
        make TEXT,
        model TEXT,
        vin TEXT,
        license_plate TEXT,
        purchase_date DATE,
        purchase_cost REAL,
        current_value REAL,
        status TEXT DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(id)
    )
    ''')
    print("✅ Created table: vehicles")

    # 6. Inspection checklist items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspection_checklist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        category TEXT,
        is_active BOOLEAN DEFAULT 1,
        display_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created table: inspection_checklist_items")

    # 7. Vehicle inspections table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicle_inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        inspector_id INTEGER,
        inspection_date TIMESTAMP NOT NULL,
        passed BOOLEAN DEFAULT 1,
        additional_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
        FOREIGN KEY (inspector_id) REFERENCES firefighters(id)
    )
    ''')
    print("✅ Created table: vehicle_inspections")

    # 8. Inspection results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspection_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_id INTEGER NOT NULL,
        checklist_item_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (inspection_id) REFERENCES vehicle_inspections(id) ON DELETE CASCADE,
        FOREIGN KEY (checklist_item_id) REFERENCES inspection_checklist_items(id)
    )
    ''')
    print("✅ Created table: inspection_results")

    # 9. Inventory items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        item_code TEXT UNIQUE,
        serial_number TEXT,
        category TEXT,
        subcategory TEXT,
        description TEXT,
        manufacturer TEXT,
        model_number TEXT,
        unit_of_measure TEXT,
        cost_per_unit REAL,
        current_value REAL,
        min_quantity INTEGER DEFAULT 0,
        location_type TEXT,
        is_consumable BOOLEAN DEFAULT 0,
        requires_certification BOOLEAN DEFAULT 0,
        requires_maintenance BOOLEAN DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created table: inventory_items")

    # 10. Inventory transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL,
        quantity_change INTEGER NOT NULL,
        quantity_after INTEGER NOT NULL,
        firefighter_id INTEGER,
        vehicle_id INTEGER,
        station_id INTEGER,
        notes TEXT,
        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
        FOREIGN KEY (firefighter_id) REFERENCES firefighters(id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (station_id) REFERENCES stations(id)
    )
    ''')
    print("✅ Created table: inventory_transactions")

    # 11. Station inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS station_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_checked TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
        UNIQUE(station_id, item_id)
    )
    ''')
    print("✅ Created table: station_inventory")

    # 12. Vehicle inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicle_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_checked TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
        UNIQUE(vehicle_id, item_id)
    )
    ''')
    print("✅ Created table: vehicle_inventory")

    # 13. Maintenance schedules table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_type TEXT NOT NULL,
        item_id INTEGER,
        vehicle_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        interval_type TEXT NOT NULL,
        interval_value INTEGER NOT NULL,
        cost_estimate REAL,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
    )
    ''')
    print("✅ Created table: maintenance_schedules")

    # 14. Maintenance records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER,
        item_id INTEGER,
        vehicle_id INTEGER,
        work_type TEXT NOT NULL,
        performed_by TEXT,
        firefighter_id INTEGER,
        performed_date TIMESTAMP NOT NULL,
        next_due_date TIMESTAMP,
        cost REAL,
        parts_used TEXT,
        notes TEXT,
        attachments TEXT,
        completed BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (schedule_id) REFERENCES maintenance_schedules(id),
        FOREIGN KEY (item_id) REFERENCES inventory_items(id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (firefighter_id) REFERENCES firefighters(id)
    )
    ''')
    print("✅ Created table: maintenance_records")

    # 15. Item certifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS item_certifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        vehicle_id INTEGER,
        station_id INTEGER,
        certification_type TEXT NOT NULL,
        certification_date DATE NOT NULL,
        expiration_date DATE NOT NULL,
        certifying_agency TEXT,
        certificate_number TEXT,
        passed BOOLEAN DEFAULT 1,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (station_id) REFERENCES stations(id)
    )
    ''')
    print("✅ Created table: item_certifications")

    print("\n📊 Creating indexes for performance...")

    # Create indexes
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_time_logs_firefighter ON time_logs(firefighter_id)',
        'CREATE INDEX IF NOT EXISTS idx_time_logs_time_in ON time_logs(time_in)',
        'CREATE INDEX IF NOT EXISTS idx_time_logs_time_out ON time_logs(time_out)',
        'CREATE INDEX IF NOT EXISTS idx_inspections_vehicle ON vehicle_inspections(vehicle_id)',
        'CREATE INDEX IF NOT EXISTS idx_inspections_date ON vehicle_inspections(inspection_date)',
        'CREATE INDEX IF NOT EXISTS idx_inspections_inspector ON vehicle_inspections(inspector_id)',
        'CREATE INDEX IF NOT EXISTS idx_inventory_category ON inventory_items(category)',
        'CREATE INDEX IF NOT EXISTS idx_inventory_serial ON inventory_items(serial_number)',
        'CREATE INDEX IF NOT EXISTS idx_transactions_item ON inventory_transactions(item_id)',
        'CREATE INDEX IF NOT EXISTS idx_transactions_date ON inventory_transactions(transaction_date)',
        'CREATE INDEX IF NOT EXISTS idx_vehicle_inventory_vehicle ON vehicle_inventory(vehicle_id)',
        'CREATE INDEX IF NOT EXISTS idx_vehicle_inventory_item ON vehicle_inventory(item_id)',
        'CREATE INDEX IF NOT EXISTS idx_station_inventory_station ON station_inventory(station_id)',
        'CREATE INDEX IF NOT EXISTS idx_station_inventory_item ON station_inventory(item_id)',
        'CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_item ON maintenance_schedules(item_id)',
        'CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_vehicle ON maintenance_schedules(vehicle_id)',
        'CREATE INDEX IF NOT EXISTS idx_maintenance_records_item ON maintenance_records(item_id)',
        'CREATE INDEX IF NOT EXISTS idx_maintenance_records_vehicle ON maintenance_records(vehicle_id)',
        'CREATE INDEX IF NOT EXISTS idx_maintenance_records_date ON maintenance_records(performed_date)',
        'CREATE INDEX IF NOT EXISTS idx_maintenance_records_next_due ON maintenance_records(next_due_date)',
        'CREATE INDEX IF NOT EXISTS idx_certifications_item ON item_certifications(item_id)',
        'CREATE INDEX IF NOT EXISTS idx_certifications_expiration ON item_certifications(expiration_date)',
        'CREATE INDEX IF NOT EXISTS idx_certifications_vehicle ON item_certifications(vehicle_id)',
        'CREATE INDEX IF NOT EXISTS idx_certifications_station ON item_certifications(station_id)'
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    print("✅ Created all indexes")

    conn.commit()
    conn.close()

    print("\n🎉 Database initialization complete!")
    print(f"📁 Database file: {DATABASE_NAME}")
    print(f"📊 Total tables: 15")
    print(f"📈 Total indexes: {len(indexes)}")

if __name__ == '__main__':
    init_database()
