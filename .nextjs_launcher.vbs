On Error Resume Next
Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "C:\Users\LENOVO\Desktop\Aktif Projeler\agenticmanagingsystem\frontend-next"

' Environment variables
Set objEnv = objShell.Environment("Process")
objEnv("NEXT_PUBLIC_API_URL") = "http://localhost:8001"
objEnv("PORT") = "3000"
objEnv("NODE_ENV") = "development"
objEnv("NEXT_TELEMETRY_DISABLED") = "1"

' Node.js ile Next.js başlat - 0 = gizli pencere
strNode = "C:\nvm4w\nodejs\node.exe"
strNext = "C:\Users\LENOVO\Desktop\Aktif Projeler\agenticmanagingsystem\frontend-next\node_modules\next\dist\bin\next"
strCmd = Chr(34) & strNode & Chr(34) & " " & Chr(34) & strNext & Chr(34) & " dev -p 3000"
objShell.Run strCmd, 0, False
