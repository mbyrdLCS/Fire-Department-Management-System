# Simple Dropbox Backup Setup (Using Your Existing Credentials)

Your Dropbox is already configured! The script uses your existing credentials.

---

## Quick Setup on PythonAnywhere (5 minutes)

**Step 1: Install Dropbox SDK**

```bash
cd ~/Fire-Department-Management-System
git pull
source ~/.virtualenvs/fdms-env/bin/activate
pip install dropbox
```

**Step 2: Test it works**

```bash
python3 backup_to_dropbox.py
```

You should see:
```
✅ Backup created: fire_dept_backup_20251103_163008.db (348.0 KB)
✅ Uploaded to Dropbox successfully!
```

**Step 3: Set up daily automatic backup**

1. Go to **Tasks** tab on PythonAnywhere
2. Click **"Create a new scheduled task"**
3. Enter this command:
   ```
   cd /home/michealhelps/Fire-Department-Management-System && /home/michealhelps/.virtualenvs/fdms-env/bin/python backup_to_dropbox.py
   ```
4. Set time: **03:00** (3 AM daily)
5. Click **Create**

**Done!** Your database will now backup to Dropbox automatically every day at 3 AM.

---

## Check Your Backups

**In Dropbox:**
- Open your Dropbox (web or app)
- Look for folder: **Fire_Dept_Backups**
- You'll see files like: fire_dept_backup_20251103_163008.db

**List from command line:**
```bash
python3 backup_to_dropbox.py list
```

**Manual backup anytime:**
```bash
python3 backup_to_dropbox.py
```

---

## What It Does

- ✅ Creates timestamped backup
- ✅ Uploads to Dropbox automatically
- ✅ Keeps 5 most recent local backups
- ✅ Never expires (uses refresh token, not access token)
- ✅ Works with your existing Dropbox app

---

## Storage

- Dropbox Free: 2 GB
- Each backup: ~350 KB
- Can store **5,700+ backups** (15+ years of daily backups)

---

That's it! Super simple because you already had Dropbox configured from your old app. The script just reuses those same credentials.
