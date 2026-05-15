import sounddevice as sd
import numpy as np
import time

print("Verfuegbare Eingabegeraete:")
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0:
        print(f"  [{i}] {d['name']}")

print()
print("Messe 5 Sekunden -- jetzt klatschen!")
print()

def cb(indata, frames, ti, status):
    rms = float(np.sqrt(np.mean(indata**2)))
    if rms > 0.005:
        print(f"RMS: {rms:.4f}")

with sd.InputStream(samplerate=44100, blocksize=1024, channels=1, dtype="float32", callback=cb):
    time.sleep(5)
