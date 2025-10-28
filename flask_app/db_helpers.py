"""
Database helper functions for Fire Department Management System
Provides easy-to-use functions for common database operations
"""

import sqlite3
from datetime import datetime, timedelta
import pytz
from db_init import get_db_connection

# Timezone
CENTRAL = pytz.timezone('America/Chicago')

# ========== FIREFIGHTER FUNCTIONS ==========

def get_all_firefighters():
    """Get all firefighters"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, fireman_number, full_name, total_hours
        FROM firefighters
        ORDER BY full_name
    ''')

    firefighters = []
    for row in cursor.fetchall():
        firefighters.append({
            'id': row[0],
            'fireman_number': row[1],
            'full_name': row[2],
            'total_hours': row[3]
        })

    conn.close()
    return firefighters

def get_firefighter_by_number(fireman_number):
    """Get firefighter by their number"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, fireman_number, full_name, total_hours
        FROM firefighters
        WHERE fireman_number = ?
    ''', (fireman_number,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0],
            'fireman_number': row[1],
            'full_name': row[2],
            'total_hours': row[3]
        }
    return None

def create_firefighter(fireman_number, full_name):
    """Create a new firefighter"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO firefighters (fireman_number, full_name, total_hours)
            VALUES (?, ?, 0)
        ''', (fireman_number, full_name))

        conn.commit()
        firefighter_id = cursor.lastrowid
        conn.close()
        return firefighter_id
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Already exists

def update_firefighter(fireman_number, new_fireman_number, full_name):
    """Update firefighter information"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE firefighters
        SET fireman_number = ?, full_name = ?, updated_at = CURRENT_TIMESTAMP
        WHERE fireman_number = ?
    ''', (new_fireman_number, full_name, fireman_number))

    conn.commit()
    conn.close()

def delete_firefighter(fireman_number):
    """Delete a firefighter"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM firefighters WHERE fireman_number = ?', (fireman_number,))

    conn.commit()
    conn.close()

# ========== ACTIVITY CATEGORY FUNCTIONS ==========

def get_all_categories():
    """Get all activity categories"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, name, default_hours FROM activity_categories ORDER BY name')

    categories = []
    for row in cursor.fetchall():
        categories.append({
            'id': row[0],
            'name': row[1],
            'default_hours': row[2]
        })

    conn.close()
    return categories

def get_category_by_name(name):
    """Get category by name"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, name, default_hours FROM activity_categories WHERE name = ?', (name,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {'id': row[0], 'name': row[1], 'default_hours': row[2]}
    return None

def create_category(name, default_hours=None):
    """Create a new activity category"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO activity_categories (name, default_hours)
            VALUES (?, ?)
        ''', (name, default_hours))

        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        return category_id
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Already exists

def delete_category(name):
    """Delete a category"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM activity_categories WHERE name = ?', (name,))

    conn.commit()
    conn.close()

# ========== TIME LOG FUNCTIONS ==========

