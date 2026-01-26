"""
EditorAgent - Premium Editör Ajanı
==================================

Görevler:
1. Dil ve gramer düzeltmeleri
2. Akış ve geçiş iyileştirmeleri
3. Tutarlılık kontrolü (terim, stil, ton)
4. Okunabilirlik optimizasyonu
5. Akademik dil standartları
6. Paragraf ve cümle yapısı
7. Başlık ve alt başlık optimizasyonu

ÖNEMLİ: Editör içeriğin ANLAMINI değiştirmez,
sadece SUNUMUNU iyileştirir.
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.llm_manager import llm_manager


class EditType(str, Enum):
    """Düzenleme türleri."""
    GRAMMAR = "grammar"              # Gramer
    SPELLING = "spelling"            # İmla
    PUNCTUATION = "punctuation"      # Noktalama
    STYLE = "style"                  # Stil
    CLARITY = "clarity"              # Netlik
    FLOW = "flow"                    # Akış
    CONSISTENCY = "consistency"      # Tutarlılık
    ACADEMIC = "academic"            # Akademik dil
    STRUCTURE = "structure"          # Yapı


class EditPriority(str, Enum):
    """Düzenleme önceliği."""
    CRITICAL = "critical"    # Anlam etkiler
    HIGH = "high"           # Önemli iyileştirme
    MEDIUM = "medium"       # Orta iyileştirme
    LOW = "low"             # Küçük iyileştirme
    OPTIONAL = "optional"   # İsteğe bağlı


@dataclass
class EditSuggestion:
    """Düzenleme önerisi."""
    edit_type: EditType
    priority: EditPriority
    original_text: str
    suggested_text: str
    explanation: str
    location: Dict[str, int]  # {paragraph, sentence, start, end}
    auto_apply: bool = False  # Otomatik uygulanabilir mi?


@dataclass
class ConsistencyIssue:
    """Tutarlılık sorunu."""
    issue_type: str  # terminology, style, tone, formatting
    description: str
    instances: List[Dict[str, str]]  # {text, location}
    recommendation: str


@dataclass
class EditingReport:
    """Düzenleme raporu."""
    document_id: str
    
    # Öneriler
    edit_suggestions: List[EditSuggestion]
    consistency_issues: List[ConsistencyIssue]
    
    # İstatistikler
    total_suggestions: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    # Puanlar
    grammar_score: float
    style_score: float
    clarity_score: float
    consistency_score: float
    overall_quality: float
    
    # Otomatik düzeltmeler
    auto_corrections: List[Dict[str, str]]
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EditorAgent:
    """
    Premium Editör Ajanı
    
    İçeriğin dilsel ve yapısal kalitesini artırır.
    İçeriğin anlamını veya argümanlarını DEĞİŞTİRMEZ.
    """
    
    def __init__(self, global_state: Optional[Any] = None):
        self.global_state = global_state
        self.language = "tr"
        
        # Akademik dil kalıpları
        self.academic_phrases = {
            "çok önemli": "kritik öneme sahip",
            "gösteriyor": "ortaya koymaktadır",
            "düşünüyorum": "değerlendirilmektedir",
            "bence": "bu bağlamda",
            "herkes bilir": "yaygın kanıya göre"
        }
        
        # Tutarsızlık kalıpları
        self.consistency_patterns = {
            "terminology": [],  # Dinamik olarak doldurulacak
            "style": ["serif/sans-serif", "formal/informal"],
            "tone": ["academic/casual", "objective/subjective"]
        }
    
    async def edit_document(
        self,
        content: str,
        document_id: str,
        style: str = "academic",
        language: str = "tr"
    ) -> EditingReport:
        """
        Dokümanı düzenle.
        
        Args:
            content: Doküman içeriği
            document_id: Doküman ID
            style: Beklenen stil
            language: Dil
            
        Returns:
            Düzenleme raporu
        """
        self.language = language
        
        # 1. Gramer ve imla kontrolü
        grammar_suggestions = await self._check_grammar(content)
        
        # 2. Stil analizi
        style_suggestions = await self._analyze_style(content, style)
        
        # 3. Netlik iyileştirmeleri
        clarity_suggestions = await self._improve_clarity(content)
        
        # 4. Tutarlılık kontrolü
        consistency_issues = await self._check_consistency(content)
        
        # 5. Akış iyileştirmeleri
        flow_suggestions = await self._improve_flow(content)
        
        # Tüm önerileri birleştir
        all_suggestions = (
            grammar_suggestions + 
            style_suggestions + 
            clarity_suggestions +
            flow_suggestions
        )
        
        # İstatistikler
        critical_count = sum(1 for s in all_suggestions if s.priority == EditPriority.CRITICAL)
        high_count = sum(1 for s in all_suggestions if s.priority == EditPriority.HIGH)
        medium_count = sum(1 for s in all_suggestions if s.priority == EditPriority.MEDIUM)
        low_count = sum(1 for s in all_suggestions if s.priority == EditPriority.LOW)
        
        # Puanlar hesapla
        grammar_score = max(0, 100 - len(grammar_suggestions) * 2)
        style_score = max(0, 100 - len(style_suggestions) * 3)
        clarity_score = max(0, 100 - len(clarity_suggestions) * 2)
        consistency_score = max(0, 100 - len(consistency_issues) * 5)
        overall_quality = (grammar_score + style_score + clarity_score + consistency_score) / 4
        
        # Otomatik düzeltmeler
        auto_corrections = [
            {"original": s.original_text, "corrected": s.suggested_text}
            for s in all_suggestions if s.auto_apply
        ]
        
        return EditingReport(
            document_id=document_id,
            edit_suggestions=all_suggestions,
            consistency_issues=consistency_issues,
            total_suggestions=len(all_suggestions),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            grammar_score=grammar_score,
            style_score=style_score,
            clarity_score=clarity_score,
            consistency_score=consistency_score,
            overall_quality=overall_quality,
            auto_corrections=auto_corrections
        )
    
    async def edit_section(
        self,
        section_content: str,
        section_title: str,
        style: str = "academic"
    ) -> Dict[str, Any]:
        """
        Tek bir bölümü düzenle.
        
        Args:
            section_content: Bölüm içeriği
            section_title: Bölüm başlığı
            style: Beklenen stil
            
        Returns:
            Düzenleme önerileri
        """
        prompt = f"""Sen bir profesyonel editörsün. Aşağıdaki bölümü düzenle.

