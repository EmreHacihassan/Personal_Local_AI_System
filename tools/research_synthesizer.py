"""
🧠 AI Research Synthesizer
==========================

Web arama sonuçlarını AI ile sentezleyen ve kaliteli yanıt üreten motor.

Özellikler:
- Multi-source sentez
- Fact-checking ve çapraz doğrulama
- Structured output (başlıklar, maddeler, tablolar)
- Citation management
- Follow-up soru önerileri
- Güvenilirlik değerlendirmesi
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class ResponseStyle(Enum):
    """Yanıt stili"""
    COMPREHENSIVE = "comprehensive"  # Detaylı, uzun yanıt
    CONCISE = "concise"  # Kısa, öz yanıt
    ACADEMIC = "academic"  # Akademik, kaynak odaklı
    CONVERSATIONAL = "conversational"  # Sohbet tarzı
    STRUCTURED = "structured"  # Maddeli, yapılandırılmış


class QueryIntent(Enum):
    """Sorgu amacı"""
    FACTUAL = "factual"  # Fact-based sorular
    EXPLANATORY = "explanatory"  # Açıklama isteyen
    COMPARATIVE = "comparative"  # Karşılaştırma
    PROCEDURAL = "procedural"  # Nasıl yapılır
    OPINION = "opinion"  # Görüş/öneri
    DEFINITION = "definition"  # Tanım
    LIST = "list"  # Liste
    CURRENT_EVENTS = "current_events"  # Güncel olaylar


@dataclass
class ResearchContext:
    """Araştırma bağlamı"""
    query: str
    intent: QueryIntent
    style: ResponseStyle
    language: str = "tr"
    sources: List[Dict] = field(default_factory=list)
    instant_answer: Optional[Dict] = None
    knowledge_panel: Optional[Dict] = None
    key_facts: List[str] = field(default_factory=list)
    conflicting_info: List[Dict] = field(default_factory=list)
    source_summary: Dict[str, int] = field(default_factory=dict)


@dataclass
class SynthesizedResponse:
    """Sentezlenmiş yanıt"""
    main_content: str
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    citations: List[Dict] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    confidence_score: float = 0.8
    sources_used: int = 0
    word_count: int = 0
    has_conflicting_info: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueryAnalyzer:
    """Sorgu analizi ve intent tespiti"""
    
    # Intent patterns
    INTENT_PATTERNS = {
        QueryIntent.DEFINITION: [
            r'nedir\?*$', r'ne demek', r'tanımı', r'anlamı', r'what is',
            r'ne anlama', r'açıkla\b', r'define'
        ],
        QueryIntent.PROCEDURAL: [
            r'nasıl', r'how to', r'adımlar', r'steps', r'yapılır',
            r'öğren', r'yöntem', r'guide', r'tutorial', r'tarif'
        ],
        QueryIntent.COMPARATIVE: [
            r'karşılaştır', r'fark\w*\s+nedir', r'vs\.?', r'versus',
            r'hangisi', r'which', r'compare', r'difference', r'mı\s+yoksa',
            r'arasındaki fark', r'better'
        ],
        QueryIntent.LIST: [
            r'listele', r'sırala', r'list', r'top \d+', r'en iyi',
            r'örnekler', r'türleri', r'çeşitleri', r'types', r'examples'
        ],
        QueryIntent.OPINION: [
            r'öneri', r'tavsiye', r'düşün', r'görüş', r'should',
            r'recommend', r'suggest', r'best', r'ideal'
        ],
        QueryIntent.CURRENT_EVENTS: [
            r'bugün', r'son\s+dakika', r'güncel', r'latest', r'recent',
            r'2024', r'2025', r'2026', r'şu an', r'news'
        ],
        QueryIntent.EXPLANATORY: [
            r'neden', r'niçin', r'why', r'sebebi', r'reason',
            r'açıkl', r'explain', r'anlat'
        ],
    }
    
    # Style patterns
    STYLE_PATTERNS = {
        ResponseStyle.COMPREHENSIVE: [
            r'detay', r'ayrıntı', r'kapsamlı', r'detailed', r'comprehensive',
            r'her şey', r'tüm', r'all about'
        ],
        ResponseStyle.CONCISE: [
            r'kısa', r'öz', r'brief', r'özet', r'summary', r'quick',
            r'hızlı', r'shortly'
        ],
        ResponseStyle.ACADEMIC: [
            r'akademik', r'bilimsel', r'scientific', r'research',
            r'araştırma', r'kaynak', r'citation'
        ],
        ResponseStyle.STRUCTURED: [
            r'madde', r'liste', r'organize', r'structured',
            r'bullet', r'step by step'
        ]
    }
    
    def analyze(self, query: str) -> Tuple[QueryIntent, ResponseStyle]:
        """Sorguyu analiz et"""
        query_lower = query.lower()
        
        # Intent tespiti
        intent = QueryIntent.FACTUAL  # Default
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    intent = intent_type
                    break
        
        # Style tespiti
        style = ResponseStyle.COMPREHENSIVE  # Default
        for style_type, patterns in self.STYLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    style = style_type
                    break
        
        # Intent'e göre style ayarla
        if intent == QueryIntent.LIST:
            style = ResponseStyle.STRUCTURED
        elif intent == QueryIntent.DEFINITION:
            style = ResponseStyle.CONCISE
        
        return intent, style


class SourceAggregator:
    """Kaynak toplama ve birleştirme"""
    
    def aggregate(self, search_response: Dict) -> ResearchContext:
        """Kaynakları topla ve analiz et"""
        query = search_response.get("query", "")
        
        # Query analizi
        analyzer = QueryAnalyzer()
        intent, style = analyzer.analyze(query)
        
        context = ResearchContext(
            query=query,
            intent=intent,
            style=style,
            sources=[],
            instant_answer=search_response.get("instant_answer"),
            knowledge_panel=search_response.get("knowledge_panel")
        )
        
        # Sonuçları işle
        for result in search_response.get("results", []):
            source = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "domain": result.get("domain", ""),
                "content": result.get("content", "") or result.get("snippet", ""),
                "type": result.get("type", "unknown"),
                "reliability": result.get("reliability", 0.5),
                "snippet": result.get("snippet", "")
            }
            context.sources.append(source)
            
            # Kaynak türü istatistiği
            source_type = source["type"]
            context.source_summary[source_type] = context.source_summary.get(source_type, 0) + 1
        
        # Key facts çıkar
        context.key_facts = self._extract_key_facts(context)
        
        # Çelişkili bilgileri tespit et
        context.conflicting_info = self._find_conflicts(context)
        
        return context
    
    def _extract_key_facts(self, context: ResearchContext) -> List[str]:
        """Önemli bilgileri çıkar"""
        facts = []
        
        # Instant answer'dan
        if context.instant_answer:
            abstract = context.instant_answer.get("abstract", "")
            if abstract:
                # İlk 2 cümle
                sentences = re.split(r'[.!?]', abstract)
                facts.extend([s.strip() + "." for s in sentences[:2] if s.strip()])
        
        # Yüksek güvenilirlikli kaynaklardan
        for source in context.sources:
            if source["reliability"] >= 0.7 and source["content"]:
                content = source["content"]
                # Önemli cümleler (sayılar, tarihler içeren)
                sentences = re.split(r'[.!?]', content)
                for s in sentences[:5]:
                    s = s.strip()
                    if len(s) > 30 and (
                        re.search(r'\d+', s) or  # Sayı içeren
                        re.search(r'\b(önemli|kritik|temel|ana|key|important)\b', s.lower())
                    ):
                        facts.append(s + ".")
        
        return list(set(facts))[:10]
    
    def _find_conflicts(self, context: ResearchContext) -> List[Dict]:
        """Çelişkili bilgileri bul"""
        conflicts = []
        
        # Basit çelişki tespiti - sayılar arasında büyük fark
        numbers_by_topic = {}
        
        for source in context.sources:
            content = source["content"]
            if not content:
                continue
            
            # Sayıları ve bağlamlarını bul
            matches = re.findall(r'(\w+)\s+(\d+(?:[.,]\d+)?)', content)
            for topic, number in matches:
                if topic not in numbers_by_topic:
                    numbers_by_topic[topic] = []
                try:
                    num = float(number.replace(",", "."))
                    numbers_by_topic[topic].append({
                        "value": num,
                        "source": source["domain"]
                    })
                except:
                    pass
        
        # Büyük farklılıkları raporla
        for topic, values in numbers_by_topic.items():
            if len(values) >= 2:
                nums = [v["value"] for v in values]
                if max(nums) > min(nums) * 2:  # 2 kattan fazla fark
                    conflicts.append({
                        "topic": topic,
                        "values": values,
                        "note": "Kaynaklarda farklı değerler var"
                    })
        
        return conflicts[:5]


class PromptBuilder:
    """AI için prompt oluşturma"""
    
    def build_system_prompt(self, context: ResearchContext) -> str:
        """Sistem promptu oluştur"""
        
        intent_instructions = {
            QueryIntent.DEFINITION: "Tanım ve açıklama odaklı, net ve anlaşılır yanıt ver.",
            QueryIntent.PROCEDURAL: "Adım adım, pratik ve uygulanabilir yanıt ver.",
            QueryIntent.COMPARATIVE: "Karşılaştırmalı, artı/eksi yönleri belirten yanıt ver.",
            QueryIntent.LIST: "Düzenli, maddeli ve kategorize edilmiş yanıt ver.",
            QueryIntent.OPINION: "Dengeli, çoklu perspektif sunan yanıt ver.",
            QueryIntent.CURRENT_EVENTS: "Güncel ve doğrulanabilir bilgilerle yanıt ver.",
            QueryIntent.EXPLANATORY: "Sebep-sonuç ilişkisi kurarak açıklayıcı yanıt ver.",
            QueryIntent.FACTUAL: "Doğru, kaynak destekli ve nesnel yanıt ver."
        }
        
        style_instructions = {
            ResponseStyle.COMPREHENSIVE: """
