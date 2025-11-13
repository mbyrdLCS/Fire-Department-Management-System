"""
Database helper functions for Fire Department Management System
Provides easy-to-use functions for common database operations
"""

import sqlite3
from datetime import datetime, timedelta
import pytz
import os
import shutil
from db_init import get_db_connection, DATABASE_PATH

# Load environment variables
from dotenv import load_dotenv
# Try multiple paths for .env file (local dev vs PythonAnywhere)
env_paths = [
    os.path.join(os.path.dirname(__file__), '..', '.env'),  # Local development
    os.path.join(os.path.dirname(__file__), '.env'),        # Same directory
    '/home/michealhelps/Fire-Department-Management-System/.env',  # PythonAnywhere absolute path
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
        break

# Optional Dropbox import
try:
    import dropbox
    from dropbox.exceptions import ApiError, AuthError
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

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
            'total_hours': row[3] if row[3] is not None else 0.0
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

    # Check if already clocked in (prevent duplicate check-ins)
    cursor.execute('''
        SELECT id FROM time_logs
        WHERE firefighter_id = ? AND time_out IS NULL
    ''', (firefighter_id,))

    if cursor.fetchone():
        conn.close()
        return False, "Already clocked in. Please clock out first."

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

def auto_checkout_stale_logs():
    """
    Auto-checkout any logs that have been open for more than 12 hours.
    Records them as 1 hour instead of actual time.
    This prevents forgotten check-ins from inflating hours.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find logs that have been open for more than 12 hours
    cursor.execute('''
        SELECT id, firefighter_id, time_in
        FROM time_logs
        WHERE time_out IS NULL
        AND datetime(time_in) <= datetime('now', '-12 hours')
    ''')

    stale_logs = cursor.fetchall()
    count = 0

    for log in stale_logs:
        log_id = log[0]
        firefighter_id = log[1]
        time_in = datetime.fromisoformat(log[2])

        # Set checkout time to 1 hour after check-in
        if time_in.tzinfo is None:
            time_in = pytz.utc.localize(time_in).astimezone(CENTRAL)

        time_out = time_in + timedelta(hours=1)
        hours_worked = 1.0  # Record as 1 hour

        # Update time log with auto_checkout flag
        cursor.execute('''
            UPDATE time_logs
            SET time_out = ?, hours_worked = ?, auto_checkout = 1
            WHERE id = ?
        ''', (time_out.isoformat(), hours_worked, log_id))

        # Update firefighter total hours (add 1 hour)
        cursor.execute('''
            UPDATE firefighters
            SET total_hours = total_hours + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (firefighter_id,))

        count += 1

    conn.commit()
    conn.close()

    return count

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

def get_latest_time_log(firefighter_number):
    """Get the most recent time log entry for a firefighter"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT tl.id, tl.time_in, tl.time_out, ac.name as activity
        FROM time_logs tl
        JOIN firefighters f ON tl.firefighter_id = f.id
        JOIN activity_categories ac ON tl.category_id = ac.id
        WHERE f.fireman_number = ?
        ORDER BY tl.time_in DESC
        LIMIT 1
    ''', (firefighter_number,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0],
            'clock_in': row[1],
            'clock_out': row[2],
            'activity': row[3]
        }
    return None

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

    # Get hours to subtract (prefer manual_added_hours if exists, else hours_worked)
    hours_to_subtract = log.get('manual_added_hours', 0) or log.get('hours_worked', 0) or 0

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

def delete_log_by_id(log_id):
    """Delete a specific log entry by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the log details before deleting
    cursor.execute('''
        SELECT tl.hours_worked, tl.manual_added_hours, f.fireman_number
        FROM time_logs tl
        JOIN firefighters f ON tl.firefighter_id = f.id
        WHERE tl.id = ?
    ''', (log_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Log not found"

    # Prefer manual_added_hours (row[1]) if exists, else hours_worked (row[0])
    hours_to_subtract = row[1] or row[0] or 0
    fireman_number = row[2]

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
            'hours': row[2] if row[2] is not None else 0.0
        })

    conn.close()
    return leaderboard

def get_recent_activity(limit=10):
    """Get recent clock in/out activity for display board"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            f.fireman_number,
            f.full_name,
            ac.name as activity,
            tl.time_in,
            tl.time_out,
            CASE
                WHEN tl.time_out IS NULL THEN 'clocked_in'
                ELSE 'clocked_out'
            END as action_type
        FROM time_logs tl
        JOIN firefighters f ON tl.firefighter_id = f.id
        JOIN activity_categories ac ON tl.category_id = ac.id
        ORDER BY
            CASE
                WHEN tl.time_out IS NULL THEN tl.time_in
                ELSE tl.time_out
            END DESC
        LIMIT ?
    ''', (limit,))

    recent = []
    for row in cursor.fetchall():
        recent.append({
            'number': row[0],
            'name': row[1],
            'activity': row[2],
            'time_in': row[3],
            'time_out': row[4],
            'action_type': row[5]
        })

    conn.close()
    return recent

# ========== VEHICLE FUNCTIONS ==========

