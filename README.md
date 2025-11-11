# 🚒 Fire Department Management System

A comprehensive web-based time tracking and management system designed specifically for volunteer fire departments. Built with Flask and SQLite, this system helps fire departments track volunteer hours, manage equipment inventory, schedule vehicle inspections, and monitor station operations.

**Live Demo:** [Spring Valley VFD](https://michealhelps.pythonanywhere.com/)

[![License](https://img.shields.io/badge/License-Non--Commercial-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/)

## ✨ Features

### Time Tracking & Activity Management
- ⏱️ **Kiosk Mode Clock In/Out**: iPad-friendly touch interface for firefighters to check in/out
- 📋 **Activity Tracking**: Track firefighting calls, training, work nights, meetings, and custom activities
- 👥 **Real-Time Dashboard**: Live display showing active firefighters and recent activity
- 📊 **Comprehensive Reports**: Hours by firefighter, activity breakdown, date ranges, and exportable Excel reports
- ⚠️ **Smart Alerts**: Automatic alerts for overdue vehicle inspections and low inventory levels

### Equipment & Inventory Management
- 📦 **Inventory System**: Track station and vehicle inventory with quantities, costs, and categories
- 🔍 **Vehicle Inspections**: Schedule and track weekly vehicle inspections with detailed checklists
- 🛢️ **Fluid Specifications**: Document required fluids (oil, coolant, brake fluid, etc.) for each vehicle
- 🔧 **Maintenance Tracking**: Monitor vehicle maintenance needs with failed inspection alerts
- 📱 **QR Code Access**: Generate QR codes for mobile access to inspections and inventory
- 💰 **Value Reporting**: Track total inventory value by location
- ⚠️ **Failed Inspection Alerts**: Automatic alerts on dashboard, display, and maintenance pages for vehicles needing attention

### Administration & Reporting
- 🔐 **Admin Panel**: Comprehensive management interface for all system features
- 📈 **Dashboard Analytics**: Visual charts and statistics for department operations
- 📤 **Excel Export**: Export any report to formatted Excel spreadsheets
- 🔔 **Alert Dashboard**: Centralized view of all system alerts and warnings
- 📺 **Digital Signage**: Display mode perfect for TV displays in the station

### Modern Features
- 📱 **Mobile Responsive**: Works great on phones, tablets, and desktop
- 🎨 **Modern UI**: Clean, intuitive interface with smooth animations
- ⚡ **Real-Time Updates**: Auto-refreshing displays keep information current
- 🔄 **Automatic Backups**: Hourly backups to Dropbox for data safety

## 📸 Screenshots

### Kiosk Mode
Touch-friendly iPad interface for firefighters to check in and out

### Display Dashboard
Real-time display with active firefighters, alerts, and leaderboards - perfect for station TVs

### Admin Panel
Comprehensive management interface with firefighter management, reports, and system controls

### Inventory Management
Track equipment across stations and vehicles with cost tracking

### Vehicle Inspections
Mobile-friendly inspection checklists with inline fluid specifications - shows exactly what oil, coolant, and brake fluid each vehicle requires

### Failed Inspection Alerts
Prominent alerts throughout the system when vehicles fail inspection, with maintenance tracking integration

*More screenshots available in the `/docs/screenshots` folder*

## 🛠️ Technology Stack

- **Backend**: Flask 2.0+ (Python)
- **Database**: SQLite with optimized queries
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Charts**: Chart.js for dashboard analytics
- **QR Codes**: qrcodejs for mobile access
- **Excel Export**: openpyxl for formatted reports
- **Backup**: Dropbox API for automatic backups
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

## 📄 License

This project is licensed under a **Non-Commercial License with Attribution Requirement**.

**Key Points:**
- ✅ Free to use for fire departments and non-profits
- ✅ Can modify and adapt for your needs
- ✅ Must keep SignPresenter.com references
- ❌ Cannot sell or use commercially
- ❌ Cannot remove attribution

See [LICENSE](LICENSE) file for full details.

For commercial licensing inquiries, contact: mike@signpresenter.com

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Guidelines
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Test your changes thoroughly
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## 💡 Support & Questions

- **Issues**: [GitHub Issues](https://github.com/mbyrdLCS/Fire-Department-Management-System/issues)
- **Email**: mike@signpresenter.com
- **Live Demo**: [Spring Valley VFD](https://michealhelps.pythonanywhere.com/)

## 🙏 Acknowledgments

- Built for volunteer fire departments who serve their communities
- Powered by [SignPresenter](https://www.signpresenter.com/) for digital signage displays
- Thanks to all contributors and fire departments using this system

## 📈 Recent Updates

### January 2025
- ✅ **Vehicle Fluid Specifications**: Track required oil, coolant, brake fluid, power steering fluid, and transmission fluid for each vehicle
- ✅ **Inline Fluid Display**: During inspections, fluid requirements automatically appear next to relevant checklist items
- ✅ **Failed Inspection System**: Comprehensive alerts across dashboard, display board, and maintenance pages
- ✅ **Auto-Generated Vehicle Codes**: Smart vehicle code generation from vehicle name and type
- ✅ **Station-Based Inspection Filtering**: Filter inspections by station with "All Stations" option
- ✅ **Enhanced Maintenance Alerts**: Failed inspections now prominently highlighted at top of maintenance menu

## 📈 Roadmap

- [ ] Mobile app for iOS/Android
- [ ] Advanced scheduling system
- [ ] Training record management
- [ ] Grant reporting features
- [ ] Multi-department support
- [ ] API for third-party integrations
- [ ] Work order system for maintenance tracking

---

**Made with ❤️ for volunteer firefighters**
