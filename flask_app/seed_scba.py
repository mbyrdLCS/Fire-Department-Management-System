#!/usr/bin/env python3
"""
Seed SCBA air bottle inventory from SVVFD Air Bottle List spreadsheet.
Run once: python3 seed_scba.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_init import get_db_connection, init_database
from datetime import datetime

def _next_hydro_from_last(hydro_str):
    if not hydro_str:
        return None
    cleaned = hydro_str.replace('\\', '/').strip()
    parts = cleaned.split('/')
    if len(parts) == 2:
        month, year = parts[0].zfill(2), parts[1]
        d = datetime.strptime(f"{year}-{month}-01", '%Y-%m-%d')
        return d.replace(year=d.year + 5).strftime('%Y-%m-%d')
    return None

def seed():
    # Ensure table exists
    init_database()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing seed data (safe to re-run)
    cursor.execute("DELETE FROM scba_bottles")
    print("Cleared existing SCBA records.")

    # ── COMPOSITE BOTTLES (Carleton, DOT SP11194, MFGR 06/2016) ──────────────
    composite = [
        # (serial, hydro_date, location, station, status)
        ('614561538', '10/2022', 'P3/STN2', 'STN2', 'active'),
        ('614561542', '10/2022', 'P3/STN2', 'STN2', 'active'),
        ('614561540', '10/2022', 'P2/STN1', 'STN1', 'active'),
        ('614561528', '10/2022', 'P2/STN1', 'STN1', 'active'),
        ('614561523', '10/2022', 'P2/STN1', 'STN1', 'active'),
        ('614561530',  None,     'STN1',    'STN1', 'out_of_service'),  # damaged – yellow
        ('614561535', '10/2022', 'P2/STN1', 'STN1', 'active'),
        ('614561533',  None,     'STN1',    'STN1', 'out_of_service'),  # damaged – yellow
        ('614561537', '06/2026', 'P2/STN1', 'STN1', 'active'),
        ('614561525', '10/2022', 'R1/STN1', 'STN1', 'active'),
        ('614561522', '10/2022', 'P2/STN1', 'STN1', 'active'),
        ('614561544', '10/2022', 'R1/STN1', 'STN1', 'active'),
        ('614561543', '10/2022', 'P2/STN1', 'STN1', 'active'),
        ('614561529', '10/2022', 'STN1',    'STN1', 'active'),
        ('614561539',  None,     'STN1',    'STN1', 'out_of_service'),  # damaged – yellow
        ('614561532', '10/2022', 'R1/STN1', 'STN1', 'active'),
        ('614561534', '10/2022', 'R1/STN1', 'STN1', 'active'),
    ]

    for serial, hydro, location, station, status in composite:
        next_due = None
        if hydro and status == 'active':
            next_due = _next_hydro_from_last(hydro)
        cursor.execute('''
            INSERT OR IGNORE INTO scba_bottles
                (bottle_type, dot_spec, serial_number, manufacturer, mfgr_date,
                 hydro_date, next_hydro_due, location, station, status)
            VALUES ('composite','SP11194',?,?,?,?,?,?,?,?)
        ''', (serial, 'Carleton', '06/2016', hydro, next_due, location, station, status))
        print(f"  Composite {serial} -> status={status}, next={next_due}")

    # ── ALUMINUM BOTTLES (Luxfer, DOT 3AL-2216) ──────────────────────────────
    aluminum = [
        # (serial, hydro_date, location, station)
        ('DG49523', '06/2026', 'STN1',    'STN1'),
        ('DG49547', '06/2026', 'STN1',    'STN1'),
        ('DG49579', '06/2026', 'STN1',    'STN1'),
        ('DG18648', '06/2026', 'STN1',    'STN1'),
        ('DG49559', '06/2026', 'STN1',    'STN1'),
        ('DG18657', '06/2026', 'STN1',    'STN1'),
        ('DG49568', '06/2026', 'STN1',    'STN1'),
        ('DG19266', '06/2026', 'STN1',    'STN1'),
        ('DG49582', '06/2026', 'STN1',    'STN1'),
        ('DG49539', '10/2022', 'STN1',    'STN1'),
        ('DG19276', '06/2026', 'STN1',    'STN1'),
        ('DG49565', '10/2022', 'STN1',    'STN1'),
        ('DG19263', '06/2026', 'STN1',    'STN1'),
        ('DG19268', '10/2022', 'STN1',    'STN1'),
        ('DG49537', '06/2026', 'P2/STN1', 'STN1'),
        ('DG18644', '06/2026', 'P3/STN2', 'STN2'),
        ('DG49558', '06/2026', 'P3/STN2', 'STN2'),
        ('DG18637', '06/2026', 'P3/STN2', 'STN2'),
        ('DG18647', '06/2026', 'P3/STN2', 'STN2'),
        ('DG49863', '06/2026', 'P3/STN2', 'STN2'),
        ('DG49543', '06/2026', 'P1/STN2', 'STN2'),
        ('DG49561', '06/2026', 'P1/STN2', 'STN2'),
        ('DG49551', '06/2026', 'P1/STN2', 'STN2'),
        ('DG19317', '06/2026', 'P1/STN2', 'STN2'),
    ]

    for serial, hydro, location, station in aluminum:
        next_due = _next_hydro_from_last(hydro)
        cursor.execute('''
            INSERT OR IGNORE INTO scba_bottles
                (bottle_type, dot_spec, serial_number, manufacturer, mfgr_date,
                 hydro_date, next_hydro_due, location, station, status)
            VALUES ('aluminum','3AL-2216',?,'Luxfer',NULL,?,?,?,?,'active')
        ''', (serial, hydro, next_due, location, station))
        print(f"  Aluminum  {serial} -> next={next_due}")

    conn.commit()
    conn.close()
    print(f"\nDone. Inserted {len(composite)} composite + {len(aluminum)} aluminum = {len(composite)+len(aluminum)} total bottles.")

if __name__ == '__main__':
    seed()
