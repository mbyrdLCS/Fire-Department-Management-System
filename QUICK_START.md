# 🚀 Quick Start Guide

The absolute minimum steps to get the Fire Department Management System running.

## For PythonAnywhere (Recommended - FREE!)

### 1. Create Account
Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com/) - free tier works great!

### 2. Clone Repository
```bash
git clone https://github.com/mbyrdLCS/Fire-Department-Management-System.git
cd Fire-Department-Management-System
```

### 3. Create Virtual Environment
```bash
mkvirtualenv fdms-env --python=python3.10
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
nano .env
```

Add these variables:
```bash
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=False

ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# Optional demo mode
DEMO_MODE=false
DEPARTMENT_NAME=Your Fire Department Name

# Optional Dropbox backups (leave blank if not using)
DROPBOX_APP_KEY=
DROPBOX_APP_SECRET=
DROPBOX_REFRESH_TOKEN=
```

Generate secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Initialize Database (ONE COMMAND!)
```bash
cd ~/Fire-Department-Management-System/flask_app
python3 db_init.py
```

This creates **all 18 database tables** including:
- ✅ Time tracking & activity logs
- ✅ Multi-user authentication
- ✅ Vehicle inspections & maintenance
- ✅ Inventory management
- ✅ ISO hose testing & compliance
- ✅ Stations & equipment tracking

### 6. Create First Admin User
```bash
cd ~/Fire-Department-Management-System
python3 add_users_table.py
```

**That's it for database setup!** No need to run any other migration scripts.

### 7. Configure Web App
In PythonAnywhere dashboard:
1. Go to **Web** tab
2. Click "Add a new web app"
3. Choose "Manual configuration" → Python 3.10
4. Set virtualenv: `/home/YOUR_USERNAME/.virtualenvs/fdms-env`
5. Edit WSGI file (see README for full WSGI configuration)
6. Click **Reload**

### 8. Visit Your Site!
Go to: `https://YOUR_USERNAME.pythonanywhere.com`

---

## For Local Development

### 1. Clone Repository
```bash
git clone https://github.com/mbyrdLCS/Fire-Department-Management-System.git
cd Fire-Department-Management-System
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
cd flask_app
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
cp ../.env.example ../.env
# Edit .env with your settings
```

### 5. Initialize Database
```bash
python3 db_init.py
```

### 6. Create Admin User
```bash
cd ..
python3 add_users_table.py
```

### 7. Run the App
```bash
cd flask_app
python app.py
```

Visit: `http://localhost:5000`

---

## 🎯 Key Points

1. **Only TWO scripts needed**: `db_init.py` (creates all tables) + `add_users_table.py` (creates first user)
2. **No manual database setup**: Everything is automated
3. **No SQL commands needed**: Python scripts handle everything
4. **Safe to re-run**: Scripts use `CREATE TABLE IF NOT EXISTS`

## 🆘 Troubleshooting

**"No such table" error?**
- Run: `cd flask_app && python3 db_init.py`

**"ModuleNotFoundError"?**
- Check your WSGI file paths (see README)
- Make sure you're using the virtualenv

**Site shows error page?**
- Check error log (Web tab → error log link)
- Most common: forgot to run `db_init.py`

## 📚 Full Documentation

See [README.md](README.md) for complete documentation including:
- Feature overview
- Detailed deployment steps
- Dropbox backup setup
- Advanced configuration
- Development guidelines

---

**Made with ❤️ for volunteer firefighters**

**Live Demo:** [https://byrdmanlk.pythonanywhere.com](https://byrdmanlk.pythonanywhere.com) (Login: demo / demo2024)
