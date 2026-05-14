# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Was ist Jarvis

Persoenlicher KI-Assistent fuer Bally (angesprochen als "Sir"), Stadt Ebenhausen-Schäftlarn. Sprachsteuerung im Browser → FastAPI Backend → Claude Haiku → ElevenLabs TTS. Doppelklatschen-Trigger startet die Session automatisch.

---

## Server starten

```powershell
$proc = Start-Process python -ArgumentList "server.py" `
    -WorkingDirectory "c:\Users\Bally\OneDrive\Desktop\BUSINESS\Jarvis Template\jarvis-voice-assistant-master" `
    -RedirectStandardOutput "$env:TEMP\jarvis_stdout.txt" `
    -RedirectStandardError "$env:TEMP\jarvis_stderr.txt" `
    -PassThru -NoNewWindow
```

**Wichtig:** Niemals `python server.py` direkt im Terminal starten — Audio funktioniert dann nicht (Browser-Autoplay-Policy). Immer `-NoNewWindow` mit Redirect verwenden.

Server läuft auf **http://localhost:8340**. Port prüfen/beenden:
```powershell
Get-NetTCPConnection -LocalPort 8340 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

Dependencies installieren:
```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

---

## Architektur

### Datenpfad pro Spracheingabe

```
Browser (Web Speech API, de-DE, continuous=false)
  → Button-Klick → Mikrofon an
    → WebSocket /ws
      → process_message() in server.py
        → Claude Haiku (max 400 tokens)
          → extract_action() — parst [ACTION:TYPE] am Ende der Antwort
            → synthesize_speech() — ElevenLabs TTS, chunked bei >250 Zeichen
              → ws.send_json({ type: "response", text, audio: base64 })
                → Browser: AudioQueue → playNext() → enterStandby()
        → (falls Action, NICHT bei "activate") execute_action()
          → zweiter Claude Haiku-Call (max 250 tokens) zum Zusammenfassen
            → nochmal TTS + WebSocket
```

### Push-to-Talk / Standby-System (frontend/main.js)

State Machine: `STANDBY ↔ LISTENING → PROCESSING → SPEAKING → STANDBY`

- Beim Öffnen: `"Jarvis activate"` gesendet → Begrüßung wird abgespielt → automatisch `enterStandby()`
- Im Standby: Talk-Button sichtbar, kein Mikrofon aktiv
- Button-Klick → `enterListening()` → `recognition.start()` (einmalig, `continuous: false`)
- Nach einer Antwort: zurück zu `enterStandby()`, Button erscheint wieder
- Kein auto-restart des Mikrofons nach Antwort

Orb-Zustände: `standby` (sehr dunkel) → `listening` (pulsierend cyan) → `thinking` (pulsierend blau) → `speaking` (hell cyan, starker Glow)

### Actions-System (server.py)

Jarvis schreibt `[ACTION:TYP] payload` ans Ende seiner Antwort. `extract_action()` trennt den gesprochenen Text vom Action-Tag. **Actions werden bei "Jarvis activate" immer übersprungen** (serverseitig und per System-Prompt-Regel).

| Action | Was passiert |
|--------|-------------|
| `SEARCH` | DuckDuckGo → erstes Ergebnis lesen via Playwright |
| `OPEN` | URL in Standard-Browser öffnen (kein zweiter LLM-Call) |
| `BROWSE` | URL direkt besuchen und Inhalt lesen |
| `SCREEN` | Screenshot → Claude Vision → Beschreibung |
| `NEWS` | worldmonitor.app scrapen |

### Browser-Tools (browser_tools.py)

Playwright läuft **headless=False** (sichtbares Chromium-Fenster, kein Viewport). Die Browser-Instanz ist ein globales Singleton (`_browser`, `_context`) — wird beim ersten Aufruf gestartet, dann wiederverwendet. `search_and_read()` schliesst die Seite NICHT. `visit()` schliesst die Seite.

### Frontend-UI (frontend/)

Iron Man / Stark Industries HUD-Design: schwarzer Hintergrund, Cyan/Blau (#00D4FF, #0080FF), Share Tech Mono Font, Scanlines-Effekt. 3-Spalten-Layout:
- Links: Input Log (User-Transkript)
- Mitte: Arc Reactor (rotierenden Ringe + Orb) + Talk-Button
- Rechts: Jarvis Response

### Session-State

Konversationshistorie liegt in `conversations: dict[str, list]` (key = WebSocket-ID). Verliert sich bei Serverrestart oder Tab-Reload. Maximal 16 Nachrichten werden ans LLM uebergeben.

---

## Config (config.json)

Liegt im Projektstamm, ist gitignored. Felder:

```json
{
  "anthropic_api_key": "...",
  "elevenlabs_api_key": "...",
  "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
  "user_name": "Bally",
  "user_address": "Sir",
  "city": "Ebenhausen-Schäftlarn",
  "workspace_path": "C:\\Users\\Bally\\...",
  "spotify_track": "spotify:track:...",
  "obsidian_inbox_path": ""
}
```

`USER_NAME` und `USER_ADDRESS` werden in `build_system_prompt()` direkt als f-String-Variablen eingesetzt — bei Änderungen dort anpassen, nicht im Prompt hardcoden.

`obsidian_inbox_path`: wenn gesetzt, liest Jarvis offene Tasks aus `{path}/Tasks.md` (Zeilen mit `- [ ]`).

---

## Clap-Trigger & Autostart

`scripts/clap-trigger.py` läuft permanent im Hintergrund (Windows Task Scheduler, Task: `JarvisClapTrigger`). Erkennt zwei Klatscher innerhalb 1.2s. Startet dann `scripts/launch-session.ps1` via `scripts/launch-hidden.vbs` (unsichtbar, kein Terminal-Fenster).

`launch-session.ps1` bei Doppelklatschen:
- Jarvis-Server starten (falls Port 8340 frei)
- Chrome mit `http://localhost:8340` auf linkem Bildschirm (x=-1920, fullscreen)
- VS Code oben-links auf rechtem Bildschirm (x=0, y=0, 960×540)
- Spotify oben-rechts auf rechtem Bildschirm (x=960, y=0, 960×540)

Task manuell neustarten nach Script-Änderungen:
```powershell
Stop-ScheduledTask -TaskName "JarvisClapTrigger"
Start-ScheduledTask -TaskName "JarvisClapTrigger"
```

---

## Systemprompt anpassen

`server.py` → `build_system_prompt()`. Persönlichkeit, Anredeform, Begrüssungsverhalten und Action-Regeln sind dort als f-String definiert. Nach Änderungen Server neu starten.

---

## ElevenLabs-Hinweis

Free Tier (10k Zeichen/Monat): Nur **Premade Voices** (z.B. Adam: `pNInz6obpgDQGcFmaJgB`) funktionieren per API. Library/Community-Voices geben 402 zurück.
