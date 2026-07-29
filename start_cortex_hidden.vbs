Dim objShell
Set objShell = WScript.CreateObject("WScript.Shell")
Dim scriptDir
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = scriptDir
' Executa a Cortex a partir da pasta correta, mesmo quando o atalho é aberto noutro local.
objShell.Run "pythonw.exe """ & scriptDir & "\cortex_overlay.py""", 0, False