- Konuyu derinlemesine ele al
- Farklı açılardan incele
- Örnekler ve detaylar ekle
- Minimum 400-500 kelime kullan
""",
            ResponseStyle.CONCISE: """
- Kısa ve öz ol
- Sadece en önemli bilgileri ver
- Gereksiz detaylardan kaçın
- 150-200 kelime yeterli
""",
            ResponseStyle.ACADEMIC: """
- Akademik dil kullan
- Kaynaklara atıf yap [1], [2] şeklinde
- Metodolojik yaklaş
- Eleştirel değerlendirme yap
""",
            ResponseStyle.STRUCTURED: """
- Başlıklar ve alt başlıklar kullan
- Madde işaretleri ile listele
- Tablolar ve karşılaştırmalar ekle
- Görsel hiyerarşi oluştur
""",
            ResponseStyle.CONVERSATIONAL: """
- Samimi ve anlaşılır dil kullan
- Jargondan kaçın veya açıkla
- Sorular sor, etkileşim kur
"""
        }
        
        # Kaynak özeti
        source_types = ", ".join([f"{k}({v})" for k, v in context.source_summary.items()])
        
        # Çelişki uyarısı
        conflict_note = ""
        if context.conflicting_info:
            conflict_note = "\n⚠️ UYARI: Bazı kaynaklarda çelişkili bilgiler var. Bunu yanıtta belirt."
        
        return f"""Sen dünya standartlarında bir araştırma asistanısın. Perplexity AI kalitesinde yanıtlar üretiyorsun.