## Bölüm: {section_title}

## İçerik:
{section_content[:3000]}

## İstenen Stil: {style}

## Görevler:
1. Gramer ve imla hatalarını bul
2. Akademik dil kullanımını kontrol et
3. Cümle yapısını değerlendir
4. Akış ve geçişleri incele
5. Tutarlılık sorunlarını tespit et

## Yanıt Formatı (JSON):
{{
    "grammar_issues": [
        {{"original": "<hatalı>", "corrected": "<düzeltilmiş>", "explanation": "<açıklama>"}}
    ],
    "style_improvements": [
        {{"original": "<mevcut>", "improved": "<iyileştirilmiş>", "reason": "<neden>"}}
    ],
    "flow_suggestions": [
        {{"location": "<konum>", "suggestion": "<öneri>"}}
    ],
    "overall_assessment": {{
        "grammar_score": <1-10>,
        "style_score": <1-10>,
        "clarity_score": <1-10>,
        "needs_revision": <true/false>
    }}
}}

ÖNEMLİ: İçeriğin ANLAMINI değiştirme, sadece SUNUMUNU iyileştir."""

        response = await self._llm_call(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "grammar_issues": [],
            "style_improvements": [],
            "flow_suggestions": [],
            "overall_assessment": {
                "grammar_score": 8,
                "style_score": 8,
                "clarity_score": 8,
                "needs_revision": False
            }
        }
    
    async def apply_edits(
        self,
        content: str,
        edits: List[EditSuggestion],
        auto_only: bool = True
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Düzenlemeleri uygula.
        
        Args:
            content: Orijinal içerik
            edits: Düzenleme önerileri
            auto_only: Sadece otomatik düzenlemeleri uygula
            
        Returns:
            (Düzenlenmiş içerik, Uygulanan değişiklikler)
        """
        edited_content = content
        applied_changes = []
        
        # Önce kritik, sonra yüksek öncelikli
        sorted_edits = sorted(
            edits,
            key=lambda x: ["critical", "high", "medium", "low", "optional"].index(x.priority.value)
        )
        
        for edit in sorted_edits:
            if auto_only and not edit.auto_apply:
                continue
            
            if edit.original_text in edited_content:
                edited_content = edited_content.replace(
                    edit.original_text,
                    edit.suggested_text,
                    1  # Sadece ilk eşleşmeyi değiştir
                )
                applied_changes.append({
                    "type": edit.edit_type.value,
                    "original": edit.original_text,
                    "new": edit.suggested_text,
                    "reason": edit.explanation
                })
        
        return edited_content, applied_changes
    
    async def _check_grammar(self, content: str) -> List[EditSuggestion]:
        """Gramer kontrolü."""
        suggestions = []
        
        # Basit Türkçe gramer kuralları
        grammar_rules = [
            (r'\bde\s+(?=[a-zğüşöçı])', 'de ', 'Ayrı yazılmalı'),
            (r'\bda\s+(?=[a-zğüşöçı])', 'da ', 'Ayrı yazılmalı'),
            (r'(?<=[a-zğüşöçı])ki\b', 'ki', '-ki eki kontrol edilmeli'),
        ]
        
        for pattern, replacement, explanation in grammar_rules:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches[:5]:  # En fazla 5 öneri
                suggestions.append(EditSuggestion(
                    edit_type=EditType.GRAMMAR,
                    priority=EditPriority.MEDIUM,
                    original_text=match.group(),
                    suggested_text=replacement,
                    explanation=explanation,
                    location={"start": match.start(), "end": match.end()},
                    auto_apply=True
                ))
        
        return suggestions
    
    async def _analyze_style(self, content: str, target_style: str) -> List[EditSuggestion]:
        """Stil analizi."""
        suggestions = []
        
        if target_style == "academic":
            # Akademik olmayan ifadeleri bul
            informal_patterns = [
                (r'\bbence\b', 'bu değerlendirmeye göre'),
                (r'\bçok\s+iyi\b', 'oldukça etkili'),
                (r'\bhiç\s+de\b', 'kesinlikle'),
                (r'\baslında\b', 'esasen'),
            ]
            
            for pattern, replacement in informal_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches[:3]:
                    suggestions.append(EditSuggestion(
                        edit_type=EditType.STYLE,
                        priority=EditPriority.LOW,
                        original_text=match.group(),
                        suggested_text=replacement,
                        explanation="Daha akademik ifade önerisi",
                        location={"start": match.start(), "end": match.end()},
                        auto_apply=False  # Stil değişiklikleri manuel onay gerektirir
                    ))
        
        return suggestions
    
    async def _improve_clarity(self, content: str) -> List[EditSuggestion]:
        """Netlik iyileştirmeleri."""
        suggestions = []
        
        # Çok uzun cümleleri bul
        sentences = re.split(r'[.!?]+', content)
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            if len(words) > 40:  # 40 kelimeden uzun cümleler
                suggestions.append(EditSuggestion(
                    edit_type=EditType.CLARITY,
                    priority=EditPriority.MEDIUM,
                    original_text=sentence[:100] + "...",
                    suggested_text="[Bölünmesi önerilen uzun cümle]",
                    explanation=f"Bu cümle {len(words)} kelime içeriyor. Okunabilirlik için bölünmesi önerilir.",
                    location={"sentence": i},
                    auto_apply=False
                ))
        
        return suggestions[:5]  # En fazla 5 öneri
    
    async def _check_consistency(self, content: str) -> List[ConsistencyIssue]:
        """Tutarlılık kontrolü."""
        issues = []
        
        # Terminoloji tutarlılığı
        terms = re.findall(r'\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)*\b', content)
        term_variations = {}
        
        for term in terms:
            lower_term = term.lower()
            if lower_term not in term_variations:
                term_variations[lower_term] = []
            if term not in term_variations[lower_term]:
                term_variations[lower_term].append(term)
        
        # Birden fazla varyasyonu olan terimleri bul
        for lower_term, variations in term_variations.items():
            if len(variations) > 1:
                issues.append(ConsistencyIssue(
                    issue_type="terminology",
                    description=f"'{lower_term}' terimi farklı şekillerde yazılmış",
                    instances=[{"text": v, "location": "document"} for v in variations],
                    recommendation=f"Tek bir yazım şekli kullanın: {variations[0]}"
                ))
        
        return issues[:10]  # En fazla 10 sorun
    
    async def _improve_flow(self, content: str) -> List[EditSuggestion]:
        """Akış iyileştirmeleri."""
        suggestions = []
        
        # Paragraf geçişlerini kontrol et
        paragraphs = content.split('\n\n')
        
        transition_words = [
            "Ayrıca", "Bununla birlikte", "Öte yandan", "Sonuç olarak",
            "Bu bağlamda", "Dolayısıyla", "Örneğin", "Benzer şekilde"
        ]
        
        for i in range(1, len(paragraphs)):
            para = paragraphs[i].strip()
            if para and not any(para.startswith(tw) for tw in transition_words):
                # Başlık veya liste öğesi değilse
                if not para.startswith('#') and not para.startswith('-') and not para.startswith('*'):
                    suggestions.append(EditSuggestion(
                        edit_type=EditType.FLOW,
                        priority=EditPriority.LOW,
                        original_text=para[:50] + "...",
                        suggested_text="[Geçiş kelimesi eklenebilir]",
                        explanation="Paragraf geçişi için bağlayıcı kelime eklenebilir",
                        location={"paragraph": i},
                        auto_apply=False
                    ))
        
        return suggestions[:5]
    
    async def enhance_academic_language(
        self,
        content: str
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Akademik dili geliştir."""
        enhanced_content = content
        changes = []
        
        for informal, formal in self.academic_phrases.items():
            if informal in enhanced_content.lower():
                # Büyük/küçük harf durumuna dikkat et
                pattern = re.compile(re.escape(informal), re.IGNORECASE)
                enhanced_content = pattern.sub(formal, enhanced_content, count=1)
                changes.append({
                    "original": informal,
                    "enhanced": formal,
                    "reason": "Akademik dil standardına uyum"
                })
        
        return enhanced_content, changes
    
    async def generate_readability_report(
        self,
        content: str
    ) -> Dict[str, Any]:
        """Okunabilirlik raporu oluştur."""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        paragraph_count = len(paragraphs)
        
        avg_sentence_length = word_count / max(sentence_count, 1)
        avg_paragraph_length = sentence_count / max(paragraph_count, 1)
        
        # Uzun kelimeler (8+ karakter)
        long_words = [w for w in words if len(w) >= 8]
        long_word_percentage = len(long_words) / max(word_count, 1) * 100
        
        # Karmaşıklık skoru (basit hesaplama)
        complexity_score = min(100, (avg_sentence_length * 2) + (long_word_percentage * 0.5))
        
        # Okunabilirlik seviyesi
        if complexity_score < 30:
            readability_level = "Kolay"
        elif complexity_score < 50:
            readability_level = "Orta"
        elif complexity_score < 70:
            readability_level = "Zor"
        else:
            readability_level = "Çok Zor"
        
        return {
            "statistics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_sentence_length": round(avg_sentence_length, 1),
                "avg_paragraph_length": round(avg_paragraph_length, 1),
                "long_word_percentage": round(long_word_percentage, 1)
            },
            "readability": {
                "complexity_score": round(complexity_score, 1),
                "level": readability_level,
                "estimated_reading_time_minutes": round(word_count / 200, 1)
            },
            "recommendations": self._generate_readability_recommendations(
                avg_sentence_length, long_word_percentage
            )
        }
    
    def _generate_readability_recommendations(
        self,
        avg_sentence_length: float,
        long_word_percentage: float
    ) -> List[str]:
        """Okunabilirlik önerileri oluştur."""
        recommendations = []
        
        if avg_sentence_length > 25:
            recommendations.append("Cümleleri daha kısa tutmayı düşünün (ortalama 15-20 kelime)")
        
        if long_word_percentage > 30:
            recommendations.append("Daha basit kelimeler kullanarak anlaşılırlığı artırabilirsiniz")
        
        if not recommendations:
            recommendations.append("Okunabilirlik açısından iyi durumdasınız!")
        
        return recommendations
    
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
