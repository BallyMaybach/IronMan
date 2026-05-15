Set WshShell = CreateObject("WScript.Shell")
Dim scriptDir
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
Dim pyScript
pyScript = scriptDir & "clap-once.py"
WshShell.Run "pythonw """ & pyScript & """", 0, False
