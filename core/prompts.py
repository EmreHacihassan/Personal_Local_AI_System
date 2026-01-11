"""
Enterprise AI Assistant - Prompt Templates
Özelleştirilmiş prompt şablonları

Endüstri standardı prompt engineering.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from string import Template
from enum import Enum


class PromptCategory(str, Enum):
    """Prompt kategorileri."""
    SYSTEM = "system"
    RESEARCH = "research"
    WRITING = "writing"
    ANALYSIS = "analysis"
    CHAT = "chat"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"


@dataclass
class PromptTemplate:
    """Prompt şablonu."""
    name: str
    category: PromptCategory
    template: str
    description: str = ""
    variables: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)
    
    def render(self, **kwargs) -> str:
        """Şablonu değişkenlerle doldur."""
        return Template(self.template).safe_substitute(**kwargs)


# ============ SYSTEM PROMPTS ============

SYSTEM_PROMPT_TR = PromptTemplate(
    name="system_turkish",
    category=PromptCategory.SYSTEM,
    description="Türkçe sistem prompt'u",
    template="""Sen bir kurumsal AI asistanısın. Görevin şirket çalışanlarına yardımcı olmak.

Temel kuralların:
1. Her zaman Türkçe yanıt ver
2. Profesyonel ve yardımsever ol
3. Kaynaklarını göster
4. Emin olmadığın konularda "bilmiyorum" de
5. Gizli bilgileri koruma konusunda dikkatli ol

Bugünün tarihi: $date
""",
    variables=["date"],
)

SYSTEM_PROMPT_EN = PromptTemplate(
    name="system_english",
    category=PromptCategory.SYSTEM,
    description="English system prompt",
    template="""You are an enterprise AI assistant. Your role is to help company employees.

Core rules:
1. Always respond in English
2. Be professional and helpful
3. Cite your sources
4. Say "I don't know" when uncertain
5. Be careful about protecting confidential information

Today's date: $date
""",
    variables=["date"],
)


# ============ RESEARCH PROMPTS ============

RESEARCH_PROMPT = PromptTemplate(
    name="research_agent",
    category=PromptCategory.RESEARCH,
    description="Araştırma agent'ı için prompt",
    template="""Sen bir araştırma uzmanısın. Görkevin verilen bilgi tabanında kapsamlı araştırma yapmak.

## Görevin
$task

## Mevcut Bağlam
$context

## Kurallar
1. Sadece verilen kaynaklardan bilgi kullan
2. Her bilgi için kaynak göster
3. Bulamadığın bilgiyi açıkça belirt
4. Birden fazla kaynağı karşılaştır
5. Sonuçları özet olarak sun

## Yanıt Formatı
- Bulunan bilgileri maddeler halinde listele
- Her maddenin sonuna [Kaynak: dosya_adı] ekle
- Sonunda kısa bir özet yaz
""",
    variables=["task", "context"],
)


# ============ WRITING PROMPTS ============

EMAIL_DRAFT_PROMPT = PromptTemplate(
    name="email_draft",
    category=PromptCategory.WRITING,
    description="Email taslağı oluşturma",
    template="""Profesyonel bir email taslağı hazırla.

## Detaylar
- Alıcı: $recipient
- Konu: $subject
- Ton: $tone
- Ana mesaj: $message

## Format
Konu: [Konu satırı]

Sayın [İsim],

[Giriş paragrafı]

[Ana içerik]

[Kapanış]

Saygılarımla,
[İmza]
""",
    variables=["recipient", "subject", "tone", "message"],
)

REPORT_PROMPT = PromptTemplate(
    name="report_generation",
    category=PromptCategory.WRITING,
    description="Rapor oluşturma",
    template="""Profesyonel bir rapor hazırla.

## Rapor Başlığı
$title

## Kaynak Veriler
$data

## Rapor Formatı
1. Yönetici Özeti
2. Giriş
3. Bulgular
4. Analiz
5. Sonuç ve Öneriler

## Kurallar
- Profesyonel dil kullan
- Verilerle destekle
- Görsel öğeler öner (tablo, grafik)
- Aksiyon önerileri sun
""",
    variables=["title", "data"],
)


# ============ ANALYSIS PROMPTS ============

DOCUMENT_ANALYSIS_PROMPT = PromptTemplate(
    name="document_analysis",
    category=PromptCategory.ANALYSIS,
    description="Döküman analizi",
    template="""Verilen dökümanı analiz et.

## Döküman
$document

## Analiz Kriterleri
$criteria

## Çıktı Formatı
### Özet
[Kısa özet]

### Ana Noktalar
- Nokta 1
- Nokta 2
- ...

### Detaylı Analiz
[Detaylı analiz]

### Öneriler
[Varsa öneriler]
""",
    variables=["document", "criteria"],
)

COMPARISON_PROMPT = PromptTemplate(
    name="comparison_analysis",
    category=PromptCategory.ANALYSIS,
    description="Karşılaştırma analizi",
    template="""İki öğeyi karşılaştır.

