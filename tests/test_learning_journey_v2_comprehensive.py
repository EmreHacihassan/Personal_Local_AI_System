"""
🎓 Learning Journey V2 - Comprehensive Test Suite
Kapsamlı test paketi - Tüm V2 sistemini test eder
"""

import asyncio
import httpx
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== TEST CONFIG ====================
BASE_URL = "http://localhost:8001"
V2_PREFIX = "/journey/v2"


# ==================== COLORS ====================
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


# ==================== TEST SUITE ====================
class LearningJourneyV2TestSuite:
    """Comprehensive test suite for V2 Learning Journey"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results: List[Dict[str, Any]] = []
        self.journey_id: Optional[str] = None
        self.package_id: Optional[str] = None
        self.exam_id: Optional[str] = None
        
    def _log(self, message: str, color: str = Colors.RESET):
        print(f"{color}{message}{Colors.RESET}")
    
    def _success(self, test_name: str, details: str = ""):
        self.passed += 1
        self.results.append({"name": test_name, "status": "passed", "details": details})
        self._log(f"  ✅ {test_name}", Colors.GREEN)
        if details:
            self._log(f"     {details}", Colors.CYAN)
    
    def _failure(self, test_name: str, reason: str):
        self.failed += 1
        self.results.append({"name": test_name, "status": "failed", "reason": reason})
        self._log(f"  ❌ {test_name}: {reason}", Colors.RED)
    
    async def _api_call(self, method: str, endpoint: str, **kwargs) -> tuple[Optional[Dict], int]:
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
            except Exception as e:
                return None, 0
    
    # ==================== MODEL TESTS ====================
    
    async def test_models_import(self):
        """Test: Core models can be imported"""
        try:
            from core.learning_journey_v2 import (
                LearningGoal, CurriculumPlan, Stage, Package, Exam,
                Exercise, ContentBlock, ExamQuestion, Certificate,
                DifficultyLevel, ContentType, ExamType, ExerciseType,
                PackageType, StageStatus, PackageStatus
            )
            self._success("Models Import", "All 16 model classes imported")
        except ImportError as e:
            self._failure("Models Import", str(e))
    
    async def test_package_status_enum(self):
        """Test: PackageStatus has all required values"""
        try:
            from core.learning_journey_v2 import PackageStatus
            required = ["LOCKED", "AVAILABLE", "IN_PROGRESS", "PASSED", "FAILED", "COMPLETED", "NEEDS_REVIEW"]
            missing = [r for r in required if not hasattr(PackageStatus, r)]
            if missing:
                self._failure("PackageStatus Enum", f"Missing: {missing}")
            else:
                self._success("PackageStatus Enum", f"All {len(required)} values present")
        except Exception as e:
            self._failure("PackageStatus Enum", str(e))
    
    async def test_learning_goal_creation(self):
        """Test: LearningGoal can be created with required fields"""
        try:
            from core.learning_journey_v2 import LearningGoal
            goal = LearningGoal(
                title="Test Goal",
                subject="Mathematics",
                target_outcome="Master calculus",
                daily_hours=2.0
            )
            assert goal.id is not None
            assert goal.title == "Test Goal"
            self._success("LearningGoal Creation", f"ID: {goal.id[:8]}")
        except Exception as e:
            self._failure("LearningGoal Creation", str(e))
    
    async def test_exam_result_model(self):
        """Test: ExamResult model has correct fields"""
        try:
            from core.learning_journey_v2.exam_system import ExamResult, CriteriaScore
            from core.learning_journey_v2 import ExamType
            
            result = ExamResult(
                exam_id="test",
                user_id="user",
                exam_type=ExamType.MULTIPLE_CHOICE,
                total_score=80.0,
                max_possible_score=100.0,
                percentage=80.0,
                passed=True,
                attempt_number=1
            )
            assert hasattr(result, 'percentage')
            assert hasattr(result, 'criteria_scores')
            assert hasattr(result, 'to_dict')
            self._success("ExamResult Model", "All required fields present")
        except Exception as e:
            self._failure("ExamResult Model", str(e))
    
    # ==================== ORCHESTRATOR TESTS ====================
    
    async def test_orchestrator_singleton(self):
        """Test: Orchestrator singleton pattern works"""
        try:
            from core.learning_journey_v2 import get_learning_orchestrator
            o1 = get_learning_orchestrator()
            o2 = get_learning_orchestrator()
            assert o1 is o2
            self._success("Orchestrator Singleton", "Same instance returned")
        except Exception as e:
            self._failure("Orchestrator Singleton", str(e))
    
    async def test_journey_creation_direct(self):
        """Test: Journey can be created via orchestrator"""
        try:
            from core.learning_journey_v2 import LearningJourneyOrchestrator, LearningGoal
            
            o = LearningJourneyOrchestrator()
            goal = LearningGoal(
                title="Direct Test",
                subject="Python",
                target_outcome="Learn basics",
                daily_hours=1.0
            )
            
            jid = None
            async for event in o.create_journey(goal, 'test_user'):
                if event.type.value == 'journey_started':
                    jid = event.data['journey_id']
                    break
            
            if jid:
                state = o.active_journeys.get(jid)
                total_exams = sum(len(p.exams) for s in state.plan.stages for p in s.packages)
                self._success("Journey Creation Direct", f"ID: {jid[:8]}, Stages: {len(state.plan.stages)}, Exams: {total_exams}")
            else:
                self._failure("Journey Creation Direct", "No journey ID received")
        except Exception as e:
            self._failure("Journey Creation Direct", str(e))
    
    async def test_exam_submission_direct(self):
        """Test: Exam can be submitted via orchestrator"""
        try:
            from core.learning_journey_v2 import LearningJourneyOrchestrator, LearningGoal
            
            o = LearningJourneyOrchestrator()
            goal = LearningGoal(title="Exam Test", subject="Math", target_outcome="Test", daily_hours=1)
            
            jid = None
            async for event in o.create_journey(goal, 'test'):
                if event.type.value == 'journey_started':
                    jid = event.data['journey_id']
                    break
            
            # Find exam
            state = o.active_journeys.get(jid)
            exam_id = None
            for stage in state.plan.stages:
                for pkg in stage.packages:
                    if pkg.exams:
                        exam_id = pkg.exams[0].id
                        break
                if exam_id:
                    break
            
            if not exam_id:
                self._failure("Exam Submission Direct", "No exams found in journey")
                return
            
            result = await o.submit_exam(jid, exam_id, {"answers": {}}, 'test')
            assert hasattr(result, 'percentage')
            assert hasattr(result, 'passed')
            self._success("Exam Submission Direct", f"Percentage: {result.percentage}%")
        except Exception as e:
            self._failure("Exam Submission Direct", str(e))
    
    # ==================== API ENDPOINT TESTS ====================
    
    async def test_api_list_journeys(self):
        """Test: GET /journey/v2/list returns journey list"""
        data, status = await self._api_call("get", "/list")
        if status == 200 and data and "journeys" in data:
            self._success("API List Journeys", f"Found {len(data['journeys'])} journeys")
        else:
            self._failure("API List Journeys", f"Status: {status}")
    
    async def test_api_create_journey(self):
        """Test: POST /journey/v2/create creates new journey"""
        payload = {
            "title": "API Test Journey",
            "subject": "Python Programming",
            "target_outcome": "Master Python",
            "daily_hours": 2.0
        }
        data, status = await self._api_call("post", "/create", json=payload)
        
        if status == 200 and data:
            self.journey_id = data.get("journey_id")
            if self.journey_id:
                self._success("API Create Journey", f"ID: {self.journey_id[:8]}")
            else:
                self._failure("API Create Journey", "No journey_id in response")
        else:
            self._failure("API Create Journey", f"Status: {status}")
    
    async def test_api_get_map(self):
        """Test: GET /journey/v2/{id}/map returns stage map"""
        if not self.journey_id:
            self._failure("API Get Map", "No journey_id available")
            return
        
        data, status = await self._api_call("get", f"/{self.journey_id}/map")
        
        if status == 200 and data:
            stages = data.get("stages", [])
            total_exams = data.get("total_exams", 0)
            
            # Find first package with exams
            for s in stages:
                for p in s.get("packages", []):
                    if p.get("exams"):
                        self.package_id = p["id"]
                        self.exam_id = p["exams"][0]["id"]
                        break
                if self.exam_id:
                    break
            
            self._success("API Get Map", f"Stages: {len(stages)}, Total Exams: {total_exams}")
        else:
            self._failure("API Get Map", f"Status: {status}")
    
    async def test_api_start_package(self):
        """Test: POST /journey/v2/{id}/packages/{pkg}/start works"""
        if not self.journey_id or not self.package_id:
            self._failure("API Start Package", "No journey or package ID")
            return
        
        data, status = await self._api_call("post", f"/{self.journey_id}/packages/{self.package_id}/start")
        
        if status == 200:
            self._success("API Start Package", f"Package: {self.package_id[:8]}")
        else:
            self._failure("API Start Package", f"Status: {status}")
    
    async def test_api_submit_exam(self):
        """Test: POST /journey/v2/{id}/exams/{exam}/submit works"""
        if not self.journey_id or not self.exam_id:
            self._failure("API Submit Exam", "No journey or exam ID available")
            return
        
        payload = {
            "exam_type": "multiple_choice",
            "answers": {},
            "explanation": "Test submission"
        }
        data, status = await self._api_call("post", f"/{self.journey_id}/exams/{self.exam_id}/submit", json=payload)
        
        if status == 200 and data:
            score = data.get("score", 0)
            passed = data.get("passed", False)
            self._success("API Submit Exam", f"Score: {score}%, Passed: {passed}")
        else:
            self._failure("API Submit Exam", f"Status: {status}, Data: {data}")
    
    async def test_api_invalid_journey(self):
        """Test: Invalid journey ID returns 404"""
        data, status = await self._api_call("get", "/invalid_journey_id/map")
        if status == 404:
            self._success("API Invalid Journey", "Returns 404 as expected")
        else:
            self._failure("API Invalid Journey", f"Expected 404, got {status}")
    
    async def test_api_invalid_package(self):
        """Test: Invalid package ID returns 404"""
        if not self.journey_id:
            self._failure("API Invalid Package", "No journey_id")
            return
        
        data, status = await self._api_call("post", f"/{self.journey_id}/packages/invalid_pkg_id/start")
        if status == 404:
            self._success("API Invalid Package", "Returns 404 as expected")
        else:
            self._failure("API Invalid Package", f"Expected 404, got {status}")
    
    # ==================== INTEGRATION TESTS ====================
    
    async def test_full_learning_flow(self):
        """Test: Complete learning flow - create, start, submit"""
        try:
            # 1. Create journey
            payload = {"title": "Flow Test", "subject": "Test", "target_outcome": "Complete flow", "daily_hours": 1}
            data, status = await self._api_call("post", "/create", json=payload)
            
            if status != 200 or not data:
                self._failure("Full Learning Flow", f"Create failed: {status}")
                return
            
            jid = data.get("journey_id")
            if not jid:
                self._failure("Full Learning Flow", "No journey_id")
                return
            
            # 2. Get map and find exam
            data, status = await self._api_call("get", f"/{jid}/map")
            if status != 200:
                self._failure("Full Learning Flow", f"Map failed: {status}")
                return
            
            exam_id = None
            pkg_id = None
            for s in data.get("stages", []):
                for p in s.get("packages", []):
                    if p.get("exams"):
                        pkg_id = p["id"]
                        exam_id = p["exams"][0]["id"]
                        break
                if exam_id:
                    break
            
            if not exam_id:
                self._failure("Full Learning Flow", "No exams found")
                return
            
            # 3. Start package
            data, status = await self._api_call("post", f"/{jid}/packages/{pkg_id}/start")
            if status != 200:
                self._failure("Full Learning Flow", f"Start package failed: {status}")
                return
            
            # 4. Submit exam
            data, status = await self._api_call("post", f"/{jid}/exams/{exam_id}/submit", json={"exam_type": "multiple_choice", "answers": {}})
            if status == 200:
                self._success("Full Learning Flow", f"Complete: Create→Map→Start→Submit")
            else:
                self._failure("Full Learning Flow", f"Submit failed: {status}")
                
        except Exception as e:
            self._failure("Full Learning Flow", str(e))
    
    # ==================== RUN ALL TESTS ====================
    
    async def run_all(self):
        """Run all tests"""
        print()
        self._log("=" * 60, Colors.BLUE)
        self._log("🎓 LEARNING JOURNEY V2 - COMPREHENSIVE TEST SUITE", Colors.BOLD)
        self._log("=" * 60, Colors.BLUE)
        print()
        
        # Model Tests
        self._log("📦 MODEL TESTS", Colors.YELLOW)
        await self.test_models_import()
        await self.test_package_status_enum()
        await self.test_learning_goal_creation()
        await self.test_exam_result_model()
        print()
        
        # Orchestrator Tests
        self._log("🎯 ORCHESTRATOR TESTS", Colors.YELLOW)
        await self.test_orchestrator_singleton()
        await self.test_journey_creation_direct()
        await self.test_exam_submission_direct()
        print()
        
        # API Tests
        self._log("🌐 API ENDPOINT TESTS", Colors.YELLOW)
        await self.test_api_list_journeys()
        await self.test_api_create_journey()
        await self.test_api_get_map()
        await self.test_api_start_package()
        await self.test_api_submit_exam()
        await self.test_api_invalid_journey()
        await self.test_api_invalid_package()
        print()
        
        # Integration Tests
        self._log("🔄 INTEGRATION TESTS", Colors.YELLOW)
        await self.test_full_learning_flow()
        print()
        
        # Summary
        total = self.passed + self.failed
        self._log("=" * 60, Colors.BLUE)
        if self.failed == 0:
            self._log(f"✅ ALL TESTS PASSED: {self.passed}/{total}", Colors.GREEN)
        else:
            self._log(f"📊 RESULTS: {self.passed}/{total} passed, {self.failed} failed", Colors.YELLOW)
        self._log("=" * 60, Colors.BLUE)
        
        return self.failed == 0


# ==================== MAIN ====================
if __name__ == "__main__":
    suite = LearningJourneyV2TestSuite()
    success = asyncio.run(suite.run_all())
    exit(0 if success else 1)
