from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from datetime import datetime, timedelta
import pytz
from io import StringIO, BytesIO
import json
import os
import csv
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox import Dropbox
from backup_manager import BackupManager
import atexit
import shutil
import threading
import time
import logging
import fcntl
from logging.handlers import RotatingFileHandler
from dropbox.exceptions import ApiError, HttpError
import requests

# Optional import for psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not installed; resource monitoring will be disabled")

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'sAeUmAQfqAwnmxyRnexjBNDPgp')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'Firefighter')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'thisisthePassword$$5')

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

# Dropbox Configuration
DROPBOX_APP_KEY = '0hpcgffvcu5vuei'
DROPBOX_APP_SECRET = '6kwngadn7oh3yrl'
DROPBOX_REFRESH_TOKEN = 'K98vLaIfGvMAAAAAAAAAAWHechPq9eCkRrYkWoOSjzZ3m7-ixpWNgiXspj0Vopvh'

# Initialize backup manager with retries
backup_manager = BackupManager(
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET,
    refresh_token=DROPBOX_REFRESH_TOKEN,
    backup_interval=3600,  # Backup every hour
    max_retries=3,
    retry_delay=5
)

# Define files to backup
files_to_backup = {
    'user_data.json': '/user_data_backup',
    'categories.json': '/categories_backup'
}

# Data files
data_file = 'user_data.json'
categories_file = 'categories.json'

# Add timezone configuration
central = pytz.timezone('America/Chicago')  # Central Time

