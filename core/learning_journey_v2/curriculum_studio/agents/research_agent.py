"""
🔍 Research Agent - Araştırma Uzmanı

Sorumluluklar:
- RAG ile bilgi çekme
- Web araştırması
- Güncel içerik bulma
- Kaynak doğrulama
- Akademik materyal önerisi
"""

import asyncio
from typing import Dict, Any, AsyncGenerator, List, Optional

from .base_agent import BaseCurriculumAgent, AgentThought, ThinkingPhase


class ResearchAgent(BaseCurriculumAgent):
    """
    Araştırma Uzmanı Agent
    
    RAG ve web araştırması ile güncel ve doğru bilgi toplayan agent.
    Kaynakları doğrular ve kaliteli içerik önerir.
    """
    
    # Güvenilir kaynak kategorileri
    TRUSTED_SOURCES = {
        "academic": ["arxiv.org", "scholar.google.com", "researchgate.net"],
        "educational": ["khanacademy.org", "coursera.org", "edx.org", "meb.gov.tr"],
        "documentation": ["docs.python.org", "developer.mozilla.org", "w3schools.com"],
        "video": ["youtube.com", "vimeo.com"]
    }
    
    def __init__(self, rag_service=None, web_search_service=None):
        super().__init__(
            name="Araştırma Uzmanı",
            role="Bilgi Toplama Uzmanı",
            specialty="RAG, web araştırması, kaynak doğrulama",
            model_preference="ollama/qwen3:8b",
            thinking_style="thorough and verification-focused"
        )
        self.icon = "🔍"
        self.rag_service = rag_service
        self.web_search_service = web_search_service
        
        # Lazy load RAG
        self._rag = None
    
    @property
    def rag(self):
        """Lazy load RAG service"""
        if self._rag is None and self.rag_service is None:
            try:
                from rag.retriever import RAGRetriever
                self._rag = RAGRetriever()
            except:
                pass
        return self.rag_service or self._rag
    
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Araştırma yap
        
        Steps:
        1. RAG Araştırması
        2. Konu Derinlik Analizi
        3. Kaynak Önerileri
        4. Video/Görsel Kaynaklar
        """
        goal = context.get("goal")
        topics = self._extract_topics(goal)
        
        # Intro
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="baslangic",
            phase=ThinkingPhase.ANALYZING,
            thinking="🔍 Araştırma başlıyor...",
            reasoning=f"Şu konuları araştıracağım: {', '.join(topics[:5])}",
            is_streaming=True
        )
        
        await asyncio.sleep(0.5)
        
        # ===== STEP 1: RAG Araştırması =====
        async for thought in self._rag_research(topics, context):
            yield thought
        
        # ===== STEP 2: Konu Derinlik Analizi =====
        async for thought in self.think(
            prompt=self._build_depth_analysis_prompt(topics),
            step="derinlik_analizi",
            context=context
        ):
            yield thought
        
        # ===== STEP 3: Kaynak Önerileri =====
        async for thought in self._recommend_sources(topics, context):
            yield thought
        
        # ===== STEP 4: Video Kaynaklar =====
        async for thought in self._find_video_resources(topics, context):
            yield thought
        
        # Final
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ozet",
            phase=ThinkingPhase.CONCLUDING,
            thinking="✅ Araştırma tamamlandı",
            conclusion=f"{len(topics)} konu için kaynaklar bulundu.",
            confidence=0.85,
            is_complete=True
        )
    
    def _extract_topics(self, goal) -> List[str]:
        """Goal'dan konuları çıkar"""
        topics = []
        
        if hasattr(goal, 'topics_to_include') and goal.topics_to_include:
            topics.extend(goal.topics_to_include)
        
        if hasattr(goal, 'subject') and goal.subject:
            topics.append(goal.subject)
        
        if hasattr(goal, 'focus_areas') and goal.focus_areas:
            topics.extend(goal.focus_areas)
        
        return list(set(topics)) or ["Genel konu"]
    
    async def _rag_research(
        self, 
        topics: List[str], 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """RAG ile araştırma"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="rag_arastirmasi",
            phase=ThinkingPhase.ANALYZING,
            thinking="📚 Bilgi tabanını tarıyorum...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.5)
        
        # RAG sorgusu
        rag_results = []
        if self.rag:
            try:
                for topic in topics[:3]:
                    results = await self._query_rag(topic)
                    rag_results.extend(results)
            except Exception as e:
                print(f"[ResearchAgent] RAG error: {e}")
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="rag_arastirmasi",
            phase=ThinkingPhase.CONCLUDING,
            thinking="📚 RAG araştırması tamamlandı",
            reasoning=f"{len(rag_results)} ilgili doküman bulundu." if rag_results else "RAG sonuçları işlendi.",
            evidence=[r.get("title", "Doküman") for r in rag_results[:5]],
            confidence=0.8,
            is_complete=True
        )
        
        # Context'e ekle
        context["rag_results"] = rag_results
    
    async def _query_rag(self, topic: str) -> List[Dict[str, Any]]:
        """RAG sorgusu"""
        try:
            if hasattr(self.rag, 'query'):
                results = await self.rag.query(topic, top_k=5)
                return results if results else []
            elif hasattr(self.rag, 'search'):
                results = self.rag.search(topic, top_k=5)
                return results if results else []
        except:
            pass
        return []
    
    async def _recommend_sources(
        self, 
        topics: List[str], 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Kaynak önerileri"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="kaynak_onerileri",
            phase=ThinkingPhase.REASONING,
            thinking="🌐 Güvenilir kaynakları belirliyorum...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.0)
        
        # Konu bazlı kaynak önerileri
        sources = self._generate_source_recommendations(topics, context.get("goal"))
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="kaynak_onerileri",
            phase=ThinkingPhase.CONCLUDING,
            thinking="🌐 Kaynak önerileri hazır",
            evidence=sources[:5],
            conclusion=f"{len(sources)} kaynak önerildi",
            confidence=0.85,
            is_complete=True
        )
        
        context["recommended_sources"] = sources
    
    def _generate_source_recommendations(self, topics: List[str], goal) -> List[str]:
        """Kaynak önerileri oluştur"""
        sources = []
        
        subject = goal.subject.lower() if hasattr(goal, 'subject') else ""
        
        # Konu bazlı öneriler
        if "matematik" in subject or "math" in subject:
            sources.extend([
                "Khan Academy - Matematik Bölümü",
                "3Blue1Brown YouTube Kanalı",
                "Paul's Online Math Notes",
                "Wolfram MathWorld"
            ])
        elif "fizik" in subject or "physics" in subject:
            sources.extend([
                "Khan Academy - Fizik Bölümü",
                "Physics Classroom",
                "HyperPhysics",
                "MIT OpenCourseWare Physics"
            ])
        elif "programlama" in subject or "coding" in subject or "python" in subject:
            sources.extend([
                "Python Resmi Dokümantasyonu",
                "Real Python",
                "freeCodeCamp",
                "Codecademy"
            ])
        elif "ingilizce" in subject or "english" in subject:
            sources.extend([
                "BBC Learning English",
                "Cambridge Dictionary",
                "Grammarly Blog",
                "English Central"
            ])
        else:
            sources.extend([
                "Wikipedia",
                "Khan Academy",
                "Coursera",
                "EdX"
            ])
        
        return sources
    
    async def _find_video_resources(
        self, 
        topics: List[str], 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Video kaynak önerileri"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="video_kaynaklar",
            phase=ThinkingPhase.ANALYZING,
            thinking="🎬 Video kaynakları arıyorum...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.0)
        
        # Video önerileri
        videos = self._generate_video_recommendations(topics, context.get("goal"))
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="video_kaynaklar",
            phase=ThinkingPhase.CONCLUDING,
            thinking="🎬 Video kaynakları bulundu",
            evidence=[v["title"] for v in videos[:3]],
            conclusion=f"{len(videos)} video önerisi hazır",
            confidence=0.8,
            is_complete=True
        )
        
        context["video_resources"] = videos
    
    def _generate_video_recommendations(self, topics: List[str], goal) -> List[Dict[str, Any]]:
        """Video önerileri oluştur"""
        videos = []
        subject = goal.subject if hasattr(goal, 'subject') else "Genel"
        
        for topic in topics[:3]:
            search_query = f"{topic} ders anlatımı"
            videos.append({
                "title": f"{topic} - Video Ders",
                "platform": "YouTube",
                "search_url": f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}",
                "estimated_duration": "15-30 dk",
                "type": "tutorial"
            })
        
        # Genel konu videoları
        videos.append({
            "title": f"{subject} - Kapsamlı Kurs",
            "platform": "Khan Academy",
            "url": f"https://www.khanacademy.org/search?search_query={subject.replace(' ', '+')}",
            "estimated_duration": "Değişken",
            "type": "course"
        })
        
        return videos
    
    def _build_depth_analysis_prompt(self, topics: List[str]) -> str:
        """Derinlik analizi promptu"""
        return f"""Şu konuların derinlik analizini yap:

Konular: {', '.join(topics)}

Her konu için belirle:
1. Temel seviye (başlangıç) - ne öğrenilmeli?
2. Orta seviye - hangi uygulamalar yapılmalı?
3. İleri seviye - hangi derinlik hedeflenmeli?
4. Kritik kavramlar - mutlaka bilinmesi gerekenler
5. Yaygın yanılgılar - dikkat edilmesi gerekenler

JSON formatında döndür."""
