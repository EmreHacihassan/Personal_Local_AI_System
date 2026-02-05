"""
🧠 HyDE - Hypothetical Document Embeddings
==========================================

Premium RAG enhancement using hypothetical document generation.
Perplexity AI ve Anthropic Claude seviyesinde.

Özellikler:
- HyDE: Sorgudan varsayımsal döküman oluşturma
- Query Expansion: Sorgu genişletme
- Query Decomposition: Karmaşık sorguyu parçalama
- Multi-Query Retrieval: Çoklu sorgu ile retrieval
- Step-Back Prompting: Soyutlama ile arama

Reference: "Precise Zero-Shot Dense Retrieval without Relevance Labels"
https://arxiv.org/abs/2212.10496
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import hashlib

# Premium Cache integration
try:
    from core.premium_cache import get_embedding_cache, EmbeddingCache
    _embedding_cache: Optional[EmbeddingCache] = None
    CACHE_ENABLED = True
except ImportError:
    _embedding_cache = None
    CACHE_ENABLED = False

logger = logging.getLogger(__name__)


class QueryTransformationType(Enum):
    """Sorgu dönüşüm türleri"""
    HYDE = "hyde"                    # Hypothetical document
    EXPANSION = "expansion"          # Query expansion
    DECOMPOSITION = "decomposition"  # Break into sub-queries
    STEP_BACK = "step_back"          # Abstract the query
    MULTI_QUERY = "multi_query"      # Multiple query variants
    REWRITE = "rewrite"              # Query rewriting


@dataclass
class TransformedQuery:
    """Dönüştürülmüş sorgu"""
    original_query: str
    transformed_queries: List[str]
    transformation_type: QueryTransformationType
    hypothetical_document: Optional[str] = None
    sub_questions: List[str] = field(default_factory=list)
    expanded_terms: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def primary_query(self) -> str:
        """Ana transformed sorgu"""
        return self.transformed_queries[0] if self.transformed_queries else self.original_query


@dataclass
class HyDEResult:
    """HyDE sonucu"""
    original_query: str
    hypothetical_document: str
    document_embedding: Optional[List[float]] = None
    retrieval_queries: List[str] = field(default_factory=list)
    generation_time_ms: int = 0


class QueryAnalyzer:
    """Sorgu analizi ve sınıflandırma"""
    
    # Soru türleri
    QUESTION_PATTERNS = {
        "factual": [
            r"^(ne|nedir|kim|kimdir|nerede|ne zaman|kaç|hangi)",
            r"^(what|who|where|when|how many|which)",
        ],
        "explanatory": [
            r"^(neden|niçin|nasıl|açıkla|anlat)",
            r"^(why|how|explain|describe)",
        ],
        "comparative": [
            r"(fark|karşılaştır|mı.*mı|versus|vs)",
            r"(difference|compare|better|worse|vs)",
        ],
        "procedural": [
            r"^(nasıl yapılır|nasıl yaparım|adımlar)",
            r"^(how to|steps to|guide|tutorial)",
        ],
        "definitional": [
            r"(tanımı|anlamı|ne demek)",
            r"(definition|meaning|what is)",
        ],
    }
    
    # Karmaşıklık göstergeleri
    COMPLEXITY_INDICATORS = {
        "high": [
            r"(ve|veya|ayrıca|hem.*hem|both.*and)",
            r"(arasındaki|ilişki|bağlantı|etki)",
            r"(compare|analyze|evaluate|discuss)",
        ],
        "multi_part": [
            r"(\?.*\?)",  # Multiple questions
            r"(birinci.*ikinci|first.*second)",
            r"(\d+\.\s)",  # Numbered items
        ],
    }
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """Sorguyu analiz et"""
        query_lower = query.lower()
        
        # Soru türü
        question_type = "general"
        for qtype, patterns in self.QUESTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    question_type = qtype
                    break
        
        # Karmaşıklık
        complexity = "simple"
        for level, patterns in self.COMPLEXITY_INDICATORS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    complexity = level
                    break
        
        # Kelime sayısı
        word_count = len(query.split())
        
        # Anahtar kelimeler
        keywords = self._extract_keywords(query)
        
        # Önerilecek dönüşüm türleri
        recommended_transforms = self._recommend_transforms(
            question_type, complexity, word_count
        )
        
        return {
            "question_type": question_type,
            "complexity": complexity,
            "word_count": word_count,
            "keywords": keywords,
            "recommended_transforms": recommended_transforms,
            "needs_decomposition": complexity in ["high", "multi_part"],
            "needs_expansion": word_count < 4,
        }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Anahtar kelimeleri çıkar"""
        # Stop words
        stop_words = {
            "bir", "ve", "veya", "ile", "için", "bu", "şu", "o",
            "ne", "nasıl", "neden", "kim", "nerede",
            "the", "a", "an", "is", "are", "was", "were", "be",
            "to", "of", "and", "or", "in", "on", "at", "for",
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:10]
    
    def _recommend_transforms(
        self,
        question_type: str,
        complexity: str,
        word_count: int
    ) -> List[QueryTransformationType]:
        """Önerilecek dönüşümleri belirle"""
        transforms = []
        
        # HyDE: Factual ve definitional sorular için
        if question_type in ["factual", "definitional", "explanatory"]:
            transforms.append(QueryTransformationType.HYDE)
        
        # Decomposition: Karmaşık sorular için
        if complexity in ["high", "multi_part"]:
            transforms.append(QueryTransformationType.DECOMPOSITION)
        
        # Expansion: Kısa sorgular için
        if word_count < 4:
            transforms.append(QueryTransformationType.EXPANSION)
        
        # Step-back: Explanatory ve comparative için
        if question_type in ["explanatory", "comparative"]:
            transforms.append(QueryTransformationType.STEP_BACK)
        
        # Multi-query: Her zaman faydalı
        transforms.append(QueryTransformationType.MULTI_QUERY)
        
        return transforms


