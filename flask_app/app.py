"""
Fire Department Management System - SQLite Version
Clean rewrite using SQLite database instead of JSON files
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from datetime import datetime, timedelta
import pytz
from io import StringIO, BytesIO
import csv
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import db_helpers

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Validate required environment variables
if not all([app.secret_key, ADMIN_USERNAME, ADMIN_PASSWORD]):
    raise ValueError("Missing required environment variables. Check your .env file.")

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('firefighter.log', maxBytes=1000000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Timezone configuration
central = pytz.timezone('America/Chicago')

# Template filters
@app.template_filter('fromisoformat')
def fromisoformat_filter(date_string):
    return datetime.fromisoformat(date_string)

def format_log_time(log_time):
    """Format log time to a more readable format with correct timezone"""
    dt = datetime.fromisoformat(log_time)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    central_time = dt.astimezone(central)
    return central_time.strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['format_log_time'] = format_log_time

# ========== ROUTES ==========

@app.route('/')
def index():
    """Home page - clock in/out interface"""
    show_new_user_form = session.get('show_new_user_form', False)
    session.pop('show_new_user_form', None)
    categories = [cat['name'] for cat in db_helpers.get_all_categories()]
    return render_template('index.html', show_new_user_form=show_new_user_form, categories=categories)

@app.route('/register', methods=['POST'])
def register():
    """Register a new firefighter"""
    try:
        full_name = request.form['full_name']
        fireman_number = request.form['fireman_number']

        result = db_helpers.create_firefighter(fireman_number, full_name)

        if result:
            flash(f'Fireman {full_name} registered successfully!')
            logger.info(f"New firefighter registered: {full_name}")
        else:
            flash(f'Fireman {full_name} already exists!')

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        flash('An error occurred during registration.')

    return redirect(url_for('index'))

@app.route('/clock_in', methods=['POST'])
def clock_in():
    """Clock in a firefighter"""
    try:
        fireman_number = request.form['username']
        activity = request.form['activity']
        other_activity = request.form.get('other_activity', '').strip()

        if activity == "Other" and other_activity:
            activity = other_activity

        # Check if firefighter exists
        firefighter = db_helpers.get_firefighter_by_number(fireman_number)

        if not firefighter:
            flash('You need to register before clocking in!')
            session['show_new_user_form'] = True
            return redirect(url_for('index'))

        # Clock in
        success, message = db_helpers.clock_in(fireman_number, activity)

        if success:
            flash(f'Fireman {firefighter["full_name"]} clocked in for {activity}!')
            logger.info(f"Clock in: {firefighter['full_name']} - {activity}")
        else:
            flash(f'Error: {message}')

    except Exception as e:
        logger.error(f"Clock in error: {str(e)}")
        flash('An error occurred while clocking in.')

    return redirect(url_for('index'))

@app.route('/clock_out', methods=['POST'])
def clock_out():
    """Clock out a firefighter"""
    try:
        fireman_number = request.form['username']

        # Check if firefighter exists
        firefighter = db_helpers.get_firefighter_by_number(fireman_number)

        if not firefighter:
            flash('You need to register before clocking out!')
            return redirect(url_for('index'))

        # Clock out
        success, message = db_helpers.clock_out(fireman_number)

        if success:
            flash(f'Fireman {firefighter["full_name"]} {message}')
            logger.info(f"Clock out: {firefighter['full_name']} - {message}")
        else:
            flash(f'Error: {message}')

    except Exception as e:
        logger.error(f"Clock out error: {str(e)}")
        flash('An error occurred while clocking out.')

    return redirect(url_for('index'))

# ========== ADMIN ROUTES ==========

@app.route('/admin', methods=['GET'])
def admin():
    """Admin login page"""
    if session.get('logged_in'):
        return redirect(url_for('admin_panel'))
    return render_template('admin_login.html')

@app.route('/admin', methods=['POST'])
def admin_auth():
    """Admin authentication"""
    username = request.form['username']
    password = request.form['password']

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        logger.info("Admin login successful")
        return redirect(url_for('admin_panel'))

    logger.warning(f"Failed admin login attempt with username: {username}")
    flash('Invalid credentials!')
    return redirect(url_for('admin'))

@app.route('/admin_panel')
def admin_panel():
    """Admin panel - manage firefighters and view logs"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    # Get all data
    firefighters_list = db_helpers.get_all_firefighters()
    categories_list = [cat['name'] for cat in db_helpers.get_all_categories()]

    # Convert to format expected by template
    user_data = {}
    for ff in firefighters_list:
        logs = db_helpers.get_firefighter_logs(ff['fireman_number'])
        user_data[ff['fireman_number']] = {
            'full_name': ff['full_name'],
            'hours': ff['total_hours'],
            'logs': logs
        }

    return render_template('admin.html', user_data=user_data, categories=categories_list)

