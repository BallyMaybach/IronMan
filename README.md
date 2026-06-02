# Jarvis — Clap Trigger

Double-clap to launch your work session. That's it.

## What it does

1. Jarvis sits silently in your system tray (grey dot = inactive)
2. Click the tray icon to activate (green dot = listening)
3. Clap twice → work session launches:
   - VS Code opens fullscreen on left monitor
   - Notion + Spotify snap to right monitor
   - A greeting MP3 plays

## Setup

**1. Install dependencies**
```
pip install -r requirements.txt
```

**2. Create your config**

Copy `config.example.json` to `config.json` and fill in your values:
```json
{
  "elevenlabs_api_key": "...",
  "elevenlabs_voice_id": "...",
  "workspace_path": "C:\\path\\to\\your\\workspace",
  "spotify_track": "spotify:track:..."
}
```

**3. Generate greeting MP3s** (one-time, requires ElevenLabs API key)
```
python scripts/generate-greetings.py
```

**4. Add to Windows startup**

Create a Task Scheduler task that runs on login:
- Program: `wscript.exe`
- Arguments: `"C:\...\scripts\start-jarvis.vbs"`
- Run only when user is logged on

## Calibration

If Jarvis triggers too easily or misses claps, run the calibration tool:
```
python scripts/calibrate.py
```

Then adjust `SPIKE_RATIO` and `HF_RATIO_MIN` in `scripts/clap-trigger.py` based on the output.

## Monitor layout

Default: left screen at x=−1920, right screen at x=0, both 1920×1080.
Adjust `$leftX`, `$rightX` in `scripts/launch-session.ps1` if your setup differs.

## Files

```
scripts/
  clap-trigger.py      — main script, runs in system tray
  launch-session.ps1   — opens all apps and snaps windows
  launch-hidden.vbs    — runs PS1 without a visible terminal
  start-jarvis.vbs     — starts clap-trigger.py silently (for Task Scheduler)
  generate-greetings.py— regenerate greeting MP3s via ElevenLabs
  calibrate.py         — microphone calibration tool
assets/greetings/
  greeting_0/1/2.mp3   — pre-generated voice greetings
  index.txt            — rotation index (0→1→2→0)
config.example.json    — config template (copy to config.json)
```
