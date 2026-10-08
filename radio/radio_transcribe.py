#!/usr/bin/env python3
"""
Fire radio transcription v5 — SDR + microphone "tone finder".

  SDR thread   rtl_fm on the current frequency with noise squelch (from v4).
               Every call it hears gets transcribed and posted.
  Mic thread   Listens to the physical radio sitting next to the Mac.  When it
               hears a sustained paging tone:
                 * SDR squelch already open  -> frequency confirmed, SDR has it.
                 * SDR silent                -> record the call from the mic and
                   transcribe that, while the dongle sweeps 150-174 MHz to find
                   which channel just lit up.  If one stands out, retune to it
                   and save it to ~/radio_freq.txt so it sticks.
  When the radio leaves with you, the mic hears nothing and the SDR keeps going.

Must be started from Terminal ON the Mac (not over SSH) the first time so macOS
can ask for microphone permission.
"""
import subprocess, threading, queue, numpy as np, wave, os, time, json, glob, csv
import urllib.request, urllib.error
from scipy.signal import butter, lfilter, filtfilt

HOME        = os.path.expanduser("~")
FREQ_FILE   = os.path.join(HOME, "radio_freq.txt")
HITS_FILE   = os.path.join(HOME, "radio_freq_hits.json")
BLOCK_FILE  = os.path.join(HOME, "radio_freq_blocked.json")   # always-on carriers, never dispatch
DEFAULT_FREQ = "155.400M"   # SVFD "COM 2": analog FM, 100.0 Hz PL (found 2026-10-07)
# While this file exists the dongle is left alone (e.g. rf_activity_logger.py is using it);
# the mic keeps recording and transcribing pages.
NO_SDR = os.path.exists(os.path.join(HOME, "radio_no_sdr"))
CAPTURE_DIR = os.path.join(HOME, "radio_captures")
KEEP_CAPTURES = 300
RTL         = "/usr/local/bin/"

SAMPLE_RATE = 16000
GAIN        = "40"     # 49.6 overloads on 155.400 and static reads as a carrier (squelch never closes)
FLASK_URL   = "https://michealhelps.pythonanywhere.com/api/radio/transcription"
MODEL_SIZE  = "base.en"
POST        = os.environ.get("RADIO_POST", "1") == "1"
CHUNK       = 1024       # ~64 ms at 16 kHz

# SDR noise squelch: fraction of audio energy above 4 kHz.  Hiss ~0.45, carrier ~0.05.
SQ_OPEN, SQ_CLOSE, OPEN_CHUNKS = 0.28, 0.34, 3
TAIL_SECS, MAX_SECS, MIN_SECS = 2.0, 90, 1.0
STUCK_MAX_CLOSES = 4             # this many back-to-back 90 s captures = constant carrier, not dispatch

# Mic tone detector
TONE_BAND        = (250, 2500)   # Hz, two-tone / Minitor paging range
TONE_PURITY      = 0.55          # share of band energy in the peak
TONE_LOUDNESS    = 5.0           # x ambient room level
TONE_MIN_SECS    = 0.6
TONE_COOLDOWN    = 90            # s between triggers
MIC_QUIET_END    = 8.0           # s of room-level quiet ends a mic recording
MIC_MIN_SECS     = 30            # always keep at least this much after the tone
MIC_MAX_SECS     = 120

# Frequency sweep
# The station radio is a Motorola MOTOTRBO R7 (DMR); VHF and UHF versions exist.
SWEEP_RANGES     = ["450M:470M:5k", "136M:174M:5k"]
SWEEP_SECS       = 24
BASELINE_EVERY   = 3600
MIN_JUMP_DB      = 10.0

HALLUCINATIONS = {
    "thanks for watching", "thank you for watching", "thank you",
    "you", "the", ".", "", "uh", "um", "hmm", "bye",
    "please subscribe", "like and subscribe", "subscribe", "yeah",
    "i", "a", "okay", "ok", "we", "it", "...", "and", " ",
}

B_BP, A_BP = butter(4, [300 / (SAMPLE_RATE/2), 3000 / (SAMPLE_RATE/2)], btype='band')
B_HF, A_HF = butter(4, 4000 / (SAMPLE_RATE/2), btype='high')

log_lock = threading.Lock()
def log(msg):
    with log_lock:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

