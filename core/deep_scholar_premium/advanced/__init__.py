"""
DeepScholar v2.0 - Advanced Premium Modülleri
==============================================

Gelişmiş özellikler:
1. DynamicPageManager - Dinamik sayfa artırma
2. MultiAgentDebate - Çok ajanlı tartışma modu
3. RealTimeStreaming - Gerçek zamanlı güncellemeler
4. OriginalityChecker - Orijinallik kontrolü
5. MultilingualResearch - Çok dilli araştırma
6. ResearchAnalytics - Araştırma analitiği
7. LiteratureReview - Literatür tarama modu
"""

from .dynamic_page_manager import DynamicPageManager
from .multi_agent_debate import MultiAgentDebate, DebateAgent, ConsensusBuilder
from .realtime_streaming import RealTimeStreamingManager, StreamingEvent
from .originality_checker import OriginalityChecker, OriginalityReport
from .multilingual_research import MultilingualResearchEngine
from .research_analytics import ResearchAnalyticsEngine
from .literature_review import LiteratureReviewEngine, PRISMAGenerator

__all__ = [
    "DynamicPageManager",
    "MultiAgentDebate",
    "DebateAgent",
    "ConsensusBuilder",
    "RealTimeStreamingManager",
    "StreamingEvent",
    "OriginalityChecker",
    "OriginalityReport",
    "MultilingualResearchEngine",
    "ResearchAnalyticsEngine",
    "LiteratureReviewEngine",
    "PRISMAGenerator",
]
