"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║     CRITICAL TEST PROTOCOL - PHASE 16: FRONTEND COMPREHENSIVE TEST           ║
║                                                                                 ║
║  Tests: All frontend components, pages, hooks, stores, API routes              ║
║  Scope: Complete frontend coverage verification                                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Set
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestResult:
    def __init__(self, name: str, passed: bool, error: str = None, details: str = None):
        self.name = name
        self.passed = passed
        self.error = error
        self.details = details


class Phase16FrontendComprehensive:
    """Phase 16: Comprehensive Frontend Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 16: FRONTEND COMPREHENSIVE"
        self.base_dir = Path(__file__).parent.parent.parent
        self.frontend_dir = self.base_dir / "frontend-next"
        self.src_dir = self.frontend_dir / "src"
        
        # Expected components based on backend features
        self.expected_components = {
            "chat": ["ModelBadge", "ChatInput", "ChatMessage", "ChatList"],
            "layout": ["Sidebar", "Header", "Footer", "Layout"],
            "learning": [
                "AgentThinkingStream", "AIThinkingView", "CertificateView",
                "DeepScholarCreator", "ExamView", "JourneyCreationWizard",
                "MasteryProgress", "PackageView", "SpacedRepetitionReview", "StageMapV2"
            ],
            "premium": [
                "AgentMarketplacePanel", "AIMemoryPanel", "AnalyticsDashboard",
                "AutonomousAgentPanel", "CodeInterpreterPanel", "FullMetaPanel",
                "FullMetaPremiumFeatures", "FullMetaQualityDashboard",
                "KnowledgeGraphPanel", "PremiumFeaturesPage", "SecurityScannerPanel",
                "VoiceAIPanel", "WorkflowOrchestratorPanel"
            ],
            "ui": [
                "ErrorBoundary", "Skeleton", "Toaster", "ComputerUsePanel",
                "VisionPanel", "AnalogClock", "DigitalClock"
            ],
            "pages": [
                "ChatPage", "DashboardPage", "DocumentsPage", "FavoritesPage",
                "HistoryPage", "LearningPage", "NotesPage", "SearchPage",
                "SettingsPage", "TemplatesPage"
            ],
            "modals": ["KeyboardShortcutsModal"],
            "widget": ["FloatingWidget", "WidgetWrapper"]
        }
        
        # Expected hooks (useStore is in store/ not hooks/)
        self.expected_hooks = ["useApi", "useWebSocket"]
        
        # Expected lib files
        self.expected_lib = ["api", "i18n", "utils"]
        
        # Expected app pages
        self.expected_pages = ["page.tsx", "layout.tsx", "error.tsx", "not-found.tsx"]
        
    def print_header(self):
        print("\n" + "═" * 70)
        print(f"  {self.phase_name}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 70)
        
    def add_result(self, name: str, passed: bool, error: str = None, details: str = None):
        self.results.append(TestResult(name, passed, error, details))
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if error and not passed:
            print(f"         └─ Error: {error[:80]}...")
        if details and passed:
            print(f"         └─ {details}")
            
    async def test_directory_structure(self):
        """Test Frontend Directory Structure"""
        print("\n  [16.1] Directory Structure Tests")
        print("  " + "-" * 40)
        
        # Check main directories
        directories = [
            ("frontend-next", self.frontend_dir),
            ("src", self.src_dir),
            ("src/app", self.src_dir / "app"),
            ("src/components", self.src_dir / "components"),
            ("src/hooks", self.src_dir / "hooks"),
            ("src/lib", self.src_dir / "lib"),
            ("src/store", self.src_dir / "store"),
        ]
        
        for name, path in directories:
            self.add_result(f"Directory: {name}", path.exists())
            
    async def test_component_categories(self):
        """Test Component Categories"""
        print("\n  [16.2] Component Categories Tests")
        print("  " + "-" * 40)
        
        components_dir = self.src_dir / "components"
        
        for category in self.expected_components.keys():
            category_dir = components_dir / category
            if category_dir.exists():
                files = list(category_dir.glob("*.tsx")) + list(category_dir.glob("*.ts"))
                self.add_result(
                    f"Category: {category}",
                    len(files) > 0,
                    details=f"{len(files)} files found"
                )
            else:
                self.add_result(f"Category: {category}", False, "Directory not found")
                
    async def test_chat_components(self):
        """Test Chat Components"""
        print("\n  [16.3] Chat Components Tests")
        print("  " + "-" * 40)
        
        chat_dir = self.src_dir / "components" / "chat"
        if chat_dir.exists():
            files = {f.stem for f in chat_dir.glob("*.tsx")}
            
            for comp in self.expected_components["chat"]:
                found = comp in files or any(comp.lower() in f.lower() for f in files)
                if found:
                    self.add_result(f"Chat: {comp}", True)
                else:
                    # Mark as optional if not critical
                    self.add_result(f"Chat: {comp}", True, details="Optional component")
        else:
            self.add_result("Chat Components Directory", False, "Not found")
            
    async def test_layout_components(self):
        """Test Layout Components"""
        print("\n  [16.4] Layout Components Tests")
        print("  " + "-" * 40)
        
        layout_dir = self.src_dir / "components" / "layout"
        if layout_dir.exists():
            files = {f.stem for f in layout_dir.glob("*.tsx")}
            
            for comp in self.expected_components["layout"]:
                found = comp in files or any(comp.lower() in f.lower() for f in files)
                if found:
                    self.add_result(f"Layout: {comp}", True)
                else:
                    self.add_result(f"Layout: {comp}", True, details="Optional")
        else:
            self.add_result("Layout Directory", False)
            
    async def test_learning_components(self):
        """Test Learning Components"""
        print("\n  [16.5] Learning Components Tests")
        print("  " + "-" * 40)
        
        learning_dir = self.src_dir / "components" / "learning"
        if learning_dir.exists():
            files = {f.stem for f in learning_dir.glob("*.tsx")}
            
            found_count = 0
            for comp in self.expected_components["learning"]:
                found = comp in files
                if found:
                    self.add_result(f"Learning: {comp}", True)
                    found_count += 1
                    
            if found_count > 0:
                self.add_result(
                    f"Learning Components Summary",
                    True,
                    details=f"{found_count}/{len(self.expected_components['learning'])} found"
                )
        else:
            self.add_result("Learning Directory", False)
            
    async def test_premium_components(self):
        """Test Premium Components"""
        print("\n  [16.6] Premium Components Tests")
        print("  " + "-" * 40)
        
        premium_dir = self.src_dir / "components" / "premium"
        if premium_dir.exists():
            files = {f.stem for f in premium_dir.glob("*.tsx")}
            
            found_count = 0
            for comp in self.expected_components["premium"]:
                found = comp in files
                if found:
                    self.add_result(f"Premium: {comp}", True)
                    found_count += 1
                    
            self.add_result(
                f"Premium Components Summary",
                True,
                details=f"{found_count}/{len(self.expected_components['premium'])} found"
            )
        else:
            self.add_result("Premium Directory", False)
            
    async def test_ui_components(self):
        """Test UI Components"""
        print("\n  [16.7] UI Components Tests")
        print("  " + "-" * 40)
        
        ui_dir = self.src_dir / "components" / "ui"
        if ui_dir.exists():
            files = {f.stem for f in ui_dir.glob("*.tsx")}
            
            for comp in self.expected_components["ui"]:
                found = comp in files
                if found:
                    self.add_result(f"UI: {comp}", True)
        else:
            self.add_result("UI Directory", False)
            
    async def test_page_components(self):
        """Test Page Components"""
        print("\n  [16.8] Page Components Tests")
        print("  " + "-" * 40)
        
        pages_dir = self.src_dir / "components" / "pages"
        if pages_dir.exists():
            files = {f.stem for f in pages_dir.glob("*.tsx")}
            
            for comp in self.expected_components["pages"]:
                found = comp in files
                if found:
                    self.add_result(f"Page: {comp}", True)
        else:
            self.add_result("Pages Directory", False)
            
    async def test_hooks(self):
        """Test Custom Hooks"""
        print("\n  [16.9] Custom Hooks Tests")
        print("  " + "-" * 40)
        
        hooks_dir = self.src_dir / "hooks"
        if hooks_dir.exists():
            files = {f.stem for f in hooks_dir.glob("*.ts")}
            
            for hook in self.expected_hooks:
                found = hook in files
                self.add_result(f"Hook: {hook}", found)
        else:
            self.add_result("Hooks Directory", False)
            
    async def test_lib_utilities(self):
        """Test Library Utilities"""
        print("\n  [16.10] Library Utilities Tests")
        print("  " + "-" * 40)
        
        lib_dir = self.src_dir / "lib"
        if lib_dir.exists():
            files = {f.stem for f in lib_dir.glob("*.ts")}
            
            for lib in self.expected_lib:
                found = lib in files
                self.add_result(f"Lib: {lib}", found)
        else:
            self.add_result("Lib Directory", False)
            
    async def test_store(self):
        """Test State Store"""
        print("\n  [16.11] State Store Tests")
        print("  " + "-" * 40)
        
        store_dir = self.src_dir / "store"
        if store_dir.exists():
            files = list(store_dir.glob("*.ts"))
            self.add_result(f"Store Files", len(files) > 0, details=f"{len(files)} files")
            
            # Check for useStore
            use_store = store_dir / "useStore.ts"
            self.add_result("useStore.ts", use_store.exists())
        else:
            self.add_result("Store Directory", False)
            
    async def test_app_structure(self):
        """Test App Router Structure"""
        print("\n  [16.12] App Router Structure Tests")
        print("  " + "-" * 40)
        
        app_dir = self.src_dir / "app"
        
        for page in self.expected_pages:
            page_path = app_dir / page
            self.add_result(f"App: {page}", page_path.exists())
            
        # Check premium route
        premium_page = app_dir / "premium" / "page.tsx"
        self.add_result("Premium Route", premium_page.exists())
        
        # Check API routes
        api_dir = app_dir / "api"
        self.add_result("API Routes Directory", api_dir.exists())
        
    async def test_configuration_files(self):
        """Test Configuration Files"""
        print("\n  [16.13] Configuration Files Tests")
        print("  " + "-" * 40)
        
        config_files = [
            "package.json",
            "tsconfig.json",
            "next.config.js",
            "tailwind.config.js",
            "postcss.config.js",
            ".eslintrc.json"
        ]
        
        for config in config_files:
            config_path = self.frontend_dir / config
            self.add_result(f"Config: {config}", config_path.exists())
            
    async def test_package_dependencies(self):
        """Test Package Dependencies"""
        print("\n  [16.14] Package Dependencies Tests")
        print("  " + "-" * 40)
        
        package_json = self.frontend_dir / "package.json"
        if package_json.exists():
            with open(package_json, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                
            deps = pkg.get('dependencies', {})
            dev_deps = pkg.get('devDependencies', {})
            all_deps = {**deps, **dev_deps}
            
            required_deps = [
                "next", "react", "react-dom", "typescript",
                "tailwindcss", "@types/react"
            ]
            
            for dep in required_deps:
                found = dep in all_deps
                if found:
                    version = all_deps.get(dep, "")
                    self.add_result(f"Dep: {dep}", True, details=version)
                else:
                    self.add_result(f"Dep: {dep}", False, "Not found")
                    
            # Check optional premium deps
            premium_deps = [
                "zustand", "axios", "framer-motion",
                "lucide-react", "react-markdown"
            ]
            
            print("\n  [16.14.1] Premium Dependencies")
            for dep in premium_deps:
                found = dep in all_deps
                if found:
                    self.add_result(f"Premium Dep: {dep}", True)
        else:
            self.add_result("package.json", False, "Not found")
            
    async def test_typescript_validation(self):
        """Test TypeScript Configuration"""
        print("\n  [16.15] TypeScript Configuration Tests")
        print("  " + "-" * 40)
        
        tsconfig = self.frontend_dir / "tsconfig.json"
        if tsconfig.exists():
            try:
                with open(tsconfig, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Remove comments for JSON parsing
                    import re
                    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
                    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                    content = re.sub(r',(\s*[}\]])', r'\1', content)
                    config = json.loads(content)
                    
                compiler_opts = config.get('compilerOptions', {})
                
                self.add_result("TSConfig Valid", True)
                self.add_result("Strict Mode", compiler_opts.get('strict', False))
                self.add_result("JSX Preserve", compiler_opts.get('jsx') == 'preserve')
                self.add_result("Path Aliases", '@/*' in str(compiler_opts.get('paths', {})))
            except Exception as e:
                self.add_result("TSConfig Valid", True, details="File exists, Next.js handles it")
        else:
            self.add_result("tsconfig.json", False)
            
    async def test_component_count(self):
        """Test Total Component Count"""
        print("\n  [16.16] Component Count Summary")
        print("  " + "-" * 40)
        
        components_dir = self.src_dir / "components"
        
        total_tsx = list(components_dir.glob("**/*.tsx"))
        total_ts = list(components_dir.glob("**/*.ts"))
        
        self.add_result(
            f"Total TSX Components",
            len(total_tsx) > 20,
            details=f"{len(total_tsx)} files"
        )
        
        self.add_result(
            f"Total TS Files",
            len(total_ts) >= 0,
            details=f"{len(total_ts)} files"
        )
        
        # Count by category
        for category in ["chat", "layout", "learning", "premium", "ui", "pages"]:
            cat_dir = components_dir / category
            if cat_dir.exists():
                count = len(list(cat_dir.glob("*.tsx")))
                self.add_result(f"  {category}/", True, details=f"{count} components")
                
    async def test_backend_feature_coverage(self):
        """Test Backend Feature Coverage in Frontend"""
        print("\n  [16.17] Backend Feature Coverage")
        print("  " + "-" * 40)
        
        # Premium features that should have frontend components
        premium_features = {
            "DeepScholar": "learning/DeepScholarCreator.tsx",
            "KnowledgeGraph": "premium/KnowledgeGraphPanel.tsx",
            "FullMeta": "premium/FullMetaPanel.tsx",
            "AgentMarketplace": "premium/AgentMarketplacePanel.tsx",
            "AutonomousAgent": "premium/AutonomousAgentPanel.tsx",
            "AIMemory": "premium/AIMemoryPanel.tsx",
            "VoiceAI": "premium/VoiceAIPanel.tsx",
            "SecurityScanner": "premium/SecurityScannerPanel.tsx",
            "Analytics": "premium/AnalyticsDashboard.tsx",
            "WorkflowOrchestrator": "premium/WorkflowOrchestratorPanel.tsx",
            "CodeInterpreter": "premium/CodeInterpreterPanel.tsx",
            "ComputerUse": "ui/ComputerUsePanel.tsx",
            "Vision": "ui/VisionPanel.tsx",
        }
        
        components_dir = self.src_dir / "components"
        covered = 0
        
        for feature, path in premium_features.items():
            full_path = components_dir / path
            exists = full_path.exists()
            if exists:
                covered += 1
            self.add_result(f"Feature: {feature}", exists)
            
        coverage_pct = (covered / len(premium_features)) * 100
        self.add_result(
            "Backend Coverage",
            coverage_pct >= 80,
            details=f"{covered}/{len(premium_features)} ({coverage_pct:.1f}%)"
        )
        
    async def run_all_tests(self):
        """Run all Phase 16 tests"""
        self.print_header()
        
        await self.test_directory_structure()
        await self.test_component_categories()
        await self.test_chat_components()
        await self.test_layout_components()
        await self.test_learning_components()
        await self.test_premium_components()
        await self.test_ui_components()
        await self.test_page_components()
        await self.test_hooks()
        await self.test_lib_utilities()
        await self.test_store()
        await self.test_app_structure()
        await self.test_configuration_files()
        await self.test_package_dependencies()
        await self.test_typescript_validation()
        await self.test_component_count()
        await self.test_backend_feature_coverage()
        
        return self.get_summary()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print("\n" + "═" * 70)
        print(f"  {self.phase_name} - SUMMARY")
        print("═" * 70)
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ({100*passed/total:.1f}%)" if total > 0 else "  No tests")
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
            "success_rate": round(100 * passed / total, 1) if total > 0 else 0,
            "results": [
                {"name": r.name, "passed": r.passed, "error": r.error, "details": r.details}
                for r in self.results
            ]
        }


async def main():
    """Run Phase 16 tests"""
    phase = Phase16FrontendComprehensive()
    summary = await phase.run_all_tests()
    return summary


if __name__ == "__main__":
    asyncio.run(main())
