# Setup Dropbox Config on PythonAnywhere

## The Issue

You pulled the code to PythonAnywhere BEFORE we moved credentials to the config file.
This means:
- ✅ Old version still works (credentials hardcoded in backup_to_dropbox.py)
- ⚠️  Next time you `git pull`, it will break (new version needs dropbox_config.py)

## Fix It Now

Run these commands in a PythonAnywhere Bash console:

```bash
# Go to your project
cd ~/Fire-Department-Management-System

# Create the config file
cat > dropbox_config.py << 'EOF'
"""
Dropbox Configuration
KEEP THIS FILE SECRET - It contains your Dropbox API credentials
This file is excluded from git via .gitignore
"""

# Dropbox API credentials from your existing app
DROPBOX_APP_KEY = '0hpcgffvcu5vuei'
DROPBOX_APP_SECRET = '6kwngadn7oh3yrl'
DROPBOX_REFRESH_TOKEN = 'K98vLaIfGvMAAAAAAAAAAWHechPq9eCkRrYkWoOSjzZ3m7-ixpWNgiXspj0Vopvh'
DROPBOX_FOLDER = '/Fire_Dept_Backups'
KEEP_LOCAL_BACKUPS = 5
EOF

# Test it works
python3 backup_to_dropbox.py

# Now pull the latest code (this will update backup_to_dropbox.py)
git pull

# Test again with the new version
python3 backup_to_dropbox.py
```

## What This Does

1. Creates `dropbox_config.py` on PythonAnywhere (before pulling new code)
2. Tests backup works with current version
3. Pulls the new secure version
4. Tests backup works with new version
5. Your scheduled task will continue working perfectly

## After This

- ✅ PythonAnywhere will have secure config file
- ✅ Scheduled task will work with new code
- ✅ Credentials won't be in git anymore
- ✅ Future deploys will work automatically
