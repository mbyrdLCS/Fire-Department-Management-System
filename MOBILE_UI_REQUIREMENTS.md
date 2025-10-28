# Mobile-First UI Requirements

## Overview
The system must be **mobile-first** since most field operations (inspections, maintenance, inventory) will be performed on smartphones.

## Primary Mobile Users

### 1. **Mechanics/Technicians**
- Recording maintenance work
- Adding notes about repairs
- Taking photos of issues
- Logging parts used
- Recording costs
- Marking maintenance complete

### 2. **Firefighters Doing Inspections**
- Daily vehicle inspections with checklists
- Pass/fail marking
- Adding notes for failures
- Quick and easy to complete

### 3. **Personnel Managing Inventory**
- Adding/removing items from vehicles
- Updating quantities
- Moving items between vehicles/stations
- Checking off items during inventory audits
- Scanning barcodes/QR codes (future)

### 4. **Admins/Officers**
- View alerts dashboard
- Approve work orders
- Review reports
- Manage schedules

## Mobile UI Design Principles

### ✅ Touch-First Interface
- **Large touch targets** (minimum 44x44px)
- **Big buttons** for primary actions
- **Swipe gestures** where appropriate
- **Bottom navigation** (easier to reach with thumb)
- **Minimal typing** required

### ✅ Quick Actions
- **Pre-filled forms** with smart defaults
- **Quick add** buttons
- **Recent items** list
- **Search** with autocomplete
- **Voice input** for notes (HTML5 speech)

