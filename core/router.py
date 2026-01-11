"""
Semantic Router
===============

Endüstri standartlarında semantic routing sistemi.
Query'leri intent'e göre doğru handler'a yönlendirir.

Features:
- Embedding-based semantic similarity
- Intent classification
- Route prioritization
- Fallback handling
- Dynamic route registration
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import hashlib

from .logger import get_logger

logger = get_logger("router")


class RouteType(Enum):
    """Route türleri"""
    AGENT = "agent"
    TOOL = "tool"
    RAG = "rag"
    DIRECT = "direct"
    FALLBACK = "fallback"


@dataclass
class Route:
    """Routing tanımı"""
    name: str
    description: str
    route_type: RouteType
    handler: Optional[Callable] = None
    examples: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)  # Regex patterns
    priority: int = 50  # 0-100, higher = more priority
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime computed
    _embedding: Optional[List[float]] = field(default=None, repr=False)
    
    def matches_keyword(self, text: str) -> bool:
        """Keyword match kontrolü"""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.keywords)
    
    def matches_pattern(self, text: str) -> bool:
        """Regex pattern match kontrolü"""
        for pattern in self.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "route_type": self.route_type.value,
            "examples": self.examples,
            "keywords": self.keywords,
            "patterns": self.patterns,
            "priority": self.priority,
            "metadata": self.metadata
        }


@dataclass
class RouteMatch:
    """Route eşleşme sonucu"""
    route: Route
    score: float
    match_type: str  # "semantic", "keyword", "pattern", "fallback"
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "route_name": self.route.name,
            "route_type": self.route.route_type.value,
            "score": self.score,
            "match_type": self.match_type,
            "confidence": self.confidence
        }


class RouterStrategy(ABC):
    """Routing stratejisi base class"""
    
    @abstractmethod
    def route(
        self,
        query: str,
        routes: List[Route],
        **kwargs
    ) -> List[RouteMatch]:
        pass


class KeywordRouter(RouterStrategy):
    """Keyword tabanlı routing"""
    
    def route(
        self,
        query: str,
        routes: List[Route],
        **kwargs
    ) -> List[RouteMatch]:
        matches = []
        
        for route in routes:
            if route.matches_keyword(query):
                matches.append(RouteMatch(
                    route=route,
                    score=0.7 + (route.priority / 1000),
                    match_type="keyword",
                    confidence=0.7
                ))
            elif route.matches_pattern(query):
                matches.append(RouteMatch(
                    route=route,
                    score=0.8 + (route.priority / 1000),
                    match_type="pattern",
                    confidence=0.8
                ))
        
        return sorted(matches, key=lambda m: m.score, reverse=True)


class SemanticRouter(RouterStrategy):
    """Embedding tabanlı semantic routing"""
    
    def __init__(self, embedding_fn: Optional[Callable[[str], List[float]]] = None):
        self.embedding_fn = embedding_fn
        self._route_embeddings: Dict[str, List[float]] = {}
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Cosine similarity hesapla"""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _get_route_embedding(self, route: Route) -> Optional[List[float]]:
        """Route için embedding al veya oluştur"""
        if route.name in self._route_embeddings:
            return self._route_embeddings[route.name]
        
        if not self.embedding_fn:
            return None
        
        # Description ve examples'dan combined text oluştur
        texts = [route.description] + route.examples
        combined = " ".join(texts)
        
        embedding = self.embedding_fn(combined)
        self._route_embeddings[route.name] = embedding
        
        return embedding
    
    def route(
        self,
        query: str,
        routes: List[Route],
        threshold: float = 0.5,
        **kwargs
    ) -> List[RouteMatch]:
        if not self.embedding_fn:
            return []
        
        query_embedding = self.embedding_fn(query)
        matches = []
        
        for route in routes:
            route_embedding = self._get_route_embedding(route)
            
            if route_embedding:
                similarity = self._cosine_similarity(query_embedding, route_embedding)
                
                if similarity >= threshold:
                    # Priority ile birleştir
                    adjusted_score = similarity * 0.8 + (route.priority / 100) * 0.2
                    
                    matches.append(RouteMatch(
                        route=route,
                        score=adjusted_score,
                        match_type="semantic",
                        confidence=similarity
                    ))
        
        return sorted(matches, key=lambda m: m.score, reverse=True)


