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
