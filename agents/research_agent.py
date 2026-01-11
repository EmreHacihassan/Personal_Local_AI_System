"""
Enterprise AI Assistant - Research Agent
Endüstri Standartlarında Kurumsal AI Çözümü

Araştırma uzmanı - bilgi arama, kaynak toplama, çapraz kontrol.
"""

from typing import Dict, Any, Optional, List

from .base_agent import BaseAgent, AgentRole, AgentResponse

import sys
sys.path.append('..')

from rag.retriever import retriever


class ResearchAgent(BaseAgent):
    """
    Araştırma Agent'ı - Endüstri standartlarına uygun.
    
    Yetenekler:
    - Bilgi tabanında arama
    - Çoklu kaynak toplama
    - Çapraz kontrol
    - Kaynak gösterimi
    """
    
    SYSTEM_PROMPT = """Sen şirketin deneyimli araştırma uzmanısın. Görevin şirketin bilgi tabanında kapsamlı ve doğru araştırma yapmak.

KURALLAR:
1. Sadece bilgi tabanında bulunan bilgileri kullan
2. Her bilgi için kaynak göster
3. Bulamadığın bilgiyi açıkça belirt - tahmin yapma
4. Birden fazla kaynağı çapraz kontrol et
5. En güncel bilgiyi öncelikle sun
6. Gizli/hassas verilere dikkat et

YANIT FORMATI:
- Net ve anlaşılır ol
- Kaynakları her zaman belirt
- Emin olmadığın konularda "Bu bilgiyi bulamadım" de
- Önemli noktaları vurgula"""
    
    def __init__(self):
        super().__init__(
            name="Research Agent",
            role=AgentRole.RESEARCH,
            description="Bilgi tabanında araştırma yapar ve kaynaklarla desteklenmiş cevaplar sunar",
            system_prompt=self.SYSTEM_PROMPT,
        )
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Araştırma görevini çalıştır.
        
        Args:
            task: Araştırılacak konu/soru
            context: Ek bağlam (filter_metadata vs.)
            
        Returns:
            AgentResponse
        """
        try:
            # Extract filter if provided
            filter_metadata = None
            if context and "filter_metadata" in context:
                filter_metadata = context["filter_metadata"]
            
            # Search in knowledge base
            search_results = retriever.retrieve(
                query=task,
                top_k=5,
                filter_metadata=filter_metadata,
                strategy="hybrid",
            )
            
            if not search_results:
                return AgentResponse(
                    content="Bu konuda bilgi tabanında herhangi bir bilgi bulunamadı.",
                    agent_name=self.name,
                    agent_role=self.role.value,
                    sources=[],
                    metadata={"search_count": 0},
                )
            
            # Build context from results
            context_text = self._format_search_results(search_results)
            
            # Get sources
            sources = list(set(r.source for r in search_results))
            
            # Generate response using LLM
            research_prompt = f"""Aşağıdaki kaynaklara dayanarak soruyu yanıtla:

{context_text}

SORU: {task}

KURALLAR:
- Sadece yukarıdaki kaynaklardaki bilgileri kullan
- Her önemli bilgi için kaynak belirt (örn: [Kaynak 1])
- Kaynakta olmayan bilgi verme
- Net ve kapsamlı yanıt ver"""
            
            response_text = self.think(research_prompt, {"documents": context_text})
            
            return AgentResponse(
                content=response_text,
                agent_name=self.name,
                agent_role=self.role.value,
                sources=sources,
                metadata={
                    "search_count": len(search_results),
                    "top_score": search_results[0].score if search_results else 0,
                },
            )
            
        except Exception as e:
            return AgentResponse(
                content="",
                agent_name=self.name,
                agent_role=self.role.value,
                success=False,
                error=str(e),
            )
    
    def _format_search_results(self, results: List[Any]) -> str:
        """Arama sonuçlarını formatla."""
        parts = []
        
        for i, result in enumerate(results, 1):
            parts.append(f"[Kaynak {i}] {result.source}")
            parts.append(f"Skor: {result.score:.2f}")
            parts.append("-" * 40)
            parts.append(result.content)
            parts.append("-" * 40)
            parts.append("")
        
        return "\n".join(parts)
    
    def quick_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Hızlı arama - sadece sonuçları döndür."""
        results = retriever.retrieve(query=query, top_k=top_k)
        return [r.to_dict() for r in results]
    
    def find_sources(self, query: str) -> List[str]:
        """Sadece kaynak listesi döndür."""
        return retriever.get_sources(query)


# Singleton instance
research_agent = ResearchAgent()
