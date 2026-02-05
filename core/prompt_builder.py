"""
🎯 Enterprise Modular Prompt Builder
====================================

Premium prompt mühendisliği sistemi:
- Modüler ve conditional prompt oluşturma
- Token-aware context management
- Dynamic instruction injection
- Few-shot example integration
- Query-type specific prompts

Author: Enterprise AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class QueryType(str, Enum):
    """Sorgu tipleri."""
    FACTUAL = "factual"           # Gerçek bilgi soruları
    ANALYTICAL = "analytical"     # Analiz/karşılaştırma
    CREATIVE = "creative"         # Yaratıcı içerik
    CODING = "coding"             # Kod soruları
    CONVERSATIONAL = "conversational"  # Genel sohbet
    SYSTEM_INFO = "system_info"   # Sistem hakkında sorular
    CONTINUATION = "continuation" # Devam et komutları


class ResponseMode(str, Enum):
    """Yanıt modları."""
    AUTO = "auto"
    CONCISE = "concise"
    DETAILED = "detailed"
    ACADEMIC = "academic"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"


class ComplexityLevel(str, Enum):
    """Karmaşıklık seviyeleri."""
    SIMPLE = "simple"
    NORMAL = "normal"
    COMPREHENSIVE = "comprehensive"
    RESEARCH = "research"


# ============================================================================
# PROMPT MODULES
# ============================================================================

@dataclass
class PromptModule:
    """Tek bir prompt modülü."""
    name: str
    content: str
    priority: int  # 1-10, yüksek = daha önemli
    estimated_tokens: int
    conditions: List[str] = field(default_factory=list)  # Modülün aktif olma koşulları
    

class PromptModuleLibrary:
    """Prompt modül kütüphanesi."""
    
    IDENTITY_MODULE = PromptModule(
        name="identity",
        content="""Sen "Enterprise AI Assistant" adlı kurumsal bir AI asistanısın (v2.2). 
Türkçe yanıt ver. Profesyonel, yardımcı ve doğru bilgi sağlamaya odaklan.""",
        priority=10,
        estimated_tokens=50,
        conditions=["always"]
    )
    
    CAPABILITIES_MODULE = PromptModule(
        name="capabilities",
        content="""### Yeteneklerin:
- **RAG (Retrieval-Augmented Generation)**: Dökümanlardan bilgi çekme
- **Web Search**: DuckDuckGo ile güncel bilgi arama
- **Multi-Agent System**: Araştırma, yazım, analiz agent'ları
- **Tool Usage**: Hesaplama, kod çalıştırma, dosya işlemleri
- **MCP Protocol**: Standart AI entegrasyon protokolü""",
        priority=3,
        estimated_tokens=100,
        conditions=["system_info"]
    )
    
    COT_MODULE = PromptModule(
        name="chain_of_thought",
        content="""### Düşünme Süreci
Karmaşık sorular için adım adım düşün:
1. Soruyu analiz et ve ana konuyu belirle
2. Gerekli bilgileri ve kaynakları değerlendir
3. Yanıt yapısını planla
4. Her bölümü mantıksal sırayla yaz
5. Sonuç ve özet ekle (gerekirse)

Düşünme sürecini <thinking>...</thinking> içinde yaz.""",
        priority=8,
        estimated_tokens=80,
        conditions=["complex_query", "analytical"]
    )
    
    DETAILED_MODE_MODULE = PromptModule(
        name="detailed_mode",
        content="""### DETAYLI YANIT MODU
- Kapsamlı ve derinlemesine açıklama
- Birden fazla açıdan ele al
- Örnekler ve karşılaştırmalar ekle
- Avantaj/dezavantaj belirt
- En az 400-600 kelime""",
        priority=7,
        estimated_tokens=60,
        conditions=["detailed"]
    )
    
    CONCISE_MODE_MODULE = PromptModule(
        name="concise_mode",
        content="""### KISA YANIT MODU
- Net ve öz açıklama (max 150 kelime)
- Doğrudan konuya odaklan
- Gereksiz detaylardan kaçın""",
        priority=7,
        estimated_tokens=40,
        conditions=["concise"]
    )
    
    ACADEMIC_MODE_MODULE = PromptModule(
        name="academic_mode",
        content="""### AKADEMİK YANIT MODU
