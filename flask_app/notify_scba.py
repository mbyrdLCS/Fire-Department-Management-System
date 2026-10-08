#!/usr/bin/env python3
"""
Daily SCBA hydro test notification script.
Run by PythonAnywhere scheduler every morning.
Emails the SCBA contact if any bottles are overdue or within 90 days.
"""

import os
import sys
import smtplib
import sqlite3
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load .env manually (no flask dependency needed)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATHS = [
    os.path.join(BASE_DIR, '..', '.env'),
    '/home/michealhelps/Fire-Department-Management-System/.env',
]
for env_path in ENV_PATHS:
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())
        break

SMTP_FROM   = os.environ.get('SMTP_FROM_EMAIL', 'springvfd.alerts@gmail.com')
SMTP_PASS   = os.environ.get('SMTP_APP_PASSWORD', '')

def get_scba_contacts():
    """Read SCBA recipient emails (comma-separated) from the database settings table."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT setting_value FROM display_settings WHERE setting_key='scba_notify_email'")
        row = cursor.fetchone()
        val = row[0] if row and row[0] else os.environ.get('SCBA_NOTIFY_EMAIL', 'chrisgreen6695@gmail.com')
        return [e.strip() for e in val.split(',') if e.strip()]
    except Exception:
        return [os.environ.get('SCBA_NOTIFY_EMAIL', 'chrisgreen6695@gmail.com')]
    finally:
        conn.close()

DB_PATHS = [
    os.path.join(BASE_DIR, 'database', 'fire_dept.db'),
    '/home/michealhelps/Fire-Department-Management-System/flask_app/database/fire_dept.db',
]

def get_db():
    for p in DB_PATHS:
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            conn.row_factory = sqlite3.Row
            return conn
    raise FileNotFoundError("Could not find fire_dept.db")

def get_alerts():
    today = date.today()
    window = today + timedelta(days=90)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bottle_type, serial_number, dot_spec, manufacturer,
               hydro_date, next_hydro_due, location, station
        FROM scba_bottles
        WHERE status = 'active'
          AND next_hydro_due IS NOT NULL
          AND next_hydro_due <= ?
        ORDER BY next_hydro_due
    ''', (window.strftime('%Y-%m-%d'),))
    rows = cursor.fetchall()
    conn.close()

    overdue, warning = [], []
    for r in rows:
        due = datetime.strptime(r['next_hydro_due'], '%Y-%m-%d').date()
        days = (due - today).days
        entry = dict(r)
        entry['days_until'] = days
        if days < 0:
            overdue.append(entry)
        else:
            warning.append(entry)
    return overdue, warning


def get_oos_alerts():
    """Return composite bottles within 365 days of their out-of-service (retirement) date."""
    today = date.today()
    window = today + timedelta(days=365)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bottle_type, serial_number, dot_spec, manufacturer,
               mfgr_date, out_of_service_date, location, station
        FROM scba_bottles
        WHERE status = 'active'
          AND bottle_type = 'composite'
          AND out_of_service_date IS NOT NULL
          AND out_of_service_date <= ?
        ORDER BY out_of_service_date
    ''', (window.strftime('%Y-%m-%d'),))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        oos = datetime.strptime(r['out_of_service_date'], '%Y-%m-%d').date()
        days = (oos - today).days
        entry = dict(r)
        entry['days_until'] = days
        results.append(entry)
    return results

def build_email(overdue, warning, oos_warning=None):
    oos_warning = oos_warning or []
    today = date.today().strftime('%B %d, %Y')

    # ── Plain text ──────────────────────────────────────────────────────────
    lines = [
        f"SVVFD SCBA Air Bottle Report",
        f"Generated: {today}",
        f"",
    ]
    if overdue:
        lines.append("HYDRO TEST OVERDUE — Immediate Action Required:")
        for b in overdue:
            lines.append(f"  • {b['bottle_type'].capitalize()} #{b['serial_number']} "
                         f"| Location: {b['location']} "
                         f"| Due: {b['next_hydro_due']} ({abs(b['days_until'])} days overdue)")
        lines.append("")
    if warning:
        lines.append("Hydro Test Due Within 90 Days:")
        for b in warning:
            lines.append(f"  • {b['bottle_type'].capitalize()} #{b['serial_number']} "
                         f"| Location: {b['location']} "
                         f"| Due: {b['next_hydro_due']} ({b['days_until']} days)")
        lines.append("")
    if oos_warning:
        lines.append("Composite Bottle Retirement Within 1 Year (replace after 15 yrs from mfgr date):")
        for b in oos_warning:
            days_str = f"{abs(b['days_until'])} days PAST retirement" if b['days_until'] < 0 else f"{b['days_until']} days"
            lines.append(f"  • Composite #{b['serial_number']} | Location: {b['location']} "
                         f"| Retire: {b['out_of_service_date']} ({days_str})")
        lines.append("")
    lines += [
        "View full inventory: https://michealhelps.pythonanywhere.com/scba",
        "",
        "— SVVFD Alert System (springvfd.alerts@gmail.com)",
    ]
    plain = "\n".join(lines)

    # ── HTML ────────────────────────────────────────────────────────────────
    def hydro_rows(bottles, color, label):
        html = ""
        for b in bottles:
            days_str = (f"{abs(b['days_until'])} days overdue" if b['days_until'] < 0
                        else f"{b['days_until']} days remaining")
            html += f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">
                <strong>{b['bottle_type'].capitalize()}</strong><br>
                <span style="font-size:0.85em;color:#64748b;">#{b['serial_number']} &bull; {b['dot_spec']}</span>
              </td>
              <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">{b['location']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">{b['next_hydro_due']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">
                <span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:0.8em;font-weight:600;">{label}</span><br>
                <span style="font-size:0.8em;color:#64748b;">{days_str}</span>
              </td>
            </tr>"""
        return html

    def oos_rows(bottles):
        html = ""
        for b in bottles:
            days_str = (f"{abs(b['days_until'])} days PAST retirement" if b['days_until'] < 0
                        else f"{b['days_until']} days remaining")
            html += f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">
                <strong>Composite</strong><br>
                <span style="font-size:0.85em;color:#64748b;">#{b['serial_number']} &bull; {b['dot_spec']}</span>
              </td>
              <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">{b['location']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">{b['out_of_service_date']}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">
                <span style="background:#f59e0b;color:white;padding:2px 8px;border-radius:10px;font-size:0.8em;font-weight:600;">REPLACE SOON</span><br>
                <span style="font-size:0.8em;color:#64748b;">{days_str}</span>
              </td>
            </tr>"""
        return html

    sections = ""
    if overdue:
        sections += f"""
        <h2 style="color:#dc2626;margin:24px 0 8px;">Hydro Test Overdue — Immediate Action Required</h2>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border:1px solid #fca5a5;border-radius:8px;overflow:hidden;">
          <thead><tr style="background:#fee2e2;">
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#991b1b;">Bottle</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#991b1b;">Location</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#991b1b;">Due Date</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#991b1b;">Status</th>
          </tr></thead>
          <tbody>{hydro_rows(overdue, '#dc2626', 'OVERDUE')}</tbody>
        </table>"""

    if warning:
        sections += f"""
        <h2 style="color:#d97706;margin:24px 0 8px;">Hydro Test Due Within 90 Days</h2>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border:1px solid #fcd34d;border-radius:8px;overflow:hidden;">
          <thead><tr style="background:#fffbeb;">
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#92400e;">Bottle</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#92400e;">Location</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#92400e;">Due Date</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#92400e;">Status</th>
          </tr></thead>
          <tbody>{hydro_rows(warning, '#d97706', 'DUE SOON')}</tbody>
        </table>"""

    if oos_warning:
        sections += f"""
        <h2 style="color:#b45309;margin:24px 0 8px;">Composite Bottle Retirement Within 1 Year</h2>
        <p style="font-size:0.85em;color:#64748b;margin:0 0 8px;">Composite cylinders must be replaced 15 years from manufacturer date (DOT SP11194).</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border:1px solid #fde68a;border-radius:8px;overflow:hidden;">
          <thead><tr style="background:#fef3c7;">
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#92400e;">Bottle</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#92400e;">Location</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#92400e;">Retire Date</th>
            <th style="padding:10px 12px;text-align:left;font-size:0.8em;color:#92400e;">Status</th>
          </tr></thead>
          <tbody>{oos_rows(oos_warning)}</tbody>
        </table>"""

    html = f"""
    <!DOCTYPE html><html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
    <div style="max-width:680px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
      <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);padding:24px 28px;color:white;">
        <div style="font-size:1.3rem;font-weight:700;">SVVFD SCBA Hydro Test Alert</div>
        <div style="font-size:0.85rem;opacity:0.8;margin-top:4px;">Spring Valley Volunteer Fire Department &bull; {today}</div>
      </div>
      <div style="padding:24px 28px;">
        {sections}
        <div style="margin-top:28px;padding-top:20px;border-top:1px solid #e2e8f0;text-align:center;">
          <a href="https://michealhelps.pythonanywhere.com/scba"
             style="background:#2563eb;color:white;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
            View Full Bottle Inventory
          </a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:14px 28px;text-align:center;font-size:0.78rem;color:#94a3b8;">
        Sent by SVVFD Alert System &bull; springvfd.alerts@gmail.com
      </div>
    </div>
    </body></html>"""

    return plain, html

def send_email(to_addr, subject, plain, html):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f"SVVFD Alerts <{SMTP_FROM}>"
    msg['To']      = to_addr
    msg.attach(MIMEText(plain, 'plain'))
    msg.attach(MIMEText(html,  'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SMTP_FROM, SMTP_PASS)
        server.sendmail(SMTP_FROM, to_addr, msg.as_string())

def is_biweekly_day():
    """True on the 1st and 15th of each month — roughly every two weeks."""
    return date.today().day in (1, 15)

def main():
    today = date.today()
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] SCBA notification check...")
    overdue, warning = get_alerts()
    oos_warning = get_oos_alerts()
    recipients = get_scba_contacts()

    if not recipients:
        print("  No recipients configured. Skipping.")
        return

    def send_to_all(subject, plain, html):
        for addr in recipients:
            try:
                send_email(addr, subject, plain, html)
                print(f"  Sent to {addr}")
            except Exception as e:
                print(f"  ERROR sending to {addr}: {e}")

    # Always alert on overdue hydro bottles regardless of day
    if overdue:
        parts = [f"{len(overdue)} Bottle(s) OVERDUE for Hydro Test"]
        if oos_warning:
            parts.append(f"{len(oos_warning)} Composite Bottle(s) Due for Retirement")
        subject = "SVVFD SCBA — " + " | ".join(parts)
        plain, html = build_email(overdue, warning, oos_warning)
        send_to_all(subject, plain, html)
        return

    # Biweekly summary (1st and 15th) — send if anything is due within windows
    if is_biweekly_day():
        if warning or oos_warning:
            parts = []
            if warning:
                parts.append(f"{len(warning)} Hydro Test(s) Due Within 90 Days")
            if oos_warning:
                parts.append(f"{len(oos_warning)} Composite Bottle(s) Due for Retirement Within 1 Year")
            subject = "SVVFD SCBA — " + " | ".join(parts)
            plain, html = build_email(overdue, warning, oos_warning)
            send_to_all(subject, plain, html)
            print(f"  Biweekly summary sent ({len(warning)} hydro upcoming, {len(oos_warning)} retirement upcoming)")
        else:
            print("  Biweekly check — nothing due. No email sent.")
    else:
        print(f"  Not a biweekly day ({today.day}) and no overdue bottles. No email sent.")

if __name__ == '__main__':
    main()
