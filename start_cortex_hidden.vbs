Dim objShell
Set objShell = WScript.CreateObject("WScript.Shell")
' Run the python script completely hidden
objShell.Run "pythonw.exe cortex_overlay.py", 0, False
