#!/usr/bin/env python3
"""
Watch one ~2 MHz slice of spectrum continuously and log every transmission:
start time, end time, duration, exact frequency, strength.

Used to pin down which channel the SVFD R7 ("COM 2") is on: line the log up
with the times the radio goes off.

  python3 rf_activity_logger.py 167.0M:169.2M      (default)
Log: ~/rf_activity.log
"""
import subprocess, sys, os, time, numpy as np

RANGE   = sys.argv[1] if len(sys.argv) > 1 else "167.0M:169.2M"
BIN     = sys.argv[2] if len(sys.argv) > 2 else "1k"
GAIN    = "49.6"
JUMP_DB = 8.0          # this far above a bin's own normal level = transmitting
HOLD    = 3            # seconds of silence before a transmission is "over"
WARMUP  = 30           # sweeps used to learn each bin's normal level before logging
LOG     = os.path.expanduser("~/rf_activity.log")

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def main():
    log(f"watching {RANGE}, alert at +{JUMP_DB} dB over each bin's normal level")
    proc = subprocess.Popen(["/usr/local/bin/rtl_power", "-f", f"{RANGE}:{BIN}", "-g", GAIN,
                             "-i", "1", "-c", "0.2", "-"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    normal = {}            # hz -> slowly-tracked normal level (dB)
    warm = {}              # hz -> samples collected during warm-up
    sweep = {}             # current sweep: hz -> dB
    last_stamp = None
    active = {}            # channel hz (rounded to 2.5 kHz) -> {start, last, peak}
    last_status = time.time()

    for line in proc.stdout:
        parts = line.strip().split(", ")
        if len(parts) < 7:
            continue
        stamp = parts[0] + " " + parts[1]
        if last_stamp is not None and stamp != last_stamp:
            if warm is not None:
                for hz, db in sweep.items():
                    warm.setdefault(hz, []).append(db)
                if max((len(v) for v in warm.values()), default=0) >= WARMUP:
                    normal.update({hz: float(np.median(v)) for hz, v in warm.items()})
                    warm = None
                    log(f"learned normal levels for {len(normal)} bins - logging transmissions now")
            else:
                evaluate(sweep, normal, active)
            sweep = {}
        last_stamp = stamp
        lo, step = float(parts[2]), float(parts[4])
        for i, v in enumerate(parts[6:]):
            try:
                sweep[int(round(lo + i * step))] = float(v)
            except ValueError:
                pass
        if time.time() - last_status > 1800:
            log(f"(alive, tracking {len(normal)} bins, {len(active)} active)")
            last_status = time.time()

def evaluate(sweep, normal, active):
    now = time.time()
    hot = {}
    for hz, db in sweep.items():
        base = normal.get(hz)
        if base is None:
            normal[hz] = db
            continue
        if db - base >= JUMP_DB:
            ch = round(hz / 2500) * 2500
            hot[ch] = max(hot.get(ch, -999), db - base)
            normal[hz] = 0.999 * base + 0.001 * db   # very slow, so a stuck carrier eventually fades
        else:
            normal[hz] = 0.98 * base + 0.02 * db
    # merge neighbouring hot bins into one channel (strongest wins)
    for ch in sorted(hot, key=hot.get, reverse=True):
        near = next((a for a in active if abs(a - ch) <= 7500), None)
        key = near if near is not None else ch
        if key not in active:
            active[key] = {"start": now, "last": now, "peak": hot[ch]}
            log(f"ON   {key / 1e6:.4f} MHz  +{hot[ch]:.1f} dB")
        a = active[key]
        a["last"], a["peak"] = now, max(a["peak"], hot[ch])
    for key in list(active):
        a = active[key]
        if now - a["last"] > HOLD:
            log(f"OFF  {key / 1e6:.4f} MHz  {a['last'] - a['start'] + 1:.0f}s  peak +{a['peak']:.1f} dB")
            del active[key]

if __name__ == "__main__":
    main()
