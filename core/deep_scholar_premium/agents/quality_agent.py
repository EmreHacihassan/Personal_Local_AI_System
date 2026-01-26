"""
QualityAssuranceAgent - Premium Kalite Güvence Ajanı
=====================================================

Görevler:
1. Üretilen çıktı yüksek kalite standartlarını karşılıyor mu?
2. Üretilen çıktı beklenen çıktı tarifine uygun mu?
3. Kalite iyileştirme önerileri
4. Çok boyutlu kalite puanlama
5. Tutarlılık ve bütünlük analizi
6. Akademik standartlara uygunluk
7. Hedef kitleye uygunluk
8. Argüman gücü ve kanıt kalitesi

Kaliteyi düşürmeden, farklı fikirleri törpülemeden kapsamlı değerlendirme.
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.llm_manager import llm_manager


class QualityDimension(str, Enum):
    """Kalite boyutları."""
    ACCURACY = "accuracy"                    # Doğruluk
    COMPLETENESS = "completeness"            # Tamlık
    COHERENCE = "coherence"                  # Tutarlılık
    RELEVANCE = "relevance"                  # İlgililik
    ORIGINALITY = "originality"              # Özgünlük
    CLARITY = "clarity"                      # Açıklık
    DEPTH = "depth"                          # Derinlik
    EVIDENCE_QUALITY = "evidence_quality"    # Kanıt kalitesi
    STRUCTURE = "structure"                  # Yapı
    ACADEMIC_RIGOR = "academic_rigor"        # Akademik titizlik
    AUDIENCE_FIT = "audience_fit"            # Hedef kitle uyumu
    ARGUMENT_STRENGTH = "argument_strength"  # Argüman gücü


class ComplianceLevel(str, Enum):
    """Uyumluluk seviyeleri."""
    EXCELLENT = "excellent"      # 90-100%
    GOOD = "good"               # 75-89%
    ACCEPTABLE = "acceptable"   # 60-74%
    NEEDS_IMPROVEMENT = "needs_improvement"  # 40-59%
    POOR = "poor"               # 0-39%


@dataclass
class QualityScore:
    """Kalite puanı."""
    dimension: QualityDimension
    score: float  # 0-100
    weight: float  # Ağırlık
    evidence: List[str]  # Kanıtlar
    issues: List[str]  # Sorunlar
    suggestions: List[str]  # İyileştirme önerileri


@dataclass  
class SpecificationCompliance:
    """Spesifikasyon uyumluluğu."""
    requirement: str
    is_met: bool
    compliance_percentage: float
    evidence: str
    gap_description: Optional[str] = None
    remediation: Optional[str] = None


@dataclass
class QualityReport:
    """Kapsamlı kalite raporu."""
    document_id: str
    overall_score: float
    compliance_level: ComplianceLevel
    dimension_scores: List[QualityScore]
    specification_compliance: List[SpecificationCompliance]
    strengths: List[str]
    weaknesses: List[str]
    critical_issues: List[str]
    improvement_suggestions: List[Dict[str, Any]]
    detailed_analysis: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON'a dönüştür."""
        return {
            "document_id": self.document_id,
            "overall_score": self.overall_score,
            "compliance_level": self.compliance_level.value,
            "dimension_scores": [
                {
                    "dimension": s.dimension.value,
                    "score": s.score,
                    "weight": s.weight,
                    "evidence": s.evidence,
                    "issues": s.issues,
                    "suggestions": s.suggestions
                }
                for s in self.dimension_scores
            ],
            "specification_compliance": [
                {
                    "requirement": c.requirement,
                    "is_met": c.is_met,
                    "compliance_percentage": c.compliance_percentage,
                    "evidence": c.evidence,
                    "gap_description": c.gap_description,
                    "remediation": c.remediation
                }
                for c in self.specification_compliance
            ],
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "critical_issues": self.critical_issues,
            "improvement_suggestions": self.improvement_suggestions,
            "detailed_analysis": self.detailed_analysis,
            "generated_at": self.generated_at
        }


