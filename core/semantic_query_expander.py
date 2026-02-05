"""
🔍 Semantic Query Expander - Premium Search Enhancement

Tek sorguyu 5-10 semantik varyasyona genişletir.
LLM tabanlı query expansion ile ilişkili konuları da arar.

Author: Enterprise AI Team
Date: 2025-02
"""

import asyncio
import logging
import re
import hashlib
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ExpansionStrategy(Enum):
    """Query expansion stratejileri"""
    SYNONYM = "synonym"           # Eş anlamlılar
    HYPERNYM = "hypernym"         # Üst kavramlar (Python → Programming Language)
    HYPONYM = "hyponym"           # Alt kavramlar (AI → Machine Learning)
    RELATED = "related"           # İlişkili kavramlar
    REPHRASE = "rephrase"         # Farklı ifade
    SPECIFIC = "specific"         # Daha spesifik
    GENERAL = "general"           # Daha genel
    TECHNICAL = "technical"       # Teknik terimlerle


@dataclass
class ExpandedQuery:
    """Genişletilmiş sorgu"""
    original: str
    expanded: str
    strategy: ExpansionStrategy
    confidence: float = 0.8
    keywords: List[str] = field(default_factory=list)


@dataclass
class ExpansionResult:
    """Expansion sonucu"""
    original_query: str
    expanded_queries: List[ExpandedQuery]
    key_concepts: List[str]
    related_terms: List[str]
    total_variations: int
    
    def get_all_queries(self) -> List[str]:
        """Tüm sorguları döndür (original + expanded)"""
        queries = [self.original_query]
        queries.extend([eq.expanded for eq in self.expanded_queries])
        return list(dict.fromkeys(queries))  # Preserve order, remove duplicates


