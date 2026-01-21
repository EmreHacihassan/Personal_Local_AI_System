#!/usr/bin/env python3
"""
Frontend vs Backend API Analysis
================================
Frontend'de çağrılan API'ler ile backend'de mevcut API'lerin karşılaştırması.
"""

import os
import re
import requests
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

BASE_URL = "http://localhost:8001"

@dataclass
class EndpointInfo:
    """Endpoint bilgisi."""
    path: str
    method: str
    source: str  # 'frontend' or 'backend'
    file: str = ""
    line: int = 0

@dataclass
class AnalysisResult:
    """Analiz sonucu."""
    frontend_endpoints: List[EndpointInfo] = field(default_factory=list)
    backend_endpoints: List[EndpointInfo] = field(default_factory=list)
    missing_in_backend: List[EndpointInfo] = field(default_factory=list)
    missing_in_frontend: List[EndpointInfo] = field(default_factory=list)
    test_results: Dict[str, dict] = field(default_factory=dict)

def extract_frontend_api_calls(frontend_path: str) -> List[EndpointInfo]:
    """Frontend dosyalarından API çağrılarını çıkar."""
    endpoints = []
    patterns = [
        # apiGet, apiPost, apiPut, apiDelete calls
        r"api(Get|Post|Put|Delete)\(['\"`](/[^'\"` ]+)['\"`]",
        # fetch calls
        r"fetch\(['\"`]https?://[^/]+(/api[^'\"` ]+)['\"`]",
        # axios calls
        r"axios\.(get|post|put|delete)\(['\"`](/[^'\"` ]+)['\"`]",
    ]
    
    for root, dirs, files in os.walk(frontend_path):
        # Skip node_modules
        if 'node_modules' in root:
            continue
            
        for file in files:
            if file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        for line_num, line in enumerate(lines, 1):
                            for pattern in patterns:
                                matches = re.findall(pattern, line)
                                for match in matches:
                                    method = match[0].upper() if isinstance(match, tuple) else 'GET'
                                    path = match[1] if isinstance(match, tuple) else match
                                    
                                    # Normalize method
                                    method_map = {'GET': 'GET', 'POST': 'POST', 'PUT': 'PUT', 'DELETE': 'DELETE'}
                                    method = method_map.get(method, method)
                                    
                                    endpoints.append(EndpointInfo(
                                        path=path,
                                        method=method,
                                        source='frontend',
                                        file=filepath.replace(frontend_path, ''),
                                        line=line_num
                                    ))
                except Exception as e:
                    pass
                    
    return endpoints

def extract_backend_endpoints(api_path: str) -> List[EndpointInfo]:
    """Backend dosyalarından endpoint tanımlarını çıkar."""
    endpoints = []
    
    # Pattern for FastAPI decorators
    decorator_pattern = r"@(router|app)\.(get|post|put|delete|patch)\(['\"`](/[^'\"` ]+)['\"`]"
    prefix_pattern = r"router\s*=\s*APIRouter\([^)]*prefix\s*=\s*['\"`](/[^'\"` ]+)['\"`]"
    
    for root, dirs, files in os.walk(api_path):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        # Find prefix
                        prefix_match = re.search(prefix_pattern, content)
                        prefix = prefix_match.group(1) if prefix_match else ""
                        
                        for line_num, line in enumerate(lines, 1):
                            matches = re.findall(decorator_pattern, line)
                            for match in matches:
                                method = match[1].upper()
                                path = prefix + match[2]
                                
                                endpoints.append(EndpointInfo(
                                    path=path,
                                    method=method,
                                    source='backend',
                                    file=filepath.replace(api_path, ''),
                                    line=line_num
                                ))
                except Exception as e:
                    pass
                    
    return endpoints

def test_endpoint(method: str, path: str, test_params: dict = None) -> dict:
    """Endpoint'i test et."""
    url = BASE_URL + path
    result = {
        "status": None,
        "success": False,
        "error": None,
        "response_time": 0
    }
    
    try:
        import time
        start = time.time()
        
        if method == 'GET':
            resp = requests.get(url, timeout=10)
        elif method == 'POST':
            resp = requests.post(url, json=test_params or {}, timeout=10)
        elif method == 'PUT':
            resp = requests.put(url, json=test_params or {}, timeout=10)
        elif method == 'DELETE':
            resp = requests.delete(url, timeout=10)
        else:
            resp = requests.get(url, timeout=10)
            
        result["status"] = resp.status_code
        result["success"] = resp.status_code < 400
        result["response_time"] = round((time.time() - start) * 1000, 2)
        
        if not result["success"]:
            try:
                result["error"] = resp.json().get("detail", resp.text[:100])
            except:
                result["error"] = resp.text[:100]
                
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection refused"
    except Exception as e:
        result["error"] = str(e)
        
    return result

