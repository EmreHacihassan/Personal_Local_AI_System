"""
Enterprise AI Assistant - Language Detector
Dil Algılama Modülü

Kullanıcı sorgusunun dilini tespit eder ve uygun yanıt dili belirler.
Premium özellik: Çok dilli destek ve akıllı dil algılama.
"""

import re
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Language(str, Enum):
    """Desteklenen diller."""
    TURKISH = "tr"
    ENGLISH = "en"
    UNKNOWN = "unknown"


@dataclass
class LanguageDetectionResult:
    """Dil algılama sonucu."""
    language: Language
    confidence: float  # 0.0 - 1.0
    reasoning: str


# Türkçe özel karakterler
TURKISH_SPECIAL_CHARS = set("şğüöçıİŞĞÜÖÇ")

# Türkçe yaygın kelimeler (stopwords + soru kelimeleri)
TURKISH_KEYWORDS = {
    # Soru kelimeleri
    "ne", "nasıl", "neden", "nerede", "kim", "hangi", "kaç", "niçin",
    # Bağlaçlar ve edatlar
    "ve", "veya", "ama", "fakat", "için", "ile", "gibi", "kadar", "daha",
    # Zamirler
    "ben", "sen", "o", "biz", "siz", "onlar", "bu", "şu",
    # Fiil ekleri (soru)
    "mı", "mi", "mu", "mü", "mısın", "misin", "musun", "müsün",
    # Yaygın kelimeler
    "bir", "olan", "olarak", "var", "yok", "evet", "hayır",
    "lütfen", "teşekkür", "merhaba", "selam",
    # Fiil kökleri
    "yap", "et", "al", "ver", "gel", "git", "sor", "bul", "ara",
    "çevir", "öner", "anlat", "açıkla", "göster", "yaz", "oku"
}

# İngilizce yaygın kelimeler
ENGLISH_KEYWORDS = {
    # Greetings & common single words
    "hello", "hi", "hey", "thanks", "thank", "please", "yes", "no", "ok", "okay",
    # Question words
    "what", "how", "why", "where", "who", "which", "when",
    # Conjunctions
    "and", "or", "but", "for", "with", "like", "than", "more",
    # Pronouns
    "i", "you", "he", "she", "it", "we", "they", "this", "that",
    # Common words
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "can", "could",
    "will", "would", "should", "may", "might",
    # Verbs
    "make", "take", "give", "get", "find", "show", "tell", "write",
    "translate", "explain", "recommend", "suggest"
}

# === Dil Override Kalıpları ===
# Kullanıcı yanıt dilini açıkça belirttiğinde kullanılır

# İngilizce yanıt iste kalıpları
ENGLISH_REQUEST_PATTERNS = [
    # Türkçe ifadeler
    "ingilizce yanıt",
    "ingilizce cevap",
    "ingilizce olarak yanıtla",
    "ingilizce olarak cevapla",
    "ingilizce yaz",
    "ingilizcede yanıt",
    "ingilizcede yaz",
    "yanıtı ingilizce",
    "cevabı ingilizce",
    # İngilizce ifadeler
    "respond in english",
    "answer in english",
    "reply in english",
    "in english please",
    "english response",
    "english answer",
]

# Türkçe yanıt iste kalıpları
TURKISH_REQUEST_PATTERNS = [
    # İngilizce ifadeler
    "respond in turkish",
    "answer in turkish",
    "reply in turkish",
    "in turkish please",
    "turkish response",
    "turkish answer",
    # Türkçe ifadeler
    "türkçe yanıt",
    "türkçe cevap",
    "türkçe olarak yanıtla",
    "türkçe olarak cevapla",
    "türkçe yaz",
    "türkçede yanıt",
    "yanıtı türkçe",
    "cevabı türkçe",
]


def detect_requested_language(text: str) -> Optional[Language]:
    """
    Kullanıcının açıkça istediği yanıt dilini tespit et.
    
    Args:
        text: Kullanıcı sorgusu
        
    Returns:
        İstenen dil veya None (açık talep yoksa)
    """
    text_lower = text.lower()
    
    # İngilizce yanıt talebi kontrol
    for pattern in ENGLISH_REQUEST_PATTERNS:
        if pattern in text_lower:
            return Language.ENGLISH
    
    # Türkçe yanıt talebi kontrol
    for pattern in TURKISH_REQUEST_PATTERNS:
        if pattern in text_lower:
            return Language.TURKISH
    
    return None


def detect_language(text: str) -> Language:
    """
    Metnin dilini tespit et.
    
    Args:
        text: Analiz edilecek metin
        
    Returns:
        Language enum değeri (TURKISH, ENGLISH, UNKNOWN)
    """
    result = detect_language_detailed(text)
    return result.language