### ✅ Simplified Workflows
- **One task per screen**
- **Progressive disclosure** (show what's needed, hide complexity)
- **Clear next steps**
- **Easy back/cancel**

### ✅ Offline Capability
- **Service workers** for offline access
- **Local storage** for drafts
- **Sync when online**
- **Clear offline indicators**

### ✅ Camera Integration
- **Photo upload** for maintenance records
- **QR code scanning** for items (future)
- **Image compression** before upload

### ✅ Responsive Breakpoints
- **Mobile:** < 768px (phone)
- **Tablet:** 768px - 1024px
- **Desktop:** > 1024px

## Key Mobile Views

### 1. **Vehicle Inspection (Mobile)**
```
┌─────────────────────────┐
│  ← Engine 1 Inspection  │
├─────────────────────────┤
│ [Your Name] [Start]     │
├─────────────────────────┤
│ □ Check engine oil      │
│   ⭕ Pass  ⭕ Fail       │
├─────────────────────────┤
│ □ Check tire pressure   │
│   ⭕ Pass  ⭕ Fail       │
├─────────────────────────┤
│ □ Test horn and sirens  │
│   ⭕ Pass  ⭕ Fail       │
│   [Add Notes if Fail]   │
├─────────────────────────┤
│ ...more items...        │
├─────────────────────────┤
│   [Submit Inspection]   │
└─────────────────────────┘
```

### 2. **Maintenance Work Order (Mobile)**
```
┌─────────────────────────┐
│  ← New Work Order       │
├─────────────────────────┤
│ Vehicle: [Engine 1 ▼]   │
│ Type:    [Repair ▼]     │
│ Date:    [Today]        │
├─────────────────────────┤
│ What was done:          │
│ ┌─────────────────────┐ │
│ │ Replaced brake pads │ │
│ │ and rotors...       │ │
│ └─────────────────────┘ │
│ [🎤 Voice Input]        │
├─────────────────────────┤
│ Parts Used:             │
│ [+ Add Part]            │
├─────────────────────────┤
│ Cost: [$_____]          │
│ [📷 Add Photos]         │
├─────────────────────────┤
│   [Save Work Order]     │
└─────────────────────────┘
```

### 3. **Quick Inventory Update (Mobile)**
```
┌─────────────────────────┐
│  ← Update Inventory     │
├─────────────────────────┤
│ Location: [Engine 1 ▼]  │
│                         │
│ Search items...         │
│ ┌─────────────────────┐ │
│ │ 🔍 [________]       │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│ Recent Items:           │
│ ┌─────────────────────┐ │
│ │ SCBA Bottle         │ │
│ │ Qty: [3] [+][-]     │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │ 2.5" Fire Hose      │ │
│ │ Qty: [5] [+][-]     │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│   [Save Changes]        │
└─────────────────────────┘
```

### 4. **Alerts Dashboard (Mobile)**
```
┌─────────────────────────┐
│  🔔 Alerts (5)          │
├─────────────────────────┤
│ 🔴 CRITICAL (2)         │
│ ┌─────────────────────┐ │
│ │ SCBA Bottle #42     │ │
│ │ Expired 3 days ago  │ │
│ │ [View] [Mark Done]  │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│ ⚠️ WARNING (3)          │
│ ┌─────────────────────┐ │
│ │ Engine 1 Oil Change │ │
│ │ Due in 5 days       │ │
│ │ [View] [Schedule]   │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│ [View All Alerts]       │
└─────────────────────────┘
```

## Technical Implementation

### Frontend Framework
- **Pure HTML/CSS/JavaScript** (no heavy frameworks)
- **CSS Grid & Flexbox** for responsive layouts
- **CSS Media Queries** for breakpoints
- **Progressive Web App (PWA)** capabilities
- **Service Workers** for offline support

### Mobile Optimizations
```css
/* Mobile-first CSS approach */
.button {
  min-height: 44px;
  min-width: 44px;
  font-size: 16px; /* Prevent iOS zoom on input focus */
}

.form-input {
  font-size: 16px; /* Prevent zoom */
  padding: 12px;
}

/* Large radio buttons for pass/fail */
.radio-option {
  width: 100px;
  height: 60px;
  font-size: 18px;
}

/* Bottom sticky navigation */
.mobile-nav {
  position: fixed;
  bottom: 0;
  width: 100%;
  padding: 10px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
}
```

### Voice Input Example
```html
<!-- HTML5 Speech Recognition for notes -->
<textarea id="notes"></textarea>
<button onclick="startVoiceInput()">🎤 Voice Input</button>

<script>
function startVoiceInput() {
  const recognition = new webkitSpeechRecognition();
  recognition.onresult = (event) => {
    document.getElementById('notes').value += event.results[0][0].transcript;
  };
  recognition.start();
}
</script>
```

### Camera Integration
```html
<!-- Mobile camera access -->
<input type="file" accept="image/*" capture="camera" id="photo">
```

## User Experience Goals

### ⚡ Fast
- Page loads in < 2 seconds
- Actions respond instantly
- Minimal animations (keep it snappy)

### 👍 Easy
- Complete inspection in < 3 minutes
- Log maintenance in < 2 minutes
- Update inventory in < 30 seconds

### 📱 Accessible
- Works on iOS and Android
- Works on older phones (not just latest)
- Large text options
- High contrast mode

### 🔒 Reliable
- Saves work automatically
- Doesn't lose data on poor connection
- Clear error messages
- Offline mode

## Testing Devices

### Primary Test Devices
- iPhone (Safari)
- Android phone (Chrome)
- iPad (Safari)
- Desktop (Chrome/Firefox)

### Network Conditions
- Fast WiFi (in station)
- 4G/LTE (in field)
- Slow 3G (edge cases)
- Offline (draft mode)

## Progressive Enhancement

1. **Base Level:** Works on all phones with basic HTML forms
2. **Enhanced:** Touch gestures, camera, voice input
3. **Advanced:** Offline mode, push notifications, home screen install

## Mobile Navigation Structure

```
Bottom Nav Bar:
┌─────┬─────┬─────┬─────┬─────┐
│Home │Insp.│Maint│Inv. │More │
└─────┴─────┴─────┴─────┴─────┘

Home:
- Clock in/out
- Quick actions
- Today's alerts

Inspections:
- Start inspection
- View history

Maintenance:
- New work order
- View scheduled
- View history

Inventory:
- Quick update
- Search items
- Move items

More:
- Reports
- Settings
- Admin (if applicable)
- Logout
```

## Implementation Priority

1. **Phase 1:** Basic mobile layouts for existing features
2. **Phase 2:** Vehicle inspections (mobile-first)
3. **Phase 3:** Maintenance work orders (mobile-first)
4. **Phase 4:** Inventory management (mobile-first)
5. **Phase 5:** Offline capabilities
6. **Phase 6:** Camera & voice input
