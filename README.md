# Fire Department Management System

A web-based time tracking and management system for fire departments, built with Flask.

## Features

- **Clock In/Out System**: Firefighters can clock in and out for various activities
- **Activity Tracking**: Track different types of activities (Firefighting, Training, Work Night, Board Meeting, EMR Meeting, or custom)
- **Admin Panel**: Manage firefighters, view hours, and generate reports
- **Automatic Checkout**: Prevents stuck sessions by auto-checking out after 12 hours
- **Display Dashboard**: Real-time view of active firefighters and leaderboard
- **Data Export**: Export time logs to CSV for reporting
- **Automatic Backups**: Hourly backups to Dropbox

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Data Storage**: JSON files
- **Backup**: Dropbox API
- **Timezone**: America/Chicago (Central Time)

## Installation

### Prerequisites

- Python 3.7+
- pip
- Virtual environment (recommended)

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Fire-Department-Management-System
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
cd flask_app
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp ../.env.example ../.env
# Edit .env with your actual credentials
```

5. Create initial data files:
```bash
cp ../user_data.json.example user_data.json
cp ../categories.json.example categories.json
cp ../vehicles.json.example vehicles.json
cp ../vehicle_inspections.json.example vehicle_inspections.json
```

6. Run the application:
```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Configuration

### Environment Variables

See `.env.example` for required environment variables:

- `FLASK_SECRET_KEY`: Secret key for Flask sessions
- `ADMIN_USERNAME`: Admin login username
- `ADMIN_PASSWORD`: Admin login password
- `DROPBOX_APP_KEY`: Dropbox API app key (for backups)
- `DROPBOX_APP_SECRET`: Dropbox API secret
- `DROPBOX_REFRESH_TOKEN`: Dropbox refresh token

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Usage

### For Firefighters

1. Visit the home page
2. Enter your firefighter number
3. Select activity type
4. Click "Clock In" when starting
5. Click "Clock Out" when finished

### For Admins

1. Visit `/admin`
2. Login with admin credentials
3. Access admin panel to:
   - View all firefighter hours
   - Add/edit/delete firefighters
   - Manually add hours
   - Export data to CSV
   - Manage activity categories

### Display Board

Visit `/display` for a real-time dashboard showing:
- Currently active firefighters
- Active alerts and warnings
- Vehicles needing inspection
- Recent activity feed
- Hours leaderboard

#### 📺 Display on TV with SignPresenter

Want to show the live dashboard on a TV in your fire station? Use **[SignPresenter](https://www.signpresenter.com/)** to display real-time updates on any Fire TV, Android device, or smart TV!

**Benefits:**
- 🚒 **Real-time updates**: Auto-refreshes every 30 seconds
- 📱 **Easy setup**: Works on Fire Stick, Android TV, or any Android device
- ⚡ **Always on**: Perfect for station wall-mounted displays
- 💰 **Affordable**: Only $10/month per device

**Setup Instructions:**
1. Visit [SignPresenter.com](https://www.signpresenter.com/) and sign up
2. Install SignPresenter on your Fire TV/Android device
3. Follow the [setup guide](https://support.signpresenter.com/topics/showwebsite.html) to add a website
4. Enter your display URL: `https://your-site.pythonanywhere.com/display`
5. Your live dashboard will now show on the TV!

This service helps keep our system running and supports continued development. Thank you!

## Project Structure

```
Fire-Department-Management-System/
├── flask_app/
│   ├── app.py                 # Main application
│   ├── backup_manager.py      # Dropbox backup handler
│   ├── requirements.txt       # Python dependencies
│   ├── templates/             # HTML templates
│   │   ├── index.html
│   │   ├── admin.html
│   │   ├── admin_login.html
│   │   ├── display.html
│   │   └── inspect.html
│   └── static/
│       └── style.css
├── .env                       # Environment variables (not in git)
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Deployment

### PythonAnywhere

1. Upload code to PythonAnywhere
2. Set up virtual environment
3. Configure WSGI file to point to `flask_app/app.py`
4. Set environment variables in WSGI file or bash console
5. Reload web app

## Security Notes

- Never commit `.env` file to Git
- Never commit actual data files (`user_data.json`, etc.)
- Change default admin credentials immediately
- Use strong passwords
- Keep Dropbox credentials secure

## Backup

The system automatically backs up to Dropbox every hour. Backups include:
- User data
- Categories
- Vehicle information

To manually trigger a backup, visit `/test_backup` while logged in as admin.

## Development

### Local Development

1. Use a separate `.env` file for development
2. Test with example data files
3. Never work directly on production server

### Adding Features

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make changes
3. Test thoroughly
4. Commit and push
5. Deploy to development server first

## Troubleshooting

### Auto-checkout not working
- Check logs in `firefighter.log`
- Verify background threads are running

### Dropbox backup failing
- Verify credentials in `.env`
- Check `backup.log` for errors
- Visit `/debug_dropbox` while logged in as admin

### Data corruption
- System automatically tries to recover from backups
- Check local backup files with `_backup_` in filename

## License

[Add your license here]

## Support

For issues or questions, contact [your contact info]
