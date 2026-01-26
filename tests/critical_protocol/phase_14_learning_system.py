"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 14: LEARNING SYSTEM                  ║
║                                                                                 ║
║  Tests: learning_journey, learning_workspace, full_meta, adaptive learning    ║
║  Scope: All learning and educational features                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestResult:
    def __init__(self, name: str, passed: bool, error: str = None):
        self.name = name
        self.passed = passed
        self.error = error


class Phase14Learning:
    """Phase 14: Learning System Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 14: LEARNING SYSTEM"
        
    def print_header(self):
        print("\n" + "═" * 70)
        print(f"  {self.phase_name}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 70)
        
    def add_result(self, name: str, passed: bool, error: str = None):
        self.results.append(TestResult(name, passed, error))
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if error and not passed:
            print(f"         └─ Error: {error[:80]}...")
            
    async def test_learning_journey_system(self):
        """Test Learning Journey System module"""
        print("\n  [14.1] Learning Journey System Tests")
        print("  " + "-" * 40)
        
        try:
            from core.learning_journey_system import LearningPath, AIContentGenerator
            self.add_result("Learning Journey System Import", True)
        except ImportError:
            try:
                from core import learning_journey_system
                self.add_result("Learning Journey System Import (module)", True)
            except Exception as e:
                self.add_result("Learning Journey System Import", False, str(e))
                return
                
        try:
            from core.learning_journey_system import AIContentGenerator
            lj = AIContentGenerator()
            self.add_result("AIContentGenerator Instantiation", lj is not None)
        except Exception as e:
            self.add_result("AIContentGenerator Instantiation", False, str(e))
            
        try:
            from core.learning_journey_system import AIContentGenerator
            lj = AIContentGenerator()
            # Actual async methods in AIContentGenerator
            methods = ['generate_lesson_content', 'generate_quiz_content', 'generate_package', 'generate_learning_path']
            has_methods = any(hasattr(lj, m) for m in methods)
            self.add_result("AIContentGenerator Methods", has_methods)
        except Exception as e:
            self.add_result("AIContentGenerator Methods", False, str(e))
            
    async def test_learning_workspace(self):
        """Test Learning Workspace module"""
        print("\n  [14.2] Learning Workspace Tests")
        print("  " + "-" * 40)
        
        try:
            from core.learning_workspace import LearningWorkspaceManager
            self.add_result("Learning Workspace Import", True)
        except ImportError:
            try:
                from core import learning_workspace
                self.add_result("Learning Workspace Import (module)", True)
            except Exception as e:
                self.add_result("Learning Workspace Import", False, str(e))
                return
                
        try:
            from core.learning_workspace import LearningWorkspaceManager
            lw = LearningWorkspaceManager()
            self.add_result("LearningWorkspaceManager Instantiation", lw is not None)
        except Exception as e:
            self.add_result("LearningWorkspaceManager Instantiation", False, str(e))
            
    async def test_full_meta_learning(self):
        """Test Full Meta Learning module"""
        print("\n  [14.3] Full Meta Learning Tests")
        print("  " + "-" * 40)
        
        try:
            from core.full_meta_learning import FullMetaEngine
            self.add_result("Full Meta Learning Import", True)
        except ImportError:
            try:
                from core import full_meta_learning
                self.add_result("Full Meta Learning Import (module)", True)
            except Exception as e:
                self.add_result("Full Meta Learning Import", False, str(e))
                return
                
        try:
            from core.full_meta_learning import FullMetaEngine
            fml = FullMetaEngine()
            self.add_result("FullMetaEngine Instantiation", fml is not None)
        except Exception as e:
            self.add_result("FullMetaEngine Instantiation", False, str(e))
            
    async def test_full_meta_adaptive(self):
        """Test Full Meta Adaptive module"""
        print("\n  [14.4] Full Meta Adaptive Tests")
        print("  " + "-" * 40)
        
        try:
            from core.full_meta_adaptive import StruggleDetectionEngine
            self.add_result("Full Meta Adaptive Import", True)
        except ImportError:
            try:
                from core import full_meta_adaptive
                self.add_result("Full Meta Adaptive Import (module)", True)
            except Exception as e:
                self.add_result("Full Meta Adaptive Import", False, str(e))
                return
                
        try:
            from core.full_meta_adaptive import StruggleDetectionEngine
            al = StruggleDetectionEngine()
            self.add_result("StruggleDetectionEngine Instantiation", al is not None)
        except Exception as e:
            self.add_result("StruggleDetectionEngine Instantiation", False, str(e))
            
    async def test_learning_api(self):
        """Test Learning API Endpoints"""
        print("\n  [14.5] Learning API Tests")
        print("  " + "-" * 40)
        
        try:
            from api.learning_endpoints import router as learning_router
            self.add_result("Learning Endpoints Import", True)
        except ImportError:
            try:
                from api import learning_endpoints
                self.add_result("Learning Endpoints Import (module)", True)
            except Exception as e:
                self.add_result("Learning Endpoints Import", False, str(e))
                return
                
    async def test_learning_premium_features(self):
        """Test Learning Premium Features"""
        print("\n  [14.6] Learning Premium Features Tests")
        print("  " + "-" * 40)
        
        try:
            from core.learning_premium_features import AITutor
            self.add_result("Learning Premium Features Import", True)
        except ImportError:
            try:
                from core import learning_premium_features
                self.add_result("Learning Premium Features Import (module)", True)
            except Exception as e:
                self.add_result("Learning Premium Features Import", False, str(e))
                return
                
        try:
            from core.learning_premium_features import AITutor
            cg = AITutor()
            self.add_result("AITutor Instantiation", cg is not None)
        except Exception as e:
            self.add_result("AITutor Instantiation", False, str(e))
            
    async def test_learning_advanced_features(self):
        """Test Learning Advanced Features"""
        print("\n  [14.7] Learning Advanced Features Tests")
        print("  " + "-" * 40)
        
        try:
            from core.learning_advanced_features import LearningAdvancedFeaturesManager
            self.add_result("Learning Advanced Features Import", True)
        except ImportError:
            try:
                from core import learning_advanced_features
                self.add_result("Learning Advanced Features Import (module)", True)
            except Exception as e:
                self.add_result("Learning Advanced Features Import", False, str(e))
                return
                
        try:
            from core.learning_advanced_features import LearningAdvancedFeaturesManager
            ka = LearningAdvancedFeaturesManager()
            self.add_result("LearningAdvancedFeaturesManager Instantiation", ka is not None)
        except Exception as e:
            self.add_result("LearningAdvancedFeaturesManager Instantiation", False, str(e))
            
    async def test_full_meta_gamification(self):
        """Test Full Meta Gamification"""
        print("\n  [14.8] Full Meta Gamification Tests")
        print("  " + "-" * 40)
        
        try:
            from core.full_meta_gamification import SkillTreeEngine
            self.add_result("Full Meta Gamification Import", True)
        except ImportError:
            try:
                from core import full_meta_gamification
                self.add_result("Full Meta Gamification Import (module)", True)
            except Exception as e:
                self.add_result("Full Meta Gamification Import", False, str(e))
                return
                
        try:
            from core.full_meta_gamification import SkillTreeEngine
            pt = SkillTreeEngine()
            self.add_result("SkillTreeEngine Instantiation", pt is not None)
        except Exception as e:
            self.add_result("SkillTreeEngine Instantiation", False, str(e))
            
    async def run_all_tests(self):
        """Run all Phase 14 tests"""
        self.print_header()
        
        await self.test_learning_journey_system()
        await self.test_learning_workspace()
        await self.test_full_meta_learning()
        await self.test_full_meta_adaptive()
        await self.test_learning_api()
        await self.test_learning_premium_features()
        await self.test_learning_advanced_features()
        await self.test_full_meta_gamification()
        
        return self.get_summary()
        
    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print("\n" + "═" * 70)
        print(f"  {self.phase_name} - SUMMARY")
        print("═" * 70)
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ({100*passed/total:.1f}%)" if total > 0 else "  No tests run")
        print(f"  Failed: {failed}")
        
        if failed > 0:
            print(f"\n  Failed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"    ✗ {r.name}: {r.error[:60] if r.error else 'Unknown'}")
                    
        print("═" * 70 + "\n")
        
        return {
            "phase": self.phase_name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round(100 * passed / total, 1) if total > 0 else 0
        }


async def main():
    phase = Phase14Learning()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
