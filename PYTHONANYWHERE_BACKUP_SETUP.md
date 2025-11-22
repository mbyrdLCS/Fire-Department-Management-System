# PythonAnywhere Automatic Backup Setup

The in-app automatic backup scheduler doesn't work reliably on PythonAnywhere due to worker process restarts. Instead, use PythonAnywhere's **Scheduled Tasks** feature.

## Setup Instructions

### 1. Access Scheduled Tasks
1. Log into your PythonAnywhere dashboard
2. Go to the **Tasks** tab
3. You'll see a section for scheduled tasks

### 2. Add Dropbox Backup Task (Hourly)

Create a new scheduled task with these settings:

**Time**: `Every hour at :05` (or choose your preferred time)
**Command**:
```bash
cd ~/Fire-Department-Management-System && /usr/bin/python3 run_dropbox_backup.py >> ~/dropbox_backup.log 2>&1
```

This will:
- Run every hour at 5 minutes past (e.g., 1:05, 2:05, 3:05, etc.)
- Create a local backup
- Upload to Dropbox
- Clean up old Dropbox backups based on your settings
- Log output to `~/dropbox_backup.log`

### 3. Add Local Backup Task (Optional - Hourly)

If you also want separate local backups (in addition to Dropbox), add another task:

**Time**: `Every hour at :00`
**Command**:
```bash
cd ~/Fire-Department-Management-System && /usr/bin/python3 run_local_backup.py >> ~/local_backup.log 2>&1
```

### 4. Verify It's Working

After the scheduled time passes, check the logs:

```bash
# View Dropbox backup log
cat ~/dropbox_backup.log

# View local backup log (if configured)
cat ~/local_backup.log
```

You should see output like:
```
============================================================
Dropbox Backup - 2025-11-22 14:05:00
============================================================

✓ Dropbox backups enabled (interval: 1 hours)

1️⃣  Creating local backup...
✓ Local backup created: fire_dept_backup_20251122_140500.db
   Path: /home/username/Fire-Department-Management-System/flask_app/database/backups/fire_dept_backup_20251122_140500.db
   Size: 2456.3 KB

2️⃣  Uploading to Dropbox...
✓ Successfully uploaded to Dropbox
   Dropbox path: /fire_dept_backup_20251122_140500.db

3️⃣  Cleaning up old Dropbox backups...
✓ Deleted 3 old backup(s), kept 20 most recent

============================================================
✅ Dropbox backup completed successfully!
============================================================
```

### 5. Disable In-App Scheduler (Optional)

Since you're now using PythonAnywhere scheduled tasks, you can disable the in-app automatic backups:

1. Go to **Backup Management** in your app
2. Under **Backup Settings**
3. Set **Dropbox Automatic Interval** to `Disabled`
4. Click **Save Settings**

This prevents the in-app scheduler from interfering (though it doesn't work reliably anyway on PythonAnywhere).

## Changing Backup Frequency

To change how often backups run:

1. Go to PythonAnywhere **Tasks** tab
2. Edit the scheduled task
3. Change the time/frequency
4. Common options:
   - `Every hour at :05` - Hourly backups
   - `Every 4 hours at :05` - Every 4 hours
   - `Daily at 02:00` - Once per day at 2 AM

## Troubleshooting

### Check if task is enabled
- Go to **Tasks** tab on PythonAnywhere
- Make sure the task shows as **enabled** (not crossed out)

### Check recent runs
- PythonAnywhere shows the last run time next to each task
- If it says "Never run", wait for the scheduled time to pass

### View error logs
```bash
# Check for any errors
tail -50 ~/dropbox_backup.log
```

### Test manually
You can test the backup script manually:
```bash
cd ~/Fire-Department-Management-System
python3 run_dropbox_backup.py
```

### Common issues
- **"Dropbox backups are DISABLED"**: Go to Backup Management settings and enable Dropbox backups
- **"Dropbox upload failed"**: Check your Dropbox credentials in `.env` file
- **Script not found**: Make sure you ran `git pull` to get the latest code

## Files Created

- `run_dropbox_backup.py` - Standalone Dropbox backup script
- `run_local_backup.py` - Standalone local backup script
- `~/dropbox_backup.log` - Dropbox backup log file
- `~/local_backup.log` - Local backup log file (if configured)
