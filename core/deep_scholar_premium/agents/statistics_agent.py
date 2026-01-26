"""
StatisticsAgent - Premium İstatistik Analiz Ajanı
==================================================

Görevler:
1. İstatistiksel veri çıkarma ve analiz
2. Veri tutarlılık kontrolü
3. İstatistiksel yanlışlık tespiti
4. Görselleştirme önerileri
5. Özet istatistikler
6. Karşılaştırmalı analiz
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.llm_manager import llm_manager


class StatisticType(str, Enum):
    """İstatistik türleri."""
    PERCENTAGE = "percentage"
    COUNT = "count"
    MEAN = "mean"
    MEDIAN = "median"
    RANGE = "range"
    RATIO = "ratio"
    GROWTH_RATE = "growth_rate"
    CORRELATION = "correlation"
    P_VALUE = "p_value"
    CONFIDENCE_INTERVAL = "confidence_interval"


class VisualizationType(str, Enum):
    """Görselleştirme türleri."""
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    HEATMAP = "heatmap"
    TABLE = "table"


@dataclass
class ExtractedStatistic:
    """Çıkarılan istatistik."""
    value: str
    type: StatisticType
    context: str  # Hangi bağlamda kullanılmış
    source_sentence: str
    has_source: bool
    source_citation: Optional[str] = None
    year: Optional[int] = None
    unit: Optional[str] = None
    
    # Doğrulama
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)


@dataclass
class StatisticalError:
    """İstatistiksel hata."""
    error_type: str
    description: str
    location: str
    severity: str  # "low", "medium", "high", "critical"
    suggestion: str


@dataclass
class VisualizationRecommendation:
    """Görselleştirme önerisi."""
    chart_type: VisualizationType
    title: str
    data_points: List[Dict[str, Any]]
    reason: str
    priority: int


@dataclass
class StatisticsReport:
    """İstatistik raporu."""
    total_statistics: int
    statistics: List[ExtractedStatistic]
    errors: List[StatisticalError]
    visualization_recommendations: List[VisualizationRecommendation]
    summary: Dict[str, Any]
    
    def to_markdown(self) -> str:
        """Markdown formatında rapor."""
        lines = [
            "# 📊 İstatistik Analiz Raporu",
            "",
            f"**Toplam İstatistik:** {self.total_statistics}",
            f"**Tespit Edilen Hata:** {len(self.errors)}",
            ""
        ]
        
        if self.errors:
            lines.extend([
                "## ⚠️ Potansiyel Hatalar",
                ""
            ])
            for error in self.errors:
                lines.append(f"- **{error.error_type}** ({error.severity}): {error.description}")
            lines.append("")
        
        if self.visualization_recommendations:
            lines.extend([
                "## 📈 Görselleştirme Önerileri",
                ""
            ])
            for rec in self.visualization_recommendations:
                lines.append(f"- **{rec.chart_type.value}**: {rec.title}")
        
        return "\n".join(lines)


class StatisticsAgent:
    """
    Premium İstatistik Analiz Ajanı
    
    İçerikteki istatistikleri analiz eder, doğrular ve görselleştirme önerir.
    """
    
    def __init__(self, global_state: Optional[Any] = None):
        self.global_state = global_state
        
        # İstatistik desenleri
        self.patterns = {
            "percentage": r'%\s*(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)\s*%',
            "number": r'\b(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(milyon|milyar|bin|trilyon|million|billion|thousand)?',
            "ratio": r'(\d+(?:[.,]\d+)?)\s*[:/]\s*(\d+(?:[.,]\d+)?)',
            "range": r'(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)',
            "p_value": r'p\s*[<=<>]\s*(\d+[.,]\d+)|p\s*=\s*(\d+[.,]\d+)',
            "confidence": r'%\s*(\d+)\s*(?:güven|CI|confidence)',
            "year": r'\b(19|20)\d{2}\b'
        }
    
    async def analyze_document(
        self,
        content: str
    ) -> StatisticsReport:
        """
        Dokümanı istatistiksel açıdan analiz et.
        
        Args:
            content: Doküman içeriği
            
        Returns:
            İstatistik raporu
        """
        # İstatistikleri çıkar
        statistics = await self.extract_statistics(content)
        
        # Hataları tespit et
        errors = await self.detect_errors(content, statistics)
        
        # Görselleştirme öner
        recommendations = await self.recommend_visualizations(statistics)
        
        # Özet oluştur
        summary = self._create_summary(statistics)
        
        return StatisticsReport(
            total_statistics=len(statistics),
            statistics=statistics,
            errors=errors,
            visualization_recommendations=recommendations,
            summary=summary
        )
    
    async def extract_statistics(
        self,
        content: str
    ) -> List[ExtractedStatistic]:
        """
        İçerikten istatistikleri çıkar.
        
        Args:
            content: Doküman içeriği
            
        Returns:
            Çıkarılan istatistikler
        """
        statistics = []
        
        # Cümlelere böl
        sentences = re.split(r'[.!?]\s+', content)
        
        for sentence in sentences:
            # Yüzdeler
            for match in re.finditer(self.patterns["percentage"], sentence):
                value = match.group(1) or match.group(2)
                if value:
                    stat = ExtractedStatistic(
                        value=f"%{value}",
                        type=StatisticType.PERCENTAGE,
                        context=self._extract_context(sentence),
                        source_sentence=sentence.strip(),
                        has_source=self._has_citation(sentence)
                    )
                    self._validate_percentage(stat)
                    statistics.append(stat)
            
            # p-değerleri
            for match in re.finditer(self.patterns["p_value"], sentence, re.IGNORECASE):
                value = match.group(1) or match.group(2)
                if value:
                    stat = ExtractedStatistic(
                        value=f"p={value}",
                        type=StatisticType.P_VALUE,
                        context=self._extract_context(sentence),
                        source_sentence=sentence.strip(),
                        has_source=self._has_citation(sentence)
                    )
                    self._validate_p_value(stat)
                    statistics.append(stat)
            
            # Büyük sayılar
            for match in re.finditer(self.patterns["number"], sentence):
                value = match.group(1)
                unit = match.group(2)
                if value and len(value.replace(",", "").replace(".", "")) >= 4:
                    stat = ExtractedStatistic(
                        value=value,
                        type=StatisticType.COUNT,
                        context=self._extract_context(sentence),
                        source_sentence=sentence.strip(),
                        has_source=self._has_citation(sentence),
                        unit=unit
                    )
                    statistics.append(stat)
        
        return statistics
    
    async def detect_errors(
        self,
        content: str,
        statistics: List[ExtractedStatistic]
    ) -> List[StatisticalError]:
        """
        İstatistiksel hataları tespit et.
        
        Args:
            content: Doküman içeriği
            statistics: Çıkarılan istatistikler
            
        Returns:
            Tespit edilen hatalar
        """
        errors = []
        
        # Kaynak eksikliği kontrolü
        for stat in statistics:
            if not stat.has_source and stat.type in [StatisticType.PERCENTAGE, StatisticType.COUNT]:
                errors.append(StatisticalError(
                    error_type="Kaynak Eksikliği",
                    description=f"'{stat.value}' değeri için kaynak belirtilmemiş",
                    location=stat.source_sentence[:50] + "...",
                    severity="medium",
                    suggestion="Bu istatistik için kaynak ekleyin"
                ))
        
        # Çelişkili istatistikler
        percentages = [s for s in statistics if s.type == StatisticType.PERCENTAGE]
        for i, stat1 in enumerate(percentages):
            for stat2 in percentages[i+1:]:
                if self._check_contradiction(stat1, stat2):
                    errors.append(StatisticalError(
                        error_type="Potansiyel Çelişki",
                        description=f"'{stat1.value}' ve '{stat2.value}' değerleri çelişebilir",
                        location=stat1.source_sentence[:30] + "...",
                        severity="high",
                        suggestion="Bu değerlerin tutarlılığını kontrol edin"
                    ))
        
        # LLM ile derin analiz
        if len(statistics) > 0:
            prompt = f"""Aşağıdaki istatistiklerde:
