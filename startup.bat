@echo off
chcp 65001 >nul 2>&1
title Enterprise AI Assistant
echo ==========================================
echo Enterprise AI Assistant v3
echo ==========================================
echo.

cd /d "C:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem"

REM Venv kontrol
if not exist ".venv\Scripts\python.exe" (
    echo [HATA] Python venv bulunamadi!
    pause
    exit /b 1
)

REM Onceki process'leri temizle
echo Portlar temizleniyor...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 >nul

REM Python ile baslat
echo Sistem baslatiliyor...
echo.
".venv\Scripts\python.exe" run.py

REM Hata kontrolu
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Startup basarisiz!
    pause
)
