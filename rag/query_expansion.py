"""
Query Expansion Module
======================

Sorgu genişletme ve iyileştirme stratejileri.

Teknikler:
- Synonym Expansion: Eş anlamlı kelimelerle genişletme
- HyDE: Hypothetical Document Embeddings
- Multi-Query: Farklı perspektiflerden sorgular
- Step-Back: Soyutlama ile genişletme
"""

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import hashlib


class ExpansionStrategy(Enum):
    """Genişletme stratejileri"""
    SYNONYM = "synonym"
    HYDE = "hyde"
    MULTI_QUERY = "multi_query"
    STEP_BACK = "step_back"
    CONTEXTUAL = "contextual"
    KEYWORD = "keyword"


@dataclass
class ExpandedQuery:
    """Genişletilmiş sorgu"""
    original: str
    expanded_queries: List[str]
    strategy: ExpansionStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def all_queries(self) -> List[str]:
        """Tüm sorguları döndür (orijinal dahil)"""
        return [self.original] + self.expanded_queries
    
    @property
    def unique_queries(self) -> List[str]:
        """Tekrarsız sorguları döndür"""
        seen = set()
        result = []
        for q in self.all_queries:
            normalized = q.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                result.append(q)
        return result


class QueryExpander(ABC):
    """Sorgu genişletici temel sınıfı"""
    
    strategy: ExpansionStrategy
    
    @abstractmethod
    async def expand(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpandedQuery:
        """Sorguyu genişlet"""
        pass


class SynonymExpander(QueryExpander):
    """
    Eş anlamlı kelimelerle genişletme
    
    Basit bir eş anlamlı sözlük kullanır.
    """
    
    strategy = ExpansionStrategy.SYNONYM
    
    # Türkçe eş anlamlılar (basit örnek)
    SYNONYMS: Dict[str, List[str]] = {
        "nasıl": ["ne şekilde", "hangi yolla", "ne biçimde"],
        "neden": ["niçin", "sebebi nedir", "ne sebeple"],
        "ne": ["hangi", "neyi"],
        "yap": ["gerçekleştir", "icra et", "uygula"],
        "bul": ["ara", "keşfet", "tespit et"],
        "göster": ["sun", "sergile", "belirt"],
        "açıkla": ["izah et", "anlat", "detaylandır"],
        "özetle": ["kısalt", "derle", "hulasa et"],
        "analiz": ["inceleme", "çözümleme", "değerlendirme"],
        "rapor": ["belge", "döküman", "tutanak"],
        "veri": ["bilgi", "data", "enformasyon"],
        "sistem": ["yapı", "düzen", "mekanizma"],
        "süreç": ["proses", "işlem", "aşama"],
        "yönetim": ["idare", "yönetme", "idarehane"],
        "performans": ["başarım", "verim", "etkinlik"],
        "strateji": ["plan", "taktik", "yöntem"],
        "hedef": ["amaç", "gaye", "maksat"],
    }
    
    def __init__(self, max_expansions: int = 3):
        self.max_expansions = max_expansions
    
    def _find_synonyms(self, word: str) -> List[str]:
        """Kelime için eş anlamlıları bul"""
        word_lower = word.lower()
        
        # Direkt eşleşme
        if word_lower in self.SYNONYMS:
            return self.SYNONYMS[word_lower][:self.max_expansions]
        
        # Kısmi eşleşme
        for key, synonyms in self.SYNONYMS.items():
            if key in word_lower or word_lower in key:
                return synonyms[:self.max_expansions]
        
        return []
    
    async def expand(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpandedQuery:
        """Sorguyu eş anlamlılarla genişlet"""
        words = query.split()
        expanded_queries = []
        
        for i, word in enumerate(words):
            synonyms = self._find_synonyms(word)
            
            for synonym in synonyms:
                new_words = words.copy()
                new_words[i] = synonym
                new_query = " ".join(new_words)
                
                if new_query.lower() != query.lower():
                    expanded_queries.append(new_query)
        
        return ExpandedQuery(
            original=query,
            expanded_queries=expanded_queries[:self.max_expansions],
            strategy=self.strategy,
            metadata={"word_count": len(words)}
        )


class HyDEExpander(QueryExpander):
    """
    Hypothetical Document Embeddings (HyDE)
    
    LLM kullanarak sorguya cevap olabilecek
    hipotetik bir doküman oluşturur.
    """
    
    strategy = ExpansionStrategy.HYDE
    
    HYDE_PROMPT = """Aşağıdaki soruya detaylı bir cevap oluştur. 
Bu cevap, gerçek bir dokümandan alınmış gibi bilgilendirici olmalı.
Kısa paragraflar halinde yaz.

Soru: {query}

Cevap:"""
    
    def __init__(
        self,
        llm_func: Optional[Callable] = None,
        num_hypothetical: int = 1
    ):
        self.llm_func = llm_func
        self.num_hypothetical = num_hypothetical
    
    async def expand(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpandedQuery:
        """HyDE ile genişlet"""
        expanded_queries = []
        
        if self.llm_func:
            try:
                prompt = self.HYDE_PROMPT.format(query=query)
                
                for _ in range(self.num_hypothetical):
                    response = await self.llm_func(prompt)
                    if response:
                        expanded_queries.append(response.strip())
            except Exception:
                pass
        
        return ExpandedQuery(
            original=query,
            expanded_queries=expanded_queries,
            strategy=self.strategy,
            metadata={"num_hypothetical": len(expanded_queries)}
        )


class MultiQueryExpander(QueryExpander):
    """
    Multi-Query Expansion
    
    LLM kullanarak farklı perspektiflerden sorgular oluşturur.
    """
    
    strategy = ExpansionStrategy.MULTI_QUERY
    
    MULTI_QUERY_PROMPT = """Aşağıdaki soruyu farklı şekillerde ifade et.
Her bir versiyon aynı bilgiyi arıyor olmalı ama farklı kelimeler kullanmalı.
{num_queries} farklı versiyon oluştur.

Orijinal soru: {query}

Her satırda bir versiyon olacak şekilde yaz:"""
    
    def __init__(
        self,
        llm_func: Optional[Callable] = None,
        num_queries: int = 3
    ):
        self.llm_func = llm_func
        self.num_queries = num_queries
    
    async def expand(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpandedQuery:
        """Multi-query ile genişlet"""
        expanded_queries = []
        
        if self.llm_func:
            try:
                prompt = self.MULTI_QUERY_PROMPT.format(
                    query=query,
                    num_queries=self.num_queries
                )
                
                response = await self.llm_func(prompt)
                
                if response:
                    # Satır satır ayır
                    lines = [l.strip() for l in response.split("\n") if l.strip()]
                    
                    # Numaraları temizle
                    for line in lines:
                        cleaned = re.sub(r"^\d+[\.\)\-\:]\s*", "", line)
                        if cleaned and cleaned.lower() != query.lower():
                            expanded_queries.append(cleaned)
            except Exception:
                pass
        
        return ExpandedQuery(
            original=query,
            expanded_queries=expanded_queries[:self.num_queries],
            strategy=self.strategy,
            metadata={"num_generated": len(expanded_queries)}
        )


class StepBackExpander(QueryExpander):
    """
    Step-Back Prompting
    
    Sorguyu daha soyut/genel bir forma dönüştürür.
    """
    
    strategy = ExpansionStrategy.STEP_BACK
    
    STEP_BACK_PROMPT = """Aşağıdaki spesifik soruyu daha genel/soyut bir soruya dönüştür.
Genel soru, orijinal soruyu cevaplayabilecek arka plan bilgisini kapsamalı.

Spesifik soru: {query}

Genel soru:"""
    
    def __init__(
        self,
        llm_func: Optional[Callable] = None,
        include_original: bool = True
    ):
        self.llm_func = llm_func
        self.include_original = include_original
    
    async def expand(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpandedQuery:
        """Step-back ile genişlet"""
        expanded_queries = []
        
        if self.llm_func:
            try:
                prompt = self.STEP_BACK_PROMPT.format(query=query)
                response = await self.llm_func(prompt)
                
                if response:
                    step_back_query = response.strip()
                    if step_back_query.lower() != query.lower():
                        expanded_queries.append(step_back_query)
            except Exception:
                pass
        
        return ExpandedQuery(
            original=query,
            expanded_queries=expanded_queries,
            strategy=self.strategy,
            metadata={"has_step_back": len(expanded_queries) > 0}
        )


class KeywordExpander(QueryExpander):
    """
    Keyword Extraction ve Expansion
    
    Sorgudaki anahtar kelimeleri çıkarır ve bunlarla
    arama yapar.
    """
    
    strategy = ExpansionStrategy.KEYWORD
    
    # Türkçe stop words
    STOP_WORDS: Set[str] = {
        "bir", "bu", "şu", "o", "ve", "veya", "ile", "için",
        "de", "da", "den", "dan", "mı", "mi", "mu", "mü",
        "ne", "nasıl", "neden", "hangi", "kim", "nere",
        "ama", "ancak", "fakat", "lakin", "yani", "çünkü",
        "her", "hiç", "bazı", "tüm", "en", "daha", "çok",
    }
    
    def __init__(
        self,
        min_word_length: int = 3,
        max_keywords: int = 5
    ):
        self.min_word_length = min_word_length
        self.max_keywords = max_keywords
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Metinden anahtar kelimeleri çıkar"""
        # Basit tokenization
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Stop words ve kısa kelimeleri filtrele
        keywords = [
            w for w in words
            if len(w) >= self.min_word_length
            and w not in self.STOP_WORDS
        ]
        
        # Sıklığa göre sırala
        from collections import Counter
        word_counts = Counter(keywords)
        
        return [w for w, _ in word_counts.most_common(self.max_keywords)]
    
    async def expand(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpandedQuery:
        """Anahtar kelimelerle genişlet"""
        keywords = self._extract_keywords(query)
        
        expanded_queries = []
        
        # Sadece anahtar kelimeler
        if keywords:
            keyword_query = " ".join(keywords)
            if keyword_query.lower() != query.lower():
                expanded_queries.append(keyword_query)
        
        # Anahtar kelime kombinasyonları (2'li)
        if len(keywords) >= 2:
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    combo = f"{keywords[i]} {keywords[j]}"
                    expanded_queries.append(combo)
        
        return ExpandedQuery(
            original=query,
            expanded_queries=expanded_queries[:5],
            strategy=self.strategy,
            metadata={
                "keywords": keywords,
                "keyword_count": len(keywords)
            }
        )


class QueryExpansionManager:
    """
    Sorgu genişletme yöneticisi
    
    Birden fazla genişletme stratejisini koordine eder.
    """
    
    def __init__(
        self,
        llm_func: Optional[Callable] = None,
        strategies: Optional[List[ExpansionStrategy]] = None,
        max_total_queries: int = 10
    ):
        self.llm_func = llm_func
        self.max_total_queries = max_total_queries
        
        # Varsayılan stratejiler
        if strategies is None:
            strategies = [
                ExpansionStrategy.SYNONYM,
                ExpansionStrategy.KEYWORD
            ]
            if llm_func:
                strategies.append(ExpansionStrategy.MULTI_QUERY)
        
        self.strategies = strategies
        self._expanders: Dict[ExpansionStrategy, QueryExpander] = {}
        
        self._initialize_expanders()
    
    def _initialize_expanders(self):
        """Genişleticileri başlat"""
        self._expanders = {
            ExpansionStrategy.SYNONYM: SynonymExpander(),
            ExpansionStrategy.KEYWORD: KeywordExpander(),
        }
        
        if self.llm_func:
            self._expanders.update({
                ExpansionStrategy.HYDE: HyDEExpander(self.llm_func),
                ExpansionStrategy.MULTI_QUERY: MultiQueryExpander(self.llm_func),
                ExpansionStrategy.STEP_BACK: StepBackExpander(self.llm_func),
            })
    
    def add_expander(
        self,
        strategy: ExpansionStrategy,
        expander: QueryExpander
    ):
        """Yeni genişletici ekle"""
        self._expanders[strategy] = expander
        if strategy not in self.strategies:
            self.strategies.append(strategy)
    
    async def expand(
        self,
        query: str,
        strategies: Optional[List[ExpansionStrategy]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sorguyu genişlet
        
        Args:
            query: Orijinal sorgu
            strategies: Kullanılacak stratejiler
            context: Ek bağlam
            
        Returns:
            Genişletme sonucu
        """
        strategies = strategies or self.strategies
        
        all_queries = [query]
        results_by_strategy = {}
        
        # Her strateji için genişlet
        for strategy in strategies:
            expander = self._expanders.get(strategy)
            if not expander:
                continue
            
            try:
                expanded = await expander.expand(query, context)
                results_by_strategy[strategy.value] = {
                    "queries": expanded.expanded_queries,
                    "metadata": expanded.metadata
                }
                
                all_queries.extend(expanded.expanded_queries)
            except Exception as e:
                results_by_strategy[strategy.value] = {
                    "error": str(e),
                    "queries": []
                }
        
        # Tekrarları kaldır
        seen = set()
        unique_queries = []
        for q in all_queries:
            normalized = q.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_queries.append(q)
        
        # Sınırla
        unique_queries = unique_queries[:self.max_total_queries]
        
        return {
            "original_query": query,
            "expanded_queries": unique_queries[1:],  # Orijinali çıkar
            "all_queries": unique_queries,
            "total_queries": len(unique_queries),
            "strategies_used": list(results_by_strategy.keys()),
            "results_by_strategy": results_by_strategy
        }
    
    async def expand_for_retrieval(
        self,
        query: str,
        retrieval_func: Callable,
        top_k: int = 5
    ) -> List[Any]:
        """
        Genişletilmiş sorgularla retrieval yap
        
        Args:
            query: Orijinal sorgu
            retrieval_func: Retrieval fonksiyonu (async, query alır, sonuç döner)
            top_k: Her sorgu için alınacak sonuç sayısı
            
        Returns:
            Birleştirilmiş sonuçlar
        """
        expansion = await self.expand(query)
        all_results = []
        seen_ids = set()
        
        for q in expansion["all_queries"]:
            try:
                results = await retrieval_func(q, top_k)
                
                for result in results:
                    # Tekrar kontrolü
                    result_id = getattr(result, "id", None)
                    if result_id is None:
                        result_id = hashlib.md5(
                            str(result).encode()
                        ).hexdigest()
                    
                    if result_id not in seen_ids:
                        seen_ids.add(result_id)
                        all_results.append(result)
            except Exception:
                continue
        
        return all_results


# Singleton instance
query_expansion_manager = QueryExpansionManager()
