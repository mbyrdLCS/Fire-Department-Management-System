#!/usr/bin/env python3
"""
Automated Database Backup Script
Creates timestamped backups of the fire department database
Run this regularly to maintain backup history
"""

import os
import sys
import shutil
from datetime import datetime
import sqlite3

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from db_init import DATABASE_PATH

def backup_database():
    """Create a timestamped backup of the database"""

    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database not found at {DATABASE_PATH}")
        return False

    # Create backups directory
    backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'fire_dept_backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        # Get database stats
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

        conn.close()

        # Copy the database file
        print(f"📦 Creating backup...")
        print(f"   Source: {DATABASE_PATH}")
        print(f"   Destination: {backup_path}")
        print(f"   Size: {db_size_kb:.1f} KB")
        print()

        shutil.copy2(DATABASE_PATH, backup_path)

        # Verify the backup
        if os.path.exists(backup_path):
            backup_size = os.path.getsize(backup_path)
            if backup_size == db_size:
                print("✅ Backup created successfully!")
                print()
                print(f"📊 Database Contents:")
                print(f"   - {firefighter_count} firefighters")
                print(f"   - {log_count} time logs")
                print(f"   - {total_hours:.2f} total hours")
                print()
                print(f"💾 Backup saved to:")
                print(f"   {backup_path}")
                return True
            else:
                print("❌ Error: Backup file size doesn't match!")
                os.remove(backup_path)
                return False
        else:
            print("❌ Error: Backup file not created!")
            return False

    except Exception as e:
        print(f"❌ Error during backup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def list_backups():
    """List all existing backups"""
    backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')

    if not os.path.exists(backup_dir):
        print("No backups directory found.")
        return

    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]

    if not backups:
        print("No backups found.")
        return

    backups.sort(reverse=True)  # Newest first

    print(f"\n📁 Available Backups ({len(backups)}):")
    print("-" * 80)

    for backup in backups:
        backup_path = os.path.join(backup_dir, backup)
        size = os.path.getsize(backup_path) / 1024  # KB
        mtime = os.path.getmtime(backup_path)
        date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"   {backup:<45} {size:>8.1f} KB    {date}")

    print("-" * 80)
    print()

def cleanup_old_backups(keep_count=10):
    """Keep only the N most recent backups"""
    backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')

    if not os.path.exists(backup_dir):
        return

    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    backups.sort(reverse=True)  # Newest first

    if len(backups) <= keep_count:
        print(f"✅ Only {len(backups)} backup(s) exist. No cleanup needed.")
        return

    backups_to_delete = backups[keep_count:]

    print(f"🧹 Cleaning up old backups (keeping {keep_count} most recent)...")
    print(f"   Deleting {len(backups_to_delete)} old backup(s)...")

    for backup in backups_to_delete:
        backup_path = os.path.join(backup_dir, backup)
        try:
            os.remove(backup_path)
            print(f"   ✓ Deleted: {backup}")
        except Exception as e:
            print(f"   ✗ Failed to delete {backup}: {str(e)}")

    print(f"✅ Cleanup complete. {keep_count} backup(s) retained.")

if __name__ == '__main__':
    print("=" * 80)
    print("Fire Department Management System - Database Backup")
    print("=" * 80)
    print()

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'list':
            list_backups()
            sys.exit(0)
        elif command == 'cleanup':
            keep = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            list_backups()
            cleanup_old_backups(keep)
            sys.exit(0)
        elif command == 'help':
            print("Usage:")
            print("  python3 backup_database.py          - Create a new backup")
            print("  python3 backup_database.py list     - List all backups")
            print("  python3 backup_database.py cleanup [N] - Keep only N most recent backups (default: 10)")
            print()
            sys.exit(0)

    # Create backup
    success = backup_database()

    print()
    print("=" * 80)
    print("💡 Tips:")
    print("   - Run this script regularly (daily or weekly)")
    print("   - Keep backups in multiple locations (local + cloud)")
    print("   - Test your backups occasionally by restoring them")
    print("   - Use 'python3 backup_database.py list' to see all backups")
    print("   - Use 'python3 backup_database.py cleanup' to remove old backups")
    print("=" * 80)

    sys.exit(0 if success else 1)
