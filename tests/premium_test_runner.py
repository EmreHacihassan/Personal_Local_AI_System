"""
🔬 AI ile Öğren V2 - Premium Test Protokolü
MASTER RUNNER

Bu script tüm premium test modüllerini sırayla çalıştırır:
1. Backend Core Tests
2. API Endpoint Tests
3. Frontend Analysis

Çalıştırma: python tests/premium_test_runner.py
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Colors
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def run_test_module(module_name: str, script_path: str) -> dict:
    """Run a test module and capture results"""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}> {module_name}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    result = {
        "module": module_name,
        "success": False,
        "output": "",
        "error": ""
    }
    
    if not Path(script_path).exists():
        result["error"] = f"Script not found: {script_path}"
        print(f"{Colors.RED}X {result['error']}{Colors.RESET}")
        return result
    
    try:
        # Set PYTHONIOENCODING for proper Unicode handling
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(Path(script_path).parent.parent),
            env=env
        )
        
        result["output"] = proc.stdout
        result["error"] = proc.stderr
        result["success"] = proc.returncode == 0
        
        # Print output
        print(proc.stdout)
        if proc.stderr:
            print(f"{Colors.YELLOW}Stderr:{Colors.RESET}")
            print(proc.stderr)
            
    except subprocess.TimeoutExpired:
        result["error"] = "Test timed out after 120 seconds"
        print(f"{Colors.RED}X {result['error']}{Colors.RESET}")
    except Exception as e:
        result["error"] = str(e)
        print(f"{Colors.RED}X Error: {e}{Colors.RESET}")
    
    return result


def main():
    """Run all premium test modules"""
    start_time = datetime.now()
    
    print()
    print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}🔬 AI ile ÖĞREN V2 - PREMIUM TEST PROTOKOLÜ{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"Başlangıç: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_path = Path(__file__).parent
    
    # Define test modules
    modules = [
        ("MODÜL 1: Backend Core Tests", base_path / "premium_test_backend.py"),
        ("MODÜL 2: API Endpoint Tests", base_path / "premium_test_api.py"),
        ("MODÜL 3: Frontend Analysis", base_path / "premium_test_frontend.py"),
    ]
    
    results = []
    
    for name, script in modules:
        result = run_test_module(name, str(script))
        results.append(result)
    
    # Final Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print()
    print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}📊 GENEL ÖZET{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    
    success_count = sum(1 for r in results if r["success"])
    
    for r in results:
        status = f"{Colors.GREEN}✅ BAŞARILI{Colors.RESET}" if r["success"] else f"{Colors.RED}❌ BAŞARISIZ{Colors.RESET}"
        print(f"  {r['module']}: {status}")
    
    print()
    print(f"Toplam Süre: {duration:.1f} saniye")
    print(f"Başarılı: {success_count}/{len(results)}")
    
    if success_count == len(results):
        print(f"\n{Colors.GREEN}{'='*70}{Colors.RESET}")
        print(f"{Colors.GREEN}✅ TÜM PREMIUM TESTLER BAŞARIYLA GEÇTİ!{Colors.RESET}")
        print(f"{Colors.GREEN}{'='*70}{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{'='*70}{Colors.RESET}")
        print(f"{Colors.YELLOW}⚠️ BAZI TESTLER BAŞARISIZ - Detaylar için yukarıya bakın{Colors.RESET}")
        print(f"{Colors.YELLOW}{'='*70}{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
