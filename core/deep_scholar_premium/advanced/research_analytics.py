"""
ResearchAnalytics - Araştırma Analitiği Sistemi
================================================

Kaynak dağılımı, atıf ağları ve konu haritaları oluşturur.

Özellikler:
- Source distribution analysis
- Citation network graph
- Topic coverage heatmap
- Research depth metrics
- Methodology analysis
"""

import asyncio
import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from collections import Counter, defaultdict

from core.llm_manager import llm_manager
from core.logger import get_logger

logger = get_logger("research_analytics")


class SourceType(str, Enum):
    """Kaynak türleri."""
    ACADEMIC_PAPER = "academic_paper"
    BOOK = "book"
    WEB_ARTICLE = "web_article"
    NEWS = "news"
    REPORT = "report"
    THESIS = "thesis"
    CONFERENCE = "conference"
    PREPRINT = "preprint"


class QualityTier(str, Enum):
    """Kalite seviyeleri."""
    TIER_1 = "tier_1"  # Q1 dergiler, prestijli yayınlar
    TIER_2 = "tier_2"  # Q2-Q3 dergiler
    TIER_3 = "tier_3"  # Web kaynakları, preprint
    UNKNOWN = "unknown"


@dataclass
class SourceMetrics:
    """Kaynak metrikleri."""
    total_sources: int
    by_type: Dict[str, int]
    by_quality: Dict[str, int]
    by_year: Dict[int, int]
    avg_citation_count: float
    diversity_score: float  # 0-1, ne kadar çeşitli kaynaklar
    recency_score: float  # 0-1, ne kadar güncel


@dataclass
class CitationNode:
    """Atıf ağı düğümü."""
    id: str
    title: str
    authors: List[str]
    year: int
    type: SourceType
    citations: List[str]  # Atıf yaptığı diğer kaynakların ID'leri
    cited_by: List[str]  # Bu kaynağı atıf yapanlar
    centrality: float  # Ağdaki önem


@dataclass
class TopicCluster:
    """Konu kümesi."""
    name: str
    keywords: List[str]
    source_count: int
    relevance_score: float
    sub_topics: List[str]


@dataclass
class ResearchAnalyticsReport:
    """Araştırma analitik raporu."""
    research_topic: str
    generated_at: datetime
    source_metrics: SourceMetrics
    citation_network: Dict[str, CitationNode]
    topic_clusters: List[TopicCluster]
    coverage_heatmap: Dict[str, Dict[str, float]]
    methodology_breakdown: Dict[str, int]
    gaps_identified: List[str]
    recommendations: List[str]
    quality_score: float  # 0-100 genel kalite skoru


