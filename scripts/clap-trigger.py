#!/usr/bin/env python3
"""
Jarvis — Double Clap Trigger (always-on loop)
Runs in background at startup. Detects two claps within 1.2s, min 0.1s apart.
Fires launch-session.ps1, then keeps listening for the next trigger.
"""

import sounddevice as sd
import numpy as np
import subprocess
import time
import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

WORKSPACE_PATH = config["workspace_path"]
SCRIPT_PATH = os.path.join(WORKSPACE_PATH, "scripts", "launch-session.ps1")
VBS_PATH = os.path.join(WORKSPACE_PATH, "scripts", "launch-hidden.vbs")

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
THRESHOLD = 1.0
MIN_GAP = 0.1
MAX_GAP = 1.2
COOLDOWN = 10.0

LOG_PATH = os.path.join(os.path.dirname(__file__), "clap-debug.log")

def log(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")

log("=== Clap-Trigger gestartet ===")

last_clap_time = 0.0
last_trigger_time = 0.0

def audio_callback(indata, frames, time_info, status):
    global last_clap_time, last_trigger_time

    now = time.time()

    if now - last_trigger_time < COOLDOWN:
        return

    rms = float(np.sqrt(np.mean(indata ** 2)))

    if rms > THRESHOLD:
        gap = now - last_clap_time

        if gap >= MIN_GAP:
            if gap <= MAX_GAP and last_clap_time > 0:
                log(f">>> DOPPELKLATSCHEN — starte Launch-Session")
                last_trigger_time = now
                last_clap_time = 0.0
                subprocess.Popen(["wscript.exe", VBS_PATH, SCRIPT_PATH])
            else:
                last_clap_time = now

def find_device(name_fragment):
    for i, d in enumerate(sd.query_devices()):
        if name_fragment.lower() in d["name"].lower() and d["max_input_channels"] > 0:
            return i
    return None

device = find_device("HyperX") or find_device("G435") or None
log(f"Verwende Gerät: {sd.query_devices(device)['name'] if device is not None else 'Standard'}")

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    channels=1,
    dtype="float32",
    callback=audio_callback,
    device=device,
):
    while True:
        time.sleep(0.1)
