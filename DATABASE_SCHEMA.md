# Fire Department Management System - SQLite Database Schema

## Overview
This document outlines the database schema for migrating from JSON to SQLite.

## Enhanced Features
- ✅ Multi-location inventory (Stations + Vehicles)
- ✅ Periodic maintenance scheduling (every X months)
- ✅ Replacement schedules (after X years)
- ✅ Cost/value tracking for insurance purposes
- ✅ Maintenance work orders with mechanic notes
- ✅ Expiration/certification tracking
- ✅ Alerts dashboard for items needing attention

## Tables

### 1. **firefighters**
Stores firefighter personnel information.

```sql
CREATE TABLE firefighters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fireman_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    total_hours REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. **activity_categories**
Stores activity types (Training, Firefighting, etc.).

```sql
CREATE TABLE activity_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    default_hours REAL DEFAULT NULL,  -- Default hours for auto-checkout
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. **time_logs**
Stores clock in/out records.

```sql
CREATE TABLE time_logs (
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
);
```

### 4. **stations**
Stores fire station locations.

```sql
CREATE TABLE stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                 -- Station 1, Headquarters, etc.
    address TEXT,
    is_primary BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. **vehicles**
Stores fire department vehicles/apparatus.

```sql
CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_code TEXT UNIQUE NOT NULL,  -- E1, E2, L1, T2, etc.
    name TEXT NOT NULL,                 -- Engine 1, Ladder 1, etc.
    vehicle_type TEXT,                  -- Engine, Ladder, Tanker, Ambulance, etc.
    station_id INTEGER,                 -- Home station
    year INTEGER,
    make TEXT,
    model TEXT,
    vin TEXT,
    license_plate TEXT,
    purchase_date DATE,
    purchase_cost REAL,
    current_value REAL,                 -- For insurance purposes
    status TEXT DEFAULT 'active',       -- active, maintenance, out_of_service
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES stations(id)
);
```

### 5. **inspection_checklist_items**
Stores reusable checklist items for inspections.

```sql
CREATE TABLE inspection_checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    category TEXT,                      -- mechanical, safety, equipment, etc.
    is_active BOOLEAN DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. **vehicle_inspections**
Stores vehicle inspection records.

```sql
CREATE TABLE vehicle_inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    inspector_id INTEGER,               -- firefighter who did the inspection
    inspection_date TIMESTAMP NOT NULL,
    passed BOOLEAN DEFAULT 1,           -- Overall pass/fail
    additional_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (inspector_id) REFERENCES firefighters(id)
);
```

### 7. **inspection_results**
Stores individual checklist item results for each inspection.

```sql
CREATE TABLE inspection_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id INTEGER NOT NULL,
    checklist_item_id INTEGER NOT NULL,
    status TEXT NOT NULL,               -- pass, fail, n/a
    notes TEXT,
    FOREIGN KEY (inspection_id) REFERENCES vehicle_inspections(id) ON DELETE CASCADE,
    FOREIGN KEY (checklist_item_id) REFERENCES inspection_checklist_items(id)
);
```

### 8. **inventory_items**
Stores inventory items (equipment, supplies, PPE, etc.).

```sql
CREATE TABLE inventory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    item_code TEXT UNIQUE,              -- SKU or internal code
    serial_number TEXT,                 -- For tracked items
    category TEXT,                      -- PPE, Tools, Medical, Hoses, SCBA, etc.
    subcategory TEXT,                   -- More specific categorization
    description TEXT,
    manufacturer TEXT,
    model_number TEXT,
    unit_of_measure TEXT,               -- each, box, gallon, etc.
    cost_per_unit REAL,                 -- Purchase cost
    current_value REAL,                 -- Current value for insurance
    min_quantity INTEGER DEFAULT 0,     -- Minimum stock level (alerts)
    location_type TEXT,                 -- station, vehicle, or both
    is_consumable BOOLEAN DEFAULT 0,    -- Consumable vs durable
    requires_certification BOOLEAN DEFAULT 0,
    requires_maintenance BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 9. **inventory_transactions**
Tracks all inventory movements (additions, usage, adjustments).

```sql
CREATE TABLE inventory_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,     -- restock, usage, adjustment, inspection, transfer
    quantity_change INTEGER NOT NULL,   -- Positive for additions, negative for usage
    quantity_after INTEGER NOT NULL,    -- Running balance
    firefighter_id INTEGER,             -- Who performed the transaction
    vehicle_id INTEGER,                 -- If item assigned to/from vehicle
    notes TEXT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
    FOREIGN KEY (firefighter_id) REFERENCES firefighters(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);
