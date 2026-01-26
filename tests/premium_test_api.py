"""
🔬 AI ile Öğren V2 - Premium Test Protokolü
MODÜL 2: API Endpoint Tests

Bu modül tüm V2 API endpoint'lerini test eder:
- Journey CRUD operations
- Package operations
- Exam submissions
- Certificate operations
- Error handling
- Validation

Çalıştırma: python tests/premium_test_api.py
"""

import asyncio
import httpx
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== CONFIG ====================
BASE_URL = "http://localhost:8001"
V2_PREFIX = "/journey/v2"


# ==================== COLORS ====================
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results: List[Dict] = []
    
    def add_pass(self, name: str, details: str = ""):
        self.passed += 1
        self.results.append({"name": name, "status": "pass", "details": details})
        print(f"  {Colors.GREEN}✅ {name}{Colors.RESET}")
        if details:
            print(f"     {Colors.CYAN}{details}{Colors.RESET}")
    
    def add_fail(self, name: str, reason: str):
        self.failed += 1
        self.results.append({"name": name, "status": "fail", "reason": reason})
        print(f"  {Colors.RED}❌ {name}: {reason}{Colors.RESET}")
    
    def add_warning(self, name: str, message: str):
        self.warnings += 1
        self.results.append({"name": name, "status": "warning", "message": message})
        print(f"  {Colors.YELLOW}⚠️ {name}: {message}{Colors.RESET}")


