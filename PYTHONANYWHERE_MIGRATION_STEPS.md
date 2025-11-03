# PythonAnywhere Migration Steps

## Step 1: Open Bash Console
Go to: https://www.pythonanywhere.com/user/michealhelps/consoles/

## Step 2: Pull Latest Changes
```bash
cd ~/Fire-Department-Management-System
git pull origin main
```

## Step 3: Verify Migration Files
```bash
ls -l migrate_for_pythonanywhere.py
ls -l migration_data/
```

You should see:
- migrate_for_pythonanywhere.py
- migration_data/user_data.json
- migration_data/categories.json

## Step 4: Run Migration (DRY RUN FIRST)
```bash
# First run WITHOUT --confirm to see what will happen
python3 migrate_for_pythonanywhere.py
```

This will show you the warning message and what data will be affected.

## Step 5: Run Migration (FOR REAL)
```bash
# Now run with --confirm to execute migration
python3 migrate_for_pythonanywhere.py --confirm
```

The script will:
- ✓ Backup your current database automatically
- ✓ Clear existing firefighter and time log data
- ✓ Import 21 firefighters from old app
- ✓ Import 619 time logs with proper hours
- ✓ Keep all 10 vehicles and 222 checklist assignments intact
- ✓ Show verification summary

## Step 6: Reload Web App
After migration completes successfully:
1. Go to: https://www.pythonanywhere.com/user/michealhelps/webapps/
2. Click the green "Reload michealhelps.pythonanywhere.com" button

## Step 7: Verify Results
Visit your site: https://michealhelps.pythonanywhere.com

Check:
- Dashboard shows 21 firefighters with their actual hours
- Fleet still shows all 10 vehicles (R1, R2, G1, G4, G5, P2, P4, T2, T3, T6)
- Checklist assignments are still intact

## Troubleshooting

### If migration fails:
The script automatically restores from backup. Check the error message and:
1. Verify the database path is correct
2. Check file permissions
3. Ensure migration_data folder exists

### To restore manually:
```bash
cd ~/Fire-Department-Management-System/flask_app/database
# List backups
ls -l *.pre_migration_backup_*
# Restore from backup (replace timestamp with actual backup)
cp fire_dept.db.pre_migration_backup_YYYYMMDD_HHMMSS fire_dept.db
```

## Expected Results

```
📊 Migration Summary:
  Firefighters: 21
  Time Logs: 619
  Categories: 6
  Vehicles: 10 (preserved)

  Top 5 by Hours:
    #31 Davita Stellway: 220.93 hours
    #2 Ronnie Smith: 108.23 hours
    #24 Tanner webster: 88.08 hours
    #25 Christian Green: 83.77 hours
    #17 Chris Webster: 82.82 hours
```