def clock_in(fireman_number, activity_name):
    """Clock in a firefighter"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get firefighter ID
    cursor.execute('SELECT id FROM firefighters WHERE fireman_number = ?', (fireman_number,))
    firefighter_row = cursor.fetchone()

    if not firefighter_row:
        conn.close()
        return False, "Firefighter not found"

    firefighter_id = firefighter_row[0]

    # Get or create category
    category = get_category_by_name(activity_name)
    if not category:
        category_id = create_category(activity_name)
    else:
        category_id = category['id']

    # Create time log
    time_in = datetime.now(CENTRAL).isoformat()

    cursor.execute('''
        INSERT INTO time_logs (firefighter_id, category_id, time_in)
        VALUES (?, ?, ?)
    ''', (firefighter_id, category_id, time_in))

    conn.commit()
    conn.close()

    return True, "Clocked in successfully"

def clock_out(fireman_number):
    """Clock out a firefighter"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get firefighter ID
    cursor.execute('SELECT id FROM firefighters WHERE fireman_number = ?', (fireman_number,))
    firefighter_row = cursor.fetchone()

    if not firefighter_row:
        conn.close()
        return False, "Firefighter not found"

    firefighter_id = firefighter_row[0]

    # Find most recent unclosed log
    cursor.execute('''
        SELECT id, time_in, category_id
        FROM time_logs
        WHERE firefighter_id = ? AND time_out IS NULL
        ORDER BY time_in DESC
        LIMIT 1
    ''', (firefighter_id,))

    log_row = cursor.fetchone()

    if not log_row:
        conn.close()
        return False, "No active clock-in found"

    log_id = log_row[0]
    time_in = datetime.fromisoformat(log_row[1])
    time_out = datetime.now(CENTRAL)

    # Ensure timezone aware
    if time_in.tzinfo is None:
        time_in = pytz.utc.localize(time_in).astimezone(CENTRAL)

    # Calculate hours
    hours_worked = (time_out - time_in).total_seconds() / 3600

    # Update time log
    cursor.execute('''
        UPDATE time_logs
        SET time_out = ?, hours_worked = ?
        WHERE id = ?
    ''', (time_out.isoformat(), hours_worked, log_id))

    # Update firefighter total hours
    cursor.execute('''
        UPDATE firefighters
        SET total_hours = total_hours + ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (hours_worked, firefighter_id))

    conn.commit()
    conn.close()

    return True, f"Clocked out after {hours_worked:.2f} hours"

def get_firefighter_logs(fireman_number):
    """Get all logs for a firefighter"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT tl.id, ac.name, tl.time_in, tl.time_out, tl.hours_worked,
               tl.auto_checkout, tl.manual_added_hours
        FROM time_logs tl
        JOIN firefighters f ON tl.firefighter_id = f.id
        JOIN activity_categories ac ON tl.category_id = ac.id
        WHERE f.fireman_number = ?
        ORDER BY tl.time_in DESC
    ''', (fireman_number,))

    logs = []
    for row in cursor.fetchall():
        logs.append({
            'id': row[0],
            'type': row[1],
            'time_in': row[2],
            'time_out': row[3],
            'hours_worked': row[4],
            'auto_checkout': row[5],
            'manual_added_hours': row[6]
        })

    conn.close()
    return logs

def get_active_firefighters():
    """Get all currently clocked-in firefighters"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT f.fireman_number, f.full_name, ac.name, tl.time_in
        FROM time_logs tl
        JOIN firefighters f ON tl.firefighter_id = f.id
        JOIN activity_categories ac ON tl.category_id = ac.id
        WHERE tl.time_out IS NULL
        ORDER BY tl.time_in ASC
    ''')

    active = []
    for row in cursor.fetchall():
        active.append({
            'number': row[0],
            'name': row[1],
            'activity': row[2],
            'time_in': row[3]
        })

    conn.close()
    return active

def add_manual_hours(fireman_number, activity_name, log_date, time_in, time_out):
    """Manually add hours for a firefighter"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get firefighter ID
    cursor.execute('SELECT id FROM firefighters WHERE fireman_number = ?', (fireman_number,))
    firefighter_row = cursor.fetchone()

    if not firefighter_row:
        conn.close()
        return False, "Firefighter not found"

    firefighter_id = firefighter_row[0]

    # Get or create category
    category = get_category_by_name(activity_name)
    if not category:
        category_id = create_category(activity_name)
    else:
        category_id = category['id']

    # Parse times
    try:
        datetime_in = CENTRAL.localize(datetime.strptime(f"{log_date} {time_in}", "%Y-%m-%d %H:%M"))
        datetime_out = CENTRAL.localize(datetime.strptime(f"{log_date} {time_out}", "%Y-%m-%d %H:%M"))

        hours_worked = (datetime_out - datetime_in).total_seconds() / 3600

        # Insert log
        cursor.execute('''
            INSERT INTO time_logs
            (firefighter_id, category_id, time_in, time_out, hours_worked, manual_added_hours)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (firefighter_id, category_id, datetime_in.isoformat(), datetime_out.isoformat(),
              hours_worked, hours_worked))

        # Update firefighter total hours
        cursor.execute('''
            UPDATE firefighters
            SET total_hours = total_hours + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (hours_worked, firefighter_id))

        conn.commit()
        conn.close()

        return True, f"Added {hours_worked:.2f} hours"

    except Exception as e:
        conn.close()
        return False, f"Error: {str(e)}"