def analyze_and_report():
    """Analiz yap ve rapor oluştur."""
    print("=" * 80)
    print("🔍 FRONTEND vs BACKEND API ANALYSIS")
    print("=" * 80)
    
    # Paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    frontend_path = os.path.join(base_path, "frontend-next", "src")
    api_path = os.path.join(base_path, "api")
    
    # Extract endpoints
    print("\n📂 Extracting frontend API calls...")
    frontend_eps = extract_frontend_api_calls(frontend_path)
    print(f"   Found {len(frontend_eps)} API calls in frontend")
    
    print("\n📂 Extracting backend endpoints...")
    backend_eps = extract_backend_endpoints(api_path)
    print(f"   Found {len(backend_eps)} endpoints in backend")
    
    # Normalize paths (remove dynamic params for comparison)
    def normalize_path(path: str) -> str:
        # Remove dynamic segments like {id}, ${id}, etc
        path = re.sub(r'\{[^}]+\}', '{id}', path)
        path = re.sub(r'\$\{[^}]+\}', '{id}', path)
        return path
    
    # Create sets for comparison
    frontend_paths = set()
    for ep in frontend_eps:
        norm_path = normalize_path(ep.path)
        frontend_paths.add((ep.method, norm_path))
    
    backend_paths = set()
    backend_path_map = {}
    for ep in backend_eps:
        norm_path = normalize_path(ep.path)
        key = (ep.method, norm_path)
        backend_paths.add(key)
        backend_path_map[key] = ep
    
    # Find mismatches
    missing_in_backend = frontend_paths - backend_paths
    missing_in_frontend = backend_paths - frontend_paths
    matched = frontend_paths & backend_paths
    
    print("\n" + "=" * 80)
    print("📊 ANALYSIS RESULTS")
    print("=" * 80)
    
    print(f"\n✅ Matched endpoints: {len(matched)}")
    print(f"❌ Frontend calls missing in backend: {len(missing_in_backend)}")
    print(f"⚠️ Backend endpoints not used in frontend: {len(missing_in_frontend)}")
    
    if missing_in_backend:
        print("\n" + "-" * 80)
        print("❌ CRITICAL: Frontend API calls without backend endpoints")
        print("-" * 80)
        for method, path in sorted(missing_in_backend):
            print(f"   [{method}] {path}")
            # Find frontend files using this endpoint
            for ep in frontend_eps:
                if ep.method == method and normalize_path(ep.path) == path:
                    print(f"       └─ {ep.file}:{ep.line}")
    
    # Key endpoints to test
    print("\n" + "=" * 80)
    print("🧪 TESTING KEY ENDPOINTS")
    print("=" * 80)
    
    test_cases = [
        # Health & Status
        ("GET", "/health", "Health Check"),
        ("GET", "/api/health", "API Health"),
        ("GET", "/api/status", "Status"),
        ("GET", "/api/system/info", "System Info"),
        
        # Premium
        ("GET", "/api/premium/status", "Premium Status"),
        ("GET", "/api/premium/features", "Premium Features"),
        
        # Learning
        ("GET", "/api/learning/workspaces", "Workspaces List"),
        
        # RAG
        ("GET", "/api/rag/status", "RAG Status"),
        ("GET", "/api/rag/stats", "RAG Stats"),
        
        # Chat/Sessions
        ("GET", "/api/sessions", "Sessions"),
        ("GET", "/api/chat/sessions", "Chat Sessions"),
        
        # Documents
        ("GET", "/api/documents", "Documents"),
        
        # WebSocket Stats
        ("GET", "/api/ws/stats", "WebSocket Stats"),
        
        # Learning Premium Features
        ("POST", "/api/learning/visual/mindmap", "Visual Mindmap", {"topic": "Test", "content": "Test content for mindmap generation"}),
        ("POST", "/api/learning/multimedia/slides", "Multimedia Slides", {"topic": "Test", "content": "Test content for slides generation"}),
        ("POST", "/api/learning/linking/prerequisites", "Linking Prerequisites", {"topic": "Python", "content": "Programming language basics"}),
    ]
    
    results = []
    for test in test_cases:
        method = test[0]
        path = test[1]
        name = test[2]
        params = test[3] if len(test) > 3 else None
        
        result = test_endpoint(method, path, params)
        status_icon = "✅" if result["success"] else "❌"
        status_code = result["status"] or "N/A"
        
        print(f"   {status_icon} [{method}] {path}")
        print(f"       └─ Status: {status_code}, Time: {result['response_time']}ms")
        if result["error"]:
            print(f"       └─ Error: {result['error'][:60]}")
        
        results.append({
            "name": name,
            "method": method,
            "path": path,
            "success": result["success"],
            "status": status_code,
            "time": result["response_time"],
            "error": result["error"]
        })
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print("\n" + "=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print(f"\n   API Tests: {successful}/{total} successful ({(successful/total)*100:.1f}%)")
    print(f"   Matched Endpoints: {len(matched)}")
    print(f"   Missing in Backend: {len(missing_in_backend)}")
    
    if len(missing_in_backend) > 0:
        print("\n⚠️ ACTION REQUIRED:")
        print("   The following frontend API calls need backend endpoints:")
        for method, path in sorted(missing_in_backend):
            print(f"      - [{method}] {path}")
    else:
        print("\n✅ All frontend API calls have matching backend endpoints!")
    
    # Failed tests
    failed = [r for r in results if not r["success"]]
    if failed:
        print("\n❌ FAILED TESTS:")
        for r in failed:
            print(f"   - {r['name']}: [{r['method']}] {r['path']} - {r['error'] or 'Unknown error'}")
    
    print("\n" + "=" * 80)
    
    return {
        "total_frontend_calls": len(frontend_eps),
        "total_backend_endpoints": len(backend_eps),
        "matched": len(matched),
        "missing_in_backend": len(missing_in_backend),
        "tests_passed": successful,
        "tests_total": total
    }

if __name__ == "__main__":
    try:
        result = analyze_and_report()
        
        # Exit code based on critical issues
        if result["missing_in_backend"] > 0 or result["tests_passed"] < result["tests_total"]:
            exit(1)
        exit(0)
    except Exception as e:
        print(f"\n❌ Analysis Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