```

### 10. **station_inventory**
Links inventory items to specific stations.

```sql
CREATE TABLE station_inventory (
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
);
```

### 11. **vehicle_inventory**
Links inventory items to specific vehicles.

```sql
CREATE TABLE vehicle_inventory (
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
);
```

### 12. **maintenance_schedules**
Defines maintenance and replacement schedules for items and vehicles.

```sql
CREATE TABLE maintenance_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_type TEXT NOT NULL,        -- periodic_maintenance, replacement, certification, inspection
    item_id INTEGER,                    -- If schedule is for an item (e.g., SCBA bottle)
    vehicle_id INTEGER,                 -- If schedule is for a vehicle
    title TEXT NOT NULL,                -- "SCBA Air Fill", "Oil Change", "Replace After 5 Years"
    description TEXT,
    interval_type TEXT NOT NULL,        -- months, years, hours, miles
    interval_value INTEGER NOT NULL,    -- e.g., 6 for "every 6 months"
    cost_estimate REAL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);
```

### 13. **maintenance_records**
Tracks actual maintenance/service work performed (work orders).

```sql
CREATE TABLE maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER,                -- Link to schedule if this was scheduled
    item_id INTEGER,                    -- Item serviced
    vehicle_id INTEGER,                 -- Vehicle serviced
    work_type TEXT NOT NULL,            -- maintenance, repair, inspection, refill, replacement
    performed_by TEXT,                  -- Mechanic/technician name or firefighter
    firefighter_id INTEGER,             -- If performed by a firefighter
    performed_date TIMESTAMP NOT NULL,
    next_due_date TIMESTAMP,            -- When next service is due
    cost REAL,
    parts_used TEXT,                    -- List of parts
    notes TEXT,                         -- Mechanic notes on what was done
    attachments TEXT,                   -- File paths to receipts, photos, etc.
    completed BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES maintenance_schedules(id),
    FOREIGN KEY (item_id) REFERENCES inventory_items(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (firefighter_id) REFERENCES firefighters(id)
);
```

### 14. **item_certifications**
Tracks certifications, expirations, and compliance dates for items.

```sql
CREATE TABLE item_certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,           -- The item being tracked
    vehicle_id INTEGER,                 -- If this specific item is on a vehicle
    station_id INTEGER,                 -- If this specific item is at a station
    certification_type TEXT NOT NULL,   -- hydrostatic_test, visual_inspection, certification, expiration
    certification_date DATE NOT NULL,   -- When it was certified/filled/inspected
    expiration_date DATE NOT NULL,      -- When it expires or needs attention
    certifying_agency TEXT,             -- Who certified/inspected it
    certificate_number TEXT,
    passed BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (station_id) REFERENCES stations(id)
);
```

## Indexes for Performance

```sql
-- Time logs indexes
CREATE INDEX idx_time_logs_firefighter ON time_logs(firefighter_id);
CREATE INDEX idx_time_logs_time_in ON time_logs(time_in);
CREATE INDEX idx_time_logs_time_out ON time_logs(time_out);

-- Inspection indexes
CREATE INDEX idx_inspections_vehicle ON vehicle_inspections(vehicle_id);
CREATE INDEX idx_inspections_date ON vehicle_inspections(inspection_date);
CREATE INDEX idx_inspections_inspector ON vehicle_inspections(inspector_id);