## Öğe 1
$item1

## Öğe 2
$item2

## Karşılaştırma Kriterleri
$criteria

## Çıktı Formatı
| Kriter | Öğe 1 | Öğe 2 |
|--------|-------|-------|
| ... | ... | ... |

### Sonuç
[Karşılaştırma özeti ve tavsiye]
""",
    variables=["item1", "item2", "criteria"],
)


# ============ SUMMARIZATION PROMPTS ============

SUMMARIZE_PROMPT = PromptTemplate(
    name="summarize",
    category=PromptCategory.SUMMARIZE,
    description="Metin özetleme",
    template="""Verilen metni özetle.

## Metin
$text

## Özet Uzunluğu
$length (kısa/orta/uzun)

## Özet Formatı
- Ana fikir
- Önemli noktalar (madde işaretli)
- Sonuç
""",
    variables=["text", "length"],
)

MEETING_NOTES_PROMPT = PromptTemplate(
    name="meeting_notes",
    category=PromptCategory.SUMMARIZE,
    description="Toplantı notları özeti",
    template="""Toplantı notlarını özetle ve aksiyonları çıkar.

## Toplantı Notları
$notes

## Çıktı Formatı
### Toplantı Özeti
- Tarih: $date
- Katılımcılar: [Listele]
- Süre: [Tahmini]

### Tartışılan Konular
1. [Konu 1]
2. [Konu 2]

### Alınan Kararlar
- Karar 1
- Karar 2

### Aksiyonlar
| Aksiyon | Sorumlu | Tarih |
|---------|---------|-------|
| ... | ... | ... |

### Sonraki Adımlar
[Varsa sonraki toplantı/adımlar]
""",
    variables=["notes", "date"],
)


# ============ RAG PROMPTS ============

RAG_QUERY_PROMPT = PromptTemplate(
    name="rag_query",
    category=PromptCategory.CHAT,
    description="RAG tabanlı soru yanıtlama",
    template="""Verilen bağlamı kullanarak soruyu yanıtla.

## Bağlam (Bilgi Tabanından)
$context

## Soru
$question

## Kurallar
1. SADECE verilen bağlamdaki bilgileri kullan
2. Bağlamda olmayan bilgi için "Bu konuda bilgi bulamadım" de
3. Yanıtın sonuna kullandığın kaynakları ekle
4. Kısa ve öz yanıt ver
5. Türkçe yanıt ver

## Yanıt
""",
    variables=["context", "question"],
)

RAG_MULTI_DOC_PROMPT = PromptTemplate(
    name="rag_multi_document",
    category=PromptCategory.CHAT,
    description="Çoklu döküman RAG",
    template="""Birden fazla kaynaktan gelen bilgileri sentezleyerek yanıtla.

## Kaynaklar
$sources

## Soru
$question

## Kurallar
1. Tüm ilgili kaynakları kullan
2. Çelişkili bilgiler varsa belirt
3. Her bilgi için kaynak göster
4. Bilgileri sentezle, kopyalama yapma
5. Emin olmadığın yerleri belirt

## Yanıt Formatı
[Ana yanıt]

**Kaynaklar:**
- [Kaynak 1]: [Kullanılan bilgi]
- [Kaynak 2]: [Kullanılan bilgi]
""",
    variables=["sources", "question"],
)


# ============ PROMPT MANAGER ============

class PromptManager:
    """Prompt şablon yöneticisi."""
    
    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Varsayılan şablonları yükle."""
        defaults = [
            SYSTEM_PROMPT_TR,
            SYSTEM_PROMPT_EN,
            RESEARCH_PROMPT,
            EMAIL_DRAFT_PROMPT,
            REPORT_PROMPT,
            DOCUMENT_ANALYSIS_PROMPT,
            COMPARISON_PROMPT,
            SUMMARIZE_PROMPT,
            MEETING_NOTES_PROMPT,
            RAG_QUERY_PROMPT,
            RAG_MULTI_DOC_PROMPT,
        ]
        
        for template in defaults:
            self._templates[template.name] = template
    
    def get(self, name: str) -> Optional[PromptTemplate]:
        """Şablon al."""
        return self._templates.get(name)
    
    def render(self, name: str, **kwargs) -> str:
        """Şablonu render et."""
        template = self.get(name)
        if template:
            return template.render(**kwargs)
        raise ValueError(f"Template not found: {name}")
    
    def add(self, template: PromptTemplate) -> None:
        """Şablon ekle."""
        self._templates[template.name] = template
    
    def list_templates(self, category: PromptCategory = None) -> List[str]:
        """Şablonları listele."""
        if category:
            return [
                name for name, t in self._templates.items()
                if t.category == category
            ]
        return list(self._templates.keys())
    
    def get_by_category(self, category: PromptCategory) -> List[PromptTemplate]:
        """Kategoriye göre şablonları al."""
        return [
            t for t in self._templates.values()
            if t.category == category
        ]


# Singleton instance
prompts = PromptManager()
prompt_manager = prompts  # Alias for compatibility
