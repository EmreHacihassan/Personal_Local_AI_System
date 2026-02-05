"""
Enterprise Intent Classifier - Query Intent Detection System

Kullanıcı sorgularını kategorize ederek uygun yanıt stratejisini belirler.
RAG gerekli mi, genel bilgi yeterli mi, web araması yapılmalı mı kararını verir.
"""

import re
from enum import Enum
from typing import Tuple, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Query intent categories"""
    PERSONAL_DATA = "personal_data"      # Kullanıcının dosyaları/projeleri hakkında
    GENERAL_KNOWLEDGE = "general_knowledge"  # Genel bilgi soruları
    EDUCATIONAL = "educational"          # Eğitim/öğretim istekleri
    CREATIVE = "creative"                # Yaratıcı içerik üretimi
    TASK = "task"                        # Görev/iş talebi
    GREETING = "greeting"                # Selamlaşma
    HYBRID = "hybrid"                    # Karma (RAG + genel bilgi)
    CODE = "code"                        # Kod yazma/düzenleme
    RESEARCH = "research"                # Araştırma/analiz


class ResponseStrategy(str, Enum):
    """Response strategy based on intent"""
    RAG_ONLY = "rag_only"                # Sadece bilgi tabanı (kişisel veri)
    LLM_ONLY = "llm_only"                # Sadece LLM (genel bilgi, selamlaşma)
    RAG_ENHANCED = "rag_enhanced"        # RAG + LLM zenginleştirme (eğitim)
    WEB_ENHANCED = "web_enhanced"        # Web araması + LLM
    FULL_HYBRID = "full_hybrid"          # RAG + Web + LLM (araştırma)


@dataclass
class IntentResult:
    """Intent classification result"""
    intent: QueryIntent
    strategy: ResponseStrategy
    confidence: float
    matched_patterns: List[str]
    requires_rag: bool
    requires_web: bool
    allow_general_knowledge: bool


class IntentClassifier:
    """
    Enterprise-grade intent classifier for query routing.
    
    Determines:
    - What type of query this is
    - Whether RAG search is needed
    - Whether web search would help
    - Whether LLM can use general knowledge
    """
    
    # Kişisel veri göstergeleri - Strict RAG mode
    PERSONAL_DATA_PATTERNS = [
        r"\b(dosya|doküman|döküman|belge|kayıt|not)lar?(ım|ımda|ımı|ında|ın|ını)?\b",
        r"\b(proje|çalışma|ödev|rapor|sunum)lar?(ım|ımda|ımı)?\b",
        r"\byükle(diğim|nen|miş)\b",
        r"\bkaydet(tiğim|ilen|miş)\b",
        r"\b(arşiv|klasör|folder)(im|ımda)?\b",
        r"\bveritabanı(mda|nda)?\b",
        r"\bindeks(te|li|lenmiş)\b",
        r"\b(bilgi\s*tabanı|knowledge\s*base)(nda|mda)?\b",
        r"\b(notlarım|toplantı\s*notları|meeting\s*notes)\b",
        r"\b(cv|özgeçmiş|resume)(im|imi)?\b",
    ]
    
    # Eğitim/öğretim göstergeleri - Enhanced mode
    EDUCATIONAL_PATTERNS = [
        r"\b(ders|kurs|eğitim)\s*(ver|anlat|hazırla)\b",
        r"\b(öğret|açıkla|anlat)(ir\s*misin|ır\s*mısın|ebilir\s*misin)?\b",
        r"\b(nedir|ne\s*demek|tanımla|açıkla)\b",
        r"\b(nasıl\s*(çalışır|yapılır|kullanılır|oluşturulur))\b",
        r"\b(temel(ler)?i?|fundamental(s)?|basics?)\b",
        r"\b(öğren|kavra|anla)(mak|yım|yalım)\b",
        r"\b(başlangıç|giriş|intro(duction)?)\b",
        r"\b(adım\s*adım|step\s*by\s*step)\b",
        r"\b(örnek(ler)?|example(s)?)\s*(ver|göster|ile|with)\b",
        r"\b(detaylı|kapsamlı|comprehensive)\s*(anlat|açıkla)\b",
        r"\b(sıfırdan|baştan|from\s*scratch)\b",
        r"\bne\s*(işe\s*yarar|için\s*kullanılır)\b",
        r"\b(fark(ı|lar)?|difference|karşılaştır|compare)\b",
    ]
    
    # Genel bilgi göstergeleri - LLM direct
    GENERAL_KNOWLEDGE_PATTERNS = [
        r"^\d+[\+\-\*\/x÷]\d+",  # Math: 2+2, 5*3
        r"\bkaç\s*(eder|yapar|kat|kere)\b",
        r"\b(kim|ne\s*zaman|nerede|neden|niçin)\s*(dir|dır|dur|dür|idi|ydı)?\b",
        r"\b(tarih|history)\s*(nedir|ne\s*zaman)\b",
        r"\b(başkent|capital|merkez)\s*(nedir|neresi)\b",
        r"\b(formül|denklem|equation)\s*(nedir|yaz)\b",
        r"\b(çevir|translate|convert)\b",
        r"\b(tanım|definition)\s*(yap|ver|nedir)\b",
    ]
    
    # Selamlaşma göstergeleri - Skip RAG
    GREETING_PATTERNS = [
        r"^(merhaba|selam|hey|hi|hello|günaydın|iyi\s*(akşam|gün)lar?)\s*[!.,]?\s*$",
        r"^(nasılsın|ne\s*haber|naber|how\s*are\s*you)\s*[!?.,]?\s*$",
        r"^(teşekkür|sağol|eyvallah|thanks?|thank\s*you)\s*[!.,]?\s*$",
        r"^(görüşürüz|hoşça\s*kal|bye|güle\s*güle)\s*[!.,]?\s*$",
    ]
    
    # Yaratıcı içerik göstergeleri
    CREATIVE_PATTERNS = [
        r"\b(yaz|oluştur|üret|create|generate|compose)\s*(bir)?\s*(hikaye|şiir|poem|story|makale|article|blog)\b",
        r"\b(hayal\s*et|imagine|düşün|brainstorm)\b",
        r"\b(yaratıcı|creative|özgün|original)\b",
        r"\b(slogan|motto|tagline|başlık|title)\s*(yaz|oluştur|bul)\b",
    ]
    
    # Kod yazma göstergeleri
    CODE_PATTERNS = [
        r"\b(kod|code|script|function|fonksiyon)\s*(yaz|oluştur|düzelt|fix)\b",
        r"\b(python|javascript|java|c\+\+|typescript|react|vue)\s*(kodu?|ile|in|using)\b",
        r"\b(debug|hata\s*bul|fix\s*the\s*bug)\b",
        r"\b(implement|implemente\s*et|gerçekleştir)\b",
        r"\b(algoritma|algorithm)\s*(yaz|oluştur|tasarla)\b",
        r"\b(refactor|optimize|iyileştir)\b",
    ]
    
    # Araştırma göstergeleri
    RESEARCH_PATTERNS = [
        r"\b(araştır|research|incele|analiz\s*et)\b",
        r"\b(karşılaştır|compare|kıyasla)\b",
        r"\b(derin|deep|kapsamlı\s*araştırma)\b",
        r"\b(piyasa|market|trend)\s*(analiz|research)\b",
        r"\b(kaynak|source|referans)\s*(bul|göster|ara)\b",
    ]
    
    def __init__(self):
        # Compile patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self._personal_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.PERSONAL_DATA_PATTERNS]
        self._educational_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.EDUCATIONAL_PATTERNS]
        self._general_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.GENERAL_KNOWLEDGE_PATTERNS]
        self._greeting_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.GREETING_PATTERNS]
        self._creative_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.CREATIVE_PATTERNS]
        self._code_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.CODE_PATTERNS]
        self._research_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.RESEARCH_PATTERNS]
    
    def _match_patterns(self, text: str, patterns: list) -> Tuple[bool, List[str]]:
        """Check if text matches any pattern, return matched patterns"""
        matched = []
        for pattern in patterns:
            if pattern.search(text):
                matched.append(pattern.pattern)
        return len(matched) > 0, matched
    
    def classify(self, query: str) -> IntentResult:
        """
        Classify query intent and determine response strategy.
        
        Args:
            query: User's query text
            
        Returns:
            IntentResult with intent, strategy, and flags
        """
        query_lower = query.lower().strip()
        matched_patterns = []
        
        # Check greeting first (highest priority for skip)
        is_greeting, greeting_matches = self._match_patterns(query_lower, self._greeting_re)
        if is_greeting:
            return IntentResult(
                intent=QueryIntent.GREETING,
                strategy=ResponseStrategy.LLM_ONLY,
                confidence=0.95,
                matched_patterns=greeting_matches,
                requires_rag=False,
                requires_web=False,
                allow_general_knowledge=True,
            )
        
        # Check personal data (strict RAG mode)
        is_personal, personal_matches = self._match_patterns(query_lower, self._personal_re)
        if is_personal:
            matched_patterns.extend(personal_matches)
            return IntentResult(
                intent=QueryIntent.PERSONAL_DATA,
                strategy=ResponseStrategy.RAG_ONLY,
                confidence=0.9,
                matched_patterns=personal_matches,
                requires_rag=True,
                requires_web=False,
                allow_general_knowledge=False,  # Strict mode
            )
        
        # Check research patterns
        is_research, research_matches = self._match_patterns(query_lower, self._research_re)
        
        # Check educational patterns
        is_educational, educational_matches = self._match_patterns(query_lower, self._educational_re)
        if is_educational:
            strategy = ResponseStrategy.FULL_HYBRID if is_research else ResponseStrategy.RAG_ENHANCED
            return IntentResult(
                intent=QueryIntent.EDUCATIONAL,
                strategy=strategy,
                confidence=0.85,
                matched_patterns=educational_matches,
                requires_rag=True,  # Try RAG first
                requires_web=is_research,  # Web if research mode
                allow_general_knowledge=True,  # Fallback to LLM
            )
        
        # Check code patterns
        is_code, code_matches = self._match_patterns(query_lower, self._code_re)
        if is_code:
            return IntentResult(
                intent=QueryIntent.CODE,
                strategy=ResponseStrategy.RAG_ENHANCED,
                confidence=0.85,
                matched_patterns=code_matches,
                requires_rag=True,  # Check existing code
                requires_web=False,
                allow_general_knowledge=True,  # LLM can write code
            )
        
        # Check creative patterns
        is_creative, creative_matches = self._match_patterns(query_lower, self._creative_re)
        if is_creative:
            return IntentResult(
                intent=QueryIntent.CREATIVE,
                strategy=ResponseStrategy.LLM_ONLY,
                confidence=0.85,
                matched_patterns=creative_matches,
                requires_rag=False,
                requires_web=False,
                allow_general_knowledge=True,
            )
        
        # Check general knowledge patterns
        is_general, general_matches = self._match_patterns(query_lower, self._general_re)
        if is_general:
            return IntentResult(
                intent=QueryIntent.GENERAL_KNOWLEDGE,
                strategy=ResponseStrategy.LLM_ONLY,
                confidence=0.8,
                matched_patterns=general_matches,
                requires_rag=False,
                requires_web=False,
                allow_general_knowledge=True,
            )
        
        # Check research patterns alone
        if is_research:
            return IntentResult(
                intent=QueryIntent.RESEARCH,
                strategy=ResponseStrategy.FULL_HYBRID,
                confidence=0.8,
                matched_patterns=research_matches,
                requires_rag=True,
                requires_web=True,
                allow_general_knowledge=True,
            )
        
        # Default: Hybrid mode (try RAG, allow general knowledge)
        return IntentResult(
            intent=QueryIntent.HYBRID,
            strategy=ResponseStrategy.RAG_ENHANCED,
            confidence=0.6,
            matched_patterns=[],
            requires_rag=True,
            requires_web=False,
            allow_general_knowledge=True,
        )
    
    def classify_fast(self, query: str) -> QueryIntent:
        """
        Fast classification for simple routing decisions.
        Uses keyword matching without full analysis.
        """
        query_lower = query.lower().strip()
        
        # Super short queries
        if len(query) < 10:
            # Check if it's a greeting
            if any(p.search(query_lower) for p in self._greeting_re):
                return QueryIntent.GREETING
            return QueryIntent.GENERAL_KNOWLEDGE
        
        # Personal data keywords
        personal_keywords = ["dosyam", "projem", "notlarım", "dokümanım", "kayıtlarım", "yüklediğim"]
        if any(kw in query_lower for kw in personal_keywords):
            return QueryIntent.PERSONAL_DATA
        
        # Educational keywords
        edu_keywords = ["ders ver", "öğret", "anlat", "nedir", "nasıl", "açıkla"]
        if any(kw in query_lower for kw in edu_keywords):
            return QueryIntent.EDUCATIONAL
        
        return QueryIntent.HYBRID
    
    def should_use_web_search(self, query: str, web_search_enabled: bool) -> bool:
        """
        Determine if web search should be used for this query.
        
        Args:
            query: User query
            web_search_enabled: Whether user enabled web search
            
        Returns:
            True if web search should be performed
        """
        if not web_search_enabled:
            return False
        
        result = self.classify(query)
        
        # Web search is useful for:
        # - Research queries
        # - Educational queries (for current info)
        # - General knowledge (for verification)
        return result.intent in [
            QueryIntent.RESEARCH,
            QueryIntent.EDUCATIONAL,
            QueryIntent.GENERAL_KNOWLEDGE,
            QueryIntent.HYBRID,
        ]
    
    def get_response_mode_instruction(self, intent_result: IntentResult) -> str:
        """
        Get system prompt instruction based on intent.
        
        Returns appropriate instruction for LLM based on query intent.
        """
        instructions = {
            QueryIntent.PERSONAL_DATA: """
