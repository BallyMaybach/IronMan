# CLAUDE.md

- **Projekt:** Jarvis Clap-Trigger
- **Was es tut:** Doppelklatschen → Begrüßungs-MP3 + Claude Desktop (links fullscreen) + Notion (rechts links) + VS Code (rechts rechts) + Spotify (minimiert, Song läuft)
- **Toggle:** System-Tray-Icon (pystray) — Jarvis kann damit ein/ausgeschaltet werden ohne den Task zu stoppen
- **Stand:** Läuft stabil. Mai 2026 — alter Voice-Assistant-Kram entfernt, nur noch Clap-Trigger.
- **Deployment:** Lokal via Windows Task Scheduler (Task: `JarvisClapTrigger`)

---

## Dateistruktur

```
jarvis-voice-assistant-master/
├── scripts/
│   ├── clap-trigger.py       ← Hauptskript, läuft permanent im Hintergrund
│   ├── launch-session.ps1    ← Startet alle Apps + MP3
│   ├── launch-hidden.vbs     ← Startet launch-session.ps1 ohne Terminal-Fenster
│   └── generate-greetings.py ← ElevenLabs MP3s neu generieren (einmalig)
├── assets/greetings/
│   ├── greeting_0/1/2.mp3    ← Pre-generierte Begrüßungen (Felix Serenitas)
│   └── index.txt             ← Aktueller MP3-Index (rotiert 0→1→2→0)
├── config.json               ← API-Keys, Pfade, Spotify-Track (gitignored)
├── config.example.json
├── requirements.txt          ← Nur: sounddevice, numpy
└── CLAUDE.md
```

---

## Clap-Trigger (clap-trigger.py)

Läuft permanent via Task Scheduler. Erkennt Doppelklatschen via:
- **RMS-Threshold** (Mindestlautstärke)
- **Frequenzanalyse**: ≥40% Energie über 2kHz → unterscheidet Klatschen von Reden/Musik

Zwei Klatscher innerhalb 1.2s (min 0.1s Abstand) → Trigger. 10s Cooldown danach.

Wichtige Konstanten in `clap-trigger.py`:
```python
THRESHOLD = 0.3       # Mindest-RMS
HIGH_FREQ_RATIO = 0.4 # Hochfrequenz-Anteil für Klatschen
HIGH_FREQ_HZ = 2000   # Grenzfrequenz in Hz
MIN_GAP = 0.1         # Mindestabstand zwischen Klatschen (s)
MAX_GAP = 1.2         # Maximalabstand für Doppelklatschen (s)
COOLDOWN = 10.0       # Sekunden nach Trigger
```

Debug-Log: `scripts/clap-debug.log` — zeigt RMS und HF-Ratio jedes erkannten Sounds.
Bei Fehlauslösern durch Reden: `HIGH_FREQ_RATIO` auf `0.5` erhöhen.
Bei nicht erkannten Klatschen: `HIGH_FREQ_RATIO` auf `0.35` senken.

Task nach Script-Änderungen neu starten:
```powershell
Stop-ScheduledTask -TaskName "JarvisClapTrigger"
Start-ScheduledTask -TaskName "JarvisClapTrigger"
```

---

## launch-session.ps1

Ablauf:
1. MP3 sofort async abspielen (blockiert nicht)
2. Alle 4 Apps gleichzeitig starten (Claude, VS Code, Notion, Spotify)
3. Fenster per Polling snappen sobald sie da sind (max 10s Wartezeit pro App)

Monitor-Layout: linker Bildschirm x=-1920, rechter x=0. Beide 1920×1080.

---

## Begrüßungs-MP3s

`assets/greetings/greeting_0/1/2.mp3` — ElevenLabs, Stimme: Felix Serenitas.
`assets/greetings/index.txt` — enthält `0`, `1` oder `2`.

Neue MP3s generieren:
```powershell
python scripts/generate-greetings.py
```

---

## config.json (gitignored)

```json
{
  "elevenlabs_api_key": "...",
  "elevenlabs_voice_id": "...",
  "workspace_path": "C:\\Users\\Bally\\...",
  "spotify_track": "spotify:track:..."
}
```