# ── shared state ──────────────────────────────────────────────────────────────

def load_freq():
    try:
        return open(FREQ_FILE).read().strip() or DEFAULT_FREQ
    except OSError:
        return DEFAULT_FREQ

def load_blocked():
    try:
        return json.load(open(BLOCK_FILE))
    except (OSError, ValueError):
        return []

class State:
    freq = load_freq()
    sdr_last_active = 0.0      # last time SDR squelch was open
    sdr_open_since = 0.0       # start of the current transmission (0 = squelch closed)
    blocked = load_blocked()   # frequencies with a constant carrier
    pause = threading.Event()  # set -> SDR thread releases the dongle
    released = threading.Event()
    baseline = None            # {hz: dB}
    baseline_time = 0.0

S = State()
jobs = queue.Queue()           # (source, samples, started)

# ── transcription worker ─────────────────────────────────────────────────────

def save_wav(samples, path):
    mx = np.abs(samples).max()
    norm = (samples / mx * 28000) if mx > 0 else samples
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
        wf.writeframes(norm.astype(np.int16).tobytes())

def post(text, ts):
    if not POST:
        return
    payload = json.dumps({'text': text, 'timestamp': ts}).encode()
    req = urllib.request.Request(FLASK_URL, data=payload,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        urllib.request.urlopen(req, timeout=10)
        log(f"  [posted] {text!r}")
    except urllib.error.URLError as e:
        log(f"  [warn] post failed: {e.reason}")

def transcriber():
    from faster_whisper import WhisperModel
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    log("Whisper ready")
    while True:
        source, samples, started = jobs.get()
        filtered = filtfilt(B_BP, A_BP, samples)
        name = time.strftime('%Y%m%d_%H%M%S', time.localtime(started)) + f"_{source}.wav"
        path = os.path.join(CAPTURE_DIR, name)
        save_wav(filtered, path)
        for f in sorted(glob.glob(os.path.join(CAPTURE_DIR, "*.wav")))[:-KEEP_CAPTURES]:
            os.unlink(f)
        segs, _ = model.transcribe(path, language='en', vad_filter=True,
                                   condition_on_previous_text=False,
                                   no_speech_threshold=0.85, beam_size=5)
        parts = [s.text.strip() for s in segs
                 if s.text.strip().lower().rstrip('!.,? ') not in HALLUCINATIONS
                 and len(s.text.strip()) >= 3]
        if parts:
            text = " ".join(parts)
            log(f"  TEXT ({source}): {text}")
            post(text, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started)))
        else:
            log(f"  (no speech in {name})")

# ── SDR thread ────────────────────────────────────────────────────────────────

def hf_ratio(x):
    hf = lfilter(B_HF, A_HF, x)
    return float(np.sum(hf ** 2)) / (float(np.sum(x ** 2)) + 1e-9)

