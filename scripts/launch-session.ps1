# Jarvis — Launch Session (Windows)

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
$halfW = 960;    $halfH = 540

# 1. Start Jarvis server if not already running on port 8340
$serverRunning = Get-NetTCPConnection -LocalPort 8340 -ErrorAction SilentlyContinue
if (-not $serverRunning) {
    Start-Process python -ArgumentList "server.py" `
        -WorkingDirectory $WORKSPACE_PATH `
        -RedirectStandardOutput "$env:TEMP\jarvis_stdout.txt" `
        -RedirectStandardError "$env:TEMP\jarvis_stderr.txt" `
        -NoNewWindow
    Start-Sleep -Seconds 3
}

# 2. Open Chrome with Jarvis on the LEFT screen
Start-Process "chrome" -ArgumentList "--autoplay-policy=no-user-gesture-required http://localhost:8340"

# 3. Open VS Code on the RIGHT screen
$vscodePath = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe"
Start-Process $vscodePath -ArgumentList "`"$WORKSPACE_PATH`""

# 4. Open Spotify and immediately play the track
Start-Process $config.spotify_track

# 5. Open Notion
$notionExe = "$env:LOCALAPPDATA\Programs\Notion\Notion.exe"
if (Test-Path $notionExe) {
    Start-Process $notionExe
} else {
    Start-Process "notion://"
}

# 6. Wait for windows to open, then snap into position
Start-Sleep -Seconds 4

# Left screen: Jarvis (fullscreen)
$chrome = Get-Process -Name "chrome" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
Snap-Window $chrome $leftX $leftY $screenW $screenH

# Right screen top-left: VS Code
$vscode = Get-Process -Name "Code" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
Snap-Window $vscode $rightX $rightY $halfW $halfH

# Right screen top-right: Spotify
$spotify = Get-Process -Name "Spotify" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
Snap-Window $spotify ($rightX + $halfW) $rightY $halfW $halfH

# Right screen bottom-right: Notion
$notion = Get-Process -Name "Notion" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
Snap-Window $notion ($rightX + $halfW) ($rightY + $halfH) $halfW $halfH
