"""
Enterprise AI Assistant - RAG Evaluation Module
RAG performans değerlendirme

Retrieval quality, answer faithfulness, context relevance.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
from collections import Counter


@dataclass
class EvaluationResult:
    """Değerlendirme sonucu."""
    metric: str
    score: float  # 0.0 - 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=datetime.now)


@dataclass
class RAGEvaluationReport:
    """RAG değerlendirme raporu."""
    query: str
    retrieved_docs: List[str]
    generated_answer: str
    ground_truth: Optional[str] = None
    metrics: Dict[str, EvaluationResult] = field(default_factory=dict)
    overall_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "retrieved_docs_count": len(self.retrieved_docs),
            "answer_length": len(self.generated_answer),
            "has_ground_truth": self.ground_truth is not None,
            "metrics": {k: {"score": v.score, "details": v.details} for k, v in self.metrics.items()},
            "overall_score": self.overall_score,
        }


class RAGEvaluator:
    """
    RAG Değerlendirici.
    
    Metrics:
    - Context Relevance: Getirilen dökümanların sorguyla ilgisi
    - Context Recall: Cevap için gerekli bilgilerin ne kadarı getirildi
    - Faithfulness: Cevabın kaynaklara sadakati
    - Answer Relevance: Cevabın soruyla ilgisi
    """
    
    def __init__(self, llm_manager=None):
        """Evaluator başlat."""
        self._llm = llm_manager
    
    def _lazy_load(self):
        """Lazy loading."""
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def evaluate_context_relevance(
        self,
        query: str,
        contexts: List[str],
    ) -> EvaluationResult:
        """
        Context Relevance: Her context'in sorguyla ilgisini değerlendir.
        
        Args:
            query: Kullanıcı sorgusu
            contexts: Getirilen dökümanlar
            
        Returns:
            Değerlendirme sonucu
        """
        if not contexts:
            return EvaluationResult(
                metric="context_relevance",
                score=0.0,
                details={"reason": "No contexts provided"},
            )
        
        self._lazy_load()
        
        scores = []
        
        for i, ctx in enumerate(contexts[:5]):
            prompt = f"""Aşağıdaki context'in sorguyla ne kadar ilgili olduğunu 0-10 arası puanla.
Sadece sayı yaz.

Sorgu: {query}

Context: {ctx[:500]}

Puan (0-10):"""
            
            try:
                response = self._llm.generate(prompt, max_tokens=10)
                score = float(re.search(r'\d+', response).group()) / 10.0
                scores.append(min(max(score, 0.0), 1.0))
            except Exception:
                scores.append(0.5)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return EvaluationResult(
            metric="context_relevance",
            score=avg_score,
            details={
                "individual_scores": scores,
                "contexts_evaluated": len(scores),
            },
        )
    
    def evaluate_faithfulness(
        self,
        answer: str,
        contexts: List[str],
    ) -> EvaluationResult:
        """
        Faithfulness: Cevabın kaynaklara sadakatini değerlendir.
        
        Cevaptaki her claim'in context'te desteklenip desteklenmediğini kontrol eder.
        
        Args:
            answer: Üretilen cevap
            contexts: Kaynak dökümanlar
            
        Returns:
            Değerlendirme sonucu
        """
        if not contexts or not answer:
            return EvaluationResult(
                metric="faithfulness",
                score=0.0,
                details={"reason": "Missing answer or contexts"},
            )
        
        self._lazy_load()
        
        combined_context = "\n\n".join(contexts[:5])
        
        prompt = f"""Aşağıdaki cevabın verilen context'e ne kadar sadık olduğunu değerlendir.
Cevaptaki bilgilerin context'te desteklenip desteklenmediğini kontrol et.

Context:
{combined_context[:2000]}

Cevap:
{answer[:1000]}

1. Cevaptaki her önemli claim context'te var mı?
2. Cevap context dışında bilgi ekliyor mu (hallucination)?

