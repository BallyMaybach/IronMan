#!/usr/bin/env python3
"""
Jarvis — Double Clap Trigger mit System-Tray-Toggle
Startet inaktiv im Tray. Klick auf Icon → aktiviert Klatschen-Erkennung.
Zweimal klatschen → Work Session.
"""

import sounddevice as sd
import numpy as np
import subprocess
import time
import os
import sys
import json
import ctypes
import threading
from collections import deque
import pystray
from PIL import Image, ImageDraw

# --- Nur eine Instanz ---
_mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "JarvisClapTriggerMutex")
if ctypes.GetLastError() == 183:
    sys.exit(0)

# --- Config ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

WORKSPACE_PATH = config["workspace_path"]
SCRIPT_PATH    = os.path.join(WORKSPACE_PATH, "scripts", "launch-session.ps1")
VBS_PATH       = os.path.join(WORKSPACE_PATH, "scripts", "launch-hidden.vbs")

SAMPLE_RATE = 44100
BLOCK_SIZE  = 1024

# --- Thresholds (kalibriert auf HyperX Quadcast) ---
MIN_RMS      = 0.05
SPIKE_RATIO  = 15.0
HIGH_FREQ_HZ = 2000
HF_RATIO_MIN = 0.55
DEBOUNCE     = 0.20
MIN_GAP      = 0.15
MAX_GAP      = 1.2
COOLDOWN     = 10.0

LOG_PATH = os.path.join(os.path.dirname(__file__), "clap-debug.log")

def log(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")

log("=== Jarvis gestartet (inaktiv) ===")

# --- Tray-Icon ---
listening_enabled = False

def make_icon(active):
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = (40, 200, 80) if active else (120, 120, 120)
    draw.ellipse([4, 4, 60, 60], fill=color)
    if active:
        # Kleines weißes Mikrofon-Symbol andeuten
        draw.ellipse([22, 10, 42, 36], fill=(255, 255, 255))
        draw.rectangle([29, 36, 35, 48], fill=(255, 255, 255))
        draw.arc([20, 28, 44, 50], 0, 180, fill=(255, 255, 255), width=3)
    return img

def toggle(icon, item=None):
    global listening_enabled
    listening_enabled = not listening_enabled
    icon.icon  = make_icon(listening_enabled)
    icon.title = "Jarvis — AKTIV (klatsch 2x!)" if listening_enabled else "Jarvis — inaktiv"
    log(f"Toggle: {'AN' if listening_enabled else 'AUS'}")

def exit_app(icon, item):
    log("=== Jarvis beendet ===")
    icon.stop()
    os._exit(0)

tray = pystray.Icon(
    "Jarvis",
    make_icon(False),
    "Jarvis — inaktiv",
    menu=pystray.Menu(
        pystray.MenuItem("Jarvis AN / AUS", toggle, default=True),
        pystray.MenuItem("Beenden", exit_app),
    )
)

# --- Audio-Erkennung ---
bg_buf             = deque([0.001] * 40, maxlen=40)
last_clap_time     = 0.0
last_trigger_time  = 0.0
last_debounce_time = 0.0

def audio_callback(indata, frames, time_info, status):
    global last_clap_time, last_trigger_time, last_debounce_time

    if not listening_enabled:
        return

    now = time.time()
    if now - last_trigger_time < COOLDOWN:
        return

    rms = float(np.sqrt(np.mean(indata ** 2)))

    if rms < MIN_RMS * 3:
        bg_buf.append(rms)

    if rms < MIN_RMS:
        return
    if now - last_debounce_time < DEBOUNCE:
        return

    bg_avg = max(float(np.mean(bg_buf)), 0.001)
    spike  = rms / bg_avg
    if spike < SPIKE_RATIO:
        return

    signal   = indata[:, 0]
    fft_mag  = np.abs(np.fft.rfft(signal))
    freqs    = np.fft.rfftfreq(len(signal), d=1.0 / SAMPLE_RATE)
    total    = np.sum(fft_mag)
    hf_ratio = float(np.sum(fft_mag[freqs >= HIGH_FREQ_HZ]) / total) if total > 0 else 0.0
    if hf_ratio < HF_RATIO_MIN:
        return

    last_debounce_time = now
    gap = now - last_clap_time
    log(f"Clap — RMS={rms:.3f} spike={spike:.1f}x hf={hf_ratio:.2f} gap={gap:.2f}s")

    if gap >= MIN_GAP and gap <= MAX_GAP and last_clap_time > 0:
        log(">>> DOPPELKLATSCHEN — starte Work Session")
        last_trigger_time = now
        last_clap_time    = 0.0
        subprocess.Popen(["wscript.exe", VBS_PATH, SCRIPT_PATH])
    else:
        last_clap_time = now

def find_device(name):
    for i, d in enumerate(sd.query_devices()):
        if name.lower() in d["name"].lower() and d["max_input_channels"] > 0:
            return i
    return None

device = find_device("HyperX") or find_device("G435") or None
log(f"Gerät: {sd.query_devices(device)['name'] if device is not None else 'Standard'}")

def audio_loop():
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype="float32",
            callback=audio_callback,
            device=device,
        ):
            log("Stream gestartet.")
            while True:
                time.sleep(0.1)
    except Exception as e:
        log(f"FEHLER Audio-Stream: {e}")

threading.Thread(target=audio_loop, daemon=True).start()

# Tray läuft im Main-Thread (pystray-Anforderung)
tray.run()