class ResearchAnalyticsEngine:
    """
    Araştırma Analitiği Motoru
    
    Araştırma kalitesini ve kapsamını analiz eder.
    """
    
    def __init__(self):
        self.sources: List[Dict[str, Any]] = []
        self.citation_graph: Dict[str, CitationNode] = {}
        self.topic_model: Dict[str, List[str]] = {}
    
    async def analyze_sources(
        self,
        sources: List[Dict[str, Any]],
        topic: str
    ) -> ResearchAnalyticsReport:
        """
        Kaynakları analiz et ve rapor oluştur.
        
        Args:
            sources: Kaynak listesi
            topic: Araştırma konusu
        
        Returns:
            ResearchAnalyticsReport
        """
        self.sources = sources
        
        # Source metrics hesapla
        source_metrics = self._calculate_source_metrics(sources)
        
        # Atıf ağı oluştur
        citation_network = await self._build_citation_network(sources)
        
        # Konu kümeleri çıkar
        topic_clusters = await self._extract_topic_clusters(sources, topic)
        
        # Coverage heatmap
        coverage_heatmap = self._generate_coverage_heatmap(
            topic_clusters,
            sources
        )
        
        # Metodoloji breakdown
        methodology = await self._analyze_methodologies(sources)
        
        # Gap analizi
        gaps = await self._identify_gaps(topic, topic_clusters, sources)
        
        # Öneriler
        recommendations = await self._generate_recommendations(
            source_metrics,
            gaps,
            topic
        )
        
        # Genel kalite skoru
        quality_score = self._calculate_quality_score(
            source_metrics,
            topic_clusters,
            coverage_heatmap
        )
        
        return ResearchAnalyticsReport(
            research_topic=topic,
            generated_at=datetime.now(),
            source_metrics=source_metrics,
            citation_network=citation_network,
            topic_clusters=topic_clusters,
            coverage_heatmap=coverage_heatmap,
            methodology_breakdown=methodology,
            gaps_identified=gaps,
            recommendations=recommendations,
            quality_score=quality_score
        )
    
    def _calculate_source_metrics(
        self,
        sources: List[Dict[str, Any]]
    ) -> SourceMetrics:
        """Kaynak metriklerini hesapla."""
        if not sources:
            return SourceMetrics(
                total_sources=0,
                by_type={},
                by_quality={},
                by_year={},
                avg_citation_count=0,
                diversity_score=0,
                recency_score=0
            )
        
        # Tür dağılımı
        by_type = Counter()
        for s in sources:
            source_type = s.get("type", "unknown")
            by_type[source_type] += 1
        
        # Kalite dağılımı
        by_quality = Counter()
        for s in sources:
            quality = self._assess_source_quality(s)
            by_quality[quality] += 1
        
        # Yıl dağılımı
        by_year = Counter()
        current_year = datetime.now().year
        for s in sources:
            year = s.get("year", s.get("publication_year", current_year))
            if isinstance(year, int) and 1900 < year <= current_year + 1:
                by_year[year] += 1
        
        # Ortalama atıf sayısı
        citation_counts = [
            s.get("citations", s.get("citation_count", 0))
            for s in sources
        ]
        avg_citations = sum(citation_counts) / len(citation_counts) if citation_counts else 0
        
        # Çeşitlilik skoru (Shannon entropy based)
        type_probs = [c / len(sources) for c in by_type.values()]
        diversity = -sum(p * math.log(p) if p > 0 else 0 for p in type_probs)
        max_entropy = math.log(max(len(SourceType), 1))
        diversity_score = diversity / max_entropy if max_entropy > 0 else 0
        
        # Güncellik skoru
        if by_year:
            weighted_sum = sum(
                year * count for year, count in by_year.items()
            )
            total_count = sum(by_year.values())
            avg_year = weighted_sum / total_count if total_count > 0 else current_year
            # Son 5 yıl = 1.0, 20+ yıl = 0
            years_old = current_year - avg_year
            recency_score = max(0, 1 - (years_old / 20))
        else:
            recency_score = 0.5
        
        return SourceMetrics(
            total_sources=len(sources),
            by_type=dict(by_type),
            by_quality=dict(by_quality),
            by_year=dict(by_year),
            avg_citation_count=avg_citations,
            diversity_score=min(1.0, diversity_score),
            recency_score=recency_score
        )
    
    def _assess_source_quality(self, source: Dict[str, Any]) -> str:
        """Kaynak kalitesini değerlendir."""
        source_type = source.get("type", "").lower()
        journal = source.get("journal", "").lower()
        citations = source.get("citations", source.get("citation_count", 0))
        
        # Tier 1 indicators
        tier1_journals = ["nature", "science", "lancet", "cell", "nejm", "pnas"]
        if any(j in journal for j in tier1_journals):
            return QualityTier.TIER_1.value
        
        if source_type in ["academic_paper", "thesis"] and citations > 50:
            return QualityTier.TIER_1.value
        
        # Tier 2
        if source_type in ["academic_paper", "book", "conference"] and citations > 10:
            return QualityTier.TIER_2.value
        
        # Tier 3
        if source_type in ["web_article", "news", "preprint"]:
            return QualityTier.TIER_3.value
        
        return QualityTier.UNKNOWN.value
    
    async def _build_citation_network(
        self,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, CitationNode]:
        """Atıf ağı oluştur."""
        network: Dict[str, CitationNode] = {}
        
        for i, source in enumerate(sources):
            source_id = source.get("id", f"source_{i}")
            citations = source.get("references", source.get("citations_list", []))
            
            node = CitationNode(
                id=source_id,
                title=source.get("title", "Unknown"),
                authors=source.get("authors", []),
                year=source.get("year", 2024),
                type=SourceType(source.get("type", "web_article")),
                citations=[str(c) for c in citations if c],
                cited_by=[],
                centrality=0.0
            )
            network[source_id] = node
        
        # Cited_by ilişkilerini kur
        for node_id, node in network.items():
            for cited_id in node.citations:
                if cited_id in network:
                    network[cited_id].cited_by.append(node_id)
        
        # Centrality hesapla (basit degree centrality)
        max_connections = max(
            len(n.citations) + len(n.cited_by)
            for n in network.values()
        ) if network else 1
        
        for node in network.values():
            connections = len(node.citations) + len(node.cited_by)
            node.centrality = connections / max_connections if max_connections > 0 else 0
        
        return network
    
    async def _extract_topic_clusters(
        self,
        sources: List[Dict[str, Any]],
        main_topic: str
    ) -> List[TopicCluster]:
        """Konu kümelerini çıkar."""
        if not sources:
            return []
        
        # Kaynaklardan anahtar kelimeleri topla
        all_keywords = []
        for source in sources:
            keywords = source.get("keywords", [])
            if isinstance(keywords, list):
                all_keywords.extend(keywords)
            
            # Title'dan keyword çıkar
            title_words = source.get("title", "").split()
            all_keywords.extend([
                w.lower() for w in title_words
                if len(w) > 4 and w.isalpha()
            ])
        
        # Keyword frekansı
        keyword_freq = Counter(all_keywords)
        top_keywords = [kw for kw, _ in keyword_freq.most_common(20)]
        
        # LLM ile kümeleme
        prompt = f"""Aşağıdaki anahtar kelimeleri {main_topic} konusu için tematik kümelere ayır.
Her küme için bir isim ve alt konular belirle.

Anahtar Kelimeler:
{', '.join(top_keywords[:30])}

Ana Konu: {main_topic}

Kümeler (JSON formatında, 3-5 küme):
[{{"name": "küme adı", "keywords": ["kw1", "kw2"], "sub_topics": ["alt konu 1", "alt konu 2"]}}]"""
        
        try:
            response = await llm_manager.generate_async(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            # JSON parse
            json_match = response.find("[")
            json_end = response.rfind("]") + 1
            if json_match >= 0 and json_end > json_match:
                clusters_data = json.loads(response[json_match:json_end])
            else:
                clusters_data = []
            
            clusters = []
            for cd in clusters_data[:5]:
                # Her küme için kaynak sayısını hesapla
                cluster_keywords = set(cd.get("keywords", []))
                source_count = sum(
                    1 for s in sources
                    if cluster_keywords.intersection(set(s.get("keywords", [])))
                )
                
                clusters.append(TopicCluster(
                    name=cd.get("name", "Unknown"),
                    keywords=cd.get("keywords", []),
                    source_count=max(1, source_count),
                    relevance_score=0.8,  # Default
                    sub_topics=cd.get("sub_topics", [])
                ))
            
            return clusters
            
        except Exception as e:
            logger.error(f"Topic clustering error: {e}")
            # Fallback: basit kümeleme
            return [TopicCluster(
                name=main_topic,
                keywords=top_keywords[:10],
                source_count=len(sources),
                relevance_score=1.0,
                sub_topics=[]
            )]
    
    def _generate_coverage_heatmap(
        self,
        clusters: List[TopicCluster],
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Kapsam heatmap'i oluştur."""
        heatmap = {}
        
        # Dimensions: topic cluster vs source type
        source_types = list(set(
            s.get("type", "unknown") for s in sources
        ))
        
        for cluster in clusters:
            cluster_sources = [
                s for s in sources
                if set(cluster.keywords).intersection(set(s.get("keywords", [])))
            ]
            
            type_coverage = {}
            for st in source_types:
                count = sum(1 for s in cluster_sources if s.get("type") == st)
                # Normalize to 0-1
                type_coverage[st] = min(1.0, count / 5)  # 5+ = full coverage
            
            heatmap[cluster.name] = type_coverage
        
        return heatmap
    
    async def _analyze_methodologies(
        self,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Metodoloji dağılımını analiz et."""
        methodology_counts = Counter()
        
        default_methodologies = {
            "literature_review": 0,
            "empirical_study": 0,
            "case_study": 0,
            "survey": 0,
            "experimental": 0,
            "theoretical": 0,
            "meta_analysis": 0,
            "mixed_methods": 0
        }
        
        for source in sources:
            methodology = source.get("methodology", "unknown")
            if methodology != "unknown":
                methodology_counts[methodology] += 1
            else:
                # Heuristic: abstract'tan tahmin et
                abstract = source.get("abstract", "").lower()
                if "systematic review" in abstract or "meta-analysis" in abstract:
                    methodology_counts["meta_analysis"] += 1
                elif "survey" in abstract or "questionnaire" in abstract:
                    methodology_counts["survey"] += 1
                elif "experiment" in abstract or "rct" in abstract:
                    methodology_counts["experimental"] += 1
                elif "case study" in abstract:
                    methodology_counts["case_study"] += 1
                else:
                    methodology_counts["literature_review"] += 1
        
        # Merge with defaults
        default_methodologies.update(methodology_counts)
        return dict(default_methodologies)
    
    async def _identify_gaps(
        self,
        topic: str,
        clusters: List[TopicCluster],
        sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Araştırma boşluklarını tespit et."""
        gaps = []
        
        # Düşük kapsama alanları
        for cluster in clusters:
            if cluster.source_count < 2:
                gaps.append(
                    f"'{cluster.name}' konusunda kaynak yetersizliği ({cluster.source_count} kaynak)"
                )
        
        # Metodoloji eksiklikleri
        source_types = Counter(s.get("type", "unknown") for s in sources)
        if source_types.get("academic_paper", 0) < 3:
            gaps.append("Akademik makale sayısı yetersiz")
        
        # Güncellik eksikliği
        current_year = datetime.now().year
        recent_sources = sum(
            1 for s in sources
            if s.get("year", 0) >= current_year - 2
        )
        if recent_sources < len(sources) * 0.3:
            gaps.append("Güncel kaynak oranı düşük (%30'un altında)")
        
        # LLM ile ek gap tespiti
        if clusters:
            cluster_names = ", ".join(c.name for c in clusters)
            prompt = f"""Aşağıdaki konu ve alt başlıklar için potansiyel araştırma boşluklarını belirle.

Ana Konu: {topic}
Mevcut Alt Başlıklar: {cluster_names}
Kaynak Sayısı: {len(sources)}

Eksik olabilecek 2-3 alan (kısa maddeler):"""
            
            try:
                response = await llm_manager.generate_async(
                    prompt=prompt,
                    temperature=0.4,
                    max_tokens=200
                )
                
                for line in response.split("\n"):
                    line = line.strip()
                    if line and line[0] in "-•123456789":
                        gap = line.lstrip("-•0123456789.) ").strip()
                        if gap and len(gap) > 10:
                            gaps.append(gap)
                
            except Exception as e:
                logger.error(f"Gap analysis error: {e}")
        
        return gaps[:6]
    
    async def _generate_recommendations(
        self,
        metrics: SourceMetrics,
        gaps: List[str],
        topic: str
    ) -> List[str]:
        """Öneriler oluştur."""
        recommendations = []
        
        # Diversity önerileri
        if metrics.diversity_score < 0.5:
            recommendations.append(
                "🔄 Kaynak çeşitliliğini artırın - farklı türde kaynaklar ekleyin"
            )
        
        # Güncellik önerileri
        if metrics.recency_score < 0.5:
            recommendations.append(
                "📅 Daha güncel kaynaklar ekleyin (son 3 yıl)"
            )
        
        # Kalite önerileri
        tier1_ratio = metrics.by_quality.get("tier_1", 0) / max(1, metrics.total_sources)
        if tier1_ratio < 0.2:
            recommendations.append(
                "⭐ Tier-1 akademik kaynakların oranını artırın"
            )
        
        # Gap-based öneriler
        for gap in gaps[:2]:
            recommendations.append(f"📊 {gap} - bu alanda araştırma genişletin")
        
        return recommendations[:5]
    
    def _calculate_quality_score(
        self,
        metrics: SourceMetrics,
        clusters: List[TopicCluster],
        heatmap: Dict[str, Dict[str, float]]
    ) -> float:
        """Genel kalite skoru hesapla (0-100)."""
        score = 0.0
        
        # Kaynak sayısı (max 20 pts)
        source_score = min(20, metrics.total_sources * 2)
        score += source_score
        
        # Çeşitlilik (max 20 pts)
        score += metrics.diversity_score * 20
        
        # Güncellik (max 20 pts)
        score += metrics.recency_score * 20
        
        # Kalite dağılımı (max 20 pts)
        tier1_ratio = metrics.by_quality.get("tier_1", 0) / max(1, metrics.total_sources)
        tier2_ratio = metrics.by_quality.get("tier_2", 0) / max(1, metrics.total_sources)
        quality_ratio = tier1_ratio + tier2_ratio * 0.5
        score += quality_ratio * 20
        
        # Konu kapsamı (max 20 pts)
        if clusters and heatmap:
            avg_coverage = sum(
                sum(v.values()) / max(1, len(v))
                for v in heatmap.values()
            ) / len(heatmap)
            score += avg_coverage * 20
        
        return min(100, round(score, 1))
    
    def to_event(self, report: ResearchAnalyticsReport) -> Dict[str, Any]:
        """WebSocket event formatına dönüştür."""
        return {
            "type": "research_analytics",
            "timestamp": report.generated_at.isoformat(),
            "topic": report.research_topic,
            "quality_score": report.quality_score,
            "source_count": report.source_metrics.total_sources,
            "diversity_score": round(report.source_metrics.diversity_score, 2),
            "recency_score": round(report.source_metrics.recency_score, 2),
            "topic_clusters": [
                {"name": c.name, "count": c.source_count}
                for c in report.topic_clusters
            ],
            "gaps_identified": report.gaps_identified[:3],
            "recommendations": report.recommendations[:3],
            "message": f"📊 Araştırma kalitesi: {report.quality_score}/100"
        }
    
    def generate_markdown_report(self, report: ResearchAnalyticsReport) -> str:
        """Markdown formatında rapor oluştur."""
        md = []
        md.append(f"# 📊 Araştırma Analitiği Raporu")
        md.append(f"**Konu:** {report.research_topic}")
        md.append(f"**Oluşturulma:** {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
        md.append(f"**Kalite Skoru:** {report.quality_score}/100")
        md.append("")
        
        # Kaynak metrikleri
        md.append("## 📚 Kaynak Metrikleri")
        md.append(f"- **Toplam Kaynak:** {report.source_metrics.total_sources}")
        md.append(f"- **Çeşitlilik Skoru:** {report.source_metrics.diversity_score:.2f}")
        md.append(f"- **Güncellik Skoru:** {report.source_metrics.recency_score:.2f}")
        md.append(f"- **Ortalama Atıf:** {report.source_metrics.avg_citation_count:.1f}")
        md.append("")
        
        # Kaynak türü dağılımı
        md.append("### Kaynak Türü Dağılımı")
        for stype, count in report.source_metrics.by_type.items():
            md.append(f"- {stype}: {count}")
        md.append("")
        
        # Konu kümeleri
        md.append("## 🎯 Konu Kümeleri")
        for cluster in report.topic_clusters:
            md.append(f"### {cluster.name}")
            md.append(f"- Kaynak sayısı: {cluster.source_count}")
            md.append(f"- Anahtar kelimeler: {', '.join(cluster.keywords[:5])}")
            if cluster.sub_topics:
                md.append(f"- Alt konular: {', '.join(cluster.sub_topics)}")
            md.append("")
        
        # Boşluklar
        md.append("## ⚠️ Tespit Edilen Boşluklar")
        for gap in report.gaps_identified:
            md.append(f"- {gap}")
        md.append("")
        
        # Öneriler
        md.append("## 💡 Öneriler")
        for rec in report.recommendations:
            md.append(f"- {rec}")
        
        return "\n".join(md)