class HyDEGenerator:
    """
    HyDE (Hypothetical Document Embeddings) Generator
    
    Sorgudan varsayımsal döküman oluşturur ve bu dökümanın
    embedding'i ile arama yapar. Bu, sorgu-döküman uyumsuzluğunu azaltır.
    """
    
    # HyDE prompt templates
    TEMPLATES = {
        "general": """Generate a detailed paragraph that would answer the following query. 
Write as if it's from a high-quality reference document.

Query: {query}

Hypothetical Document:""",

        "technical": """Generate a technical documentation excerpt that explains the following:

Query: {query}

```
Technical Documentation:""",

        "academic": """Generate an academic paper excerpt that addresses the following research question:

Query: {query}

Abstract: This paper examines""",

        "factual": """Generate a Wikipedia-style paragraph that provides factual information about:

Query: {query}

Encyclopedia Entry:""",

        "turkish": """Aşağıdaki soruyu cevaplayan detaylı bir paragraf oluştur.
Yüksek kaliteli bir referans dökümanından alınmış gibi yaz.

Soru: {query}

Varsayımsal Döküman:""",
    }
    
    def __init__(self, llm_client=None, embedding_func=None):
        """
        Args:
            llm_client: LLM client (ollama, openai, etc.)
            embedding_func: Embedding function (optional)
        """
        self.llm_client = llm_client
        self.embedding_func = embedding_func
        self.analyzer = QueryAnalyzer()
        self._cache: Dict[str, HyDEResult] = {}
        
        # Try to get default embedding function
        if self.embedding_func is None:
            self.embedding_func = self._get_default_embedding_func()
    
    def _get_default_embedding_func(self):
        """Get default embedding function from vector store"""
        try:
            from rag.unified_orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
            if orchestrator and hasattr(orchestrator, 'vector_store'):
                vs = orchestrator.vector_store
                if hasattr(vs, 'embed_text'):
                    return vs.embed_text
        except Exception:
            pass
        return None
    
    async def generate(
        self,
        query: str,
        template_type: str = "auto",
        use_cache: bool = True,
        generate_embedding: bool = True,
    ) -> HyDEResult:
        """
        HyDE döküman oluştur.
        
        Args:
            query: Orijinal sorgu
            template_type: Template türü (auto, general, technical, academic, factual)
            use_cache: Cache kullan
            generate_embedding: Embedding üret
            
        Returns:
            HyDEResult
        """
        import time
        start_time = time.time()
        
        # Cache check
        cache_key = hashlib.md5(f"{query}:{template_type}".encode()).hexdigest()
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Analyze query
        analysis = self.analyzer.analyze(query)
        
        # Select template
        if template_type == "auto":
            template_type = self._select_template(query, analysis)
        
        template = self.TEMPLATES.get(template_type, self.TEMPLATES["general"])
        prompt = template.format(query=query)
        
        # Generate hypothetical document
        hypothetical_doc = await self._generate_document(prompt)
        
        # Generate embedding for hypothetical document
        embedding = None
        if generate_embedding and hypothetical_doc:
            embedding = await self._generate_embedding(hypothetical_doc)
        
        # Generate additional retrieval queries
        retrieval_queries = self._generate_retrieval_queries(query, hypothetical_doc)
        
        generation_time = int((time.time() - start_time) * 1000)
        
        result = HyDEResult(
            original_query=query,
            hypothetical_document=hypothetical_doc,
            document_embedding=embedding,
            retrieval_queries=retrieval_queries,
            generation_time_ms=generation_time,
        )
        
        # Cache
        if use_cache:
            self._cache[cache_key] = result
        
        return result
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Embedding üret"""
        # Check cache first
        if CACHE_ENABLED:
            global _embedding_cache
            if _embedding_cache is None:
                _embedding_cache = get_embedding_cache()
            
            cached = _embedding_cache.get_embedding(text, "hyde")
            if cached is not None:
                return cached
        
        embedding = None
        
        # Try embedding function
        if self.embedding_func:
            try:
                if asyncio.iscoroutinefunction(self.embedding_func):
                    embedding = await self.embedding_func(text)
                else:
                    embedding = self.embedding_func(text)
            except Exception as e:
                logger.warning(f"Embedding function failed: {e}")
        
        # Fallback: Use Ollama embedding
        if embedding is None:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "http://localhost:11434/api/embeddings",
                        json={
                            "model": "nomic-embed-text",
                            "prompt": text[:2000]  # Limit text length
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        embedding = data.get("embedding")
            except Exception as e:
                logger.warning(f"Ollama embedding failed: {e}")
        
        # Cache embedding
        if embedding and CACHE_ENABLED:
            _embedding_cache.set_embedding(text, embedding, "hyde")
        
        return embedding
    
    def _select_template(self, query: str, analysis: Dict) -> str:
        """Otomatik template seçimi"""
        # Turkish detection
        tr_chars = set('çğıöşüÇĞİÖŞÜ')
        if any(c in query for c in tr_chars):
            return "turkish"
        
        question_type = analysis.get("question_type", "general")
        
        if question_type == "factual":
            return "factual"
        elif question_type in ["procedural", "explanatory"]:
            keywords = analysis.get("keywords", [])
            tech_words = {"code", "api", "function", "error", "python", "java"}
            if any(k in tech_words for k in keywords):
                return "technical"
            return "general"
        elif question_type == "definitional":
            return "factual"
        
        return "general"
    
    async def _generate_document(self, prompt: str) -> str:
        """LLM ile döküman oluştur"""
        if self.llm_client:
            try:
                # Use provided LLM client
                response = await self.llm_client.generate(prompt, max_tokens=500)
                return response
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}")
        
        # Fallback: Use local Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 300,
                            "temperature": 0.7,
                        }
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
        
        # Ultimate fallback: Return query-based document
        return f"This document discusses {prompt.split('Query:')[-1].strip().split(chr(10))[0]}. It provides comprehensive information about the topic, including key concepts, definitions, and relevant details."
    
    def _generate_retrieval_queries(
        self,
        original_query: str,
        hypothetical_doc: str
    ) -> List[str]:
        """Retrieval için ek sorgular oluştur"""
        queries = [original_query]
        
        # Extract key phrases from hypothetical doc
        sentences = hypothetical_doc.split('.')[:3]
        for sent in sentences:
            if len(sent.strip()) > 20:
                # First 50 chars as query
                queries.append(sent.strip()[:50])
        
        return queries[:4]


class QueryTransformer:
    """
    Advanced Query Transformation
    
    Sorguları çeşitli tekniklerle dönüştürür:
    - HyDE
    - Query Expansion
    - Query Decomposition
    - Step-Back Prompting
    - Multi-Query Generation
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.hyde = HyDEGenerator(llm_client)
        self.analyzer = QueryAnalyzer()
    
    async def transform(
        self,
        query: str,
        transformation_type: QueryTransformationType = QueryTransformationType.HYDE,
        auto_select: bool = False,
    ) -> TransformedQuery:
        """
        Sorguyu dönüştür.
        
        Args:
            query: Orijinal sorgu
            transformation_type: Dönüşüm türü
            auto_select: Otomatik dönüşüm seçimi
            
        Returns:
            TransformedQuery
        """
        # Auto-select best transformation
        if auto_select:
            analysis = self.analyzer.analyze(query)
            recommended = analysis.get("recommended_transforms", [])
            if recommended:
                transformation_type = recommended[0]
        
        if transformation_type == QueryTransformationType.HYDE:
            return await self._transform_hyde(query)
        elif transformation_type == QueryTransformationType.EXPANSION:
            return await self._transform_expansion(query)
        elif transformation_type == QueryTransformationType.DECOMPOSITION:
            return await self._transform_decomposition(query)
        elif transformation_type == QueryTransformationType.STEP_BACK:
            return await self._transform_step_back(query)
        elif transformation_type == QueryTransformationType.MULTI_QUERY:
            return await self._transform_multi_query(query)
        elif transformation_type == QueryTransformationType.REWRITE:
            return await self._transform_rewrite(query)
        else:
            return TransformedQuery(
                original_query=query,
                transformed_queries=[query],
                transformation_type=transformation_type,
            )
    
    async def transform_all(self, query: str) -> Dict[str, TransformedQuery]:
        """Tüm dönüşümleri uygula"""
        analysis = self.analyzer.analyze(query)
        recommended = analysis.get("recommended_transforms", [])
        
        results = {}
        for transform_type in recommended[:3]:  # Max 3 transforms
            try:
                result = await self.transform(query, transform_type)
                results[transform_type.value] = result
            except Exception as e:
                logger.warning(f"Transform {transform_type.value} failed: {e}")
        
        return results
    
    async def _transform_hyde(self, query: str) -> TransformedQuery:
        """HyDE dönüşümü"""
        hyde_result = await self.hyde.generate(query)
        
        return TransformedQuery(
            original_query=query,
            transformed_queries=hyde_result.retrieval_queries,
            transformation_type=QueryTransformationType.HYDE,
            hypothetical_document=hyde_result.hypothetical_document,
            metadata={"generation_time_ms": hyde_result.generation_time_ms},
        )
    
    async def _transform_expansion(self, query: str) -> TransformedQuery:
        """Sorgu genişletme"""
        # Generate expanded queries
        expanded = await self._llm_expand_query(query)
        
        return TransformedQuery(
            original_query=query,
            transformed_queries=expanded,
            transformation_type=QueryTransformationType.EXPANSION,
            expanded_terms=self._extract_new_terms(query, expanded),
        )
    
    async def _transform_decomposition(self, query: str) -> TransformedQuery:
        """Sorguyu alt sorulara ayır"""
        sub_questions = await self._llm_decompose_query(query)
        
        return TransformedQuery(
            original_query=query,
            transformed_queries=sub_questions,
            transformation_type=QueryTransformationType.DECOMPOSITION,
            sub_questions=sub_questions,
        )
    
    async def _transform_step_back(self, query: str) -> TransformedQuery:
        """Step-back prompting - soyutlama"""
        step_back_query = await self._llm_step_back(query)
        
        return TransformedQuery(
            original_query=query,
            transformed_queries=[step_back_query, query],
            transformation_type=QueryTransformationType.STEP_BACK,
        )
    
    async def _transform_multi_query(self, query: str) -> TransformedQuery:
        """Çoklu sorgu varyantları"""
        variants = self._generate_query_variants(query)
        
        return TransformedQuery(
            original_query=query,
            transformed_queries=variants,
            transformation_type=QueryTransformationType.MULTI_QUERY,
        )
    
    async def _transform_rewrite(self, query: str) -> TransformedQuery:
        """Sorgu yeniden yazma"""
        rewritten = await self._llm_rewrite_query(query)
        
        return TransformedQuery(
            original_query=query,
            transformed_queries=[rewritten],
            transformation_type=QueryTransformationType.REWRITE,
        )
    
    # ============ LLM HELPERS ============
    
    async def _llm_expand_query(self, query: str) -> List[str]:
        """LLM ile sorgu genişlet"""
        prompt = f"""Expand the following search query with synonyms and related terms.
Generate 3 alternative search queries.

Original query: {query}

Alternative queries (one per line):"""
        
        response = await self._call_llm(prompt)
        queries = [q.strip() for q in response.split('\n') if q.strip()]
        return [query] + queries[:3]
    
    async def _llm_decompose_query(self, query: str) -> List[str]:
        """LLM ile sorguyu parçala"""
        prompt = f"""Break down this complex question into simpler sub-questions.
Generate 2-4 sub-questions that together answer the main question.

Main question: {query}

Sub-questions (one per line):"""
        
        response = await self._call_llm(prompt)
        sub_questions = [q.strip() for q in response.split('\n') if q.strip()]
        return sub_questions[:4] if sub_questions else [query]
    
    async def _llm_step_back(self, query: str) -> str:
        """LLM ile step-back query"""
        prompt = f"""Generate a more general/abstract version of this question 
that would help understand the broader context.

Specific question: {query}

General question:"""
        
        response = await self._call_llm(prompt)
        return response.strip() or query
    
    async def _llm_rewrite_query(self, query: str) -> str:
        """LLM ile sorgu yeniden yaz"""
        prompt = f"""Rewrite this search query to be clearer and more effective for search.
Keep the same intent but improve clarity.

Original: {query}

Rewritten:"""
        
        response = await self._call_llm(prompt)
        return response.strip() or query
    
    async def _call_llm(self, prompt: str) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=200)
            except Exception:
                pass
        
        # Fallback to Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 150, "temperature": 0.5}
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception:
            pass
        
        return ""
    
    def _generate_query_variants(self, query: str) -> List[str]:
        """Basit sorgu varyantları (LLM olmadan)"""
        variants = [query]
        
        # Add question prefix if not present
        question_words = ["ne", "nasıl", "neden", "kim", "nerede", "what", "how", "why", "who", "where"]
        has_question = any(query.lower().startswith(w) for w in question_words)
        
        if not has_question:
            variants.append(f"nedir {query}")
            variants.append(f"what is {query}")
        
        # Remove question marks and reformat
        clean_query = query.rstrip('?').strip()
        if clean_query != query:
            variants.append(clean_query)
        
        # Keywords only
        keywords = self.analyzer._extract_keywords(query)
        if len(keywords) >= 2:
            variants.append(" ".join(keywords))
        
        return variants[:5]
    
    def _extract_new_terms(self, original: str, expanded: List[str]) -> List[str]:
        """Genişletmeden eklenen yeni terimleri çıkar"""
        original_words = set(original.lower().split())
        new_terms = set()
        
        for query in expanded:
            for word in query.lower().split():
                if word not in original_words and len(word) > 2:
                    new_terms.add(word)
        
        return list(new_terms)[:10]