# New Safety Functions
def safely_load_json(filename, default_value):
    """
    Safely load JSON file with backup fallback and error handling
    """
    try:
        with open(filename, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            logger.info(f"Successfully loaded {filename}")
            return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading {filename}: {str(e)}")
        # Try to load from most recent backup
        try:
            backup_files = [f for f in os.listdir() if f.startswith(f"{filename.replace('.json', '')}_backup")]
            if backup_files:
                latest_backup = max(backup_files)
                logger.info(f"Attempting to load from backup: {latest_backup}")
                with open(latest_backup, 'r') as f:
                    return json.load(f)
        except Exception as backup_e:
            logger.error(f"Backup loading failed: {str(backup_e)}")

        logger.warning(f"Using default value for {filename}")
        return default_value

def safe_write_json(filename, data):
    """
    Safely write JSON data with file locking and backup creation
    """
    temp_file = f"{filename}.tmp"
    try:
        with open(temp_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        os.rename(temp_file, filename)
        logger.info(f"Successfully wrote {filename}")
        create_backup()  # Create backup after successful write
    except Exception as e:
        logger.error(f"Error writing {filename}: {str(e)}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise

def verify_json_integrity():
    """
    Verify integrity of JSON files
    """
    try:
        safely_load_json(data_file, {})
        safely_load_json(categories_file, [])
        logger.info("JSON integrity check passed")
    except Exception as e:
        logger.error(f"JSON integrity check failed: {str(e)}")

# Load or initialize user data with safe loading
user_data = safely_load_json(data_file, {})
categories = safely_load_json(categories_file, ["Firefighting", "Training", "Work Night", "Board Meeting", "EMR Meeting"])

# Enhanced backup creation
def create_backup():
    """Create backup with enhanced error handling"""
    try:
        success = backup_manager.perform_backup(files_to_backup)
        if success:
            logger.info("Backup created successfully")
            return True
        else:
            logger.error("Backup failed after retries")
            return False
    except Exception as e:
        logger.error(f"Backup error: {str(e)}")
        return False

# Core functionality functions
def get_activity_hours(activity_type):
    """Returns the hours to credit for each activity type when auto checking out"""
    durations = {
        "Training": 2,
        "EMR Meeting": 2,
        "Work Night": 2,
        "Board Meeting": 3,
    }
    return durations.get(activity_type, 5)

def process_auto_checkouts(user_data, central_tz=pytz.timezone('America/Chicago')):
    """Process automatic checkouts for sessions over 12 hours"""
    now = datetime.now(central_tz)
    processed_checkouts = []

    for fireman_number, details in user_data.items():
        for log in details['logs']:
            if log['time_out'] is None:
                time_in = datetime.fromisoformat(log['time_in'])
                if time_in.tzinfo is None:
                    time_in = pytz.utc.localize(time_in)
                time_in = time_in.astimezone(central_tz)

                duration = (now - time_in).total_seconds() / 3600

                if duration > 12:
                    credited_hours = get_activity_hours(log['type'])
                    checkout_time = time_in + timedelta(hours=credited_hours)
                    log['time_out'] = checkout_time.isoformat()
                    log['auto_checkout'] = True
                    log['auto_checkout_note'] = f"Historical auto-checkout after {credited_hours} hours (system cleanup)"
                    details['hours'] += credited_hours

                    processed_checkouts.append({
                        'fireman_number': fireman_number,
                        'name': details['full_name'],
                        'activity': log['type'],
                        'time_in': time_in.isoformat(),
                        'time_out': log['time_out'],
                        'hours_added': credited_hours
                    })

    return processed_checkouts

def start_auto_checkout_scheduler():
    """Starts a background thread that checks for and processes automatic checkouts"""
    def auto_checkout_task():
        while True:
            try:
                processed = process_auto_checkouts(user_data)
                if processed:
                    safe_write_json(data_file, user_data)
                    for checkout in processed:
                        logger.info(
                            f"Auto checkout after 12+ hours: {checkout['name']} from {checkout['activity']} "
                            f"credited with {checkout['hours_added']} hours"
                        )
            except Exception as e:
                logger.error(f"Auto checkout error: {str(e)}")
            time.sleep(300)  # Check every 5 minutes

    auto_checkout_thread = threading.Thread(target=auto_checkout_task, daemon=True)
    auto_checkout_thread.start()

def format_log_time(log_time):
    """Format log time to a more readable format with correct timezone"""
    dt = datetime.fromisoformat(log_time)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    central_time = dt.astimezone(central)
    return central_time.strftime('%Y-%m-%d %H:%M:%S')

# Template filters
@app.template_filter('fromisoformat')
def fromisoformat_filter(date_string):
    return datetime.fromisoformat(date_string)

app.jinja_env.filters['format_log_time'] = format_log_time

# Application startup and cleanup
@app.before_first_request
def start_backup_system():
    """Initialize backup and monitoring systems"""
    try:
        backup_manager.start_automatic_backup(files_to_backup)
        start_auto_checkout_scheduler()

        def run_verify():
            while True:
                verify_json_integrity()
                time.sleep(900)  # Check every 15 minutes

        integrity_thread = threading.Thread(target=run_verify, daemon=True)
        integrity_thread.start()

        # Add heartbeat to detect crashes
        def heartbeat():
            while True:
                logger.info("Heartbeat: App is running")
                time.sleep(300)  # Every 5 minutes
        threading.Thread(target=heartbeat, daemon=True).start()

        # Add resource monitoring if psutil is available
        if PSUTIL_AVAILABLE:
            def log_resources():
                while True:
                    process = psutil.Process(os.getpid())
                    memory = process.memory_info().rss / 1024 / 1024  # MB
                    cpu = process.cpu_percent(interval=1.0)
                    logger.info(f"Memory usage: {memory:.2f} MB, CPU usage: {cpu:.2f}%")
                    time.sleep(3600)  # Every hour
            threading.Thread(target=log_resources, daemon=True).start()
        else:
            logger.info("Resource monitoring skipped (psutil not available)")

        logger.info("Backup and monitoring systems initialized successfully")
    except Exception as e:
        logger.error(f"Error starting backup system: {str(e)}")

@atexit.register
def cleanup():
    """Cleanup with enhanced error handling"""
    try:
        backup_manager.stop_automatic_backup()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")

# Routes
@app.route('/')
def index():
    show_new_user_form = session.get('show_new_user_form', False)
    session.pop('show_new_user_form', None)
    return render_template('index.html', show_new_user_form=show_new_user_form, categories=categories)

@app.route('/register', methods=['POST'])
def register():
    try:
        full_name = request.form['full_name']
        fireman_number = request.form['fireman_number']

        if fireman_number not in user_data:
            user_data[fireman_number] = {"full_name": full_name, "hours": 0, "logs": []}
            safe_write_json(data_file, user_data)
            flash(f'Fireman {full_name} registered successfully!')
            logger.info(f"New firefighter registered: {full_name}")
        else:
            flash(f'Fireman {full_name} already exists!')
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        flash('An error occurred during registration.')
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET'])
def admin():
    if session.get('logged_in'):
        return redirect(url_for('admin_panel'))
    return render_template('admin_login.html')

@app.route('/admin', methods=['POST'])
def admin_auth():
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
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))
    return render_template('admin.html', user_data=user_data, categories=categories)

@app.route('/clock_in', methods=['POST'])
def clock_in():
    try:
        fireman_number = request.form['username']
        activity = request.form['activity']
        other_activity = request.form.get('other_activity', '').strip()

        if activity == "Other" and other_activity:
            activity = other_activity

        if fireman_number not in user_data:
            flash('You need to register before clocking in!')
            session['show_new_user_form'] = True
            return redirect(url_for('index'))

        clock_in_time = datetime.now(central).isoformat()
        user_data[fireman_number]['logs'].append({
            "type": activity,
            "time_in": clock_in_time,
            "time_out": None
        })

        safe_write_json(data_file, user_data)
        flash(f'Fireman {user_data[fireman_number]["full_name"]} clocked in for {activity}!')
        logger.info(f"Clock in: {user_data[fireman_number]['full_name']} - {activity}")
    except Exception as e:
        logger.error(f"Clock in error: {str(e)}")
        flash('An error occurred while clocking in.')
    return redirect(url_for('index'))

@app.route('/clock_out', methods=['POST'])
def clock_out():
    try:
        fireman_number = request.form['username']

        if fireman_number not in user_data:
            flash('You need to register before clocking out!')
            return redirect(url_for('index'))

        if not any(log['time_out'] is None for log in user_data[fireman_number]['logs']):
            flash('You have never checked in!')
            return redirect(url_for('index'))

        for log in reversed(user_data[fireman_number]['logs']):
            if log['time_out'] is None:
                log['time_out'] = datetime.now(central).isoformat()
                time_in = datetime.fromisoformat(log['time_in'])
                time_out = datetime.fromisoformat(log['time_out'])

                if time_in.tzinfo is None:
                    time_in = pytz.utc.localize(time_in)
                if time_out.tzinfo is None:
                    time_out = pytz.utc.localize(time_out)

                hours_worked = (time_out - time_in).total_seconds() / 3600
                user_data[fireman_number]['hours'] += hours_worked

                safe_write_json(data_file, user_data)
                flash(f'Fireman {user_data[fireman_number]["full_name"]} clocked out after {hours_worked:.2f} hours!')
                logger.info(f"Clock out: {user_data[fireman_number]['full_name']} - {hours_worked:.2f} hours")
                break
    except Exception as e:
        logger.error(f"Clock out error: {str(e)}")
        flash('An error occurred while clocking out.')
    return redirect(url_for('index'))

@app.route('/update_hours', methods=['POST'])
def update_hours():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        fireman_number = request.form['fireman_number']
        activity = request.form['activity']
        log_date = request.form['log_date']
        time_in = request.form['time_in']
        time_out = request.form['time_out']

        if fireman_number in user_data:
            datetime_in = central.localize(
                datetime.strptime(f"{log_date} {time_in}", "%Y-%m-%d %H:%M")
            )
            datetime_out = central.localize(
                datetime.strptime(f"{log_date} {time_out}", "%Y-%m-%d %H:%M")
            )

            hours_worked = (datetime_out - datetime_in).total_seconds() / 3600

            user_data[fireman_number]['logs'].append({
                'type': activity,
                'time_in': datetime_in.isoformat(),
                'time_out': datetime_out.isoformat(),
                'manual_added_hours': hours_worked
            })

            user_data[fireman_number]['hours'] += hours_worked

            safe_write_json(data_file, user_data)
            flash(f'Created a new log for {user_data[fireman_number]["full_name"]} with {hours_worked:.2f} hours.')
            logger.info(f"Manual hours update: {user_data[fireman_number]['full_name']} - {hours_worked:.2f} hours")
        else:
            flash(f'No firefighter found with the number {fireman_number}.')
    except Exception as e:
        logger.error(f"Update hours error: {str(e)}")
        flash('An error occurred while updating hours.')

    return redirect(url_for('admin_panel'))

@app.route('/edit_firefighter', methods=['POST'])
def edit_firefighter():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        fireman_number = request.form['fireman_number']
        new_fireman_number = request.form['new_fireman_number']
        new_full_name = request.form['full_name']

        if fireman_number in user_data:
            if fireman_number != new_fireman_number:
                user_data[new_fireman_number] = user_data.pop(fireman_number)

            user_data[new_fireman_number]['full_name'] = new_full_name

            safe_write_json(data_file, user_data)
            flash('Firefighter information updated successfully!')
            logger.info(f"Firefighter edited: {new_full_name}")
        else:
            flash('Firefighter not found!')
    except Exception as e:
        logger.error(f"Edit firefighter error: {str(e)}")
        flash('An error occurred while updating firefighter information.')

    return redirect(url_for('admin_panel'))

@app.route('/delete_firefighter', methods=['POST'])
def delete_firefighter():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        fireman_number = request.form['fireman_number']

        if fireman_number in user_data:
            firefighter_name = user_data[fireman_number]['full_name']
            del user_data[fireman_number]

            safe_write_json(data_file, user_data)
            flash(f'Firefighter {firefighter_name} has been deleted successfully!')
            logger.info(f"Firefighter deleted: {firefighter_name}")
        else:
            flash('Firefighter not found!')
    except Exception as e:
        logger.error(f"Delete firefighter error: {str(e)}")
        flash('An error occurred while deleting the firefighter.')

    return redirect(url_for('admin_panel'))

@app.route('/add_category', methods=['POST'])
def add_category():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        new_category = request.form['new_category']
        if new_category and new_category not in categories:
            categories.append(new_category)
            safe_write_json(categories_file, categories)
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
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        category_to_remove = request.form['category_to_remove']
        if category_to_remove in categories:
            categories.remove(category_to_remove)
            safe_write_json(categories_file, categories)
            flash(f'Category "{category_to_remove}" removed successfully!')
            logger.info(f"Category removed: {category_to_remove}")
        else:
            flash('Category not found!')
    except Exception as e:
        logger.error(f"Remove category error: {str(e)}")
        flash('An error occurred while removing the category.')

    return redirect(url_for('admin_panel'))

@app.route('/export_data')
def export_data():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        # Get month and year from query parameters
        month = request.args.get('month')
        year = request.args.get('year')
        output = StringIO()
        cw = csv.writer(output)
        cw.writerow(['Firefighter Number', 'Name', 'Total Hours', 'Activity', 'Time In', 'Time Out', 'Manual Added Hours'])
        for fireman_number, details in user_data.items():
            for log in details['logs']:
                # Filter by month and year if provided
                if month and year:
                    time_in = datetime.fromisoformat(log['time_in'])
                    if time_in.month != int(month) or time_in.year != int(year):
                        continue
                cw.writerow([
                    fireman_number,
                    details['full_name'],
                    details['hours'],
                    log['type'],
                    log['time_in'],
                    log['time_out'],
                    log.get('manual_added_hours', '')
                ])
        output.seek(0)
        return send_file(BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='firefighters_export.csv')
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        flash('An error occurred during export.')
        return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully!')
    logger.info("Admin logged out")
    return redirect(url_for('index'))

@app.route('/display')
def display():
    try:
        active_firefighters = []

        for fireman_number, details in user_data.items():
            for log in reversed(details['logs']):
                if log['time_out'] is None:
                    active_firefighters.append({
                        'number': fireman_number,
                        'name': details['full_name'],
                        'activity': log['type'],
                        'time_in': log['time_in']
                    })
                    break

        leaderboard = []
        for fireman_number, details in user_data.items():
            leaderboard.append({
                'number': fireman_number,
                'name': details['full_name'],
                'hours': details['hours']
            })

        leaderboard.sort(key=lambda x: x['hours'], reverse=True)
        logger.info("Display page loaded successfully")
        return render_template('display.html',
                             active_firefighters=active_firefighters,
                             leaderboard=leaderboard)
    except Exception as e:
        logger.error(f"Display page error: {str(e)}")
        flash('An error occurred while loading the display page.')
        return redirect(url_for('index'))

@app.route('/clear_all_logs', methods=['POST'])
def clear_all_logs():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        for fireman_number in user_data:
            user_data[fireman_number]['hours'] = 0
            user_data[fireman_number]['logs'] = []

        safe_write_json(data_file, user_data)
        flash('All logs and hours have been cleared successfully!')
        logger.info("All logs cleared")
    except Exception as e:
        logger.error(f"Clear logs error: {str(e)}")
        flash('An error occurred while clearing logs.')

    return redirect(url_for('admin_panel'))

@app.route('/test_backup')
def test_backup():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        logger.info("Starting backup test...")
        success = backup_manager.perform_backup(files_to_backup)
        if success:
            flash('Backup completed successfully!')
            logger.info("Backup test completed successfully")
        else:
            flash('Backup failed after retries!')
            logger.error("Backup test failed after retries")
    except Exception as e:
        logger.error(f"Backup test error: {str(e)}")
        flash(f'Backup failed: {str(e)}')

    return redirect(url_for('admin_panel'))

@app.route('/delete_log', methods=['POST'])
def delete_log():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        fireman_number = request.form['fireman_number']
        log_index = int(request.form['log_index'])

        if fireman_number in user_data:
            try:
                # If the log has hours recorded, subtract them from total
                log_to_delete = user_data[fireman_number]['logs'][log_index]
                if 'manual_added_hours' in log_to_delete:
                    user_data[fireman_number]['hours'] -= log_to_delete['manual_added_hours']
                elif log_to_delete['time_out']:  # If it was a normal clock in/out
                    time_in = datetime.fromisoformat(log_to_delete['time_in'])
                    time_out = datetime.fromisoformat(log_to_delete['time_out'])
                    if time_in.tzinfo is None:
                        time_in = pytz.utc.localize(time_in)
                    if time_out.tzinfo is None:
                        time_out = pytz.utc.localize(time_out)
                    hours = (time_out - time_in).total_seconds() / 3600
                    user_data[fireman_number]['hours'] -= hours

                # Delete the log
                del user_data[fireman_number]['logs'][log_index]

                # Save changes
                safe_write_json(data_file, user_data)
                logger.info(f"Log deleted for firefighter: {user_data[fireman_number]['full_name']}")
                flash('Log entry deleted successfully!')
            except Exception as e:
                logger.error(f"Error deleting log: {str(e)}")
                flash(f'Error deleting log: {str(e)}')
        else:
            flash('Firefighter not found!')
    except Exception as e:
        logger.error(f"Delete log error: {str(e)}")
        flash('An error occurred while deleting the log.')

    return redirect(url_for('admin_panel'))

@app.route('/check_credentials')
def check_credentials():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    return f"""
    <h2>Current Dropbox Credentials:</h2>
    <p>App Key: {DROPBOX_APP_KEY}</p>
    <p>App Secret: {DROPBOX_APP_SECRET}</p>
    <p>Refresh Token: {DROPBOX_REFRESH_TOKEN}</p>
    <p><a href="/get_dropbox_token">Click here to get new refresh token</a></p>
    """

@app.route('/debug_dropbox')
def debug_dropbox():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        auth_flow = DropboxOAuth2FlowNoRedirect(
            consumer_key=DROPBOX_APP_KEY,
            consumer_secret=DROPBOX_APP_SECRET,
            token_access_type='offline'
        )

        authorize_url = auth_flow.start()
        return f"""
        <h1>Dropbox Debug Info</h1>
        <h2>Current Settings:</h2>
        <pre>
        App Key: {DROPBOX_APP_KEY}
        App Secret: {DROPBOX_APP_SECRET}
        Current Refresh Token: {DROPBOX_REFRESH_TOKEN}
        </pre>

        <h2>Get New Token:</h2>
        <ol>
            <li><a href="https://www.dropbox.com/developers/apps" target="_blank">Click here to open Dropbox App Console</a></li>
            <li>Find your app and click on it</li>
            <li>Under "OAuth 2", look for your app key and secret</li>
            <li>Verify they match the values above</li>
            <li>Then <a href="{authorize_url}" target="_blank">click here to authorize the app</a></li>
            <li>Enter the code you get here:
                <form action="/finish_auth">
                    <input type="text" name="code" size="50">
                    <input type="submit" value="Submit">
                </form>
            </li>
        </ol>
        """
    except Exception as e:
        logger.error(f"Debug Dropbox error: {str(e)}")
        return f"Error: {str(e)}"

@app.route('/get_dropbox_token')
def get_dropbox_token():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        auth_flow = DropboxOAuth2FlowNoRedirect(
            consumer_key=DROPBOX_APP_KEY,
            consumer_secret=DROPBOX_APP_SECRET,
            token_access_type='offline'
        )

        authorize_url = auth_flow.start()
        return f"""
        <h2>Dropbox Authorization Process:</h2>
        <ol>
            <li>First, verify these credentials match your Dropbox App settings:
                <ul>
                    <li>App Key: {DROPBOX_APP_KEY}</li>
                    <li>App Secret: {DROPBOX_APP_SECRET}</li>
                </ul>
            </li>
            <li>Then click this link: <a href="{authorize_url}" target="_blank">Authorize App</a></li>
            <li>After allowing access, you'll get a code</li>
            <li>Enter that code here:
                <form action="/finish_auth">
                    <input type="text" name="code" size="50">
                    <input type="submit" value="Submit">
                </form>
            </li>
        </ol>
        """
    except Exception as e:
        logger.error(f"Get Dropbox token error: {str(e)}")
        return f"Error starting auth flow: {str(e)}"

@app.route('/finish_auth')
def finish_auth():
    if not session.get('logged_in'):
        flash('Please log in first!')
        return redirect(url_for('admin'))

    try:
        auth_code = request.args.get('code')
        if not auth_code:
            return 'Error: No authorization code provided'

        auth_flow = DropboxOAuth2FlowNoRedirect(
            consumer_key=DROPBOX_APP_KEY,
            consumer_secret=DROPBOX_APP_SECRET,
            token_access_type='offline'
        )

        oauth_result = auth_flow.finish(auth_code)
        logger.info("Dropbox authentication completed successfully")
        return f"""
        <h2>Success!</h2>
        <p>Here's your new refresh token:</p>
        <pre>{oauth_result.refresh_token}</pre>
        <p>Update your app.py DROPBOX_REFRESH_TOKEN with this value.</p>
        <p>After updating, restart your Flask app.</p>
        """
    except Exception as e:
        logger.error(f"Finish auth error: {str(e)}")
        return f'Error finishing auth: {str(e)}'

@app.route('/get_firefighter_logs/<fireman_number>')
def get_firefighter_logs(fireman_number):
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authorized'}), 401

    if fireman_number in user_data:
        logs = []
        for log in user_data[fireman_number]['logs']:
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

                if 'manual_added_hours' in log:
                    hours = f"{log['manual_added_hours']:.2f}"
                else:
                    duration = (time_out - time_in).total_seconds() / 3600
                    hours = f"{duration:.2f}"

            logs.append({
                'type': log['type'],
                'time_in': time_in.strftime('%Y-%m-%d %H:%M:%S'),
                'time_out': time_out_display,
                'hours': hours
            })

        return jsonify({
            'logs': logs,
            'name': user_data[fireman_number]['full_name']
        })
    return jsonify({'error': 'Firefighter not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)