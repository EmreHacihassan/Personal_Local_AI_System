"""
ConsistencyChecker - Tutarlılık Kontrol Modülü
==============================================

Kontrol Alanları:
1. Terminoloji tutarlılığı
2. Stil tutarlılığı
3. Zaman kiplerinde tutarlılık
4. Kısaltma kullanımı
5. Sayı ve birim formatları
6. Referans tutarlılığı
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

from core.llm_manager import llm_manager


class InconsistencyType(str, Enum):
    """Tutarsızlık türü."""
    TERMINOLOGY = "terminology"      # Farklı terimler aynı kavram için
    SPELLING = "spelling"           # Yazım farklılıkları
    ABBREVIATION = "abbreviation"   # Kısaltma tutarsızlığı
    TENSE = "tense"                # Zaman kipi
    STYLE = "style"                 # Stil tutarsızlığı
    FORMAT = "format"               # Format tutarsızlığı
    REFERENCE = "reference"         # Referans tutarsızlığı
    NUMBERING = "numbering"         # Numaralandırma


class Severity(str, Enum):
    """Ciddiyet seviyesi."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Inconsistency:
    """Tutarsızlık."""
    type: InconsistencyType
    description: str
    instances: List[str]
    locations: List[str]
    severity: Severity
    suggestion: str


@dataclass
class ConsistencyReport:
    """Tutarlılık raporu."""
    overall_score: float  # 0-100
    total_issues: int
    inconsistencies: List[Inconsistency]
    
    # Kategorik sonuçlar
    by_type: Dict[str, int] = field(default_factory=dict)
    by_severity: Dict[str, int] = field(default_factory=dict)
    
    # Özet
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        lines = [
            "# 🔄 Tutarlılık Raporu",
            "",
            f"**Tutarlılık Puanı:** {round(self.overall_score)}/100",
            f"**Toplam Sorun:** {self.total_issues}",
            ""
        ]
        
        if self.by_severity:
            lines.extend([
                "## Ciddiyet Dağılımı",
                f"- Kritik: {self.by_severity.get('critical', 0)}",
                f"- Yüksek: {self.by_severity.get('high', 0)}",
                f"- Orta: {self.by_severity.get('medium', 0)}",
                f"- Düşük: {self.by_severity.get('low', 0)}",
                ""
            ])
        
        if self.inconsistencies:
            lines.extend(["## Tespit Edilen Tutarsızlıklar", ""])
            for i, inc in enumerate(self.inconsistencies[:10], 1):
                lines.append(f"### {i}. {inc.type.value.replace('_', ' ').title()}")
                lines.append(f"**Açıklama:** {inc.description}")
                lines.append(f"**Örnekler:** {', '.join(inc.instances[:3])}")
                lines.append(f"**Öneri:** {inc.suggestion}")
                lines.append("")
        
        return "\n".join(lines)


class ConsistencyChecker:
    """
    Tutarlılık Kontrol Modülü
    
    Doküman genelinde tutarlılığı denetler.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Bilinen alternatif yazımlar
        self.known_variants = {
            # Türkçe-İngilizce alternatifler
            ("yapay zeka", "artificial intelligence", "AI", "YZ"),
            ("makine öğrenmesi", "machine learning", "ML"),
            ("derin öğrenme", "deep learning", "DL"),
            ("veri bilimi", "data science"),
            ("büyük veri", "big data"),
        }
        
        # Format kalıpları
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',     # DD/MM/YYYY
            r'\d{1,2}\.\d{1,2}\.\d{2,4}',   # DD.MM.YYYY
            r'\d{1,2}-\d{1,2}-\d{2,4}',     # DD-MM-YYYY
            r'\d{4}-\d{2}-\d{2}'             # YYYY-MM-DD
        ]
        
        self.number_patterns = [
            r'\d{1,3}(?:\.\d{3})+',          # 1.000.000 (TR)
            r'\d{1,3}(?:,\d{3})+',           # 1,000,000 (EN)
        ]
    
    async def check_document(
        self,
        content: str,
        sections: Optional[List[Dict[str, str]]] = None
    ) -> ConsistencyReport:
        """
        Dokümanı tutarlılık için kontrol et.
        
        Args:
            content: Doküman içeriği
            sections: Bölümler (opsiyonel)
            
        Returns:
            Tutarlılık raporu
        """
        inconsistencies: List[Inconsistency] = []
        
        # Terminoloji kontrolü
        term_issues = await self._check_terminology(content)
        inconsistencies.extend(term_issues)
        
        # Kısaltma kontrolü
        abbr_issues = self._check_abbreviations(content)
        inconsistencies.extend(abbr_issues)
        
        # Format kontrolü
        format_issues = self._check_formats(content)
        inconsistencies.extend(format_issues)
        
        # Stil kontrolü
        style_issues = await self._check_style(content)
        inconsistencies.extend(style_issues)
        
        # Zaman kipi kontrolü
        tense_issues = await self._check_tense(content)
        inconsistencies.extend(tense_issues)
        
        # Referans kontrolü (varsa)
        ref_issues = self._check_references(content)
        inconsistencies.extend(ref_issues)
        
        # Puan hesapla
        score = self._calculate_score(inconsistencies)
        
        # Rapor oluştur
        return self._create_report(score, inconsistencies)
    
    async def _check_terminology(
        self,
        content: str
    ) -> List[Inconsistency]:
        """Terminoloji tutarlılığını kontrol et."""
        issues = []
        content_lower = content.lower()
        
        # Bilinen varyantları kontrol et
        for variant_group in self.known_variants:
            found_variants = []
            for variant in variant_group:
                if variant.lower() in content_lower:
                    found_variants.append(variant)
            
            if len(found_variants) > 1:
                issues.append(Inconsistency(
                    type=InconsistencyType.TERMINOLOGY,
                    description=f"Aynı kavram için farklı terimler kullanılmış",
                    instances=found_variants,
                    locations=[],
                    severity=Severity.MEDIUM,
                    suggestion=f"Tek bir terim seçin ve tutarlı kullanın (önerilen: {found_variants[0]})"
                ))
        
        # LLM ile derin analiz
        prompt = f"""Bu metinde terminoloji tutarsızlıklarını tespit et.