def get_all_vehicles():
    """Get all vehicles with all fields including fluid specifications"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, vehicle_code, name, vehicle_type, station_id, year, make, model,
               vin, license_plate, purchase_date, purchase_cost, current_value,
               status, notes,
               oil_type, antifreeze_type, brake_fluid_type,
               power_steering_fluid_type, transmission_fluid_type
        FROM vehicles
        WHERE status = 'active'
        ORDER BY vehicle_code
    ''')

    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            'id': row[0],
            'vehicle_code': row[1],
            'name': row[2],
            'vehicle_type': row[3],
            'station_id': row[4],
            'year': row[5],
            'make': row[6],
            'model': row[7],
            'vin': row[8],
            'license_plate': row[9],
            'purchase_date': row[10],
            'purchase_cost': row[11],
            'current_value': row[12],
            'status': row[13],
            'notes': row[14],
            'oil_type': row[15] if row[15] else '',
            'antifreeze_type': row[16] if row[16] else '',
            'brake_fluid_type': row[17] if row[17] else '',
            'power_steering_fluid_type': row[18] if row[18] else '',
            'transmission_fluid_type': row[19] if row[19] else ''
        })

    conn.close()
    return vehicles

def get_vehicles_needing_inspection(station_id=None):
    """Get vehicles that need inspection (not inspected in last 6 days)

    Args:
        station_id: Optional station ID to filter vehicles by station
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current time minus 6 days
    six_days_ago = datetime.now(CENTRAL) - timedelta(days=6)

    # Build query with optional station filter
    query = '''
        SELECT v.id, v.vehicle_code, v.name, v.vehicle_type, v.status,
               MAX(vi.inspection_date) as last_inspection, v.station_id
        FROM vehicles v
        LEFT JOIN vehicle_inspections vi ON v.id = vi.vehicle_id
        WHERE v.status = 'active'
    '''

    params = []
    if station_id is not None:
        query += ' AND v.station_id = ?'
        params.append(station_id)

    query += '''
        GROUP BY v.id
        HAVING last_inspection IS NULL OR last_inspection < ?
        ORDER BY v.vehicle_code
    '''

    params.append(six_days_ago.isoformat())
    cursor.execute(query, params)

    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'type': row[3],
            'status': row[4],
            'last_inspection': row[5],
            'station_id': row[6]
        })

    conn.close()
    return vehicles

def get_vehicle_by_id(vehicle_id):
    """Get vehicle by ID with all details including fluid specifications"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Try to get all columns including fluid specs
    try:
        cursor.execute('''
            SELECT id, vehicle_code, name, vehicle_type, status,
                   oil_type, antifreeze_type, brake_fluid_type,
                   power_steering_fluid_type, transmission_fluid_type
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
                'status': row[4],
                'oil_type': row[5] or '',
                'antifreeze_type': row[6] or '',
                'brake_fluid_type': row[7] or '',
                'power_steering_fluid_type': row[8] or '',
                'transmission_fluid_type': row[9] or ''
            }
    except Exception as e:
        # Fallback if fluid columns don't exist yet (for backwards compatibility)
        conn.close()
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
                'status': row[4],
                'oil_type': '',
                'antifreeze_type': '',
                'brake_fluid_type': '',
                'power_steering_fluid_type': '',
                'transmission_fluid_type': ''
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

def get_all_checklist_items():
    """Get all inspection checklist items (active and inactive)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, description, category, is_active, display_order
        FROM inspection_checklist_items
        ORDER BY display_order
    ''')

    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'description': row[1],
            'category': row[2],
            'is_active': row[3],
            'display_order': row[4]
        })

    conn.close()
    return items

def create_checklist_item(description, category='', display_order=0):
    """Create a new inspection checklist item"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO inspection_checklist_items
            (description, category, is_active, display_order)
            VALUES (?, ?, 1, ?)
        ''', (description, category, display_order))

        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return True, item_id

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def update_checklist_item(item_id, description, category='', display_order=0, is_active=True):
    """Update an existing checklist item"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE inspection_checklist_items
            SET description = ?, category = ?, display_order = ?, is_active = ?
            WHERE id = ?
        ''', (description, category, display_order, 1 if is_active else 0, item_id))

        conn.commit()
        conn.close()
        return True, item_id

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def toggle_checklist_item(item_id):
    """Toggle active status of a checklist item"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE inspection_checklist_items
            SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
            WHERE id = ?
        ''', (item_id,))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        return False

def delete_checklist_item(item_id):
    """Delete a checklist item"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM inspection_checklist_items WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        return True, "Item deleted successfully"

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def update_checklist_item_order(item_id, display_order):
    """Update the display order of a checklist item"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE inspection_checklist_items
            SET display_order = ?
            WHERE id = ?
        ''', (display_order, item_id))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        return False

def get_vehicle_checklist(vehicle_id):
    """Get checklist items assigned to a specific vehicle"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ci.id, ci.description, ci.category, ci.display_order
        FROM inspection_checklist_items ci
        INNER JOIN vehicle_checklist_assignments vca ON ci.id = vca.checklist_item_id
        WHERE vca.vehicle_id = ? AND ci.is_active = 1
        ORDER BY ci.display_order
    ''', (vehicle_id,))

    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'description': row[1],
            'category': row[2],
            'display_order': row[3]
        })

    conn.close()
    return items

def assign_checklist_to_vehicle(vehicle_id, checklist_item_ids):
    """Assign checklist items to a vehicle (replaces existing assignments)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Remove existing assignments
        cursor.execute('DELETE FROM vehicle_checklist_assignments WHERE vehicle_id = ?', (vehicle_id,))

        # Add new assignments
        for item_id in checklist_item_ids:
            cursor.execute('''
                INSERT INTO vehicle_checklist_assignments (vehicle_id, checklist_item_id)
                VALUES (?, ?)
            ''', (vehicle_id, item_id))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        return False

def add_checklist_item_to_vehicle(vehicle_id, checklist_item_id):
    """Add a single checklist item to a vehicle"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO vehicle_checklist_assignments (vehicle_id, checklist_item_id)
            VALUES (?, ?)
        ''', (vehicle_id, checklist_item_id))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        return False

def remove_checklist_item_from_vehicle(vehicle_id, checklist_item_id):
    """Remove a checklist item from a vehicle"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            DELETE FROM vehicle_checklist_assignments
            WHERE vehicle_id = ? AND checklist_item_id = ?
        ''', (vehicle_id, checklist_item_id))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        return False

def get_vehicles_for_checklist_item(checklist_item_id):
    """Get all vehicles that have this checklist item assigned"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT v.id, v.vehicle_code, v.name
        FROM vehicles v
        INNER JOIN vehicle_checklist_assignments vca ON v.id = vca.vehicle_id
        WHERE vca.checklist_item_id = ?
        ORDER BY v.vehicle_code
    ''', (checklist_item_id,))

    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            'id': row[0],
            'code': row[1],
            'name': row[2]
        })

    conn.close()
    return vehicles

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

