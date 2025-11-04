# Deploy Display Board Updates

The display board has been improved with:
- ✅ Auto-rotating carousel (shows 6 firefighters at a time)
- ✅ Rotates every 8 seconds when more than 6 firefighters on duty
- ✅ Visual dots indicator showing current page
- ✅ QR codes for quick access (Kiosk and Inspections)
- ✅ Optimized for 16:9 TV screens

## Deploy to PythonAnywhere

Run these commands in PythonAnywhere Bash console:

```bash
cd ~/Fire-Department-Management-System
git pull
```

Then reload your web app:
1. Go to **Web** tab on PythonAnywhere
2. Click **Reload michealhelps.pythonanywhere.com**

## Test at Fire Station

Visit: https://michealhelps.pythonanywhere.com/display

Check that:
- Carousel rotates smoothly every 8 seconds
- QR codes scan correctly on mobile devices
- Everything fits on 16:9 TV screen
- No scrolling needed

## Files Changed
- `flask_app/templates/display.html` - Complete redesign
- `flask_app/app.py` - Added base_url for QR codes