def sdr_worker():
    tail_chunks = int(TAIL_SECS * SAMPLE_RATE / CHUNK)
    max_samples = MAX_SECS * SAMPLE_RATE
    while True:
        if S.pause.is_set():
            S.released.set()
            while S.pause.is_set():
                time.sleep(0.2)
        freq = S.freq
        log(f"[sdr] listening {freq}")
        proc = subprocess.Popen([RTL + 'rtl_fm', '-f', freq, '-M', 'fm', '-s', '16k',
                                 '-r', str(SAMPLE_RATE), '-g', GAIN, '-E', 'deemp'],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        recording, buf, pre, quiet_run, noisy_run, started = False, [], [], 0, 0, 0.0
        stuck, S.sdr_open_since = 0, 0.0
        try:
            while not S.pause.is_set() and S.freq == freq:
                raw = proc.stdout.read(CHUNK * 2)
                if not raw:
                    log("[sdr] rtl_fm exited; restarting")
                    time.sleep(2)
                    break
                x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                x = x - x.mean()
                r = hf_ratio(x)
                if not recording:
                    pre = (pre + [x])[-OPEN_CHUNKS:]
                    quiet_run = quiet_run + 1 if r < SQ_OPEN else 0
                    if quiet_run >= OPEN_CHUNKS:
                        recording, buf, noisy_run, started = True, list(pre), 0, time.time()
                        S.sdr_last_active = time.time()
                        if not S.sdr_open_since:
                            S.sdr_open_since = started
                        log(f"[sdr] carrier on {freq}")
                else:
                    buf.append(x)
                    if r <= SQ_CLOSE:
                        S.sdr_last_active = time.time()
                    noisy_run = noisy_run + 1 if r > SQ_CLOSE else 0
                    total = sum(len(b) for b in buf)
                    if noisy_run >= tail_chunks or total >= max_samples:
                        dur = total / SAMPLE_RATE
                        log(f"[sdr] close {dur:.1f}s")
                        if dur >= MIN_SECS:
                            jobs.put(("sdr", np.concatenate(buf), started))
                        recording, buf, pre, quiet_run = False, [], [], 0
                        if total >= max_samples:
                            stuck += 1
                            if stuck >= STUCK_MAX_CLOSES:
                                block_frequency(freq)
                                break
                        else:
                            stuck, S.sdr_open_since = 0, 0.0
        finally:
            proc.terminate(); proc.wait()
            if recording and buf:
                jobs.put(("sdr", np.concatenate(buf), started))

def block_frequency(freq):
    """A channel that never goes quiet is a data/paging transmitter, not dispatch."""
    if freq not in S.blocked:
        S.blocked.append(freq)
        json.dump(S.blocked, open(BLOCK_FILE, "w"), indent=1)
    log(f"[sdr] {freq} has a constant carrier — blocking it and going back to {DEFAULT_FREQ}")
    S.freq = DEFAULT_FREQ
    S.sdr_open_since = 0.0
    open(FREQ_FILE, "w").write(DEFAULT_FREQ + "\n")

# ── frequency sweep ───────────────────────────────────────────────────────────

def rtl_power(seconds):
    """Return {hz: [dB,...]} across SWEEP_RANGES, splitting `seconds` between them.
    Caller must own the dongle."""
    out = "/tmp/radio_sweep.csv"
    acc = {}
    for rng in SWEEP_RANGES:
        subprocess.run([RTL + 'rtl_power', '-f', rng, '-g', GAIN, '-i', '2',
                        '-c', '0.2', '-e', f'{max(4, seconds // len(SWEEP_RANGES))}s', out],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(out) as f:
            for r in csv.reader(f):
                lo, step = float(r[2]), float(r[4])
                for i, v in enumerate(r[6:]):
                    acc.setdefault(int(round(lo + i * step)), []).append(float(v))
    return acc

def with_dongle(fn):
    S.released.clear()
    S.pause.set()
    S.released.wait(timeout=10)
    try:
        return fn()
    finally:
        S.pause.clear()

def take_baseline():
    acc = with_dongle(lambda: rtl_power(16))
    S.baseline = {hz: float(np.median(v)) for hz, v in acc.items()}
    S.baseline_time = time.time()
    log(f"[sweep] baseline stored ({len(S.baseline)} bins)")

def record_hit(freq):
    try:
        hits = json.load(open(HITS_FILE))
    except (OSError, ValueError):
        hits = {}
    hits[freq] = hits.get(freq, 0) + 1
    json.dump(hits, open(HITS_FILE, "w"), indent=1)
    return hits[freq]

def find_channel():
    log("[sweep] tone heard but SDR silent — sweeping 450–470 + 136–174 MHz")
    acc = with_dongle(lambda: rtl_power(SWEEP_SECS))
    if not S.baseline:
        log("[sweep] no baseline yet; skipping")
        return
    blocked_hz = [float(f.rstrip('M')) * 1e6 for f in S.blocked]
    best_hz, best_jump = None, 0.0
    for hz, vals in acc.items():
        base = S.baseline.get(hz)
        if base is None or any(abs(hz - b) <= 7500 for b in blocked_hz):
            continue
        jump = max(vals) - base
        if jump > best_jump:
            best_hz, best_jump = hz, jump
    if best_hz is None or best_jump < MIN_JUMP_DB:
        log(f"[sweep] nothing stood out (best +{best_jump:.1f} dB). Dispatch may be "
            "outside the swept bands, or too weak here")
        return
    snapped = round(best_hz / 2500) * 2500
    freq = f"{snapped / 1e6:.4f}M"
    n = record_hit(freq)
    top = sorted(((max(v) - S.baseline[h], h) for h, v in acc.items()
                  if h in S.baseline and not any(abs(h - b) <= 7500 for b in blocked_hz)), reverse=True)[:5]
    log("[sweep] top jumps: " + ", ".join(f"{h / 1e6:.4f} +{d:.1f}" for d, h in top))
    log(f"[sweep] FOUND activity on {freq} (+{best_jump:.1f} dB), seen {n}x — retuning")
    S.freq = freq
    open(FREQ_FILE, "w").write(freq + "\n")

# ── mic thread ────────────────────────────────────────────────────────────────

def mic_worker():
    import sounddevice as sd
    blocks = queue.Queue()
    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32',
                            blocksize=CHUNK, callback=lambda d, *_: blocks.put(d[:, 0].copy()))
    stream.start()
    log("[mic] listening for paging tones")
    freqs = np.fft.rfftfreq(CHUNK, 1 / SAMPLE_RATE)
    band = (freqs >= TONE_BAND[0]) & (freqs <= TONE_BAND[1])
    win = np.hanning(CHUNK)
    ambient = 1e-3
    tone_run, tone_hz, last_trigger = 0, 0.0, 0.0
    need = int(TONE_MIN_SECS * SAMPLE_RATE / CHUNK)
    last_stat = time.time()

    while True:
        x = blocks.get()
        rms = float(np.sqrt(np.mean(x ** 2)))
        p = np.abs(np.fft.rfft(x * win)) ** 2
        pb = p[band]
        k = int(np.argmax(pb))
        purity = pb[max(0, k-1):k+2].sum() / (pb.sum() + 1e-12)
        peak_hz = freqs[band][k]
        tonal = purity > TONE_PURITY and rms > ambient * TONE_LOUDNESS

        if tonal and abs(peak_hz - tone_hz) < 20:
            tone_run += 1
        elif tonal:
            tone_run, tone_hz = 1, peak_hz
        else:
            tone_run = 0
            ambient = 0.995 * ambient + 0.005 * rms   # slow room-level tracker

        if time.time() - last_stat > 600:
            log(f"[mic] ok, room level {ambient:.4f}")
            last_stat = time.time()

        if tone_run >= need and time.time() - last_trigger > TONE_COOLDOWN:
            last_trigger = time.time()
            tone_run = 0
            log(f"[mic] PAGING TONE {tone_hz:.0f} Hz")
            # The SDR only "has it" if a transmission started just before the tone;
            # a carrier that has been up for minutes is something else.
            if S.sdr_open_since and time.time() - S.sdr_open_since < 45:
                n = record_hit(S.freq)
                log(f"[mic] SDR picked this up on {S.freq} too — confirmed ({n}x)")
            elif not NO_SDR:
                threading.Thread(target=find_channel, daemon=True).start()
            # Always record the call from the mic so it gets transcribed.
            started, buf, quiet = time.time(), [x], 0.0
            while time.time() - started < MIC_MAX_SECS:
                y = blocks.get()
                buf.append(y)
                if float(np.sqrt(np.mean(y ** 2))) < ambient * 3:
                    quiet += CHUNK / SAMPLE_RATE
                    if quiet >= MIC_QUIET_END and time.time() - started > MIC_MIN_SECS:
                        break
                else:
                    quiet = 0.0
            audio = np.concatenate(buf) * 32767
            log(f"[mic] recorded {len(audio) / SAMPLE_RATE:.0f}s from radio speaker")
            jobs.put(("mic", audio, started))

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    threading.Thread(target=transcriber, daemon=True).start()
    mic_on = os.environ.get("RADIO_NO_MIC") != "1" and not os.path.exists(os.path.join(HOME, "radio_no_mic"))
    if mic_on:
        threading.Thread(target=mic_worker, daemon=True).start()
    if NO_SDR:
        log("[sdr] disabled (~/radio_no_sdr exists) - mic only")
        while True:
            time.sleep(3600)
    threading.Thread(target=sdr_worker, daemon=True).start()
    if not mic_on:
        # Baselines only feed the mic-triggered channel search; don't pause the SDR for them.
        while True:
            time.sleep(3600)
    take_baseline()
    while True:
        time.sleep(30)
        if time.time() - S.baseline_time > BASELINE_EVERY and time.time() - S.sdr_last_active > 60:
            take_baseline()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log("[stopped]")