Aynı kavram için farklı terimler kullanılmış mı?

Metin:
{content[:3000]}

JSON formatında yanıt ver:
[{{"term1": "", "term2": "", "concept": ""}}]
Tutarsızlık yoksa boş array döndür: []"""

        try:
            response = await self._llm_call(prompt)
            import json
            match = re.search(r'\[[\s\S]*\]', response)
            if match:
                data = json.loads(match.group())
                for item in data:
                    if item.get("term1") and item.get("term2"):
                        issues.append(Inconsistency(
                            type=InconsistencyType.TERMINOLOGY,
                            description=f"'{item.get('concept', 'Kavram')}' için farklı terimler",
                            instances=[item["term1"], item["term2"]],
                            locations=[],
                            severity=Severity.MEDIUM,
                            suggestion=f"Tutarlı terim kullanın"
                        ))
        except:
            pass
        
        return issues
    
    def _check_abbreviations(
        self,
        content: str
    ) -> List[Inconsistency]:
        """Kısaltma kullanımını kontrol et."""
        issues = []
        
        # Kısaltmaları bul
        abbreviations = re.findall(r'\b[A-Z]{2,6}\b', content)
        abbr_counter = Counter(abbreviations)
        
        # İlk kullanımda açıklama kontrolü
        for abbr, count in abbr_counter.items():
            if count >= 2:
                # Açıklama paterni: "... (ABC)" veya "ABC (Açıklama)"
                explained = bool(re.search(
                    rf'\([^)]*{abbr}[^)]*\)|{abbr}\s*\([^)]+\)',
                    content
                ))
                
                if not explained:
                    issues.append(Inconsistency(
                        type=InconsistencyType.ABBREVIATION,
                        description=f"'{abbr}' kısaltması açıklanmamış",
                        instances=[abbr],
                        locations=[],
                        severity=Severity.LOW,
                        suggestion=f"İlk kullanımda kısaltmayı açıklayın: 'Tam Adı ({abbr})'"
                    ))
        
        return issues
    
    def _check_formats(
        self,
        content: str
    ) -> List[Inconsistency]:
        """Format tutarlılığını kontrol et."""
        issues = []
        
        # Tarih formatları
        date_formats_found = []
        for i, pattern in enumerate(self.date_patterns):
            if re.search(pattern, content):
                date_formats_found.append(i)
        
        if len(date_formats_found) > 1:
            issues.append(Inconsistency(
                type=InconsistencyType.FORMAT,
                description="Farklı tarih formatları kullanılmış",
                instances=["DD/MM/YYYY", "DD.MM.YYYY", "YYYY-MM-DD"],
                locations=[],
                severity=Severity.MEDIUM,
                suggestion="Tek bir tarih formatı kullanın (önerilen: GG.AA.YYYY)"
            ))
        
        # Sayı formatları
        tr_format = re.findall(self.number_patterns[0], content)
        en_format = re.findall(self.number_patterns[1], content)
        
        if tr_format and en_format:
            issues.append(Inconsistency(
                type=InconsistencyType.FORMAT,
                description="Farklı sayı formatları kullanılmış",
                instances=["1.000 (TR)", "1,000 (EN)"],
                locations=[],
                severity=Severity.MEDIUM,
                suggestion="Tek bir sayı formatı kullanın"
            ))
        
        return issues
    
    async def _check_style(
        self,
        content: str
    ) -> List[Inconsistency]:
        """Stil tutarlılığını kontrol et."""
        issues = []
        
        # Aktif/Pasif cümle karışımı kontrolü
        passive_indicators_tr = ["tarafından", "edilmiş", "yapılmış", "gerçekleştirilmiş"]
        passive_count = sum(content.lower().count(ind) for ind in passive_indicators_tr)
        
        # ~10 cümleden fazlaysa ve karışık kullanım varsa
        sentence_count = len(re.split(r'[.!?]', content))
        passive_ratio = passive_count / max(sentence_count, 1)
        
        if 0.2 < passive_ratio < 0.8 and sentence_count > 10:
            issues.append(Inconsistency(
                type=InconsistencyType.STYLE,
                description="Aktif ve pasif cümle kullanımı karışık",
                instances=["Aktif: 'araştırdık'", "Pasif: 'araştırılmıştır'"],
                locations=[],
                severity=Severity.LOW,
                suggestion="Akademik metinlerde tutarlı olarak pasif çatı tercih edin"
            ))
        
        return issues
    
    async def _check_tense(
        self,
        content: str
    ) -> List[Inconsistency]:
        """Zaman kipi tutarlılığını kontrol et."""
        issues = []
        
        # Basit zaman kipi analizi
        past_indicators = ["yaptı", "buldu", "gösterdi", "belirlendi"]
        present_indicators = ["yapar", "bulur", "gösterir", "belirlenir"]
        
        past_count = sum(1 for ind in past_indicators if ind in content.lower())
        present_count = sum(1 for ind in present_indicators if ind in content.lower())
        
        if past_count > 3 and present_count > 3:
            issues.append(Inconsistency(
                type=InconsistencyType.TENSE,
                description="Zaman kipi tutarsızlığı (geçmiş/geniş zaman karışık)",
                instances=["Geçmiş: 'gösterdi'", "Geniş: 'gösterir'"],
                locations=[],
                severity=Severity.MEDIUM,
                suggestion="Literatür taramasında geniş zaman, metodolojide geçmiş zaman kullanın"
            ))
        
        return issues
    
    def _check_references(
        self,
        content: str
    ) -> List[Inconsistency]:
        """Referans tutarlılığını kontrol et."""
        issues = []
        
        # APA ve IEEE karışık kullanım kontrolü
        apa_pattern = r'\([A-Z][a-z]+(?:\s+(?:&|ve)\s+[A-Z][a-z]+)?,?\s*\d{4}\)'
        ieee_pattern = r'\[\d+\]'
        
        apa_refs = re.findall(apa_pattern, content)
        ieee_refs = re.findall(ieee_pattern, content)
        
        if apa_refs and ieee_refs:
            issues.append(Inconsistency(
                type=InconsistencyType.REFERENCE,
                description="Farklı referans stilleri karışık kullanılmış",
                instances=["APA: (Smith, 2020)", "IEEE: [1]"],
                locations=[],
                severity=Severity.HIGH,
                suggestion="Tek bir referans stili kullanın (APA veya IEEE)"
            ))
        
        return issues
    
    def _calculate_score(
        self,
        inconsistencies: List[Inconsistency]
    ) -> float:
        """Tutarlılık puanı hesapla."""
        if not inconsistencies:
            return 100.0
        
        # Ciddiyet ağırlıkları
        weights = {
            Severity.LOW: 2,
            Severity.MEDIUM: 5,
            Severity.HIGH: 10,
            Severity.CRITICAL: 20
        }
        
        total_penalty = sum(weights.get(inc.severity, 5) for inc in inconsistencies)
        
        # Maksimum 100 puan düş
        score = max(0, 100 - total_penalty)
        
        return score
    
    def _create_report(
        self,
        score: float,
        inconsistencies: List[Inconsistency]
    ) -> ConsistencyReport:
        """Rapor oluştur."""
        # Kategorik sayımlar
        by_type = Counter(inc.type.value for inc in inconsistencies)
        by_severity = Counter(inc.severity.value for inc in inconsistencies)
        
        # Özet
        if score >= 90:
            summary = "Doküman yüksek tutarlılık gösteriyor."
        elif score >= 70:
            summary = "Doküman genel olarak tutarlı, bazı küçük iyileştirmeler önerilir."
        elif score >= 50:
            summary = "Orta düzeyde tutarsızlık tespit edildi. Revizyon önerilir."
        else:
            summary = "Ciddi tutarsızlık sorunları var. Kapsamlı revizyon gerekli."
        
        # Öneriler
        recommendations = []
        if by_type.get("terminology", 0) > 0:
            recommendations.append("Terim sözlüğü oluşturun ve tutarlı kullanın")
        if by_type.get("abbreviation", 0) > 0:
            recommendations.append("Kısaltmalar listesi hazırlayın ve ilk kullanımda açıklayın")
        if by_type.get("format", 0) > 0:
            recommendations.append("Stil kılavuzu belirleyin ve uygulayın")
        
        return ConsistencyReport(
            overall_score=score,
            total_issues=len(inconsistencies),
            inconsistencies=inconsistencies,
            by_type=dict(by_type),
            by_severity=dict(by_severity),
            summary=summary,
            recommendations=recommendations
        )
    
    async def _llm_call(self, prompt: str, timeout: int = 120) -> str:
        """LLM çağrısı."""
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
        except:
            return "[]"
