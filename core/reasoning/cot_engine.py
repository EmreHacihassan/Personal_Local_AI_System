"""
🧠 Chain-of-Thought Reasoning Engine
=====================================

Premium düşünme motoru:
- Adım adım düşünme (CoT)
- Self-consistency checking
- Thought decomposition
- Reasoning traces

Author: Enterprise AI Team
Version: 1.0.0
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ReasoningStrategy(str, Enum):
    """Düşünme stratejileri."""
    ZERO_SHOT = "zero_shot"           # Direkt yanıt
    FEW_SHOT = "few_shot"             # Örneklerle
    CHAIN_OF_THOUGHT = "cot"          # Adım adım
    STRUCTURED = "structured"          # Yapılandırılmış
    SELF_CONSISTENCY = "self_consistency"  # Çoklu yanıt + oylama


@dataclass
class ThinkingStep:
    """Tek bir düşünme adımı."""
    step_number: int
    description: str
    content: str
    confidence: float = 0.8


@dataclass
class ReasoningResult:
    """Düşünme sonucu."""
    strategy: ReasoningStrategy
    thinking_steps: List[ThinkingStep]
    final_answer: str
    confidence: float
    reasoning_trace: str
    tokens_used: int = 0


# ============================================================================
# COT TEMPLATES
# ============================================================================

class CoTTemplates:
    """Chain-of-Thought prompt şablonları."""
    
    # Genel CoT şablonu
    GENERAL_COT = """
Yanıt vermeden önce adım adım düşün:

<thinking>
**Adım 1: Soruyu Analiz Et**
- Soru ne soruyor?
- Anahtar kavramlar neler?
- Ne tür bir yanıt bekleniyor?

**Adım 2: Bilgi Toplama**
- Bu konuda ne biliyorum?
- Hangi kaynaklar kullanılabilir?
- Eksik bilgi var mı?

**Adım 3: Çözüm Planı**
- Nasıl yaklaşmalıyım?
- Hangi adımları izlemeliyim?
- Olası zorluklar neler?

**Adım 4: Uygulama**
- Planı adım adım uygula
- Her adımı kontrol et
- Sonuçları değerlendir

**Adım 5: Doğrulama**
- Yanıt soruyu karşılıyor mu?
- Mantıksal tutarlılık var mı?
- Eksik bir şey var mı?
</thinking>

<answer>
[YANITINIZ]
</answer>
"""
    
    # Analiz soruları için
    ANALYTICAL_COT = """
Bu analitik soru için sistematik düşün:

<thinking>
**1. Problem Tanımlama**
- Ana problem: [tanımla]
- Alt problemler: [listele]
- Kısıtlar: [belirt]

**2. Veri/Bilgi Değerlendirmesi**
- Mevcut veriler: [listele]
- Eksik bilgiler: [belirt]
- Varsayımlar: [listele]

**3. Analiz Yöntemi**
- Yaklaşım: [seç]
- Adımlar: [planla]
- Metrikler: [belirle]

**4. Uygulama**
[adım adım analiz]

**5. Sonuç ve Öneriler**
- Bulgular: [özetle]
- Öneriler: [listele]
- Limitasyonlar: [belirt]
</thinking>

<answer>
[ANALİZ SONUCU]
</answer>
"""
    
    # Karşılaştırma soruları için
    COMPARISON_COT = """
Karşılaştırma için yapılandırılmış düşün:

<thinking>
**1. Karşılaştırılacaklar**
- A: [tanımla]
- B: [tanımla]
- Karşılaştırma kriterleri: [listele]

**2. Kriter Bazlı Analiz**
| Kriter | A | B | Kazanan |
|--------|---|---|---------|
| [kriter1] | [değer] | [değer] | [A/B/Eşit] |
| [kriter2] | [değer] | [değer] | [A/B/Eşit] |

**3. Avantaj/Dezavantajlar**
A: 
+ [avantaj]
- [dezavantaj]

B:
+ [avantaj]
- [dezavantaj]

**4. Bağlama Göre Seçim**
- [durum1] için: [öneri]
- [durum2] için: [öneri]
</thinking>

<answer>
[KARŞILAŞTIRMA SONUCU]
</answer>
"""
    
    # Kod soruları için
    CODING_COT = """
Kod çözümü için sistematik düşün:

<thinking>
**1. Gereksinim Analizi**
- Girdi: [tanımla]
- Çıktı: [tanımla]
- Kısıtlar: [listele]
- Edge case'ler: [listele]

