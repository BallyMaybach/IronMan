#!/usr/bin/env python3
"""
Jarvis Clap-Trigger (Toggle)
Tray-Icon: grau = aus | cyan = an
Linksklick -> togglet an/aus
Wenn an: Doppelklatschen -> Jarvis starten, bleibt danach an
Rechtsklick -> Beenden
"""
import sounddevice as sd
import numpy as np
import subprocess
import time
import os
import json
import threading
import pystray
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "..", "config.json")) as f:
    cfg = json.load(f)

VBS = os.path.join(cfg["workspace_path"], "scripts", "launch-hidden.vbs")
PS1 = os.path.join(cfg["workspace_path"], "scripts", "launch-session.ps1")

THRESHOLD = 0.007
MIN_GAP   = 0.1
MAX_GAP   = 1.2
COOLDOWN  = 10.0
BOOT_DELAY = 8

active          = False
last_clap       = 0.0
last_trigger    = 0.0
_icon           = None

def make_img(rgb):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([4, 4, 60, 60], fill=rgb)
    return img

IMG_OFF = make_img((90, 90, 90))
IMG_ON  = make_img((0, 212, 255))

def audio_cb(indata, frames, ti, status):
    global last_clap, last_trigger, active
    if not active:
        return
    now = time.time()
    if now - last_trigger < COOLDOWN:
        return
    rms = float(np.sqrt(np.mean(indata ** 2)))
    if rms > THRESHOLD:
        gap = now - last_clap
        if gap >= MIN_GAP:
            if gap <= MAX_GAP and last_clap > 0:
                last_trigger = now
                last_clap    = 0.0
                subprocess.Popen(["wscript.exe", VBS, PS1])
            else:
                last_clap = now

def toggle(icon, item=None):
    global active, last_clap
    active    = not active
    last_clap = 0.0
    if active:
        icon.icon  = IMG_ON
        icon.title = "Jarvis — hoert zu"
    else:
        icon.icon  = IMG_OFF
        icon.title = "Jarvis — aus"

def quit_app(icon, item=None):
    stream.stop()
    icon.stop()

# Warten bis Windows Audio beim Boot fertig ist
time.sleep(BOOT_DELAY)

stream = sd.InputStream(
    samplerate=44100,
    blocksize=1024,
    channels=1,
    dtype="float32",
    callback=audio_cb,
    device=None,  # Windows-Standardmikrofon, stabil nach Neustart
)
stream.start()

menu  = pystray.Menu(
    pystray.MenuItem("Toggle", toggle, default=True),
    pystray.MenuItem("Beenden", quit_app),
)
_icon = pystray.Icon("jarvis-clap", IMG_OFF, "Jarvis — aus", menu)
_icon.run()