@app.route('/update_hours', methods=['POST'])
def update_hours():
    """Manually add hours for a firefighter"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        fireman_number = request.form['fireman_number']
        activity = request.form['activity']
        log_date = request.form['log_date']
        time_in = request.form['time_in']
        time_out = request.form['time_out']

        success, message = db_helpers.add_manual_hours(
            fireman_number, activity, log_date, time_in, time_out
        )

        if success:
            firefighter = db_helpers.get_firefighter_by_number(fireman_number)
            flash(f'Created a new log for {firefighter["full_name"]}: {message}')
            logger.info(f"Manual hours update: {firefighter['full_name']} - {message}")
        else:
            flash(f'Error: {message}')

    except Exception as e:
        logger.error(f"Update hours error: {str(e)}")
        flash('An error occurred while updating hours.')

    return redirect(url_for('admin_panel'))

@app.route('/edit_firefighter', methods=['POST'])
def edit_firefighter():
    """Edit firefighter information"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        fireman_number = request.form['fireman_number']
        new_fireman_number = request.form['new_fireman_number']
        new_full_name = request.form['full_name']

        db_helpers.update_firefighter(fireman_number, new_fireman_number, new_full_name)

        flash('Firefighter information updated successfully!')
        logger.info(f"Firefighter edited: {new_full_name}")

    except Exception as e:
        logger.error(f"Edit firefighter error: {str(e)}")
        flash('An error occurred while updating firefighter information.')

    return redirect(url_for('admin_panel'))

@app.route('/delete_firefighter', methods=['POST'])
def delete_firefighter():
    """Delete a firefighter"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        fireman_number = request.form['fireman_number']

        firefighter = db_helpers.get_firefighter_by_number(fireman_number)

        if firefighter:
            db_helpers.delete_firefighter(fireman_number)
            flash(f'Firefighter {firefighter["full_name"]} has been deleted successfully!')
            logger.info(f"Firefighter deleted: {firefighter['full_name']}")
        else:
            flash('Firefighter not found!')

    except Exception as e:
        logger.error(f"Delete firefighter error: {str(e)}")
        flash('An error occurred while deleting the firefighter.')

    return redirect(url_for('admin_panel'))

@app.route('/add_category', methods=['POST'])
def add_category():
    """Add a new activity category"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        new_category = request.form['new_category']

        result = db_helpers.create_category(new_category)

        if result:
            flash(f'Category "{new_category}" added successfully!')
            logger.info(f"New category added: {new_category}")
        else:
            flash('Invalid or duplicate category!')

    except Exception as e:
        logger.error(f"Add category error: {str(e)}")
        flash('An error occurred while adding the category.')

    return redirect(url_for('admin_panel'))

@app.route('/remove_category', methods=['POST'])
def remove_category():
    """Remove an activity category"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        category_to_remove = request.form['category_to_remove']

        db_helpers.delete_category(category_to_remove)

        flash(f'Category "{category_to_remove}" removed successfully!')
        logger.info(f"Category removed: {category_to_remove}")

    except Exception as e:
        logger.error(f"Remove category error: {str(e)}")
        flash('An error occurred while removing the category.')

    return redirect(url_for('admin_panel'))

@app.route('/delete_log', methods=['POST'])
def delete_log():
    """Delete a specific log entry"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        fireman_number = request.form['fireman_number']
        log_index = int(request.form['log_index'])

        success, message = db_helpers.delete_log(fireman_number, log_index)

        if success:
            flash('Log entry deleted successfully!')
            firefighter = db_helpers.get_firefighter_by_number(fireman_number)
            logger.info(f"Log deleted for firefighter: {firefighter['full_name']}")
        else:
            flash(f'Error: {message}')

    except Exception as e:
        logger.error(f"Delete log error: {str(e)}")
        flash('An error occurred while deleting the log.')

    return redirect(url_for('admin_panel'))