- Akademik ve formal dil kullan
- Kaynaklara referans ver
- Terminolojiyi doğru kullan
- Objektif ve tarafsız ol""",
        priority=7,
        estimated_tokens=50,
        conditions=["academic"]
    )
    
    REFERENCE_MODULE = PromptModule(
        name="reference_system",
        content="""### KAYNAK REFERANS SİSTEMİ
Bilgi kaynaklarını belirt:
- Dökümanlardan: [Kaynak A], [Kaynak B.2] (sayfa no)
- Web'den: 🌐 kaynak linki
- Genel bilgi: 💡 işareti ile

Her önemli bilginin kaynağını belirt.""",
        priority=6,
        estimated_tokens=70,
        conditions=["has_sources"]
    )
    
    CONTINUATION_MODULE = PromptModule(
        name="continuation",
        content="""### DEVAM ET KOMUTU
Kullanıcı önceki yarım kalan yanıtın devamını istiyor.
- Konuşma geçmişindeki son asistan mesajını kontrol et
- Kaldığın yerden AYNEN devam et
- Yeni başlık açma, önceki bağlamı koru
- Önceki formatı sürdür""",
        priority=9,
        estimated_tokens=60,
        conditions=["continuation"]
    )
    
    CODING_MODULE = PromptModule(
        name="coding_mode",
        content="""### KOD YAZIM MODU
