"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 8: PREMIUM FEATURES                  ║
║                                                                                 ║
║  Tests: premium_features, deep_scholar, deep_scholar_premium modules          ║
║  Scope: Premium/advanced features and DeepScholar research system             ║
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


class Phase08PremiumFeatures:
    """Phase 8: Premium Features Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 8: PREMIUM FEATURES"
        
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
            
    async def test_premium_features(self):
        """Test Premium Features module"""
        print("\n  [8.1] Premium Features Tests")
        print("  " + "-" * 40)
        
        try:
            from core.premium_features import PremiumFeatures
            self.add_result("Premium Features Import", True)
        except ImportError:
            try:
                from core import premium_features
                self.add_result("Premium Features Import (module)", True)
            except Exception as e:
                self.add_result("Premium Features Import", False, str(e))
                return
                
    async def test_premium_features_v2(self):
        """Test Premium Features V2 module"""
        print("\n  [8.2] Premium Features V2 Tests")
        print("  " + "-" * 40)
        
        try:
            from core.premium_features_v2 import PremiumFeaturesV2
            self.add_result("Premium Features V2 Import", True)
        except ImportError:
            try:
                from core import premium_features_v2
                self.add_result("Premium Features V2 Import (module)", True)
            except Exception as e:
                self.add_result("Premium Features V2 Import", False, str(e))
                
    async def test_premium_features_v3(self):
        """Test Premium Features V3 module"""
        print("\n  [8.3] Premium Features V3 Tests")
        print("  " + "-" * 40)
        
        try:
            from core.premium_features_v3 import PremiumFeaturesV3
            self.add_result("Premium Features V3 Import", True)
        except ImportError:
            try:
                from core import premium_features_v3
                self.add_result("Premium Features V3 Import (module)", True)
            except Exception as e:
                self.add_result("Premium Features V3 Import", False, str(e))
                
    async def test_deep_scholar(self):
        """Test DeepScholar module"""
        print("\n  [8.4] DeepScholar Tests")
        print("  " + "-" * 40)
        
        try:
            from core.deep_scholar import DeepScholarOrchestrator
            self.add_result("DeepScholar Import", True)
        except ImportError:
            try:
                from core import deep_scholar
                self.add_result("DeepScholar Import (module)", True)
            except Exception as e:
                self.add_result("DeepScholar Import", False, str(e))
                return
                
        try:
            from core.deep_scholar import DeepScholarOrchestrator
            ds = DeepScholarOrchestrator()
            self.add_result("DeepScholarOrchestrator Instantiation", ds is not None)
        except Exception as e:
            self.add_result("DeepScholarOrchestrator Instantiation", False, str(e))
            
    async def test_deep_scholar_premium_quality(self):
        """Test DeepScholar Premium Quality modules"""
        print("\n  [8.5] DeepScholar Premium Quality Tests")
        print("  " + "-" * 40)
        
        quality_modules = [
            ("ReadabilityAnalyzer", "quality.readability_analyzer", "ReadabilityAnalyzer"),
            ("PlagiarismDetector", "quality.plagiarism_detector", "PlagiarismDetector"),
            ("ConsistencyChecker", "quality.consistency_checker", "ConsistencyChecker"),
            ("BiasAnalyzer", "quality.bias_analyzer", "BiasAnalyzer"),
            ("QualityScorer", "quality.quality_scorer", "QualityScorer"),
        ]
        
        for name, submodule, class_name in quality_modules:
            try:
                mod = __import__(f"core.deep_scholar_premium.{submodule}", fromlist=[class_name])
                cls = getattr(mod, class_name)
                self.add_result(f"Premium {name} Import", True)
            except Exception as e:
                self.add_result(f"Premium {name} Import", False, str(e))
                
    async def test_deep_scholar_premium_research(self):
        """Test DeepScholar Premium Research modules"""
        print("\n  [8.6] DeepScholar Premium Research Tests")
        print("  " + "-" * 40)
        
        research_modules = [
            ("AdvancedSearchEngine", "research.advanced_search", "AdvancedSearchEngine"),
            ("SourceQualityAnalyzer", "research.source_quality", "SourceQualityAnalyzer"),
            ("SourceVerifier", "research.source_verifier", "SourceVerifier"),
        ]
        
        for name, submodule, class_name in research_modules:
            try:
                mod = __import__(f"core.deep_scholar_premium.{submodule}", fromlist=[class_name])
                cls = getattr(mod, class_name)
                self.add_result(f"Premium {name} Import", True)
            except Exception as e:
                self.add_result(f"Premium {name} Import", False, str(e))
                
    async def test_deep_scholar_premium_visuals(self):
        """Test DeepScholar Premium Visuals modules"""
        print("\n  [8.7] DeepScholar Premium Visuals Tests")
        print("  " + "-" * 40)
        
        visual_modules = [
            ("DiagramGenerator", "visuals.diagram_generator", "DiagramGenerator"),
            ("SVGChartGenerator", "visuals.svg_charts", "SVGChartGenerator"),
            ("DataVisualizationEngine", "visuals.data_visualization", "DataVisualizationEngine"),
        ]
        
        for name, submodule, class_name in visual_modules:
            try:
                mod = __import__(f"core.deep_scholar_premium.{submodule}", fromlist=[class_name])
                cls = getattr(mod, class_name)
                self.add_result(f"Premium {name} Import", True)
            except Exception as e:
                self.add_result(f"Premium {name} Import", False, str(e))
                
    async def test_deep_scholar_premium_export(self):
        """Test DeepScholar Premium Export modules"""
        print("\n  [8.8] DeepScholar Premium Export Tests")
        print("  " + "-" * 40)
        
        export_modules = [
            ("HTMLExporter", "export.html_exporter", "HTMLExporter"),
            ("LaTeXExporter", "export.latex_exporter", "LaTeXExporter"),
            ("DOCXExporter", "export.docx_exporter", "DOCXExporter"),
            ("PresentationGenerator", "export.presentation_generator", "PresentationGenerator"),
            ("PremiumPDFExporter", "export.pdf_exporter", "PremiumPDFExporter"),
        ]
        
        for name, submodule, class_name in export_modules:
            try:
                mod = __import__(f"core.deep_scholar_premium.{submodule}", fromlist=[class_name])
                cls = getattr(mod, class_name)
                self.add_result(f"Premium {name} Import", True)
            except Exception as e:
                self.add_result(f"Premium {name} Import", False, str(e))
                
    async def test_deep_scholar_premium_agents(self):
        """Test DeepScholar Premium Agent modules"""
        print("\n  [8.9] DeepScholar Premium Agents Tests")
        print("  " + "-" * 40)
        
        agent_modules = [
            ("QualityAssuranceAgent", "agents.quality_agent", "QualityAssuranceAgent"),
            ("CriticAgent", "agents.critic_agent", "CriticAgent"),
            ("EditorAgent", "agents.editor_agent", "EditorAgent"),
            ("CitationAgent", "agents.citation_agent", "CitationAgent"),
            ("StatisticsAgent", "agents.statistics_agent", "StatisticsAgent"),
            ("TranslatorAgent", "agents.translator_agent", "TranslatorAgent"),
        ]
        
        for name, submodule, class_name in agent_modules:
            try:
                mod = __import__(f"core.deep_scholar_premium.{submodule}", fromlist=[class_name])
                cls = getattr(mod, class_name)
                instance = cls()
                self.add_result(f"Premium {name}", instance is not None)
            except Exception as e:
                self.add_result(f"Premium {name}", False, str(e))
                
    async def test_premium_integrations(self):
        """Test Premium Integrations module"""
        print("\n  [8.10] Premium Integrations Tests")
        print("  " + "-" * 40)
        
        try:
            from core.premium_integrations import PremiumIntegrations
            self.add_result("Premium Integrations Import", True)
        except ImportError:
            try:
                from core import premium_integrations
                self.add_result("Premium Integrations Import (module)", True)
            except Exception as e:
                self.add_result("Premium Integrations Import", False, str(e))
                
    async def run_all_tests(self):
        """Run all Phase 8 tests"""
        self.print_header()
        
        await self.test_premium_features()
        await self.test_premium_features_v2()
        await self.test_premium_features_v3()
        await self.test_deep_scholar()
        await self.test_deep_scholar_premium_quality()
        await self.test_deep_scholar_premium_research()
        await self.test_deep_scholar_premium_visuals()
        await self.test_deep_scholar_premium_export()
        await self.test_deep_scholar_premium_agents()
        await self.test_premium_integrations()
        
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
    phase = Phase08PremiumFeatures()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
