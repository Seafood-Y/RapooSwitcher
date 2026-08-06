' Wrapper: run switch_to_linux.bat without showing a console window.
' Bind this .vbs to your hotkey (via AutoHotkey or PowerToys).
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & scriptDir & "\switch_to_linux.bat" & chr(34), 0, False
