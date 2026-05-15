# Work Session — Launch (Windows)

$configPath = Join-Path $PSScriptRoot "..\config.json"
$config = Get-Content $configPath | ConvertFrom-Json
$WORKSPACE_PATH = $config.workspace_path

Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinPos {
    [DllImport("user32.dll")]
    public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int W, int H, bool repaint);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

function Snap-Window($proc, $x, $y, $w, $h) {
    if ($proc -and $proc.MainWindowHandle -ne 0) {
        [WinPos]::ShowWindow($proc.MainWindowHandle, 9) | Out-Null
        Start-Sleep -Milliseconds 300
        [WinPos]::MoveWindow($proc.MainWindowHandle, $x, $y, $w, $h, $true) | Out-Null
    }
}

# Monitor layout: left screen (-1920,7), right screen (0,0)
$leftX  = -1920; $leftY  = 7
$rightX = 0;     $rightY = 0
$screenW = 1920; $screenH = 1080

# 1. Open Claude Desktop App on LEFT screen (fullscreen)
$claudeExe = "$env:LOCALAPPDATA\AnthropicClaude\claude.exe"
if (Test-Path $claudeExe) {
    Start-Process $claudeExe
} else {
    Start-Process "claude://"
}

# 2. Open VS Code on the RIGHT screen
$vscodePath = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe"
Start-Process $vscodePath -ArgumentList "`"$WORKSPACE_PATH`""

# 3. Open Spotify and immediately play the track
Start-Process $config.spotify_track

# 4. Open Notion (To-Dos)
$notionExe = "$env:LOCALAPPDATA\Programs\Notion\Notion.exe"
if (Test-Path $notionExe) {
    Start-Process $notionExe
} else {
    Start-Process "notion://"
}

# 5. Play rotating greeting MP3
$greetDir  = Join-Path $PSScriptRoot "..\assets\greetings"
$indexFile = Join-Path $greetDir "index.txt"
if (Test-Path $indexFile) {
    $idx = [int](Get-Content $indexFile -Raw).Trim()
    $mp3 = Join-Path $greetDir "greeting_$idx.mp3"
    if (Test-Path $mp3) {
        Add-Type -AssemblyName presentationCore
        $player = New-Object System.Windows.Media.MediaPlayer
        $player.Open([Uri]("file:///" + $mp3.Replace('\', '/')))
        $player.Play()
        Start-Sleep -Seconds 2
        $dur = [int]$player.NaturalDuration.TimeSpan.TotalSeconds + 2
        Start-Sleep -Seconds $dur
        $player.Close()
    }
    Set-Content $indexFile (($idx + 1) % 3)
}

# 6. Wait for windows to open, then snap into position
Start-Sleep -Seconds 4

# Left screen: Claude fullscreen
$claude = Get-Process -Name "claude" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
Snap-Window $claude $leftX $leftY $screenW $screenH

# Right screen left half: Notion
$notion = Get-Process -Name "Notion" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
Snap-Window $notion $rightX $rightY ($screenW / 2) ($screenH - 45)

# Right screen right half: VS Code
$vscode = Get-Process -Name "Code" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
Snap-Window $vscode ($rightX + $screenW / 2) $rightY ($screenW / 2) ($screenH - 45)

# Spotify: minimize (plays in background)
$spotify = Get-Process -Name "Spotify" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if ($spotify -and $spotify.MainWindowHandle -ne 0) {
    [WinPos]::ShowWindow($spotify.MainWindowHandle, 6) | Out-Null
}
