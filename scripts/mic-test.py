import sounddevice as sd
import numpy as np
import time

print("=" * 50)
print("JARVIS MIC DIAGNOSE")
print("=" * 50)

# Alle Eingabegeraete auflisten
devices = sd.query_devices()
input_devs = [(i, d) for i, d in enumerate(devices) if d["max_input_channels"] > 0]

print(f"\n{len(input_devs)} Eingabegeraete gefunden:\n")
for i, d in input_devs:
    marker = ">>>" if "hyperx" in d["name"].lower() else "   "
    print(f"  {marker} [{i:2}] {d['name']}  ({d['max_input_channels']}ch, {int(d['default_samplerate'])}Hz)")

# HyperX finden
hyperx = [(i, d) for i, d in input_devs if "hyperx" in d["name"].lower()]
if not hyperx:
    print("\nFEHLER: Kein HyperX Geraet gefunden!")
else:
    print(f"\nHyperX gefunden: {len(hyperx)}x")

print("\n" + "=" * 50)

# Test 1: Standard-Device (was Windows gerade nutzt)
print("\nTEST 1 — Windows Standard-Mic (3 Sek, ruhig bleiben)")
vals = []
def cb1(indata, *_):
    vals.append(float(np.sqrt(np.mean(indata**2))))
with sd.InputStream(samplerate=44100, blocksize=1024, channels=1, dtype="float32", callback=cb1, device=None):
    time.sleep(3)
avg1 = sum(vals)/len(vals) if vals else 0
max1 = max(vals) if vals else 0
print(f"  Durchschnitt: {avg1:.5f}  |  Max: {max1:.5f}  |  Samples: {len(vals)}")
if avg1 < 0.0001:
    print("  STATUS: KEIN SIGNAL — Standard-Mic liefert nichts")
elif avg1 < 0.001:
    print("  STATUS: sehr schwaches Signal (Hintergrundrauschen?)")
else:
    print("  STATUS: Signal vorhanden")

# Test 2: Jetzt laut klatschen
print("\nTEST 2 — Standard-Mic (3 Sek, JETZT KLATSCHEN!)")
vals2 = []
def cb2(indata, *_):
    rms = float(np.sqrt(np.mean(indata**2)))
    if rms > 0.001:
        vals2.append(rms)
        print(f"  RMS: {rms:.5f}")
with sd.InputStream(samplerate=44100, blocksize=1024, channels=1, dtype="float32", callback=cb2, device=None):
    time.sleep(3)
if not vals2:
    print("  NICHTS erkannt — Klatschen hat kein Signal erzeugt")
else:
    print(f"  Max beim Klatschen: {max(vals2):.5f}")

# Test 3: HyperX direkt testen (falls gefunden)
if hyperx:
    idx = hyperx[0][0]
    name = hyperx[0][1]["name"]
    print(f"\nTEST 3 — HyperX direkt [{idx}] (3 Sek, KLATSCHEN!)")
    vals3 = []
    def cb3(indata, *_):
        rms = float(np.sqrt(np.mean(indata**2)))
        if rms > 0.001:
            vals3.append(rms)
            print(f"  RMS: {rms:.5f}")
    try:
        with sd.InputStream(samplerate=44100, blocksize=1024, channels=1, dtype="float32", callback=cb3, device=idx):
            time.sleep(3)
        if not vals3:
            print("  NICHTS erkannt auf HyperX direkt")
        else:
            print(f"  Max: {max(vals3):.5f}")
    except Exception as e:
        print(f"  FEHLER beim Oeffnen: {e}")

print("\n" + "=" * 50)
print("DIAGNOSE ABGESCHLOSSEN")
print("=" * 50)
