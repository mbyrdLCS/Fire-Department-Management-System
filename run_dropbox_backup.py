#!/usr/bin/env python3
"""
Standalone script to run Dropbox backup
Designed to be run as a PythonAnywhere scheduled task
"""

import sys
import os
from datetime import datetime

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

# Import db_helpers
import db_helpers

def main():
    """Run Dropbox backup"""
    print(f"\n{'='*60}")
    print(f"Dropbox Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Check if Dropbox backups are enabled
    try:
        interval = float(db_helpers.get_setting('dropbox_backup_interval_hours', '1'))
        if interval == 0:
            print("❌ Dropbox automatic backups are DISABLED (interval set to 0)")
            print("   Enable them in Backup Management settings")
            return

        print(f"✓ Dropbox backups enabled (interval: {interval} hours)")
    except Exception as e:
        print(f"⚠️  Warning: Could not check backup interval: {e}")

    # Create local backup first
    print("\n1️⃣  Creating local backup...")
    result = db_helpers.create_database_backup()

    if not result['success']:
        print(f"❌ Local backup failed: {result.get('error')}")
        sys.exit(1)

    print(f"✓ Local backup created: {result['backup_filename']}")
    print(f"   Path: {result['backup_path']}")
    print(f"   Size: {result.get('size_kb', 0):.1f} KB")

    # Upload to Dropbox
    print("\n2️⃣  Uploading to Dropbox...")
    dropbox_result = db_helpers.upload_backup_to_dropbox(result['backup_path'])

    if not dropbox_result['success']:
        print(f"❌ Dropbox upload failed: {dropbox_result.get('error')}")
        sys.exit(1)

    print(f"✓ Successfully uploaded to Dropbox")
    print(f"   Dropbox path: {dropbox_result['dropbox_path']}")

    # Cleanup old Dropbox backups
    print("\n3️⃣  Cleaning up old Dropbox backups...")
    try:
        keep_count = int(db_helpers.get_setting('max_dropbox_backups', '20'))
        cleanup_result = db_helpers.cleanup_old_dropbox_backups(keep_count)

        if cleanup_result['success']:
            if cleanup_result['deleted_count'] > 0:
                print(f"✓ Deleted {cleanup_result['deleted_count']} old backup(s), kept {keep_count} most recent")
            else:
                print(f"✓ No cleanup needed ({cleanup_result.get('message', 'All backups retained')})")
        else:
            print(f"⚠️  Cleanup warning: {cleanup_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"⚠️  Cleanup error: {e}")

    print(f"\n{'='*60}")
    print("✅ Dropbox backup completed successfully!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Backup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