class SemanticQueryExpander:
    """
    Semantic Query Expander
    
    LLM kullanarak sorguyu semantik olarak genişletir.
    Tek sorgu yerine 5-10 farklı varyasyon üretir.
    """
    
    # Turkish stopwords
    TURKISH_STOPWORDS = {
        "ve", "veya", "ile", "için", "bu", "şu", "o", "bir", "de", "da",
        "mi", "mı", "mu", "mü", "ne", "nasıl", "neden", "kim", "hangi",
        "gibi", "kadar", "daha", "çok", "az", "en", "her", "bazı", "hiç",
        "olan", "olarak", "üzerinde", "altında", "içinde", "dışında"
    }
    
    # English stopwords
    ENGLISH_STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "of", "in", "to",
        "for", "with", "on", "at", "by", "from", "as", "into", "through",
        "about", "what", "which", "who", "how", "why", "when", "where"
    }
    
    # Query expansion prompt template
    EXPANSION_PROMPT = """Sen bir arama sorgusu genişletme uzmanısın.

KULLANICI SORGUSU: "{query}"

Bu sorguyla ilişkili 8 farklı arama sorgusu üret. Her sorgu farklı bir açıdan yaklaşmalı:

1. **REPHRASE**: Aynı anlam, farklı kelimeler
2. **SPECIFIC**: Daha detaylı/spesifik versiyon
3. **GENERAL**: Daha genel/kapsayıcı versiyon
4. **TECHNICAL**: Teknik terimlerle
5. **CASUAL**: Günlük dille
6. **RELATED_1**: İlişkili alt konu 1
7. **RELATED_2**: İlişkili alt konu 2
8. **CONCEPT**: Temel kavram odaklı

KURALLAR:
- Her sorgu 3-10 kelime olmalı
- Orijinal sorgudan farklı kelimeler kullan
- Türkçe soru ise Türkçe, İngilizce ise İngilizce yaz
- Sadece arama sorguları yaz, açıklama ekleme

FORMAT (JSON array):
["sorgu1", "sorgu2", "sorgu3", "sorgu4", "sorgu5", "sorgu6", "sorgu7", "sorgu8"]

Sadece JSON array döndür, başka bir şey yazma."""

    CONCEPT_EXTRACTION_PROMPT = """Aşağıdaki sorgudan anahtar kavramları çıkar.

SORGU: "{query}"

FORMAT (JSON):
{{
    "main_concepts": ["kavram1", "kavram2"],
    "related_terms": ["ilişkili1", "ilişkili2", "ilişkili3"],
    "domain": "konu alanı"
}}

Sadece JSON döndür."""

    def __init__(self, llm_client=None, cache_enabled: bool = True):
        """
        Args:
            llm_client: LLM client (Ollama/OpenAI compatible)
            cache_enabled: Expansion sonuçlarını cache'le
        """
        self.llm_client = llm_client
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, ExpansionResult] = {}
        self._stats = {
            "total_expansions": 0,
            "cache_hits": 0,
            "llm_calls": 0,
            "fallback_used": 0,
        }
    
    def _get_cache_key(self, query: str) -> str:
        """Cache key oluştur"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Metinden anahtar kelimeleri çıkar"""
        # Küçük harfe çevir ve özel karakterleri temizle
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Kelimelere ayır
        words = text.split()
        
        # Stopwords'leri kaldır
        stopwords = self.TURKISH_STOPWORDS | self.ENGLISH_STOPWORDS
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        return keywords
    
    def _basic_expansion(self, query: str) -> List[ExpandedQuery]:
        """LLM olmadan temel expansion (fallback)"""
        keywords = self._extract_keywords(query)
        expanded = []
        
        # 1. Keyword combinations
        if len(keywords) >= 2:
            # Keywords reversed
            expanded.append(ExpandedQuery(
                original=query,
                expanded=" ".join(reversed(keywords)),
                strategy=ExpansionStrategy.REPHRASE,
                confidence=0.6
            ))
            
            # Subset combinations
            for i in range(len(keywords)):
                subset = keywords[:i] + keywords[i+1:]
                if subset:
                    expanded.append(ExpandedQuery(
                        original=query,
                        expanded=" ".join(subset),
                        strategy=ExpansionStrategy.GENERAL,
                        confidence=0.5
                    ))
        
        # 2. Add common modifiers
        modifiers_tr = ["nedir", "nasıl", "örnekleri", "kullanımı", "avantajları"]
        modifiers_en = ["tutorial", "guide", "examples", "best practices", "introduction"]
        
        # Detect language
        is_turkish = any(c in query.lower() for c in ['ı', 'ğ', 'ü', 'ş', 'ö', 'ç'])
        modifiers = modifiers_tr if is_turkish else modifiers_en
        
        for mod in modifiers[:3]:
            expanded.append(ExpandedQuery(
                original=query,
                expanded=f"{query} {mod}",
                strategy=ExpansionStrategy.SPECIFIC,
                confidence=0.5
            ))
        
        return expanded[:8]
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """LLM'i çağır"""
        if not self.llm_client:
            # Try to import and use default LLM
            try:
                from core.llm_manager import llm_manager
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: llm_manager.generate(prompt, model="qwen3:4b")
                )
                return response
            except Exception as e:
                logger.warning(f"LLM call failed: {e}")
                return None
        
        try:
            if hasattr(self.llm_client, 'generate'):
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.llm_client.generate(prompt)
                )
                return response
            elif hasattr(self.llm_client, 'chat'):
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.llm_client.chat(prompt)
                )
                return response
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
        
        return None
    
    def _parse_json_array(self, text: str) -> List[str]:
        """JSON array'i parse et"""
        import json
        
        # Clean the text
        text = text.strip()
        
        # Find JSON array
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: Extract quoted strings
        matches = re.findall(r'"([^"]+)"', text)
        if matches:
            return matches
        
        # Fallback: Split by newlines
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        return [re.sub(r'^[\d\.\)\-\*]+\s*', '', l) for l in lines if len(l) > 3]
    
    def _parse_json_object(self, text: str) -> Dict:
        """JSON object'i parse et"""
        import json
        
        text = text.strip()
        
        # Find JSON object
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        return {}
    
    async def expand_query(
        self,
        query: str,
        max_variations: int = 8,
        use_llm: bool = True
    ) -> ExpansionResult:
        """
        Sorguyu semantik olarak genişlet.
        
        Args:
            query: Orijinal sorgu
            max_variations: Maksimum varyasyon sayısı
            use_llm: LLM kullanılsın mı
            
        Returns:
            ExpansionResult with all variations
        """
        self._stats["total_expansions"] += 1
        
        # Check cache
        cache_key = self._get_cache_key(query)
        if self.cache_enabled and cache_key in self._cache:
            self._stats["cache_hits"] += 1
            return self._cache[cache_key]
        
        # Extract keywords
        keywords = self._extract_keywords(query)
        
        expanded_queries: List[ExpandedQuery] = []
        key_concepts: List[str] = keywords[:5]
        related_terms: List[str] = []
        
        if use_llm:
            # Try LLM expansion
            prompt = self.EXPANSION_PROMPT.format(query=query)
            response = await self._call_llm(prompt)
            
            if response:
                self._stats["llm_calls"] += 1
                variations = self._parse_json_array(response)
                
                strategies = [
                    ExpansionStrategy.REPHRASE,
                    ExpansionStrategy.SPECIFIC,
                    ExpansionStrategy.GENERAL,
                    ExpansionStrategy.TECHNICAL,
                    ExpansionStrategy.RELATED,
                    ExpansionStrategy.RELATED,
                    ExpansionStrategy.RELATED,
                    ExpansionStrategy.SYNONYM,
                ]
                
                for i, var in enumerate(variations[:max_variations]):
                    if var and var.lower() != query.lower():
                        strategy = strategies[i] if i < len(strategies) else ExpansionStrategy.RELATED
                        expanded_queries.append(ExpandedQuery(
                            original=query,
                            expanded=var,
                            strategy=strategy,
                            confidence=0.8 - (i * 0.05),
                            keywords=self._extract_keywords(var)
                        ))
                
                # Extract concepts
                concept_prompt = self.CONCEPT_EXTRACTION_PROMPT.format(query=query)
                concept_response = await self._call_llm(concept_prompt)
                if concept_response:
                    concept_data = self._parse_json_object(concept_response)
                    key_concepts = concept_data.get("main_concepts", keywords[:5])
                    related_terms = concept_data.get("related_terms", [])
        
        # Fallback if LLM didn't work or not enough variations
        if len(expanded_queries) < 3:
            self._stats["fallback_used"] += 1
            fallback = self._basic_expansion(query)
            for fb in fallback:
                if fb.expanded.lower() not in [eq.expanded.lower() for eq in expanded_queries]:
                    expanded_queries.append(fb)
                    if len(expanded_queries) >= max_variations:
                        break
        
        # Create result
        result = ExpansionResult(
            original_query=query,
            expanded_queries=expanded_queries[:max_variations],
            key_concepts=key_concepts,
            related_terms=related_terms,
            total_variations=len(expanded_queries)
        )
        
        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = result
        
        logger.info(f"Query expanded: '{query}' → {len(result.expanded_queries)} variations")
        return result
    
    async def batch_expand(
        self,
        queries: List[str],
        max_variations_per_query: int = 5
    ) -> Dict[str, ExpansionResult]:
        """Birden fazla sorguyu paralel genişlet"""
        tasks = [
            self.expand_query(q, max_variations_per_query)
            for q in queries
        ]
        results = await asyncio.gather(*tasks)
        return {q: r for q, r in zip(queries, results)}
    
    def get_stats(self) -> Dict[str, int]:
        """İstatistikleri döndür"""
        return self._stats.copy()
    
    def clear_cache(self):
        """Cache'i temizle"""
        self._cache.clear()


