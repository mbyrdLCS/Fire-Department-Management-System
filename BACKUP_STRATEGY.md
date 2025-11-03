# Fire Department Management System - Backup Strategy

## Overview

Your system has two important components that need backing up:

1. **CODE** → Backed up to GitHub ✅
2. **DATABASE** → Needs regular backups (this guide)

---

## Quick Start - Create a Backup Now

```bash
python3 backup_database.py
```

This creates a timestamped backup in `flask_app/database/backups/`

---

## Recommended Backup Strategy

### The 3-2-1 Rule

**3** copies of your data
**2** different storage types
**1** copy offsite

### For Your Fire Department System:

**Copy 1:** Production database on PythonAnywhere
**Copy 2:** Local backups on your Mac
**Copy 3:** Cloud backup (Google Drive, Dropbox, or iCloud)

---

## Backup Methods

### Method 1: Manual Backups (Simple)

**On your Mac (weekly):**
```bash
cd ~/Fire-Department-Management-System
python3 backup_database.py
```

**On PythonAnywhere (weekly):**
```bash
cd ~/Fire-Department-Management-System
python3 backup_database.py
```

Then download the backup:
- Go to Files → `flask_app/database/backups/`
- Click the backup file to download
- Save to your Mac

**Pros:** Simple, full control
**Cons:** Must remember to do it

---

### Method 2: Automated PythonAnywhere Backups

PythonAnywhere has two backup options:

#### Option A: Scheduled Task (Free Accounts)

1. Go to **Tasks** tab in PythonAnywhere
2. Click "Create a new scheduled task"
3. Command:
   ```bash
   cd ~/Fire-Department-Management-System && /home/michealhelps/.virtualenvs/fdms-env/bin/python backup_database.py
   ```
4. Schedule: Daily at 2:00 AM (or your preferred time)

**Pros:** Fully automated, runs daily
**Cons:** Need to download manually, free accounts get 1 task

#### Option B: PythonAnywhere's Built-in Backup (Paid Feature)

If you upgrade to a paid account, PythonAnywhere automatically backs up your files daily.

---

### Method 3: Cloud Sync (Recommended)

Store backups in the cloud automatically:

#### Using Google Drive (or Dropbox, iCloud):

**On your Mac:**

1. Create a folder in Google Drive: "Fire Dept Backups"

2. Create a simple sync script:

```bash
# Add this to backup_and_sync.sh
cd ~/Fire-Department-Management-System
python3 backup_database.py
cp flask_app/database/backups/*.db ~/Google\ Drive/Fire\ Dept\ Backups/
```

3. Run weekly or use macOS Calendar to remind you

**Pros:** Offsite backup, accessible from anywhere
**Cons:** Manual sync unless you set up automation

---

## Backup Commands Cheat Sheet

```bash
# Create a new backup
python3 backup_database.py

# List all backups
python3 backup_database.py list

# Keep only the 10 most recent backups (delete old ones)
python3 backup_database.py cleanup

# Keep only the 5 most recent backups
python3 backup_database.py cleanup 5
```

---

## How to Restore from Backup

### If something goes wrong:

**1. Stop the web app (on PythonAnywhere):**
   - Go to Web tab → Click "Disable" (if needed)

**2. Restore the backup:**
```bash
cd ~/Fire-Department-Management-System/flask_app/database
cp backups/fire_dept_backup_20251103_153851.db fire_dept.db
```

**3. Restart the web app:**
   - Go to Web tab → Click "Reload"

**4. Verify the data:**
   - Check admin panel to confirm firefighter hours are correct

---

## What Gets Backed Up

**Included in database backups:**
- ✅ All firefighters and their hours
- ✅ All time logs (check-ins/check-outs)
- ✅ Activity categories
- ✅ Vehicles and equipment
- ✅ Inspection records
- ✅ Maintenance records
- ✅ Inventory data

**Already safe in GitHub:**
- ✅ All Python code
- ✅ All HTML templates
- ✅ Database schema (structure)
- ✅ Configuration files

**Not backed up (and doesn't need to be):**
- Log files (*.log)
- Temporary files
- Virtual environment files

---

## Recommended Schedule

| When | Where | Action |
|------|-------|--------|
| **Daily** | PythonAnywhere | Automated backup (if you set up scheduled task) |
| **Weekly** | Your Mac | Run `backup_database.py` |
| **Weekly** | Cloud | Copy backup to Google Drive/Dropbox |
| **Monthly** | Test | Restore a backup to verify it works |

---

## Emergency Recovery Plan

If your PythonAnywhere database gets corrupted or deleted:

1. **Stay calm** - you have backups!

2. **Get your most recent backup:**
   - From PythonAnywhere backups folder, OR
   - From your Mac, OR
   - From cloud storage

3. **Upload to PythonAnywhere:**
   ```bash
   # In PythonAnywhere console
   cd ~/Fire-Department-Management-System/flask_app/database
   # Upload file via Files tab
   mv uploaded_backup.db fire_dept.db
   ```

4. **Reload web app**

5. **Verify data in admin panel**

---

## Best Practices

✅ **DO:**
- Back up before making major changes
- Test your backups occasionally
- Keep at least 10 recent backups
- Store one copy offsite (cloud)
- Document when you make backups

❌ **DON'T:**
- Delete all backups at once
- Store backups only in one place
- Wait until after disaster to test restore
- Commit database files to git
- Share backup files publicly (contains user data)

---

## Monitoring Backup Health

**Weekly checklist:**
- [ ] Backup created this week?
- [ ] Backup file size looks normal (~350 KB)?
- [ ] Cloud copy exists?
- [ ] Can access PythonAnywhere backups?

**Monthly checklist:**
- [ ] Test restore a backup
- [ ] Clean up old backups (keep 10 most recent)
- [ ] Verify backup file integrity

---

## File Locations

| Item | Location |
|------|----------|
| **Production database** | PythonAnywhere: `~/Fire-Department-Management-System/flask_app/database/fire_dept.db` |
| **Production backups** | PythonAnywhere: `~/Fire-Department-Management-System/flask_app/database/backups/` |
| **Local database** | Mac: `/Users/MJB/Fire-Department-Management-System/flask_app/database/fire_dept.db` |
| **Local backups** | Mac: `/Users/MJB/Fire-Department-Management-System/flask_app/database/backups/` |
| **Backup script** | Both: `backup_database.py` |

---

## Questions?

**Q: How often should I back up?**
A: Daily automated + weekly manual download to your Mac

**Q: How long should I keep backups?**
A: Keep at least 10 recent backups (covers ~2-3 months if weekly)

**Q: What if I forget to back up?**
A: Set up the automated PythonAnywhere scheduled task

**Q: How do I know if a backup is good?**
A: File size should be ~350 KB and contain 619+ logs

**Q: Should I back up my Mac database too?**
A: Yes! Your Mac is the "master" copy, definitely back it up

---

## Summary

**Minimum protection (Basic):**
- Run `python3 backup_database.py` weekly
- Keep backups on your Mac

**Good protection (Recommended):**
- Set up PythonAnywhere scheduled task (daily)
- Download backup to Mac weekly
- Copy to Google Drive weekly

**Excellent protection (Best):**
- Automated daily backups on PythonAnywhere
- Weekly download to Mac
- Weekly cloud sync
- Monthly restore tests

**Remember:** The database is your most valuable asset - it contains all your firefighters' hours and records. Code can be recovered from GitHub, but data cannot be recreated if lost!
