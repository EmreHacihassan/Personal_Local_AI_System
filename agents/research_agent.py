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
    
    SYSTEM_PROMPT = """Sen dünya standartlarında bir AI Eğitmen ve Araştırmacısın. Görevin kullanıcıya konuyu GERÇEKTEN ÖĞRETMEKtir.

## TEMEL PRENSİPLER:
1. **Derinlemesine Açıklama**: Her kavramı "neden" ve "nasıl" boyutlarıyla açıkla
2. **Pratik Örnekler**: Soyut kavramları somut örneklerle destekle
3. **Kod Öğretimi**: Sadece kod gösterme - her satırı açıkla, alternatiflerini sun
4. **Kritik Noktalar**: Yaygın hatalar, best practice'ler ve edge case'leri vurgula
5. **Bağlam**: Konunun büyük resimde nereye oturduğunu açıkla

## YANITLAMA FORMATI:
### 📚 Konu Başlığı
- Konunun tanımı ve önemi
- Neden öğrenilmeli?

### 🎯 Temel Kavramlar
- Her kavram için detaylı açıklama
- Gerçek dünya analojileri
- İlişkili kavramlarla bağlantılar

### 💻 Kod Örnekleri (varsa)
```language
# Her satır için detaylı yorum
code_line  # Bu ne yapıyor, NEDEN yapıyor, alternatifi ne?
```
**Satır Satır Açıklama:**
1. `code_line`: Ne yapar, neden bu şekilde yazılır
2. Alternatif yaklaşımlar ve trade-off'lar
3. Yaygın hatalar ve nasıl kaçınılır

### ⚠️ Dikkat Edilmesi Gerekenler
- **Yaygın Hata 1**: Açıklama ve çözüm
- **Yaygın Hata 2**: Açıklama ve çözüm
- **Best Practice'ler**: Endüstri standartları
- **Edge Case'ler**: Özel durumlar

### 🔄 Adım Adım Uygulama
1. Birinci adım - detaylı açıklama
2. İkinci adım - detaylı açıklama
...

### 🔗 İlişkili Konular
- Bu konuyla bağlantılı kavramlar
- Sonraki öğrenme adımları
- İleri okuma kaynakları

### 📝 Özet
- ✅ Kilit nokta 1
- ✅ Kilit nokta 2
- ✅ Kilit nokta 3

ÖNEMLİ KURALLAR:
- ASLA yüzeysel geçme - her kavramı tam açıkla
- Minimum 1500 kelime hedefle (karmaşık konularda daha fazla)
- Kod varsa her satırı açıkla
- Kaynak belirt ama sadece kopyalama - bilgiyi sentezle ve açıkla"""
    
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
                top_k=30,
                filter_metadata=filter_metadata,
                strategy="hybrid",
            )
            
            if not search_results:
                # Check if this is a personal data query or allows general knowledge
                allow_general = context.get("allow_general_knowledge", True) if context else True
                is_personal = context.get("is_personal_data", False) if context else False
                web_search_enabled = context.get("web_search", False) if context else False
                
                if is_personal and not allow_general:
                    # Strict personal data mode - no general knowledge
                    return AgentResponse(
                        content="📌 **Bilgi Tabanı Araması Sonucu:**\n\nDosyalarınızda/bilgi tabanınızda bu konuyla ilgili bilgi bulunamadı.\n\n💡 **Öneri:** Bu konuyla ilgili dökümanlarınız varsa yükleyebilirsiniz.",
                        agent_name=self.name,
                        agent_role=self.role.value,
                        sources=[],
                        metadata={"search_count": 0, "used_general_knowledge": False},
                    )
                else:
                    # Allow general knowledge fallback
                    fallback_prompt = f"""## KULLANICI SORUSU
{task}

## DURUM
Bilgi tabanında bu konuyla ilgili spesifik içerik bulunamadı.

## GÖREVİN
Genel bilginle KAPSAMLI, DERİNLEMESİNE ve ÖĞRETİCİ bir yanıt ver.

## YANITLAMA FORMATI

### 📚 Konu Başlığı
- Konunun tanımı ve önemi
- Neden öğrenilmesi gerekiyor?

### 🎯 Temel Kavramlar
Her kavram için:
- Detaylı açıklama
- Gerçek dünya örneği/analojisi
- Neden önemli?

### 💻 Kod/Uygulama (varsa)
```language
# Her satır için detaylı yorum
kod_satiri  # Ne yapıyor, NEDEN yapıyor
```
**Satır Satır Açıklama:**
- Her satırın ne yaptığını açıkla
- Alternatif yaklaşımları belirt
- Yaygın hataları göster

### ⚠️ Dikkat Edilmesi Gerekenler
- Yaygın hatalar ve çözümleri
- Best practice'ler
- Edge case'ler

### 📝 Özet
- Kilit noktaların listesi

## UZUNLUK
- Minimum 1500 kelime
- Her kavramı tam açıkla, yüzeysel geçme
- Kod varsa her satırı açıkla"""
                    
                    response_text = self.think(fallback_prompt, {"mode": "general_knowledge"})
                    
                    return AgentResponse(
                        content=response_text,
                        agent_name=self.name,
                        agent_role=self.role.value,
                        sources=[],
                        metadata={"search_count": 0, "used_general_knowledge": True},
                    )
            
            # Build context from results
            context_text = self._format_search_results(search_results)
            
            # Get sources
            sources = list(set(r.source for r in search_results))
            
            # Generate response using LLM
            research_prompt = f"""## 📚 ARAŞTIRMA KAYNAKLARI
{context_text}

## ❓ KULLANICI SORUSU
{task}

## 📝 YANITLAMA TALİMATLARI

### Kaynak Kullanımı:
- Yukarıdaki kaynaklardan BİLGİ SENTEZİ yap
- Her önemli bilgi için [Kaynak X] referansı ver
- Farklı kaynaklardan gelen bilgileri birleştir

### Format Gereksinimleri:
1. **Giriş**: Konunun tanımı ve önemi
2. **Ana İçerik**: 
   - Her kavramı derinlemesine açıkla (sadece tanım değil, NEDEN ve NASIL)
   - Kod varsa: Her satırı açıkla, alternatiflerini göster, yaygın hataları belirt
   - Pratik örnekler ve analojiler kullan
3. **Kritik Noktalar**: Dikkat edilmesi gerekenler, yaygın hatalar, best practice'ler
4. **Özet**: Kilit noktaları listele

### Uzunluk:
- KAPSAMLI ve DETAYLI yanıt ver
- Her önemli kavramı tam olarak açıkla
- Minimum 1200 kelime hedefle"""
            
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