## 📋 GÖREV
Kullanıcının sorusuna kapsamlı, doğru ve kaynak destekli yanıt ver.

## 🎯 SORGU ANALİZİ
- **Amaç:** {context.intent.value} ({intent_instructions.get(context.intent, '')})
- **Kaynak Dağılımı:** {source_types or 'Çeşitli'}
- **Dil:** Türkçe
{conflict_note}

## 📝 YANITLAMA STİLİ
{style_instructions.get(context.style, style_instructions[ResponseStyle.COMPREHENSIVE])}

## 🔖 KAYNAK KULLANIMI
1. Her önemli bilgiyi kaynak numarası ile destekle: "Bu konuda... [1]"
2. Wikipedia ve resmi kaynakları öncelikle kullan
3. Çelişen bilgilerde her iki görüşü de belirt
4. Emin olmadığın bilgileri "bazı kaynaklara göre" şeklinde sun

## 📐 FORMAT
### Yanıt Yapısı:
1. **Özet** (2-3 cümle): Sorunun doğrudan cevabı
2. **Detaylı Açıklama**: Alt başlıklar ile organize
3. **Önemli Noktalar**: Maddeli liste
4. **Kaynaklar**: Otomatik eklenecek, yanıtta yazma

### Markdown Kullanımı:
- **Kalın** önemli kavramlar için
- `kod` teknik terimler için
- > Alıntı önemli bilgiler için
- Tablolar karşılaştırmalar için

