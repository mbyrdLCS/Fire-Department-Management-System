#!/usr/bin/env python3
"""
Check backup configuration and status
Helps diagnose why automatic backups aren't working
"""

import sys
import os
from datetime import datetime

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

import db_helpers

print(f"\n{'='*60}")
print("BACKUP SYSTEM DIAGNOSTIC")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")

# Check settings
print("📋 BACKUP SETTINGS:")
print("-" * 60)

local_interval = db_helpers.get_setting('local_backup_interval_hours', '1')
dropbox_interval = db_helpers.get_setting('dropbox_backup_interval_hours', '1')
max_local = db_helpers.get_setting('max_local_backups', '10')
max_dropbox = db_helpers.get_setting('max_dropbox_backups', '20')

print(f"Local Backup Interval:    {local_interval} hours")
print(f"Dropbox Backup Interval:  {dropbox_interval} hours")
print(f"Max Local Backups:        {max_local}")
print(f"Max Dropbox Backups:      {max_dropbox}")

local_enabled = float(local_interval) > 0
dropbox_enabled = float(dropbox_interval) > 0

print(f"\nLocal Backups:   {'✓ ENABLED' if local_enabled else '✗ DISABLED'}")
print(f"Dropbox Backups: {'✓ ENABLED' if dropbox_enabled else '✗ DISABLED'}")

# Check Dropbox credentials
print(f"\n☁️  DROPBOX CREDENTIALS:")
print("-" * 60)

app_key = bool(os.getenv('DROPBOX_APP_KEY'))
app_secret = bool(os.getenv('DROPBOX_APP_SECRET'))
refresh_token = bool(os.getenv('DROPBOX_REFRESH_TOKEN'))

print(f"DROPBOX_APP_KEY:       {'✓ Set' if app_key else '✗ Missing'}")
print(f"DROPBOX_APP_SECRET:    {'✓ Set' if app_secret else '✗ Missing'}")
print(f"DROPBOX_REFRESH_TOKEN: {'✓ Set' if refresh_token else '✗ Missing'}")

all_creds = app_key and app_secret and refresh_token
print(f"\nDropbox Configured: {'✓ YES' if all_creds else '✗ NO - Missing credentials'}")

# Test Dropbox connection
if all_creds:
    print("\n🔌 TESTING DROPBOX CONNECTION:")
    print("-" * 60)
    dbx = db_helpers.get_dropbox_client()
    if dbx:
        try:
            account = dbx.users_get_current_account()
            print(f"✓ Successfully connected to Dropbox")
            print(f"  Account: {account.email}")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
    else:
        print("✗ Could not create Dropbox client")

# Check local backups
print(f"\n💾 LOCAL BACKUP STATUS:")
print("-" * 60)

local_status = db_helpers.get_backup_status()
if local_status.get('healthy'):
    print(f"✓ Status: HEALTHY")
else:
    print(f"⚠️  Status: NEEDS ATTENTION")

print(f"Total Backups: {local_status.get('total_backups', 0)}")
if local_status.get('last_backup'):
    lb = local_status['last_backup']
    print(f"Last Backup:   {lb['date'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"               ({local_status.get('hours_since_last', 0):.1f} hours ago)")
else:
    print(f"Last Backup:   None found")

if local_status.get('warning'):
    print(f"\n⚠️  {local_status['warning']}")

# Check Dropbox backups
if all_creds:
    print(f"\n☁️  DROPBOX BACKUP STATUS:")
    print("-" * 60)

    dropbox_status = db_helpers.get_dropbox_backup_status()

    if not dropbox_status.get('configured'):
        print("✗ Dropbox not configured")
    elif dropbox_status.get('healthy'):
        print(f"✓ Status: HEALTHY")
        print(f"Total Backups: {dropbox_status.get('total_backups', 0)}")
        if dropbox_status.get('last_backup'):
            lb = dropbox_status['last_backup']
            print(f"Last Backup:   {lb['date'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"               ({dropbox_status.get('hours_since_last', 0):.1f} hours ago)")
    else:
        print(f"⚠️  Status: NEEDS ATTENTION")
        print(f"Total Backups: {dropbox_status.get('total_backups', 0)}")
        if dropbox_status.get('last_backup'):
            lb = dropbox_status['last_backup']
            print(f"Last Backup:   {lb['date'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"               ({dropbox_status.get('hours_since_last', 0):.1f} hours ago)")
        else:
            print(f"Last Backup:   None found")

        if dropbox_status.get('warning'):
            print(f"\n⚠️  {dropbox_status['warning']}")
        if dropbox_status.get('error'):
            print(f"❌ Error: {dropbox_status['error']}")

# Recommendations
print(f"\n💡 RECOMMENDATIONS:")
print("-" * 60)

if not all_creds:
    print("1. Configure Dropbox credentials in .env file")
    print("   - DROPBOX_APP_KEY")
    print("   - DROPBOX_APP_SECRET")
    print("   - DROPBOX_REFRESH_TOKEN")

if not dropbox_enabled:
    print("2. Enable Dropbox automatic backups:")
    print("   - Go to Backup Management in the web app")
    print("   - Set Dropbox interval to 1 hour (or your preference)")
    print("   - Click Save Settings")

if all_creds and dropbox_enabled:
    print("3. Set up PythonAnywhere scheduled task:")
    print("   - Go to PythonAnywhere Tasks tab")
    print("   - Create hourly task:")
    print("     cd ~/Fire-Department-Management-System && /usr/bin/python3 run_dropbox_backup.py")
    print("   - See PYTHONANYWHERE_BACKUP_SETUP.md for details")

print(f"\n{'='*60}\n")
