# Enterprise AI Assistant - Robust Startup Script
# Log ve hata yakalama ile

$ProjectPath = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
$LogFile = "$ProjectPath\startup_log.txt"
$OllamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$venvPython = "$ProjectPath\venv\Scripts\python.exe"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $LogFile -Append
}

try {
    Write-Log "=== Enterprise AI Startup Basladi ==="
    
    # Dizine git
    Set-Location -Path $ProjectPath
    Write-Log "Dizin: $ProjectPath"
    
    # Ollama kontrolu ve baslatma
    Write-Log "Ollama kontrol ediliyor..."
    
    if (Test-Path $OllamaPath) {
        # Ollama zaten calisiyor mu?
        $ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
        
        if (-not $ollamaProcess) {
            Write-Log "Ollama baslatiliyor: $OllamaPath serve"
            Start-Process -FilePath $OllamaPath -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 8
            Write-Log "Ollama baslatildi"
        } else {
            Write-Log "Ollama zaten calisiyor"
        }
    } else {
        Write-Log "UYARI: Ollama bulunamadi: $OllamaPath"
    }
    
    # Python venv kontrolu
    if (-not (Test-Path $venvPython)) {
        Write-Log "HATA: Python venv bulunamadi: $venvPython"
        exit 1
    }
    Write-Log "Python venv bulundu: $venvPython"
    
    # API baslatma (arka planda)
    Write-Log "API baslatiliyor (port 8001)..."
    $apiProcess = Start-Process -FilePath $venvPython -ArgumentList "-m uvicorn api.main:app --host 0.0.0.0 --port 8001" -WorkingDirectory $ProjectPath -WindowStyle Hidden -PassThru
    Write-Log "API baslatildi (PID: $($apiProcess.Id))"
    Start-Sleep -Seconds 3
    
    # Frontend baslatma (arka planda)
    Write-Log "Frontend baslatiliyor (port 8501)..."
    $frontendProcess = Start-Process -FilePath $venvPython -ArgumentList "-m streamlit run frontend/app.py --server.port 8501 --server.headless true" -WorkingDirectory $ProjectPath -WindowStyle Hidden -PassThru
    Write-Log "Frontend baslatildi (PID: $($frontendProcess.Id))"
    Start-Sleep -Seconds 3
    
    # Tarayici ac
    Write-Log "Tarayici aciliyor..."
    Start-Process "http://localhost:8501"
    Write-Log "Tarayici acildi"
    
    Write-Log "=== Startup tamamlandi ==="
    
} catch {
    Write-Log "HATA: $_"
    exit 1
}
