"""
Einmalig ausführen: generiert 3 Begrüßungs-MP3s mit ElevenLabs.
python scripts/generate-greetings.py
"""

import json
import os
import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

API_KEY   = config["elevenlabs_api_key"]
VOICE_ID  = config.get("elevenlabs_voice_id", "pNInz6obpgDQGcFmaJgB")

GREETINGS = [
    "Welcome back, Sir. Ready when you are.",
    "Good to have you back, Sir. All systems standing by.",
    "At your service, Sir. What shall we accomplish today?",
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "greetings")
os.makedirs(OUT_DIR, exist_ok=True)

for i, text in enumerate(GREETINGS):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    resp = requests.post(url, headers={
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }, json={
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.65, "similarity_boost": 0.82, "style": 0.15, "use_speaker_boost": True},
    })
    if resp.status_code == 200:
        path = os.path.join(OUT_DIR, f"greeting_{i}.mp3")
        with open(path, "wb") as f:
            f.write(resp.content)
        print(f"OK  greeting_{i}.mp3  —  {text}")
    else:
        print(f"ERR {resp.status_code}: {resp.text[:200]}")

index_path = os.path.join(OUT_DIR, "index.txt")
if not os.path.exists(index_path):
    with open(index_path, "w") as f:
        f.write("0")

print("\nFertig. Starte jetzt launch-session.ps1 um zu testen.")
