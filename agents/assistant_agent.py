"""
Enterprise AI Assistant - Assistant Agent
Endüstri Standartlarında Kurumsal AI Çözümü

Genel asistan - kullanıcı etkileşimi, soru-cevap, yönlendirme.
"""

from typing import Dict, Any, Optional

from .base_agent import BaseAgent, AgentRole, AgentResponse

import sys
sys.path.append('..')

from rag.retriever import retriever


class AssistantAgent(BaseAgent):
    """
    Asistan Agent'ı - Endüstri standartlarına uygun.
    
    Yetenekler:
    - Genel soru-cevap
    - Görev yönlendirme
    - Netleştirme soruları
    - Yardım ve rehberlik
    - Basit sohbet
    """
    
    SYSTEM_PROMPT = """Sen yardımsever, sabırlı ve bilgili bir AI asistansın. Görevin kullanıcılara her konuda yardımcı olmak ve doğru yönlendirmek.

KURALLAR:
1. Her zaman nazik ve profesyonel ol
2. Soruyu tam anlamaya çalış
3. Belirsiz durumlarda netleştirici soru sor
4. Kapsamlı ama öz yanıtlar ver
5. Kaynaklara dayalı bilgi sun
6. Emin olmadığın şeyleri belirt

YANIT YAKLAŞIMI:
1. Soruyu anla
2. Bilgi tabanında ara (gerekirse)
3. Net ve yapılandırılmış yanıt ver
4. Ek yardım öner

KAPASİTELERİN:
- Şirket bilgi tabanında arama
- Genel sorulara cevap
- Karmaşık görevleri diğer uzmanlara yönlendirme
- Kullanım rehberliği

SINIRLAMALAR:
- Bilgi tabanında olmayan konularda tahmin yapma
- Kişisel görüş verme
- Gizli bilgileri açıklamama"""
    
    def __init__(self):
        super().__init__(
            name="Assistant Agent",
            role=AgentRole.ASSISTANT,
            description="Kullanıcılara yardımcı olan genel asistan",
            system_prompt=self.SYSTEM_PROMPT,
        )
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Asistan görevini çalıştır.
        
        Args:
            task: Kullanıcı sorusu/talebi
            context: Ek bağlam
            
        Returns:
            AgentResponse
        """
        try:
            # Determine if we need to search knowledge base
            needs_search = self._needs_knowledge_search(task)
            
            sources = []
            context_text = ""
            
            if needs_search:
                # Search knowledge base
                search_results = retriever.retrieve(query=task, top_k=3)
                
                if search_results:
                    context_text = self._format_context(search_results)
                    sources = list(set(r.source for r in search_results))
            
            # Build prompt
            prompt = self._build_assistant_prompt(task, context_text, context)
            
            # Generate response
            response_text = self.think(prompt, context)
            
            return AgentResponse(
                content=response_text,
                agent_name=self.name,
                agent_role=self.role.value,
                sources=sources,
                metadata={
                    "used_knowledge_base": needs_search and bool(sources),
                    "source_count": len(sources),
                },
            )
            
        except Exception as e:
            return AgentResponse(
                content="Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
                agent_name=self.name,
                agent_role=self.role.value,
                success=False,
                error=str(e),
            )
    
    def _needs_knowledge_search(self, task: str) -> bool:
        """Bilgi tabanında arama gerekip gerekmediğini belirle."""
        task_lower = task.lower()
        
        # Keywords that suggest knowledge search
        search_keywords = [
            "politika", "prosedür", "nasıl", "nedir", "kim",
            "ne zaman", "nerede", "hangi", "kaç", "süreç",
            "döküman", "bilgi", "şirket", "çalışan", "izin",
            "maaş", "rapor", "sözleşme", "proje", "müşteri",
            "policy", "procedure", "how", "what", "who",
            "when", "where", "which", "document", "information",
        ]
        
        # Simple greetings don't need search
        greeting_patterns = [
            "merhaba", "selam", "günaydın", "iyi günler",
            "hello", "hi", "hey", "teşekkür", "thanks",
        ]
        
        # Check if it's just a greeting
        if any(pattern in task_lower and len(task.split()) <= 3 for pattern in greeting_patterns):
            return False
        
        # Check if it needs knowledge search
        return any(keyword in task_lower for keyword in search_keywords)
    
    def _format_context(self, results: list) -> str:
        """Arama sonuçlarını context'e formatla."""
        parts = []
        for i, result in enumerate(results, 1):
            parts.append(f"[Kaynak {i}]: {result.source}")
            parts.append(result.content[:500])  # Limit content length
            parts.append("")
        return "\n".join(parts)
    
    def _build_assistant_prompt(
        self,
        task: str,
        context_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Asistan promptu oluştur."""
        parts = []
        
        if context_text:
            parts.extend([
                "=== BİLGİ TABANINDAN BULUNAN İLGİLİ BİLGİLER ===",
                context_text,
                "",
                "Yukarıdaki bilgileri kullanarak kullanıcının sorusunu yanıtla.",
                "Bilgi tabanında bulunmayan konularda 'Bu konuda bilgi tabanımızda bilgi bulunamadı' de.",
                "",
            ])
        
        if context and "chat_history" in context:
            parts.extend([
                "=== ÖNCEKİ KONUŞMA ===",
                str(context["chat_history"][-5:]),  # Last 5 messages
                "",
            ])
        
        parts.extend([
            "=== KULLANICI SORUSU ===",
            task,
            "",
            "Net, yardımcı ve profesyonel bir yanıt ver.",
        ])
        
        return "\n".join(parts)
    
    def chat(self, message: str, chat_history: Optional[list] = None) -> str:
        """Basit chat interface."""
        context = {}
        if chat_history:
            context["chat_history"] = chat_history
        
        response = self.execute(message, context)
        return response.content
    
    def help(self) -> str:
        """Yardım mesajı döndür."""
        return """🤖 **Enterprise AI Assistant - Yardım**

Ben şirketinizin AI asistanıyım. Size şu konularda yardımcı olabilirim:

📚 **Bilgi Arama**
- Şirket politikaları ve prosedürleri
- Döküman içeriklerinde arama
- Çalışan el kitabı soruları

📝 **İçerik Üretimi**
- Email taslakları
- Rapor hazırlama
- Özet çıkarma

📊 **Analiz**
- Döküman analizi
- Karşılaştırma
- Risk değerlendirme

💡 **Örnek Sorular:**
- "İzin politikamız nedir?"
- "Satış raporunu özetle"
- "Müdüre email taslağı hazırla"

Nasıl yardımcı olabilirim?"""


# Singleton instance
assistant_agent = AssistantAgent()
