import json, httpx, base64, os

with open("config.json") as f:
    config = json.load(f)

url = f"https://api.elevenlabs.io/v1/text-to-speech/{config['elevenlabs_voice_id']}"
resp = httpx.post(url, headers={
    "xi-api-key": config["elevenlabs_api_key"],
    "Content-Type": "application/json",
    "Accept": "audio/mpeg",
}, json={"text": "Hallo Sir, Jarvis ist bereit.", "model_id": "eleven_turbo_v2_5"})

print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    with open("test_output.mp3", "wb") as f:
        f.write(resp.content)
    print(f"Audio gespeichert: {len(resp.content)} bytes → test_output.mp3")
else:
    print(f"Fehler: {resp.text[:300]}")
