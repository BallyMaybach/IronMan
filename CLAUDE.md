# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Was ist dieses Projekt

Work-Session-Launcher für Bally. Doppelklatschen → Begrüßungs-MP3 spielt ab → Claude Desktop App (links, fullscreen) + VS Code + Notion (rechts) + Spotify (minimiert) öffnen sich automatisch.

Der alte Jarvis-Voiceassistent (FastAPI + Claude Haiku + ElevenLabs TTS + Browser-Frontend) ist noch im Repo vorhanden aber **nicht mehr der primäre Use Case**.

---

## Clap-Trigger & Session-Start

`scripts/clap-trigger.py` läuft permanent im Hintergrund (Windows Task Scheduler, Task: `JarvisClapTrigger`). Erkennt zwei Klatscher innerhalb 1.2s. Startet dann `scripts/launch-session.ps1` via `scripts/launch-clap.vbs` (unsichtbar, kein Terminal-Fenster).

`launch-session.ps1` Ablauf bei Doppelklatschen:
1. Begrüßungs-MP3 abspielen (rotierend: 0→1→2→0→..., Index in `assets/greetings/index.txt`)
2. Claude Desktop App fullscreen auf linkem Bildschirm (x=-1920)
3. Notion links auf rechtem Bildschirm, VS Code rechts auf rechtem Bildschirm
4. Spotify starten und minimieren

Task manuell neustarten nach Script-Änderungen:
```powershell
Stop-ScheduledTask -TaskName "JarvisClapTrigger"
Start-ScheduledTask -TaskName "JarvisClapTrigger"
```

---

## Begrüßungs-MP3s

`assets/greetings/greeting_0.mp3`, `greeting_1.mp3`, `greeting_2.mp3` — pre-generiert mit ElevenLabs, Stimme: Felix Serenitas.

`assets/greetings/index.txt` — enthält `0`, `1` oder `2`, wird nach jedem Start inkrementiert.

Neue MP3s generieren (ElevenLabs API, einmalig):
```powershell
python scripts/generate-greetings.py
```

MP3-Texte und Voice-Settings in `generate-greetings.py` anpassen, dann neu generieren und Dateien ersetzen.

---

## Config (config.json)

Liegt im Projektstamm, ist gitignored:

```json
{
  "anthropic_api_key": "...",
  "elevenlabs_api_key": "...",
  "elevenlabs_voice_id": "...",
  "user_name": "Bally",
  "user_address": "Sir",
  "city": "Ebenhausen-Schäftlarn",
  "workspace_path": "C:\\Users\\Bally\\...",
  "spotify_track": "spotify:track:...",
  "obsidian_inbox_path": ""
}
```

---

## Jarvis Voice Server (legacy, noch funktionsfähig)

FastAPI-Server mit WebSocket, Claude Haiku, ElevenLabs TTS und Playwright-Browser-Tools.

Server starten (niemals direkt `python server.py` — Audio funktioniert dann nicht):
```powershell
Start-Process python -ArgumentList "server.py" `
    -WorkingDirectory "c:\Users\Bally\OneDrive\Desktop\BUSINESS\Jarvis Template\jarvis-voice-assistant-master" `
    -RedirectStandardOutput "$env:TEMP\jarvis_stdout.txt" `
    -RedirectStandardError "$env:TEMP\jarvis_stderr.txt" `
    -PassThru -NoNewWindow
```

Port beenden:
```powershell
Get-NetTCPConnection -LocalPort 8340 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

Dependencies:
```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Datenpfad (server.py)

```
Browser (Web Speech API) → WebSocket /ws → process_message()
  → Claude Haiku (max 400 tokens)
    → extract_action() — parst [ACTION:TYPE] am Ende der Antwort
      → synthesize_speech() — ElevenLabs TTS, chunked bei >250 Zeichen
        → ws.send_json({ type: "response", text, audio: base64 })
  → execute_action() — SEARCH / OPEN / BROWSE / SCREEN / NEWS
    → zweiter Claude Haiku-Call (max 250 tokens) → nochmal TTS
```

Actions werden bei `"Jarvis activate"` immer übersprungen. `extract_action()` trennt gesprochenen Text vom Action-Tag. Systemprompt anpassen: `build_system_prompt()` in `server.py`.

### Browser-Tools (browser_tools.py)

Playwright headless=False, globales Singleton (`_browser`, `_context`). `search_and_read()` lässt Seite offen, `visit()` schliesst sie.

### Frontend (frontend/)

Iron Man HUD: schwarz, Cyan/Blau (#00D4FF, #0080FF), Share Tech Mono. State Machine: `STANDBY ↔ LISTENING → PROCESSING → SPEAKING → STANDBY`. Konversationshistorie im Server (max 16 Nachrichten, verliert sich bei Restart).

### ElevenLabs Free Tier

Nur Premade Voices per API (z.B. Adam: `pNInz6obpgDQGcFmaJgB`). Library/Community-Voices → 402.
