"""
🔬 AI ile Öğren V2 - Premium Test Protokolü
MODÜL 3: Frontend Analysis

Bu modül Frontend bileşenlerini analiz eder:
- Component imports/exports
- TypeScript interface uyumu
- API endpoint URL'leri
- State management
- Props validation

Çalıştırma: python tests/premium_test_frontend.py
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

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


class FrontendAnalyzer:
    """Frontend Component Analyzer"""
    
    def __init__(self, frontend_path: str):
        self.frontend_path = Path(frontend_path)
        self.results = TestResult()
        self.component_files: List[Path] = []
        self.found_imports: Set[str] = set()
        self.api_calls: List[Dict] = []
        
    def find_tsx_files(self) -> List[Path]:
        """Find all TSX files in frontend"""
        if not self.frontend_path.exists():
            return []
        return list(self.frontend_path.rglob("*.tsx")) + list(self.frontend_path.rglob("*.ts"))
    
    def find_learning_components(self) -> List[Path]:
        """Find learning journey related components"""
        all_files = self.find_tsx_files()
        learning_keywords = [
            "journey", "learning", "stage", "package", "exam", 
            "certificate", "wizard", "thinking", "feynman"
        ]
        
        related = []
        for f in all_files:
            name_lower = f.stem.lower()
            if any(kw in name_lower for kw in learning_keywords):
                related.append(f)
        
        return related
    
    def extract_api_urls(self, content: str) -> List[str]:
        """Extract API URL patterns from content"""
        patterns = [
            r'/journey/v2/[^\'"\s\`\)]+',
            r'/api/journey/[^\'"\s\`\)]+',
            r'`\${[^}]*}/journey[^`]*`',
        ]
        
        urls = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            urls.extend(matches)
        
        return urls
    
    def extract_interfaces(self, content: str) -> List[Tuple[str, List[str]]]:
        """Extract TypeScript interfaces"""
        pattern = r'interface\s+(\w+)\s*\{([^}]+)\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        result = []
        for name, body in matches:
            fields = re.findall(r'(\w+)\s*[:\?]', body)
            result.append((name, fields))
        
        return result
    
    def extract_types(self, content: str) -> List[Tuple[str, str]]:
        """Extract TypeScript type definitions"""
        pattern = r'type\s+(\w+)\s*=\s*([^;]+)'
        matches = re.findall(pattern, content)
        return matches
    
    def extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
        return re.findall(pattern, content)
    
    def extract_component_props(self, content: str) -> List[Tuple[str, str]]:
        """Extract component props"""
        pattern = r'(export\s+)?(const|function)\s+(\w+)\s*(?::\s*React\.FC<(\w+)>)?'
        matches = re.findall(pattern, content)
        
        result = []
        for m in matches:
            component = m[2]
            props = m[3] if len(m) > 3 else None
            if component[0].isupper():  # React components start with uppercase
                result.append((component, props or "unknown"))
        
        return result
    
    # ==================== FILE STRUCTURE TESTS ====================
    
    def test_component_files_exist(self):
        """Test: Required component files exist"""
        required_components = [
            "JourneyCreationWizard",
            "AIThinkingView", 
            "StageMapV2",
            "PackageView",
            "ExamView",
            "CertificateView"
        ]
        
        tsx_files = self.find_tsx_files()
        file_names = [f.stem for f in tsx_files]
        
        for comp in required_components:
            if comp in file_names or any(comp.lower() in f.lower() for f in file_names):
                self.results.add_pass(f"Component: {comp}", "Found")
            else:
                self.results.add_fail(f"Component: {comp}", "Not found")
    
    def test_learning_folder_structure(self):
        """Test: Learning journey folder structure"""
        learning_path = self.frontend_path / "app" / "learning-journey"
        
        if learning_path.exists():
            self.results.add_pass("Learning folder", str(learning_path))
            
            # Check for expected subfolders
            subdirs = [d.name for d in learning_path.iterdir() if d.is_dir()]
            if subdirs:
                self.results.add_pass("Learning subdirs", ", ".join(subdirs[:5]))
        else:
            # Try components folder
            components_path = self.frontend_path / "components" / "learning-journey"
            if components_path.exists():
                self.results.add_pass("Learning folder (components)", str(components_path))
            else:
                self.results.add_warning("Learning folder", "Not found in expected locations")
    
    # ==================== API URL TESTS ====================
    
    def test_api_url_patterns(self):
        """Test: API URL patterns in frontend match backend"""
        tsx_files = self.find_learning_components()
        
        all_urls = []
        for f in tsx_files:
            try:
                content = f.read_text(encoding="utf-8")
                urls = self.extract_api_urls(content)
                for url in urls:
                    all_urls.append((f.name, url))
            except Exception as e:
                self.results.add_warning(f"Read {f.name}", str(e))
        
        if all_urls:
            # Check for correct V2 prefix
            v2_correct = [u for u in all_urls if "/journey/v2" in u[1]]
            v2_wrong = [u for u in all_urls if "/api/journey/v2" in u[1]]
            
            if v2_correct:
                self.results.add_pass("API URL V2", f"{len(v2_correct)} correct patterns found")
            
            if v2_wrong:
                self.results.add_fail("API URL Wrong", 
                    f"{len(v2_wrong)} files use /api/journey/v2 instead of /journey/v2")
                for fname, url in v2_wrong[:3]:
                    print(f"       ↳ {Colors.CYAN}{fname}: {url}{Colors.RESET}")
            
            if not v2_correct and not v2_wrong:
                self.results.add_warning("API URLs", "No V2 API patterns found")
        else:
            self.results.add_warning("API URLs", "No API URLs found in learning components")
    
    # ==================== INTERFACE TESTS ====================
    
    def test_typescript_interfaces(self):
        """Test: TypeScript interfaces for learning journey"""
        tsx_files = self.find_learning_components()
        
        all_interfaces = []
        for f in tsx_files:
            try:
                content = f.read_text(encoding="utf-8")
                interfaces = self.extract_interfaces(content)
                for name, fields in interfaces:
                    all_interfaces.append((f.name, name, fields))
            except:
                pass
        
        expected_interfaces = [
            "Journey", "Stage", "Package", "Exam", "ExamResult", "Certificate"
        ]
        
        found_names = [i[1] for i in all_interfaces]
        
        for exp in expected_interfaces:
            if any(exp.lower() in n.lower() for n in found_names):
                self.results.add_pass(f"Interface: {exp}", "Defined")
            else:
                self.results.add_warning(f"Interface: {exp}", "Not found")
        
        if all_interfaces:
            self.results.add_pass("Total Interfaces", f"{len(all_interfaces)} found")
    
    def test_enum_consistency(self):
        """Test: Frontend enums match backend"""
        tsx_files = self.find_tsx_files()
        
        # Backend enums to check
        backend_enums = {
            "PackageStatus": ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "NEEDS_REVIEW"],
            "StageStatus": ["LOCKED", "UNLOCKED", "IN_PROGRESS", "COMPLETED"],
            "ExamType": ["multiple_choice", "feynman", "true_false", "case_study"],
            "PackageType": ["core", "practice", "review", "project"]
        }
        
        for f in tsx_files:
            try:
                content = f.read_text(encoding="utf-8")
                
                for enum_name, values in backend_enums.items():
                    # Check if enum or type exists
                    if enum_name in content or enum_name.lower() in content.lower():
                        # Check for value consistency
                        values_found = sum(1 for v in values if v in content or v.lower() in content.lower())
                        if values_found >= len(values) // 2:
                            self.results.add_pass(f"{enum_name} values", f"{values_found}/{len(values)} found in {f.name}")
                            break
            except:
                pass
    
    # ==================== IMPORT TESTS ====================
    
    def test_react_imports(self):
        """Test: Required React/Next.js imports"""
        tsx_files = self.find_learning_components()
        
        for f in tsx_files:
            try:
                content = f.read_text(encoding="utf-8")
                imports = self.extract_imports(content)
                
                # Check for useState, useEffect
                has_hooks = any("react" in imp.lower() for imp in imports)
                if has_hooks:
                    self.found_imports.add(f.name)
            except:
                pass
        
        if self.found_imports:
            self.results.add_pass("React imports", f"{len(self.found_imports)} components have React hooks")
        else:
            self.results.add_warning("React imports", "Could not verify React imports")
    
    def test_framer_motion(self):
        """Test: Framer Motion for animations"""
        tsx_files = self.find_learning_components()
        
        has_motion = False
        for f in tsx_files:
            try:
                content = f.read_text(encoding="utf-8")
                if "framer-motion" in content or "motion." in content:
                    has_motion = True
                    self.results.add_pass("Framer Motion", f"Found in {f.name}")
                    break
            except:
                pass
        
        if not has_motion:
            self.results.add_warning("Framer Motion", "Not found (AI thinking animation may not work)")
    
    # ==================== COMPONENT ANALYSIS ====================
    
    def test_component_props(self):
        """Test: Component props are properly typed"""
        tsx_files = self.find_learning_components()
        
        total_components = 0
        typed_components = 0
        
        for f in tsx_files:
            try:
                content = f.read_text(encoding="utf-8")
                components = self.extract_component_props(content)
                
                for comp_name, props in components:
                    total_components += 1
                    if props and props != "unknown":
                        typed_components += 1
            except:
                pass
        
        if total_components > 0:
            ratio = typed_components / total_components * 100
            if ratio >= 80:
                self.results.add_pass("Props typing", f"{typed_components}/{total_components} ({ratio:.0f}%)")
            else:
                self.results.add_warning("Props typing", f"{typed_components}/{total_components} ({ratio:.0f}%)")
        else:
            self.results.add_warning("Props typing", "No components found")
    
    def test_error_handling(self):
        """Test: Error handling in components"""
        tsx_files = self.find_learning_components()
        
        error_patterns = ["catch", "try", "error", "onError", "errorBoundary"]
        
        files_with_error_handling = 0
        for f in tsx_files:
            try:
                content = f.read_text(encoding="utf-8")
                if any(p in content for p in error_patterns):
                    files_with_error_handling += 1
            except:
                pass
        
        if files_with_error_handling > 0:
            self.results.add_pass("Error handling", f"{files_with_error_handling} components have error handling")
        else:
            self.results.add_warning("Error handling", "No error handling patterns found")
    
    def test_loading_states(self):
        """Test: Loading state management"""
        tsx_files = self.find_learning_components()
        
        loading_patterns = ["loading", "isLoading", "setLoading", "Spinner", "skeleton"]
        
        files_with_loading = 0
        for f in tsx_files:
            try:
                content = f.read_text(encoding="utf-8")
                if any(p in content.lower() for p in loading_patterns):
                    files_with_loading += 1
            except:
                pass
        
        if files_with_loading > 0:
            self.results.add_pass("Loading states", f"{files_with_loading} components have loading states")
        else:
            self.results.add_warning("Loading states", "No loading patterns found")
    
    # ==================== RUN ALL ====================
    
    def run_all(self):
        """Run all frontend analysis tests"""
        print()
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}🔬 PREMIUM TEST PROTOKOLÜ - MODÜL 3: FRONTEND ANALYSIS{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print()
        
        if not self.frontend_path.exists():
            print(f"{Colors.RED}❌ Frontend path not found: {self.frontend_path}{Colors.RESET}")
            return False
        
        # File Structure
        print(f"{Colors.YELLOW}📁 FILE STRUCTURE{Colors.RESET}")
        self.test_component_files_exist()
        self.test_learning_folder_structure()
        print()
        
        # API URLs
        print(f"{Colors.YELLOW}🔗 API URL PATTERNS{Colors.RESET}")
        self.test_api_url_patterns()
        print()
        
        # TypeScript
        print(f"{Colors.YELLOW}📝 TYPESCRIPT ANALYSIS{Colors.RESET}")
        self.test_typescript_interfaces()
        self.test_enum_consistency()
        print()
        
        # Imports
        print(f"{Colors.YELLOW}📦 IMPORTS & DEPENDENCIES{Colors.RESET}")
        self.test_react_imports()
        self.test_framer_motion()
        print()
        
        # Components
        print(f"{Colors.YELLOW}⚛️ COMPONENT ANALYSIS{Colors.RESET}")
        self.test_component_props()
        self.test_error_handling()
        self.test_loading_states()
        print()
        
        # Summary
        total = self.results.passed + self.results.failed
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        if self.results.failed == 0:
            print(f"{Colors.GREEN}✅ TÜM FRONTEND TESTLERİ GEÇTİ: {self.results.passed}/{total}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}📊 SONUÇ: {self.results.passed}/{total} geçti, {self.results.failed} başarısız{Colors.RESET}")
        if self.results.warnings > 0:
            print(f"{Colors.YELLOW}⚠️ Uyarılar: {self.results.warnings}{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        
        return self.results.failed == 0


# ==================== MAIN ====================

if __name__ == "__main__":
    # Get frontend path
    base_path = Path(__file__).parent.parent
    frontend_path = base_path / "frontend-next"  # Next.js frontend
    
    if not frontend_path.exists():
        # Try alternate locations
        alt_paths = [
            base_path / "frontend",
            base_path / "app",
            base_path / "src",
            base_path.parent / "frontend",
        ]
        for alt in alt_paths:
            if alt.exists():
                frontend_path = alt
                break
    
    print(f"Frontend path: {frontend_path}")
    
    analyzer = FrontendAnalyzer(str(frontend_path))
    success = analyzer.run_all()
    sys.exit(0 if success else 1)
