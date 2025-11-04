#!/usr/bin/env python3
"""
Automated Backup to Dropbox
Creates a database backup and uploads it to Dropbox automatically
Perfect for PythonAnywhere scheduled tasks
"""

import os
import sys
import shutil
from datetime import datetime

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

try:
    import dropbox
    from dropbox.exceptions import AuthError, ApiError
except ImportError:
    print("❌ Error: Dropbox SDK not installed")
    print("   Install with: pip install dropbox")
    sys.exit(1)

from db_init import DATABASE_PATH

# Import Dropbox credentials from config file (not tracked in git)
try:
    from dropbox_config import (
        DROPBOX_APP_KEY,
        DROPBOX_APP_SECRET,
        DROPBOX_REFRESH_TOKEN,
        DROPBOX_FOLDER,
        KEEP_LOCAL_BACKUPS
    )
except ImportError:
    print("❌ Error: dropbox_config.py not found")
    print("   Create dropbox_config.py with your Dropbox credentials")
    print("   See dropbox_config.py.example for template")
    sys.exit(1)

def get_dropbox_client():
    """Get Dropbox client using refresh token (never expires)"""
    try:
        dbx = dropbox.Dropbox(
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET
        )
        # Verify it works
        dbx.users_get_current_account()
        return dbx
    except AuthError as e:
        print("❌ Error: Dropbox authentication failed")
        print(f"   {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error connecting to Dropbox: {str(e)}")
        return None

def create_backup():
    """Create a timestamped backup of the database"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database not found at {DATABASE_PATH}")
        return None

    # Create local backups directory
    backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'fire_dept_backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)

    # Copy the database
    try:
        shutil.copy2(DATABASE_PATH, backup_path)

        if os.path.exists(backup_path):
            size_kb = os.path.getsize(backup_path) / 1024
            print(f"✅ Backup created: {backup_filename} ({size_kb:.1f} KB)")
            return backup_path, backup_filename
        else:
            print("❌ Error: Backup file not created")
            return None
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return None

def upload_to_dropbox(backup_path, backup_filename):
    """Upload backup file to Dropbox"""
    try:
        # Get Dropbox client
        dbx = get_dropbox_client()
        if not dbx:
            return False

        # Create folder if it doesn't exist
        try:
            dbx.files_get_metadata(DROPBOX_FOLDER)
        except ApiError:
            # Folder doesn't exist, create it
            dbx.files_create_folder_v2(DROPBOX_FOLDER)
            print(f"📁 Created folder: {DROPBOX_FOLDER}")

        # Upload file
        dropbox_path = f"{DROPBOX_FOLDER}/{backup_filename}"

        with open(backup_path, 'rb') as f:
            print(f"☁️  Uploading to Dropbox: {dropbox_path}")
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

        print(f"✅ Uploaded to Dropbox successfully!")
        return True

    except Exception as e:
        print(f"❌ Error uploading to Dropbox: {str(e)}")
        return False

def cleanup_old_backups():
    """Remove old local backups, keeping only the most recent N"""
    backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')

    if not os.path.exists(backup_dir):
        return

    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]

    if len(backups) <= KEEP_LOCAL_BACKUPS:
        return

    # Sort by name (timestamp is in filename)
    backups.sort(reverse=True)

    # Delete old backups
    backups_to_delete = backups[KEEP_LOCAL_BACKUPS:]

    for backup in backups_to_delete:
        try:
            os.remove(os.path.join(backup_dir, backup))
            print(f"🧹 Removed old backup: {backup}")
        except Exception as e:
            print(f"⚠️  Could not delete {backup}: {str(e)}")

def list_dropbox_backups():
    """List all backups currently in Dropbox"""
    try:
        dbx = get_dropbox_client()
        if not dbx:
            return

        result = dbx.files_list_folder(DROPBOX_FOLDER)

        if not result.entries:
            print("No backups found in Dropbox")
            return

        print(f"\n☁️  Dropbox Backups ({len(result.entries)}):")
        print("-" * 80)

        # Sort by name (which includes timestamp)
        entries = sorted(result.entries, key=lambda x: x.name, reverse=True)

        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                size_kb = entry.size / 1024
                modified = entry.client_modified.strftime('%Y-%m-%d %H:%M:%S')
                print(f"   {entry.name:<45} {size_kb:>8.1f} KB    {modified}")

        print("-" * 80)

    except Exception as e:
        print(f"❌ Error listing Dropbox backups: {str(e)}")

def main():
    print("=" * 80)
    print("Fire Department Database - Automated Dropbox Backup")
    print("=" * 80)
    print()

    # Check for list command
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_dropbox_backups()
        sys.exit(0)

    # Create backup
    print("📦 Creating backup...")
    result = create_backup()

    if not result:
        sys.exit(1)

    backup_path, backup_filename = result

    # Upload to Dropbox
    print()
    success = upload_to_dropbox(backup_path, backup_filename)

    if not success:
        sys.exit(1)

    # Cleanup old local backups
    print()
    cleanup_old_backups()

    print()
    print("=" * 80)
    print("✅ Backup Complete!")
    print(f"   Local: {backup_path}")
    print(f"   Dropbox: {DROPBOX_FOLDER}/{backup_filename}")
    print()
    print("💡 Tip: Set up a PythonAnywhere scheduled task to run this daily:")
    print(f"   Command: cd ~/Fire-Department-Management-System && python3 backup_to_dropbox.py")
    print("=" * 80)

if __name__ == '__main__':
    main()
