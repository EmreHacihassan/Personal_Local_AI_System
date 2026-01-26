Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strProjectPath = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
strPythonW = strProjectPath & "\.venv\Scripts\pythonw.exe"
strRunPy = strProjectPath & "\run.py"
strFrontendPath = strProjectPath & "\frontend-next"

' Log dosyasi olustur
Set logFile = objFSO.OpenTextFile(strProjectPath & "\startup_log.txt", 8, True)
logFile.WriteLine Now & " - Startup VBS baslatildi (v6 - Backend + Frontend-Next)"

' Calisma dizinine git
objShell.CurrentDirectory = strProjectPath
logFile.WriteLine Now & " - Dizin ayarlandi: " & strProjectPath

' Environment variables ayarla
Set objEnv = objShell.Environment("Process")
objEnv("HF_HUB_OFFLINE") = "1"
objEnv("TRANSFORMERS_OFFLINE") = "1"

' Eski surecler varsa sonlandir (sessiz)
On Error Resume Next
objShell.Run "taskkill /F /IM node.exe /FI ""WINDOWTITLE eq *npm*""", 0, True
objShell.Run "taskkill /F /IM pythonw.exe /FI ""WINDOWTITLE eq *run.py*""", 0, True
On Error GoTo 0

' Backend: pythonw.exe ile gizli calistir
strBackendCommand = """" & strPythonW & """ """ & strRunPy & """"
logFile.WriteLine Now & " - Backend Komut: " & strBackendCommand
objShell.Run strBackendCommand, 0, False
logFile.WriteLine Now & " - Backend baslatildi"

' 3 saniye bekle (backend hazir olsun)
WScript.Sleep 3000

' Frontend-Next: npm run dev gizli calistir
strFrontendCommand = "cmd.exe /c cd /d """ & strFrontendPath & """ && npm run dev"
logFile.WriteLine Now & " - Frontend Komut: " & strFrontendCommand
objShell.Run strFrontendCommand, 0, False
logFile.WriteLine Now & " - Frontend-Next baslatildi"

' 2 saniye bekle sonra tarayici ac
WScript.Sleep 2000
objShell.Run "http://localhost:3000", 1, False
logFile.WriteLine Now & " - Tarayici acildi (http://localhost:3000)"

logFile.WriteLine Now & " - Tam sistem gizli modda baslatildi (Backend + Frontend-Next)"
logFile.Close