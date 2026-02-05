"""
📏 Response Length Manager - Premium Search Enhancement

Strict uzunluk kontrolü ve kapsamlı yanıt yönetimi.
Her kaynak kullanılarak derinlikli yanıtlar üretilir.

Author: Enterprise AI Team
Date: 2025-02
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseMode(Enum):
    """Yanıt modu"""
    BRIEF = "brief"
    NORMAL = "normal"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class LengthProfile:
    """Uzunluk profili"""
    mode: ResponseMode
    min_words: int
    max_words: int
    min_sources: int
    max_sources: int
    detail_level: str
    paragraph_min: int
    section_count: int


# Length profiles
LENGTH_PROFILES: Dict[ResponseMode, LengthProfile] = {
    ResponseMode.BRIEF: LengthProfile(
        mode=ResponseMode.BRIEF,
        min_words=150,
        max_words=400,
        min_sources=3,
        max_sources=8,
        detail_level="overview",
        paragraph_min=2,
        section_count=1,
    ),
    ResponseMode.NORMAL: LengthProfile(
        mode=ResponseMode.NORMAL,
        min_words=400,
        max_words=1200,
        min_sources=10,
        max_sources=20,
        detail_level="balanced",
        paragraph_min=4,
        section_count=2,
    ),
    ResponseMode.DETAILED: LengthProfile(
        mode=ResponseMode.DETAILED,
        min_words=1200,
        max_words=3000,
        min_sources=20,
        max_sources=35,
        detail_level="comprehensive",
        paragraph_min=8,
        section_count=4,
    ),
    ResponseMode.COMPREHENSIVE: LengthProfile(
        mode=ResponseMode.COMPREHENSIVE,
        min_words=3000,
        max_words=6000,
        min_sources=35,
        max_sources=50,
        detail_level="exhaustive",
        paragraph_min=15,
        section_count=6,
    ),
}


class ResponseLengthManager:
    """
    Response Length Manager
    
    Yanıt uzunluğunu ve derinliğini kontrol eder.
    Her kaynak kullanılarak kapsamlı yanıtlar üretilmesini sağlar.
    """
    
    # Enhanced system prompts for each mode
    SYSTEM_PROMPT_TEMPLATES = {
        ResponseMode.BRIEF: """
📝 **KISAYANİT MODU**

ZORUNLU KURALLAR:
- Minimum {min_words} kelime, maksimum {max_words} kelime
- En az {paragraph_min} paragraf yaz
- Konuyu özet olarak anlat
- Kaynaklardan sadece en önemli bilgileri al

KAYNAK KULLANIMI:
- {source_count} kaynak sağlandı
- En alakalı {max_sources} kaynağı kullan
- Her kaynaktan 1 anahtar bilgi al
""",
        
        ResponseMode.NORMAL: """
📝 **NORMAL YANIT MODU**

ZORUNLU KURALLAR:
- Minimum {min_words} kelime, maksimum {max_words} kelime
- En az {paragraph_min} paragraf yaz
- {section_count} ana bölüm oluştur
- Her bölümü detaylıca açıkla

KAYNAK KULLANIMI:
- {source_count} kaynak sağlandı
- En az {min_sources} kaynaktan bilgi al
- Kaynakları karşılaştır ve sentezle
- Çelişkili bilgileri belirt
""",
        
        ResponseMode.DETAILED: """
📝 **DETAYLI YANIT MODU**

ZORUNLU KURALLAR:
- Minimum {min_words} kelime, maksimum {max_words} kelime
- En az {paragraph_min} paragraf yaz
- {section_count} ana bölüm oluştur
- Her bölümde alt başlıklar kullan
- Örnekler ve açıklamalar ekle

KAYNAK KULLANIMI:
- {source_count} kaynak sağlandı - HEPSİNDEN bilgi çıkar
- En az {min_sources} kaynaktan detaylı bilgi al
- Kaynakları derinlemesine analiz et
- Farklı perspektifleri karşılaştır
- Akademik kaynakları öne çıkar

İÇERİK YAPISI:
1. Giriş (sorunu tanımla)
2. Ana Konular (her biri detaylı)
3. Karşılaştırma/Analiz
4. Sonuç ve Öneriler
""",
        
        ResponseMode.COMPREHENSIVE: """
