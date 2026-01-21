# Enterprise AI Assistant - Startup Script v4
# Next.js + FastAPI - Tamamen izole başlatma
# Güncelleme: Ocak 2026

$ProjectPath = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
$LogFile = "$ProjectPath\startup_log.txt"
$venvPython = "$ProjectPath\venv\Scripts\python.exe"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $LogFile -Append
    Write-Host "$timestamp - $Message"
}

try {
    Write-Log "=========================================="
    Write-Log "=== Enterprise AI Startup v4 ==="
    Write-Log "=========================================="
    
    Set-Location -Path $ProjectPath
    
    # Python venv kontrolü
    if (-not (Test-Path $venvPython)) {
        Write-Log "HATA: Python venv bulunamadi: $venvPython"
        exit 1
    }
    
    # Ortam değişkenlerini ayarla
    $env:HF_HUB_OFFLINE = "1"
    $env:TRANSFORMERS_OFFLINE = "1"
    $env:ANONYMIZED_TELEMETRY = "false"
    $env:PYTHONUNBUFFERED = "1"
    
    Write-Log "run.py başlatılıyor..."
    
    # run.py'yi çalıştır - tüm servisleri yönetir
    & $venvPython run.py
    
    Write-Log "=========================================="
    Write-Log "Servisler kapatıldı"
    Write-Log "=========================================="
    
} catch {
    Write-Log "KRITIK HATA: $_"
    exit 1
}