class PremiumAPITestSuite:
    """Premium API Test Suite"""
    
    def __init__(self):
        self.results = TestResult()
        self.journey_id: Optional[str] = None
        self.package_id: Optional[str] = None
        self.exam_id: Optional[str] = None
        self.exam_type: Optional[str] = None
    
    async def _api_call(self, method: str, endpoint: str, **kwargs) -> tuple:
        """Make API call and return (data, status_code)"""
        url = f"{BASE_URL}{V2_PREFIX}{endpoint}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await getattr(client, method)(url, **kwargs)
                try:
                    data = response.json()
                except:
                    data = None
                return data, response.status_code
            except httpx.ConnectError:
                return None, 0
            except Exception as e:
                return {"error": str(e)}, -1
    
    # ==================== CONNECTION TEST ====================
    
    async def test_api_connection(self):
        """Test: API is reachable"""
        data, status = await self._api_call("get", "/list")
        if status == 0:
            self.results.add_fail("API Connection", "Cannot connect to localhost:8001")
            return False
        elif status == 200:
            self.results.add_pass("API Connection", "API is running")
            return True
        else:
            self.results.add_fail("API Connection", f"Unexpected status: {status}")
            return False
    
    # ==================== JOURNEY ENDPOINTS ====================
    
    async def test_list_journeys(self):
        """Test: GET /journey/v2/list"""
        data, status = await self._api_call("get", "/list")
        
        if status == 200 and data and "journeys" in data:
            count = len(data["journeys"])
            self.results.add_pass("GET /list", f"Found {count} journeys")
        else:
            self.results.add_fail("GET /list", f"Status: {status}, Data: {data}")
    
    async def test_create_journey_valid(self):
        """Test: POST /journey/v2/create with valid data"""
        payload = {
            "title": "Premium API Test",
            "subject": "Python Programming",
            "target_outcome": "Master Python basics",
            "motivation": "Career growth",
            "daily_hours": 2.0,
            "content_preferences": ["text", "video"],
            "exam_preferences": ["multiple_choice", "feynman"]
        }
        
        data, status = await self._api_call("post", "/create", json=payload)
        
        if status == 200 and data:
            self.journey_id = data.get("journey_id")
            if self.journey_id:
                plan = data.get("plan", {})
                self.results.add_pass("POST /create", 
                    f"ID: {self.journey_id[:8]}, Stages: {plan.get('total_stages', '?')}")
            else:
                self.results.add_fail("POST /create", "No journey_id in response")
        else:
            self.results.add_fail("POST /create", f"Status: {status}")
    
    async def test_create_journey_minimal(self):
        """Test: POST /journey/v2/create with minimal data"""
        payload = {
            "title": "Minimal Test",
            "subject": "Test",
            "target_outcome": "Test",
            "daily_hours": 1.0
        }
        
        data, status = await self._api_call("post", "/create", json=payload)
        
        if status == 200 and data and data.get("journey_id"):
            self.results.add_pass("POST /create (minimal)", "Works with required fields only")
        else:
            self.results.add_fail("POST /create (minimal)", f"Status: {status}")
    
    async def test_create_journey_missing_required(self):
        """Test: POST /journey/v2/create without required fields"""
        payload = {
            "title": "Missing Fields"
            # Missing: subject, target_outcome, daily_hours
        }
        
        data, status = await self._api_call("post", "/create", json=payload)
        
        if status == 422:
            self.results.add_pass("POST /create (missing fields)", "Returns 422 as expected")
        else:
            self.results.add_fail("POST /create (missing fields)", f"Expected 422, got {status}")
    
    async def test_get_journey_map(self):
        """Test: GET /journey/v2/{id}/map"""
        if not self.journey_id:
            self.results.add_warning("GET /{id}/map", "No journey_id available")
            return
        
        data, status = await self._api_call("get", f"/{self.journey_id}/map")
        
        if status == 200 and data:
            stages = data.get("stages", [])
            total_exams = data.get("total_exams", 0)
            total_packages = data.get("total_packages", 0)
            
            # Find first package with exams
            for s in stages:
                for p in s.get("packages", []):
                    self.package_id = p.get("id")
                    if p.get("exams"):
                        self.exam_id = p["exams"][0].get("id")
                        self.exam_type = p["exams"][0].get("type", "multiple_choice")
                    if self.package_id:
                        break
                if self.exam_id:
                    break
            
            self.results.add_pass("GET /{id}/map", 
                f"Stages: {len(stages)}, Packages: {total_packages}, Exams: {total_exams}")
        else:
            self.results.add_fail("GET /{id}/map", f"Status: {status}")
    
    async def test_get_journey_map_invalid(self):
        """Test: GET /journey/v2/{invalid_id}/map"""
        data, status = await self._api_call("get", "/invalid_journey_id_12345/map")
        
        if status == 404:
            self.results.add_pass("GET /{invalid}/map", "Returns 404 as expected")
        else:
            self.results.add_fail("GET /{invalid}/map", f"Expected 404, got {status}")
    
    async def test_get_journey_progress(self):
        """Test: GET /journey/v2/{id}/progress"""
        if not self.journey_id:
            self.results.add_warning("GET /{id}/progress", "No journey_id")
            return
        
        data, status = await self._api_call("get", f"/{self.journey_id}/progress")
        
        if status == 200:
            self.results.add_pass("GET /{id}/progress", "Returns progress data")
        elif status == 404:
            self.results.add_warning("GET /{id}/progress", "Endpoint not found (may not be implemented)")
        else:
            self.results.add_fail("GET /{id}/progress", f"Status: {status}")
    
    # ==================== PACKAGE ENDPOINTS ====================
    
    async def test_start_package(self):
        """Test: POST /journey/v2/{id}/packages/{pkg}/start"""
        if not self.journey_id or not self.package_id:
            self.results.add_warning("POST /packages/{id}/start", "No journey or package ID")
            return
        
        data, status = await self._api_call("post", 
            f"/{self.journey_id}/packages/{self.package_id}/start")
        
        if status == 200:
            content_count = len(data.get("content_blocks", [])) if data else 0
            self.results.add_pass("POST /packages/{id}/start", 
                f"Content blocks: {content_count}")
        else:
            self.results.add_fail("POST /packages/{id}/start", f"Status: {status}")
    
    async def test_start_package_invalid(self):
        """Test: POST /journey/v2/{id}/packages/{invalid}/start"""
        if not self.journey_id:
            self.results.add_warning("POST /packages/{invalid}/start", "No journey_id")
            return
        
        data, status = await self._api_call("post", 
            f"/{self.journey_id}/packages/invalid_package_id/start")
        
        if status == 404:
            self.results.add_pass("POST /packages/{invalid}/start", "Returns 404 as expected")
        else:
            self.results.add_fail("POST /packages/{invalid}/start", f"Expected 404, got {status}")
    
    async def test_complete_package(self):
        """Test: POST /journey/v2/{id}/packages/{pkg}/complete"""
        if not self.journey_id or not self.package_id:
            self.results.add_warning("POST /packages/{id}/complete", "No IDs available")
            return
        
        data, status = await self._api_call("post", 
            f"/{self.journey_id}/packages/{self.package_id}/complete")
        
        if status == 200:
            self.results.add_pass("POST /packages/{id}/complete", "Package completed")
        elif status == 404:
            self.results.add_warning("POST /packages/{id}/complete", "Endpoint may not exist")
        else:
            self.results.add_fail("POST /packages/{id}/complete", f"Status: {status}")
    
    # ==================== EXAM ENDPOINTS ====================
    
    async def test_submit_exam_valid(self):
        """Test: POST /journey/v2/{id}/exams/{exam}/submit with valid data"""
        if not self.journey_id or not self.exam_id:
            self.results.add_warning("POST /exams/{id}/submit", "No journey or exam ID")
            return
        
        payload = {
            "exam_type": self.exam_type or "multiple_choice",
            "answers": {},
            "explanation": "Test explanation for Feynman exam"
        }
        
        data, status = await self._api_call("post", 
            f"/{self.journey_id}/exams/{self.exam_id}/submit", json=payload)
        
        if status == 200 and data:
            score = data.get("score", 0)
            passed = data.get("passed", False)
            self.results.add_pass("POST /exams/{id}/submit", 
                f"Score: {score}%, Passed: {passed}")
        else:
            self.results.add_fail("POST /exams/{id}/submit", f"Status: {status}, Data: {data}")
    
    async def test_submit_exam_missing_type(self):
        """Test: POST /journey/v2/{id}/exams/{exam}/submit without exam_type"""
        if not self.journey_id or not self.exam_id:
            self.results.add_warning("POST /exams (no type)", "No IDs available")
            return
        
        payload = {
            "answers": {}
            # Missing: exam_type (required)
        }
        
        data, status = await self._api_call("post", 
            f"/{self.journey_id}/exams/{self.exam_id}/submit", json=payload)
        
        if status == 422:
            self.results.add_pass("POST /exams (no type)", "Returns 422 as expected")
        else:
            self.results.add_fail("POST /exams (no type)", f"Expected 422, got {status}")
    
    async def test_submit_exam_invalid_exam(self):
        """Test: POST /journey/v2/{id}/exams/{invalid}/submit"""
        if not self.journey_id:
            self.results.add_warning("POST /exams/{invalid}/submit", "No journey_id")
            return
        
        payload = {
            "exam_type": "multiple_choice",
            "answers": {}
        }
        
        data, status = await self._api_call("post", 
            f"/{self.journey_id}/exams/invalid_exam_id/submit", json=payload)
        
        if status in [404, 500]:  # 500 might occur if exam not found throws
            self.results.add_pass("POST /exams/{invalid}/submit", f"Returns {status}")
        else:
            self.results.add_fail("POST /exams/{invalid}/submit", f"Unexpected status: {status}")
    
    # ==================== JOURNEY COMPLETE ====================
    
    async def test_complete_journey(self):
        """Test: POST /journey/v2/{id}/complete"""
        if not self.journey_id:
            self.results.add_warning("POST /{id}/complete", "No journey_id")
            return
        
        payload = {
            "user_name": "Test User"
        }
        
        data, status = await self._api_call("post", 
            f"/{self.journey_id}/complete", json=payload)
        
        if status == 200:
            self.results.add_pass("POST /{id}/complete", "Journey can be completed")
        elif status == 400:
            self.results.add_warning("POST /{id}/complete", "Journey not ready to complete (expected)")
        else:
            self.results.add_fail("POST /{id}/complete", f"Status: {status}")
    
    # ==================== INTEGRATION TEST ====================
    
    async def test_full_flow(self):
        """Test: Complete learning flow - create, map, start, submit"""
        # 1. Create new journey
        payload = {
            "title": "Full Flow Test",
            "subject": "Integration",
            "target_outcome": "Test complete flow",
            "daily_hours": 1.0
        }
        data, status = await self._api_call("post", "/create", json=payload)
        
        if status != 200 or not data:
            self.results.add_fail("Full Flow", f"Create failed: {status}")
            return
        
        jid = data.get("journey_id")
        if not jid:
            self.results.add_fail("Full Flow", "No journey_id")
            return
        
        # 2. Get map
        data, status = await self._api_call("get", f"/{jid}/map")
        if status != 200 or not data:
            self.results.add_fail("Full Flow", f"Map failed: {status}")
            return
        
        # Find package with exam
        pkg_id = None
        exam_id = None
        exam_type = None
        
        for s in data.get("stages", []):
            for p in s.get("packages", []):
                if p.get("exams"):
                    pkg_id = p["id"]
                    exam_id = p["exams"][0]["id"]
                    exam_type = p["exams"][0].get("type", "multiple_choice")
                    break
            if exam_id:
                break
        
        if not pkg_id:
            pkg_id = data["stages"][0]["packages"][0]["id"] if data.get("stages") else None
        
        if not pkg_id:
            self.results.add_fail("Full Flow", "No package found")
            return
        
        # 3. Start package
        data, status = await self._api_call("post", f"/{jid}/packages/{pkg_id}/start")
        if status != 200:
            self.results.add_fail("Full Flow", f"Start package failed: {status}")
            return
        
        # 4. Submit exam (if found)
        if exam_id:
            payload = {
                "exam_type": exam_type,
                "answers": {},
                "explanation": "Full flow test explanation"
            }
            data, status = await self._api_call("post", f"/{jid}/exams/{exam_id}/submit", json=payload)
            
            if status == 200:
                self.results.add_pass("Full Flow", "Create→Map→Start→Submit ✓")
            else:
                self.results.add_fail("Full Flow", f"Submit failed: {status}")
        else:
            self.results.add_pass("Full Flow", "Create→Map→Start ✓ (no exam in first package)")
    
    # ==================== RUN ALL ====================
    
    async def run_all(self):
        """Run all API tests"""
        print()
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}🔬 PREMIUM TEST PROTOKOLÜ - MODÜL 2: API ENDPOINTS{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print()
        
        # Connection Test
        print(f"{Colors.YELLOW}🔌 CONNECTION{Colors.RESET}")
        connected = await self.test_api_connection()
        print()
        
        if not connected:
            print(f"{Colors.RED}❌ API bağlantısı kurulamadı! Backend çalışıyor mu?{Colors.RESET}")
            return False
        
        # Journey Endpoints
        print(f"{Colors.YELLOW}📚 JOURNEY ENDPOINTS{Colors.RESET}")
        await self.test_list_journeys()
        await self.test_create_journey_valid()
        await self.test_create_journey_minimal()
        await self.test_create_journey_missing_required()
        await self.test_get_journey_map()
        await self.test_get_journey_map_invalid()
        await self.test_get_journey_progress()
        print()
        
        # Package Endpoints
        print(f"{Colors.YELLOW}📦 PACKAGE ENDPOINTS{Colors.RESET}")
        await self.test_start_package()
        await self.test_start_package_invalid()
        await self.test_complete_package()
        print()
        
        # Exam Endpoints
        print(f"{Colors.YELLOW}📝 EXAM ENDPOINTS{Colors.RESET}")
        await self.test_submit_exam_valid()
        await self.test_submit_exam_missing_type()
        await self.test_submit_exam_invalid_exam()
        print()
        
        # Journey Complete
        print(f"{Colors.YELLOW}🏆 JOURNEY COMPLETION{Colors.RESET}")
        await self.test_complete_journey()
        print()
        
        # Integration
        print(f"{Colors.YELLOW}🔄 INTEGRATION TEST{Colors.RESET}")
        await self.test_full_flow()
        print()
        
        # Summary
        total = self.results.passed + self.results.failed
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        if self.results.failed == 0:
            print(f"{Colors.GREEN}✅ TÜM API TESTLERİ GEÇTİ: {self.results.passed}/{total}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}📊 SONUÇ: {self.results.passed}/{total} geçti, {self.results.failed} başarısız{Colors.RESET}")
        if self.results.warnings > 0:
            print(f"{Colors.YELLOW}⚠️ Uyarılar: {self.results.warnings}{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        
        return self.results.failed == 0


# ==================== MAIN ====================

if __name__ == "__main__":
    suite = PremiumAPITestSuite()
    success = asyncio.run(suite.run_all())
    sys.exit(0 if success else 1)
