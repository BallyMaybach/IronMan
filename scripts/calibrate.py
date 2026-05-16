#!/usr/bin/env python3
"""
Jarvis — Kalibrierung mit Countdown-Anleitung
"""

import sounddevice as sd
import numpy as np
import time
import os
import json
import threading
from collections import deque

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

SAMPLE_RATE  = 44100
BLOCK_SIZE   = 1024
HIGH_FREQ_HZ = 2000
BG_WINDOW    = 40

LOG_PATH = os.path.join(os.path.dirname(__file__), "calibrate.log")

bg_buf   = deque([0.001] * BG_WINDOW, maxlen=BG_WINDOW)
log_lines = []

def find_device(name):
    for i, d in enumerate(sd.query_devices()):
        if name.lower() in d["name"].lower() and d["max_input_channels"] > 0:
            return i
    return None

def callback(indata, frames, time_info, status):
    rms = float(np.sqrt(np.mean(indata ** 2)))

    if rms < 0.005:
        bg_buf.append(rms)
        return

    bg_avg = max(float(np.mean(bg_buf)), 0.001)
    spike  = rms / bg_avg

    signal   = indata[:, 0]
    fft_mag  = np.abs(np.fft.rfft(signal))
    freqs    = np.fft.rfftfreq(len(signal), d=1.0 / SAMPLE_RATE)
    total    = np.sum(fft_mag)
    hf_ratio = float(np.sum(fft_mag[freqs >= HIGH_FREQ_HZ]) / total) if total > 0 else 0.0

    if rms < 0.02:
        bg_buf.append(rms)
        return

    elapsed = time.time() - start_time
    line = f"t={elapsed:5.1f}s  RMS={rms:.4f}  spike={spike:5.1f}x  hf={hf_ratio:.2f}  bg={bg_avg:.5f}"
    log_lines.append(line)

device = find_device("HyperX") or find_device("G435") or None
print(f"\nGerät: {sd.query_devices(device)['name'] if device is not None else 'Standard'}")
print("─" * 50)

# Countdown-Anleitung
phases = [
    (3,  "BEREIT MACHEN..."),
    (7,  ">>> JETZT REDEN (erzähl was, räusper dich, summ)"),
    (5,  ">>> JETZT 2x KLATSCHEN"),
    (5,  ">>> NOCHMAL REDEN"),
]

start_time = 0.0

def run_countdown():
    global start_time
    for duration, label in phases:
        print(f"\n{label}")
        for i in range(duration, 0, -1):
            print(f"  {i}s...", end="\r", flush=True)
            time.sleep(1)
    print("\n\n  Fertig! Werte werden gespeichert...\n")

with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                    channels=1, dtype="float32", callback=callback, device=device):
    start_time = time.time()
    t = threading.Thread(target=run_countdown)
    t.start()
    t.join()

with open(LOG_PATH, "w", encoding="utf-8") as f:
    f.write(f"=== Kalibrierung {time.strftime('%H:%M:%S')} ===\n")
    f.write("Format: Zeit | RMS | Spike(xBG) | HF-Ratio | BG-Level\n\n")
    for line in log_lines:
        f.write(line + "\n")

print(f"Log gespeichert: {LOG_PATH}")
print("Sag Claude Bescheid, er liest es aus!")