-- Inventory indexes
CREATE INDEX idx_inventory_category ON inventory_items(category);
CREATE INDEX idx_inventory_serial ON inventory_items(serial_number);
CREATE INDEX idx_transactions_item ON inventory_transactions(item_id);
CREATE INDEX idx_transactions_date ON inventory_transactions(transaction_date);
CREATE INDEX idx_vehicle_inventory_vehicle ON vehicle_inventory(vehicle_id);
CREATE INDEX idx_vehicle_inventory_item ON vehicle_inventory(item_id);
CREATE INDEX idx_station_inventory_station ON station_inventory(station_id);
CREATE INDEX idx_station_inventory_item ON station_inventory(item_id);

-- Maintenance indexes
CREATE INDEX idx_maintenance_schedules_item ON maintenance_schedules(item_id);
CREATE INDEX idx_maintenance_schedules_vehicle ON maintenance_schedules(vehicle_id);
CREATE INDEX idx_maintenance_records_item ON maintenance_records(item_id);
CREATE INDEX idx_maintenance_records_vehicle ON maintenance_records(vehicle_id);
CREATE INDEX idx_maintenance_records_date ON maintenance_records(performed_date);
CREATE INDEX idx_maintenance_records_next_due ON maintenance_records(next_due_date);

-- Certification indexes
CREATE INDEX idx_certifications_item ON item_certifications(item_id);
CREATE INDEX idx_certifications_expiration ON item_certifications(expiration_date);
CREATE INDEX idx_certifications_vehicle ON item_certifications(vehicle_id);
CREATE INDEX idx_certifications_station ON item_certifications(station_id);
```

## Views for Common Queries

```sql
-- Active firefighters (currently clocked in)
CREATE VIEW active_firefighters AS
SELECT
    f.id,
    f.fireman_number,
    f.full_name,
    ac.name as activity,
    tl.time_in
FROM time_logs tl
JOIN firefighters f ON tl.firefighter_id = f.id
JOIN activity_categories ac ON tl.category_id = ac.id
WHERE tl.time_out IS NULL;

-- Leaderboard
CREATE VIEW firefighter_leaderboard AS
SELECT
    fireman_number,
    full_name,
    total_hours
FROM firefighters
ORDER BY total_hours DESC;

-- Low stock inventory alerts
CREATE VIEW low_stock_items AS
SELECT
    id,
    name,
    item_code,
    category,
    current_quantity,
    min_quantity,
    (min_quantity - current_quantity) as shortage
FROM inventory_items
WHERE current_quantity <= min_quantity
ORDER BY shortage DESC;

-- Vehicle inspection history
CREATE VIEW vehicle_inspection_summary AS
SELECT
    v.vehicle_code,
    v.name as vehicle_name,
    COUNT(vi.id) as total_inspections,
    SUM(CASE WHEN vi.passed = 1 THEN 1 ELSE 0 END) as passed_count,
    SUM(CASE WHEN vi.passed = 0 THEN 1 ELSE 0 END) as failed_count,
    MAX(vi.inspection_date) as last_inspection
FROM vehicles v
LEFT JOIN vehicle_inspections vi ON v.id = vi.id
GROUP BY v.id;

-- Items with expiring certifications (next 30 days)
CREATE VIEW expiring_certifications AS
SELECT
    ii.name as item_name,
    ii.item_code,
    ii.serial_number,
    ic.certification_type,
    ic.expiration_date,
    CAST((julianday(ic.expiration_date) - julianday('now')) AS INTEGER) as days_until_expiration,
    CASE
        WHEN ic.vehicle_id IS NOT NULL THEN v.name
        WHEN ic.station_id IS NOT NULL THEN s.name
        ELSE 'Unassigned'
    END as location,
    ic.notes
