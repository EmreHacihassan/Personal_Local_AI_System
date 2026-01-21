Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strProjectPath = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
strPythonW = strProjectPath & "\.venv\Scripts\pythonw.exe"
strRunPy = strProjectPath & "\run.py"

' Log dosyasi olustur
Set logFile = objFSO.OpenTextFile(strProjectPath & "\startup_log.txt", 8, True)
logFile.WriteLine Now & " - Startup VBS baslatildi (v5 - Tamamen Gizli)"

' Calisma dizinine git
objShell.CurrentDirectory = strProjectPath
logFile.WriteLine Now & " - Dizin ayarlandi: " & strProjectPath

' Environment variables ayarla
Set objEnv = objShell.Environment("Process")
objEnv("HF_HUB_OFFLINE") = "1"
objEnv("TRANSFORMERS_OFFLINE") = "1"

' pythonw.exe ile gizli calistir (hicbir pencere acilmaz)
strCommand = """" & strPythonW & """ """ & strRunPy & """"
logFile.WriteLine Now & " - Komut: " & strCommand

objShell.Run strCommand, 0, False
logFile.WriteLine Now & " - Proje gizli modda baslatildi"
logFile.Close