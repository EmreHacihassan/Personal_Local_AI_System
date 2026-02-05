"""
🎯 Adaptive Threshold Engine
============================

Sorgu tipine ve içerik kalitesine göre dinamik RAG eşik değeri.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import statistics

logger = logging.getLogger(__name__)


class QueryDifficulty(Enum):
    """Sorgu zorluk seviyesi."""
    SIMPLE = "simple"  # Düşük threshold
    MODERATE = "moderate"  # Orta threshold
    COMPLEX = "complex"  # Yüksek threshold
    EXPERT = "expert"  # Çok yüksek threshold


@dataclass
class ThresholdConfig:
    """Threshold konfigürasyonu."""
    base_threshold: float = 0.3
    min_threshold: float = 0.15
    max_threshold: float = 0.7
    
    # Dinamik ayarlama faktörleri
    query_length_factor: float = 0.02
    technical_boost: float = 0.1
    context_quality_factor: float = 0.05


@dataclass
class ThresholdResult:
    """Threshold hesaplama sonucu."""
    final_threshold: float
    adjustments: Dict[str, float]
    reasoning: str
    confidence: float


class AdaptiveThresholdEngine:
    """
    Dinamik RAG threshold motoru.
    
    Sorgu ve sonuçlara göre optimal threshold belirler.
    """
    
    def __init__(self, config: Optional[ThresholdConfig] = None):
        self.config = config or ThresholdConfig()
        
        # Teknik terimler
        self.technical_terms = {
            "api", "docker", "kubernetes", "microservice", "database",
            "algorithm", "machine learning", "neural network", "rest",
            "graphql", "authentication", "encryption", "ssl", "tcp",
            "http", "websocket", "redis", "mongodb", "postgresql",
            "react", "fastapi", "django", "pytorch", "tensorflow",
            "git", "cicd", "devops", "aws", "azure", "cloud",
            "python", "javascript", "typescript", "rust", "golang"
        }
        
        # Domain kategorileri ve threshold ayarları
        self.domain_thresholds = {
            "coding": 0.35,
            "technical": 0.4,
            "scientific": 0.45,
            "general": 0.25,
            "conversational": 0.2
        }
    
    def calculate_threshold(
        self,
        query: str,
        initial_results: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ThresholdResult:
        """
        Optimal threshold hesapla.
        
        Args:
            query: Kullanıcı sorgusu
            initial_results: İlk RAG sonuçları (opsiyonel)
            context: Ek bağlam bilgisi
            
        Returns:
            ThresholdResult: Hesaplanan threshold ve detaylar
        """
        adjustments = {}
        
        # 1. Temel threshold
        base = self.config.base_threshold
        
        # 2. Sorgu uzunluğu ayarı
        query_words = len(query.split())
        length_adj = 0.0
        if query_words < 5:
            length_adj = -0.05  # Kısa sorgular için düşür
        elif query_words > 20:
            length_adj = 0.08  # Uzun sorgular için artır
        elif query_words > 10:
            length_adj = 0.04
        adjustments["query_length"] = length_adj
        
        # 3. Teknik içerik analizi
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        technical_count = len(query_terms & self.technical_terms)
        technical_adj = min(technical_count * 0.03, 0.15)
        adjustments["technical_terms"] = technical_adj
        
        # 4. Domain tespiti
        domain = self._detect_domain(query_lower)
        domain_adj = self.domain_thresholds.get(domain, 0.3) - base
        adjustments["domain"] = domain_adj
        
        # 5. Soru tipi analizi
        question_adj = 0.0
        if "?" in query:
            if any(w in query_lower for w in ["what is", "ne", "nedir"]):
                question_adj = -0.05  # Tanım soruları
            elif any(w in query_lower for w in ["how", "nasıl", "explain"]):
                question_adj = 0.03  # Açıklama soruları
            elif any(w in query_lower for w in ["why", "neden", "compare"]):
                question_adj = 0.08  # Analitik sorular
        adjustments["question_type"] = question_adj
        
        # 6. İlk sonuçlara göre adaptasyon
        if initial_results:
            results_adj = self._analyze_initial_results(initial_results)
            adjustments["results_analysis"] = results_adj
        
        # 7. Final threshold hesaplama
        total_adjustment = sum(adjustments.values())
        final_threshold = max(
            self.config.min_threshold,
            min(self.config.max_threshold, base + total_adjustment)
        )
        
        # Reasoning oluştur
        reasoning = self._generate_reasoning(
            query, domain, adjustments, final_threshold
        )
        
        # Confidence hesapla
        confidence = self._calculate_confidence(adjustments)
        
        return ThresholdResult(
            final_threshold=round(final_threshold, 3),
            adjustments=adjustments,
            reasoning=reasoning,
            confidence=confidence
        )
    
    def _detect_domain(self, query_lower: str) -> str:
        """Domain tespit et."""
        coding_indicators = {
            "code", "function", "class", "variable", "debug",
            "error", "bug", "implement", "syntax", "compile"
        }
        technical_indicators = {
            "system", "architecture", "infrastructure", "deploy",
            "config", "setup", "install", "network", "server"
        }
        scientific_indicators = {
            "research", "study", "experiment", "hypothesis",
            "theory", "analysis", "data", "statistics"
        }
        conversational_indicators = {
            "hello", "hi", "thanks", "bye", "please", "help"
        }
        
        query_words = set(query_lower.split())
        
        if query_words & coding_indicators:
            return "coding"
        elif query_words & technical_indicators:
            return "technical"
        elif query_words & scientific_indicators:
            return "scientific"
        elif query_words & conversational_indicators:
            return "conversational"
        else:
            return "general"
    
    def _analyze_initial_results(
        self,
        results: List[Dict[str, Any]]
    ) -> float:
        """İlk sonuçları analiz et ve threshold ayarı öner."""
        if not results:
            return 0.0
        
        # Similarity skorlarını çek
        scores = []
        for r in results:
            score = r.get("similarity", r.get("score", 0))
            if score:
                scores.append(float(score))
        
        if not scores:
            return 0.0
        
        avg_score = statistics.mean(scores)
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # Yüksek averajla düşük std = threshold artırılabilir
        if avg_score > 0.7 and score_std < 0.15:
            return 0.1
        # Düşük averajla yüksek std = threshold düşürülmeli
        elif avg_score < 0.4 and score_std > 0.2:
            return -0.1
        # Çok düşük averaj = muhtemelen threshold çok yüksek
        elif avg_score < 0.25:
            return -0.15
        
        return 0.0
    
    def _generate_reasoning(
        self,
        query: str,
        domain: str,
        adjustments: Dict[str, float],
        final: float
    ) -> str:
        """Threshold kararı için reasoning oluştur."""
        parts = [f"Domain: {domain}"]
        
        significant = [
            (k, v) for k, v in adjustments.items()
            if abs(v) >= 0.03
        ]
        
        for key, value in significant:
            direction = "artırıldı" if value > 0 else "düşürüldü"
            parts.append(f"{key}: {direction} ({value:+.2f})")
        
        return f"Threshold {final:.3f}: " + ", ".join(parts)
    
    def _calculate_confidence(self, adjustments: Dict[str, float]) -> float:
        """Threshold kararının güven skorunu hesapla."""
        # Tutarlı ayarlamalar = yüksek güven
        positive = sum(1 for v in adjustments.values() if v > 0)
        negative = sum(1 for v in adjustments.values() if v < 0)
        
        if positive == 0 or negative == 0:
            return 0.9  # Tek yönlü = yüksek güven
        
        # Karışık sinyaller
        ratio = min(positive, negative) / max(positive, negative)
        return 0.7 - (ratio * 0.2)
    
    def suggest_retrieval_count(
        self,
        threshold: float,
        desired_minimum: int = 3
    ) -> int:
        """Threshold'a göre kaç sonuç alınması gerektiğini öner."""
        # Yüksek threshold = daha fazla sonuç al (filtreleme sert)
        if threshold > 0.5:
            return max(desired_minimum * 3, 15)
        elif threshold > 0.35:
            return max(desired_minimum * 2, 10)
        else:
            return max(desired_minimum, 5)


