' Enterprise AI Assistant - Windows Startup Launcher
' Bu dosyayı shell:startup klasörüne kopyalayın
' Bilgisayar her açıldığında otomatik çalışır

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Project path
strProjectPath = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
strStartupScript = strProjectPath & "\enterprise_autostart.ps1"

' Check if script exists
If objFSO.FileExists(strStartupScript) Then
    ' Run PowerShell script silently (Hidden window)
    strCommand = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & strStartupScript & """ -Silent"
    objShell.Run strCommand, 0, False
Else
    MsgBox "Enterprise AI startup script bulunamadı: " & strStartupScript, vbCritical, "Başlatma Hatası"
End If

Set objShell = Nothing
Set objFSO = Nothing