FROM item_certifications ic
JOIN inventory_items ii ON ic.item_id = ii.id
LEFT JOIN vehicles v ON ic.vehicle_id = v.id
LEFT JOIN stations s ON ic.station_id = s.id
WHERE ic.expiration_date <= date('now', '+30 days')
ORDER BY ic.expiration_date ASC;

-- Maintenance due soon (next 30 days)
CREATE VIEW maintenance_due_soon AS
SELECT
    mr.id as record_id,
    CASE
        WHEN mr.vehicle_id IS NOT NULL THEN v.name
        WHEN mr.item_id IS NOT NULL THEN ii.name
        ELSE 'Unknown'
    END as item_name,
    ms.title as schedule_title,
    mr.next_due_date,
    CAST((julianday(mr.next_due_date) - julianday('now')) AS INTEGER) as days_until_due,
    ms.cost_estimate,
    mr.notes as last_service_notes
FROM maintenance_records mr
LEFT JOIN maintenance_schedules ms ON mr.schedule_id = ms.id
LEFT JOIN vehicles v ON mr.vehicle_id = v.id
LEFT JOIN inventory_items ii ON mr.item_id = ii.id
WHERE mr.next_due_date IS NOT NULL
  AND mr.next_due_date <= date('now', '+30 days')
  AND mr.completed = 1
ORDER BY mr.next_due_date ASC;

-- Overdue maintenance
CREATE VIEW overdue_maintenance AS
SELECT
    mr.id as record_id,
    CASE
        WHEN mr.vehicle_id IS NOT NULL THEN v.name
        WHEN mr.item_id IS NOT NULL THEN ii.name
        ELSE 'Unknown'
    END as item_name,
    ms.title as schedule_title,
    mr.next_due_date,
    CAST((julianday('now') - julianday(mr.next_due_date)) AS INTEGER) as days_overdue,
    ms.cost_estimate
FROM maintenance_records mr
LEFT JOIN maintenance_schedules ms ON mr.schedule_id = ms.id
LEFT JOIN vehicles v ON mr.vehicle_id = v.id
LEFT JOIN inventory_items ii ON mr.item_id = ii.id
WHERE mr.next_due_date IS NOT NULL
  AND mr.next_due_date < date('now')
  AND mr.completed = 1
ORDER BY mr.next_due_date ASC;

-- Total vehicle value (vehicle + inventory)
CREATE VIEW vehicle_total_value AS
SELECT
    v.id,
    v.vehicle_code,
    v.name,
    v.current_value as vehicle_value,
    COALESCE(SUM(ii.current_value * vi.quantity), 0) as inventory_value,
    (v.current_value + COALESCE(SUM(ii.current_value * vi.quantity), 0)) as total_value
FROM vehicles v
LEFT JOIN vehicle_inventory vi ON v.id = vi.vehicle_id
LEFT JOIN inventory_items ii ON vi.item_id = ii.id
GROUP BY v.id;

-- Total station inventory value
CREATE VIEW station_inventory_value AS
SELECT
    s.id,
    s.name as station_name,
    COALESCE(SUM(ii.current_value * si.quantity), 0) as total_inventory_value,
    COUNT(DISTINCT si.item_id) as unique_items
FROM stations s
LEFT JOIN station_inventory si ON s.id = si.station_id
LEFT JOIN inventory_items ii ON si.item_id = ii.id
GROUP BY s.id;

-- Complete alerts dashboard
CREATE VIEW alerts_dashboard AS
SELECT
    'Expired Certification' as alert_type,
    'critical' as severity,
    item_name as description,
    days_until_expiration as days,
    location
FROM expiring_certifications
WHERE days_until_expiration < 0

UNION ALL

SELECT
    'Certification Expiring Soon' as alert_type,
    'warning' as severity,
    item_name as description,
    days_until_expiration as days,
    location
FROM expiring_certifications
WHERE days_until_expiration BETWEEN 0 AND 30

UNION ALL

