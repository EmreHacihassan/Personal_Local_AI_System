"""
🔬 AI ile Öğren V2 - Premium Test Protokolü
MODÜL 1: Backend Core Tests

Bu modül backend core bileşenlerini test eder:
- Models & Enums
- Orchestrator
- Curriculum Planner
- Exam System
- Certificate System

Çalıştırma: python tests/premium_test_backend.py
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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


class PremiumBackendTestSuite:
    """Premium Backend Test Suite"""
    
    def __init__(self):
        self.results = TestResult()
    
    # ==================== MODULE 1: MODELS & ENUMS ====================
    
    async def test_models_import(self):
        """Test: All models can be imported"""
        try:
            from core.learning_journey_v2 import (
                LearningGoal, CurriculumPlan, Stage, Package, Exam,
                Exercise, Certificate, UserProgress, ContentBlock, ExamQuestion
            )
            self.results.add_pass("Models Import", "10 model classes imported")
        except ImportError as e:
            self.results.add_fail("Models Import", str(e))
    
    async def test_enums_import(self):
        """Test: All enums can be imported"""
        try:
            from core.learning_journey_v2 import (
                DifficultyLevel, ContentType, ExamType, ExerciseType,
                PackageType, StageStatus, PackageStatus
            )
            self.results.add_pass("Enums Import", "7 enums imported")
        except ImportError as e:
            self.results.add_fail("Enums Import", str(e))
    
    async def test_package_status_values(self):
        """Test: PackageStatus has all required values"""
        try:
            from core.learning_journey_v2 import PackageStatus
            required = ["LOCKED", "AVAILABLE", "IN_PROGRESS", "PASSED", "FAILED", "COMPLETED", "NEEDS_REVIEW"]
            missing = []
            for r in required:
                if not hasattr(PackageStatus, r):
                    missing.append(r)
            
            if missing:
                self.results.add_fail("PackageStatus Values", f"Missing: {missing}")
            else:
                self.results.add_pass("PackageStatus Values", f"All {len(required)} values present")
        except Exception as e:
            self.results.add_fail("PackageStatus Values", str(e))
    
    async def test_stage_status_values(self):
        """Test: StageStatus has all required values"""
        try:
            from core.learning_journey_v2 import StageStatus
            required = ["LOCKED", "AVAILABLE", "IN_PROGRESS", "COMPLETED", "MASTERED"]
            missing = [r for r in required if not hasattr(StageStatus, r)]
            
            if missing:
                self.results.add_fail("StageStatus Values", f"Missing: {missing}")
            else:
                self.results.add_pass("StageStatus Values", f"All {len(required)} values present")
        except Exception as e:
            self.results.add_fail("StageStatus Values", str(e))
    
    async def test_exam_type_values(self):
        """Test: ExamType has all required values"""
        try:
            from core.learning_journey_v2 import ExamType
            required = ["MULTIPLE_CHOICE", "FEYNMAN", "PROBLEM_SOLVING", "TEACH_BACK", "CONCEPT_MAP"]
            missing = [r for r in required if not hasattr(ExamType, r)]
            
            if missing:
                self.results.add_fail("ExamType Values", f"Missing: {missing}")
            else:
                self.results.add_pass("ExamType Values", f"All critical values present")
        except Exception as e:
            self.results.add_fail("ExamType Values", str(e))
    
    async def test_package_type_values(self):
        """Test: PackageType has all required values"""
        try:
            from core.learning_journey_v2 import PackageType
            required = ["LEARNING", "PRACTICE", "EXAM", "REVIEW", "CLOSURE", "INTRO"]
            missing = [r for r in required if not hasattr(PackageType, r)]
            
            if missing:
                self.results.add_fail("PackageType Values", f"Missing: {missing}")
            else:
                self.results.add_pass("PackageType Values", f"All {len(required)} values present")
        except Exception as e:
            self.results.add_fail("PackageType Values", str(e))
    
    async def test_learning_goal_creation(self):
        """Test: LearningGoal can be created"""
        try:
            from core.learning_journey_v2 import LearningGoal
            goal = LearningGoal(
                title="Test Goal",
                subject="Mathematics",
                target_outcome="Master calculus",
                daily_hours=2.0
            )
            assert goal.id is not None and len(goal.id) > 0
            assert goal.title == "Test Goal"
            assert goal.subject == "Mathematics"
            self.results.add_pass("LearningGoal Creation", f"ID: {goal.id}")
        except Exception as e:
            self.results.add_fail("LearningGoal Creation", str(e))
    
    async def test_learning_goal_to_dict(self):
        """Test: LearningGoal.to_dict() works"""
        try:
            from core.learning_journey_v2 import LearningGoal
            goal = LearningGoal(title="Test", subject="Math", target_outcome="Learn", daily_hours=1)
            d = goal.to_dict()
            assert isinstance(d, dict)
            assert "id" in d
            assert "title" in d
            assert d["title"] == "Test"
            self.results.add_pass("LearningGoal.to_dict()", "Returns valid dict")
        except Exception as e:
            self.results.add_fail("LearningGoal.to_dict()", str(e))
    
    async def test_package_to_dict(self):
        """Test: Package.to_dict() works"""
        try:
            from core.learning_journey_v2 import Package, PackageType, PackageStatus
            pkg = Package(
                stage_id="stage1",
                number=1,
                title="Test Package",
                type=PackageType.LEARNING,
                status=PackageStatus.AVAILABLE
            )
            d = pkg.to_dict()
            assert isinstance(d, dict)
            assert d["type"] == "learning"
            assert d["status"] == "available"
            self.results.add_pass("Package.to_dict()", "Enum values serialized correctly")
        except Exception as e:
            self.results.add_fail("Package.to_dict()", str(e))
    
    # ==================== MODULE 2: ORCHESTRATOR ====================
    
    async def test_orchestrator_import(self):
        """Test: Orchestrator can be imported"""
        try:
            from core.learning_journey_v2 import LearningJourneyOrchestrator, get_learning_orchestrator
            self.results.add_pass("Orchestrator Import", "Both class and getter imported")
        except ImportError as e:
            self.results.add_fail("Orchestrator Import", str(e))
    
    async def test_orchestrator_singleton(self):
        """Test: Orchestrator singleton pattern"""
        try:
            from core.learning_journey_v2 import get_learning_orchestrator
            o1 = get_learning_orchestrator()
            o2 = get_learning_orchestrator()
            if o1 is o2:
                self.results.add_pass("Orchestrator Singleton", "Same instance returned")
            else:
                self.results.add_fail("Orchestrator Singleton", "Different instances!")
        except Exception as e:
            self.results.add_fail("Orchestrator Singleton", str(e))
    
    async def test_orchestrator_create_journey(self):
        """Test: Orchestrator can create journey"""
        try:
            from core.learning_journey_v2 import LearningJourneyOrchestrator, LearningGoal
            
            o = LearningJourneyOrchestrator()
            goal = LearningGoal(
                title="Test Journey",
                subject="Python",
                target_outcome="Learn basics",
                daily_hours=1.0
            )
            
            jid = None
            event_count = 0
            async for event in o.create_journey(goal, 'test_user'):
                event_count += 1
                if event.type.value == 'journey_started':
                    jid = event.data.get('journey_id')
            
            if jid:
                state = o.active_journeys.get(jid)
                stages = len(state.plan.stages) if state and state.plan else 0
                total_exams = sum(len(p.exams) for s in state.plan.stages for p in s.packages) if state else 0
                self.results.add_pass("Orchestrator Create Journey", 
                    f"ID: {jid[:8]}, Stages: {stages}, Exams: {total_exams}, Events: {event_count}")
            else:
                self.results.add_fail("Orchestrator Create Journey", "No journey_id received")
        except Exception as e:
            self.results.add_fail("Orchestrator Create Journey", str(e))
    
    async def test_orchestrator_get_stage_map(self):
        """Test: get_stage_map returns correct structure"""
        try:
            from core.learning_journey_v2 import LearningJourneyOrchestrator, LearningGoal
            
            o = LearningJourneyOrchestrator()
            goal = LearningGoal(title="Map Test", subject="Math", target_outcome="Test", daily_hours=1)
            
            jid = None
            async for event in o.create_journey(goal, 'test'):
                if event.type.value == 'journey_started':
                    jid = event.data['journey_id']
                    break
            
            stage_map = o.get_stage_map(jid)
            
            if not stage_map:
                self.results.add_fail("Orchestrator get_stage_map", "Returned None")
                return
            
            # Validate structure
            required_keys = ["stages", "total_packages", "total_exams"]
            missing = [k for k in required_keys if k not in stage_map]
            
            if missing:
                self.results.add_fail("Orchestrator get_stage_map", f"Missing keys: {missing}")
            else:
                exam_count = sum(len(p.get('exams', [])) for s in stage_map['stages'] for p in s.get('packages', []))
                self.results.add_pass("Orchestrator get_stage_map", 
                    f"Stages: {len(stage_map['stages'])}, Exams in packages: {exam_count}")
        except Exception as e:
            self.results.add_fail("Orchestrator get_stage_map", str(e))
    
    async def test_orchestrator_start_package(self):
        """Test: start_package works"""
        try:
            from core.learning_journey_v2 import LearningJourneyOrchestrator, LearningGoal
            
            o = LearningJourneyOrchestrator()
            goal = LearningGoal(title="Pkg Test", subject="Math", target_outcome="Test", daily_hours=1)
            
            jid = None
            async for event in o.create_journey(goal, 'test'):
                if event.type.value == 'journey_started':
                    jid = event.data['journey_id']
                    break
            
            # Get first package
            state = o.active_journeys.get(jid)
            pkg_id = state.plan.stages[0].packages[0].id if state else None
            
            if not pkg_id:
                self.results.add_fail("Orchestrator start_package", "No package found")
                return
            
            events = []
            async for event in o.start_package(jid, pkg_id, 'test'):
                events.append(event)
            
            if events:
                self.results.add_pass("Orchestrator start_package", f"Generated {len(events)} events")
            else:
                self.results.add_warning("Orchestrator start_package", "No events generated")
        except Exception as e:
            self.results.add_fail("Orchestrator start_package", str(e))
    
    async def test_orchestrator_submit_exam(self):
        """Test: submit_exam works"""
        try:
            from core.learning_journey_v2 import LearningJourneyOrchestrator, LearningGoal
            
            o = LearningJourneyOrchestrator()
            goal = LearningGoal(title="Exam Test", subject="Math", target_outcome="Test", daily_hours=1)
            
            jid = None
            async for event in o.create_journey(goal, 'test'):
                if event.type.value == 'journey_started':
                    jid = event.data['journey_id']
                    break
            
            # Find first exam
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
                self.results.add_warning("Orchestrator submit_exam", "No exams found to test")
                return
            
            result = await o.submit_exam(jid, exam_id, {"answers": {}}, 'test')
            
            if hasattr(result, 'percentage') and hasattr(result, 'passed'):
                self.results.add_pass("Orchestrator submit_exam", 
                    f"Score: {result.percentage}%, Passed: {result.passed}")
            else:
                self.results.add_fail("Orchestrator submit_exam", "Invalid result object")
        except Exception as e:
            self.results.add_fail("Orchestrator submit_exam", str(e))
    
    # ==================== MODULE 3: EXAM SYSTEM ====================
    
    async def test_exam_system_import(self):
        """Test: ExamSystem can be imported"""
        try:
            from core.learning_journey_v2 import ExamSystem, ExamResult, get_exam_system
            self.results.add_pass("ExamSystem Import", "ExamSystem, ExamResult, getter imported")
        except ImportError as e:
            self.results.add_fail("ExamSystem Import", str(e))
    
    async def test_exam_result_model(self):
        """Test: ExamResult has all required fields"""
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
            
            required_attrs = ['exam_id', 'percentage', 'passed', 'criteria_scores', 'detailed_feedback', 'to_dict']
            missing = [a for a in required_attrs if not hasattr(result, a)]
            
            if missing:
                self.results.add_fail("ExamResult Model", f"Missing: {missing}")
            else:
                self.results.add_pass("ExamResult Model", "All required attributes present")
        except Exception as e:
            self.results.add_fail("ExamResult Model", str(e))
    
    async def test_evaluators_exist(self):
        """Test: All evaluators can be imported"""
        try:
            from core.learning_journey_v2 import (
                FeynmanExamEvaluator,
                MultipleChoiceEvaluator,
                ProblemSolvingEvaluator,
                TeachBackEvaluator,
                ConceptMapEvaluator
            )
            self.results.add_pass("Evaluators Import", "5 evaluators imported")
        except ImportError as e:
            self.results.add_fail("Evaluators Import", str(e))
    
    # ==================== MODULE 4: CURRICULUM PLANNER ====================
    
    async def test_curriculum_planner_import(self):
        """Test: CurriculumPlanner can be imported"""
        try:
            from core.learning_journey_v2 import CurriculumPlannerAgent, AgentThought, get_curriculum_planner
            self.results.add_pass("CurriculumPlanner Import", "Planner and AgentThought imported")
        except ImportError as e:
            self.results.add_fail("CurriculumPlanner Import", str(e))
    
    async def test_curriculum_creation(self):
        """Test: Curriculum can be created"""
        try:
            from core.learning_journey_v2 import CurriculumPlannerAgent, LearningGoal
            
            planner = CurriculumPlannerAgent()
            goal = LearningGoal(
                title="Curriculum Test",
                subject="Python",
                target_outcome="Learn Python",
                daily_hours=2.0
            )
            
            plan, thoughts = await planner.plan_curriculum(goal)
            
            if plan and plan.stages:
                total_pkgs = sum(len(s.packages) for s in plan.stages)
                total_exams = plan.total_exams
                self.results.add_pass("Curriculum Creation", 
                    f"Stages: {len(plan.stages)}, Packages: {total_pkgs}, Exams: {total_exams}")
            else:
                self.results.add_fail("Curriculum Creation", "No stages created")
        except Exception as e:
            self.results.add_fail("Curriculum Creation", str(e))
    
    # ==================== MODULE 5: CERTIFICATE SYSTEM ====================
    
    async def test_certificate_system_import(self):
        """Test: CertificateSystem can be imported"""
        try:
            from core.learning_journey_v2 import (
                CertificateGenerator, CertificateAnalytics, CertificateStats,
                get_certificate_generator, get_certificate_analytics
            )
            self.results.add_pass("Certificate Import", "All certificate classes imported")
        except ImportError as e:
            self.results.add_fail("Certificate Import", str(e))
    
    async def test_certificate_model(self):
        """Test: Certificate model works"""
        try:
            from core.learning_journey_v2 import Certificate
            
            # Model uses: user_id, journey_id, title, description, subject
            cert = Certificate(
                user_id="test",
                journey_id="journey1",
                title="Python Course Certificate",
                subject="Python",
                description="Completed Python course"
            )
            
            assert cert.id is not None
            assert cert.verification_code is not None
            d = cert.to_dict()
            assert isinstance(d, dict)
            
            self.results.add_pass("Certificate Model", f"Code: {cert.verification_code}")
        except Exception as e:
            self.results.add_fail("Certificate Model", str(e))
    
    # ==================== MODULE 6: CONTENT GENERATOR ====================
    
    async def test_content_generator_import(self):
        """Test: ContentGenerator can be imported"""
        try:
            from core.learning_journey_v2 import ContentGeneratorAgent, RAGContentEnhancer, get_content_generator
            self.results.add_pass("ContentGenerator Import", "Generator and enhancer imported")
        except ImportError as e:
            self.results.add_fail("ContentGenerator Import", str(e))
    
    # ==================== RUN ALL ====================
    
    async def run_all(self):
        """Run all backend tests"""
        print()
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}🔬 PREMIUM TEST PROTOKOLÜ - MODÜL 1: BACKEND CORE{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print()
        
        # Module 1: Models & Enums
        print(f"{Colors.YELLOW}📦 1. MODELS & ENUMS{Colors.RESET}")
        await self.test_models_import()
        await self.test_enums_import()
        await self.test_package_status_values()
        await self.test_stage_status_values()
        await self.test_exam_type_values()
        await self.test_package_type_values()
        await self.test_learning_goal_creation()
        await self.test_learning_goal_to_dict()
        await self.test_package_to_dict()
        print()
        
        # Module 2: Orchestrator
        print(f"{Colors.YELLOW}🎯 2. ORCHESTRATOR{Colors.RESET}")
        await self.test_orchestrator_import()
        await self.test_orchestrator_singleton()
        await self.test_orchestrator_create_journey()
        await self.test_orchestrator_get_stage_map()
        await self.test_orchestrator_start_package()
        await self.test_orchestrator_submit_exam()
        print()
        
        # Module 3: Exam System
        print(f"{Colors.YELLOW}📝 3. EXAM SYSTEM{Colors.RESET}")
        await self.test_exam_system_import()
        await self.test_exam_result_model()
        await self.test_evaluators_exist()
        print()
        
        # Module 4: Curriculum Planner
        print(f"{Colors.YELLOW}📚 4. CURRICULUM PLANNER{Colors.RESET}")
        await self.test_curriculum_planner_import()
        await self.test_curriculum_creation()
        print()
        
        # Module 5: Certificate System
        print(f"{Colors.YELLOW}🏆 5. CERTIFICATE SYSTEM{Colors.RESET}")
        await self.test_certificate_system_import()
        await self.test_certificate_model()
        print()
        
        # Module 6: Content Generator
        print(f"{Colors.YELLOW}✍️ 6. CONTENT GENERATOR{Colors.RESET}")
        await self.test_content_generator_import()
        print()
        
        # Summary
        total = self.results.passed + self.results.failed
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        if self.results.failed == 0:
            print(f"{Colors.GREEN}✅ TÜM BACKEND TESTLERİ GEÇTİ: {self.results.passed}/{total}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}📊 SONUÇ: {self.results.passed}/{total} geçti, {self.results.failed} başarısız{Colors.RESET}")
        if self.results.warnings > 0:
            print(f"{Colors.YELLOW}⚠️ Uyarılar: {self.results.warnings}{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        
        return self.results.failed == 0


# ==================== MAIN ====================

if __name__ == "__main__":
    suite = PremiumBackendTestSuite()
    success = asyncio.run(suite.run_all())
    sys.exit(0 if success else 1)