def get_station_by_id(station_id):
    """Get a specific station by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, address, is_primary, notes
        FROM stations
        WHERE id = ?
    ''', (station_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0],
            'name': row[1],
            'address': row[2],
            'is_primary': row[3],
            'notes': row[4]
        }
    return None

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

def update_station(station_id, name, address='', is_primary=False, notes=''):
    """Update an existing fire station"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE stations
            SET name = ?, address = ?, is_primary = ?, notes = ?
            WHERE id = ?
        ''', (name, address, is_primary, notes, station_id))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error updating station: {e}")
        return False

def delete_station(station_id):
    """Delete a fire station"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM stations WHERE id = ?', (station_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error deleting station: {e}")
        return False

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
        # Convert empty strings to None for UNIQUE constraint fields
        item_code = item_code.strip() if item_code and item_code.strip() else None
        serial_number = serial_number.strip() if serial_number and serial_number.strip() else None

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

def generate_vehicle_code(name, vehicle_type=''):
    """Auto-generate a vehicle code from name and type

    Examples:
    - "Rescue 1" -> "R1"
    - "Pumper 2" -> "P2"
    - "Grass Truck 5" -> "G5"
    - "Tanker 3" -> "T3"
    - "Engine 4" -> "E4"
    - "Ladder 1" -> "L1"
    - "Custom Fire Truck" -> "CFT1" (uses initials + next number)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Common fire vehicle type abbreviations
    type_map = {
        'rescue': 'R',
        'pumper': 'P',
        'grass': 'G',
        'tanker': 'T',
        'engine': 'E',
        'ladder': 'L',
        'truck': 'T',
        'ambulance': 'A',
        'squad': 'S'
    }

    # Try to extract vehicle type and number from name
    name_lower = name.lower()
    words = name_lower.split()

    # Look for a number in the name
    number = None
    for word in words:
        if word.isdigit():
            number = word
            break

    # Try to find vehicle type from name or vehicle_type field
    prefix = None
    for type_name, abbrev in type_map.items():
        if type_name in name_lower or type_name in vehicle_type.lower():
            prefix = abbrev
            break

    # If no match found, use first letters of each word
    if not prefix:
        # Take first letter of each word (up to 3 letters)
        prefix = ''.join([word[0].upper() for word in words if word[0].isalpha()])[:3]

    # If no number found, get next available number for this prefix
    if not number:
        cursor.execute('''
            SELECT vehicle_code FROM vehicles
            WHERE vehicle_code LIKE ?
            ORDER BY vehicle_code DESC
            LIMIT 1
        ''', (f'{prefix}%',))

        result = cursor.fetchone()
        if result:
            # Extract number from existing code
            existing_code = result[0]
            existing_num = ''.join(filter(str.isdigit, existing_code))
            number = str(int(existing_num) + 1) if existing_num else '1'
        else:
            number = '1'

    vehicle_code = f'{prefix}{number}'

    # Check if code already exists
    cursor.execute('SELECT id FROM vehicles WHERE vehicle_code = ?', (vehicle_code,))
    if cursor.fetchone():
        # If exists, add next number
        cursor.execute('''
            SELECT vehicle_code FROM vehicles
            WHERE vehicle_code LIKE ?
            ORDER BY vehicle_code DESC
            LIMIT 1
        ''', (f'{prefix}%',))

        result = cursor.fetchone()
        if result:
            existing_code = result[0]
            existing_num = ''.join(filter(str.isdigit, existing_code))
            next_num = int(existing_num) + 1 if existing_num else 1
            vehicle_code = f'{prefix}{next_num}'

    conn.close()
    return vehicle_code

def create_vehicle(vehicle_code, name, vehicle_type='', station_id=None, year=None, make='', model='', vin='', license_plate='', purchase_date=None, purchase_cost=None, current_value=None, notes='', oil_type='', antifreeze_type='', brake_fluid_type='', power_steering_fluid_type='', transmission_fluid_type=''):
    """Create a new vehicle and automatically assign all active checklist items

    If vehicle_code is empty, it will be auto-generated from the name and type
    """
    # Auto-generate vehicle code if not provided
    if not vehicle_code or vehicle_code.strip() == '':
        vehicle_code = generate_vehicle_code(name, vehicle_type)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Create the vehicle
        cursor.execute('''
            INSERT INTO vehicles
            (vehicle_code, name, vehicle_type, station_id, year, make, model, vin, license_plate,
             purchase_date, purchase_cost, current_value, notes, status,
             oil_type, antifreeze_type, brake_fluid_type, power_steering_fluid_type, transmission_fluid_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
        ''', (vehicle_code, name, vehicle_type, station_id, year, make, model, vin, license_plate,
              purchase_date, purchase_cost, current_value, notes,
              oil_type, antifreeze_type, brake_fluid_type, power_steering_fluid_type, transmission_fluid_type))

        vehicle_id = cursor.lastrowid

        # Automatically assign all active checklist items to this vehicle
        cursor.execute('''
            INSERT INTO vehicle_checklist_assignments (vehicle_id, checklist_item_id)
            SELECT ?, id FROM inspection_checklist_items WHERE is_active = 1
        ''', (vehicle_id,))

        conn.commit()
        conn.close()
        return True, vehicle_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def update_vehicle(vehicle_id, vehicle_code, name, vehicle_type='', station_id=None, year=None, make='', model='', vin='', license_plate='', purchase_date=None, purchase_cost=None, current_value=None, notes='', status='active', oil_type='', antifreeze_type='', brake_fluid_type='', power_steering_fluid_type='', transmission_fluid_type=''):
    """Update an existing vehicle"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE vehicles
            SET vehicle_code = ?, name = ?, vehicle_type = ?, station_id = ?, year = ?,
                make = ?, model = ?, vin = ?, license_plate = ?, purchase_date = ?,
                purchase_cost = ?, current_value = ?, notes = ?, status = ?,
                oil_type = ?, antifreeze_type = ?, brake_fluid_type = ?,
                power_steering_fluid_type = ?, transmission_fluid_type = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (vehicle_code, name, vehicle_type, station_id, year, make, model, vin, license_plate,
              purchase_date, purchase_cost, current_value, notes, status,
              oil_type, antifreeze_type, brake_fluid_type, power_steering_fluid_type, transmission_fluid_type,
              vehicle_id))

        conn.commit()
        conn.close()
        return True, "Vehicle updated successfully"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def delete_vehicle(vehicle_id):
    """Delete a vehicle (CASCADE will handle related records)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get vehicle name for confirmation message
        cursor.execute('SELECT name FROM vehicles WHERE id = ?', (vehicle_id,))
        result = cursor.fetchone()
        vehicle_name = result[0] if result else "Unknown"

        # Delete the vehicle (CASCADE will delete related records)
        cursor.execute('DELETE FROM vehicles WHERE id = ?', (vehicle_id,))

        conn.commit()
        conn.close()
        return True, f"Vehicle '{vehicle_name}' deleted successfully"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# ========== ALERTS AND NOTIFICATIONS FUNCTIONS ==========

def get_all_alerts(station_id=None):
    """Get all active alerts for the dashboard, optionally filtered by station"""
    alerts = {
        'inspections_overdue': [],
        'inspections_failed': [],
        'low_inventory_station': [],
        'low_inventory_vehicle': [],
        'total_count': 0
    }

    # Get overdue inspections (filtered by station if specified)
    alerts['inspections_overdue'] = get_vehicles_needing_inspection(station_id=station_id)

    # Get failed inspections (vehicles needing maintenance)
    conn = get_db_connection()
    cursor = conn.cursor()

    if station_id:
        cursor.execute('''
            SELECT v.id, v.name, v.vehicle_code, vi.inspection_date, vi.additional_notes
            FROM vehicle_inspections vi
            JOIN vehicles v ON vi.vehicle_id = v.id
            WHERE vi.passed = 0
            AND v.station_id = ?
            AND vi.id = (
                SELECT MAX(id) FROM vehicle_inspections
                WHERE vehicle_id = v.id
            )
            ORDER BY vi.inspection_date DESC
        ''', (station_id,))
    else:
        cursor.execute('''
            SELECT v.id, v.name, v.vehicle_code, vi.inspection_date, vi.additional_notes
            FROM vehicle_inspections vi
            JOIN vehicles v ON vi.vehicle_id = v.id
            WHERE vi.passed = 0
            AND vi.id = (
                SELECT MAX(id) FROM vehicle_inspections
                WHERE vehicle_id = v.id
            )
            ORDER BY vi.inspection_date DESC
        ''')

    for row in cursor.fetchall():
        alerts['inspections_failed'].append({
            'id': row[0],
            'name': row[1],
            'code': row[2],
            'failed_date': row[3],
            'notes': row[4] or 'Maintenance required'
        })

    # Get low inventory at stations (filtered by station if specified)
    if station_id:
        cursor.execute('''
            SELECT s.name as station_name, ii.name as item_name, si.quantity, ii.min_quantity, ii.category
            FROM station_inventory si
            JOIN inventory_items ii ON si.item_id = ii.id
            JOIN stations s ON si.station_id = s.id
            WHERE ii.min_quantity > 0 AND si.quantity < ii.min_quantity
            AND si.station_id = ?
            ORDER BY s.name, ii.name
        ''', (station_id,))
    else:
        cursor.execute('''
            SELECT s.name as station_name, ii.name as item_name, si.quantity, ii.min_quantity, ii.category
            FROM station_inventory si
            JOIN inventory_items ii ON si.item_id = ii.id
            JOIN stations s ON si.station_id = s.id
            WHERE ii.min_quantity > 0 AND si.quantity < ii.min_quantity
            ORDER BY s.name, ii.name
        ''')

    for row in cursor.fetchall():
        alerts['low_inventory_station'].append({
            'station_name': row[0],
            'item_name': row[1],
            'quantity': row[2],
            'min_quantity': row[3],
            'category': row[4]
        })

    # Get low inventory on vehicles (filtered by station if specified)
    if station_id:
        cursor.execute('''
            SELECT v.name as vehicle_name, v.vehicle_code, ii.name as item_name, vi.quantity, ii.min_quantity, ii.category
            FROM vehicle_inventory vi
            JOIN inventory_items ii ON vi.item_id = ii.id
            JOIN vehicles v ON vi.vehicle_id = v.id
            WHERE ii.min_quantity > 0 AND vi.quantity < ii.min_quantity
            AND v.station_id = ?
            ORDER BY v.name, ii.name
        ''', (station_id,))
    else:
        cursor.execute('''
            SELECT v.name as vehicle_name, v.vehicle_code, ii.name as item_name, vi.quantity, ii.min_quantity, ii.category
            FROM vehicle_inventory vi
            JOIN inventory_items ii ON vi.item_id = ii.id
            JOIN vehicles v ON vi.vehicle_id = v.id
            WHERE ii.min_quantity > 0 AND vi.quantity < ii.min_quantity
            ORDER BY v.name, ii.name
        ''')

    for row in cursor.fetchall():
        alerts['low_inventory_vehicle'].append({
            'vehicle_name': row[0],
            'vehicle_code': row[1],
            'item_name': row[2],
            'quantity': row[3],
            'min_quantity': row[4],
            'category': row[5]
        })

    conn.close()

    # Calculate total alerts
    alerts['total_count'] = (
        len(alerts['inspections_overdue']) +
        len(alerts['inspections_failed']) +
        len(alerts['low_inventory_station']) +
        len(alerts['low_inventory_vehicle'])
    )

    return alerts

# ========== DASHBOARD STATISTICS ==========

def get_dashboard_stats():
    """Get overall dashboard statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    # Total firefighters
    cursor.execute('SELECT COUNT(*) FROM firefighters')
    stats['total_firefighters'] = cursor.fetchone()[0]

    # Currently active
    cursor.execute('SELECT COUNT(*) FROM time_logs WHERE time_out IS NULL')
    stats['active_now'] = cursor.fetchone()[0]

    # Total hours this month
    cursor.execute('''
        SELECT COALESCE(SUM(
            CASE
                WHEN time_out IS NULL THEN
                    (julianday('now') - julianday(time_in)) * 24
                ELSE
                    (julianday(time_out) - julianday(time_in)) * 24
            END
        ), 0)
        FROM time_logs
        WHERE strftime('%Y-%m', time_in) = strftime('%Y-%m', 'now')
    ''')
    stats['hours_this_month'] = round(cursor.fetchone()[0], 1)

    # Total hours all time
    cursor.execute('SELECT COALESCE(SUM(total_hours), 0) FROM firefighters')
    stats['total_hours_all_time'] = round(cursor.fetchone()[0], 1)

    # Total vehicles
    cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'active'")
    stats['total_vehicles'] = cursor.fetchone()[0]

    # Vehicles needing inspection
    cursor.execute('''
        SELECT COUNT(*)
        FROM (
            SELECT v.id
            FROM vehicles v
            LEFT JOIN vehicle_inspections vi ON v.id = vi.vehicle_id
            WHERE v.status = 'active'
            GROUP BY v.id
            HAVING MAX(vi.inspection_date) IS NULL OR
                   julianday('now') - julianday(MAX(vi.inspection_date)) > 6
        )
    ''')
    stats['vehicles_needing_inspection'] = cursor.fetchone()[0] or 0

    # Total inventory items
    cursor.execute('SELECT COUNT(*) FROM inventory_items')
    stats['total_inventory_items'] = cursor.fetchone()[0]

    # Low inventory count
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT 1 FROM station_inventory si
            JOIN inventory_items ii ON si.item_id = ii.id
            WHERE ii.min_quantity > 0 AND si.quantity < ii.min_quantity
            UNION ALL
            SELECT 1 FROM vehicle_inventory vi
            JOIN inventory_items ii ON vi.item_id = ii.id
            WHERE ii.min_quantity > 0 AND vi.quantity < ii.min_quantity
        )
    ''')
    stats['low_inventory_count'] = cursor.fetchone()[0]

    # Total alerts
    stats['total_alerts'] = stats['vehicles_needing_inspection'] + stats['low_inventory_count']

    conn.close()
    return stats