## ⚠️ ÖNEMLİ KURALLAR
1. ASLA uydurma bilgi verme
2. Kaynaklarda olmayan bilgiyi "genel bilgi" olarak sun
3. Güncel tarih/istatistiklerde dikkatli ol
4. Yanıt sonunda kaynak listesi YAZMA (otomatik gösterilecek)
5. Soruyu direkt cevapla, uzun giriş yapma
"""

    def build_user_prompt(self, context: ResearchContext) -> str:
        """Kullanıcı promptu oluştur"""
        
        parts = []
        
        # Soru
        parts.append(f"## ❓ SORU\n{context.query}\n")
        
        # Instant Answer
        if context.instant_answer:
            ia = context.instant_answer
            parts.append(f"""
## 📌 HIZLI REFERANS (Wikipedia/Ansiklopedi)
**{ia.get('title', '')}**
{ia.get('abstract', '')}
Kaynak: {ia.get('source', '')}
""")
        
        # Key Facts
        if context.key_facts:
            facts = "\n".join([f"• {f}" for f in context.key_facts[:5]])
            parts.append(f"""
## 🔑 ÖNEMLİ BİLGİLER
{facts}
""")
        
        # Web Kaynakları
        parts.append("\n## 🌐 WEB ARAŞTIRMASI SONUÇLARI\n")
        
        for i, source in enumerate(context.sources, 1):
            reliability_stars = "⭐" * int(source["reliability"] * 5)
            content = source["content"][:2500] if source["content"] else source["snippet"]
            
            parts.append(f"""
---
### [{i}] {source['title']}
📍 {source['domain']} | {reliability_stars} | Tür: {source['type']}
URL: {source['url']}

{content}
""")
        
        # Çelişkiler
        if context.conflicting_info:
            conflict_text = "\n".join([
                f"⚠️ '{c['topic']}' konusunda farklı değerler: {c['values']}"
                for c in context.conflicting_info
            ])
            parts.append(f"""
## ⚠️ KAYNAKLARDA ÇELİŞKİ
{conflict_text}
Bu farklılıkları yanıtta değerlendir.
""")
        
        # Final talimat
        parts.append("""