def delete_log(fireman_number, log_index):
    """Delete a specific log entry"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all logs for this firefighter
    logs = get_firefighter_logs(fireman_number)

    if log_index < 0 or log_index >= len(logs):
        conn.close()
        return False, "Invalid log index"

    log = logs[log_index]
    log_id = log['id']

    # Get hours to subtract
    hours_to_subtract = log.get('hours_worked', 0) or log.get('manual_added_hours', 0) or 0

    # Delete the log
    cursor.execute('DELETE FROM time_logs WHERE id = ?', (log_id,))

    # Update firefighter total hours
    cursor.execute('''
        UPDATE firefighters
        SET total_hours = total_hours - ?, updated_at = CURRENT_TIMESTAMP
        WHERE fireman_number = ?
    ''', (hours_to_subtract, fireman_number))

    conn.commit()
    conn.close()

    return True, "Log deleted successfully"

def clear_all_logs():
    """Clear all logs and reset hours"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM time_logs')
    cursor.execute('UPDATE firefighters SET total_hours = 0, updated_at = CURRENT_TIMESTAMP')

    conn.commit()
    conn.close()

# ========== LEADERBOARD ==========

def get_leaderboard():
    """Get firefighter leaderboard sorted by hours"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT fireman_number, full_name, total_hours
        FROM firefighters
        ORDER BY total_hours DESC
    ''')

    leaderboard = []
    for row in cursor.fetchall():
        leaderboard.append({
            'number': row[0],
            'name': row[1],
            'hours': row[2]
        })

    conn.close()
    return leaderboard

# ========== VEHICLE FUNCTIONS ==========

def get_all_vehicles():
    """Get all vehicles"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, vehicle_code, name, vehicle_type, status
        FROM vehicles
        WHERE status = 'active'
        ORDER BY vehicle_code
    ''')

    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'type': row[3],
            'status': row[4]
        })

    conn.close()
    return vehicles

def get_vehicles_needing_inspection():
    """Get vehicles that need inspection (not inspected in last 6 days)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current time minus 6 days
    six_days_ago = datetime.now(CENTRAL) - timedelta(days=6)

    cursor.execute('''
        SELECT v.id, v.vehicle_code, v.name, v.vehicle_type, v.status,
               MAX(vi.inspection_date) as last_inspection
        FROM vehicles v
        LEFT JOIN vehicle_inspections vi ON v.id = vi.vehicle_id
        WHERE v.status = 'active'
        GROUP BY v.id
        HAVING last_inspection IS NULL OR last_inspection < ?
        ORDER BY v.vehicle_code
    ''', (six_days_ago.isoformat(),))

    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'type': row[3],
            'status': row[4],
            'last_inspection': row[5]
        })

    conn.close()
    return vehicles

def get_vehicle_by_id(vehicle_id):
    """Get vehicle by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, vehicle_code, name, vehicle_type, status
        FROM vehicles
        WHERE id = ?
    ''', (vehicle_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'type': row[3],
            'status': row[4]
        }
    return None

# ========== INSPECTION FUNCTIONS ==========

