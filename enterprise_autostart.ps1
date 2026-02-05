# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  ENTERPRISE AI ASSISTANT - PREMIUM AUTO-START SCRIPT v5.0                    ║
# ║  Bilgisayar açılışında otomatik çalışır                                       ║
# ║  Güncelleme: Şubat 2026                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

param(
    [switch]$Silent,
    [switch]$SkipBrowser
)

# ============ CONFIGURATION ============
$ProjectPath = "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"
$LogFile = "$ProjectPath\logs\autostart_$(Get-Date -Format 'yyyy-MM-dd').log"
$venvPython = "$ProjectPath\.venv\Scripts\python.exe"
$venvPythonW = "$ProjectPath\.venv\Scripts\pythonw.exe"
$FrontendPath = "$ProjectPath\frontend-next"

# Ports
$BackendPort = 8001
$FrontendPort = 3000

# Timeouts (seconds)
$BackendTimeout = 60
$FrontendTimeout = 120

# ============ LOGGING ============
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $icons = @{
        "INFO"    = "ℹ️"
        "SUCCESS" = "✅"
        "WARNING" = "⚠️"
        "ERROR"   = "❌"
    }
    
    $logEntry = "$timestamp [$Level] $Message"
    
    # Ensure log directory exists
    $logDir = Split-Path -Path $LogFile -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # Write to file
    $logEntry | Out-File -FilePath $LogFile -Append -Encoding UTF8
    
    # Console output
    if (-not $Silent) {
        $icon = $icons[$Level]
        Write-Host "$icon $logEntry"
    }
}

# ============ PORT CHECKING ============
function Test-PortInUse {
    param([int]$Port)
    
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        return $null -ne $connection
    }
    catch {
        return $false
    }
}

function Stop-ProcessOnPort {
    param([int]$Port)
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Log "Port $Port üzerindeki process kapatılıyor: $($process.Name) (PID: $($process.Id))" "WARNING"
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Seconds 2
    }
    catch {
        Write-Log "Port $Port temizlenirken hata: $_" "WARNING"
    }
}

function Wait-ForPort {
    param(
        [int]$Port,
        [int]$Timeout,
        [string]$ServiceName
    )
    
    $elapsed = 0
    $interval = 2
    
    while ($elapsed -lt $Timeout) {
        if (Test-PortInUse -Port $Port) {
            Write-Log "$ServiceName başarıyla başlatıldı (Port: $Port)" "SUCCESS"
            return $true
        }
        
        Start-Sleep -Seconds $interval
        $elapsed += $interval
        
        if (-not $Silent -and ($elapsed % 10 -eq 0)) {
            Write-Host "   ⏳ $ServiceName bekleniyor... ($elapsed/$Timeout saniye)"
        }
    }
    
    Write-Log "$ServiceName başlatılamadı (Timeout: $Timeout saniye)" "ERROR"
    return $false
}