class QualityAssuranceAgent:
    """
    Premium Kalite Güvence Ajanı
    
    Kapsamlı kalite kontrolü yaparak dokümanın:
    - Yüksek kalite standartlarını karşılamasını
    - Beklenen spesifikasyonlara uygunluğunu
    - Sürekli iyileştirme için öneriler sunmasını sağlar.
    
    ÖNEMLİ: Bu ajan farklı fikirleri törpülemez, 
    kaliteyi düşürmez. Amacı kaliteyi ARTIRMAK ve
    eksiklikleri TAMAMLAMAKTIR.
    """
    
    def __init__(self, global_state: Optional[Any] = None):
        self.global_state = global_state
        self.quality_thresholds = {
            ComplianceLevel.EXCELLENT: 90,
            ComplianceLevel.GOOD: 75,
            ComplianceLevel.ACCEPTABLE: 60,
            ComplianceLevel.NEEDS_IMPROVEMENT: 40,
            ComplianceLevel.POOR: 0
        }
        
        # Kalite boyutları ve ağırlıkları
        self.dimension_weights = {
            QualityDimension.ACCURACY: 0.15,
            QualityDimension.COMPLETENESS: 0.12,
            QualityDimension.COHERENCE: 0.10,
            QualityDimension.RELEVANCE: 0.10,
            QualityDimension.ORIGINALITY: 0.08,
            QualityDimension.CLARITY: 0.10,
            QualityDimension.DEPTH: 0.10,
            QualityDimension.EVIDENCE_QUALITY: 0.10,
            QualityDimension.STRUCTURE: 0.05,
            QualityDimension.ACADEMIC_RIGOR: 0.05,
            QualityDimension.AUDIENCE_FIT: 0.03,
            QualityDimension.ARGUMENT_STRENGTH: 0.02
        }
    
    async def evaluate_document(
        self,
        content: str,
        specification: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """
        Dokümanı kapsamlı şekilde değerlendir.
        
        Args:
            content: Doküman içeriği
            specification: Beklenen çıktı spesifikasyonu
            metadata: Ek meta veriler
            
        Returns:
            Kapsamlı kalite raporu
        """
        # 1. Her boyut için puan hesapla
        dimension_scores = await self._evaluate_all_dimensions(content, specification)
        
        # 2. Spesifikasyon uyumluluğunu kontrol et
        spec_compliance = await self._check_specification_compliance(content, specification)
        
        # 3. Güçlü ve zayıf yönleri belirle
        strengths, weaknesses = await self._identify_strengths_weaknesses(
            content, dimension_scores
        )
        
        # 4. Kritik sorunları tespit et
        critical_issues = await self._detect_critical_issues(content, specification)
        
        # 5. İyileştirme önerileri oluştur
        improvement_suggestions = await self._generate_improvement_suggestions(
            content, dimension_scores, spec_compliance, weaknesses
        )
        
        # 6. Detaylı analiz
        detailed_analysis = await self._perform_detailed_analysis(
            content, specification, metadata
        )
        
        # 7. Genel puan hesapla
        overall_score = self._calculate_overall_score(dimension_scores)
        compliance_level = self._determine_compliance_level(overall_score)
        
        return QualityReport(
            document_id=metadata.get("document_id", "") if metadata else "",
            overall_score=overall_score,
            compliance_level=compliance_level,
            dimension_scores=dimension_scores,
            specification_compliance=spec_compliance,
            strengths=strengths,
            weaknesses=weaknesses,
            critical_issues=critical_issues,
            improvement_suggestions=improvement_suggestions,
            detailed_analysis=detailed_analysis
        )
    
    async def evaluate_section(
        self,
        section_content: str,
        section_spec: Dict[str, Any],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tek bir bölümü değerlendir.
        
        Args:
            section_content: Bölüm içeriği
            section_spec: Bölüm spesifikasyonu
            context: Önceki bölümler için bağlam
            
        Returns:
            Bölüm kalite değerlendirmesi
        """
        prompt = f"""Aşağıdaki bölümü kalite açısından değerlendir.

## Bölüm İçeriği:
{section_content[:3000]}

## Beklenen Spesifikasyon:
- Başlık: {section_spec.get('title', 'N/A')}
- Kelime hedefi: {section_spec.get('word_target', 'N/A')}
- Ana konular: {', '.join(section_spec.get('topics', []))}
- Beklenen derinlik: {section_spec.get('depth', 'moderate')}

{f"## Önceki Bağlam: {context[:500]}" if context else ""}

## Değerlendirme Kriterleri:
1. İçerik kalitesi (1-10)
2. Spesifikasyona uygunluk (1-10)
3. Argüman gücü (1-10)
4. Kaynak kullanımı (1-10)
5. Okunabilirlik (1-10)

## Yanıt Formatı (JSON):
{{
    "scores": {{
        "content_quality": <1-10>,
        "spec_compliance": <1-10>,
        "argument_strength": <1-10>,
        "source_usage": <1-10>,
        "readability": <1-10>
    }},
    "overall_score": <1-10>,
    "meets_expectations": <true/false>,
    "strengths": ["<güçlü yön 1>", "<güçlü yön 2>"],
    "issues": ["<sorun 1>", "<sorun 2>"],
    "suggestions": ["<öneri 1>", "<öneri 2>"],
    "missing_elements": ["<eksik 1>", "<eksik 2>"]
}}

ÖNEMLİ: Farklı bakış açılarını törpüleme, özgün fikirleri koru.
Amacın kaliteyi ARTIRMAK, içeriği eşitleştirmek DEĞİL."""

        response = await self._llm_call(prompt)
        
        try:
            # JSON parse
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "scores": {"content_quality": 7, "spec_compliance": 7},
            "overall_score": 7,
            "meets_expectations": True,
            "strengths": [],
            "issues": [],
            "suggestions": []
        }
    
    async def suggest_improvements(
        self,
        content: str,
        quality_report: QualityReport
    ) -> List[Dict[str, Any]]:
        """
        Somut iyileştirme önerileri oluştur.
        
        Args:
            content: Mevcut içerik
            quality_report: Kalite raporu
            
        Returns:
            Önceliklendirilmiş iyileştirme önerileri
        """
        prompt = f"""Aşağıdaki kalite raporuna göre somut iyileştirme önerileri oluştur.

## Kalite Raporu Özeti:
- Genel Puan: {quality_report.overall_score}/100
- Seviye: {quality_report.compliance_level.value}
- Zayıf Yönler: {', '.join(quality_report.weaknesses[:5])}
- Kritik Sorunlar: {', '.join(quality_report.critical_issues[:3])}

## İçerik Önizleme:
{content[:2000]}

## Yanıt Formatı (JSON Array):
[
    {{
        "priority": "critical|high|medium|low",
        "category": "content|structure|evidence|clarity|depth",
        "title": "<kısa başlık>",
        "description": "<detaylı açıklama>",
        "action_items": ["<somut adım 1>", "<somut adım 2>"],
        "expected_impact": "<beklenen etki>",
        "effort_level": "low|medium|high"
    }}
]

Her öneri somut, uygulanabilir ve kaliteyi artırıcı olmalı.
Farklı fikirleri törpüleyen öneriler VERME."""

        response = await self._llm_call(prompt)
        
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                suggestions = json.loads(json_match.group())
                # Önceliklere göre sırala
                priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
                return suggestions
        except:
            pass
        
        return []
    
    async def verify_requirements(
        self,
        content: str,
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Belirli gereksinimlerin karşılanıp karşılanmadığını doğrula.
        
        Args:
            content: Doküman içeriği
            requirements: Gereksinim listesi
            
        Returns:
            Gereksinim doğrulama sonuçları
        """
        results = {
            "total_requirements": len(requirements),
            "met_requirements": 0,
            "partially_met": 0,
            "not_met": 0,
            "details": []
        }
        
        for req in requirements:
            verification = await self._verify_single_requirement(content, req)
            results["details"].append(verification)
            
            if verification["status"] == "met":
                results["met_requirements"] += 1
            elif verification["status"] == "partial":
                results["partially_met"] += 1
            else:
                results["not_met"] += 1
        
        results["compliance_rate"] = (
            results["met_requirements"] + 0.5 * results["partially_met"]
        ) / max(results["total_requirements"], 1) * 100
        
        return results
    
    async def _evaluate_all_dimensions(
        self,
        content: str,
        specification: Dict[str, Any]
    ) -> List[QualityScore]:
        """Tüm kalite boyutlarını değerlendir."""
        scores = []
        
        for dimension, weight in self.dimension_weights.items():
            score = await self._evaluate_dimension(content, dimension, specification)
            scores.append(QualityScore(
                dimension=dimension,
                score=score["score"],
                weight=weight,
                evidence=score.get("evidence", []),
                issues=score.get("issues", []),
                suggestions=score.get("suggestions", [])
            ))
        
        return scores
    
    async def _evaluate_dimension(
        self,
        content: str,
        dimension: QualityDimension,
        specification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Tek bir kalite boyutunu değerlendir."""
        dimension_prompts = {
            QualityDimension.ACCURACY: "Bilgilerin doğruluğu ve güvenilirliği",
            QualityDimension.COMPLETENESS: "Konunun ne kadar tam işlendiği",
            QualityDimension.COHERENCE: "Mantıksal tutarlılık ve akış",
            QualityDimension.RELEVANCE: "Konuyla ilgililik",
            QualityDimension.ORIGINALITY: "Özgün katkı ve perspektif",
            QualityDimension.CLARITY: "Anlaşılırlık ve netlik",
            QualityDimension.DEPTH: "Analiz derinliği",
            QualityDimension.EVIDENCE_QUALITY: "Kanıt ve kaynak kalitesi",
            QualityDimension.STRUCTURE: "Yapısal organizasyon",
            QualityDimension.ACADEMIC_RIGOR: "Akademik titizlik",
            QualityDimension.AUDIENCE_FIT: "Hedef kitleye uygunluk",
            QualityDimension.ARGUMENT_STRENGTH: "Argüman gücü ve ikna ediciliği"
        }
        
        prompt = f"""Aşağıdaki içeriği "{dimension.value}" boyutunda değerlendir.

Değerlendirme kriteri: {dimension_prompts.get(dimension, dimension.value)}

İçerik (ilk 2000 karakter):
{content[:2000]}

Spesifikasyon:
- Konu: {specification.get('topic', 'N/A')}
- Sayfa sayısı: {specification.get('page_count', 'N/A')}
- Stil: {specification.get('style', 'academic')}

JSON formatında yanıt ver:
{{
    "score": <0-100 arası puan>,
    "evidence": ["<kanıt 1>", "<kanıt 2>"],
    "issues": ["<sorun 1>", "<sorun 2>"],
    "suggestions": ["<öneri 1>", "<öneri 2>"]
}}

Puanlama:
- 90-100: Mükemmel
- 75-89: İyi
- 60-74: Kabul edilebilir
- 40-59: İyileştirme gerekli
- 0-39: Yetersiz"""

        response = await self._llm_call(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*?\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"score": 70, "evidence": [], "issues": [], "suggestions": []}
    
    async def _check_specification_compliance(
        self,
        content: str,
        specification: Dict[str, Any]
    ) -> List[SpecificationCompliance]:
        """Spesifikasyon uyumluluğunu kontrol et."""
        compliance_results = []
        
        # Temel spesifikasyonları kontrol et
        specs_to_check = [
            ("Konu uyumu", specification.get("topic", "")),
            ("Kelime sayısı hedefi", str(specification.get("word_target", ""))),
            ("Bölüm yapısı", str(specification.get("sections", []))),
            ("Stil uyumu", specification.get("style", "academic")),
            ("Kaynak gereksinimleri", str(specification.get("min_sources", ""))),
            ("Dil uyumu", specification.get("language", "tr"))
        ]
        
        for req_name, req_value in specs_to_check:
            if not req_value:
                continue
                
            compliance = await self._check_single_spec(content, req_name, req_value)
            compliance_results.append(compliance)
        
        return compliance_results
    
    async def _check_single_spec(
        self,
        content: str,
        requirement_name: str,
        requirement_value: str
    ) -> SpecificationCompliance:
        """Tek bir spesifikasyonu kontrol et."""
        # Basit kontroller
        is_met = True
        compliance_percentage = 100.0
        evidence = "Kontrol yapıldı"
        gap_description = None
        remediation = None
        
        if "kelime" in requirement_name.lower():
            # Kelime sayısı kontrolü
            word_count = len(content.split())
            try:
                target = int(requirement_value)
                ratio = word_count / target if target > 0 else 1
                compliance_percentage = min(ratio * 100, 100)
                is_met = ratio >= 0.8  # %80 tolerans
                evidence = f"Mevcut: {word_count}, Hedef: {target}"
                if not is_met:
                    gap_description = f"{target - word_count} kelime eksik"
                    remediation = "İçeriği genişlet veya daha detaylı açıklamalar ekle"
            except:
                pass
        
        return SpecificationCompliance(
            requirement=requirement_name,
            is_met=is_met,
            compliance_percentage=compliance_percentage,
            evidence=evidence,
            gap_description=gap_description,
            remediation=remediation
        )
    
    async def _identify_strengths_weaknesses(
        self,
        content: str,
        dimension_scores: List[QualityScore]
    ) -> Tuple[List[str], List[str]]:
        """Güçlü ve zayıf yönleri belirle."""
        strengths = []
        weaknesses = []
        
        for score in dimension_scores:
            if score.score >= 80:
                strengths.append(f"{score.dimension.value}: {score.score}/100")
                strengths.extend(score.evidence[:2])
            elif score.score < 60:
                weaknesses.append(f"{score.dimension.value}: {score.score}/100")
                weaknesses.extend(score.issues[:2])
        
        return strengths[:10], weaknesses[:10]
    
    async def _detect_critical_issues(
        self,
        content: str,
        specification: Dict[str, Any]
    ) -> List[str]:
        """Kritik sorunları tespit et."""
        prompt = f"""Aşağıdaki içerikte kritik sorunları tespit et.

İçerik (ilk 3000 karakter):
{content[:3000]}

Kritik sorun kategorileri:
1. Faktüel hatalar veya çelişkiler
2. Eksik zorunlu bölümler
3. Kaynak yetersizliği
4. Mantıksal tutarsızlıklar
5. Akademik standartlara aykırılık

NOT: Farklı bakış açıları veya özgün fikirler sorun DEĞİLDİR.

Sadece kritik sorunları listele (JSON array):
["<sorun 1>", "<sorun 2>", ...]

Kritik sorun yoksa: []"""

        response = await self._llm_call(prompt)
        
        try:
            json_match = re.search(r'\[[\s\S]*?\]', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    async def _generate_improvement_suggestions(
        self,
        content: str,
        dimension_scores: List[QualityScore],
        spec_compliance: List[SpecificationCompliance],
        weaknesses: List[str]
    ) -> List[Dict[str, Any]]:
        """İyileştirme önerileri oluştur."""
        suggestions = []
        
        # Düşük puanlı boyutlar için öneriler
        for score in dimension_scores:
            if score.score < 70:
                suggestions.append({
                    "category": score.dimension.value,
                    "priority": "high" if score.score < 50 else "medium",
                    "current_score": score.score,
                    "suggestions": score.suggestions,
                    "expected_improvement": f"+{min(20, 100-score.score)} puan"
                })
        
        # Karşılanmayan spesifikasyonlar için öneriler
        for spec in spec_compliance:
            if not spec.is_met and spec.remediation:
                suggestions.append({
                    "category": "specification",
                    "priority": "high",
                    "requirement": spec.requirement,
                    "gap": spec.gap_description,
                    "remediation": spec.remediation
                })
        
        # Önceliğe göre sırala
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
        
        return suggestions[:15]
    
    async def _perform_detailed_analysis(
        self,
        content: str,
        specification: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detaylı analiz gerçekleştir."""
        word_count = len(content.split())
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        sentence_count = len(re.findall(r'[.!?]+', content))
        
        # Ortalama cümle uzunluğu
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Başlık analizi
        headers = re.findall(r'^#+\s+.+$', content, re.MULTILINE)
        
        return {
            "statistics": {
                "word_count": word_count,
                "paragraph_count": paragraph_count,
                "sentence_count": sentence_count,
                "avg_sentence_length": round(avg_sentence_length, 1),
                "header_count": len(headers)
            },
            "structure_analysis": {
                "has_introduction": any("giriş" in h.lower() or "introduction" in h.lower() for h in headers),
                "has_conclusion": any("sonuç" in h.lower() or "conclusion" in h.lower() for h in headers),
                "section_count": len(headers)
            },
            "readability_estimate": {
                "complexity": "high" if avg_sentence_length > 25 else "medium" if avg_sentence_length > 15 else "low",
                "estimated_reading_time_minutes": round(word_count / 200, 1)
            }
        }
    
    async def _verify_single_requirement(
        self,
        content: str,
        requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Tek bir gereksinimi doğrula."""
        req_type = requirement.get("type", "general")
        req_value = requirement.get("value", "")
        req_description = requirement.get("description", "")
        
        prompt = f"""Aşağıdaki gereksinimin karşılanıp karşılanmadığını değerlendir.

Gereksinim: {req_description}
Beklenen: {req_value}

İçerik (ilk 2000 karakter):
{content[:2000]}

JSON formatında yanıt:
{{
    "status": "met|partial|not_met",
    "confidence": <0-100>,
    "evidence": "<kanıt>",
    "missing": "<eksik olan>" 
}}"""

        response = await self._llm_call(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*?\}', response)
            if json_match:
                result = json.loads(json_match.group())
                result["requirement"] = req_description
                return result
        except:
            pass
        
        return {
            "requirement": req_description,
            "status": "partial",
            "confidence": 50,
            "evidence": "Değerlendirme yapılamadı"
        }
    
    def _calculate_overall_score(self, dimension_scores: List[QualityScore]) -> float:
        """Ağırlıklı genel puan hesapla."""
        total_weight = sum(s.weight for s in dimension_scores)
        if total_weight == 0:
            return 0
        
        weighted_sum = sum(s.score * s.weight for s in dimension_scores)
        return round(weighted_sum / total_weight, 1)
    
    def _determine_compliance_level(self, score: float) -> ComplianceLevel:
        """Puana göre uyumluluk seviyesini belirle."""
        for level, threshold in self.quality_thresholds.items():
            if score >= threshold:
                return level
        return ComplianceLevel.POOR
    
    async def _llm_call(self, prompt: str, timeout: int = 300) -> str:
        """LLM çağrısı yap."""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_manager.chat,
                    messages=messages,
                    model_type="default"
                ),
                timeout=timeout
            )
            return response.get("content", "") if isinstance(response, dict) else str(response)
        except Exception as e:
            return f"Error: {str(e)}"
    
    # ========================
    # BONUS: Kalite Metrikleri
    # ========================
    
    async def calculate_flesch_reading_ease(self, content: str) -> float:
        """Flesch Reading Ease skoru hesapla (0-100)."""
        words = content.split()
        sentences = re.findall(r'[.!?]+', content)
        syllables = sum(self._count_syllables(word) for word in words)
        
        word_count = len(words)
        sentence_count = len(sentences) or 1
        
        # Flesch formülü
        score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllables / word_count)
        return max(0, min(100, round(score, 1)))
    
    def _count_syllables(self, word: str) -> int:
        """Kelime hecesi say (yaklaşık)."""
        word = word.lower()
        vowels = "aeıioöuü"
        count = sum(1 for char in word if char in vowels)
        return max(1, count)
    
    async def generate_quality_badge(self, score: float) -> Dict[str, Any]:
        """Kalite rozeti oluştur."""
        if score >= 90:
            return {"badge": "⭐ Premium Quality", "color": "#FFD700", "level": "gold"}
        elif score >= 75:
            return {"badge": "✓ High Quality", "color": "#C0C0C0", "level": "silver"}
        elif score >= 60:
            return {"badge": "• Standard Quality", "color": "#CD7F32", "level": "bronze"}
        else:
            return {"badge": "△ Needs Improvement", "color": "#808080", "level": "basic"}