- Temiz, okunabilir ve iyi yorumlanmış kod yaz
- Best practice'leri takip et
- Kod bloklarını ```language formatında ver
- Açıklama ve kullanım örneği ekle
- Hata kontrolü ve edge case'leri düşün""",
        priority=8,
        estimated_tokens=70,
        conditions=["coding"]
    )
    
    RULES_MODULE = PromptModule(
        name="critical_rules",
        content="""### KRİTİK KURALLAR
1. Kullanıcının ASIL SORUSUNA ODAKLAN
2. RAG/Web bilgisi varsa öncelikle kullan
3. Kaynak belirt (varsa)
4. Yanıtı YARIDA BIRAKMA
5. Halüsinasyondan kaçın - emin değilsen belirt""",
        priority=9,
        estimated_tokens=60,
        conditions=["always"]
    )


# ============================================================================
# QUERY ANALYZER
# ============================================================================

class QueryAnalyzer:
    """Sorgu analizi ve sınıflandırma."""
    
    # Keyword patterns for query type detection
    QUERY_PATTERNS = {
        QueryType.CODING: [
            "kod", "code", "python", "javascript", "java", "c++", "sql",
            "fonksiyon", "function", "class", "sınıf", "hata", "error", "debug",
            "algorithm", "algoritma", "implement", "uygula"
        ],
        QueryType.ANALYTICAL: [
            "karşılaştır", "compare", "analiz", "analyze", "fark", "difference",
            "avantaj", "dezavantaj", "pros", "cons", "değerlendir", "evaluate",
            "neden", "why", "nasıl", "how", "açıkla", "explain"
        ],
        QueryType.CREATIVE: [
            "yaz", "write", "oluştur", "create", "hikaye", "story", "şiir", "poem",
            "slogan", "başlık", "title", "içerik", "content", "metin", "text"
        ],
        QueryType.SYSTEM_INFO: [
            "sen kimsin", "kimsin sen", "kendini tanıt", "adın ne", "ismin ne",
            "nasıl çalışıyorsun", "özelliklerin", "yeteneklerin", "neler yapabilirsin",
            "mcp nedir", "rag nedir", "who are you", "what are you"
        ],
        QueryType.CONTINUATION: [
            "devam et", "devam", "bitir", "tamamla", "kaldığın yerden",
            "continue", "finish", "go on", "keep going", "son cevabını bitir"
        ],
        QueryType.CONVERSATIONAL: [
            "merhaba", "selam", "hey", "hi", "hello", "günaydın", "nasılsın",
            "teşekkür", "sağol", "thanks", "bye", "görüşürüz", "tamam", "ok"
        ]
    }
    
    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        "high": [
            "kapsamlı", "detaylı", "derinlemesine", "araştırma", "comprehensive",
            "detailed", "in-depth", "research", "akademik", "academic"
        ],
        "low": [
            "kısa", "özet", "basit", "hızlı", "short", "brief", "simple", "quick"
        ]
    }
    
    def analyze(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Sorguyu analiz et.
        
        Returns:
            {
                "query_type": QueryType,
                "complexity": ComplexityLevel,
                "is_simple": bool,
                "needs_cot": bool,
                "needs_sources": bool,
                "suggested_temperature": float,
                "suggested_mode": ResponseMode,
                "detected_keywords": List[str],
            }
        """
        query_lower = query.lower().strip()
        words = query_lower.split()
        
        # Detect query type
        query_type = self._detect_query_type(query_lower)
        
        # Detect complexity
        complexity = self._detect_complexity(query_lower, len(words))
        
        # Simple query detection
        is_simple = (
            len(words) <= 5 and 
            query_type == QueryType.CONVERSATIONAL
        ) or len(query_lower) < 20
        
        # Chain-of-Thought needed?
        needs_cot = (
            query_type in [QueryType.ANALYTICAL, QueryType.CODING] or
            complexity in [ComplexityLevel.COMPREHENSIVE, ComplexityLevel.RESEARCH] or
            any(word in query_lower for word in ["neden", "nasıl", "açıkla", "karşılaştır"])
        )
        
        # Sources needed?
        needs_sources = context and (
            context.get("rag_results") or 
            context.get("web_results") or
            context.get("documents")
        )
        
        # Suggested temperature
        temperature = self._suggest_temperature(query_type, complexity)
        
        # Suggested mode
        mode = self._suggest_mode(query_type, complexity)
        
        return {
            "query_type": query_type,
            "complexity": complexity,
            "is_simple": is_simple,
            "needs_cot": needs_cot,
            "needs_sources": bool(needs_sources),
            "suggested_temperature": temperature,
            "suggested_mode": mode,
            "word_count": len(words),
        }
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Sorgu tipini belirle."""
        scores = {qt: 0 for qt in QueryType}
        
        for query_type, patterns in self.QUERY_PATTERNS.items():
            for pattern in patterns:
                if pattern in query:
                    scores[query_type] += 1
        
        # En yüksek skoru al
        max_type = max(scores, key=scores.get)
        
        # Eğer hiçbir pattern eşleşmediyse FACTUAL varsay
        if scores[max_type] == 0:
            return QueryType.FACTUAL
        
        return max_type
    
    def _detect_complexity(self, query: str, word_count: int) -> ComplexityLevel:
        """Karmaşıklık seviyesini belirle."""
        # Kelime sayısına göre baz seviye
        if word_count <= 5:
            base_level = ComplexityLevel.SIMPLE
        elif word_count <= 15:
            base_level = ComplexityLevel.NORMAL
        elif word_count <= 30:
            base_level = ComplexityLevel.COMPREHENSIVE
        else:
            base_level = ComplexityLevel.RESEARCH
        
        # Keyword'lere göre ayarla
        for indicator in self.COMPLEXITY_INDICATORS["high"]:
            if indicator in query:
                if base_level == ComplexityLevel.SIMPLE:
                    return ComplexityLevel.NORMAL
                elif base_level == ComplexityLevel.NORMAL:
                    return ComplexityLevel.COMPREHENSIVE
                else:
                    return ComplexityLevel.RESEARCH
        
        for indicator in self.COMPLEXITY_INDICATORS["low"]:
            if indicator in query:
                if base_level in [ComplexityLevel.COMPREHENSIVE, ComplexityLevel.RESEARCH]:
                    return ComplexityLevel.NORMAL
                else:
                    return ComplexityLevel.SIMPLE
        
        return base_level
    
    def _suggest_temperature(self, query_type: QueryType, complexity: ComplexityLevel) -> float:
        """Önerilen temperature."""
        base_temps = {
            QueryType.FACTUAL: 0.3,
            QueryType.ANALYTICAL: 0.4,
            QueryType.CODING: 0.2,
            QueryType.CREATIVE: 0.8,
            QueryType.CONVERSATIONAL: 0.6,
            QueryType.SYSTEM_INFO: 0.3,
            QueryType.CONTINUATION: 0.5,
        }
        
        temp = base_temps.get(query_type, 0.5)
        
        # Complexity adjustment
        if complexity == ComplexityLevel.RESEARCH:
            temp = max(0.1, temp - 0.1)  # Daha deterministik
        elif complexity == ComplexityLevel.SIMPLE:
            temp = min(0.9, temp + 0.1)  # Biraz daha rahat
        
        return round(temp, 2)
    
    def _suggest_mode(self, query_type: QueryType, complexity: ComplexityLevel) -> ResponseMode:
        """Önerilen yanıt modu."""
        if complexity == ComplexityLevel.SIMPLE:
            return ResponseMode.CONCISE
        elif complexity == ComplexityLevel.RESEARCH:
            return ResponseMode.ACADEMIC
        elif query_type == QueryType.CODING:
            return ResponseMode.TECHNICAL
        elif query_type == QueryType.CREATIVE:
            return ResponseMode.FRIENDLY
        elif complexity == ComplexityLevel.COMPREHENSIVE:
            return ResponseMode.DETAILED
        else:
            return ResponseMode.AUTO


# ============================================================================
# MODULAR PROMPT BUILDER
# ============================================================================

class ModularPromptBuilder:
    """
    Token-aware modüler prompt oluşturucu.
    
    Features:
    - Conditional module loading
    - Token budget management
    - Priority-based inclusion
    - Dynamic context injection
    """
    
    def __init__(self, token_manager=None):
        from .token_manager import token_manager as default_tm
        self.token_manager = token_manager or default_tm
        self.module_library = PromptModuleLibrary()
        self.query_analyzer = QueryAnalyzer()
    
    def build(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        max_system_tokens: int = 2000,
        response_mode: Optional[ResponseMode] = None,
        include_cot: bool = True,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Modüler system prompt oluştur.
        
        Args:
            query: Kullanıcı sorusu
            context: Ek bağlam bilgileri
                - rag_results: RAG sonuçları
                - web_results: Web arama sonuçları
                - chat_history: Önceki mesajlar
                - notes: Kullanıcı notları
                - documents: Yüklü dökümanlar
            max_system_tokens: Maksimum system prompt token sayısı
            response_mode: İstenilen yanıt modu (None = auto)
            include_cot: Chain-of-Thought dahil edilsin mi
            
        Returns:
            (system_prompt, metadata)
        """
        context = context or {}
        
        # Sorgu analizi
        analysis = self.query_analyzer.analyze(query, context)
        
        # Response mode belirleme
        if response_mode is None or response_mode == ResponseMode.AUTO:
            response_mode = analysis["suggested_mode"]
        
        # Aktif modülleri belirle
        active_conditions = self._get_active_conditions(analysis, context, response_mode)
        
        # Modülleri topla ve filtrele
        modules = self._collect_modules(active_conditions)
        
        # Token budget'a göre sırala ve seç
        selected_modules = self._select_modules_by_budget(modules, max_system_tokens)
        
        # Prompt'u oluştur
        system_prompt = self._assemble_prompt(selected_modules, context, analysis)
        
        # Metadata
        metadata = {
            "analysis": analysis,
            "response_mode": response_mode,
            "selected_modules": [m.name for m in selected_modules],
            "total_tokens": self.token_manager.count_tokens(system_prompt),
            "temperature": analysis["suggested_temperature"],
        }
        
        return system_prompt, metadata
    
    def _get_active_conditions(
        self,
        analysis: Dict[str, Any],
        context: Dict[str, Any],
        mode: ResponseMode
    ) -> set:
        """Aktif koşulları belirle."""
        conditions = {"always"}
        
        # Query type based
        query_type = analysis["query_type"]
        if query_type == QueryType.SYSTEM_INFO:
            conditions.add("system_info")
        elif query_type == QueryType.CODING:
            conditions.add("coding")
        elif query_type == QueryType.ANALYTICAL:
            conditions.add("analytical")
        elif query_type == QueryType.CONTINUATION:
            conditions.add("continuation")
        
        # Complexity based
        if analysis["needs_cot"]:
            conditions.add("complex_query")
        
        # Mode based
        if mode == ResponseMode.DETAILED:
            conditions.add("detailed")
        elif mode == ResponseMode.CONCISE:
            conditions.add("concise")
        elif mode == ResponseMode.ACADEMIC:
            conditions.add("academic")
        
        # Context based
        if context.get("rag_results") or context.get("web_results"):
            conditions.add("has_sources")
        
        return conditions
    
    def _collect_modules(self, active_conditions: set) -> List[PromptModule]:
        """Koşullara göre modülleri topla."""
        modules = []
        library = self.module_library
        
        all_modules = [
            library.IDENTITY_MODULE,
            library.CAPABILITIES_MODULE,
            library.COT_MODULE,
            library.DETAILED_MODE_MODULE,
            library.CONCISE_MODE_MODULE,
            library.ACADEMIC_MODE_MODULE,
            library.REFERENCE_MODULE,
            library.CONTINUATION_MODULE,
            library.CODING_MODULE,
            library.RULES_MODULE,
        ]
        
        for module in all_modules:
            # "always" koşulu veya aktif koşullardan biri varsa dahil et
            if "always" in module.conditions or any(c in active_conditions for c in module.conditions):
                modules.append(module)
        
        return modules
    
    def _select_modules_by_budget(
        self,
        modules: List[PromptModule],
        max_tokens: int
    ) -> List[PromptModule]:
        """Token budget'a göre modül seç."""
        # Priority'ye göre sırala
        sorted_modules = sorted(modules, key=lambda m: m.priority, reverse=True)
        
        selected = []
        used_tokens = 0
        
        for module in sorted_modules:
            if used_tokens + module.estimated_tokens <= max_tokens:
                selected.append(module)
                used_tokens += module.estimated_tokens
        
        # Priority sırasını koru
        return sorted(selected, key=lambda m: m.priority, reverse=True)
    
    def _assemble_prompt(
        self,
        modules: List[PromptModule],
        context: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """Modüllerden prompt oluştur."""
        parts = []
        
        # Modül içeriklerini ekle
        for module in modules:
            parts.append(module.content)
        
        # Context bölümlerini ekle
        if context.get("chat_history"):
            history_text = self._format_history(context["chat_history"])
            if history_text:
                parts.append(f"\n### ÖNCEKİ KONUŞMA\n{history_text}")
        
        if context.get("rag_results"):
            rag_text = self._format_rag_results(context["rag_results"])
            if rag_text:
                parts.append(f"\n### BİLGİ TABANI\n{rag_text}")
        
        if context.get("web_results"):
            web_text = self._format_web_results(context["web_results"])
            if web_text:
                parts.append(f"\n### WEB KAYNAKLARI\n{web_text}")
        
        if context.get("notes"):
            notes_text = self._format_notes(context["notes"])
            if notes_text:
                parts.append(f"\n### KULLANICI NOTLARI\n{notes_text}")
        
        return "\n\n".join(parts)
    
    def _format_history(self, history: List[Dict], max_messages: int = 10) -> str:
        """Chat history'yi formatla."""
        if not history:
            return ""
        
        recent = history[-max_messages:]
        lines = []
        for msg in recent:
            role = "👤 Kullanıcı" if msg.get("role") == "user" else "🤖 Asistan"
            content = msg.get("content", "")[:500]  # Truncate long messages
            lines.append(f"**{role}:** {content}")
        
        return "\n".join(lines)
    
    def _format_rag_results(self, results: List[Dict]) -> str:
        """RAG sonuçlarını formatla."""
        if not results:
            return ""
        
        lines = []
        for i, r in enumerate(results[:5], 1):
            source = r.get("metadata", {}).get("filename", f"Kaynak {i}")
            content = r.get("document", r.get("content", ""))[:400]
            lines.append(f"[{source}]: {content}")
        
        return "\n\n".join(lines)
    
    def _format_web_results(self, results: List[Dict]) -> str:
        """Web sonuçlarını formatla."""
        if not results:
            return ""
        
        lines = []
        for r in results[:3]:
            title = r.get("title", "Web")
            content = r.get("content", r.get("snippet", ""))[:300]
            url = r.get("url", "")
            lines.append(f"🌐 **{title}**\n{content}\n({url})")
        
        return "\n\n".join(lines)
    
    def _format_notes(self, notes: List[Dict]) -> str:
        """Notları formatla."""
        if not notes:
            return ""
        
        lines = []
        for note in notes[:5]:
            title = note.get("title", "Not")
            content = note.get("content", "")[:200]
            lines.append(f"📝 **{title}:** {content}")
        
        return "\n".join(lines)


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

# Global instances
query_analyzer = QueryAnalyzer()
prompt_builder = ModularPromptBuilder()


__all__ = [
    "ModularPromptBuilder",
    "QueryAnalyzer",
    "PromptModuleLibrary",
    "QueryType",
    "ResponseMode",
    "ComplexityLevel",
    "query_analyzer",
    "prompt_builder",
]