def get_hours_by_day(days=30):
    """Get hours worked per day for the last N days"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            DATE(time_in) as day,
            SUM(
                CASE
                    WHEN time_out IS NULL THEN
                        (julianday('now') - julianday(time_in)) * 24
                    ELSE
                        (julianday(time_out) - julianday(time_in)) * 24
                END
            ) as total_hours
        FROM time_logs
        WHERE julianday('now') - julianday(time_in) <= ?
        GROUP BY DATE(time_in)
        ORDER BY day DESC
    ''', (days,))

    data = []
    for row in cursor.fetchall():
        data.append({
            'date': row[0],
            'hours': round(row[1], 1)
        })

    conn.close()
    return list(reversed(data))  # Oldest to newest for chart display

def get_activity_breakdown():
    """Get breakdown of hours by activity type"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            ac.name,
            COUNT(*) as session_count,
            SUM(
                CASE
                    WHEN tl.time_out IS NULL THEN
                        (julianday('now') - julianday(tl.time_in)) * 24
                    ELSE
                        (julianday(tl.time_out) - julianday(tl.time_in)) * 24
                END
            ) as total_hours
        FROM time_logs tl
        JOIN activity_categories ac ON tl.category_id = ac.id
        GROUP BY ac.name
        ORDER BY total_hours DESC
    ''')

    data = []
    for row in cursor.fetchall():
        data.append({
            'activity': row[0],
            'sessions': row[1],
            'hours': round(row[2], 1)
        })

    conn.close()
    return data

def get_vehicle_status_summary():
    """Get summary of vehicle inspection status"""
    conn = get_db_connection()
    cursor = conn.cursor()

    summary = {
        'up_to_date': 0,
        'due_soon': 0,
        'overdue': 0
    }

    cursor.execute('''
        SELECT
            CASE
                WHEN MAX(vi.inspection_date) IS NULL THEN 'overdue'
                WHEN julianday('now') - julianday(MAX(vi.inspection_date)) > 6 THEN 'overdue'
                WHEN julianday('now') - julianday(MAX(vi.inspection_date)) > 5 THEN 'due_soon'
                ELSE 'up_to_date'
            END as inspection_status
        FROM vehicles v
        LEFT JOIN vehicle_inspections vi ON v.id = vi.vehicle_id
        WHERE v.status = 'active'
        GROUP BY v.id
    ''')

    for row in cursor.fetchall():
        status = row[0]
        if status in summary:
            summary[status] += 1

    conn.close()
    return summary

def get_top_performers(limit=10):
    """Get top firefighters by hours this month"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            f.fireman_number,
            f.full_name,
            COALESCE(SUM(
                CASE
                    WHEN tl.time_out IS NULL THEN
                        (julianday('now') - julianday(tl.time_in)) * 24
                    ELSE
                        (julianday(tl.time_out) - julianday(tl.time_in)) * 24
                END
            ), 0) as monthly_hours,
            f.total_hours
        FROM firefighters f
        LEFT JOIN time_logs tl ON f.id = tl.firefighter_id
            AND strftime('%Y-%m', tl.time_in) = strftime('%Y-%m', 'now')
        GROUP BY f.id, f.fireman_number, f.full_name, f.total_hours
        ORDER BY monthly_hours DESC
        LIMIT ?
    ''', (limit,))

    performers = []
    for row in cursor.fetchall():
        performers.append({
            'number': row[0],
            'name': row[1],
            'monthly_hours': round(row[2], 1),
            'total_hours': round(row[3], 1)
        })

    conn.close()
    return performers

