#!/usr/bin/env python3
"""
Otomatik başlatma kısayolu oluştur - Eski frontend yöntemi
"""
import os
import subprocess
import sys

def create_startup_shortcut():
    """Windows Startup klasörüne kısayol oluştur"""
    startup_path = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EnterpriseAI.lnk")
    project_path = os.path.dirname(os.path.abspath(__file__))
    vbs_path = os.path.join(project_path, "startup.vbs")
    
    print(f"Startup path: {startup_path}")
    print(f"VBS path: {vbs_path}")
    print(f"VBS exists: {os.path.exists(vbs_path)}")
    
    # PowerShell komutu - eski frontend'deki gibi
    ps_command = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{startup_path}")
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = '"{vbs_path}"'
$Shortcut.WorkingDirectory = "{project_path}"
$Shortcut.Description = "Enterprise AI Assistant - Auto Start"
$Shortcut.WindowStyle = 7
$Shortcut.Save()
Write-Host "Shortcut created successfully!"
'''
    
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    
    exists = os.path.exists(startup_path)
    print(f"Shortcut exists after creation: {exists}")
    
    return exists

def create_task_scheduler():
    """Task Scheduler'a görev ekle (daha güvenilir)"""
    project_path = os.path.dirname(os.path.abspath(__file__))
    vbs_path = os.path.join(project_path, "startup.vbs")
    
    # Önce varsa sil
    subprocess.run(
        ["schtasks", "/Delete", "/TN", "EnterpriseAIAssistant", "/F"],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    
    # Yeni görev oluştur
    result = subprocess.run(
        [
            "schtasks", "/Create",
            "/TN", "EnterpriseAIAssistant",
            "/TR", f'wscript.exe "{vbs_path}"',
            "/SC", "ONLOGON",
            "/RL", "HIGHEST",
            "/F"
        ],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    
    print(f"Task Scheduler return code: {result.returncode}")
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    
    return result.returncode == 0

if __name__ == "__main__":
    print("=" * 60)
    print("ENTERPRISE AI - AUTOSTART KURULUMU")
    print("=" * 60)
    
    print("\n[1/2] Startup klasörüne kısayol oluşturuluyor...")
    startup_ok = create_startup_shortcut()
    
    print("\n[2/2] Task Scheduler'a görev ekleniyor...")
    task_ok = create_task_scheduler()
    
    print("\n" + "=" * 60)
    if startup_ok or task_ok:
        print("✅ Otomatik başlatma etkinleştirildi!")
        if startup_ok:
            print("   - Startup klasörü: OK")
        if task_ok:
            print("   - Task Scheduler: OK")
    else:
        print("❌ Otomatik başlatma kurulumu başarısız!")
    print("=" * 60)
