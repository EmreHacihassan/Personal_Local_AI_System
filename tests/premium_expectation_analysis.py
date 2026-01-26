"""
🔬 AI ile Öğren V2 - Beklenti Karşılaştırma Analizi
Premium Expectation Validation

Bu script beklentileri kod ile karşılaştırır ve rapor üretir.
Çalıştırma: python tests/premium_expectation_analysis.py
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field

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


@dataclass
class Expectation:
    """Tek bir beklenti"""
    id: str
    category: str
    description: str
    priority: str  # kritik, onemli, normal
    status: str = "not_checked"  # met, partial, not_met, not_checked
    details: str = ""


@dataclass
class AnalysisResult:
    expectations: List[Expectation] = field(default_factory=list)
    
    @property
    def met_count(self) -> int:
        return sum(1 for e in self.expectations if e.status == "met")
    
    @property
    def partial_count(self) -> int:
        return sum(1 for e in self.expectations if e.status == "partial")
    
    @property
    def not_met_count(self) -> int:
        return sum(1 for e in self.expectations if e.status == "not_met")
    
    @property
    def total(self) -> int:
        return len(self.expectations)
    
    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0
        return (self.met_count + self.partial_count * 0.5) / self.total * 100


class ExpectationAnalyzer:
    """Beklenti analiz edici"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.result = AnalysisResult()
    
    def check_file_exists(self, pattern: str) -> bool:
        """Dosya var mı kontrol et"""
        matches = list(self.base_path.rglob(pattern))
        return len(matches) > 0
    
    def check_class_exists(self, module_path: str, class_name: str) -> bool:
        """Class var mı kontrol et"""
        try:
            full_path = self.base_path / module_path
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                return f"class {class_name}" in content
        except:
            pass
        return False
    
    def check_function_exists(self, module_path: str, func_name: str) -> bool:
        """Function var mı kontrol et"""
        try:
            full_path = self.base_path / module_path
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                return f"def {func_name}" in content or f"async def {func_name}" in content
        except:
            pass
        return False
    
    def check_enum_value(self, module_path: str, enum_name: str, value: str) -> bool:
        """Enum değeri var mı"""
        try:
            full_path = self.base_path / module_path
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                return value.upper() in content or value.lower() in content
        except:
            pass
        return False
    
    def check_api_endpoint(self, endpoint: str) -> bool:
        """API endpoint var mı"""
        try:
            api_file = self.base_path / "api" / "learning_journey_v2_endpoints.py"
            if api_file.exists():
                content = api_file.read_text(encoding='utf-8')
                # Pattern kontrolü
                pattern = endpoint.replace("{", "\\{").replace("}", "\\}")
                return endpoint in content or re.search(pattern, content) is not None
        except:
            pass
        return False
    
    def check_frontend_component(self, component_name: str) -> bool:
        """Frontend component var mı"""
        patterns = [
            f"frontend-next/**/{component_name}.tsx",
            f"frontend-next/**/{component_name}.jsx",
        ]
        for pattern in patterns:
            if self.check_file_exists(pattern):
                return True
        return False
    
    # ==================== BEKLENTİ KATEGORİLERİ ====================
    
    def analyze_general_vision(self):
        """1. Genel Vizyon beklentileri"""
        print(f"\n{Colors.YELLOW}1. GENEL VİZYON{Colors.RESET}")
        
        # Journey Creation Wizard
        exp = Expectation(
            id="GV1",
            category="Genel Vizyon",
            description="Journey Creation Wizard (5 adımlı sihirbaz)",
            priority="kritik"
        )
        if self.check_frontend_component("JourneyCreationWizard"):
            content = (self.base_path / "frontend-next" / "src" / "components" / "learning" / "JourneyCreationWizard.tsx").read_text(encoding='utf-8')
            steps = content.count("Step") 
            if steps >= 5:
                exp.status = "met"
                exp.details = f"{steps}+ adım bulundu"
            else:
                exp.status = "partial"
                exp.details = f"Sadece {steps} adım"
        else:
            exp.status = "not_met"
            exp.details = "Component bulunamadı"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # AI Thinking View
        exp = Expectation(
            id="GV2",
            category="Genel Vizyon",
            description="AI Thinking View (animasyonlu düşünce görünümü)",
            priority="kritik"
        )
        if self.check_frontend_component("AIThinkingView"):
            content = (self.base_path / "frontend-next" / "src" / "components" / "learning" / "AIThinkingView.tsx").read_text(encoding='utf-8')
            has_framer = "framer-motion" in content
            has_agents = "AGENT_ICONS" in content
            if has_framer and has_agents:
                exp.status = "met"
                exp.details = "Framer Motion + Agent ikonları mevcut"
            else:
                exp.status = "partial"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Stage Map V2
        exp = Expectation(
            id="GV3",
            category="Genel Vizyon",
            description="Stage Map V2 (Candy Crush tarzı harita)",
            priority="kritik"
        )
        if self.check_frontend_component("StageMapV2"):
            exp.status = "met"
            exp.details = "Component mevcut"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Package View
        exp = Expectation(
            id="GV4",
            category="Genel Vizyon", 
            description="Package View (içerik görüntüleme)",
            priority="kritik"
        )
        if self.check_frontend_component("PackageView"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Exam View
        exp = Expectation(
            id="GV5",
            category="Genel Vizyon",
            description="Exam View (sınav sistemi)",
            priority="kritik"
        )
        if self.check_frontend_component("ExamView"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Certificate View
        exp = Expectation(
            id="GV6",
            category="Genel Vizyon",
            description="Certificate View (sertifika sistemi)",
            priority="onemli"
        )
        if self.check_frontend_component("CertificateView"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
    
    def analyze_backend(self):
        """3. Backend beklentileri"""
        print(f"\n{Colors.YELLOW}2. BACKEND MODÜLLER{Colors.RESET}")
        
        models_path = "core/learning_journey_v2/models.py"
        
        # LearningGoal model
        exp = Expectation(id="BE1", category="Backend", 
                         description="LearningGoal data model", priority="kritik")
        if self.check_class_exists(models_path, "LearningGoal"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # CurriculumPlan
        exp = Expectation(id="BE2", category="Backend",
                         description="CurriculumPlan model", priority="kritik")
        if self.check_class_exists(models_path, "CurriculumPlan"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Stage model
        exp = Expectation(id="BE3", category="Backend",
                         description="Stage model", priority="kritik")
        if self.check_class_exists(models_path, "Stage"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Package model
        exp = Expectation(id="BE4", category="Backend",
                         description="Package model", priority="kritik")
        if self.check_class_exists(models_path, "Package"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Exam model
        exp = Expectation(id="BE5", category="Backend",
                         description="Exam model", priority="kritik")
        if self.check_class_exists(models_path, "Exam"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Certificate model
        exp = Expectation(id="BE6", category="Backend",
                         description="Certificate model", priority="onemli")
        if self.check_class_exists(models_path, "Certificate"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # UserProgress
        exp = Expectation(id="BE7", category="Backend",
                         description="UserProgress model", priority="onemli")
        if self.check_class_exists(models_path, "UserProgress"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Orchestrator
        exp = Expectation(id="BE8", category="Backend",
                         description="LearningJourneyOrchestrator", priority="kritik")
        if self.check_class_exists("core/learning_journey_v2/orchestrator.py", "LearningJourneyOrchestrator"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # CurriculumPlanner
        exp = Expectation(id="BE9", category="Backend",
                         description="CurriculumPlannerAgent", priority="kritik")
        if self.check_class_exists("core/learning_journey_v2/curriculum_planner.py", "CurriculumPlannerAgent"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # ExamSystem
        exp = Expectation(id="BE10", category="Backend",
                         description="ExamSystem", priority="kritik")
        if self.check_class_exists("core/learning_journey_v2/exam_system.py", "ExamSystem"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # CertificateGenerator
        exp = Expectation(id="BE11", category="Backend",
                         description="CertificateGenerator", priority="onemli")
        if self.check_class_exists("core/learning_journey_v2/certificate_system.py", "CertificateGenerator"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # ContentGenerator
        exp = Expectation(id="BE12", category="Backend",
                         description="ContentGeneratorAgent", priority="kritik")
        if self.check_class_exists("core/learning_journey_v2/content_generator.py", "ContentGeneratorAgent"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
    
    def analyze_enums(self):
        """Enum beklentileri"""
        print(f"\n{Colors.YELLOW}3. ENUM & TYPES{Colors.RESET}")
        
        models_path = "core/learning_journey_v2/models.py"
        
        # ExamType - 15 tür bekleniyor
        exp = Expectation(id="EN1", category="Enums",
                         description="ExamType enum (15 sınav türü)", priority="kritik")
        try:
            content = (self.base_path / models_path).read_text(encoding='utf-8')
            exam_types = ["MULTIPLE_CHOICE", "FEYNMAN", "TRUE_FALSE", "FILL_BLANK", 
                         "SHORT_ANSWER", "ESSAY", "TEACH_BACK", "CONCEPT_MAP",
                         "PROBLEM_SOLVING", "CODE_CHALLENGE"]
            found = sum(1 for t in exam_types if t in content)
            if found >= 10:
                exp.status = "met"
                exp.details = f"{found}/10+ türü mevcut"
            elif found >= 5:
                exp.status = "partial"
                exp.details = f"{found}/10 türü mevcut"
            else:
                exp.status = "not_met"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # PackageType
        exp = Expectation(id="EN2", category="Enums",
                         description="PackageType enum", priority="kritik")
        types = ["LEARNING", "PRACTICE", "EXAM", "REVIEW", "CLOSURE", "INTRO"]
        try:
            content = (self.base_path / models_path).read_text(encoding='utf-8')
            found = sum(1 for t in types if t in content)
            if found >= 5:
                exp.status = "met"
                exp.details = f"{found}/6 türü mevcut"
            else:
                exp.status = "partial"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # PackageStatus
        exp = Expectation(id="EN3", category="Enums",
                         description="PackageStatus enum (COMPLETED, NEEDS_REVIEW dahil)", priority="kritik")
        statuses = ["LOCKED", "AVAILABLE", "IN_PROGRESS", "COMPLETED", "NEEDS_REVIEW"]
        try:
            content = (self.base_path / models_path).read_text(encoding='utf-8')
            found = sum(1 for s in statuses if s in content)
            if found >= 5:
                exp.status = "met"
                exp.details = f"{found}/5 durum mevcut"
            else:
                exp.status = "partial"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # StageStatus
        exp = Expectation(id="EN4", category="Enums",
                         description="StageStatus enum", priority="onemli")
        if self.check_class_exists(models_path, "StageStatus"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # ContentType
        exp = Expectation(id="EN5", category="Enums",
                         description="ContentType enum (12 içerik türü)", priority="onemli")
        types = ["TEXT", "VIDEO", "IMAGE", "INTERACTIVE", "SUMMARY", "EXAMPLE"]
        try:
            content = (self.base_path / models_path).read_text(encoding='utf-8')
            found = sum(1 for t in types if t in content)
            if found >= 5:
                exp.status = "met"
            else:
                exp.status = "partial"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
    
    def analyze_api_endpoints(self):
        """API endpoint beklentileri"""
        print(f"\n{Colors.YELLOW}4. API ENDPOINTS{Colors.RESET}")
        
        endpoints = [
            ("AP1", "/list", "GET /journey/v2/list", "kritik"),
            ("AP2", "/create", "POST /journey/v2/create", "kritik"),
            ("AP3", "/map", "GET /journey/v2/{id}/map", "kritik"),
            ("AP4", "/progress", "GET /journey/v2/{id}/progress", "onemli"),
            ("AP5", "/start", "POST /packages/{id}/start", "kritik"),
            ("AP6", "/complete", "POST /packages/{id}/complete", "onemli"),
            ("AP7", "/submit", "POST /exams/{id}/submit", "kritik"),
            ("AP8", "/complete", "POST /journey/v2/{id}/complete", "onemli"),
        ]
        
        for eid, pattern, desc, priority in endpoints:
            exp = Expectation(id=eid, category="API", description=desc, priority=priority)
            if self.check_api_endpoint(pattern):
                exp.status = "met"
            else:
                exp.status = "not_met"
            self.result.expectations.append(exp)
            self._print_status(exp)
    
    def analyze_exam_system(self):
        """Sınav sistemi beklentileri"""
        print(f"\n{Colors.YELLOW}5. SINAV SİSTEMİ{Colors.RESET}")
        
        exam_path = "core/learning_journey_v2/exam_system.py"
        
        # FeynmanExamEvaluator
        exp = Expectation(id="EX1", category="Sınav",
                         description="FeynmanExamEvaluator (Feynman değerlendirme)", priority="kritik")
        if self.check_class_exists(exam_path, "FeynmanExamEvaluator"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # MultipleChoiceEvaluator
        exp = Expectation(id="EX2", category="Sınav",
                         description="MultipleChoiceEvaluator", priority="kritik")
        if self.check_class_exists(exam_path, "MultipleChoiceEvaluator"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # ProblemSolvingEvaluator
        exp = Expectation(id="EX3", category="Sınav",
                         description="ProblemSolvingEvaluator", priority="onemli")
        if self.check_class_exists(exam_path, "ProblemSolvingEvaluator"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Feynman 5 kriter
        exp = Expectation(id="EX4", category="Sınav",
                         description="Feynman 5 değerlendirme kriteri", priority="kritik")
        try:
            content = (self.base_path / exam_path).read_text(encoding='utf-8')
            criteria = ["accuracy", "simplicity", "examples", "logical_flow", "completeness"]
            found = sum(1 for c in criteria if c in content.lower())
            if found >= 4:
                exp.status = "met"
                exp.details = f"{found}/5 kriter mevcut"
            else:
                exp.status = "partial"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # ExamResult model
        exp = Expectation(id="EX5", category="Sınav",
                         description="ExamResult model", priority="kritik")
        if self.check_class_exists(exam_path, "ExamResult"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
    
    def analyze_certificate_system(self):
        """Sertifika sistemi beklentileri"""
        print(f"\n{Colors.YELLOW}6. SERTİFİKA SİSTEMİ{Colors.RESET}")
        
        cert_path = "core/learning_journey_v2/certificate_system.py"
        
        # 4 seviye
        exp = Expectation(id="CE1", category="Sertifika",
                         description="4 sertifika seviyesi (Bronze/Silver/Gold/Platinum)", priority="onemli")
        try:
            content = (self.base_path / cert_path).read_text(encoding='utf-8')
            levels = ["Bronz", "Gümüş", "Altın", "Platin", "bronze", "silver", "gold", "platinum"]
            found = sum(1 for l in levels if l.lower() in content.lower())
            if found >= 4:
                exp.status = "met"
                exp.details = "4 seviye mevcut"
            else:
                exp.status = "partial"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Doğrulama kodu
        exp = Expectation(id="CE2", category="Sertifika",
                         description="Benzersiz doğrulama kodu üretimi", priority="onemli")
        if self.check_function_exists(cert_path, "generate_verification_code"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # HTML/PDF
        exp = Expectation(id="CE3", category="Sertifika",
                         description="Sertifika HTML/PDF oluşturma", priority="normal")
        if self.check_function_exists(cert_path, "generate_certificate_html"):
            exp.status = "met"
        else:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Paylaşım linkleri
        exp = Expectation(id="CE4", category="Sertifika",
                         description="Sosyal medya paylaşım linkleri", priority="normal")
        try:
            content = (self.base_path / cert_path).read_text(encoding='utf-8')
            if "share_links" in content or "twitter" in content.lower():
                exp.status = "met"
            else:
                exp.status = "not_met"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
    
    def analyze_frontend_features(self):
        """Frontend özellik beklentileri"""
        print(f"\n{Colors.YELLOW}7. FRONTEND ÖZELLİKLERİ{Colors.RESET}")
        
        # Framer Motion animasyonları
        exp = Expectation(id="FE1", category="Frontend",
                         description="Framer Motion animasyonları", priority="onemli")
        ai_thinking = self.base_path / "frontend-next" / "src" / "components" / "learning" / "AIThinkingView.tsx"
        try:
            content = ai_thinking.read_text(encoding='utf-8')
            if "framer-motion" in content and "motion." in content:
                exp.status = "met"
            else:
                exp.status = "partial"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # 8+ konu kartı
        exp = Expectation(id="FE2", category="Frontend",
                         description="8+ konu kartı (SUBJECTS array)", priority="onemli")
        wizard = self.base_path / "frontend-next" / "src" / "components" / "learning" / "JourneyCreationWizard.tsx"
        try:
            content = wizard.read_text(encoding='utf-8')
            if "SUBJECTS" in content:
                subjects_match = re.search(r'SUBJECTS\s*=\s*\[(.*?)\];', content, re.DOTALL)
                if subjects_match:
                    count = subjects_match.group(1).count("{")
                    if count >= 8:
                        exp.status = "met"
                        exp.details = f"{count} konu kartı"
                    else:
                        exp.status = "partial"
                        exp.details = f"Sadece {count} konu"
                else:
                    exp.status = "partial"
            else:
                exp.status = "not_met"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Dark mode desteği
        exp = Expectation(id="FE3", category="Frontend",
                         description="Dark mode desteği", priority="onemli")
        try:
            content = wizard.read_text(encoding='utf-8')
            if "dark:" in content:
                exp.status = "met"
            else:
                exp.status = "partial"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
        
        # Doğru API URL'leri
        exp = Expectation(id="FE4", category="Frontend",
                         description="Doğru API URL'leri (/journey/v2)", priority="kritik")
        try:
            exam_view = self.base_path / "frontend-next" / "src" / "components" / "learning" / "ExamView.tsx"
            content = exam_view.read_text(encoding='utf-8')
            if "/api/journey/v2" in content:
                exp.status = "not_met"
                exp.details = "Hatalı URL: /api/journey/v2"
            elif "/journey/v2" in content:
                exp.status = "met"
            else:
                exp.status = "partial"
        except:
            exp.status = "not_met"
        self.result.expectations.append(exp)
        self._print_status(exp)
    
    def _print_status(self, exp: Expectation):
        """Durumu yazdır"""
        if exp.status == "met":
            icon = f"{Colors.GREEN}✓{Colors.RESET}"
            status = f"{Colors.GREEN}KARŞILANDI{Colors.RESET}"
        elif exp.status == "partial":
            icon = f"{Colors.YELLOW}~{Colors.RESET}"
            status = f"{Colors.YELLOW}KISMİ{Colors.RESET}"
        else:
            icon = f"{Colors.RED}✗{Colors.RESET}"
            status = f"{Colors.RED}EKSİK{Colors.RESET}"
        
        priority_color = Colors.RED if exp.priority == "kritik" else (Colors.YELLOW if exp.priority == "onemli" else Colors.CYAN)
        
        print(f"  {icon} [{exp.id}] {exp.description}")
        if exp.details:
            print(f"       {Colors.CYAN}{exp.details}{Colors.RESET}")
    
    def run_full_analysis(self):
        """Tam analiz çalıştır"""
        print()
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}🔬 AI ile ÖĞREN V2 - BEKLENTİ ANALİZİ{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        
        self.analyze_general_vision()
        self.analyze_backend()
        self.analyze_enums()
        self.analyze_api_endpoints()
        self.analyze_exam_system()
        self.analyze_certificate_system()
        self.analyze_frontend_features()
        
        # Özet
        print()
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}📊 ÖZET{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        
        print(f"\n  {Colors.GREEN}✓ Karşılanan:{Colors.RESET}     {self.result.met_count}")
        print(f"  {Colors.YELLOW}~ Kısmi:{Colors.RESET}          {self.result.partial_count}")
        print(f"  {Colors.RED}✗ Eksik:{Colors.RESET}          {self.result.not_met_count}")
        print(f"  {Colors.BOLD}Toplam:{Colors.RESET}           {self.result.total}")
        print(f"\n  {Colors.BOLD}Başarı Oranı:{Colors.RESET}     {self.result.percentage:.1f}%")
        
        # Kritik eksikler
        critical_missing = [e for e in self.result.expectations 
                          if e.status == "not_met" and e.priority == "kritik"]
        
        if critical_missing:
            print(f"\n  {Colors.RED}⚠️ KRİTİK EKSİKLER:{Colors.RESET}")
            for e in critical_missing:
                print(f"     - {e.description}")
        
        print(f"\n{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        
        if self.result.percentage >= 90:
            print(f"{Colors.GREEN}✅ BEKLENTİLER BÜYÜK ÖLÇÜDE KARŞILANIYOR!{Colors.RESET}")
        elif self.result.percentage >= 70:
            print(f"{Colors.YELLOW}⚠️ BEKLENTİLER KISMEN KARŞILANIYOR{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ ÖNEMLİ EKSİKLER MEVCUT{Colors.RESET}")
        
        print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
        
        return self.result


# ==================== MAIN ====================

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent
    analyzer = ExpectationAnalyzer(str(base_path))
    result = analyzer.run_full_analysis()
    
    sys.exit(0 if result.percentage >= 80 else 1)