# ========== REPORTING FUNCTIONS ==========

def get_hours_report(start_date=None, end_date=None, firefighter_id=None):
    """Get detailed hours report with optional filters"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT
            f.fireman_number,
            f.full_name,
            ac.name as activity,
            DATE(tl.time_in) as date,
            tl.time_in,
            tl.time_out,
            CASE
                WHEN tl.time_out IS NULL THEN
                    (julianday('now') - julianday(tl.time_in)) * 24
                ELSE
                    (julianday(tl.time_out) - julianday(tl.time_in)) * 24
            END as hours
        FROM time_logs tl
        JOIN firefighters f ON tl.firefighter_id = f.id
        JOIN activity_categories ac ON tl.category_id = ac.id
        WHERE 1=1
    '''

    params = []

    if start_date:
        query += ' AND DATE(tl.time_in) >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND DATE(tl.time_in) <= ?'
        params.append(end_date)

    if firefighter_id:
        query += ' AND f.id = ?'
        params.append(firefighter_id)

    query += ' ORDER BY tl.time_in DESC'

    cursor.execute(query, params)

    report_data = []
    total_hours = 0

    for row in cursor.fetchall():
        hours = round(row[6], 2)
        total_hours += hours
        report_data.append({
            'firefighter_number': row[0],
            'firefighter_name': row[1],
            'activity': row[2],
            'date': row[3],
            'time_in': row[4],
            'time_out': row[5],
            'hours': hours
        })

    conn.close()

    return {
        'data': report_data,
        'total_hours': round(total_hours, 2),
        'start_date': start_date,
        'end_date': end_date
    }

def get_firefighter_summary_report(start_date=None, end_date=None):
    """Get hours summary grouped by firefighter"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT
            f.fireman_number,
            f.full_name,
            COUNT(DISTINCT DATE(tl.time_in)) as days_worked,
            COUNT(*) as sessions,
            SUM(
                CASE
                    WHEN tl.time_out IS NULL THEN
                        (julianday('now') - julianday(tl.time_in)) * 24
                    ELSE
                        (julianday(tl.time_out) - julianday(tl.time_in)) * 24
                END
            ) as total_hours
        FROM firefighters f
        LEFT JOIN time_logs tl ON f.id = tl.firefighter_id
    '''

    params = []

    if start_date or end_date:
        query += ' WHERE 1=1'
        if start_date:
            query += ' AND DATE(tl.time_in) >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND DATE(tl.time_in) <= ?'
            params.append(end_date)

    query += ' GROUP BY f.id, f.fireman_number, f.full_name ORDER BY total_hours DESC'

    cursor.execute(query, params)

    report_data = []
    total_hours_all = 0

    for row in cursor.fetchall():
        hours = round(row[4] or 0, 2)
        total_hours_all += hours
        report_data.append({
            'firefighter_number': row[0],
            'firefighter_name': row[1],
            'days_worked': row[2] or 0,
            'sessions': row[3] or 0,
            'total_hours': hours
        })

    conn.close()

    return {
        'data': report_data,
        'total_hours': round(total_hours_all, 2),
        'start_date': start_date,
        'end_date': end_date
    }

def get_activity_report(start_date=None, end_date=None):
    """Get hours breakdown by activity type"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT
            ac.name as activity,
            COUNT(*) as sessions,
            COUNT(DISTINCT tl.firefighter_id) as unique_firefighters,
            SUM(
                CASE
                    WHEN tl.time_out IS NULL THEN
                        (julianday('now') - julianday(tl.time_in)) * 24
                    ELSE
                        (julianday(tl.time_out) - julianday(tl.time_in)) * 24
                END
            ) as total_hours
        FROM time_logs tl
        JOIN activity_categories ac ON tl.category_id = ac.id
        WHERE 1=1
    '''

    params = []

    if start_date:
        query += ' AND DATE(tl.time_in) >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND DATE(tl.time_in) <= ?'
        params.append(end_date)

    query += ' GROUP BY ac.name ORDER BY total_hours DESC'

    cursor.execute(query, params)

    report_data = []
    total_hours_all = 0

    for row in cursor.fetchall():
        hours = round(row[3], 2)
        total_hours_all += hours
        report_data.append({
            'activity': row[0],
            'sessions': row[1],
            'unique_firefighters': row[2],
            'total_hours': hours
        })

    conn.close()

    return {
        'data': report_data,
        'total_hours': round(total_hours_all, 2),
        'start_date': start_date,
        'end_date': end_date
    }

