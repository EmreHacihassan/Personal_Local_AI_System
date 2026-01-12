Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strProjectPath = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
strPSScript = strProjectPath & "\startup.ps1"

' Log dosyasi olustur
Set logFile = objFSO.OpenTextFile(strProjectPath & "\startup_log.txt", 8, True)
logFile.WriteLine Now & " - Startup VBS baslatildi"

' Calisma dizinine git
objShell.CurrentDirectory = strProjectPath
logFile.WriteLine Now & " - Dizin ayarlandi: " & strProjectPath

' PowerShell script'i calistir
strCommand = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & strPSScript & """"
logFile.WriteLine Now & " - Komut: " & strCommand

objShell.Run strCommand, 0, False
logFile.WriteLine Now & " - Komut calistirildi"
logFile.Close