📝 **KAPSAMLI YANIT MODU (EN DETAYLI)**

ZORUNLU KURALLAR:
- Minimum {min_words} kelime, maksimum {max_words} kelime
- En az {paragraph_min} paragraf yaz
- {section_count} ana bölüm oluştur
- Her bölümde en az 3 alt başlık olmalı
- Teorik ve pratik bilgiler içermeli
- Örnekler, karşılaştırmalar ve analizler eklenmeli

KAYNAK KULLANIMI:
- {source_count} kaynak sağlandı - TÜM KAYNAKLARDAN bilgi çıkar
- Her kaynaktan en az 2-3 bilgi al
- Kaynak çeşitliliğini koru (akademik, web, referans)
- Çelişkili kaynakları karşılaştır
- Güncel ve tarihsel perspektif sun

İÇERİK YAPISI:
1. 📌 Giriş ve Bağlam
   - Problem tanımı
   - Önem ve güncellik
   - Kapsam
   
2. 📚 Temel Kavramlar
   - Tanımlar
   - Tarihçe
   - İlgili kavramlar
   
3. 🔍 Detaylı Analiz
   - Ana konular (her biri detaylı)
   - Alt konular
   - Teknik detaylar
   
4. ⚖️ Karşılaştırma
   - Farklı yaklaşımlar
   - Avantajlar/dezavantajlar
   - Kullanım senaryoları
   
5. 💡 Pratik Uygulamalar
   - Örnekler
   - Best practices
   - Yaygın hatalar
   
6. 🎯 Sonuç ve Öneriler
   - Özet
   - Tavsiyeler
   - Gelecek perspektifi
"""
    }
    
    def __init__(self):
        self.profiles = LENGTH_PROFILES
    
    def get_profile(self, mode: str) -> LengthProfile:
        """Mode adından profil al"""
        try:
            response_mode = ResponseMode(mode.lower())
            return self.profiles[response_mode]
        except (ValueError, KeyError):
            return self.profiles[ResponseMode.NORMAL]
    
    def get_system_prompt_enhancement(
        self,
        mode: str,
        source_count: int
    ) -> str:
        """Sistem promptuna eklenecek uzunluk talimatları"""
        profile = self.get_profile(mode)
        
        template = self.SYSTEM_PROMPT_TEMPLATES.get(
            profile.mode,
            self.SYSTEM_PROMPT_TEMPLATES[ResponseMode.NORMAL]
        )
        
        return template.format(
            min_words=profile.min_words,
            max_words=profile.max_words,
            min_sources=min(profile.min_sources, source_count),
            max_sources=min(profile.max_sources, source_count),
            source_count=source_count,
            paragraph_min=profile.paragraph_min,
            section_count=profile.section_count,
        )
    
    def validate_response_length(
        self,
        response: str,
        mode: str
    ) -> Dict[str, Any]:
        """Yanıt uzunluğunu doğrula"""
        profile = self.get_profile(mode)
        
        # Count words
        words = response.split()
        word_count = len(words)
        
        # Count paragraphs (double newline separated)
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Count sections (headers with #)
        import re
        sections = re.findall(r'^#+\s+.+$', response, re.MULTILINE)
        section_count = len(sections)
        
        # Validation
        is_valid = True
        warnings = []
        
        if word_count < profile.min_words:
            is_valid = False
            warnings.append(f"Çok kısa: {word_count} kelime (min: {profile.min_words})")
        
        if word_count > profile.max_words:
            warnings.append(f"Çok uzun: {word_count} kelime (max: {profile.max_words})")
        
        if paragraph_count < profile.paragraph_min:
            warnings.append(f"Yetersiz paragraf: {paragraph_count} (min: {profile.paragraph_min})")
        
        return {
            "is_valid": is_valid,
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "section_count": section_count,
            "expected_min_words": profile.min_words,
            "expected_max_words": profile.max_words,
            "warnings": warnings,
            "mode": mode,
        }
    
    def suggest_mode_for_query(
        self,
        query: str,
        source_count: int
    ) -> ResponseMode:
        """Sorgu ve kaynak sayısına göre mod öner"""
        query_lower = query.lower()
        
        # Comprehensive indicators
        comprehensive_keywords = [
            "detaylı", "kapsamlı", "tüm yönleriyle", "derinlemesine",
            "comprehensive", "detailed", "in-depth", "complete",
            "analiz et", "karşılaştır", "incele", "araştır",
        ]
        
        # Brief indicators
        brief_keywords = [
            "kısaca", "özetle", "hızlıca", "briefly", "quick",
            "nedir", "ne demek", "what is", "define",
        ]
        
        # Check for comprehensive
        if any(kw in query_lower for kw in comprehensive_keywords):
            return ResponseMode.COMPREHENSIVE
        
        # Check for brief
        if any(kw in query_lower for kw in brief_keywords):
            return ResponseMode.BRIEF
        
        # Based on source count
        if source_count >= 35:
            return ResponseMode.COMPREHENSIVE
        elif source_count >= 20:
            return ResponseMode.DETAILED
        elif source_count >= 10:
            return ResponseMode.NORMAL
        else:
            return ResponseMode.BRIEF
    
    def calculate_optimal_sources(
        self,
        mode: str,
        available_sources: int
    ) -> int:
        """Mod için optimal kaynak sayısı"""
        profile = self.get_profile(mode)
        return min(profile.max_sources, available_sources)


# Singleton instance
_manager_instance: Optional[ResponseLengthManager] = None


def get_length_manager() -> ResponseLengthManager:
    """Singleton instance al"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ResponseLengthManager()
    return _manager_instance


