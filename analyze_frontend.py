"""
🔍 Frontend Analysis & Feature Detection
=========================================

Frontend'de hangi özelliklerin mevcut olduğunu ve 
hangilerinin eksik olduğunu analiz eder.

Author: Enterprise AI Assistant  
Version: 1.0.0
"""

import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from collections import defaultdict
from datetime import datetime

# Project paths
FRONTEND_PATH = Path("c:/Users/LENOVO/Desktop/Aktif Projeler/AgenticManagingSystem/frontend-next")
API_PATH = Path("c:/Users/LENOVO/Desktop/Aktif Projeler/AgenticManagingSystem/api")

print("🔍 Frontend Analysis & Feature Detection")
print("=" * 60)
print(f"Started: {datetime.now().isoformat()}")
print()


def scan_api_endpoints() -> Dict[str, List[str]]:
    """API endpoint'lerini tara."""
    endpoints = defaultdict(list)
    
    for py_file in API_PATH.glob("*.py"):
        if py_file.name.startswith("__"):
            continue
            
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            
            # Find router prefixes
            prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']+)["\']', content)
            prefix = prefix_match.group(1) if prefix_match else ""
            
            # Find route decorators
            route_patterns = [
                r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in route_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    method = match.group(1).upper()
                    path = match.group(2)
                    full_path = prefix + path if not path.startswith(prefix) else path
                    endpoints[py_file.stem].append(f"{method} {full_path}")
            
            # Find WebSocket routes
            ws_pattern = r'@router\.websocket\s*\(\s*["\']([^"\']+)["\']'
            for match in re.finditer(ws_pattern, content):
                path = match.group(1)
                full_path = prefix + path if not path.startswith(prefix) else path
                endpoints[py_file.stem].append(f"WS {full_path}")
                
        except Exception as e:
            print(f"  Warning: Could not parse {py_file.name}: {e}")
    
    return dict(endpoints)


def scan_frontend_api_calls() -> Dict[str, List[str]]:
    """Frontend'deki API çağrılarını tara."""
    api_calls = defaultdict(list)
    
    src_path = FRONTEND_PATH / "src"
    
    for tsx_file in src_path.rglob("*.tsx"):
        try:
            content = tsx_file.read_text(encoding="utf-8", errors="ignore")
            relative_path = tsx_file.relative_to(src_path)
            
            # Find fetch calls
            fetch_patterns = [
                r'fetch\s*\(\s*`[^`]*(/api/[^`]+)`',
                r'fetch\s*\(\s*["\'][^"\']*(/api/[^"\']+)["\']',
                r'API_BASE\s*\+\s*["\']([^"\']+)["\']',
                r'`\$\{API_BASE\}([^`]+)`',
            ]
            
            for pattern in fetch_patterns:
                for match in re.finditer(pattern, content):
                    api_path = match.group(1)
                    if api_path and not api_path.startswith("$"):
                        api_calls[str(relative_path)].append(api_path)
            
            # Find WebSocket connections
            ws_patterns = [
                r'new\s+WebSocket\s*\(\s*["\'][^"\']*(/api/[^"\']+)["\']',
                r'WebSocket\s*\(\s*`[^`]*(/api/[^`]+)`',
            ]
            
            for pattern in ws_patterns:
                for match in re.finditer(pattern, content):
                    ws_path = match.group(1)
                    if ws_path:
                        api_calls[str(relative_path)].append(f"WS:{ws_path}")
                        
        except Exception as e:
            pass
    
    return dict(api_calls)


def analyze_feature_coverage() -> Dict[str, Any]:
    """Özellik kapsama analizi."""
    
    # Backend feature keywords
    backend_features = {
        "vision": ["vision", "screen", "capture", "llava"],
        "computer_use": ["computer", "automation", "pyautogui", "desktop"],
        "voice": ["voice", "speech", "whisper", "tts", "stt"],
        "documents": ["document", "upload", "rag", "pdf"],
        "learning": ["learning", "flashcard", "quiz", "spaced"],
        "deep_scholar": ["deep-scholar", "deepscholar", "scholar"],
        "premium": ["premium", "integration"],
        "agents": ["agent", "orchestrator", "autonomous"],
    }
    
    # Frontend feature keywords
    frontend_features = defaultdict(lambda: {"found": False, "files": [], "calls": []})
    
    src_path = FRONTEND_PATH / "src"
    
    for tsx_file in src_path.rglob("*.tsx"):
        try:
            content = tsx_file.read_text(encoding="utf-8", errors="ignore").lower()
            relative_path = str(tsx_file.relative_to(src_path))
            
            for feature, keywords in backend_features.items():
                for keyword in keywords:
                    if keyword in content:
                        frontend_features[feature]["found"] = True
                        if relative_path not in frontend_features[feature]["files"]:
                            frontend_features[feature]["files"].append(relative_path)
                        break
                        
        except Exception:
            pass
    
    return dict(frontend_features)


def check_new_features() -> Dict[str, Dict]:
    """Yeni eklenen özelliklerin frontend desteğini kontrol et."""
    
    new_features = {
        "vision_api": {
            "backend_endpoints": [
                "/api/vision/status",
                "/api/vision/ask",
                "/api/vision/analyze",
                "/api/vision/capture",
            ],
            "description": "Real-time screen vision and AI analysis",
            "frontend_required": True,
        },
        "computer_use_api": {
            "backend_endpoints": [
                "/api/computer/status",
                "/api/computer/task",
                "/api/computer/approve",
                "/api/computer/emergency-stop",
            ],
            "description": "AI-controlled desktop automation with approval",
            "frontend_required": True,
        },
        "security_audit": {
            "backend_endpoints": [],
            "description": "Security hardening and audit logging",
            "frontend_required": False,
        },
    }
    
    # Check frontend for these features
    frontend_api_calls = scan_frontend_api_calls()
    all_frontend_calls = []
    for calls in frontend_api_calls.values():
        all_frontend_calls.extend(calls)
    
    results = {}
    
    for feature, info in new_features.items():
        found_endpoints = []
        missing_endpoints = []
        
        for endpoint in info["backend_endpoints"]:
            if any(endpoint in call for call in all_frontend_calls):
                found_endpoints.append(endpoint)
            else:
                missing_endpoints.append(endpoint)
        
        results[feature] = {
            "description": info["description"],
            "frontend_required": info["frontend_required"],
            "found_in_frontend": found_endpoints,
            "missing_in_frontend": missing_endpoints,
            "coverage": len(found_endpoints) / len(info["backend_endpoints"]) * 100 if info["backend_endpoints"] else 100,
        }
    
    return results


def generate_frontend_recommendations() -> List[Dict]:
    """Frontend için öneriler oluştur."""
    recommendations = []
    
    feature_status = check_new_features()
    
    for feature, status in feature_status.items():
        if status["frontend_required"] and status["coverage"] < 100:
            recommendations.append({
                "feature": feature,
                "priority": "HIGH" if status["coverage"] == 0 else "MEDIUM",
                "description": status["description"],
                "missing_endpoints": status["missing_in_frontend"],
                "recommendation": f"Add frontend component for {feature}",
            })
    
    return recommendations


def main():
    """Ana analiz fonksiyonu."""
    
    print("📡 1. Backend API Endpoints")
    print("-" * 40)
    api_endpoints = scan_api_endpoints()
    total_endpoints = 0
    for module, endpoints in sorted(api_endpoints.items()):
        count = len(endpoints)
        total_endpoints += count
        print(f"  {module}: {count} endpoints")
    print(f"  TOTAL: {total_endpoints} endpoints")
    
    print("\n🌐 2. Frontend API Calls")
    print("-" * 40)
    frontend_calls = scan_frontend_api_calls()
    unique_calls = set()
    for file, calls in frontend_calls.items():
        for call in calls:
            unique_calls.add(call)
    print(f"  Files with API calls: {len(frontend_calls)}")
    print(f"  Unique API calls: {len(unique_calls)}")
    
    print("\n🔧 3. Feature Coverage Analysis")
    print("-" * 40)
    coverage = analyze_feature_coverage()
    for feature, info in sorted(coverage.items()):
        status = "✅" if info["found"] else "❌"
        files_count = len(info["files"])
        print(f"  {status} {feature}: {files_count} files")
    
    print("\n🆕 4. New Features Frontend Status")
    print("-" * 40)
    new_features = check_new_features()
    for feature, status in new_features.items():
        coverage_pct = status["coverage"]
        icon = "✅" if coverage_pct == 100 else "⚠️" if coverage_pct > 0 else "❌"
        print(f"  {icon} {feature}: {coverage_pct:.0f}% coverage")
        if status["missing_in_frontend"]:
            print(f"      Missing: {', '.join(status['missing_in_frontend'][:3])}")
    
    print("\n📋 5. Recommendations")
    print("-" * 40)
    recommendations = generate_frontend_recommendations()
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. [{rec['priority']}] {rec['feature']}")
            print(f"      → {rec['recommendation']}")
    else:
        print("  ✅ No critical recommendations")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ANALYSIS SUMMARY")
    print("-" * 40)
    
    vision_status = new_features.get("vision_api", {})
    computer_status = new_features.get("computer_use_api", {})
    
    print(f"  Backend Endpoints: {total_endpoints}")
    print(f"  Frontend API Calls: {len(unique_calls)}")
    print(f"  Vision API Coverage: {vision_status.get('coverage', 0):.0f}%")
    print(f"  Computer Use Coverage: {computer_status.get('coverage', 0):.0f}%")
    
    # Determine overall status
    if vision_status.get("coverage", 0) == 0 and computer_status.get("coverage", 0) == 0:
        print("\n⚠️  New features need frontend components!")
        print("    Vision and Computer Use APIs are backend-only.")
        print("    Consider adding UI components for these features.")
    elif vision_status.get("coverage", 0) > 0 or computer_status.get("coverage", 0) > 0:
        print("\n🔄 Partial frontend integration detected.")
    else:
        print("\n✅ Good frontend-backend coverage!")
    
    print(f"\nCompleted: {datetime.now().isoformat()}")
    
    return {
        "api_endpoints": total_endpoints,
        "frontend_calls": len(unique_calls),
        "vision_coverage": vision_status.get("coverage", 0),
        "computer_use_coverage": computer_status.get("coverage", 0),
        "recommendations": len(recommendations),
    }


if __name__ == "__main__":
    result = main()