SELECT
    'Maintenance Overdue' as alert_type,
    'critical' as severity,
    item_name as description,
    days_overdue * -1 as days,
    schedule_title as location
FROM overdue_maintenance

UNION ALL

SELECT
    'Maintenance Due Soon' as alert_type,
    'warning' as severity,
    item_name as description,
    days_until_due as days,
    schedule_title as location
FROM maintenance_due_soon

UNION ALL

SELECT
    'Low Stock' as alert_type,
    'info' as severity,
    name as description,
    (min_quantity - current_quantity) as days,
    location_type as location
FROM low_stock_items
ORDER BY severity DESC, days ASC;
```

## Migration Notes

1. **Preserve all existing data** from JSON files
2. **Maintain backward compatibility** during transition
3. **Add timestamps** for better auditing
4. **Add relationships** between tables for data integrity
5. **Keep JSON backup** files until migration verified

## Benefits of SQLite Migration

- ✅ **Relational data** - Proper relationships between entities
- ✅ **Data integrity** - Foreign keys and constraints
- ✅ **Better queries** - Complex joins and aggregations
- ✅ **Transactions** - Atomic operations for data safety
- ✅ **Scalability** - Better performance with more data
- ✅ **Concurrent access** - Multiple users/processes
- ✅ **Standard SQL** - Easier to understand and maintain
- ✅ **Built-in Python support** - No additional dependencies

## Key Features Summary

### ✅ Complete Inventory Management
- Track items at **stations** and on **vehicles**
- Serial number tracking for individual items
- Cost tracking for insurance valuations
- Category/subcategory organization
- Low stock alerts

### ✅ Maintenance Scheduling System
- Define maintenance schedules (every 6 months, every 5 years, etc.)
- Track periodic maintenance (oil changes, inspections, refills)
- Track replacement schedules (after X years/hours)
- Automatic calculation of next due dates
- Cost estimates for budgeting

### ✅ Maintenance Records with Mechanic Notes
- Full work order system
- Mechanic notes on what was done
- Parts used tracking
- Cost tracking
- Photo/receipt attachments
- Links to maintenance schedules

### ✅ Certification & Expiration Tracking
- Track SCBA bottle certifications
- Hydrostatic test dates
- Visual inspection dates
- Generic expiration dates
- Certification numbers and agencies

### ✅ Alerts Dashboard
Shows everything that needs attention:
- **Critical:** Expired certifications, overdue maintenance
- **Warning:** Expiring soon (30 days), maintenance due soon
- **Info:** Low stock items
- All in one easy-to-read view

### ✅ Total Value Calculations
- Calculate complete vehicle value (vehicle + inventory)
- Calculate station inventory value
- Insurance documentation support

### ✅ Vehicle Inspections
- Daily vehicle checklist inspections
- Track who inspected and when
- Pass/fail for each item
- Notes for failures
- Inspection history

## Example Use Cases

**Scenario 1: SCBA Bottle Maintenance**
1. Add SCBA bottle to `inventory_items`
2. Create certification record in `item_certifications` (air fill date + 6 months)
3. Create maintenance schedule: "Air Refill every 6 months"
4. Create maintenance schedule: "Replace after 15 years"
5. When serviced, add record to `maintenance_records` with mechanic notes
6. System automatically shows on alerts dashboard when due

**Scenario 2: Calculate Truck Value for Insurance**
1. Query `vehicle_total_value` view
2. Get vehicle value + all equipment value
3. Export for insurance documentation

**Scenario 3: Daily Vehicle Inspection**
1. Inspector logs in
2. Selects vehicle (Engine 1)
3. Goes through checklist items
4. Marks pass/fail with notes
5. Inspection saved with timestamp and inspector name

**Scenario 4: Track Tool Inventory**
1. Add tool to `inventory_items` with cost
2. Assign quantity to station via `station_inventory`
3. When assigned to vehicle, move via `inventory_transactions`
4. Update `vehicle_inventory`
5. Full audit trail of where tool has been
