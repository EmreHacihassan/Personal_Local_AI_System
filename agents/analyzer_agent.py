"""
Enterprise AI Assistant - Analyzer Agent
Endüstri Standartlarında Kurumsal AI Çözümü

Veri analisti - analiz, karşılaştırma, trend tespiti, insight üretimi.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from .base_agent import BaseAgent, AgentRole, AgentResponse


class AnalysisType(Enum):
    """Analiz tipleri."""
    SUMMARIZATION = "summarization"
    COMPARISON = "comparison"
    EXTRACTION = "extraction"
    TREND_ANALYSIS = "trend_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    GAP_ANALYSIS = "gap_analysis"


class AnalyzerAgent(BaseAgent):
    """
    Analizci Agent'ı - Endüstri standartlarına uygun.
    
    Yetenekler:
    - Döküman analizi ve özetleme
    - Karşılaştırmalı analiz
    - Bilgi çıkarma (extraction)
    - Trend analizi
    - Risk değerlendirme
    - Boşluk analizi
    """
    
    SYSTEM_PROMPT = """Sen analitik düşünen, detaycı bir veri analistisin. Görevin dökümanları ve verileri analiz ederek değerli içgörüler çıkarmak.

KURALLAR:
1. Önce genel resme bak, sonra detaylara in
2. Kritik noktaları belirle ve vurgula
3. Sayısal verileri yorumla
4. Karşılaştırmalar yap
5. Somut önerilerde bulun
6. Varsayımlarını belirt

ANALİZ YAKLAŞIMI:
1. Veriyi anla
2. Kalıpları tespit et
3. Anormallikleri bul
4. İlişkileri kur
5. Sonuç çıkar
6. Öneri sun