def get_inspection_checklist():
    """Get all active inspection checklist items"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, description, category
        FROM inspection_checklist_items
        WHERE is_active = 1
        ORDER BY display_order
    ''')

    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'description': row[1],
            'category': row[2]
        })

    conn.close()
    return items

def create_vehicle_inspection(vehicle_id, inspector_id, inspection_results, additional_notes=''):
    """Create a new vehicle inspection with results"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Determine if inspection passed (all items passed)
        passed = all(result['status'] == 'pass' for result in inspection_results)

        # Create inspection record
        cursor.execute('''
            INSERT INTO vehicle_inspections
            (vehicle_id, inspector_id, inspection_date, passed, additional_notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (vehicle_id, inspector_id, datetime.now(CENTRAL).isoformat(), passed, additional_notes))

        inspection_id = cursor.lastrowid

        # Add inspection results
        for result in inspection_results:
            cursor.execute('''
                INSERT INTO inspection_results
                (inspection_id, checklist_item_id, status, notes)
                VALUES (?, ?, ?, ?)
            ''', (inspection_id, result['item_id'], result['status'], result.get('notes', '')))

        conn.commit()
        conn.close()

        return True, inspection_id

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def get_vehicle_inspection_history(vehicle_id, limit=10):
    """Get inspection history for a vehicle"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT vi.id, vi.inspection_date, vi.passed, f.full_name, vi.additional_notes
        FROM vehicle_inspections vi
        LEFT JOIN firefighters f ON vi.inspector_id = f.id
        WHERE vi.vehicle_id = ?
        ORDER BY vi.inspection_date DESC
        LIMIT ?
    ''', (vehicle_id, limit))

    history = []
    for row in cursor.fetchall():
        history.append({
            'id': row[0],
            'date': row[1],
            'passed': row[2],
            'inspector': row[3] or 'Unknown',
            'notes': row[4]
        })

    conn.close()
    return history

# ========== MAINTENANCE FUNCTIONS ==========

def create_maintenance_record(vehicle_id, work_type, performed_by, performed_date, cost=None, parts_used='', notes='', firefighter_id=None):
    """Create a new maintenance record"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO maintenance_records
            (vehicle_id, work_type, performed_by, performed_date, cost, parts_used, notes, firefighter_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vehicle_id, work_type, performed_by, performed_date, cost, parts_used, notes, firefighter_id))

        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        return True, record_id

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def get_maintenance_records_for_vehicle(vehicle_id, limit=50):
    """Get all maintenance records for a specific vehicle"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT mr.id, mr.work_type, mr.performed_by, mr.performed_date, mr.cost, mr.parts_used, mr.notes,
               f.full_name as firefighter_name
        FROM maintenance_records mr
        LEFT JOIN firefighters f ON mr.firefighter_id = f.id
        WHERE mr.vehicle_id = ?
        ORDER BY mr.performed_date DESC
        LIMIT ?
    ''', (vehicle_id, limit))

    records = []
    for row in cursor.fetchall():
        records.append({
            'id': row[0],
            'work_type': row[1],
            'performed_by': row[2],
            'performed_date': row[3],
            'cost': row[4],
            'parts_used': row[5],
            'notes': row[6],
            'firefighter_name': row[7]
        })

    conn.close()
    return records

def get_all_maintenance_records(limit=100):
    """Get all maintenance records across all vehicles"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT mr.id, v.name as vehicle_name, v.vehicle_code, mr.work_type, mr.performed_by,
               mr.performed_date, mr.cost, mr.parts_used, mr.notes,
               f.full_name as firefighter_name
        FROM maintenance_records mr
        LEFT JOIN vehicles v ON mr.vehicle_id = v.id
        LEFT JOIN firefighters f ON mr.firefighter_id = f.id
        ORDER BY mr.performed_date DESC
        LIMIT ?
    ''', (limit,))

    records = []
    for row in cursor.fetchall():
        records.append({
            'id': row[0],
            'vehicle_name': row[1],
            'vehicle_code': row[2],
            'work_type': row[3],
            'performed_by': row[4],
            'performed_date': row[5],
            'cost': row[6],
            'parts_used': row[7],
            'notes': row[8],
            'firefighter_name': row[9]
        })

    conn.close()
    return records