# Singleton instance
_expander_instance: Optional[SemanticQueryExpander] = None


def get_query_expander() -> SemanticQueryExpander:
    """Singleton query expander instance'ı al"""
    global _expander_instance
    if _expander_instance is None:
        _expander_instance = SemanticQueryExpander()
    return _expander_instance


# === UTILITY FUNCTIONS ===

async def expand_search_query(query: str, max_variations: int = 8) -> List[str]:
    """
    Basit utility function - sorguyu genişlet ve tüm varyasyonları döndür.
    
    Usage:
        queries = await expand_search_query("Python machine learning")
        # Returns: ["Python machine learning", "ML with Python tutorial", ...]
    """
    expander = get_query_expander()
    result = await expander.expand_query(query, max_variations)
    return result.get_all_queries()


def expand_search_query_sync(query: str, max_variations: int = 8) -> List[str]:
    """Senkron versiyon"""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(expand_search_query(query, max_variations))


# === TEST ===

if __name__ == "__main__":
    async def test():
        expander = SemanticQueryExpander()
        
        test_queries = [
            "Python machine learning tutorial",
            "Yapay zeka nedir",
            "React vs Vue comparison",
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Original: {query}")
            print(f"{'='*60}")
            
            result = await expander.expand_query(query)
            
            print(f"\nKey Concepts: {result.key_concepts}")
            print(f"Related Terms: {result.related_terms}")
            print(f"\nExpanded Queries:")
            
            for i, eq in enumerate(result.expanded_queries, 1):
                print(f"  {i}. [{eq.strategy.value}] {eq.expanded} (conf: {eq.confidence:.2f})")
            
            print(f"\nAll queries for search:")
            for q in result.get_all_queries():
                print(f"  - {q}")
    
    asyncio.run(test())