0-10 arası puan ver (10 = tamamen sadık, 0 = tamamen uydurma):
Puan:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=50)
            score = float(re.search(r'\d+', response).group()) / 10.0
            score = min(max(score, 0.0), 1.0)
        except Exception:
            score = 0.5
        
        return EvaluationResult(
            metric="faithfulness",
            score=score,
            details={
                "answer_length": len(answer),
                "context_length": len(combined_context),
            },
        )
    
    def evaluate_answer_relevance(
        self,
        query: str,
        answer: str,
    ) -> EvaluationResult:
        """
        Answer Relevance: Cevabın soruyla ilgisini değerlendir.
        
        Args:
            query: Kullanıcı sorgusu
            answer: Üretilen cevap
            
        Returns:
            Değerlendirme sonucu
        """
        if not query or not answer:
            return EvaluationResult(
                metric="answer_relevance",
                score=0.0,
                details={"reason": "Missing query or answer"},
            )
        
        self._lazy_load()
        
        prompt = f"""Aşağıdaki cevabın soruyu ne kadar iyi yanıtladığını değerlendir.

Soru: {query}

Cevap: {answer[:1000]}

Değerlendirme kriterleri:
- Cevap soruyu doğrudan yanıtlıyor mu?
- Cevap konudan sapıyor mu?
- Cevap yeterince detaylı mı?

0-10 arası puan ver:
Puan:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=20)
            score = float(re.search(r'\d+', response).group()) / 10.0
            score = min(max(score, 0.0), 1.0)
        except Exception:
            score = 0.5
        
        return EvaluationResult(
            metric="answer_relevance",
            score=score,
            details={"query_length": len(query), "answer_length": len(answer)},
        )
    
    def evaluate_lexical_overlap(
        self,
        answer: str,
        contexts: List[str],
    ) -> EvaluationResult:
        """
        Lexical Overlap: Kelime düzeyinde örtüşme (basit metrik).
        
        Args:
            answer: Cevap
            contexts: Contexts
            
        Returns:
            Değerlendirme sonucu
        """
        if not answer or not contexts:
            return EvaluationResult(
                metric="lexical_overlap",
                score=0.0,
                details={"reason": "Missing data"},
            )
        
        # Tokenize
        answer_words = set(answer.lower().split())
        context_words = set(" ".join(contexts).lower().split())
        
        # Remove stopwords (basic)
        stopwords = {"bir", "ve", "bu", "için", "ile", "de", "da", "the", "a", "an", "is"}
        answer_words -= stopwords
        context_words -= stopwords
        
        if not answer_words:
            return EvaluationResult(metric="lexical_overlap", score=0.0)
        
        overlap = answer_words & context_words
        score = len(overlap) / len(answer_words)
        
        return EvaluationResult(
            metric="lexical_overlap",
            score=score,
            details={
                "answer_words": len(answer_words),
                "context_words": len(context_words),
                "overlap_words": len(overlap),
            },
        )
    
    def evaluate_answer_correctness(
        self,
        answer: str,
        ground_truth: str,
    ) -> EvaluationResult:
        """
        Answer Correctness: Cevabın doğruluğu (ground truth varsa).
        
        Args:
            answer: Üretilen cevap
            ground_truth: Doğru cevap
            
        Returns:
            Değerlendirme sonucu
        """
        if not answer or not ground_truth:
            return EvaluationResult(
                metric="answer_correctness",
                score=0.0,
                details={"reason": "Missing ground truth"},
            )
        
        self._lazy_load()
        
        prompt = f"""İki cevabı karşılaştır ve benzerliklerini değerlendir.

Üretilen Cevap:
{answer[:800]}

Doğru Cevap:
{ground_truth[:800]}

Üretilen cevap doğru cevapla ne kadar uyumlu?
0-10 arası puan ver (10 = tamamen aynı anlam, 0 = tamamen farklı):
Puan:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=20)
            score = float(re.search(r'\d+', response).group()) / 10.0
            score = min(max(score, 0.0), 1.0)
        except Exception:
            score = 0.5
        
        return EvaluationResult(
            metric="answer_correctness",
            score=score,
            details={
                "answer_length": len(answer),
                "ground_truth_length": len(ground_truth),
            },
        )
    
    def evaluate_full(
        self,
        query: str,
        contexts: List[str],
        answer: str,
        ground_truth: str = None,
    ) -> RAGEvaluationReport:
        """
        Tam RAG değerlendirmesi yap.
        
        Args:
            query: Sorgu
            contexts: Getirilen dökümanlar
            answer: Üretilen cevap
            ground_truth: Doğru cevap (opsiyonel)
            
        Returns:
            Değerlendirme raporu
        """
        report = RAGEvaluationReport(
            query=query,
            retrieved_docs=contexts,
            generated_answer=answer,
            ground_truth=ground_truth,
        )
        
        # Evaluate all metrics
        report.metrics["context_relevance"] = self.evaluate_context_relevance(query, contexts)
        report.metrics["faithfulness"] = self.evaluate_faithfulness(answer, contexts)
        report.metrics["answer_relevance"] = self.evaluate_answer_relevance(query, answer)
        report.metrics["lexical_overlap"] = self.evaluate_lexical_overlap(answer, contexts)
        
        if ground_truth:
            report.metrics["answer_correctness"] = self.evaluate_answer_correctness(answer, ground_truth)
        
        # Calculate overall score (weighted average)
        weights = {
            "context_relevance": 0.2,
            "faithfulness": 0.3,
            "answer_relevance": 0.3,
            "lexical_overlap": 0.1,
            "answer_correctness": 0.1,
        }
        
        total_weight = 0
        weighted_sum = 0
        
        for metric, result in report.metrics.items():
            if metric in weights:
                weighted_sum += result.score * weights[metric]
                total_weight += weights[metric]
        
        report.overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        return report


class BatchEvaluator:
    """Toplu değerlendirme."""
    
    def __init__(self):
        """Batch evaluator başlat."""
        self.evaluator = RAGEvaluator()
        self.results: List[RAGEvaluationReport] = []
    
    def add_sample(
        self,
        query: str,
        contexts: List[str],
        answer: str,
        ground_truth: str = None,
    ):
        """Örnek ekle."""
        report = self.evaluator.evaluate_full(query, contexts, answer, ground_truth)
        self.results.append(report)
    
    def get_summary(self) -> Dict[str, Any]:
        """Özet istatistikler."""
        if not self.results:
            return {"error": "No results"}
        
        metric_scores = {}
        
        for report in self.results:
            for metric, result in report.metrics.items():
                if metric not in metric_scores:
                    metric_scores[metric] = []
                metric_scores[metric].append(result.score)
        
        summary = {
            "total_samples": len(self.results),
            "overall_avg": sum(r.overall_score for r in self.results) / len(self.results),
            "metrics": {},
        }
        
        for metric, scores in metric_scores.items():
            summary["metrics"][metric] = {
                "mean": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
            }
        
        return summary


# Singleton instance
rag_evaluator = RAGEvaluator()
