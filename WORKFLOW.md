# Development Workflow Guide

Quick reference for working on the Fire Department Management System.

## 🔗 Important Links

- **GitHub Repository**: https://github.com/mbyrdLCS/Fire-Department-Management-System
- **Live Site**: https://michealhelps.pythonanywhere.com
- **PythonAnywhere Username**: michealhelps

## 📁 Project Structure

```
Fire-Department-Management-System/
├── flask_app/              # Main application code
│   ├── app.py             # Flask application
│   ├── db_helpers.py      # Database functions
│   ├── db_init.py         # Database initialization
│   ├── templates/         # HTML templates
│   ├── static/            # CSS, JS, images
│   └── database/          # SQLite database (fire_dept.db)
├── README.md              # Project overview
├── DEPLOYMENT.md          # Deployment instructions
├── DATABASE_SCHEMA.md     # Database documentation
└── requirements.txt       # Python dependencies
```

## 🚀 Standard Development Workflow

### 1. Make Changes Locally

```bash
# Navigate to project
cd /Users/MJB/Fire-Department-Management-System

# Make your changes to files
# Test locally if needed
cd flask_app
source ../venv/bin/activate
python app.py
# Visit: http://localhost:5001
```

### 2. Commit and Push to GitHub

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Description of what you changed"

# Push to GitHub
git push origin main
```

### 3. Deploy to PythonAnywhere

**Open PythonAnywhere bash console and run:**

```bash
# Navigate to project
cd ~/Fire-Department-Management-System

# Pull latest changes from GitHub
git pull origin main

# If you changed Python dependencies:
workon fdms-env
pip install -r requirements.txt

# If you changed database schema:
cd ~/Fire-Department-Management-System/flask_app
python db_init.py  # Only for NEW databases
# OR run migration scripts if needed
```

**Then reload the web app:**
- Go to: https://www.pythonanywhere.com/user/michealhelps/
- Click **Web** tab
- Click green **Reload** button
- Test: https://michealhelps.pythonanywhere.com

## 🔧 Common Tasks

### Update Database Schema
```bash
# PythonAnywhere console
cd ~/Fire-Department-Management-System/flask_app
workon fdms-env
python db_init.py  # For fresh database
```

### Add Default Categories
```bash
# PythonAnywhere console
cd ~/Fire-Department-Management-System/flask_app
workon fdms-env
python add_default_categories.py
```

### Check Error Logs
```bash
# PythonAnywhere console
tail -50 /var/log/michealhelps.pythonanywhere.com.error.log
```

### View Database
```bash
# PythonAnywhere console
cd ~/Fire-Department-Management-System/flask_app/database
sqlite3 fire_dept.db
.tables
.schema table_name
.quit
```

### Create Git Commit with Claude Code
When Claude Code makes changes:
```bash
git add .
git commit -m "Descriptive message of changes"
git push origin main
```

## 📝 Key Files to Remember

- **Main App**: `flask_app/app.py`
- **Database Functions**: `flask_app/db_helpers.py`
- **Database Schema**: `flask_app/db_init.py`
- **Templates**: `flask_app/templates/*.html`
- **Config**: `.env` (contains passwords - NEVER commit!)
- **WSGI Config**: On PythonAnywhere at `/var/www/michealhelps_pythonanywhere_com_wsgi.py`

## ⚙️ Environment Variables

Located in `.env` file (NOT in git):
```
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key_here
```

## 🐛 Troubleshooting

### Site Not Loading
1. Check error logs: `tail -50 /var/log/michealhelps.pythonanywhere.com.error.log`
2. Check if web app reloaded: Go to Web tab, click Reload
3. Check if database exists: `ls -la ~/Fire-Department-Management-System/flask_app/database/`

### Changes Not Showing
1. Did you push to GitHub? `git status`
2. Did you pull on PythonAnywhere? `git pull origin main`
3. Did you reload the web app? Go to Web tab → Reload

### Database Issues
1. Check database path in logs
2. Verify database file exists: `~/Fire-Department-Management-System/flask_app/database/fire_dept.db`
3. Check permissions: `ls -la ~/Fire-Department-Management-System/flask_app/database/`

## 💡 Quick Tips

- ✅ Always test locally before deploying (if possible)
- ✅ Commit often with clear messages
- ✅ Check error logs if something breaks
- ✅ Keep `.env` file secure and never commit it
- ✅ Document major changes in commit messages
- ❌ Never force push to main (`git push --force`)
- ❌ Never commit passwords or API keys

## 📦 When Starting a New Session

1. Open project folder: `cd /Users/MJB/Fire-Department-Management-System`
2. Check what changed: `git status`
3. Pull any changes from GitHub: `git pull origin main`
4. Start making changes!

## 🔄 Full Deployment Checklist

- [ ] Make changes locally
- [ ] Test locally (optional)
- [ ] `git add .`
- [ ] `git commit -m "Message"`
- [ ] `git push origin main`
- [ ] SSH/Console to PythonAnywhere
- [ ] `cd ~/Fire-Department-Management-System`
- [ ] `git pull origin main`
- [ ] Go to Web tab
- [ ] Click Reload button
- [ ] Test site: https://michealhelps.pythonanywhere.com
- [ ] Check for errors in logs if needed

## 📞 Support Resources

- **GitHub Issues**: https://github.com/mbyrdLCS/Fire-Department-Management-System/issues
- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/

## 🎯 Project Goals

Fire Department Management System for tracking:
- ✅ Firefighter clock in/out
- ✅ Activity tracking (Work night, Training, Board Meeting, EMR Meeting, Other)
- ✅ Vehicle inspections (6-day intervals)
- ✅ Maintenance work orders
- ✅ Inventory management (station & vehicle)
- ✅ Reports and analytics
- ✅ Dashboard and display board for TV

---

**Remember**: GitHub → PythonAnywhere → Reload → Test!