Bu bir KİŞİSEL VERİ araması. Sadece bilgi tabanındaki içeriği kullan.
Eğer bilgi tabanında bu konuda bilgi bulunamazsa, açıkça belirt:
"Dosyalarınızda/bilgi tabanınızda bu konuyla ilgili bilgi bulunamadı."
Tahmin yapma veya genel bilgi kullanma.
""",
            QueryIntent.EDUCATIONAL: """
Bu bir EĞİTİM/ÖĞRENME isteği. Kapsamlı, öğretici ve anlaşılır yanıt ver.

YANITLAMA STRATEJİSİ:
1. Bilgi tabanında ilgili içerik varsa, önce onu kullan ve kaynak göster
2. Bilgi tabanında yoksa, genel bilginle detaylı ve kapsamlı ders ver
3. Örnekler, açıklamalar ve adım adım anlatım kullan
4. Kaynak belirt: [Bilgi Tabanı] veya [Genel Bilgi]

Premium formatlama kullan:
- Başlıklar ve alt başlıklar
- Madde işaretleri
- Kod blokları (gerekirse)
- Önemli noktaları vurgula
""",
            QueryIntent.GENERAL_KNOWLEDGE: """
Bu genel bir bilgi sorusu. Doğrudan ve net yanıt ver.
Bilgi tabanı aramasına gerek yok - kendi bilginle yanıtla.
""",
            QueryIntent.CREATIVE: """
