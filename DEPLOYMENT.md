# PythonAnywhere Deployment Guide

## Prerequisites
- PythonAnywhere account (free or paid)
- Git repository with your code (already done ✓)

## Step 1: Set Up PythonAnywhere Account

1. Log in to [PythonAnywhere](https://www.pythonanywhere.com/)
2. Go to the **Web** tab
3. Click **Add a new web app**
4. Choose **Manual configuration** (not Django)
5. Select **Python 3.10** (or latest available version)

## Step 2: Clone Your Repository

Open a **Bash console** from the PythonAnywhere dashboard and run:

```bash
cd ~
git clone https://github.com/mbyrdLCS/Fire-Department-Management-System.git
cd Fire-Department-Management-System
```

## Step 3: Set Up Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.10 fdms-env
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

Create your `.env` file:

```bash
cd ~/Fire-Department-Management-System
cp .env.example .env
nano .env
```

Update the following variables:
```
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key_here
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

## Step 5: Initialize Database

```bash
cd ~/Fire-Department-Management-System/flask_app
python init_database.py
```

This will create the SQLite database with all necessary tables.

## Step 6: Configure WSGI File

1. Go to the **Web** tab in PythonAnywhere
2. Click on your web app
3. Scroll to the **Code** section
4. Click on the WSGI configuration file link

Replace the contents with:

```python
import sys
import os

# Update this path with your PythonAnywhere username
project_home = '/home/YOUR_USERNAME/Fire-Department-Management-System'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# Import Flask app
from flask_app.app import app as application

# Ensure database directory exists
db_path = os.path.join(project_home, 'flask_app', 'database')
os.makedirs(db_path, exist_ok=True)
```

**Important:** Replace `YOUR_USERNAME` with your actual PythonAnywhere username.

## Step 7: Configure Virtual Environment Path

On the **Web** tab, in the **Virtualenv** section:

1. Click **Enter path to a virtualenv**
2. Enter: `/home/YOUR_USERNAME/.virtualenvs/fdms-env`
3. Replace `YOUR_USERNAME` with your actual username

## Step 8: Configure Static Files

In the **Static files** section, add:

| URL          | Directory                                                      |
|--------------|----------------------------------------------------------------|
| `/static`    | `/home/YOUR_USERNAME/Fire-Department-Management-System/flask_app/static` |

## Step 9: Set Working Directory

In the **Code** section:
- **Working directory**: `/home/YOUR_USERNAME/Fire-Department-Management-System/flask_app`

## Step 10: Reload Your Web App

1. Scroll to the top of the **Web** tab
2. Click the **Reload** button (big green button)
3. Wait for the reload to complete

## Step 11: Test Your Deployment

Visit your app at: `https://YOUR_USERNAME.pythonanywhere.com`

## Troubleshooting

### View Error Logs

Check error logs in PythonAnywhere:
1. Go to **Web** tab
2. Click on **Error log** link
3. Check **Server log** link as well

### Common Issues

**Issue: 502 Bad Gateway**
- Check that the WSGI file path is correct
- Verify virtual environment is activated
- Check error logs

**Issue: Static files not loading**
- Verify static files path in Web tab
- Check permissions on static directory
- Force reload with Ctrl+F5

**Issue: Database errors**
- Ensure `flask_app/database/` directory exists
- Check file permissions: `chmod 755 flask_app/database/`
- Re-run `init_database.py`

**Issue: Missing dependencies**
- Activate virtualenv: `workon fdms-env`
- Reinstall: `pip install -r requirements.txt`

## Updating Your App

When you make changes and push to GitHub:

```bash
# SSH into PythonAnywhere console
cd ~/Fire-Department-Management-System
git pull origin main

# Reload the web app from the Web tab
```

## Database Backups

Set up regular backups:

```bash
# Create backup directory
mkdir -p ~/backups

# Create backup script
cat > ~/backup_fdms.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/Fire-Department-Management-System/flask_app/database/fire_dept.db ~/backups/fire_dept_$DATE.db
# Keep only last 7 days
find ~/backups -name "fire_dept_*.db" -mtime +7 -delete
EOF

chmod +x ~/backup_fdms.sh
```

Add to crontab (daily at 2 AM):
```bash
crontab -e
```

Add line:
```
0 2 * * * /home/YOUR_USERNAME/backup_fdms.sh
```

## Security Notes

1. **Change default credentials** in `.env` file
2. **Keep `.env` file secure** - never commit to git
3. **Use HTTPS** - PythonAnywhere provides this automatically
4. **Regular backups** - set up the backup script above
5. **Monitor logs** regularly for suspicious activity

## Performance Tips

For free accounts:
- Database size limit: 512 MB
- Set up log rotation to prevent filling disk
- Monitor daily CPU seconds usage

For paid accounts:
- Consider upgrading database storage if needed
- Use MySQL instead of SQLite for better performance

## Support

- PythonAnywhere Forums: https://www.pythonanywhere.com/forums/
- PythonAnywhere Help: https://help.pythonanywhere.com/
- Your GitHub Issues: https://github.com/mbyrdLCS/Fire-Department-Management-System/issues