def get_maintenance_cost_report(start_date=None, end_date=None, vehicle_id=None):
    """Get maintenance costs report - Returns empty data until work orders system is implemented"""
    # TODO: Implement maintenance_work_orders table and tracking system
    # For now, return empty report structure with $0 totals

    return {
        'data': [],
        'total_labor_cost': 0.00,
        'total_parts_cost': 0.00,
        'total_cost': 0.00,
        'start_date': start_date,
        'end_date': end_date
    }

def get_inventory_value_report():
    """Get inventory value report by location"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Station inventory
    cursor.execute('''
        SELECT
            s.name as location,
            'Station' as location_type,
            ii.name as item_name,
            ii.category,
            si.quantity,
            ii.cost_per_unit,
            (si.quantity * COALESCE(ii.cost_per_unit, 0)) as total_value
        FROM station_inventory si
        JOIN stations s ON si.station_id = s.id
        JOIN inventory_items ii ON si.item_id = ii.id
        WHERE si.quantity > 0
        ORDER BY s.name, ii.category, ii.name
    ''')

    station_data = []
    station_total = 0

    for row in cursor.fetchall():
        value = round(row[6], 2)
        station_total += value
        station_data.append({
            'location': row[0],
            'location_type': row[1],
            'item_name': row[2],
            'category': row[3],
            'quantity': row[4],
            'cost_per_unit': round(row[5] or 0, 2),
            'total_value': value
        })

    # Vehicle inventory
    cursor.execute('''
        SELECT
            v.name as location,
            'Vehicle' as location_type,
            ii.name as item_name,
            ii.category,
            vi.quantity,
            ii.cost_per_unit,
            (vi.quantity * COALESCE(ii.cost_per_unit, 0)) as total_value
        FROM vehicle_inventory vi
        JOIN vehicles v ON vi.vehicle_id = v.id
        JOIN inventory_items ii ON vi.item_id = ii.id
        WHERE vi.quantity > 0
        ORDER BY v.name, ii.category, ii.name
    ''')

    vehicle_data = []
    vehicle_total = 0

    for row in cursor.fetchall():
        value = round(row[6], 2)
        vehicle_total += value
        vehicle_data.append({
            'location': row[0],
            'location_type': row[1],
            'item_name': row[2],
            'category': row[3],
            'quantity': row[4],
            'cost_per_unit': round(row[5] or 0, 2),
            'total_value': value
        })

    conn.close()

    return {
        'station_inventory': station_data,
        'vehicle_inventory': vehicle_data,
        'station_total': round(station_total, 2),
        'vehicle_total': round(vehicle_total, 2),
        'grand_total': round(station_total + vehicle_total, 2)
    }

# ========== DISPLAY SETTINGS FUNCTIONS ==========

def get_display_setting(setting_key, default_value='true'):
    """Get a display setting value from database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT setting_value
            FROM display_settings
            WHERE setting_key = ?
        ''', (setting_key,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return row[0]
        return default_value
    except:
        # Table might not exist yet
        conn.close()
        return default_value

def update_display_setting(setting_key, setting_value):
    """Update a display setting value in database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # First ensure the table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS display_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Then insert or update the setting
        cursor.execute('''
            INSERT INTO display_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(setting_key)
            DO UPDATE SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
        ''', (setting_key, setting_value, setting_value))

        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error updating display setting: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_all_display_settings():
    """Get all display settings"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # First ensure the table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS display_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert default values if they don't exist
        cursor.execute('''
            INSERT OR IGNORE INTO display_settings (setting_key, setting_value)
            VALUES ('show_inventory_qr', 'true')
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO display_settings (setting_key, setting_value)
            VALUES ('show_maintenance_qr', 'true')
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO display_settings (setting_key, setting_value)
            VALUES ('show_inspections_qr', 'true')
        ''')

        cursor.execute('''
            SELECT setting_key, setting_value
            FROM display_settings
        ''')

        settings = {}
        for row in cursor.fetchall():
            settings[row[0]] = row[1]

        conn.close()
        return settings
    except Exception as e:
        # Table might not exist yet
        print(f"Error getting display settings: {e}")
        conn.close()
        return {
            'show_inventory_qr': 'true',
            'show_maintenance_qr': 'true',
            'show_inspections_qr': 'true'
        }

# ========== KIOSK SETTINGS FUNCTIONS ==========

def get_kiosk_settings():
    """Get all kiosk settings with defaults"""
    conn = get_db_connection()
    cursor = conn.cursor()

    defaults = {
        'kiosk_timeout_seconds': '20',
        'kiosk_orientation': 'horizontal',
        'kiosk_qr_code': 'inventory',
        'kiosk_message': 'Use your phone to scan the QR code below and start inspecting trucks.'
    }

    try:
        # Ensure default values exist
        for key, value in defaults.items():
            cursor.execute('''
                INSERT OR IGNORE INTO display_settings (setting_key, setting_value)
                VALUES (?, ?)
            ''', (key, value))

        # Get all kiosk settings
        cursor.execute('''
            SELECT setting_key, setting_value
            FROM display_settings
            WHERE setting_key LIKE 'kiosk_%'
        ''')

        settings = {}
        for row in cursor.fetchall():
            settings[row[0]] = row[1]

        conn.close()

        # Fill in any missing defaults
        for key, value in defaults.items():
            if key not in settings:
                settings[key] = value

        return settings
    except Exception as e:
        print(f"Error getting kiosk settings: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return defaults

def update_kiosk_setting(setting_key, setting_value):
    """Update a specific kiosk setting"""
    return update_display_setting(setting_key, setting_value)

def update_all_kiosk_settings(timeout_seconds, orientation, qr_code, message):
    """Update all kiosk settings at once"""
    try:
        update_display_setting('kiosk_timeout_seconds', str(timeout_seconds))
        update_display_setting('kiosk_orientation', orientation)
        update_display_setting('kiosk_qr_code', qr_code)
        update_display_setting('kiosk_message', message)
        return True
    except Exception as e:
        print(f"Error updating kiosk settings: {e}")
        import traceback
        traceback.print_exc()
        return False

# ========== BACKUP FUNCTIONS ==========

def create_database_backup():
    """
    Create a timestamped backup of the database
    Returns: dict with success status, backup path, and statistics
    """
    try:
        # Check if database exists
        if not os.path.exists(DATABASE_PATH):
            return {
                'success': False,
                'error': f'Database not found at {DATABASE_PATH}'
            }

        # Create backups directory
        backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'fire_dept_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)

        # Get database stats before backup
        db_size = os.path.getsize(DATABASE_PATH)
        db_size_kb = db_size / 1024

        # Get record counts
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM firefighters')
        firefighter_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM time_logs')
        log_count = cursor.fetchone()[0]

        cursor.execute('SELECT COALESCE(SUM(total_hours), 0) FROM firefighters')
        total_hours = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM vehicles')
        vehicle_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM inventory_items')
        inventory_count = cursor.fetchone()[0]

        conn.close()

        # Copy the database file
        shutil.copy2(DATABASE_PATH, backup_path)

        # Verify the backup
        if os.path.exists(backup_path):
            backup_size = os.path.getsize(backup_path)
            if backup_size == db_size:
                return {
                    'success': True,
                    'backup_path': backup_path,
                    'backup_filename': backup_filename,
                    'size_kb': db_size_kb,
                    'stats': {
                        'firefighters': firefighter_count,
                        'time_logs': log_count,
                        'total_hours': total_hours,
                        'vehicles': vehicle_count,
                        'inventory_items': inventory_count
                    },
                    'timestamp': timestamp
                }
            else:
                # Size mismatch - delete bad backup
                os.remove(backup_path)
                return {
                    'success': False,
                    'error': 'Backup file size mismatch - backup may be corrupt'
                }
        else:
            return {
                'success': False,
                'error': 'Backup file not created'
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def list_database_backups():
    """
    List all existing database backups
    Returns: list of backup info dictionaries
    """
    try:
        backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')

        if not os.path.exists(backup_dir):
            return []

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                backup_path = os.path.join(backup_dir, filename)
                size = os.path.getsize(backup_path) / 1024  # KB
                mtime = os.path.getmtime(backup_path)
                date = datetime.fromtimestamp(mtime)

                backups.append({
                    'filename': filename,
                    'path': backup_path,
                    'size_kb': size,
                    'date': date,
                    'date_formatted': date.strftime('%Y-%m-%d %H:%M:%S')
                })

        # Sort by date, newest first
        backups.sort(key=lambda x: x['date'], reverse=True)
        return backups

    except Exception as e:
        print(f"Error listing backups: {e}")
        return []

def cleanup_old_backups(keep_count=10):
    """
    Remove old backups, keeping only the N most recent
    Returns: dict with success status and number deleted
    """
    try:
        backups = list_database_backups()

        if len(backups) <= keep_count:
            return {
                'success': True,
                'deleted_count': 0,
                'message': f'Only {len(backups)} backup(s) exist. No cleanup needed.'
            }

        backups_to_delete = backups[keep_count:]
        deleted_count = 0
        errors = []

        for backup in backups_to_delete:
            try:
                os.remove(backup['path'])
                deleted_count += 1
            except Exception as e:
                errors.append(f"Failed to delete {backup['filename']}: {str(e)}")

        return {
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors,
            'message': f'Cleanup complete. {keep_count} backup(s) retained, {deleted_count} deleted.'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_backup_status():
    """
    Get the current backup system status
    Returns: dict with backup health information
    """
    try:
        backups = list_database_backups()

        if not backups:
            return {
                'healthy': False,
                'total_backups': 0,
                'last_backup': None,
                'warning': 'No backups found! Please create a backup immediately.'
            }

        last_backup = backups[0]
        hours_since_last = (datetime.now() - last_backup['date']).total_seconds() / 3600

        # Check if backup is recent (within 7 days)
        healthy = hours_since_last < (7 * 24)

        total_size_mb = sum(b['size_kb'] for b in backups) / 1024

        return {
            'healthy': healthy,
            'total_backups': len(backups),
            'last_backup': last_backup,
            'hours_since_last': hours_since_last,
            'total_size_mb': total_size_mb,
            'warning': None if healthy else f'Last backup was {hours_since_last/24:.1f} days ago. Consider creating a new backup.'
        }

    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }

def get_dropbox_client():
    """
    Get authenticated Dropbox client using credentials from environment
    Returns: Dropbox client or None if unavailable/failed
    """
    if not DROPBOX_AVAILABLE:
        print("Dropbox SDK not available - dropbox module not installed")
        return None

    try:
        # Get credentials from environment
        app_key = os.getenv('DROPBOX_APP_KEY')
        app_secret = os.getenv('DROPBOX_APP_SECRET')
        refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')

        # Debug: Check if credentials are present
        has_key = bool(app_key)
        has_secret = bool(app_secret)
        has_token = bool(refresh_token)

        print(f"Dropbox credentials check - Key: {has_key}, Secret: {has_secret}, Token: {has_token}")

        if not all([app_key, app_secret, refresh_token]):
            print(f"Missing Dropbox credentials - app_key: {has_key}, app_secret: {has_secret}, refresh_token: {has_token}")
            return None

        dbx = dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
            timeout=30
        )

        # Verify it works
        account = dbx.users_get_current_account()
        print(f"Successfully connected to Dropbox account: {account.email}")
        return dbx

    except Exception as e:
        print(f"Error connecting to Dropbox: {e}")
        import traceback
        traceback.print_exc()
        return None

def list_dropbox_backups():
    """
    List all backups stored in Dropbox
    Returns: list of Dropbox backup info dictionaries
    """
    try:
        dbx = get_dropbox_client()
        if not dbx:
            return {
                'success': False,
                'error': 'Dropbox not configured or unavailable',
                'backups': []
            }

        # List files in Dropbox root (where backups are stored)
        result = dbx.files_list_folder('')

        backups = []
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                # Only include database backup files
                if entry.name.endswith('.db') or 'backup' in entry.name.lower():
                    # Ensure date is timezone-aware
                    date = entry.client_modified
                    if date.tzinfo is None:
                        date = pytz.UTC.localize(date)

                    backups.append({
                        'filename': entry.name,
                        'size_kb': entry.size / 1024,
                        'date': date,
                        'date_formatted': date.strftime('%Y-%m-%d %H:%M:%S'),
                        'path': entry.path_display
                    })

        # Sort by date, newest first
        backups.sort(key=lambda x: x['date'], reverse=True)

        return {
            'success': True,
            'backups': backups,
            'total_count': len(backups)
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'backups': []
        }

def get_dropbox_backup_status():
    """
    Get Dropbox backup system status
    Returns: dict with Dropbox backup health information
    """
    try:
        dbx = get_dropbox_client()
        if not dbx:
            return {
                'configured': False,
                'healthy': False,
                'error': 'Dropbox credentials not configured or SDK not installed'
            }

        # Get account info
        account = dbx.users_get_current_account()

        # List backups
        backups_result = list_dropbox_backups()

        if not backups_result['success']:
            return {
                'configured': True,
                'healthy': False,
                'error': backups_result['error']
            }

        backups = backups_result['backups']

        if not backups:
            return {
                'configured': True,
                'healthy': False,
                'account_email': account.email,
                'total_backups': 0,
                'last_backup': None,
                'warning': 'No backups found in Dropbox'
            }

        last_backup = backups[0]
        hours_since_last = (datetime.now(pytz.UTC) - last_backup['date']).total_seconds() / 3600

        # Check if backup is recent (within 2 hours = 2 backup cycles)
        healthy = hours_since_last < 2

        total_size_mb = sum(b['size_kb'] for b in backups) / 1024

        return {
            'configured': True,
            'healthy': healthy,
            'account_email': account.email,
            'total_backups': len(backups),
            'last_backup': last_backup,
            'hours_since_last': hours_since_last,
            'total_size_mb': total_size_mb,
            'warning': None if healthy else f'Last Dropbox backup was {hours_since_last:.1f} hours ago. Expected hourly backups.'
        }

    except Exception as e:
        return {
            'configured': True,
            'healthy': False,
            'error': str(e)
        }

def upload_backup_to_dropbox(local_backup_path):
    """
    Upload a local backup file to Dropbox
    Returns: dict with success status
    """
    try:
        dbx = get_dropbox_client()
        if not dbx:
            return {
                'success': False,
                'error': 'Dropbox not configured'
            }

        if not os.path.exists(local_backup_path):
            return {
                'success': False,
                'error': 'Backup file not found'
            }

        filename = os.path.basename(local_backup_path)
        dropbox_path = f'/{filename}'

        with open(local_backup_path, 'rb') as f:
            dbx.files_upload(
                f.read(),
                dropbox_path,
                mode=dropbox.files.WriteMode.overwrite
            )

        return {
            'success': True,
            'dropbox_path': dropbox_path,
            'filename': filename
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