def detect_language_detailed(text: str) -> LanguageDetectionResult:
    """
    Metnin dilini detaylı analiz ile tespit et.
    
    Args:
        text: Analiz edilecek metin
        
    Returns:
        LanguageDetectionResult with language, confidence, and reasoning
    """
    if not text or not text.strip():
        return LanguageDetectionResult(
            language=Language.UNKNOWN,
            confidence=0.0,
            reasoning="Boş metin"
        )
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    if not words:
        return LanguageDetectionResult(
            language=Language.UNKNOWN,
            confidence=0.0,
            reasoning="Kelime bulunamadı"
        )
    
    # === Türkçe Özel Karakter Kontrolü ===
    turkish_char_count = sum(1 for c in text if c in TURKISH_SPECIAL_CHARS)
    has_turkish_chars = turkish_char_count > 0
    
    # === Kelime Eşleşme Analizi ===
    turkish_matches = sum(1 for w in words if w in TURKISH_KEYWORDS)
    english_matches = sum(1 for w in words if w in ENGLISH_KEYWORDS)
    
    total_words = len(words)
    turkish_ratio = turkish_matches / total_words if total_words > 0 else 0
    english_ratio = english_matches / total_words if total_words > 0 else 0
    
    # === Karar Mantığı ===
    
    # 1. Türkçe özel karakter varsa - güçlü Türkçe sinyali
    if has_turkish_chars:
        confidence = min(0.95, 0.7 + (turkish_char_count * 0.05))
        return LanguageDetectionResult(
            language=Language.TURKISH,
            confidence=confidence,
            reasoning=f"Türkçe özel karakter tespit edildi ({turkish_char_count} adet)"
        )
    
    # 2. Tek kelime kontrolü - doğrudan keyword eşleşmesi
    if total_words == 1:
        word = words[0]
        if word in TURKISH_KEYWORDS:
            return LanguageDetectionResult(
                language=Language.TURKISH,
                confidence=0.8,
                reasoning=f"Tek kelime Türkçe eşleşmesi: {word}"
            )
        if word in ENGLISH_KEYWORDS:
            return LanguageDetectionResult(
                language=Language.ENGLISH,
                confidence=0.8,
                reasoning=f"Tek kelime İngilizce eşleşmesi: {word}"
            )
    
    # 3. Türkçe kelime oranı yüksekse
    if turkish_ratio >= 0.15 and turkish_matches >= 2:
        confidence = min(0.9, 0.5 + turkish_ratio)
        return LanguageDetectionResult(
            language=Language.TURKISH,
            confidence=confidence,
            reasoning=f"Türkçe kelime eşleşmesi ({turkish_matches}/{total_words})"
        )
    
    # 4. İngilizce kelime oranı yüksekse
    if english_ratio >= 0.15 and english_matches >= 2:
        confidence = min(0.9, 0.5 + english_ratio)
        return LanguageDetectionResult(
            language=Language.ENGLISH,
            confidence=confidence,
            reasoning=f"İngilizce kelime eşleşmesi ({english_matches}/{total_words})"
        )
    
    # 5. Karşılaştırmalı karar
    if turkish_matches > english_matches:
        return LanguageDetectionResult(
            language=Language.TURKISH,
            confidence=0.6,
            reasoning=f"Türkçe baskın ({turkish_matches} vs {english_matches})"
        )
    elif english_matches > turkish_matches:
        return LanguageDetectionResult(
            language=Language.ENGLISH,
            confidence=0.6,
            reasoning=f"İngilizce baskın ({english_matches} vs {turkish_matches})"
        )
    
    # 5. Varsayılan - Türkçe (lokal sistem)
    return LanguageDetectionResult(
        language=Language.TURKISH,
        confidence=0.4,
        reasoning="Varsayılan dil (Türkçe)"
    )


def get_system_prompt_for_language(language: Language) -> str:
    """
    Dile göre uygun system prompt döndür.
    
    Args:
        language: Hedef dil
        
    Returns:
        Dile uygun system prompt
    """
    if language == Language.TURKISH:
        return """Sen yardımcı bir AI asistanısın.

⚠️ ZORUNLU KURALLAR:

1. DİL KURALI: TÜRKÇE yanıt ver - kullanıcı Türkçe sordu.
   - Farklı bir dil açıkça istenmediği sürece Türkçe devam et.
   - Teknik terimler için parantez içinde İngilizce karşılık verebilirsin.

2. ÇOKLU GÖREV KURALI: Tüm görevleri tamamla.
   - Birden fazla istek varsa HEPSİNİ yap.
   - "İkisini de yap", "hepsini çevir" gibi ifadelerde TÜM görevleri tamamla.
   - Her görevi numaralı liste ile ayrı ayrı işaretle.

3. DOĞRULUK KURALI: Context'e dayalı doğru cevap ver.
   - Emin olmadığın konularda bunu belirt.
   - Kaynaklarını göster."""

    else:  # ENGLISH or UNKNOWN
        return """You are a helpful AI assistant.

⚠️ MANDATORY RULES:

1. LANGUAGE RULE: Respond in English - user asked in English.
   - Continue in English unless different language explicitly requested.
   - You may use original terms in parentheses when needed.

2. MULTI-TASK RULE: Complete ALL tasks.
   - If multiple requests, do ALL of them.
   - For "do both", "translate all" type requests, complete EVERY task.
   - Mark each task separately with numbered list.

3. ACCURACY RULE: Provide accurate answers based on context.
   - Indicate when you're uncertain.
   - Show your sources."""


def get_language_instruction(language: Language, query: str) -> str:
    """
    Sorgu için dil talimatı oluştur.
    
    Args:
        language: Algılanan dil
        query: Kullanıcı sorgusu
        
    Returns:
        LLM için dil talimatı
    """
    if language == Language.TURKISH:
        return f"""
[KULLANICI DİLİ: TÜRKÇE - Türkçe yanıt ver]

Kullanıcı Sorusu: {query}"""
    else:
        return f"""
[USER LANGUAGE: ENGLISH - Respond in English]

User Question: {query}"""


# === Utility Functions ===

def is_turkish(text: str) -> bool:
    """Metnin Türkçe olup olmadığını kontrol et."""
    return detect_language(text) == Language.TURKISH


def is_english(text: str) -> bool:
    """Metnin İngilizce olup olmadığını kontrol et."""
    return detect_language(text) == Language.ENGLISH
