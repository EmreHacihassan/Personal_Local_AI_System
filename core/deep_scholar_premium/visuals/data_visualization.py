"""
DataVisualizationEngine - Veri Görselleştirme Motoru
====================================================

Veri analizi ve görselleştirme entegrasyonu.
StatisticsAgent ile entegre çalışır.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import math
import statistics

from .svg_charts import SVGChartGenerator, DataSeries, ChartConfig, Chart, ChartType
from .diagram_generator import DiagramGenerator, DiagramType, DiagramFormat


class VisualizationType(str, Enum):
    """Görselleştirme türleri."""
    # Karşılaştırma
    COMPARISON_BAR = "comparison_bar"
    COMPARISON_GROUPED = "comparison_grouped"
    
    # Trend
    TREND_LINE = "trend_line"
    TREND_AREA = "trend_area"
    
    # Dağılım
    DISTRIBUTION_PIE = "distribution_pie"
    DISTRIBUTION_DONUT = "distribution_donut"
    
    # İlişki
    CORRELATION_HEATMAP = "correlation_heatmap"
    RELATIONSHIP_SCATTER = "relationship_scatter"
    
    # Süreç
    PROCESS_FLOW = "process_flow"
    TIMELINE = "timeline"
    
    # Hiyerarşi
    HIERARCHY_TREE = "hierarchy_tree"
    ORGANIZATION = "organization"


@dataclass
class DataSet:
    """Veri seti."""
    name: str
    data: Union[List[float], Dict[str, float], List[Dict[str, Any]]]
    labels: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualizationResult:
    """Görselleştirme sonucu."""
    visualization_type: VisualizationType
    chart: Optional[Chart] = None
    diagram_code: Optional[str] = None
    insights: List[str] = field(default_factory=list)
    statistics: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class DataVisualizationEngine:
    """
    Veri Görselleştirme Motoru
    
    Veri analizi yaparak en uygun görselleştirmeyi öneren
    ve oluşturan akıllı sistem.
    """
    
    def __init__(
        self,
        chart_generator: Optional[SVGChartGenerator] = None,
        diagram_generator: Optional[DiagramGenerator] = None
    ):
        self.chart_generator = chart_generator or SVGChartGenerator()
        self.diagram_generator = diagram_generator or DiagramGenerator()
    
    def analyze_and_visualize(
        self,
        dataset: DataSet,
        visualization_type: Optional[VisualizationType] = None,
        title: Optional[str] = None
    ) -> VisualizationResult:
        """
        Veri setini analiz edip görselleştir.
        
        Args:
            dataset: Veri seti
            visualization_type: Görselleştirme türü (None ise otomatik seç)
            title: Görselleştirme başlığı
            
        Returns:
            Görselleştirme sonucu
        """
        # İstatistikler
        stats = self._calculate_statistics(dataset)
        
        # Otomatik tür seçimi
        if visualization_type is None:
            visualization_type = self._recommend_visualization(dataset, stats)
        
        # Görselleştirme oluştur
        result = self._create_visualization(dataset, visualization_type, title)
        
        # İçgörüler
        result.statistics = stats
        result.insights = self._generate_insights(dataset, stats)
        result.recommendations = self._generate_recommendations(dataset, stats)
        
        return result
    
    def compare_datasets(
        self,
        datasets: List[DataSet],
        title: Optional[str] = None
    ) -> VisualizationResult:
        """Birden fazla veri setini karşılaştır."""
        if not datasets:
            raise ValueError("En az bir veri seti gerekli")
        
        # Serileri oluştur
        series = []
        labels = None
        
        for ds in datasets:
            if isinstance(ds.data, list) and all(isinstance(x, (int, float)) for x in ds.data):
                series.append(DataSeries(
                    name=ds.name,
                    values=ds.data
                ))
                if ds.labels and labels is None:
                    labels = ds.labels
        
        if not labels and series:
            labels = [f"Değer {i+1}" for i in range(len(series[0].values))]
        
        # Grafik oluştur
        chart = self.chart_generator.create_bar_chart(
            labels=labels or [],
            series=series,
            title=title or "Veri Karşılaştırması"
        )
        
        # Karşılaştırma istatistikleri
        comparison_stats = {}
        for ds in datasets:
            if isinstance(ds.data, list) and all(isinstance(x, (int, float)) for x in ds.data):
                comparison_stats[f"{ds.name}_mean"] = statistics.mean(ds.data) if ds.data else 0
        
        return VisualizationResult(
            visualization_type=VisualizationType.COMPARISON_GROUPED,
            chart=chart,
            statistics=comparison_stats,
            insights=self._generate_comparison_insights(datasets)
        )
    
    def create_trend_visualization(
        self,
        dataset: DataSet,
        time_labels: List[str],
        title: Optional[str] = None,
        show_forecast: bool = False
    ) -> VisualizationResult:
        """Trend görselleştirmesi oluştur."""
        values = dataset.data if isinstance(dataset.data, list) else list(dataset.data.values())
        
        # Basit tahmin (lineer regresyon)
        forecast_values = []
        if show_forecast and len(values) >= 3:
            n = len(values)
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n
            
            numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator != 0:
                slope = numerator / denominator
                intercept = y_mean - slope * x_mean
                
                for i in range(n, n + 3):
                    forecast_values.append(slope * i + intercept)
        
        # Seriler
        series = [DataSeries(name=dataset.name, values=values)]
        
        if forecast_values:
            full_forecast = [None] * len(values) + forecast_values
            # Not: None değerleri için ayrı handling gerekebilir
            series.append(DataSeries(
                name="Tahmin",
                values=values + forecast_values,
                color="#999999"
            ))
            time_labels = time_labels + [f"T+{i+1}" for i in range(len(forecast_values))]
        
        chart = self.chart_generator.create_line_chart(
            labels=time_labels,
            series=[DataSeries(name=dataset.name, values=values + forecast_values)] if forecast_values else series,
            title=title or "Trend Analizi",
            smooth=True
        )
        
        # Trend istatistikleri
        stats = self._calculate_statistics(dataset)
        
        # Trend yönü
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            trend_direction = "yükseliş" if second_half > first_half else "düşüş"
        else:
            trend_direction = "belirsiz"
        
        insights = [
            f"Trend yönü: {trend_direction}",
            f"Ortalama değer: {stats.get('mean', 0):.2f}",
            f"Değişim aralığı: {stats.get('range', 0):.2f}"
        ]
        
        return VisualizationResult(
            visualization_type=VisualizationType.TREND_LINE,
            chart=chart,
            statistics=stats,
            insights=insights
        )
    
    def create_distribution_visualization(
        self,
        dataset: DataSet,
        title: Optional[str] = None,
        donut: bool = False
    ) -> VisualizationResult:
        """Dağılım görselleştirmesi oluştur."""
        if isinstance(dataset.data, dict):
            labels = list(dataset.data.keys())
            values = list(dataset.data.values())
        else:
            labels = dataset.labels or [f"Kategori {i+1}" for i in range(len(dataset.data))]
            values = dataset.data
        
        chart = self.chart_generator.create_pie_chart(
            labels=labels,
            values=values,
            title=title or "Dağılım",
            donut=donut
        )
        
        # Dağılım istatistikleri
        total = sum(values)
        percentages = [(v / total * 100) if total > 0 else 0 for v in values]
        
        insights = []
        max_idx = percentages.index(max(percentages)) if percentages else 0
        min_idx = percentages.index(min(percentages)) if percentages else 0
        
        if labels:
            insights.append(f"En büyük pay: {labels[max_idx]} ({percentages[max_idx]:.1f}%)")
            insights.append(f"En küçük pay: {labels[min_idx]} ({percentages[min_idx]:.1f}%)")
        
        return VisualizationResult(
            visualization_type=VisualizationType.DISTRIBUTION_DONUT if donut else VisualizationType.DISTRIBUTION_PIE,
            chart=chart,
            statistics={"total": total, "category_count": len(labels)},
            insights=insights
        )
    
    def create_process_visualization(
        self,
        steps: List[Dict[str, Any]],
        title: Optional[str] = None
    ) -> VisualizationResult:
        """Süreç görselleştirmesi oluştur."""
        # Mermaid flowchart
        mermaid_code = "flowchart TD\n"
        
        for i, step in enumerate(steps):
            step_id = f"S{i}"
            step_name = step.get("name", f"Adım {i+1}")
            step_type = step.get("type", "process")
            
            # Node shape
            if step_type == "start":
                mermaid_code += f"    {step_id}(({step_name}))\n"
            elif step_type == "end":
                mermaid_code += f"    {step_id}(({step_name}))\n"
            elif step_type == "decision":
                mermaid_code += f"    {step_id}{{{step_name}}}\n"
            else:
                mermaid_code += f"    {step_id}[{step_name}]\n"
            
            # Bağlantı
            if i > 0:
                prev_id = f"S{i-1}"
                label = steps[i-1].get("link_label", "")
                if label:
                    mermaid_code += f"    {prev_id} -->|{label}| {step_id}\n"
                else:
                    mermaid_code += f"    {prev_id} --> {step_id}\n"
        
        return VisualizationResult(
            visualization_type=VisualizationType.PROCESS_FLOW,
            diagram_code=mermaid_code,
            insights=[f"Toplam {len(steps)} adım"],
            statistics={"step_count": len(steps)}
        )
    
    def _calculate_statistics(self, dataset: DataSet) -> Dict[str, float]:
        """İstatistikleri hesapla."""
        if isinstance(dataset.data, dict):
            values = list(dataset.data.values())
        else:
            values = [v for v in dataset.data if isinstance(v, (int, float))]
        
        if not values:
            return {}
        
        stats = {
            "count": len(values),
            "sum": sum(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values)
        }
        
        if len(values) > 1:
            stats["stdev"] = statistics.stdev(values)
            stats["variance"] = statistics.variance(values)
        
        if len(values) >= 2:
            stats["median"] = statistics.median(values)
        
        return stats
    
    def _recommend_visualization(
        self,
        dataset: DataSet,
        stats: Dict[str, float]
    ) -> VisualizationType:
        """Uygun görselleştirme türü öner."""
        data = dataset.data
        
        # Dict ise kategori bazlı
        if isinstance(data, dict):
            if len(data) <= 6:
                return VisualizationType.DISTRIBUTION_PIE
            else:
                return VisualizationType.COMPARISON_BAR
        
        # Liste ise
        if isinstance(data, list):
            if len(data) > 10:
                return VisualizationType.TREND_LINE
            elif len(data) <= 5:
                return VisualizationType.DISTRIBUTION_PIE
            else:
                return VisualizationType.COMPARISON_BAR
        
        return VisualizationType.COMPARISON_BAR
    
    def _create_visualization(
        self,
        dataset: DataSet,
        viz_type: VisualizationType,
        title: Optional[str]
    ) -> VisualizationResult:
        """Görselleştirme oluştur."""
        if isinstance(dataset.data, dict):
            labels = list(dataset.data.keys())
            values = list(dataset.data.values())
        else:
            labels = dataset.labels or [f"Değer {i+1}" for i in range(len(dataset.data))]
            values = dataset.data
        
        chart = None
        
        if viz_type in [VisualizationType.COMPARISON_BAR, VisualizationType.COMPARISON_GROUPED]:
            chart = self.chart_generator.create_bar_chart(
                labels=labels,
                series=[DataSeries(name=dataset.name, values=values)],
                title=title
            )
        
        elif viz_type in [VisualizationType.TREND_LINE, VisualizationType.TREND_AREA]:
            chart = self.chart_generator.create_line_chart(
                labels=labels,
                series=[DataSeries(name=dataset.name, values=values)],
                title=title,
                smooth=True
            )
        
        elif viz_type == VisualizationType.DISTRIBUTION_PIE:
            chart = self.chart_generator.create_pie_chart(
                labels=labels,
                values=values,
                title=title
            )
        
        elif viz_type == VisualizationType.DISTRIBUTION_DONUT:
            chart = self.chart_generator.create_pie_chart(
                labels=labels,
                values=values,
                title=title,
                donut=True
            )
        
        return VisualizationResult(
            visualization_type=viz_type,
            chart=chart
        )
    
    def _generate_insights(
        self,
        dataset: DataSet,
        stats: Dict[str, float]
    ) -> List[str]:
        """Veri içgörüleri oluştur."""
        insights = []
        
        if "mean" in stats:
            insights.append(f"Ortalama: {stats['mean']:.2f}")
        
        if "stdev" in stats:
            cv = (stats['stdev'] / stats['mean'] * 100) if stats['mean'] != 0 else 0
            if cv > 50:
                insights.append("Yüksek değişkenlik gözlemlendi")
            elif cv < 10:
                insights.append("Veriler oldukça homojen")
        
        if "min" in stats and "max" in stats:
            insights.append(f"Değer aralığı: {stats['min']:.2f} - {stats['max']:.2f}")
        
        return insights
    
    def _generate_recommendations(
        self,
        dataset: DataSet,
        stats: Dict[str, float]
    ) -> List[str]:
        """Öneriler oluştur."""
        recommendations = []
        
        if stats.get("count", 0) < 5:
            recommendations.append("Daha güvenilir analiz için daha fazla veri toplanması önerilir")
        
        if stats.get("stdev", 0) > stats.get("mean", 1):
            recommendations.append("Yüksek değişkenlik nedeniyle aykırı değerler incelenmeli")
        
        return recommendations
    
    def _generate_comparison_insights(self, datasets: List[DataSet]) -> List[str]:
        """Karşılaştırma içgörüleri."""
        insights = []
        
        means = {}
        for ds in datasets:
            if isinstance(ds.data, list) and ds.data:
                means[ds.name] = statistics.mean([d for d in ds.data if isinstance(d, (int, float))])
        
        if means:
            max_name = max(means, key=means.get)
            min_name = min(means, key=means.get)
            insights.append(f"En yüksek ortalama: {max_name}")
            insights.append(f"En düşük ortalama: {min_name}")
        
        return insights