class HybridRouter(RouterStrategy):
    """Keyword + Semantic hybrid routing"""
    
    def __init__(
        self,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7
    ):
        self.keyword_router = KeywordRouter()
        self.semantic_router = SemanticRouter(embedding_fn)
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight
    
    def route(
        self,
        query: str,
        routes: List[Route],
        **kwargs
    ) -> List[RouteMatch]:
        # Her iki router'dan sonuç al
        keyword_matches = self.keyword_router.route(query, routes)
        semantic_matches = self.semantic_router.route(query, routes, **kwargs)
        
        # Sonuçları birleştir
        combined: Dict[str, RouteMatch] = {}
        
        for match in keyword_matches:
            combined[match.route.name] = RouteMatch(
                route=match.route,
                score=match.score * self.keyword_weight,
                match_type="keyword",
                confidence=match.confidence
            )
        
        for match in semantic_matches:
            if match.route.name in combined:
                # Mevcut match'e semantic score ekle
                existing = combined[match.route.name]
                combined[match.route.name] = RouteMatch(
                    route=match.route,
                    score=existing.score + match.score * self.semantic_weight,
                    match_type="hybrid",
                    confidence=max(existing.confidence, match.confidence)
                )
            else:
                combined[match.route.name] = RouteMatch(
                    route=match.route,
                    score=match.score * self.semantic_weight,
                    match_type="semantic",
                    confidence=match.confidence
                )
        
        return sorted(combined.values(), key=lambda m: m.score, reverse=True)


