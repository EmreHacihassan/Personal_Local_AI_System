# Enterprise AI Assistant - Otomatik Başlatıcı (Backend + Yeni Frontend)
$project = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
$venv = "$project\.venv\Scripts\pythonw.exe"
$runpy = "$project\run.py"
$frontend = "$project\frontend-next"
$log = "$project\startup_log.txt"

# Eski süreçleri öldür
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*AgenticManagingSystem*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Backend başlat (sessiz)
Start-Process -FilePath $venv -ArgumentList $runpy -WindowStyle Hidden

# Frontend-next başlat (sessiz)
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd `"$frontend`" && npm run dev" -WindowStyle Hidden

# Logla
Add-Content -Path $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Otomatik başlatıcı çalıştı"
