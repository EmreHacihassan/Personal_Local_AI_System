"""
Enterprise AI Assistant - Query Analyzer Service
==================================================

Merkezi sorgu analiz servisi.
Tüm sorgu sınıflandırma ve analiz işlemlerini tek noktadan yönetir.

Features:
- Query complexity detection (simple/normal/comprehensive/research)
- Query type classification (greeting/question/task/creative)
- Intent classification integration
- Simple query fast-path detection
- Personal data query detection
- System query detection

This service eliminates duplicate pattern matching across the codebase.

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class QueryComplexity(str, Enum):
    """Sorgu karmaşıklık seviyesi."""
    SIMPLE = "simple"               # Kısa, basit sorgular (selamlaşma vb.)
    NORMAL = "normal"               # Standart sorgular
    COMPREHENSIVE = "comprehensive" # Detaylı analiz gerektiren
    RESEARCH = "research"           # Derin araştırma gerektiren


class QueryType(str, Enum):
    """Sorgu tipi sınıflandırması."""
    GREETING = "greeting"           # Selamlaşma
    SIMPLE_QUESTION = "simple_question"  # Basit soru
    COMPLEX_QUESTION = "complex_question" # Karmaşık soru
    TASK = "task"                   # Görev/iş talebi
    CREATIVE = "creative"           # Yaratıcı içerik
    EDUCATIONAL = "educational"     # Eğitim/öğrenme
    PERSONAL_DATA = "personal_data" # Kişisel veri sorgusu
    SYSTEM_INFO = "system_info"     # Sistem hakkında bilgi
    HYBRID = "hybrid"               # Karışık tip


class IntentType(str, Enum):
    """Kullanıcı niyet sınıflandırması."""
    INFORMATION_SEEKING = "information_seeking"
    TASK_EXECUTION = "task_execution"
    CONTENT_CREATION = "content_creation"
    LEARNING = "learning"
    CONVERSATION = "conversation"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QueryAnalysis:
    """Sorgu analiz sonucu."""
    original_query: str
    normalized_query: str
    complexity: QueryComplexity
    query_type: QueryType
    intent: IntentType
    is_simple: bool
    is_personal_data: bool
    is_system_query: bool
    requires_rag: bool
    requires_web_search: bool
    allow_general_knowledge: bool
    key_entities: List[str] = field(default_factory=list)
    detected_patterns: List[str] = field(default_factory=list)
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "complexity": self.complexity.value,
            "query_type": self.query_type.value,
            "intent": self.intent.value,
            "is_simple": self.is_simple,
            "is_personal_data": self.is_personal_data,
            "is_system_query": self.is_system_query,
            "requires_rag": self.requires_rag,
            "requires_web_search": self.requires_web_search,
            "allow_general_knowledge": self.allow_general_knowledge,
            "key_entities": self.key_entities,
            "confidence": self.confidence,
        }


# =============================================================================
# PATTERN DEFINITIONS (Centralized)
# =============================================================================

# Simple query patterns - greetings and basic interactions
SIMPLE_QUERY_PATTERNS = [
    r"^(merhaba|selam|hey|hi|hello|günaydın|iyi günler|iyi akşamlar|iyi geceler)[\s!?.]*$",
    r"^(nasılsın|ne haber|n'aber|naber|nasıl gidiyor)[\s!?.]*$",
    r"^(teşekkürler|teşekkür|sağol|eyvallah|thanks|thank you)[\s!?.]*$",
    r"^(evet|hayır|tamam|ok|olur|peki)[\s!?.]*$",
    r"^(iyi|güzel|süper|harika|muhteşem)[\s!?.]*$",
    r"^(anladım|tamamdır|oldu|görüşürüz|bye|bb|hoşçakal)[\s!?.]*$",
]

# System/self query patterns
SYSTEM_QUERY_PATTERNS = [
    r"(sen kimsin|seni kim yaptı|enterprise ai|kimsin|kendini tanıt)",
    r"(hakkında bilgi|ne yapabilirsin|what can you do|who are you|who made you)",
    r"(mcp nedir|multi-agent|teknolojilerin|yeteneklerin|özelliklerin)",
    r"(hangi model|hangi llm|kullandığın teknoloji)",
]

# Personal data query patterns - require RAG, no general knowledge fallback
PERSONAL_DATA_PATTERNS = [
    r"(dosya|belge|döküman|kayıt|not|arşiv)",
    r"(yüklediğim|eklediğim|kaydettiğim|yazdığım)",
    r"(benim|kendi|bendeki|bende|benimki)",
    r"(my files|my documents|my notes|uploaded|added)",
    r"(bilgi tabanı|knowledge base|veritabanı)",
]

# Educational/learning patterns - allow general knowledge
EDUCATIONAL_PATTERNS = [
    r"(öğret|anlat|açıkla|tarif et|nedir|ne demek)",
    r"(nasıl yapılır|nasıl çalışır|nasıl kullanılır)",
    r"(örnek ver|örneğini|örnekle|examples?)",
    r"(teach me|explain|what is|how does|how to)",
    r"(ders|eğitim|öğrenme|kurs|tutorial)",
    r"(fundamentals?|basics?|introduction|temel)",
]

# Complex/comprehensive query indicators
COMPREHENSIVE_PATTERNS = [
    r"(karşılaştır|analiz et|değerlendir|incele)",
    r"(detaylı|kapsamlı|derinlemesine|ayrıntılı)",
    r"(tüm|bütün|hepsi|herşey|komple)",
    r"(compare|analyze|evaluate|comprehensive)",
    r"(avantaj|dezavantaj|artı|eksi|pros|cons)",
    r"(stratej|plan|yol haritası|roadmap)",
]

# Research query indicators
RESEARCH_PATTERNS = [
    r"(araştır|incele|bul|keşfet|research)",
    r"(güncel|son|yeni|latest|recent|2024|2025|2026)",
    r"(trend|gelişme|yenilik|innovation)",
    r"(kaynak|referans|source|citation)",
    r"(akademik|bilimsel|scientific)",
]

# Creative content patterns
CREATIVE_PATTERNS = [
    r"(yaz|oluştur|hazırla|compose|write|create)",
    r"(hikaye|şiir|makale|blog|essay|story|poem)",
    r"(tasarla|design|çiz|sketch)",
    r"(senaryo|script|diyalog)",
]

# Task/command patterns
TASK_PATTERNS = [
    r"(yap|oluştur|sil|düzenle|güncelle|ekle)",
    r"(do|make|create|delete|edit|update|add)",
    r"(çevir|translate|dönüştür|convert)",
    r"(hesapla|calculate|compute)",
    r"(listele|list|sırala|sort)",
]


# =============================================================================
# QUERY ANALYZER SERVICE
# =============================================================================

class QueryAnalyzerService:
    """
    Merkezi sorgu analiz servisi.
    
    Tüm sorgu sınıflandırma işlemlerini tek noktadan yönetir.
    Duplicate pattern matching'i ortadan kaldırır.
    """
    
    def __init__(self):
        """Initialize with compiled patterns."""
        self._compile_patterns()
        self._stats = {
            "total_analyzed": 0,
            "simple_queries": 0,
            "personal_data_queries": 0,
            "system_queries": 0,
        }
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        self._simple_patterns = [re.compile(p, re.IGNORECASE) for p in SIMPLE_QUERY_PATTERNS]
        self._system_patterns = [re.compile(p, re.IGNORECASE) for p in SYSTEM_QUERY_PATTERNS]
        self._personal_patterns = [re.compile(p, re.IGNORECASE) for p in PERSONAL_DATA_PATTERNS]
        self._educational_patterns = [re.compile(p, re.IGNORECASE) for p in EDUCATIONAL_PATTERNS]
        self._comprehensive_patterns = [re.compile(p, re.IGNORECASE) for p in COMPREHENSIVE_PATTERNS]
        self._research_patterns = [re.compile(p, re.IGNORECASE) for p in RESEARCH_PATTERNS]
        self._creative_patterns = [re.compile(p, re.IGNORECASE) for p in CREATIVE_PATTERNS]
        self._task_patterns = [re.compile(p, re.IGNORECASE) for p in TASK_PATTERNS]
    
    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze a query and return comprehensive analysis.
        
        Args:
            query: User query string
            
        Returns:
            QueryAnalysis with all classification results
        """
        self._stats["total_analyzed"] += 1
        
        # Normalize query
        normalized = self._normalize_query(query)
        query_lower = query.lower().strip()
        
        # Detect patterns
        detected_patterns = []
        
        # Check simple query
        is_simple = self._is_simple_query(query_lower, detected_patterns)
        if is_simple:
            self._stats["simple_queries"] += 1
        
        # Check system query
        is_system = self._is_system_query(query_lower, detected_patterns)
        if is_system:
            self._stats["system_queries"] += 1
        
        # Check personal data query
        is_personal = self._is_personal_data_query(query_lower, detected_patterns)
        if is_personal:
            self._stats["personal_data_queries"] += 1
        
        # Determine complexity
        complexity = self._determine_complexity(query_lower, is_simple, detected_patterns)
        
        # Determine query type
        query_type = self._determine_query_type(
            query_lower, is_simple, is_system, is_personal, detected_patterns
        )
        
        # Determine intent
        intent = self._determine_intent(query_lower, query_type, detected_patterns)
        
        # Determine knowledge source requirements
        requires_rag = is_personal or complexity in [QueryComplexity.COMPREHENSIVE, QueryComplexity.RESEARCH]
        requires_web = complexity == QueryComplexity.RESEARCH and not is_personal
        allow_general = not is_personal and query_type in [
            QueryType.EDUCATIONAL, QueryType.SIMPLE_QUESTION, 
            QueryType.COMPLEX_QUESTION, QueryType.CREATIVE
        ]
        
        # Extract entities (simple extraction)
        entities = self._extract_entities(query)
        
        return QueryAnalysis(
            original_query=query,
            normalized_query=normalized,
            complexity=complexity,
            query_type=query_type,
            intent=intent,
            is_simple=is_simple,
            is_personal_data=is_personal,
            is_system_query=is_system,
            requires_rag=requires_rag,
            requires_web_search=requires_web,
            allow_general_knowledge=allow_general,
            key_entities=entities,
            detected_patterns=detected_patterns,
            confidence=self._calculate_confidence(detected_patterns),
        )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query text."""
        # Remove extra whitespace
        normalized = " ".join(query.split())
        # Remove repeated punctuation
        normalized = re.sub(r"([.!?])\1+", r"\1", normalized)
        return normalized.strip()
    
    def _is_simple_query(self, query_lower: str, patterns: List[str]) -> bool:
        """Check if query is a simple greeting or short interaction."""
        # Length check (but not sole criterion)
        if len(query_lower) > 50:
            return False
        
        # Pattern matching
        for pattern in self._simple_patterns:
            if pattern.match(query_lower):
                patterns.append("simple_pattern")
                return True
        
        # Very short queries without question marks are often simple
        if len(query_lower) < 15 and "?" not in query_lower:
            # But check if it's not a command
            if not any(p.search(query_lower) for p in self._task_patterns):
                patterns.append("short_simple")
                return True
        
        return False
    
    def _is_system_query(self, query_lower: str, patterns: List[str]) -> bool:
        """Check if query is about the system/AI itself."""
        for pattern in self._system_patterns:
            if pattern.search(query_lower):
                patterns.append("system_query")
                return True
        return False
    
    def _is_personal_data_query(self, query_lower: str, patterns: List[str]) -> bool:
        """Check if query is about user's personal data/documents."""
        for pattern in self._personal_patterns:
            if pattern.search(query_lower):
                patterns.append("personal_data")
                return True
        return False
    
    def _determine_complexity(
        self, 
        query_lower: str, 
        is_simple: bool,
        patterns: List[str]
    ) -> QueryComplexity:
        """Determine query complexity level."""
        if is_simple:
            return QueryComplexity.SIMPLE
        
        # Check for research indicators
        research_score = sum(1 for p in self._research_patterns if p.search(query_lower))
        if research_score >= 2:
            patterns.append("research_indicators")
            return QueryComplexity.RESEARCH
        
        # Check for comprehensive indicators
        comp_score = sum(1 for p in self._comprehensive_patterns if p.search(query_lower))
        if comp_score >= 1:
            patterns.append("comprehensive_indicators")
            return QueryComplexity.COMPREHENSIVE
        
        # Length-based heuristic
        word_count = len(query_lower.split())
        if word_count >= 20:
            return QueryComplexity.COMPREHENSIVE
        elif word_count >= 10:
            return QueryComplexity.NORMAL
        
        return QueryComplexity.NORMAL
    
    def _determine_query_type(
        self,
        query_lower: str,
        is_simple: bool,
        is_system: bool,
        is_personal: bool,
        patterns: List[str]
    ) -> QueryType:
        """Determine the type of query."""
        if is_simple and "simple_pattern" in patterns:
            return QueryType.GREETING
        
        if is_system:
            return QueryType.SYSTEM_INFO
        
        if is_personal:
            return QueryType.PERSONAL_DATA
        
        # Check educational
        if any(p.search(query_lower) for p in self._educational_patterns):
            patterns.append("educational")
            return QueryType.EDUCATIONAL
        
        # Check creative
        if any(p.search(query_lower) for p in self._creative_patterns):
            patterns.append("creative")
            return QueryType.CREATIVE
        
        # Check task
        if any(p.search(query_lower) for p in self._task_patterns):
            patterns.append("task")
            return QueryType.TASK
        
        # Default to question based on punctuation
        if "?" in query_lower:
            if len(query_lower.split()) > 10:
                return QueryType.COMPLEX_QUESTION
            return QueryType.SIMPLE_QUESTION
        
        return QueryType.HYBRID
    
    def _determine_intent(
        self,
        query_lower: str,
        query_type: QueryType,
        patterns: List[str]
    ) -> IntentType:
        """Determine user intent."""
        intent_map = {
            QueryType.GREETING: IntentType.CONVERSATION,
            QueryType.SIMPLE_QUESTION: IntentType.INFORMATION_SEEKING,
            QueryType.COMPLEX_QUESTION: IntentType.ANALYSIS,
            QueryType.TASK: IntentType.TASK_EXECUTION,
            QueryType.CREATIVE: IntentType.CONTENT_CREATION,
            QueryType.EDUCATIONAL: IntentType.LEARNING,
            QueryType.PERSONAL_DATA: IntentType.INFORMATION_SEEKING,
            QueryType.SYSTEM_INFO: IntentType.INFORMATION_SEEKING,
            QueryType.HYBRID: IntentType.INFORMATION_SEEKING,
        }
        
        # Check for comparison intent
        if any(p.search(query_lower) for p in self._comprehensive_patterns[:2]):
            return IntentType.COMPARISON
        
        return intent_map.get(query_type, IntentType.INFORMATION_SEEKING)
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract key entities from query (simple extraction)."""
        entities = []
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)
        
        # Extract capitalized words (potential proper nouns)
        caps = re.findall(r'\b[A-Z][a-zA-Z]+\b', query)
        entities.extend(caps)
        
        return list(set(entities))[:5]  # Limit to 5
    
    def _calculate_confidence(self, patterns: List[str]) -> float:
        """Calculate confidence based on detected patterns."""
        if not patterns:
            return 0.5
        
        # More patterns = higher confidence
        confidence = min(0.5 + len(patterns) * 0.1, 0.95)
        return round(confidence, 2)
    
    def is_simple_query(self, query: str) -> bool:
        """Quick check if query is simple (for fast-path)."""
        return self.analyze(query).is_simple
    
    def get_complexity(self, query: str) -> QueryComplexity:
        """Get query complexity level."""
        return self.analyze(query).complexity
    
    def get_stats(self) -> Dict[str, int]:
        """Get analysis statistics."""
        return self._stats.copy()


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

query_analyzer = QueryAnalyzerService()