1. Matematik hataları
2. Mantıksız değerler
3. Bağlamla uyumsuzluk
4. Güncellik sorunları

tespit et.

## İstatistikler:
{json.dumps([{"value": s.value, "context": s.context} for s in statistics[:20]], ensure_ascii=False)}

## Yanıt (JSON Array):
[{{"error_type": "", "description": "", "severity": "low/medium/high", "suggestion": ""}}]"""

            response = await self._llm_call(prompt)
            
            try:
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    data = json.loads(json_match.group())
                    for item in data:
                        if item.get("description"):
                            errors.append(StatisticalError(
                                error_type=item.get("error_type", "Genel"),
                                description=item.get("description", ""),
                                location="",
                                severity=item.get("severity", "medium"),
                                suggestion=item.get("suggestion", "")
                            ))
            except:
                pass
        
        return errors
    
    async def recommend_visualizations(
        self,
        statistics: List[ExtractedStatistic]
    ) -> List[VisualizationRecommendation]:
        """
        Görselleştirme öner.
        
        Args:
            statistics: Çıkarılan istatistikler
            
        Returns:
            Görselleştirme önerileri
        """
        recommendations = []
        
        # Yüzdelik dağılım varsa
        percentages = [s for s in statistics if s.type == StatisticType.PERCENTAGE]
        if len(percentages) >= 3:
            recommendations.append(VisualizationRecommendation(
                chart_type=VisualizationType.PIE_CHART,
                title="Yüzde Dağılımı",
                data_points=[{"label": s.context[:30], "value": s.value} for s in percentages[:5]],
                reason="Birden fazla yüzdelik değer pasta grafikte gösterilebilir",
                priority=1
            ))
        
        # Zaman serisi varsa
        stats_with_years = [s for s in statistics if s.year]
        if len(stats_with_years) >= 2:
            recommendations.append(VisualizationRecommendation(
                chart_type=VisualizationType.LINE_CHART,
                title="Zaman Serisi Analizi",
                data_points=[{"year": s.year, "value": s.value} for s in stats_with_years],
                reason="Yıllara göre değişim çizgi grafikte gösterilebilir",
                priority=2
            ))
        
        # Karşılaştırmalı veriler
        counts = [s for s in statistics if s.type == StatisticType.COUNT]
        if len(counts) >= 2:
            recommendations.append(VisualizationRecommendation(
                chart_type=VisualizationType.BAR_CHART,
                title="Karşılaştırmalı Analiz",
                data_points=[{"label": s.context[:30], "value": s.value} for s in counts[:6]],
                reason="Sayısal karşılaştırmalar bar grafikte etkili",
                priority=3
            ))
        
        # Tablo önerisi (her zaman)
        if len(statistics) >= 3:
            recommendations.append(VisualizationRecommendation(
                chart_type=VisualizationType.TABLE,
                title="İstatistik Özet Tablosu",
                data_points=[{"metric": s.context[:40], "value": s.value} for s in statistics[:10]],
                reason="Tüm istatistikler özet tabloda sunulabilir",
                priority=4
            ))
        
        return sorted(recommendations, key=lambda x: x.priority)
    
    async def calculate_summary_statistics(
        self,
        data: List[float],
        label: str = "Veri"
    ) -> Dict[str, Any]:
        """
        Özet istatistikler hesapla.
        
        Args:
            data: Sayısal veri listesi
            label: Veri etiketi
            
        Returns:
            Özet istatistikler
        """
        if not data:
            return {"error": "Veri bulunamadı"}
        
        n = len(data)
        sorted_data = sorted(data)
        
        mean = sum(data) / n
        variance = sum((x - mean) ** 2 for x in data) / n
        std_dev = variance ** 0.5
        
        median = sorted_data[n // 2] if n % 2 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
        
        q1 = sorted_data[n // 4]
        q3 = sorted_data[3 * n // 4]
        iqr = q3 - q1
        
        return {
            "label": label,
            "n": n,
            "mean": round(mean, 2),
            "median": median,
            "std_dev": round(std_dev, 2),
            "min": min(data),
            "max": max(data),
            "range": max(data) - min(data),
            "q1": q1,
            "q3": q3,
            "iqr": iqr
        }
    
    def _extract_context(self, sentence: str) -> str:
        """Bağlam çıkar."""
        # Anahtar kelimeleri bul
        keywords = ["oranı", "yüzdesi", "sayısı", "artış", "azalış", 
                   "büyüme", "düşüş", "değer", "miktar", "toplam"]
        
        for keyword in keywords:
            if keyword in sentence.lower():
                # Anahtar kelime etrafındaki bağlamı al
                idx = sentence.lower().find(keyword)
                start = max(0, idx - 20)
                end = min(len(sentence), idx + len(keyword) + 20)
                return sentence[start:end].strip()
        
        return sentence[:50].strip()
    
    def _has_citation(self, sentence: str) -> bool:
        """Atıf var mı kontrol et."""
        patterns = [
            r'\([^)]+\d{4}\)',  # APA style
            r'\[\d+\]',         # IEEE style
            r'[A-Z][a-z]+\s+\(\d{4}\)',  # Author (year)
        ]
        return any(re.search(p, sentence) for p in patterns)
    
    def _validate_percentage(self, stat: ExtractedStatistic):
        """Yüzdeyi doğrula."""
        try:
            value = float(stat.value.replace("%", "").replace(",", "."))
            if value < 0:
                stat.is_valid = False
                stat.issues.append("Negatif yüzde değeri")
            elif value > 100:
                # %100'den büyük olabilir (büyüme oranı gibi)
                stat.issues.append("100'den büyük - büyüme oranı olabilir")
        except:
            pass
    
    def _validate_p_value(self, stat: ExtractedStatistic):
        """p-değerini doğrula."""
        try:
            value = float(stat.value.split("=")[1].replace(",", "."))
            if value < 0 or value > 1:
                stat.is_valid = False
                stat.issues.append("p-değeri 0-1 arasında olmalı")
        except:
            pass
    
    def _check_contradiction(
        self, 
        stat1: ExtractedStatistic, 
        stat2: ExtractedStatistic
    ) -> bool:
        """İki istatistik çelişiyor mu?"""
        # Aynı bağlamda farklı değerler
        if stat1.context and stat2.context:
            context_overlap = set(stat1.context.lower().split()) & set(stat2.context.lower().split())
            if len(context_overlap) >= 3 and stat1.value != stat2.value:
                return True
        return False
    
    def _create_summary(
        self, 
        statistics: List[ExtractedStatistic]
    ) -> Dict[str, Any]:
        """Özet oluştur."""
        return {
            "total": len(statistics),
            "by_type": {
                t.value: len([s for s in statistics if s.type == t])
                for t in StatisticType
            },
            "with_source": len([s for s in statistics if s.has_source]),
            "without_source": len([s for s in statistics if not s.has_source]),
            "with_issues": len([s for s in statistics if s.issues])
        }
    
    async def _llm_call(self, prompt: str, timeout: int = 300) -> str:
        """LLM çağrısı yap."""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_manager.chat,
                    messages=messages,
                    model_type="default"
                ),
                timeout=timeout
            )
            return response.get("content", "") if isinstance(response, dict) else str(response)
        except Exception as e:
            return f"Error: {str(e)}"