---
## 📝 ŞİMDİ YANITLA
Yukarıdaki kaynaklara dayanarak kapsamlı, doğru ve iyi yapılandırılmış bir yanıt yaz.
""")
        
        return "\n".join(parts)


class ResponseFormatter:
    """Yanıt formatlama ve post-processing"""
    
    def format(self, raw_response: str, context: ResearchContext) -> SynthesizedResponse:
        """Ham yanıtı formatla"""
        
        # Kelime sayısı
        word_count = len(raw_response.split())
        
        # Key points çıkar
        key_points = self._extract_key_points(raw_response)
        
        # Citation'ları düzenle
        citations = self._format_citations(raw_response, context.sources)
        
        # Follow-up sorular
        follow_ups = self._generate_follow_ups(context)
        
        # Confidence score hesapla
        confidence = self._calculate_confidence(context, word_count)
        
        # Özet oluştur (ilk 2-3 cümle)
        sentences = re.split(r'[.!?]', raw_response)
        summary = ". ".join(s.strip() for s in sentences[:3] if s.strip()) + "."
        
        return SynthesizedResponse(
            main_content=raw_response,
            summary=summary,
            key_points=key_points,
            citations=citations,
            follow_up_questions=follow_ups,
            confidence_score=confidence,
            sources_used=len(context.sources),
            word_count=word_count,
            has_conflicting_info=len(context.conflicting_info) > 0,
            metadata={
                "intent": context.intent.value,
                "style": context.style.value,
                "source_types": context.source_summary
            }
        )
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Anahtar noktaları çıkar"""
        points = []
        
        # Kalın metin
        bold = re.findall(r'\*\*([^*]+)\*\*', text)
        points.extend(bold[:5])
        
        # Maddeli listeler
        bullets = re.findall(r'^[\-\*•]\s*(.+)$', text, re.MULTILINE)
        points.extend(bullets[:5])
        
        # Numaralı listeler
        numbered = re.findall(r'^\d+[\.\)]\s*(.+)$', text, re.MULTILINE)
        points.extend(numbered[:5])
        
        return list(set(points))[:8]
    
    def _format_citations(self, text: str, sources: List[Dict]) -> List[Dict]:
        """Citation'ları formatla"""
        citations = []
        
        # Metindeki [1], [2] vb. referansları bul
        refs = set(re.findall(r'\[(\d+)\]', text))
        
        for ref in refs:
            idx = int(ref) - 1
            if 0 <= idx < len(sources):
                source = sources[idx]
                citations.append({
                    "index": int(ref),
                    "title": source["title"],
                    "url": source["url"],
                    "domain": source["domain"]
                })
        
        # Referans yoksa ilk 3 kaynağı ekle
        if not citations:
            for i, source in enumerate(sources[:3], 1):
                citations.append({
                    "index": i,
                    "title": source["title"],
                    "url": source["url"],
                    "domain": source["domain"]
                })
        
        return citations
    
    def _generate_follow_ups(self, context: ResearchContext) -> List[str]:
        """Takip soruları oluştur"""
        query = context.query.lower()
        follow_ups = []
        
        # Intent bazlı sorular
        if context.intent == QueryIntent.DEFINITION:
            follow_ups.append(f"{context.query} örnekleri nelerdir?")
            follow_ups.append(f"{context.query} tarihçesi nedir?")
        
        elif context.intent == QueryIntent.PROCEDURAL:
            follow_ups.append("En sık yapılan hatalar nelerdir?")
            follow_ups.append("Alternatif yöntemler var mı?")
        
        elif context.intent == QueryIntent.COMPARATIVE:
            follow_ups.append("Hangi durumda hangisi tercih edilmeli?")
            follow_ups.append("Fiyat/performans açısından değerlendirme?")
        
        elif context.intent == QueryIntent.LIST:
            follow_ups.append("Bu listedeki en popüler hangisi?")
            follow_ups.append("Daha fazla örnek var mı?")
        
        # Genel sorular
        follow_ups.append("Bu konuda güncel gelişmeler neler?")
        follow_ups.append("Daha fazla bilgi için hangi kaynakları önerirsin?")
        
        return follow_ups[:4]
    
    def _calculate_confidence(self, context: ResearchContext, word_count: int) -> float:
        """Güven skoru hesapla"""
        score = 0.5
        
        # Kaynak sayısı
        source_count = len(context.sources)
        score += min(source_count * 0.05, 0.2)
        
        # Yüksek güvenilirlikli kaynak
        high_reliability = sum(1 for s in context.sources if s["reliability"] >= 0.7)
        score += high_reliability * 0.05
        
        # Instant answer
        if context.instant_answer:
            score += 0.1
        
        # Çelişki varsa düş
        if context.conflicting_info:
            score -= 0.1
        
        # Yeterli içerik
        if word_count >= 200:
            score += 0.1
        
        return min(max(score, 0.3), 0.95)


class ResearchSynthesizer:
    """
    Ana sentez sınıfı.
    
    Web arama sonuçlarını alır, analiz eder ve AI için optimal prompt oluşturur.
    """
    
    def __init__(self):
        self.aggregator = SourceAggregator()
        self.prompt_builder = PromptBuilder()
        self.formatter = ResponseFormatter()
    
    def prepare_context(self, search_response: Dict) -> ResearchContext:
        """Arama sonuçlarından bağlam hazırla"""
        return self.aggregator.aggregate(search_response)
    
    def build_prompts(self, context: ResearchContext) -> Tuple[str, str]:
        """Sistem ve kullanıcı promptlarını oluştur"""
        system = self.prompt_builder.build_system_prompt(context)
        user = self.prompt_builder.build_user_prompt(context)
        return system, user
    
    def format_response(self, raw_response: str, context: ResearchContext) -> SynthesizedResponse:
        """Ham yanıtı formatla"""
        return self.formatter.format(raw_response, context)
    
    def get_quick_summary(self, context: ResearchContext) -> str:
        """Hızlı özet oluştur (LLM olmadan)"""
        parts = []
        
        if context.instant_answer:
            parts.append(context.instant_answer.get("abstract", "")[:500])
        
        for source in context.sources[:3]:
            if source["reliability"] >= 0.6:
                parts.append(source["snippet"][:200])
        
        return " ".join(parts)[:1000]


# Singleton instance
_synthesizer: Optional[ResearchSynthesizer] = None

def get_synthesizer() -> ResearchSynthesizer:
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = ResearchSynthesizer()
    return _synthesizer
