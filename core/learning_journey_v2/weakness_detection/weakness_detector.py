"""
🎯 Weakness Detector

Otomatik zayıflık tespiti ve adaptif içerik sistemi.
Sınav sonuçlarını analiz ederek zayıf noktaları tespit eder
ve kişiselleştirilmiş takviye içerik önerir.

Özellikler:
- Pattern-based weakness detection
- Cross-topic correlation analysis
- Trend analysis (iyileşme/kötüleşme)
- Adaptive content recommendation
- Dynamic stage closure entegrasyonu
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from collections import defaultdict
import math


class WeaknessType(Enum):
    """Zayıflık türleri"""
    KNOWLEDGE_GAP = "knowledge_gap"           # Bilgi eksikliği
    CONCEPTUAL_ERROR = "conceptual_error"     # Kavram yanılgısı
    APPLICATION_FAILURE = "application_failure"  # Uygulama zorluğu
    MEMORY_DECAY = "memory_decay"             # Hafıza zayıflaması
    TIME_MANAGEMENT = "time_management"       # Zaman yönetimi
    CARELESS_ERROR = "careless_error"         # Dikkatsizlik


class TrendDirection(Enum):
    """Trend yönü"""
    IMPROVING = "improving"       # İyileşme
    STABLE = "stable"             # Stabil
    DECLINING = "declining"       # Kötüleşme
    FLUCTUATING = "fluctuating"   # Dalgalı


@dataclass
class WeaknessSignal:
    """Tek bir zayıflık sinyali"""
    signal_id: str
    topic_id: str
    weakness_type: WeaknessType
    severity: float              # 0.0-1.0 (yüksek = daha ciddi)
    confidence: float            # 0.0-1.0
    
    # Kanıt
    evidence: List[str] = field(default_factory=list)
    related_questions: List[str] = field(default_factory=list)
    
    # Zaman
    detected_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    occurrence_count: int = 1


@dataclass
class WeaknessCluster:
    """İlişkili zayıflıkların kümesi"""
    cluster_id: str
    name: str
    description: str
    
    signals: List[WeaknessSignal] = field(default_factory=list)
    affected_topics: Set[str] = field(default_factory=set)
    
    # Aggregated metrics
    average_severity: float = 0.0
    total_occurrences: int = 0
    trend: TrendDirection = TrendDirection.STABLE
    
    # Öneriler
    recommended_actions: List[str] = field(default_factory=list)
    priority: int = 0  # 1 = en yüksek


@dataclass
class AdaptiveContent:
    """Adaptif içerik önerisi"""
    content_id: str
    content_type: str  # video, practice, explanation, example
    topic_id: str
    weakness_types: List[WeaknessType]
    
    title: str
    description: str
    estimated_minutes: int
    
    # Hedefleme
    target_severity: float  # Bu seviyedeki zayıflıklar için
    effectiveness_score: float = 0.0  # Geçmiş performansa göre
    
    # Priority
    priority: int = 0


class WeaknessDetector:
    """
    Zayıflık Tespit Sistemi
    
    Sınav ve alıştırma sonuçlarından zayıflıkları tespit eder,
    kategorize eder ve adaptif içerik önerir.
    """
    
    # Thresholds
    WEAKNESS_THRESHOLD = 0.6       # Bu skorun altı = zayıflık
    SEVERE_THRESHOLD = 0.4         # Bu skorun altı = ciddi zayıflık
    CRITICAL_THRESHOLD = 0.25      # Bu skorun altı = kritik
    
    # Trend detection
    MIN_ATTEMPTS_FOR_TREND = 3     # Trend için minimum deneme
    TREND_WINDOW_DAYS = 14         # Trend penceresi
    
    # Content effectiveness
    MIN_EFFECTIVENESS = 0.3        # Minimum içerik etkinliği
    
    def __init__(self):
        self.weakness_signals: Dict[str, WeaknessSignal] = {}
        self.weakness_clusters: Dict[str, WeaknessCluster] = {}
        
        # History for trend analysis
        self.attempt_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        
        # Adaptive content library
        self.content_library: Dict[str, AdaptiveContent] = {}
        
        # Cross-topic correlations
        self.topic_correlations: Dict[str, Set[str]] = defaultdict(set)
    
    def analyze_attempt(
        self,
        topic_id: str,
        score: float,
        question_results: List[Dict] = None,
        time_taken_seconds: int = 0,
        expected_time_seconds: int = 0
    ) -> List[WeaknessSignal]:
        """
        Tek bir denemeyi analiz et
        
        Args:
            topic_id: Konu ID
            score: 0.0-1.0 arası skor
            question_results: Soru bazlı sonuçlar
            time_taken_seconds: Harcanan süre
            expected_time_seconds: Beklenen süre
        
        Returns:
            Tespit edilen zayıflık sinyalleri
        """
        now = datetime.now()
        signals = []
        
        # History'e ekle
        self.attempt_history[topic_id].append((now, score))
        
        # 1. Genel performans kontrolü
        if score < self.WEAKNESS_THRESHOLD:
            severity = 1.0 - score
            signal = self._create_signal(
                topic_id=topic_id,
                weakness_type=WeaknessType.KNOWLEDGE_GAP,
                severity=severity,
                confidence=0.8,
                evidence=[f"Skor: %{int(score * 100)} (eşik: %{int(self.WEAKNESS_THRESHOLD * 100)})"]
            )
            signals.append(signal)
        
        # 2. Soru bazlı analiz
        if question_results:
            question_signals = self._analyze_questions(topic_id, question_results)
            signals.extend(question_signals)
        
        # 3. Zaman analizi
        if time_taken_seconds > 0 and expected_time_seconds > 0:
            time_signals = self._analyze_time(
                topic_id, time_taken_seconds, expected_time_seconds, score
            )
            signals.extend(time_signals)
        
        # 4. Trend analizi
        trend = self._analyze_trend(topic_id)
        if trend == TrendDirection.DECLINING:
            signal = self._create_signal(
                topic_id=topic_id,
                weakness_type=WeaknessType.MEMORY_DECAY,
                severity=0.6,
                confidence=0.7,
                evidence=["Performans düşüş trendi tespit edildi"]
            )
            signals.append(signal)
        
        # Sinyalleri kaydet
        for signal in signals:
            self.weakness_signals[signal.signal_id] = signal
        
        # Cluster güncelle
        self._update_clusters()
        
        return signals
    
    def _analyze_questions(
        self,
        topic_id: str,
        question_results: List[Dict]
    ) -> List[WeaknessSignal]:
        """Soru bazlı zayıflık analizi"""
        signals = []
        
        # Soru türlerine göre grupla
        by_type: Dict[str, List[Dict]] = defaultdict(list)
        for q in question_results:
            q_type = q.get("question_type", "unknown")
            by_type[q_type].append(q)
        
        # Her tür için analiz
        for q_type, questions in by_type.items():
            correct = sum(1 for q in questions if q.get("correct", False))
            total = len(questions)
            type_score = correct / total if total > 0 else 0
            
            if type_score < self.WEAKNESS_THRESHOLD:
                # Bu soru türünde zayıflık var
                weakness_type = self._map_question_type_to_weakness(q_type)
                severity = 1.0 - type_score
                
                signal = self._create_signal(
                    topic_id=topic_id,
                    weakness_type=weakness_type,
                    severity=severity,
                    confidence=min(0.9, 0.5 + total * 0.1),
                    evidence=[f"{q_type} sorularında: {correct}/{total} doğru"],
                    related_questions=[q.get("question_id", "") for q in questions if not q.get("correct")]
                )
                signals.append(signal)
        
        # Dikkatsizlik hatası tespiti
        careless = self._detect_careless_errors(question_results)
        if careless:
            signal = self._create_signal(
                topic_id=topic_id,
                weakness_type=WeaknessType.CARELESS_ERROR,
                severity=0.4,
                confidence=0.6,
                evidence=[f"{len(careless)} dikkatsizlik hatası tespit edildi"],
                related_questions=careless
            )
            signals.append(signal)
        
        return signals
    
    def _analyze_time(
        self,
        topic_id: str,
        time_taken: int,
        expected_time: int,
        score: float
    ) -> List[WeaknessSignal]:
        """Zaman bazlı analiz"""
        signals = []
        
        time_ratio = time_taken / expected_time
        
        # Çok hızlı + düşük skor = dikkatsizlik
        if time_ratio < 0.5 and score < 0.7:
            signal = self._create_signal(
                topic_id=topic_id,
                weakness_type=WeaknessType.CARELESS_ERROR,
                severity=0.5,
                confidence=0.65,
                evidence=[f"Beklenen sürenin %{int(time_ratio * 100)}'inde tamamlandı, skor: %{int(score * 100)}"]
            )
            signals.append(signal)
        
        # Çok yavaş = uygulama zorluğu
        elif time_ratio > 2.0:
            severity = min(0.8, (time_ratio - 1) * 0.3)
            signal = self._create_signal(
                topic_id=topic_id,
                weakness_type=WeaknessType.APPLICATION_FAILURE,
                severity=severity,
                confidence=0.6,
                evidence=[f"Beklenen sürenin {time_ratio:.1f} katı harcandı"]
            )
            signals.append(signal)
        
        return signals
    
    def _analyze_trend(self, topic_id: str) -> TrendDirection:
        """Trend analizi"""
        history = self.attempt_history.get(topic_id, [])
        
        if len(history) < self.MIN_ATTEMPTS_FOR_TREND:
            return TrendDirection.STABLE
        
        # Son 14 gündeki denemeleri al
        cutoff = datetime.now() - timedelta(days=self.TREND_WINDOW_DAYS)
        recent = [(dt, score) for dt, score in history if dt >= cutoff]
        
        if len(recent) < self.MIN_ATTEMPTS_FOR_TREND:
            return TrendDirection.STABLE
        
        # Basit lineer regresyon
        scores = [score for _, score in sorted(recent, key=lambda x: x[0])]
        n = len(scores)
        
        # Slope hesapla
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return TrendDirection.STABLE
        
        slope = numerator / denominator
        
        # Slope yorumla
        if slope > 0.05:
            return TrendDirection.IMPROVING
        elif slope < -0.05:
            return TrendDirection.DECLINING
        else:
            # Varyans kontrolü
            variance = sum((s - y_mean) ** 2 for s in scores) / n
            if variance > 0.1:
                return TrendDirection.FLUCTUATING
            return TrendDirection.STABLE
    
    def _create_signal(
        self,
        topic_id: str,
        weakness_type: WeaknessType,
        severity: float,
        confidence: float,
        evidence: List[str],
        related_questions: List[str] = None
    ) -> WeaknessSignal:
        """Yeni zayıflık sinyali oluştur"""
        signal_id = f"{topic_id}_{weakness_type.value}_{datetime.now().timestamp()}"
        
        return WeaknessSignal(
            signal_id=signal_id,
            topic_id=topic_id,
            weakness_type=weakness_type,
            severity=min(1.0, max(0.0, severity)),
            confidence=min(1.0, max(0.0, confidence)),
            evidence=evidence,
            related_questions=related_questions or []
        )
    
    def _map_question_type_to_weakness(self, q_type: str) -> WeaknessType:
        """Soru türünü zayıflık türüne eşle"""
        mapping = {
            "multiple_choice": WeaknessType.KNOWLEDGE_GAP,
            "true_false": WeaknessType.CONCEPTUAL_ERROR,
            "fill_blank": WeaknessType.MEMORY_DECAY,
            "short_answer": WeaknessType.KNOWLEDGE_GAP,
            "problem_solving": WeaknessType.APPLICATION_FAILURE,
            "feynman": WeaknessType.CONCEPTUAL_ERROR,
            "concept_map": WeaknessType.CONCEPTUAL_ERROR
        }
        return mapping.get(q_type, WeaknessType.KNOWLEDGE_GAP)
    
    def _detect_careless_errors(
        self, 
        question_results: List[Dict]
    ) -> List[str]:
        """Dikkatsizlik hatalarını tespit et"""
        careless = []
        
        for q in question_results:
            if q.get("correct"):
                continue
            
            # Kolay soru + yanlış cevap = dikkatsizlik olabilir
            difficulty = q.get("difficulty", 0.5)
            if difficulty < 0.3:  # Kolay soru
                careless.append(q.get("question_id", ""))
            
            # Zaman çok kısa + yanlış = dikkatsizlik
            time_spent = q.get("time_spent_seconds", 0)
            if time_spent < 10 and not q.get("correct"):
                if q.get("question_id") not in careless:
                    careless.append(q.get("question_id", ""))
        
        return careless
    
    def _update_clusters(self):
        """Zayıflık kümelerini güncelle"""
        # Türe göre grupla
        by_type: Dict[WeaknessType, List[WeaknessSignal]] = defaultdict(list)
        
        for signal in self.weakness_signals.values():
            by_type[signal.weakness_type].append(signal)
        
        # Her tür için cluster oluştur/güncelle
        for weakness_type, signals in by_type.items():
            cluster_id = weakness_type.value
            
            if cluster_id not in self.weakness_clusters:
                self.weakness_clusters[cluster_id] = WeaknessCluster(
                    cluster_id=cluster_id,
                    name=self._get_weakness_name(weakness_type),
                    description=self._get_weakness_description(weakness_type)
                )
            
            cluster = self.weakness_clusters[cluster_id]
            cluster.signals = signals
            cluster.affected_topics = set(s.topic_id for s in signals)
            cluster.total_occurrences = sum(s.occurrence_count for s in signals)
            
            if signals:
                cluster.average_severity = sum(s.severity for s in signals) / len(signals)
            
            # Priority hesapla
            cluster.priority = self._calculate_priority(cluster)
            
            # Öneriler
            cluster.recommended_actions = self._generate_recommendations(cluster)
    
    def _get_weakness_name(self, wtype: WeaknessType) -> str:
        """Zayıflık türü adı"""
        names = {
            WeaknessType.KNOWLEDGE_GAP: "Bilgi Eksikliği",
            WeaknessType.CONCEPTUAL_ERROR: "Kavram Yanılgısı",
            WeaknessType.APPLICATION_FAILURE: "Uygulama Zorluğu",
            WeaknessType.MEMORY_DECAY: "Hafıza Zayıflaması",
            WeaknessType.TIME_MANAGEMENT: "Zaman Yönetimi",
            WeaknessType.CARELESS_ERROR: "Dikkatsizlik Hataları"
        }
        return names.get(wtype, "Bilinmeyen")
    
    def _get_weakness_description(self, wtype: WeaknessType) -> str:
        """Zayıflık türü açıklaması"""
        descriptions = {
            WeaknessType.KNOWLEDGE_GAP: "Temel bilgi ve kavramlarda eksiklik",
            WeaknessType.CONCEPTUAL_ERROR: "Kavramların yanlış anlaşılması",
            WeaknessType.APPLICATION_FAILURE: "Teorik bilgiyi pratiğe dökme zorluğu",
            WeaknessType.MEMORY_DECAY: "Öğrenilen bilgilerin zamanla unutulması",
            WeaknessType.TIME_MANAGEMENT: "Soru çözme süresini etkili kullanamama",
            WeaknessType.CARELESS_ERROR: "Dikkatsizlikten kaynaklanan hatalar"
        }
        return descriptions.get(wtype, "")
    
    def _calculate_priority(self, cluster: WeaknessCluster) -> int:
        """Cluster önceliği hesapla (1 = en yüksek)"""
        if cluster.average_severity >= 0.8:
            return 1
        elif cluster.average_severity >= 0.6:
            return 2
        elif cluster.average_severity >= 0.4:
            return 3
        else:
            return 4
    
    def _generate_recommendations(
        self, 
        cluster: WeaknessCluster
    ) -> List[str]:
        """Cluster için öneriler oluştur"""
        recommendations = []
        wtype = WeaknessType(cluster.cluster_id)
        
        if wtype == WeaknessType.KNOWLEDGE_GAP:
            recommendations.extend([
                "Temel kavramları tekrar gözden geçirin",
                "Video içeriklerle görsel öğrenmeyi deneyin",
                "Özet notlar çıkarın"
            ])
        elif wtype == WeaknessType.CONCEPTUAL_ERROR:
            recommendations.extend([
                "Kavram haritası oluşturun",
                "Feynman tekniği ile öğretmeye çalışın",
                "Farklı kaynaklardan okuyun"
            ])
        elif wtype == WeaknessType.APPLICATION_FAILURE:
            recommendations.extend([
                "Daha fazla pratik problem çözün",
                "Adım adım çözüm örneklerini inceleyin",
                "Gerçek dünya uygulamalarını araştırın"
            ])
        elif wtype == WeaknessType.MEMORY_DECAY:
            recommendations.extend([
                "Aralıklı tekrar yapın",
                "Flashcard'lar kullanın",
                "Aktif hatırlama tekniklerini uygulayın"
            ])
        elif wtype == WeaknessType.TIME_MANAGEMENT:
            recommendations.extend([
                "Zamanlı pratikler yapın",
                "Pomodoro tekniğini deneyin",
                "Önce kolay sorularla başlayın"
            ])
        elif wtype == WeaknessType.CARELESS_ERROR:
            recommendations.extend([
                "Cevapları tekrar kontrol edin",
                "Daha dikkatli okuyun",
                "Sakin bir ortamda çalışın"
            ])
        
        return recommendations
    
    def get_weakness_summary(self) -> Dict[str, Any]:
        """Genel zayıflık özeti"""
        clusters = sorted(
            self.weakness_clusters.values(),
            key=lambda c: (c.priority, -c.average_severity)
        )
        
        total_signals = len(self.weakness_signals)
        critical = sum(1 for s in self.weakness_signals.values() if s.severity >= 0.75)
        moderate = sum(1 for s in self.weakness_signals.values() if 0.5 <= s.severity < 0.75)
        mild = sum(1 for s in self.weakness_signals.values() if s.severity < 0.5)
        
        all_topics = set(s.topic_id for s in self.weakness_signals.values())
        
        return {
            "total_signals": total_signals,
            "by_severity": {
                "critical": critical,
                "moderate": moderate,
                "mild": mild
            },
            "affected_topics": len(all_topics),
            "clusters": [
                {
                    "id": c.cluster_id,
                    "name": c.name,
                    "priority": c.priority,
                    "severity": c.average_severity,
                    "topic_count": len(c.affected_topics),
                    "recommendations": c.recommended_actions[:2]
                }
                for c in clusters
            ],
            "top_priority_topics": self._get_priority_topics(5)
        }
    
    def _get_priority_topics(self, limit: int = 5) -> List[Dict]:
        """En öncelikli konuları getir"""
        topic_severity: Dict[str, float] = defaultdict(float)
        topic_signals: Dict[str, int] = defaultdict(int)
        
        for signal in self.weakness_signals.values():
            topic_severity[signal.topic_id] = max(
                topic_severity[signal.topic_id],
                signal.severity
            )
            topic_signals[signal.topic_id] += 1
        
        # Skora göre sırala
        sorted_topics = sorted(
            topic_severity.items(),
            key=lambda x: (-x[1], -topic_signals[x[0]])
        )
        
        return [
            {
                "topic_id": topic_id,
                "severity": severity,
                "signal_count": topic_signals[topic_id]
            }
            for topic_id, severity in sorted_topics[:limit]
        ]
    
    def get_stage_closure_adjustments(
        self,
        stage_id: str,
        base_questions: List[Dict]
    ) -> List[Dict]:
        """
        Stage kapanış sınavı için zayıflık bazlı ek sorular
        
        Zayıf alanlara %40 extra soru ekler.
        """
        # Stage'e ait zayıflıkları bul
        stage_topics = set()
        for signal in self.weakness_signals.values():
            # Topic'in stage'e ait olup olmadığını kontrol et
            # (Gerçek implementasyonda topic->stage mapping gerekli)
            stage_topics.add(signal.topic_id)
        
        # Zayıf topic'ler için ek sorular
        extra_questions = []
        
        for signal in self.weakness_signals.values():
            if signal.topic_id in stage_topics and signal.severity >= 0.5:
                # Bu topic için ek soru öner
                extra_questions.append({
                    "topic_id": signal.topic_id,
                    "weakness_type": signal.weakness_type.value,
                    "severity": signal.severity,
                    "suggested_question_types": self._get_remediation_question_types(
                        signal.weakness_type
                    ),
                    "focus_areas": signal.evidence[:2]
                })
        
        # En fazla %40 extra
        max_extra = int(len(base_questions) * 0.4)
        
        return sorted(
            extra_questions,
            key=lambda x: -x["severity"]
        )[:max_extra]
    
    def _get_remediation_question_types(
        self, 
        wtype: WeaknessType
    ) -> List[str]:
        """Zayıflık türü için önerilen soru türleri"""
        type_map = {
            WeaknessType.KNOWLEDGE_GAP: ["multiple_choice", "fill_blank"],
            WeaknessType.CONCEPTUAL_ERROR: ["feynman", "concept_map"],
            WeaknessType.APPLICATION_FAILURE: ["problem_solving"],
            WeaknessType.MEMORY_DECAY: ["fill_blank", "short_answer"],
            WeaknessType.TIME_MANAGEMENT: ["multiple_choice"],
            WeaknessType.CARELESS_ERROR: ["true_false", "multiple_choice"]
        }
        return type_map.get(wtype, ["multiple_choice"])
    
    def recommend_adaptive_content(
        self,
        topic_id: str,
        max_recommendations: int = 5
    ) -> List[AdaptiveContent]:
        """Konu için adaptif içerik öner"""
        # Topic'in zayıflıklarını bul
        topic_signals = [
            s for s in self.weakness_signals.values()
            if s.topic_id == topic_id
        ]
        
        if not topic_signals:
            return []
        
        # En ciddi zayıflıkları belirle
        weakness_types = set(s.weakness_type for s in topic_signals)
        max_severity = max(s.severity for s in topic_signals)
        
        # İçerik önerileri oluştur
        recommendations = []
        
        for wtype in weakness_types:
            content = self._create_adaptive_content(
                topic_id=topic_id,
                weakness_type=wtype,
                severity=max_severity
            )
            recommendations.append(content)
        
        # Priority'ye göre sırala
        recommendations.sort(key=lambda c: -c.priority)
        
        return recommendations[:max_recommendations]
    
    def _create_adaptive_content(
        self,
        topic_id: str,
        weakness_type: WeaknessType,
        severity: float
    ) -> AdaptiveContent:
        """Adaptif içerik oluştur"""
        content_templates = {
            WeaknessType.KNOWLEDGE_GAP: {
                "type": "explanation",
                "title": "Temel Kavram Açıklaması",
                "minutes": 15
            },
            WeaknessType.CONCEPTUAL_ERROR: {
                "type": "video",
                "title": "Kavram Düzeltme Videosu",
                "minutes": 10
            },
            WeaknessType.APPLICATION_FAILURE: {
                "type": "practice",
                "title": "Adım Adım Uygulama Pratiği",
                "minutes": 20
            },
            WeaknessType.MEMORY_DECAY: {
                "type": "flashcard",
                "title": "Hızlı Tekrar Kartları",
                "minutes": 10
            },
            WeaknessType.TIME_MANAGEMENT: {
                "type": "timed_quiz",
                "title": "Zamanlı Mini Quiz",
                "minutes": 5
            },
            WeaknessType.CARELESS_ERROR: {
                "type": "careful_practice",
                "title": "Dikkatli Okuma Pratiği",
                "minutes": 10
            }
        }
        
        template = content_templates.get(
            weakness_type,
            {"type": "practice", "title": "Ek Pratik", "minutes": 15}
        )
        
        return AdaptiveContent(
            content_id=f"{topic_id}_{weakness_type.value}_content",
            content_type=template["type"],
            topic_id=topic_id,
            weakness_types=[weakness_type],
            title=template["title"],
            description=self._get_weakness_description(weakness_type),
            estimated_minutes=template["minutes"],
            target_severity=severity,
            priority=int(severity * 10)
        )


# Singleton instance
weakness_detector = WeaknessDetector()
