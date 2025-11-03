# Automated Dropbox Backup Setup Guide

This guide will help you set up automatic daily backups to Dropbox. Once configured, your database will be backed up to Dropbox every day automatically - no manual work required!

---

## What You'll Get

- ✅ **Automatic daily backups** to Dropbox (offsite storage)
- ✅ **Free** - Dropbox free tier gives you 2GB (plenty for database backups)
- ✅ **No manual work** - runs automatically on PythonAnywhere
- ✅ **Peace of mind** - your data is safe even if PythonAnywhere has issues

---

## Step-by-Step Setup

### Step 1: Create Dropbox App (5 minutes)

1. **Go to Dropbox Developers:**
   Visit: https://www.dropbox.com/developers/apps

2. **Click "Create app"**

3. **Choose options:**
   - API: **Scoped access**
   - Access type: **Full Dropbox**
   - Name: **Fire Dept Backup** (or whatever you want)
   - Click **Create app**

4. **Set Permissions:**
   - Click the **Permissions** tab
   - Check these boxes:
     - ☑️ files.content.write
     - ☑️ files.content.read
   - Click **Submit** at the bottom

5. **Generate Access Token:**
   - Click the **Settings** tab
   - Scroll down to "OAuth 2"
   - Under "Generated access token", click **Generate**
   - Copy the token (it's a long string like: sl.B1234567890...)
   - **IMPORTANT:** Save this somewhere safe - you can't see it again!

---

### Step 2: Install on PythonAnywhere (5 minutes)

**Open a Bash console on PythonAnywhere and run:**

```bash
# Go to your project
cd ~/Fire-Department-Management-System

# Pull the latest code
git pull

# Activate your virtual environment
source ~/.virtualenvs/fdms-env/bin/activate

# Install Dropbox SDK
pip install dropbox

# Save your Dropbox token (replace YOUR_TOKEN with the token you copied)
echo 'YOUR_TOKEN_HERE' > .dropbox_token
chmod 600 .dropbox_token
```

**IMPORTANT:** Replace `YOUR_TOKEN_HERE` with the actual token you copied from Dropbox!

---

### Step 3: Test the Backup (2 minutes)

Still in the Bash console:

```bash
python3 backup_to_dropbox.py
```

You should see:
```
✅ Backup created: fire_dept_backup_20251103_154530.db (348.0 KB)
☁️  Uploading to Dropbox: /Fire_Dept_Backups/fire_dept_backup_20251103_154530.db
✅ Uploaded to Dropbox successfully!
```

**Check Dropbox:**
- Go to your Dropbox (web or app)
- Look for a folder called "Fire_Dept_Backups"
- You should see your backup file!

---

### Step 4: Set Up Daily Automatic Backup (3 minutes)

**On PythonAnywhere:**

1. **Go to the Tasks tab** (in the top menu)

2. **Create a new scheduled task:**
   - Click **"Create a new scheduled task"**

3. **Configure the task:**
   - **Description:** Daily Fire Dept Database Backup
   - **Command:**
     ```
     cd /home/michealhelps/Fire-Department-Management-System && /home/michealhelps/.virtualenvs/fdms-env/bin/python backup_to_dropbox.py
     ```
   - **Hour:** 03 (3 AM)
   - **Minute:** 00

4. **Click "Create"**

**That's it!** Your database will now backup to Dropbox automatically every day at 3 AM.

---

## Usage Commands

**Create a backup manually:**
```bash
cd ~/Fire-Department-Management-System
python3 backup_to_dropbox.py
```

**List all backups in Dropbox:**
```bash
python3 backup_to_dropbox.py list
```

**View local backups:**
```bash
python3 backup_database.py list
```

---

## What Happens Automatically

Every day at 3 AM:
1. ✅ Creates a timestamped backup of your database
2. ✅ Uploads it to Dropbox folder "Fire_Dept_Backups"
3. ✅ Keeps the 5 most recent local backups (deletes older ones)
4. ✅ Logs any errors

---

## Monitoring Your Backups

**Check if it's working:**

1. **Look at scheduled task history:**
   - Go to Tasks tab on PythonAnywhere
   - Check the log for your task
   - Should show "✅ Backup Complete!"

2. **Check Dropbox:**
   - Go to Fire_Dept_Backups folder
   - Should have a new backup each day
   - Filenames include dates: fire_dept_backup_20251103_030000.db

3. **Run the list command:**
   ```bash
   python3 backup_to_dropbox.py list
   ```

---

## Storage Management

**Dropbox Free Tier:**
- 2 GB storage (free)
- Each backup is ~350 KB
- Can store about **5,700 backups** before running out of space
- At 1 backup per day = **15+ years** of backups!

**Auto-cleanup:**
- Local backups: Keeps only 5 most recent
- Dropbox backups: Keeps all (you have plenty of space)

**If you want to delete old Dropbox backups:**
- Just go to Dropbox and delete files manually
- Or keep them all (they're tiny files)

---

## How to Restore from Dropbox Backup

If you need to restore:

1. **Download backup from Dropbox:**
   - Go to Fire_Dept_Backups folder
   - Pick the backup you want (usually most recent)
   - Download it to your computer

2. **Upload to PythonAnywhere:**
   ```bash
   cd ~/Fire-Department-Management-System/flask_app/database
   # Upload the file using Files tab
   mv fire_dept.db fire_dept.db.old_backup
   mv downloaded_backup.db fire_dept.db
   ```

3. **Reload your web app**

---

## Troubleshooting

**"Invalid Dropbox token":**
- Your token expired or was regenerated
- Go back to Dropbox developers and generate a new token
- Update the file: `echo 'NEW_TOKEN' > .dropbox_token`

**"Scheduled task failed":**
- Check the task log on PythonAnywhere
- Make sure the full path is correct
- Test manually: `python3 backup_to_dropbox.py`

**"Not uploading to Dropbox":**
- Check your internet connection
- Verify token: `cat .dropbox_token`
- Make sure Dropbox app has correct permissions

**"Out of space":**
- Unlikely (15+ years of daily backups fit in 2GB)
- If it happens, delete old backups from Dropbox
- Or upgrade to Dropbox Plus (2TB for $11.99/month)

---

## Security Notes

**Your Dropbox token:**
- ✅ Stored in `.dropbox_token` (excluded from git)
- ✅ Only readable by you (chmod 600)
- ❌ Never commit to GitHub
- ❌ Never share publicly

**Backup files contain:**
- All firefighter data and hours
- All inventory and equipment
- All inspection and maintenance records
- Keep them secure!

---

## Alternative: Google Drive

If you prefer Google Drive instead of Dropbox, I can create a similar setup. Let me know!

**Google Drive advantages:**
- 15 GB free (vs 2GB Dropbox)
- May already have Google account

**Dropbox advantages:**
- Simpler API
- Easier token management
- No OAuth flow required

---

## Summary

Once set up:
- **No manual work required**
- **Runs every day at 3 AM**
- **Keeps 5 local backups**
- **Keeps all backups in Dropbox**
- **Free for 15+ years of daily backups**

**You're protected against:**
- ✅ Accidental deletion
- ✅ Database corruption
- ✅ PythonAnywhere server issues
- ✅ Hard drive failures
- ✅ Human error

---

## Questions?

**Q: Can I change the backup time?**
A: Yes! Edit the scheduled task on PythonAnywhere

**Q: How do I know if it's working?**
A: Check the Tasks tab log, or look at your Dropbox folder

**Q: Can I backup to multiple places?**
A: Yes! Set up multiple scheduled tasks (Dropbox + local + Google Drive)

**Q: What if I run out of Dropbox space?**
A: Delete old backups, or upgrade to paid plan. But you won't run out for years!

**Q: Can I access backups from my phone?**
A: Yes! Install Dropbox app on your phone and you can see all backups

---

Need help? Just ask!