Bu yaratıcı bir içerik isteği. Özgün ve yaratıcı ol.
Kendi hayal gücünü kullan, sınırlandırma yok.
""",
            QueryIntent.CODE: """
Bu bir kod yazma/düzenleme isteği. 
1. Varsa bilgi tabanındaki mevcut kodu incele
2. Temiz, okunabilir ve iyi yorumlanmış kod yaz
3. Best practice'leri takip et
4. Açıklama ekle
""",
            QueryIntent.RESEARCH: """
Bu bir ARAŞTIRMA isteği. Kapsamlı ve çok kaynaklı yanıt ver.

YANITLAMA STRATEJİSİ:
1. Bilgi tabanından alakalı içerikleri topla
2. Web araması sonuçlarını dahil et
3. Her kaynağı ayrı ayrı belirt
4. Sonunda tüm kaynakların listesini ver

FORMAT:
📚 BİLGİ TABANI KAYNAKLARI:
[Bilgi tabanındaki içerik]

🌐 WEB KAYNAKLARI:
[Web araması sonuçları]

💡 GENEL DEĞERLENDİRME:
[Sentez ve sonuç]

🔗 KAYNAKLAR:
- [Link 1]
- [Link 2]
""",
            QueryIntent.GREETING: """
Samimi ve sıcak bir şekilde selamla. Kısa tut.
""",
            QueryIntent.HYBRID: """
Bu karma bir sorgu. Aşağıdaki stratejiyi kullan:

1. Önce bilgi tabanını kontrol et
2. Bilgi tabanında içerik varsa, onu kullan ve kaynak göster
3. Bilgi tabanında yoksa veya yetersizse, genel bilginle tamamla
4. Hangi bilginin nereden geldiğini belirt

FORMAT:
📚 BİLGİ TABANINDAN:
[RAG içeriği veya "Bu konuda bilgi tabanınızda içerik bulunamadı"]

💡 EK BİLGİ:
[Genel bilgi ile zenginleştirme]
""",
        }
        
        return instructions.get(intent_result.intent, instructions[QueryIntent.HYBRID])


# Singleton instance
intent_classifier = IntentClassifier()
