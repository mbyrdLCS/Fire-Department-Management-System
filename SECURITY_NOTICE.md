# Security Notice - Dropbox Credentials

## What Happened

Your Dropbox API credentials were accidentally committed to GitHub in the file `backup_to_dropbox.py`. This means they were publicly visible.

## What I Fixed

✅ Moved credentials to `dropbox_config.py` (now excluded from git)
✅ Updated `backup_to_dropbox.py` to import from config file
✅ Added `dropbox_config.py` to `.gitignore`
✅ Created `dropbox_config.py.example` as a template

## What You Should Do

### Option 1: Rotate Your Credentials (Recommended)

Since the credentials were public, it's safest to generate new ones:

1. Go to https://www.dropbox.com/developers/apps
2. Find your app: "Fire Department Backup" (or whatever you named it)
3. Click on it
4. Under "OAuth 2", click **"Generate new refresh token"**
5. Copy the new refresh token
6. Update `/Users/MJB/Fire-Department-Management-System/dropbox_config.py` with the new token
7. On PythonAnywhere, also update `~/Fire-Department-Management-System/dropbox_config.py`

### Option 2: Keep Current Credentials (If Low Risk)

If your GitHub repo is private and you trust that no one accessed the credentials, you can keep using them. The credentials are now secure going forward.

## Current Status

- ✅ Local credentials are secure in `dropbox_config.py`
- ✅ Future commits will NOT include credentials
- ⚠️  Old commits in GitHub still contain the credentials (removing requires force push)
- ✅ Backup script tested and working with new config system

## For PythonAnywhere

When you pull the latest code on PythonAnywhere, you'll need to create the config file there too:

```bash
cd ~/Fire-Department-Management-System
git pull
cp dropbox_config.py.example dropbox_config.py
nano dropbox_config.py  # Edit and paste your credentials
```

The scheduled task will continue to work automatically.

## Repository Privacy

Your repository appears to be at: https://github.com/mbyrdLCS/Fire-Department-Management-System

- If it's **private**: Lower risk, only you and authorized collaborators could see it
- If it's **public**: Higher risk, rotate credentials recommended

You can check by visiting that URL while logged out of GitHub.