class AdaptiveRetriever:
    """
    Adaptive threshold ile RAG retrieval.
    
    Threshold motorunu kullanarak optimal sonuçlar döndürür.
    """
    
    def __init__(
        self,
        threshold_engine: Optional[AdaptiveThresholdEngine] = None
    ):
        self.threshold_engine = threshold_engine or AdaptiveThresholdEngine()
    
    async def retrieve(
        self,
        query: str,
        collection: Any,  # ChromaDB collection
        initial_k: int = 20,
        min_results: int = 3,
        max_results: int = 10
    ) -> Tuple[List[Dict[str, Any]], ThresholdResult]:
        """
        Adaptive threshold ile doküman al.
        
        Args:
            query: Sorgu
            collection: ChromaDB collection
            initial_k: İlk çekilen sonuç sayısı
            min_results: Minimum sonuç
            max_results: Maksimum sonuç
            
        Returns:
            Filtrelenmiş sonuçlar ve threshold bilgisi
        """
        # 1. İlk sonuçları al
        try:
            results = collection.query(
                query_texts=[query],
                n_results=initial_k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return [], ThresholdResult(
                final_threshold=0.3,
                adjustments={},
                reasoning="Error during retrieval",
                confidence=0.0
            )
        
        # Sonuçları format et
        formatted_results = self._format_results(results)
        
        # 2. Threshold hesapla
        threshold_result = self.threshold_engine.calculate_threshold(
            query=query,
            initial_results=formatted_results
        )
        
        # 3. Threshold'a göre filtrele
        filtered = [
            r for r in formatted_results
            if r.get("similarity", 0) >= threshold_result.final_threshold
        ]
        
        # 4. Min/max sınırları uygula
        if len(filtered) < min_results and formatted_results:
            # Minimum sağlanamıyorsa en iyi sonuçları al
            filtered = sorted(
                formatted_results,
                key=lambda x: x.get("similarity", 0),
                reverse=True
            )[:min_results]
        
        filtered = filtered[:max_results]
        
        logger.info(
            f"Adaptive retrieval: {len(formatted_results)} -> {len(filtered)} "
            f"(threshold: {threshold_result.final_threshold})"
        )
        
        return filtered, threshold_result
    
    def _format_results(self, raw_results: Dict) -> List[Dict[str, Any]]:
        """ChromaDB sonuçlarını formatla."""
        formatted = []
        
        if not raw_results.get("documents"):
            return formatted
        
        documents = raw_results["documents"][0]
        distances = raw_results.get("distances", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        
        for i, doc in enumerate(documents):
            # Distance'ı similarity'ye çevir (cosine distance için)
            distance = distances[i] if i < len(distances) else 1.0
            similarity = 1 - (distance / 2)  # [-1,1] -> [0,1]
            
            formatted.append({
                "content": doc,
                "similarity": similarity,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "rank": i + 1
            })
        
        return formatted


# Singleton instance
adaptive_threshold = AdaptiveThresholdEngine()
adaptive_retriever = AdaptiveRetriever(adaptive_threshold)