class SemanticRouterManager:
    """
    Semantic Router Manager
    
    Query'leri intent'e göre yönlendirir.
    """
    
    # Önceden tanımlı route'lar
    DEFAULT_ROUTES = [
        Route(
            name="rag_search",
            description="Dökümanlardan bilgi arama, belge sorgulama",
            route_type=RouteType.RAG,
            examples=[
                "İzin politikamız nedir?",
                "Şirket kuralları hakkında bilgi ver",
                "Dökümanlarda şunu ara",
                "Bu konuda ne yazıyor?"
            ],
            keywords=["döküman", "belge", "politika", "kural", "prosedür", "ara", "bul"],
            priority=70
        ),
        Route(
            name="analysis",
            description="Veri analizi, karşılaştırma, özet çıkarma",
            route_type=RouteType.AGENT,
            examples=[
                "Bu verileri analiz et",
                "Karşılaştırma yap",
                "Özet çıkar",
                "Trend analizi"
            ],
            keywords=["analiz", "karşılaştır", "özet", "trend", "rapor", "istatistik"],
            priority=60
        ),
        Route(
            name="writing",
            description="Email, rapor, döküman yazma",
            route_type=RouteType.AGENT,
            examples=[
                "Email yaz",
                "Rapor hazırla",
                "Döküman oluştur",
                "Mektup yaz"
            ],
            keywords=["yaz", "email", "rapor", "mektup", "döküman oluştur", "hazırla"],
            patterns=[r"(yaz|hazırla|oluştur)\s*(bir|bana)?"],
            priority=65
        ),
        Route(
            name="research",
            description="Araştırma, bilgi toplama",
            route_type=RouteType.AGENT,
            examples=[
                "Araştır",
                "Bilgi topla",
                "İnceleme yap"
            ],
            keywords=["araştır", "incele", "bilgi topla", "öğren"],
            priority=55
        ),
        Route(
            name="general_chat",
            description="Genel sohbet, basit sorular",
            route_type=RouteType.DIRECT,
            examples=[
                "Merhaba",
                "Nasılsın?",
                "Teşekkürler",
                "Yardım et"
            ],
            keywords=["merhaba", "selam", "nasıl", "teşekkür", "yardım"],
            priority=40
        ),
        Route(
            name="web_search",
            description="İnternet araması, güncel bilgi",
            route_type=RouteType.TOOL,
            examples=[
                "İnternette ara",
                "Web'de bul",
                "Güncel haber",
                "Online bilgi"
            ],
            keywords=["internet", "web", "online", "güncel", "haber", "ara"],
            priority=50
        ),
        Route(
            name="file_operation",
            description="Dosya işlemleri",
            route_type=RouteType.TOOL,
            examples=[
                "Dosya oluştur",
                "Dosyayı oku",
                "Kaydet"
            ],
            keywords=["dosya", "kaydet", "oku", "yükle", "indir"],
            priority=45
        ),
    ]
    
    def __init__(
        self,
        strategy: Optional[RouterStrategy] = None,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        fallback_route: Optional[Route] = None
    ):
        self.strategy = strategy or HybridRouter(embedding_fn)
        self.routes: List[Route] = []
        self.fallback = fallback_route or Route(
            name="fallback",
            description="Default fallback route",
            route_type=RouteType.FALLBACK,
            priority=0
        )
        
        self._handlers: Dict[str, Callable] = {}
        
        # Default route'ları ekle
        for route in self.DEFAULT_ROUTES:
            self.add_route(route)
    
    def add_route(self, route: Route):
        """Route ekle"""
        self.routes.append(route)
        logger.debug(f"Route added: {route.name}")
    
    def remove_route(self, route_name: str) -> bool:
        """Route kaldır"""
        original_count = len(self.routes)
        self.routes = [r for r in self.routes if r.name != route_name]
        return len(self.routes) < original_count
    
    def register_handler(self, route_name: str, handler: Callable):
        """Route handler kaydet"""
        self._handlers[route_name] = handler
        
        # Route'a da ekle
        for route in self.routes:
            if route.name == route_name:
                route.handler = handler
                break
    
    def route(
        self,
        query: str,
        top_k: int = 3,
        min_confidence: float = 0.3
    ) -> List[RouteMatch]:
        """
        Query'yi route et
        
        Returns:
            Top-k route matches
        """
        matches = self.strategy.route(query, self.routes)
        
        # Confidence filtresi
        matches = [m for m in matches if m.confidence >= min_confidence]
        
        # Top-k
        matches = matches[:top_k]
        
        # Eğer hiç match yoksa fallback
        if not matches:
            matches = [RouteMatch(
                route=self.fallback,
                score=0.0,
                match_type="fallback",
                confidence=0.0
            )]
        
        logger.info(f"Query routed: '{query[:50]}...' -> {matches[0].route.name}")
        
        return matches
    
    def get_best_route(self, query: str) -> RouteMatch:
        """En iyi route'u döndür"""
        return self.route(query, top_k=1)[0]
    
    async def execute(self, query: str, **kwargs) -> Any:
        """
        Query'yi route et ve handler'ı çalıştır
        """
        match = self.get_best_route(query)
        
        handler = match.route.handler or self._handlers.get(match.route.name)
        
        if handler:
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                return await handler(query, **kwargs)
            else:
                return handler(query, **kwargs)
        
        return {
            "route": match.route.name,
            "message": f"No handler for route: {match.route.name}",
            "query": query
        }
    
    def get_routes_summary(self) -> List[Dict]:
        """Route'ların özetini al"""
        return [route.to_dict() for route in self.routes]


# Global instance
semantic_router = SemanticRouterManager()


__all__ = [
    "SemanticRouterManager",
    "Route",
    "RouteMatch",
    "RouteType",
    "RouterStrategy",
    "KeywordRouter",
    "SemanticRouter",
    "HybridRouter",
    "semantic_router"
]