def get_recent_maintenance(days=30):
    """Get maintenance records from the last N days"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cutoff_date = datetime.now(CENTRAL) - timedelta(days=days)

    cursor.execute('''
        SELECT mr.id, v.name as vehicle_name, v.vehicle_code, mr.work_type, mr.performed_by,
               mr.performed_date, mr.cost
        FROM maintenance_records mr
        LEFT JOIN vehicles v ON mr.vehicle_id = v.id
        WHERE mr.performed_date >= ?
        ORDER BY mr.performed_date DESC
    ''', (cutoff_date.isoformat(),))

    records = []
    for row in cursor.fetchall():
        records.append({
            'id': row[0],
            'vehicle_name': row[1],
            'vehicle_code': row[2],
            'work_type': row[3],
            'performed_by': row[4],
            'performed_date': row[5],
            'cost': row[6]
        })

    conn.close()
    return records

# ========== INVENTORY MANAGEMENT FUNCTIONS ==========

# Station Functions
def get_all_stations():
    """Get all fire stations"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, address, is_primary, notes
        FROM stations
        ORDER BY is_primary DESC, name ASC
    ''')

    stations = []
    for row in cursor.fetchall():
        stations.append({
            'id': row[0],
            'name': row[1],
            'address': row[2],
            'is_primary': row[3],
            'notes': row[4]
        })

    conn.close()
    return stations

def create_station(name, address='', is_primary=False, notes=''):
    """Create a new fire station"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO stations (name, address, is_primary, notes)
            VALUES (?, ?, ?, ?)
        ''', (name, address, is_primary, notes))

        conn.commit()
        station_id = cursor.lastrowid
        conn.close()
        return True, station_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Inventory Item Functions
def get_all_inventory_items():
    """Get all inventory items from master catalog"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, item_code, category, subcategory, description,
               manufacturer, model_number, unit_of_measure, cost_per_unit,
               current_value, min_quantity, is_consumable
        FROM inventory_items
        ORDER BY category, name
    ''')

    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'name': row[1],
            'item_code': row[2],
            'category': row[3],
            'subcategory': row[4],
            'description': row[5],
            'manufacturer': row[6],
            'model_number': row[7],
            'unit_of_measure': row[8],
            'cost_per_unit': row[9],
            'current_value': row[10],
            'min_quantity': row[11],
            'is_consumable': row[12]
        })

    conn.close()
    return items

def create_inventory_item(name, category, item_code='', subcategory='', description='',
                         manufacturer='', model_number='', unit_of_measure='each',
                         cost_per_unit=None, current_value=None, min_quantity=0,
                         is_consumable=False, serial_number='', notes=''):
    """Create a new inventory item in master catalog"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO inventory_items
            (name, item_code, serial_number, category, subcategory, description,
             manufacturer, model_number, unit_of_measure, cost_per_unit, current_value,
             min_quantity, is_consumable, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, item_code, serial_number, category, subcategory, description,
              manufacturer, model_number, unit_of_measure, cost_per_unit, current_value,
              min_quantity, is_consumable, notes))

        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return True, item_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def search_inventory_items(search_term):
    """Search inventory items by name, code, or category"""
    conn = get_db_connection()
    cursor = conn.cursor()

    search_pattern = f'%{search_term}%'
    cursor.execute('''
        SELECT id, name, item_code, category, unit_of_measure, cost_per_unit
        FROM inventory_items
        WHERE name LIKE ? OR item_code LIKE ? OR category LIKE ?
        ORDER BY name
        LIMIT 50
    ''', (search_pattern, search_pattern, search_pattern))

    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'name': row[1],
            'item_code': row[2],
            'category': row[3],
            'unit_of_measure': row[4],
            'cost_per_unit': row[5]
        })

    conn.close()
    return items