ÇIKTI FORMATI:
- Yapılandırılmış ve okunabilir
- Bullet point'ler kullan
- Önemli bulguları vurgula
- Her zaman sonuç bölümü ekle"""
    
    def __init__(self):
        super().__init__(
            name="Analyzer Agent",
            role=AgentRole.ANALYZER,
            description="Veri ve döküman analizi yapar, içgörüler çıkarır",
            system_prompt=self.SYSTEM_PROMPT,
        )
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Analiz görevini çalıştır.
        
        Args:
            task: Analiz görevi
            context: Ek bağlam (analysis_type, data vs.)
            
        Returns:
            AgentResponse
        """
        try:
            # Determine analysis type
            analysis_type = AnalysisType.SUMMARIZATION
            if context and "analysis_type" in context:
                analysis_type = AnalysisType(context["analysis_type"])
            
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(task, analysis_type, context)
            
            # Generate analysis
            analysis = self.think(analysis_prompt, context)
            
            return AgentResponse(
                content=analysis,
                agent_name=self.name,
                agent_role=self.role.value,
                metadata={
                    "analysis_type": analysis_type.value,
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
    
    def _build_analysis_prompt(
        self,
        task: str,
        analysis_type: AnalysisType,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Analiz tipine göre prompt oluştur."""
        
        analysis_instructions = {
            AnalysisType.SUMMARIZATION: """ÖZETLEME ANALİZİ:
1. Ana temaları belirle
2. Kritik noktaları çıkar
3. Gereksiz detayları ele
4. Mantıksal sıra ile özetle

ÇIKTI:
## Özet
[Genel özet]

## Ana Noktalar
- [Nokta 1]
- [Nokta 2]

## Sonuç
[Tek paragraf sonuç]""",
            
            AnalysisType.COMPARISON: """KARŞILAŞTIRMA ANALİZİ:
1. Karşılaştırılacak öğeleri belirle
2. Ortak kriterleri tanımla
3. Her öğeyi kriterlere göre değerlendir
4. Benzerlikleri ve farklılıkları listele

ÇIKTI:
## Karşılaştırma

| Kriter | Öğe A | Öğe B |
|--------|-------|-------|
| ... | ... | ... |

## Benzerlikler
- ...

## Farklılıklar
- ...

## Değerlendirme
[Hangi durumda hangisi tercih edilmeli]""",
            
            AnalysisType.EXTRACTION: """BİLGİ ÇIKARMA ANALİZİ:
1. Hedef bilgi türlerini belirle
2. Metni tara
3. İlgili bilgileri çıkar
4. Yapılandır

ÇIKTI:
## Çıkarılan Bilgiler

### Kategori 1
- Bilgi: [değer]
- Kaynak: [nereden çıkarıldı]

### Kategori 2
- ...

## Bulunamayan Bilgiler
- [Eksik bilgiler listesi]""",
            
            AnalysisType.TREND_ANALYSIS: """TREND ANALİZİ:
1. Zaman serisi verilerini incele
2. Kalıpları tespit et
3. Yön ve hızı belirle
4. Gelecek tahmini yap

ÇIKTI:
## Trend Analizi

### Mevcut Durum
[Şu anki durum özeti]

### Tespit Edilen Trendler
1. [Trend 1]: [yön] - [etki]
2. [Trend 2]: ...

### Tahminler
- Kısa vadeli: ...
- Orta vadeli: ...

### Öneriler
- ...""",
            
            AnalysisType.RISK_ASSESSMENT: """RİSK DEĞERLENDİRME ANALİZİ:
1. Potansiyel riskleri belirle
2. Her risk için olasılık ve etki değerlendir
3. Önceliklendirme yap
4. Azaltma stratejileri öner

ÇIKTI:
## Risk Değerlendirmesi

### Yüksek Riskler 🔴
| Risk | Olasılık | Etki | Azaltma |
|------|----------|------|---------|
| ... | ... | ... | ... |

### Orta Riskler 🟡
| ... | ... | ... | ... |

### Düşük Riskler 🟢
| ... | ... | ... | ... |

### Genel Değerlendirme
[Risk skoru ve özet]""",
            
            AnalysisType.GAP_ANALYSIS: """BOŞLUK ANALİZİ:
1. Mevcut durumu tanımla
2. Hedef durumu tanımla
3. Boşlukları belirle
4. Kapama stratejileri öner

ÇIKTI:
## Boşluk Analizi

### Mevcut Durum
[Şu anki durum]

### Hedef Durum
[Olması gereken durum]

### Tespit Edilen Boşluklar
1. [Boşluk 1]
   - Mevcut: ...
   - Hedef: ...
   - Fark: ...

### Kapama Stratejileri
1. [Boşluk 1 için]: ...
2. ...

### Öncelikli Aksiyonlar
- [ ] ...
- [ ] ...""",
        }
        
        prompt_parts = [
            f"ANALİZ TİPİ: {analysis_type.value}",
            "",
            "TALİMATLAR:",
            analysis_instructions[analysis_type],
            "",
        ]
        
        # Add data if provided
        if context and "data" in context:
            prompt_parts.extend([
                "ANALİZ EDİLECEK VERİ:",
                str(context["data"]),
                "",
            ])
        
        if context and "documents" in context:
            prompt_parts.extend([
                "ANALİZ EDİLECEK DÖKÜMANLAR:",
                str(context["documents"]),
                "",
            ])
        
        prompt_parts.extend([
            "GÖREV:",
            task,
        ])
        
        return "\n".join(prompt_parts)
    
    def summarize(self, text: str) -> str:
        """Metin özetle."""
        response = self.execute(
            f"Bu metni özetle:\n\n{text}",
            {"analysis_type": "summarization"}
        )
        return response.content
    
    def compare(self, items: List[str], criteria: Optional[List[str]] = None) -> str:
        """Öğeleri karşılaştır."""
        task = f"Şu öğeleri karşılaştır: {', '.join(items)}"
        if criteria:
            task += f"\nKriterler: {', '.join(criteria)}"
        
        response = self.execute(task, {"analysis_type": "comparison"})
        return response.content
    
    def extract_info(self, text: str, info_types: List[str]) -> str:
        """Belirli bilgileri çıkar."""
        task = f"Bu metinden şu bilgileri çıkar: {', '.join(info_types)}\n\nMetin:\n{text}"
        response = self.execute(task, {"analysis_type": "extraction"})
        return response.content
    
    def assess_risks(self, scenario: str) -> str:
        """Risk değerlendirmesi yap."""
        response = self.execute(
            f"Bu senaryo için risk değerlendirmesi yap:\n\n{scenario}",
            {"analysis_type": "risk_assessment"}
        )
        return response.content


# Singleton instance
analyzer_agent = AnalyzerAgent()