# === UTILITY FUNCTIONS ===

def get_response_prompt_enhancement(
    mode: str = "normal",
    source_count: int = 10
) -> str:
    """
    Basit utility - sistem promptuna eklenecek uzunluk talimatları.
    
    Usage:
        enhancement = get_response_prompt_enhancement("detailed", 30)
        system_prompt = base_prompt + enhancement
    """
    manager = get_length_manager()
    return manager.get_system_prompt_enhancement(mode, source_count)


def suggest_response_mode(query: str, source_count: int = 10) -> str:
    """
    Sorguya göre yanıt modu öner.
    
    Returns: "brief", "normal", "detailed", or "comprehensive"
    """
    manager = get_length_manager()
    mode = manager.suggest_mode_for_query(query, source_count)
    return mode.value


def validate_response(response: str, mode: str = "normal") -> Dict[str, Any]:
    """Yanıt uzunluğunu doğrula"""
    manager = get_length_manager()
    return manager.validate_response_length(response, mode)


# === TEST ===

if __name__ == "__main__":
    manager = ResponseLengthManager()
    
    print("=" * 60)
    print("Response Length Manager Test")
    print("=" * 60)
    
    # Test profiles
    for mode in ResponseMode:
        profile = manager.profiles[mode]
        print(f"\n{mode.value.upper()}:")
        print(f"  Words: {profile.min_words}-{profile.max_words}")
        print(f"  Sources: {profile.min_sources}-{profile.max_sources}")
        print(f"  Detail: {profile.detail_level}")
    
    # Test prompt enhancement
    print("\n" + "=" * 60)
    print("DETAILED Mode Prompt Enhancement (30 sources):")
    print("=" * 60)
    print(manager.get_system_prompt_enhancement("detailed", 30))
    
    # Test mode suggestion
    print("\n" + "=" * 60)
    print("Mode Suggestions:")
    print("=" * 60)
    
    test_queries = [
        ("Python nedir?", 5),
        ("Machine learning hakkında bilgi ver", 15),
        ("Yapay zekanın tarihini detaylı anlat", 25),
        ("Kuantum bilgisayarları kapsamlı olarak tüm yönleriyle incele", 45),
    ]
    
    for query, sources in test_queries:
        mode = manager.suggest_mode_for_query(query, sources)
        print(f"  '{query[:40]}...' ({sources} sources) → {mode.value}")
    
    # Test validation
    print("\n" + "=" * 60)
    print("Response Validation:")
    print("=" * 60)
    
    short_response = "Bu çok kısa bir yanıt."
    result = manager.validate_response_length(short_response, "detailed")
    print(f"  Short response: valid={result['is_valid']}, words={result['word_count']}")
    print(f"  Warnings: {result['warnings']}")
