# Jarvis — Work Session Launch

$configPath = Join-Path $PSScriptRoot "..\config.json"
$config     = Get-Content $configPath | ConvertFrom-Json
$WORKSPACE  = $config.workspace_path

Add-Type -AssemblyName presentationCore
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinPos {
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int h2, bool r);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
}
"@

# Monitor layout
$leftX   = -1920; $leftY = 7
$rightX  = 0;     $rightY = 0
$screenW = 1920;  $screenH = 1080

# --- 1. Greeting MP3 in eigenem Prozess abspielen (läuft unabhängig, wird nicht abgebrochen) ---
$greetDir  = Join-Path $PSScriptRoot "..\assets\greetings"
$indexFile = Join-Path $greetDir "index.txt"
if (Test-Path $indexFile) {
    $idx = [int](Get-Content $indexFile -Raw).Trim()
    $mp3 = Join-Path $greetDir "greeting_$idx.mp3"
    if (Test-Path $mp3) {
        $mp3Uri = "file:///" + $mp3.Replace('\', '/')
        $audioScript = @"
Add-Type -AssemblyName presentationCore
`$p = New-Object System.Windows.Media.MediaPlayer
`$p.Open([Uri]('$mp3Uri'))
`$p.Play()
Start-Sleep -Seconds 30
`$p.Close()
"@
        Start-Process powershell -ArgumentList "-WindowStyle Hidden -Command $audioScript" -WindowStyle Hidden
    }
    Set-Content $indexFile (($idx + 1) % 3)
}

# --- 2. Alle Apps gleichzeitig starten ---
$vscodeExe = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe"
Start-Process $vscodeExe -ArgumentList "`"$WORKSPACE`""

$notionExe = "$env:LOCALAPPDATA\Programs\Notion\Notion.exe"
if (Test-Path $notionExe) { Start-Process $notionExe } else { Start-Process "notion://" }

Start-Process $config.spotify_track

# --- 3. Warten bis Fenster da sind (max 10s), dann snappen ---
function Wait-And-Snap($name, $x, $y, $w, $h) {
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline) {
        $proc = Get-Process -Name $name -ErrorAction SilentlyContinue |
                Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
        if ($proc) {
            [WinPos]::ShowWindow($proc.MainWindowHandle, 9) | Out-Null
            Start-Sleep -Milliseconds 200
            [WinPos]::MoveWindow($proc.MainWindowHandle, $x, $y, $w, $h, $true) | Out-Null
            return
        }
        Start-Sleep -Milliseconds 400
    }
}

# Kurz warten damit Apps starten können, dann parallel snappen
Start-Sleep -Seconds 2

# VS Code (AI OS) → linker Bildschirm fullscreen
Wait-And-Snap "Code"    $leftX  $leftY  $screenW          $screenH

# Notion → rechter Bildschirm links
Wait-And-Snap "Notion"  $rightX $rightY ($screenW / 2)    $screenH

# Spotify → rechter Bildschirm rechts
Wait-And-Snap "Spotify" ($rightX + $screenW / 2) $rightY ($screenW / 2) $screenH