class AdvancedRetriever:
    """
    Advanced RAG Retriever
    
    HyDE ve Query Transformation ile gelişmiş retrieval.
    """
    
    def __init__(
        self,
        vector_store,
        embedding_func,
        llm_client=None,
    ):
        self.vector_store = vector_store
        self.embedding_func = embedding_func
        self.transformer = QueryTransformer(llm_client)
        self.hyde = HyDEGenerator(llm_client)
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_hyde: bool = True,
        use_multi_query: bool = True,
        rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Gelişmiş retrieval.
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek sonuç sayısı
            use_hyde: HyDE kullan
            use_multi_query: Multi-query kullan
            rerank: Sonuçları yeniden sırala
            
        Returns:
            Sonuç listesi
        """
        all_results = []
        
        # 1. Standard query retrieval
        standard_results = await self._retrieve_standard(query, top_k * 2)
        all_results.extend(standard_results)
        
        # 2. HyDE retrieval
        if use_hyde:
            hyde_results = await self._retrieve_with_hyde(query, top_k)
            all_results.extend(hyde_results)
        
        # 3. Multi-query retrieval
        if use_multi_query:
            multi_results = await self._retrieve_multi_query(query, top_k)
            all_results.extend(multi_results)
        
        # 4. Deduplicate
        unique_results = self._deduplicate(all_results)
        
        # 5. Rerank
        if rerank:
            unique_results = await self._rerank(query, unique_results)
        
        return unique_results[:top_k]
    
    async def _retrieve_standard(self, query: str, top_k: int) -> List[Dict]:
        """Standart retrieval"""
        try:
            results = self.vector_store.search_with_scores(
                query=query,
                n_results=top_k,
            )
            return results
        except Exception as e:
            logger.warning(f"Standard retrieval error: {e}")
            return []
    
    async def _retrieve_with_hyde(self, query: str, top_k: int) -> List[Dict]:
        """HyDE ile retrieval"""
        try:
            # Generate hypothetical document
            hyde_result = await self.hyde.generate(query)
            
            # Embed hypothetical document
            hyde_embedding = self.embedding_func([hyde_result.hypothetical_document])[0]
            
            # Search with hypothetical document embedding
            results = self.vector_store.search_by_embedding(
                embedding=hyde_embedding,
                n_results=top_k,
            )
            
            # Mark as HyDE results
            for r in results:
                r["retrieval_method"] = "hyde"
            
            return results
        except Exception as e:
            logger.warning(f"HyDE retrieval error: {e}")
            return []
    
    async def _retrieve_multi_query(self, query: str, top_k: int) -> List[Dict]:
        """Multi-query retrieval"""
        try:
            # Transform query
            transformed = await self.transformer.transform(
                query,
                QueryTransformationType.MULTI_QUERY
            )
            
            all_results = []
            for variant_query in transformed.transformed_queries[:3]:
                results = self.vector_store.search_with_scores(
                    query=variant_query,
                    n_results=top_k // 2,
                )
                for r in results:
                    r["retrieval_method"] = "multi_query"
                    r["variant_query"] = variant_query
                all_results.extend(results)
            
            return all_results
        except Exception as e:
            logger.warning(f"Multi-query retrieval error: {e}")
            return []
    
    def _deduplicate(self, results: List[Dict]) -> List[Dict]:
        """Sonuçları deduplicate et"""
        seen = set()
        unique = []
        
        for r in results:
            content = r.get("document", "")[:200]
            content_hash = hash(content)
            
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(r)
        
        return unique
    
    async def _rerank(self, query: str, results: List[Dict]) -> List[Dict]:
        """Sonuçları yeniden sırala"""
        # Simple scoring based on relevance
        for r in results:
            score = r.get("score", 0.5)
            
            # Boost HyDE results slightly
            if r.get("retrieval_method") == "hyde":
                score *= 1.1
            
            # Boost if title contains query words
            title = r.get("metadata", {}).get("title", "")
            query_words = set(query.lower().split())
            title_words = set(title.lower().split())
            overlap = len(query_words & title_words)
            score += overlap * 0.05
            
            r["final_score"] = min(1.0, score)
        
        # Sort by final score
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return results


# ============ CONVENIENCE FUNCTIONS ============

_transformer: Optional[QueryTransformer] = None
_hyde_generator: Optional[HyDEGenerator] = None

def get_query_transformer() -> QueryTransformer:
    global _transformer
    if _transformer is None:
        _transformer = QueryTransformer()
    return _transformer

def get_hyde_generator() -> HyDEGenerator:
    global _hyde_generator
    if _hyde_generator is None:
        _hyde_generator = HyDEGenerator()
    return _hyde_generator


async def transform_query(
    query: str,
    method: str = "auto"
) -> TransformedQuery:
    """Convenience function for query transformation"""
    transformer = get_query_transformer()
    
    if method == "auto":
        return await transformer.transform(query, auto_select=True)
    
    transform_type = QueryTransformationType[method.upper()]
    return await transformer.transform(query, transform_type)


async def generate_hyde_document(query: str) -> str:
    """Convenience function for HyDE document generation"""
    hyde = get_hyde_generator()
    result = await hyde.generate(query)
    return result.hypothetical_document


# ============ TEST ============

async def test_hyde():
    """Test HyDE"""
    print("Testing HyDE...")
    
    query = "Python'da decorator nasıl kullanılır?"
    
    hyde = HyDEGenerator()
    result = await hyde.generate(query)
    
    print(f"\nOriginal Query: {result.original_query}")
    print(f"Generation Time: {result.generation_time_ms}ms")
    print(f"\nHypothetical Document:\n{result.hypothetical_document[:500]}")
    print(f"\nRetrieval Queries: {result.retrieval_queries}")


async def test_transformer():
    """Test Query Transformer"""
    print("\nTesting Query Transformer...")
    
    query = "Python ve JavaScript arasındaki farklar nelerdir ve hangisi web geliştirme için daha uygun?"
    
    transformer = QueryTransformer()
    
    # Analyze
    analysis = transformer.analyzer.analyze(query)
    print(f"\nAnalysis: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    
    # Transform
    result = await transformer.transform(query, QueryTransformationType.DECOMPOSITION)
    print(f"\nDecomposition:")
    for sq in result.sub_questions:
        print(f"  - {sq}")


if __name__ == "__main__":
    asyncio.run(test_hyde())
    asyncio.run(test_transformer())