# Station Inventory Functions
def get_station_inventory(station_id):
    """Get all inventory items assigned to a specific station"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT si.id, si.item_id, ii.name, ii.item_code, ii.category, ii.unit_of_measure,
               si.quantity, ii.cost_per_unit, ii.min_quantity, si.last_checked, si.notes
        FROM station_inventory si
        JOIN inventory_items ii ON si.item_id = ii.id
        WHERE si.station_id = ?
        ORDER BY ii.category, ii.name
    ''', (station_id,))

    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'item_id': row[1],
            'name': row[2],
            'item_code': row[3],
            'category': row[4],
            'unit_of_measure': row[5],
            'quantity': row[6],
            'cost_per_unit': row[7],
            'min_quantity': row[8],
            'last_checked': row[9],
            'notes': row[10]
        })

    conn.close()
    return items

def add_item_to_station(station_id, item_id, quantity, notes=''):
    """Add or update an item in station inventory"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if item already exists at this station
        cursor.execute('''
            SELECT id, quantity FROM station_inventory
            WHERE station_id = ? AND item_id = ?
        ''', (station_id, item_id))

        existing = cursor.fetchone()

        if existing:
            # Update existing quantity
            new_quantity = existing[1] + quantity
            cursor.execute('''
                UPDATE station_inventory
                SET quantity = ?, last_checked = CURRENT_TIMESTAMP, notes = ?
                WHERE id = ?
            ''', (new_quantity, notes, existing[0]))
        else:
            # Add new item
            cursor.execute('''
                INSERT INTO station_inventory (station_id, item_id, quantity, notes)
                VALUES (?, ?, ?, ?)
            ''', (station_id, item_id, quantity, notes))

        conn.commit()
        conn.close()
        return True, "Item updated successfully"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def update_station_inventory_quantity(station_inventory_id, new_quantity):
    """Update the quantity of an item in station inventory"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE station_inventory
            SET quantity = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_quantity, station_inventory_id))

        conn.commit()
        conn.close()
        return True, "Quantity updated"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def remove_item_from_station(station_inventory_id):
    """Remove an item from station inventory"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM station_inventory WHERE id = ?', (station_inventory_id,))
        conn.commit()
        conn.close()
        return True, "Item removed"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Vehicle Inventory Functions
def get_vehicle_inventory(vehicle_id):
    """Get all inventory items assigned to a specific vehicle"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT vi.id, vi.item_id, ii.name, ii.item_code, ii.category, ii.unit_of_measure,
               vi.quantity, ii.cost_per_unit, vi.last_checked, vi.notes
        FROM vehicle_inventory vi
        JOIN inventory_items ii ON vi.item_id = ii.id
        WHERE vi.vehicle_id = ?
        ORDER BY ii.category, ii.name
    ''', (vehicle_id,))

    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'item_id': row[1],
            'name': row[2],
            'item_code': row[3],
            'category': row[4],
            'unit_of_measure': row[5],
            'quantity': row[6],
            'cost_per_unit': row[7],
            'last_checked': row[8],
            'notes': row[9]
        })

    conn.close()
    return items

def add_item_to_vehicle(vehicle_id, item_id, quantity, notes=''):
    """Add or update an item in vehicle inventory"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if item already exists on this vehicle
        cursor.execute('''
            SELECT id, quantity FROM vehicle_inventory
            WHERE vehicle_id = ? AND item_id = ?
        ''', (vehicle_id, item_id))

        existing = cursor.fetchone()

        if existing:
            # Update existing quantity
            new_quantity = existing[1] + quantity
            cursor.execute('''
                UPDATE vehicle_inventory
                SET quantity = ?, last_checked = CURRENT_TIMESTAMP, notes = ?
                WHERE id = ?
            ''', (new_quantity, notes, existing[0]))
        else:
            # Add new item
            cursor.execute('''
                INSERT INTO vehicle_inventory (vehicle_id, item_id, quantity, notes)
                VALUES (?, ?, ?, ?)
            ''', (vehicle_id, item_id, quantity, notes))

        conn.commit()
        conn.close()
        return True, "Item updated successfully"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def update_vehicle_inventory_quantity(vehicle_inventory_id, new_quantity):
    """Update the quantity of an item in vehicle inventory"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE vehicle_inventory
            SET quantity = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_quantity, vehicle_inventory_id))

        conn.commit()
        conn.close()
        return True, "Quantity updated"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def remove_item_from_vehicle(vehicle_inventory_id):
    """Remove an item from vehicle inventory"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM vehicle_inventory WHERE id = ?', (vehicle_inventory_id,))
        conn.commit()
        conn.close()
        return True, "Item removed"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Helper function to get vehicles by station
def get_vehicles_by_station(station_id):
    """Get all vehicles assigned to a specific station"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, vehicle_code, name, vehicle_type, vin, license_plate
        FROM vehicles
        WHERE station_id = ?
        ORDER BY vehicle_code
    ''', (station_id,))

    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            'id': row[0],
            'vehicle_code': row[1],
            'name': row[2],
            'vehicle_type': row[3],
            'vin': row[4],
            'license_plate': row[5]
        })

    conn.close()
    return vehicles