# ============ HEALTH CHECK ============
function Test-ServiceHealth {
    param(
        [string]$Url,
        [string]$ServiceName
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# ============ MAIN STARTUP ============
function Start-EnterpriseAI {
    Write-Log "═══════════════════════════════════════════════════════" "INFO"
    Write-Log "   ENTERPRISE AI ASSISTANT - PREMIUM STARTUP v5.0" "INFO"
    Write-Log "═══════════════════════════════════════════════════════" "INFO"
    
    # Check project path
    if (-not (Test-Path $ProjectPath)) {
        Write-Log "Proje dizini bulunamadı: $ProjectPath" "ERROR"
        return $false
    }
    
    Set-Location -Path $ProjectPath
    
    # Check Python venv
    if (-not (Test-Path $venvPython)) {
        Write-Log "Python venv bulunamadı: $venvPython" "ERROR"
        return $false
    }
    
    # Set environment variables
    $env:HF_HUB_OFFLINE = "1"
    $env:TRANSFORMERS_OFFLINE = "1"
    $env:ANONYMIZED_TELEMETRY = "false"
    $env:PYTHONUNBUFFERED = "1"
    $env:CHROMA_TELEMETRY = "false"
    
    Write-Log "Ortam değişkenleri ayarlandı (Offline mode aktif)" "INFO"
    
    # ===== BACKEND STARTUP =====
    Write-Log "Backend başlatılıyor (Port: $BackendPort)..." "INFO"
    
    # Clean port if in use
    if (Test-PortInUse -Port $BackendPort) {
        Write-Log "Port $BackendPort kullanımda, temizleniyor..." "WARNING"
        Stop-ProcessOnPort -Port $BackendPort
    }
    
    # Start backend
    $backendProcess = Start-Process -FilePath $venvPythonW -ArgumentList "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", $BackendPort -WorkingDirectory $ProjectPath -PassThru -WindowStyle Hidden
    
    Write-Log "Backend process başlatıldı (PID: $($backendProcess.Id))" "INFO"
    
    # Wait for backend
    if (-not (Wait-ForPort -Port $BackendPort -Timeout $BackendTimeout -ServiceName "Backend API")) {
        Write-Log "Backend başlatılamadı!" "ERROR"
        return $false
    }
    
    # Verify backend health
    Start-Sleep -Seconds 3
    if (Test-ServiceHealth -Url "http://localhost:$BackendPort/health" -ServiceName "Backend") {
        Write-Log "Backend health check PASSED" "SUCCESS"
    }
    else {
        Write-Log "Backend health check FAILED (devam ediliyor)" "WARNING"
    }
    
    # ===== FRONTEND STARTUP =====
    Write-Log "Frontend başlatılıyor (Port: $FrontendPort)..." "INFO"
    
    # Clean port if in use
    if (Test-PortInUse -Port $FrontendPort) {
        Write-Log "Port $FrontendPort kullanımda, temizleniyor..." "WARNING"
        Stop-ProcessOnPort -Port $FrontendPort
    }
    
    # Check if npm exists
    $npmPath = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmPath) {
        Write-Log "npm bulunamadı! Node.js kurulu olmalı." "ERROR"
        return $false
    }
    
    # Start frontend
    $frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd /d `"$FrontendPath`" && npm run dev" -WorkingDirectory $FrontendPath -PassThru -WindowStyle Hidden
    
    Write-Log "Frontend process başlatıldı (PID: $($frontendProcess.Id))" "INFO"
    
    # Wait for frontend
    if (-not (Wait-ForPort -Port $FrontendPort -Timeout $FrontendTimeout -ServiceName "Frontend")) {
        Write-Log "Frontend başlatılamadı!" "ERROR"
        return $false
    }
    
    # ===== SUCCESS =====
    Write-Log "═══════════════════════════════════════════════════════" "SUCCESS"
    Write-Log "   TÜM SERVİSLER BAŞARIYLA BAŞLATILDI!" "SUCCESS"
    Write-Log "   Backend:  http://localhost:$BackendPort" "SUCCESS"
    Write-Log "   Frontend: http://localhost:$FrontendPort" "SUCCESS"
    Write-Log "═══════════════════════════════════════════════════════" "SUCCESS"
    
    # Open browser
    if (-not $SkipBrowser) {
        Start-Sleep -Seconds 3
        Start-Process "http://localhost:$FrontendPort"
        Write-Log "Tarayıcı açıldı" "INFO"
    }
    
    # Save PID file for later cleanup
    $pidInfo = @{
        backend_pid = $backendProcess.Id
        frontend_pid = $frontendProcess.Id
        started_at = (Get-Date).ToString("o")
    }
    $pidInfo | ConvertTo-Json | Out-File -FilePath "$ProjectPath\.run.pid.json" -Encoding UTF8
    
    return $true
}

# ============ EXECUTE ============
try {
    $success = Start-EnterpriseAI
    
    if ($success) {
        Write-Log "Startup tamamlandı" "SUCCESS"
        exit 0
    }
    else {
        Write-Log "Startup başarısız!" "ERROR"
        exit 1
    }
}
catch {
    Write-Log "KRİTİK HATA: $_" "ERROR"
    exit 1
}
