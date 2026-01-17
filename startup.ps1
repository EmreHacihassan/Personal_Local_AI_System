# Enterprise AI Assistant - Startup Script v3
# Sifir sorun garantili baslatma scripti
# Guncelleme: Ocak 2026 - Tam port temizleme ve robust baslatma

$ProjectPath = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
$LogFile = "$ProjectPath\startup_log.txt"
$OllamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$venvPython = "$ProjectPath\venv\Scripts\python.exe"

# Sabit Portlar
$ApiPort = 8001
$FrontendPort = 8501

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $LogFile -Append
    Write-Host "$timestamp - $Message"
}

function Clear-Port {
    param([int]$Port)
    
    # netstat ile tum PID'leri bul
    $netstat = netstat -ano 2>$null | Select-String ":$Port\s+"
    
    $killed = @()
    foreach ($line in $netstat) {
        $parts = $line -split '\s+'
        $pid = $parts[-1]
        if ($pid -match '^\d+$' -and $pid -ne '0' -and $pid -notin $killed) {
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                $killed += $pid
                Write-Log "Port $Port - PID $pid durduruldu"
            } catch {}
        }
    }
    
    if ($killed.Count -gt 0) {
        Start-Sleep -Seconds 1
    }
    
    return $killed.Count -gt 0
}

function Test-PortFree {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Ensure-PortAvailable {
    param([int]$Port)
    
    if (Test-PortFree -Port $Port) {
        return $true
    }
    
    Write-Log "Port $Port mesgul, temizleniyor..."
    
    for ($i = 1; $i -le 3; $i++) {
        Clear-Port -Port $Port
        Start-Sleep -Milliseconds 500
        
        if (Test-PortFree -Port $Port) {
            Write-Log "Port $Port temizlendi"
            return $true
        }
    }
    
    Write-Log "UYARI: Port $Port temizlenemedi"
    return $false
}

function Test-ApiHealth {
    param([int]$MaxRetries = 30)
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$ApiPort/health" -TimeoutSec 3 -ErrorAction Stop
            if ($response.status -eq "healthy" -or $response.status -eq "degraded") {
                Write-Log "API hazir (deneme $i): $($response.status)"
                return $true
            }
        } catch {}
        
        if ($i % 5 -eq 0) {
            Write-Log "API bekleniyor... ($i/$MaxRetries)"
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Test-OllamaHealth {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 3 -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

try {
    Write-Log "=========================================="
    Write-Log "=== Enterprise AI Startup v3 ==="
    Write-Log "=========================================="
    
    Set-Location -Path $ProjectPath
    Write-Log "Dizin: $ProjectPath"
    
    # ===== PORTLARI TEMIZLE =====
    Write-Log "Portlar temizleniyor..."
    Ensure-PortAvailable -Port $ApiPort | Out-Null
    Ensure-PortAvailable -Port $FrontendPort | Out-Null
    
    # ===== OLLAMA =====
    Write-Log "Ollama kontrol ediliyor..."
    
    if (-not (Test-OllamaHealth)) {
        if (Test-Path $OllamaPath) {
            Write-Log "Ollama baslatiliyor..."
            Start-Process -FilePath $OllamaPath -ArgumentList "serve" -WindowStyle Hidden
            
            for ($i = 1; $i -le 15; $i++) {
                Start-Sleep -Seconds 1
                if (Test-OllamaHealth) {
                    Write-Log "Ollama hazir"
                    break
                }
            }
        } else {
            Write-Log "UYARI: Ollama bulunamadi"
        }
    } else {
        Write-Log "Ollama zaten calisiyor"
    }
    
    # ===== PYTHON VENV =====
    if (-not (Test-Path $venvPython)) {
        Write-Log "HATA: Python venv bulunamadi: $venvPython"
        exit 1
    }
    
    # ===== API =====
    Write-Log "API baslatiliyor (port $ApiPort)..."
    
    $apiProcess = Start-Process -FilePath $venvPython `
        -ArgumentList "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "$ApiPort", "--log-level", "warning" `
        -WorkingDirectory $ProjectPath `
        -WindowStyle Hidden `
        -PassThru
    
    Write-Log "API PID: $($apiProcess.Id)"
    
    # Health check
    Write-Log "API hazir olmasi bekleniyor..."
    if (Test-ApiHealth -MaxRetries 30) {
        Write-Log "API hazir!"
    } else {
        Write-Log "UYARI: API health check zaman asimi"
    }
    
    # ===== FRONTEND =====
    Write-Log "Frontend baslatiliyor (port $FrontendPort)..."
    
    $frontendProcess = Start-Process -FilePath $venvPython `
        -ArgumentList "-m", "streamlit", "run", "frontend/app.py", "--server.port", "$FrontendPort", "--server.headless", "true" `
        -WorkingDirectory $ProjectPath `
        -WindowStyle Hidden `
        -PassThru
    
    Write-Log "Frontend PID: $($frontendProcess.Id)"
    Start-Sleep -Seconds 3
    
    # ===== TARAYICI =====
    Start-Process "http://localhost:$FrontendPort"
    
    # ===== SONUC =====
    Write-Log "=========================================="
    Write-Log "BASLATMA TAMAMLANDI"
    Write-Log "Frontend: http://localhost:$FrontendPort"
    Write-Log "API: http://localhost:$ApiPort"
    Write-Log "API Docs: http://localhost:$ApiPort/docs"
    Write-Log "=========================================="
    
} catch {
    Write-Log "KRITIK HATA: $_"
    exit 1
}
