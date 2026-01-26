"""
BiasAnalyzer - Tarafsızlık ve Perspektif Çeşitliliği Analiz Modülü
==================================================================

ÖNEMLİ PRENSİP:
Bu modül tarafsızlığı analiz ederken FARKLI BAKIŞ AÇILARINI TÖRPÜLEMEZ.
Aksine, perspektif çeşitliliğini DEĞERLİ görür ve ÖDÜLLENDIRIR.

Analiz Yaklaşımı:
1. Farklı perspektifler ZENGINLIK olarak değerlendirilir
2. Tek taraflı argümanlar uyarı alır
3. Çok yönlü analizler ödüllendirilir
4. Eleştirel düşünce teşvik edilir

Analiz Alanları:
1. Perspektif çeşitliliği (ÖDÜLLENDİRİLİR)
2. Argüman dengesi
3. Kaynak çeşitliliği
4. Dil nötrlüğü
5. Çerçeveleme analizi
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.llm_manager import llm_manager


class PerspectiveType(str, Enum):
    """Perspektif türü."""
    SUPPORTING = "supporting"       # Destekleyici
    OPPOSING = "opposing"           # Karşıt
    NEUTRAL = "neutral"            # Nötr
    ALTERNATIVE = "alternative"    # Alternatif
    CRITICAL = "critical"          # Eleştirel
    SYNTHESIS = "synthesis"        # Sentez


class BalanceLevel(str, Enum):
    """Denge seviyesi."""
    HIGHLY_BALANCED = "highly_balanced"     # Mükemmel denge
    BALANCED = "balanced"                    # İyi denge
    SLIGHTLY_SKEWED = "slightly_skewed"     # Hafif eğilim
    SKEWED = "skewed"                        # Eğilimli
    HEAVILY_BIASED = "heavily_biased"       # Ağır yanlılık


@dataclass
class Perspective:
    """Tespit edilen perspektif."""
    type: PerspectiveType
    description: str
    supporting_text: str
    source: Optional[str] = None
    strength: float = 0.5  # 0-1


@dataclass
class BiasIndicator:
    """Yanlılık göstergesi."""
    type: str
    description: str
    example: str
    location: str
    severity: str  # "low", "medium", "high"
    suggestion: str


@dataclass
class PerspectiveDiversity:
    """
    Perspektif çeşitliliği analizi.
    
    ÖNEMLİ: Bu analiz farklı bakış açılarını DEĞERLİ bulur.
    Çeşitlilik yüksekse → OLUMLU değerlendirme
    Tek taraflıysa → UYARI (ama farklı fikirleri silme önerisi YOK)
    """
    total_perspectives: int
    unique_viewpoints: int
    perspective_distribution: Dict[str, int]
    diversity_score: float  # 0-100, yüksek = iyi
    
    # Perspektifler
    perspectives: List[Perspective] = field(default_factory=list)
    
    # Değerlendirme
    is_diverse: bool = True
    missing_perspectives: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class BiasReport:
    """
    Tarafsızlık ve Perspektif Çeşitliliği Raporu.
    
    NOT: Bu rapor farklı bakış açılarını ENGELLEMEYİ değil,
    DENGELI SUNUMU teşvik eder.
    """
    balance_level: BalanceLevel
    overall_score: float  # 0-100
    
    # Perspektif analizi (EN ÖNEMLİ)
    perspective_diversity: PerspectiveDiversity
    
    # Yanlılık göstergeleri (dikkatli kullanılmalı)
    bias_indicators: List[BiasIndicator] = field(default_factory=list)
    
    # Olumlu yönler
    strengths: List[str] = field(default_factory=list)
    
    # İyileştirme önerileri (içerik değiştirme değil, zenginleştirme)
    suggestions: List[str] = field(default_factory=list)
    
    # Özet
    summary: str = ""
    
    def to_markdown(self) -> str:
        lines = [
            "# ⚖️ Perspektif Çeşitliliği ve Denge Raporu",
            "",
            "**NOT:** Bu analiz farklı bakış açılarını değerli bulur.",
            "Amaç fikirleri törpülemek değil, dengeli sunum sağlamaktır.",
            "",
            f"**Denge Seviyesi:** {self.balance_level.value.replace('_', ' ').title()}",
            f"**Genel Puan:** {round(self.overall_score)}/100",
            f"**Perspektif Çeşitliliği:** {round(self.perspective_diversity.diversity_score)}/100",
            ""
        ]
        
        # Güçlü yönler (ÖNCELİKLİ)
        if self.strengths:
            lines.extend(["## ✅ Güçlü Yönler", ""])
            for s in self.strengths:
                lines.append(f"- {s}")
            lines.append("")
        
        # Perspektif dağılımı
        if self.perspective_diversity.perspectives:
            lines.extend(["## 🔍 Tespit Edilen Perspektifler", ""])
            for p in self.perspective_diversity.perspectives:
                lines.append(f"- **{p.type.value.title()}**: {p.description}")
            lines.append("")
        
        # Eksik perspektifler (öneri olarak, zorunluluk değil)
        if self.perspective_diversity.missing_perspectives:
            lines.extend(["## 💡 Eklenebilecek Perspektifler (Opsiyonel)", ""])
            lines.append("*Bu perspektiflerin eklenmesi içeriği zenginleştirebilir:*")
            for mp in self.perspective_diversity.missing_perspectives:
                lines.append(f"- {mp}")
            lines.append("")
        
        # Öneriler
        if self.suggestions:
            lines.extend(["## 📝 Öneriler", ""])
            lines.append("*Bu öneriler içeriği kısıtlamak değil, zenginleştirmek içindir:*")
            for s in self.suggestions:
                lines.append(f"- {s}")
        
        return "\n".join(lines)


class BiasAnalyzer:
    """
    Tarafsızlık ve Perspektif Çeşitliliği Analiz Modülü
    
    ÖNEMLİ İLKELER:
    ===============
    1. FARKLI BAKIŞ AÇILARI DEĞERLİDİR
       - Karşıt görüşler kaliteyi DÜŞÜRMEZ, aksine ARTTIRIR
       - Çok perspektifli analiz ÖDÜLLENDİRİLİR
       
    2. TÖRPÜLEME YASAK
       - Bu modül fikirleri "yumuşatmak" için DEĞİL
       - Dengeli SUNUM için öneriler sunar
       
    3. ELEŞTİREL DÜŞÜNCE TEŞVİK EDİLİR
       - Zıt görüşlerin sunulması teşvik edilir
       - Sentez yapabilme yeteneği ödüllendirilir
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Yanlılık göstergeleri (dikkatli kullanılmalı)
        self.loaded_language_patterns = [
            # Abartılı ifadeler
            (r'\b(kesinlikle|mutlaka|her zaman|asla|hiçbir zaman)\b', "Mutlak ifade"),
            # Bu pattern'ler DİKKATLİ kullanılmalı - savunuculuk bazen geçerlidir
        ]
        
        # Perspektif göstergeleri
        self.perspective_indicators = {
            "supporting": ["desteklemekte", "göstermektedir", "kanıtlamaktadır", "ortaya koymaktadır"],
            "opposing": ["eleştirmekte", "karşı çıkmakta", "reddetmekte", "itiraz etmekte"],
            "alternative": ["alternatif olarak", "farklı bir yaklaşım", "başka bir görüşe göre"],
            "neutral": ["tarafsız", "objektif", "nötr"],
            "critical": ["eleştirel", "sorgulayarak", "kritik", "irdeleyerek"]
        }
    
    async def analyze_document(
        self,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> BiasReport:
        """
        Dokümanı perspektif çeşitliliği ve denge açısından analiz et.
        
        ÖNEMLİ: Bu analiz fikirleri törpülemek için DEĞİL,
        dengeli sunum için geri bildirim sağlar.
        
        Args:
            content: Doküman içeriği
            sources: Kullanılan kaynaklar
            
        Returns:
            Tarafsızlık ve perspektif raporu
        """
        # Perspektif çeşitliliği analizi
        diversity = await self._analyze_perspective_diversity(content)
        
        # Yanlılık göstergeleri (dikkatli)
        indicators = await self._detect_bias_indicators(content)
        
        # Kaynak çeşitliliği
        source_diversity = self._analyze_source_diversity(sources) if sources else 0.8
        
        # Güçlü yönleri belirle (ÖNCELİKLİ)
        strengths = self._identify_strengths(diversity, indicators)
        
        # Öneriler (zenginleştirme odaklı)
        suggestions = self._generate_suggestions(diversity, indicators)
        
        # Genel puan
        overall_score = self._calculate_score(diversity, indicators, source_diversity)
        
        # Denge seviyesi
        balance_level = self._determine_balance_level(overall_score, diversity)
        
        # Özet
        summary = self._generate_summary(balance_level, diversity)
        
        return BiasReport(
            balance_level=balance_level,
            overall_score=overall_score,
            perspective_diversity=diversity,
            bias_indicators=indicators,
            strengths=strengths,
            suggestions=suggestions,
            summary=summary
        )
    
    async def _analyze_perspective_diversity(
        self,
        content: str
    ) -> PerspectiveDiversity:
        """
        Perspektif çeşitliliğini analiz et.
        
        FARKLI BAKIŞ AÇILARI = DEĞERLİ
        """
        perspectives: List[Perspective] = []
        distribution = {t.value: 0 for t in PerspectiveType}
        
        # Pattern tabanlı tespit
        for ptype, indicators in self.perspective_indicators.items():
            for indicator in indicators:
                if indicator in content.lower():
                    distribution[ptype] += 1
        
        # LLM ile derin analiz
        prompt = f"""Bu akademik metindeki farklı bakış açılarını ve perspektifleri tespit et.

ÖNEMLİ: Farklı perspektifler DEĞERLİDİR. Amaç onları eleştirmek değil, tespit etmektir.

Metin:
{content[:4000]}

Her perspektif için:
1. Türü (supporting/opposing/alternative/neutral/critical/synthesis)
2. Kısa açıklama
3. Destekleyici metin parçası

JSON formatında yanıt ver:
[
    {{"type": "", "description": "", "supporting_text": ""}}
]

Hiç perspektif yoksa boş array: []"""

        try:
            response = await self._llm_call(prompt)
            import json
            match = re.search(r'\[[\s\S]*\]', response)
            if match:
                data = json.loads(match.group())
                for item in data:
                    ptype = item.get("type", "neutral")
                    try:
                        perspective_type = PerspectiveType(ptype)
                    except:
                        perspective_type = PerspectiveType.NEUTRAL
                    
                    perspectives.append(Perspective(
                        type=perspective_type,
                        description=item.get("description", ""),
                        supporting_text=item.get("supporting_text", "")[:200]
                    ))
                    distribution[ptype] = distribution.get(ptype, 0) + 1
        except:
            pass
        
        # Çeşitlilik skoru hesapla
        unique_types = len([v for v in distribution.values() if v > 0])
        total = len(perspectives)
        
        # Çeşitlilik YÜKSEK = İYİ
        if unique_types >= 4:
            diversity_score = 95.0
        elif unique_types >= 3:
            diversity_score = 85.0
        elif unique_types >= 2:
            diversity_score = 70.0
        elif unique_types == 1 and total > 0:
            diversity_score = 50.0  # Tek perspektif, düşük ama kötü değil
        else:
            diversity_score = 40.0
        
        # Eksik perspektifler (öneri olarak)
        missing = []
        if distribution.get("opposing", 0) == 0:
            missing.append("Karşıt görüşler eklenebilir")
        if distribution.get("alternative", 0) == 0:
            missing.append("Alternatif yaklaşımlar belirtilebilir")
        if distribution.get("critical", 0) == 0:
            missing.append("Eleştirel değerlendirme zenginlik katabilir")
        
        # Güçlü yönler
        strengths = []
        if unique_types >= 3:
            strengths.append("Çok yönlü perspektif sunumu")
        if distribution.get("opposing", 0) > 0 and distribution.get("supporting", 0) > 0:
            strengths.append("Hem destekleyici hem karşıt görüşler mevcut")
        if distribution.get("synthesis", 0) > 0:
            strengths.append("Sentez yapabilme yeteneği gösterilmiş")
        
        return PerspectiveDiversity(
            total_perspectives=total,
            unique_viewpoints=unique_types,
            perspective_distribution=distribution,
            diversity_score=diversity_score,
            perspectives=perspectives,
            is_diverse=unique_types >= 2,
            missing_perspectives=missing,
            strengths=strengths
        )
    
    async def _detect_bias_indicators(
        self,
        content: str
    ) -> List[BiasIndicator]:
        """
        Yanlılık göstergelerini tespit et.
        
        DİKKAT: Bu tespit, fikirleri DEĞİŞTİRMEK için değil,
        farkındalık yaratmak içindir.
        """
        indicators = []
        
        # Mutlak ifade kontrolü (sadece aşırı durumlar)
        absolute_words = ["kesinlikle", "mutlaka", "asla", "hiçbir zaman", "tamamen"]
        for word in absolute_words:
            count = content.lower().count(word)
            if count >= 3:  # Sadece tekrarlı kullanım
                indicators.append(BiasIndicator(
                    type="Mutlak İfade",
                    description=f"'{word}' kelimesi sık kullanılmış ({count} kez)",
                    example=word,
                    location="",
                    severity="low",
                    suggestion=f"Mutlak ifadeler yerine 'genellikle', 'çoğunlukla' gibi nüanslı ifadeler düşünülebilir"
                ))
        
        return indicators
    
    def _analyze_source_diversity(
        self,
        sources: List[Dict[str, Any]]
    ) -> float:
        """Kaynak çeşitliliğini analiz et."""
        if not sources:
            return 0.5
        
        # Farklı yayın yılları
        years = set(s.get("year") for s in sources if s.get("year"))
        
        # Farklı yazarlar
        authors = set()
        for s in sources:
            for a in s.get("authors", []):
                authors.add(a)
        
        # Çeşitlilik skoru
        score = 0.5
        if len(years) >= 5:
            score += 0.2
        if len(authors) >= 10:
            score += 0.2
        if len(sources) >= 10:
            score += 0.1
        
        return min(score, 1.0)
    
    def _identify_strengths(
        self,
        diversity: PerspectiveDiversity,
        indicators: List[BiasIndicator]
    ) -> List[str]:
        """Güçlü yönleri belirle (ÖNCELİKLİ)."""
        strengths = []
        
        # Perspektif çeşitliliği güçlü yönleri
        strengths.extend(diversity.strengths)
        
        # Az yanlılık göstergesi = güçlü yön
        if len(indicators) <= 2:
            strengths.append("Dengeli ve ölçülü dil kullanımı")
        
        if diversity.diversity_score >= 80:
            strengths.append("Mükemmel perspektif çeşitliliği")
        
        return strengths
    
    def _generate_suggestions(
        self,
        diversity: PerspectiveDiversity,
        indicators: List[BiasIndicator]
    ) -> List[str]:
        """
        Öneriler oluştur.
        
        ÖNEMLİ: Bu öneriler içeriği KISITLAMAK değil,
        ZENGINLEŞTİRMEK içindir.
        """
        suggestions = []
        
        # Eksik perspektif önerileri (zorunluluk değil, zenginleştirme)
        if diversity.missing_perspectives:
            suggestions.append(
                "İçeriği zenginleştirmek için farklı perspektifler EKLENEBİLİR "
                "(mevcut içerik değiştirilmeden)"
            )
        
        if not diversity.is_diverse:
            suggestions.append(
                "Tek taraflı argüman güçlü olabilir, ancak karşıt görüşlerin "
                "kısa bir özeti okuyucuya bağlam sağlayabilir"
            )
        
        # Sentez önerisi
        if diversity.unique_viewpoints >= 2 and diversity.perspective_distribution.get("synthesis", 0) == 0:
            suggestions.append(
                "Farklı perspektifleri birleştiren bir sentez bölümü eklenebilir"
            )
        
        return suggestions
    
    def _calculate_score(
        self,
        diversity: PerspectiveDiversity,
        indicators: List[BiasIndicator],
        source_diversity: float
    ) -> float:
        """Genel puanı hesapla."""
        # Temel: perspektif çeşitliliği (en ağırlıklı)
        score = diversity.diversity_score * 0.6
        
        # Kaynak çeşitliliği
        score += source_diversity * 100 * 0.2
        
        # Yanlılık göstergeleri cezası (hafif)
        penalty = min(len(indicators) * 3, 20)
        score -= penalty
        
        # Bonus: eleştirel düşünce
        if diversity.perspective_distribution.get("critical", 0) > 0:
            score += 5
        
        return max(0, min(100, score + 20))  # Baz puan
    
    def _determine_balance_level(
        self,
        score: float,
        diversity: PerspectiveDiversity
    ) -> BalanceLevel:
        """Denge seviyesini belirle."""
        if score >= 85 and diversity.is_diverse:
            return BalanceLevel.HIGHLY_BALANCED
        elif score >= 70:
            return BalanceLevel.BALANCED
        elif score >= 55:
            return BalanceLevel.SLIGHTLY_SKEWED
        elif score >= 40:
            return BalanceLevel.SKEWED
        else:
            return BalanceLevel.HEAVILY_BIASED
    
    def _generate_summary(
        self,
        level: BalanceLevel,
        diversity: PerspectiveDiversity
    ) -> str:
        """Özet oluştur."""
        summaries = {
            BalanceLevel.HIGHLY_BALANCED: 
                "Metin mükemmel perspektif çeşitliliği sunuyor. "
                "Farklı bakış açıları dengeli şekilde temsil edilmiş.",
            
            BalanceLevel.BALANCED:
                "Metin genel olarak dengeli bir sunum içeriyor. "
                "Birden fazla perspektif mevcut.",
            
            BalanceLevel.SLIGHTLY_SKEWED:
                "Metin belirli bir perspektife hafif eğilim gösteriyor. "
                "Bu durum savunmacı metinlerde normal olabilir.",
            
            BalanceLevel.SKEWED:
                "Metin belirli bir bakış açısına ağırlık veriyor. "
                "Academic bağlamda alternatif görüşlerin eklenmesi düşünülebilir.",
            
            BalanceLevel.HEAVILY_BIASED:
                "Metin tek taraflı bir perspektif sunuyor. "
                "Okuyucunun farklı görüşleri değerlendirmesi için "
                "alternatif perspektifler eklenebilir."
        }
        
        return summaries.get(level, "Analiz tamamlandı.")
    
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
