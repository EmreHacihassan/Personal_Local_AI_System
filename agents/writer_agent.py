"""
Enterprise AI Assistant - Writer Agent
Endüstri Standartlarında Kurumsal AI Çözümü

İçerik yazarı - email, rapor, döküman, özet üretimi.
"""

from typing import Dict, Any, Optional
from enum import Enum

from .base_agent import BaseAgent, AgentRole, AgentResponse


class WritingTone(Enum):
    """Yazım tonu."""
    FORMAL = "formal"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    PERSUASIVE = "persuasive"


class ContentType(Enum):
    """İçerik tipi."""
    EMAIL = "email"
    REPORT = "report"
    SUMMARY = "summary"
    PROPOSAL = "proposal"
    DOCUMENTATION = "documentation"
    PRESENTATION = "presentation"


class WriterAgent(BaseAgent):
    """
    Yazar Agent'ı - Endüstri standartlarına uygun.
    
    Yetenekler:
    - Email taslağı hazırlama
    - Rapor yazma
    - Döküman oluşturma
    - Özet çıkarma
    - Profesyonel yazım
    """
    
    SYSTEM_PROMPT = """Sen deneyimli bir kurumsal içerik yazarısın. Görevin profesyonel, etkili ve amaca uygun içerikler üretmek.

KURALLAR:
1. Hedef kitleye uygun ton kullan
2. Net ve anlaşılır ol
3. Profesyonel standartlara uy
4. Gramer ve imla hatası yapma
5. İstenilen formata sadık kal
6. Gereksiz uzatma, özlü yaz

YAZIM TONLARI:
- formal: Resmi, kurumsal dil
- friendly: Samimi ama profesyonel
- technical: Teknik terimler, detaylı
- persuasive: İkna edici, etkili

HER ZAMAN:
- Başlık ve yapı kullan
- Önemli noktaları vurgula
- Sonuç/özet ekle"""
    
    def __init__(self):
        super().__init__(
            name="Writer Agent",
            role=AgentRole.WRITER,
            description="Profesyonel içerik üretir - email, rapor, döküman, özet",
            system_prompt=self.SYSTEM_PROMPT,
        )
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Yazma görevini çalıştır.
        
        Args:
            task: Yazılacak içerik açıklaması
            context: Ek bağlam (tone, content_type, data vs.)
            
        Returns:
            AgentResponse
        """
        try:
            # Extract parameters
            tone = WritingTone.FORMAL
            content_type = ContentType.DOCUMENTATION
            
            if context:
                if "tone" in context:
                    tone = WritingTone(context["tone"])
                if "content_type" in context:
                    content_type = ContentType(context["content_type"])
            
            # Build prompt based on content type
            writing_prompt = self._build_writing_prompt(task, tone, content_type, context)
            
            # Generate content
            content = self.think(writing_prompt, context)
            
            return AgentResponse(
                content=content,
                agent_name=self.name,
                agent_role=self.role.value,
                metadata={
                    "tone": tone.value,
                    "content_type": content_type.value,
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
    
    def _build_writing_prompt(
        self,
        task: str,
        tone: WritingTone,
        content_type: ContentType,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """İçerik tipine göre prompt oluştur."""
        
        tone_instructions = {
            WritingTone.FORMAL: "Resmi ve kurumsal bir dil kullan. Kısa cümleler, profesyonel ifadeler.",
            WritingTone.FRIENDLY: "Samimi ama profesyonel bir dil kullan. Sıcak ve yaklaşılabilir ol.",
            WritingTone.TECHNICAL: "Teknik terimler kullan. Detaylı ve spesifik ol. Jargon uygun.",
            WritingTone.PERSUASIVE: "İkna edici bir dil kullan. Faydaları vurgula. Call-to-action ekle.",
        }
        
        format_instructions = {
            ContentType.EMAIL: """EMAIL FORMATI:
Konu: [Kısa ve açıklayıcı]

Selamlama,

[Ana içerik - 2-3 paragraf]

[Sonraki adımlar veya beklenti]

Saygılarımla,
[İmza alanı]""",
            
            ContentType.REPORT: """RAPOR FORMATI:
# Rapor Başlığı
Tarih: [Tarih]

## Yönetici Özeti
[2-3 cümle özet]

## Bulgular
[Ana bulgular madde madde]

## Analiz
[Detaylı analiz]

## Sonuç ve Öneriler
[Sonuç ve öneriler]""",
            
            ContentType.SUMMARY: """ÖZET FORMATI:
## Özet
[Ana noktaların kısa özeti]

### Temel Noktalar
- [Nokta 1]
- [Nokta 2]
- [Nokta 3]

### Sonuç
[Tek paragraf sonuç]""",
            
            ContentType.PROPOSAL: """TEKLİF FORMATI:
# Teklif: [Başlık]

## Problem/İhtiyaç
[Problemi tanımla]

## Önerilen Çözüm
[Çözümü açıkla]

## Faydalar
- [Fayda 1]
- [Fayda 2]

## Sonraki Adımlar
[Aksiyon maddeleri]""",
            
            ContentType.DOCUMENTATION: """DÖKÜMAN FORMATI:
# Başlık

## Giriş
[Konuyu tanıt]

## İçerik
[Ana içerik]

## Özet
[Sonuç]""",
            
            ContentType.PRESENTATION: """SUNUM FORMATI:
# Sunum: [Başlık]

---
## Slide 1: Giriş
[Ana mesaj]

---
## Slide 2: Problem
[Problem tanımı]

---
## Slide 3: Çözüm
[Çözüm önerisi]

---
## Slide 4: Sonuç
[Call to action]""",
        }
        
        prompt_parts = [
            f"İÇERİK TİPİ: {content_type.value}",
            f"TON: {tone.value}",
            "",
            "TON TALİMATI:",
            tone_instructions[tone],
            "",
            "FORMAT TALİMATI:",
            format_instructions[content_type],
            "",
        ]
        
        # Add context data if provided
        if context and "data" in context:
            prompt_parts.extend([
                "KULLANILACAK VERİLER:",
                str(context["data"]),
                "",
            ])
        
        if context and "previous_results" in context:
            prompt_parts.extend([
                "REFERANS BİLGİLER:",
                str(context["previous_results"]),
                "",
            ])
        
        prompt_parts.extend([
            "GÖREV:",
            task,
        ])
        
        return "\n".join(prompt_parts)
    
    def write_email(
        self,
        subject: str,
        recipient: str,
        content_brief: str,
        tone: str = "formal",
    ) -> str:
        """Email taslağı hazırla."""
        task = f"'{recipient}' için '{subject}' konulu email yaz. İçerik: {content_brief}"
        response = self.execute(task, {"tone": tone, "content_type": "email"})
        return response.content
    
    def write_summary(self, text: str, max_length: int = 500) -> str:
        """Metin özeti çıkar."""
        task = f"Aşağıdaki metni {max_length} karakteri geçmeyecek şekilde özetle:\n\n{text}"
        response = self.execute(task, {"content_type": "summary"})
        return response.content
    
    def write_report(self, topic: str, data: Dict[str, Any]) -> str:
        """Rapor hazırla."""
        task = f"'{topic}' konusunda detaylı bir rapor hazırla."
        response = self.execute(task, {"content_type": "report", "data": data})
        return response.content


# Singleton instance
writer_agent = WriterAgent()