@app.route('/clear_all_logs', methods=['POST'])
def clear_all_logs():
    """Clear all logs and reset hours"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        db_helpers.clear_all_logs()
        flash('All logs and hours have been cleared successfully!')
        logger.info("All logs cleared")

    except Exception as e:
        logger.error(f"Clear logs error: {str(e)}")
        flash('An error occurred while clearing logs.')

    return redirect(url_for('admin_panel'))

@app.route('/export_data')
def export_data():
    """Export firefighter time logs to CSV (formatted for payroll)"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        # Get month and year from query parameters
        month = request.args.get('month')
        year = request.args.get('year')

        output = StringIO()
        cw = csv.writer(output)

        # Header row
        if month and year:
            month_name = datetime(int(year), int(month), 1).strftime('%B %Y')
            cw.writerow([f'PAYROLL REPORT - {month_name}'])
        else:
            cw.writerow(['PAYROLL REPORT - ALL TIME'])
        cw.writerow([])  # Blank row

        firefighters = db_helpers.get_all_firefighters()

        for ff in firefighters:
            logs = db_helpers.get_firefighter_logs(ff['fireman_number'])

            # Filter logs by month/year if specified
            filtered_logs = []
            month_total = 0

            for log in logs:
                if log['time_in']:
                    time_in = datetime.fromisoformat(log['time_in'])

                    # Filter by month and year if provided
                    if month and year:
                        if time_in.month != int(month) or time_in.year != int(year):
                            continue

                    filtered_logs.append(log)
                    month_total += log.get('hours_worked', 0) or 0

            # Only show firefighter if they have logs in this period
            if filtered_logs:
                # Firefighter header
                cw.writerow([f"FIREFIGHTER #{ff['fireman_number']} - {ff['full_name']}"])
                cw.writerow(['Date', 'Time In', 'Time Out', 'Activity', 'Hours Worked'])

                # Individual log entries
                for log in filtered_logs:
                    time_in_dt = datetime.fromisoformat(log['time_in']) if log['time_in'] else None
                    time_out_dt = datetime.fromisoformat(log['time_out']) if log['time_out'] else None

                    date_str = time_in_dt.strftime('%Y-%m-%d') if time_in_dt else ''
                    time_in_str = time_in_dt.strftime('%I:%M %p') if time_in_dt else ''
                    time_out_str = time_out_dt.strftime('%I:%M %p') if time_out_dt else 'Still clocked in'
                    hours = f"{log.get('hours_worked', 0):.2f}" if log.get('hours_worked') else '0.00'

                    cw.writerow([
                        date_str,
                        time_in_str,
                        time_out_str,
                        log['type'],
                        hours
                    ])

                # Subtotal for this firefighter
                cw.writerow(['', '', '', 'TOTAL HOURS:', f"{month_total:.2f}"])
                cw.writerow([])  # Blank row between firefighters

        output.seek(0)

        # Generate filename
        if month and year:
            filename = f'payroll_{year}_{int(month):02d}.csv'
        else:
            filename = 'payroll_all_time.csv'

        return send_file(
            BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        flash('An error occurred during export.')
        return redirect(url_for('admin_panel'))

@app.route('/export_inspections')
def export_inspections():
    """Export vehicle inspection logs to CSV"""
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        # Get month and year from query parameters
        month = request.args.get('month')
        year = request.args.get('year')

        output = StringIO()
        cw = csv.writer(output)

        # Header row
        if month and year:
            month_name = datetime(int(year), int(month), 1).strftime('%B %Y')
            cw.writerow([f'VEHICLE INSPECTION REPORT - {month_name}'])
        else:
            cw.writerow(['VEHICLE INSPECTION REPORT - ALL TIME'])
        cw.writerow([])
        cw.writerow(['Vehicle Code', 'Vehicle Name', 'Inspection Date', 'Inspector', 'Result', 'Notes'])

        vehicles = db_helpers.get_all_vehicles()

        for vehicle in vehicles:
            history = db_helpers.get_vehicle_inspection_history(vehicle['id'], limit=1000)

            for inspection in history:
                # Filter by month and year if provided
                if month and year:
                    inspection_date = datetime.fromisoformat(inspection['date'])
                    if inspection_date.month != int(month) or inspection_date.year != int(year):
                        continue

                date_str = datetime.fromisoformat(inspection['date']).strftime('%Y-%m-%d %I:%M %p')
                result = 'PASSED' if inspection['passed'] else 'FAILED'

                cw.writerow([
                    vehicle['code'],
                    vehicle['name'],
                    date_str,
                    inspection['inspector'],
                    result,
                    inspection.get('notes', '')
                ])

        output.seek(0)

        # Generate filename
        if month and year:
            filename = f'inspections_{year}_{int(month):02d}.csv'
        else:
            filename = 'inspections_all_time.csv'

        return send_file(
            BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Inspection export error: {str(e)}")
        flash('An error occurred during inspection export.')
        return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    """Logout admin"""
    session.pop('logged_in', None)
    flash('Logged out successfully!')
    logger.info("Admin logged out")
    return redirect(url_for('index'))

# ========== DISPLAY ROUTES ==========

@app.route('/display')
def display():
    """Display dashboard - active firefighters and leaderboard"""
    try:
        active_firefighters = db_helpers.get_active_firefighters()
        leaderboard = db_helpers.get_leaderboard()
        vehicles_needing_inspection = db_helpers.get_vehicles_needing_inspection()

        logger.info("Display page loaded successfully")
        return render_template('display.html',
                             active_firefighters=active_firefighters,
                             leaderboard=leaderboard,
                             vehicles_needing_inspection=vehicles_needing_inspection)

    except Exception as e:
        logger.error(f"Display page error: {str(e)}")
        flash('An error occurred while loading the display page.')
        return redirect(url_for('index'))

@app.route('/get_firefighter_logs/<fireman_number>')
def get_firefighter_logs(fireman_number):
    """API endpoint to get firefighter logs"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authorized'}), 401

    firefighter = db_helpers.get_firefighter_by_number(fireman_number)

    if not firefighter:
        return jsonify({'error': 'Firefighter not found'}), 404

    logs = db_helpers.get_firefighter_logs(fireman_number)

    # Format logs for display
    formatted_logs = []
    for log in logs:
        time_in = datetime.fromisoformat(log['time_in'])
        if time_in.tzinfo is None:
            time_in = pytz.utc.localize(time_in)
        time_in = time_in.astimezone(central)

        hours = 'N/A'
        time_out_display = 'Still Active'

        if log['time_out']:
            time_out = datetime.fromisoformat(log['time_out'])
            if time_out.tzinfo is None:
                time_out = pytz.utc.localize(time_out)
            time_out = time_out.astimezone(central)
            time_out_display = time_out.strftime('%Y-%m-%d %H:%M:%S')

            hours_val = log.get('hours_worked') or log.get('manual_added_hours')
            if hours_val:
                hours = f"{hours_val:.2f}"

        formatted_logs.append({
            'type': log['type'],
            'time_in': time_in.strftime('%Y-%m-%d %H:%M:%S'),
            'time_out': time_out_display,
            'hours': hours
        })

    return jsonify({
        'logs': formatted_logs,
        'name': firefighter['full_name']
    })

# ========== VEHICLE INSPECTION ROUTES ==========

@app.route('/inspections')
def inspections_menu():
    """Vehicle inspections menu - select a vehicle"""
    vehicles = db_helpers.get_vehicles_needing_inspection()
    return render_template('inspections_menu.html', vehicles=vehicles)

@app.route('/inspect/<int:vehicle_id>')
def inspect_vehicle(vehicle_id):
    """Start inspection for a specific vehicle"""
    vehicle = db_helpers.get_vehicle_by_id(vehicle_id)

    if not vehicle:
        flash('Vehicle not found!')
        return redirect(url_for('inspections_menu'))

    checklist_items = db_helpers.get_inspection_checklist()
    firefighters = db_helpers.get_all_firefighters()

    return render_template('inspect_vehicle.html',
                         vehicle=vehicle,
                         checklist_items=checklist_items,
                         firefighters=firefighters)

@app.route('/submit_inspection', methods=['POST'])
def submit_inspection():
    """Submit a vehicle inspection"""
    try:
        vehicle_id = int(request.form['vehicle_id'])
        inspector_number = request.form.get('inspector_number', '')
        additional_notes = request.form.get('additional_notes', '')

        # Get inspector ID
        inspector = None
        if inspector_number:
            inspector = db_helpers.get_firefighter_by_number(inspector_number)

        inspector_id = inspector['id'] if inspector else None

        # Collect inspection results
        inspection_results = []
        checklist_items = db_helpers.get_inspection_checklist()

        for item in checklist_items:
            item_id = item['id']
            status = request.form.get(f'item_{item_id}', 'pass')
            notes = request.form.get(f'notes_{item_id}', '')

            inspection_results.append({
                'item_id': item_id,
                'status': status,
                'notes': notes
            })

        # Save inspection
        success, result = db_helpers.create_vehicle_inspection(
            vehicle_id,
            inspector_id,
            inspection_results,
            additional_notes
        )

        if success:
            vehicle = db_helpers.get_vehicle_by_id(vehicle_id)
            flash(f'Inspection for {vehicle["name"]} completed successfully!')
            logger.info(f"Vehicle inspection completed: {vehicle['name']}")
            return redirect(url_for('inspections_menu'))
        else:
            flash(f'Error saving inspection: {result}')
            return redirect(url_for('inspect_vehicle', vehicle_id=vehicle_id))

    except Exception as e:
        logger.error(f"Submit inspection error: {str(e)}")
        flash('An error occurred while submitting the inspection.')
        return redirect(url_for('inspections_menu'))

@app.route('/inspection_history/<int:vehicle_id>')
def inspection_history(vehicle_id):
    """View inspection history for a vehicle"""
    vehicle = db_helpers.get_vehicle_by_id(vehicle_id)

    if not vehicle:
        flash('Vehicle not found!')
        return redirect(url_for('inspections_menu'))

    history = db_helpers.get_vehicle_inspection_history(vehicle_id)

    return render_template('inspection_history.html',
                         vehicle=vehicle,
                         history=history)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