**2. Algoritma Tasarımı**
- Yaklaşım: [seç]
- Zaman karmaşıklığı: O(?)
- Alan karmaşıklığı: O(?)
- Pseudo-kod:
  1. [adım]
  2. [adım]

**3. İmplementasyon Notları**
- Dil: [seç]
- Kütüphaneler: [listele]
- Dikkat edilecekler: [listele]

**4. Test Senaryoları**
- Normal case: [input] → [expected]
- Edge case: [input] → [expected]
- Error case: [input] → [expected]
</thinking>

<answer>
[KOD ÇÖZÜMÜ]
</answer>
"""
    
    # Matematiksel sorular için
    MATH_COT = """
Matematiksel problem için adım adım çöz:

<thinking>
**1. Problem Anlama**
- Verilenler: [listele]
- İstenenler: [belirt]
- Formüller: [ilgili formüller]

**2. Çözüm Stratejisi**
- Yöntem: [seç]
- Adımlar: [planla]

**3. Hesaplama**
[adım adım hesaplama, her adımı göster]

**4. Doğrulama**
- Sonuç mantıklı mı?
- Birim kontrolü: [kontrol et]
- Alternatif yöntem: [varsa doğrula]
</thinking>

<answer>
[MATEMATİKSEL SONUÇ]
</answer>
"""


# ============================================================================
# COT ENGINE
# ============================================================================

class ChainOfThoughtEngine:
    """
    Chain-of-Thought düşünme motoru.
    
    Features:
    - Otomatik CoT şablon seçimi
    - Düşünme adımlarını parse etme
    - Confidence hesaplama
    - Reasoning trace oluşturma
    """
    
    # Sorgu tipi -> CoT şablonu mapping
    TEMPLATE_MAP = {
        "analytical": CoTTemplates.ANALYTICAL_COT,
        "comparison": CoTTemplates.COMPARISON_COT,
        "coding": CoTTemplates.CODING_COT,
        "math": CoTTemplates.MATH_COT,
        "general": CoTTemplates.GENERAL_COT,
    }
    
    # CoT gerektiren keyword'ler
    COT_TRIGGER_KEYWORDS = {
        "analytical": ["analiz", "analyze", "değerlendir", "evaluate", "incele"],
        "comparison": ["karşılaştır", "compare", "fark", "difference", "vs", "versus"],
        "coding": ["kod", "code", "fonksiyon", "function", "algoritma", "algorithm"],
        "math": ["hesapla", "calculate", "formül", "formula", "matematiksel", "mathematical"],
        "reasoning": ["neden", "why", "nasıl", "how", "açıkla", "explain", "sebep", "reason"],
    }
    
    def __init__(self):
        self.templates = CoTTemplates()
    
    def should_use_cot(self, query: str, complexity: str = "normal") -> bool:
        """
        Bu sorgu için CoT kullanılmalı mı?
        
        Args:
            query: Kullanıcı sorusu
            complexity: Karmaşıklık seviyesi
            
        Returns:
            CoT kullanılmalı mı
        """
        query_lower = query.lower()
        
        # Basit sorgular için CoT gereksiz
        if complexity == "simple" or len(query.split()) <= 5:
            return False
        
        # Karmaşık sorgular için her zaman
        if complexity in ["comprehensive", "research"]:
            return True
        
        # Trigger keyword varsa
        for category, keywords in self.COT_TRIGGER_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return True
        
        return False
    
    def select_template(self, query: str) -> str:
        """
        Sorgu için uygun CoT şablonunu seç.
        
        Args:
            query: Kullanıcı sorusu
            
        Returns:
            CoT şablonu
        """
        query_lower = query.lower()
        
        # Sırayla kontrol et
        if any(kw in query_lower for kw in self.COT_TRIGGER_KEYWORDS["coding"]):
            return self.TEMPLATE_MAP["coding"]
        
        if any(kw in query_lower for kw in self.COT_TRIGGER_KEYWORDS["math"]):
            return self.TEMPLATE_MAP["math"]
        
        if any(kw in query_lower for kw in self.COT_TRIGGER_KEYWORDS["comparison"]):
            return self.TEMPLATE_MAP["comparison"]
        
        if any(kw in query_lower for kw in self.COT_TRIGGER_KEYWORDS["analytical"]):
            return self.TEMPLATE_MAP["analytical"]
        
        return self.TEMPLATE_MAP["general"]
    
    def inject_cot(self, system_prompt: str, query: str) -> str:
        """
        System prompt'a CoT talimatı ekle.
        
        Args:
            system_prompt: Mevcut system prompt
            query: Kullanıcı sorusu
            
        Returns:
            CoT eklenmiş system prompt
        """
        template = self.select_template(query)
        
        return f"{system_prompt}\n\n{template}"
    
    def parse_thinking(self, response: str) -> Tuple[str, str]:
        """
        Yanıttan thinking ve answer kısımlarını ayır.
        
        Args:
            response: LLM yanıtı
            
        Returns:
            (thinking_content, answer_content)
        """
        # <thinking>...</thinking> ve <answer>...</answer> pattern'leri
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
        answer_match = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)
        
        thinking = thinking_match.group(1).strip() if thinking_match else ""
        answer = answer_match.group(1).strip() if answer_match else response
        
        # Eğer answer bulunamadıysa, thinking'i çıkar ve kalanı al
        if not answer_match and thinking_match:
            answer = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL).strip()
        
        return thinking, answer
    
    def extract_steps(self, thinking: str) -> List[ThinkingStep]:
        """
        Düşünme içeriğinden adımları çıkar.
        
        Args:
            thinking: Düşünme içeriği
            
        Returns:
            Adım listesi
        """
        steps = []
        
        # **Adım N:** veya **N.** pattern'lerini ara
        step_patterns = [
            r'\*\*(?:Adım\s*)?(\d+)[.:]\s*(.*?)\*\*\s*(.*?)(?=\*\*(?:Adım\s*)?\d+[.:]|\Z)',
            r'(\d+)\.\s*\*\*(.*?)\*\*\s*(.*?)(?=\d+\.\s*\*\*|\Z)',
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, thinking, re.DOTALL)
            if matches:
                for match in matches:
                    step_num = int(match[0])
                    description = match[1].strip()
                    content = match[2].strip()
                    
                    steps.append(ThinkingStep(
                        step_number=step_num,
                        description=description,
                        content=content,
                        confidence=0.8
                    ))
                break
        
        # Eğer pattern bulunamadıysa, paragrafları adım olarak al
        if not steps:
            paragraphs = [p.strip() for p in thinking.split('\n\n') if p.strip()]
            for i, para in enumerate(paragraphs, 1):
                steps.append(ThinkingStep(
                    step_number=i,
                    description=f"Adım {i}",
                    content=para,
                    confidence=0.7
                ))
        
        return steps
    
    def calculate_confidence(self, thinking: str, answer: str) -> float:
        """
        Yanıt güvenilirliğini hesapla.
        
        Args:
            thinking: Düşünme içeriği
            answer: Yanıt içeriği
            
        Returns:
            Güven skoru (0-1)
        """
        confidence = 0.5
        
        # Thinking uzunluğu
        if len(thinking) > 500:
            confidence += 0.1
        if len(thinking) > 1000:
            confidence += 0.1
        
        # Adım sayısı
        step_count = len(re.findall(r'\*\*(?:Adım\s*)?\d+[.:]', thinking))
        if step_count >= 3:
            confidence += 0.1
        if step_count >= 5:
            confidence += 0.05
        
        # Belirsizlik ifadeleri
        uncertainty_words = ["belki", "muhtemelen", "olabilir", "sanırım", "maybe", "probably"]
        uncertainty_count = sum(1 for word in uncertainty_words if word in answer.lower())
        confidence -= uncertainty_count * 0.05
        
        # Kaynak referansları
        if re.search(r'\[Kaynak|\[Source', answer):
            confidence += 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def process_response(self, response: str, query: str) -> ReasoningResult:
        """
        LLM yanıtını işle ve reasoning result oluştur.
        
        Args:
            response: LLM yanıtı
            query: Orijinal sorgu
            
        Returns:
            ReasoningResult
        """
        thinking, answer = self.parse_thinking(response)
        steps = self.extract_steps(thinking) if thinking else []
        confidence = self.calculate_confidence(thinking, answer)
        
        return ReasoningResult(
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT if thinking else ReasoningStrategy.ZERO_SHOT,
            thinking_steps=steps,
            final_answer=answer,
            confidence=confidence,
            reasoning_trace=thinking,
        )


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

cot_engine = ChainOfThoughtEngine()


__all__ = [
    "ChainOfThoughtEngine",
    "CoTTemplates",
    "ReasoningStrategy",
    "ReasoningResult",
    "ThinkingStep",
    "cot_engine",
]
