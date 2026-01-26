"""
🎯 Content Generator Agent
AI-Powered İçerik Üretim Sistemi

Bu modül:
1. Metin içeriği (açıklamalar, özetler)
2. Video önerileri (YouTube, vb.)
3. Görsel önerileri
4. İnteraktif içerik
5. RAG ile zenginleştirilmiş içerik
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from .models import (
    ContentBlock, ContentType, Package, Stage,
    DifficultyLevel
)


# ==================== CONTENT TEMPLATES ====================

EXPLANATION_TEMPLATES = {
    "concept": """
## {title}

### Tanım
{definition}

### Temel Kavramlar
{key_concepts}

### Örnekler
{examples}

### Özet
{summary}
""",
    "formula": """
## {title}

### Formül
$$
{formula}
$$

### Değişkenler
{variables}

### Kullanım Alanları
{applications}

### Örnek Problemler
{example_problems}
""",
    "procedure": """
## {title}

### Genel Bakış
{overview}

### Adımlar
{steps}

### İpuçları
{tips}

### Yaygın Hatalar
{common_mistakes}
"""
}

VIDEO_SOURCES = [
    {
        "platform": "youtube",
        "base_url": "https://www.youtube.com/watch?v=",
        "search_url": "https://www.youtube.com/results?search_query="
    },
    {
        "platform": "khan_academy",
        "base_url": "https://www.khanacademy.org/",
        "search_url": "https://www.khanacademy.org/search?referer=%2F&page_search_query="
    }
]


# ==================== CONTENT GENERATOR AGENT ====================

class ContentGeneratorAgent:
    """
    İçerik Üretim Agent'ı
    
    Capabilities:
    - LLM ile metin içeriği üretimi
    - RAG ile zenginleştirilmiş içerik
    - Video arama ve öneri
    - Görsel öneri
    - İnteraktif içerik planı
    """
    
    def __init__(self, llm_service=None, rag_service=None, web_search_service=None):
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.web_search = web_search_service
    
    async def generate_package_content(
        self,
        package: Package,
        stage: Stage,
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    ) -> List[ContentBlock]:
        """Paket için tüm içeriği üret"""
        
        content_blocks = []
        
        # 1. Giriş metni
        intro_block = await self._generate_intro(package, stage)
        content_blocks.append(intro_block)
        
        # 2. Her konu için açıklama
        for topic in package.topics:
            explanation = await self._generate_topic_explanation(
                topic, 
                package.curriculum_section,
                difficulty
            )
            content_blocks.append(explanation)
        
        # 3. Formüller ve kavramlar (matematiksel içerik için)
        if self._is_math_content(package):
            formulas = await self._generate_formulas(package.topics)
            content_blocks.extend(formulas)
        
        # 4. Örnekler
        examples = await self._generate_examples(package.topics, difficulty)
        content_blocks.extend(examples)
        
        # 5. Video önerileri
        videos = await self._find_videos(package.topics, stage.main_topic)
        content_blocks.extend(videos)
        
        # 6. Özet
        summary = await self._generate_summary(package, content_blocks)
        content_blocks.append(summary)
        
        return content_blocks
    
    async def _generate_intro(self, package: Package, stage: Stage) -> ContentBlock:
        """Giriş metni oluştur"""
        
        if self.llm_service:
            prompt = f"""Aşağıdaki öğrenme paketi için kısa ve motive edici bir giriş yaz.

**Paket:** {package.title}
**Stage:** {stage.title}
**Konular:** {', '.join(package.topics)}
**Hedefler:** {', '.join(package.learning_objectives)}

Giriş:
- 2-3 paragraf olsun
- Konunun önemini vurgula
- Öğrenciyi motive et
- Ne öğreneceğini açıkla"""

            try:
                content = await self.llm_service.generate(prompt)
            except:
                content = self._mock_intro(package)
        else:
            content = self._mock_intro(package)
        
        return ContentBlock(
            type=ContentType.TEXT,
            title=f"🎯 {package.title} - Giriş",
            content={"markdown": content, "text": content},
            duration_minutes=2,
            order=1,
            is_required=True,
            metadata={"package_id": package.id}
        )
    
    def _mock_intro(self, package: Package) -> str:
        """Mock giriş içeriği"""
        return f"""## Hoş Geldin! 👋

Bu pakette **{package.title}** konusunu öğreneceksin.

### Bu Pakette Neler Var?
{chr(10).join(f'- {topic}' for topic in package.topics)}

### Öğrenme Hedeflerin
{chr(10).join(f'- {obj}' for obj in package.learning_objectives)}

### Hazır mısın?
Bu konuyu adım adım işleyeceğiz. Her adımı tamamladıktan sonra bir sonrakine geçebilirsin.

Başarılar! 🚀"""
    
    async def _generate_topic_explanation(
        self,
        topic: str,
        curriculum_section: str,
        difficulty: DifficultyLevel
    ) -> ContentBlock:
        """Konu açıklaması oluştur"""
        
        if self.llm_service:
            prompt = f"""Aşağıdaki konu için detaylı bir açıklama yaz.

**Konu:** {topic}
**Müfredat Bölümü:** {curriculum_section}
**Zorluk Seviyesi:** {difficulty.value}

Açıklama:
- Kavramı basit dille anlat
- Önemli terimleri tanımla
- Örnekler ver
- Yaygın yanlış anlamaları düzelt
- Markdown formatında yaz"""

            try:
                content = await self.llm_service.generate(prompt)
            except:
                content = self._mock_explanation(topic)
        else:
            content = self._mock_explanation(topic)
        
        return ContentBlock(
            type=ContentType.TEXT,
            title=f"📖 {topic}",
            content={"markdown": content, "text": content},
            duration_minutes=5,
            order=0,
            is_required=True,
            metadata={"topic": topic, "curriculum_section": curriculum_section}
        )
    
    def _mock_explanation(self, topic: str) -> str:
        """Mock açıklama içeriği"""
        return f"""## {topic}

### Tanım
{topic}, matematiğin temel kavramlarından biridir.

### Temel Özellikler
- Özellik 1
- Özellik 2
- Özellik 3

### Örnek
Basit bir örnek ile açıklayalım:

```
Örnek problem burada...
```

### Özet
{topic} konusunu öğrendin! Şimdi pratik yapmaya hazırsın."""
    
    async def _generate_formulas(self, topics: List[str]) -> List[ContentBlock]:
        """Formüller ve kavramsal kartlar oluştur"""
        
        blocks = []
        
        # Mock formül içeriği
        formulas = {
            "Türev": {
                "formulas": [
                    ("Türev Tanımı", r"f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}"),
                    ("Kuvvet Kuralı", r"\frac{d}{dx}(x^n) = nx^{n-1}"),
                    ("Çarpım Kuralı", r"(fg)' = f'g + fg'"),
                    ("Bölüm Kuralı", r"\left(\frac{f}{g}\right)' = \frac{f'g - fg'}{g^2}")
                ]
            },
            "İntegral": {
                "formulas": [
                    ("Belirsiz İntegral", r"\int x^n dx = \frac{x^{n+1}}{n+1} + C"),
                    ("Belirli İntegral", r"\int_a^b f(x)dx = F(b) - F(a)"),
                    ("Parçalı İntegral", r"\int u \, dv = uv - \int v \, du")
                ]
            },
            "Limit": {
                "formulas": [
                    ("Limit Tanımı", r"\lim_{x \to a} f(x) = L"),
                    ("L'Hôpital Kuralı", r"\lim_{x \to a} \frac{f(x)}{g(x)} = \lim_{x \to a} \frac{f'(x)}{g'(x)}")
                ]
            }
        }
        
        for topic in topics:
            if topic in formulas:
                formula_list = formulas[topic]["formulas"]
                content = f"## {topic} Formülleri\n\n"
                
                for name, formula in formula_list:
                    content += f"### {name}\n\n"
                    content += f"$$\n{formula}\n$$\n\n"
                
                blocks.append(ContentBlock(
                    type=ContentType.FORMULA_SHEET,
                    title=f"📐 {topic} Formülleri",
                    content={"markdown": content, "formulas": formula_list},
                    duration_minutes=3,
                    order=0,
                    metadata={"topic": topic}
                ))
        
        return blocks
    
    async def _generate_examples(
        self,
        topics: List[str],
        difficulty: DifficultyLevel
    ) -> List[ContentBlock]:
        """Örnekler oluştur"""
        
        blocks = []
        
        for topic in topics[:2]:  # İlk 2 konu için
            if self.llm_service:
                prompt = f"""'{topic}' konusu için {difficulty.value} seviyesinde 3 örnek problem ve çözümü yaz.

Her örnek için:
1. Problem açıklaması
2. Adım adım çözüm
3. Sonuç

Markdown formatında yaz."""

                try:
                    content = await self.llm_service.generate(prompt)
                except:
                    content = self._mock_examples(topic)
            else:
                content = self._mock_examples(topic)
            
            blocks.append(ContentBlock(
                type=ContentType.EXAMPLE,
                title=f"✏️ {topic} Örnekleri",
                content={"markdown": content, "text": content},
                duration_minutes=10,
                order=0,
                metadata={"topic": topic, "type": "worked_examples"}
            ))
        
        return blocks
    
    def _mock_examples(self, topic: str) -> str:
        """Mock örnek içeriği"""
        return f"""## {topic} - Çözümlü Örnekler

### Örnek 1
**Problem:** {topic} ile ilgili temel problem...

**Çözüm:**
1. Adım 1
2. Adım 2
3. Adım 3

**Sonuç:** Cevap

---

### Örnek 2
**Problem:** {topic} ile ilgili orta seviye problem...

**Çözüm:**
1. Önce şunu yapıyoruz...
2. Sonra bunu...

**Sonuç:** Cevap

---

### Örnek 3
**Problem:** {topic} ile ilgili ileri seviye problem...

**Çözüm:**
Detaylı çözüm...

**Sonuç:** Cevap"""
    
    async def _find_videos(self, topics: List[str], main_topic: str) -> List[ContentBlock]:
        """Video önerileri bul"""
        
        blocks = []
        
        # Mock video önerileri
        video_suggestions = [
            {
                "title": f"{main_topic} - Temel Kavramlar",
                "platform": "YouTube",
                "url": f"https://www.youtube.com/results?search_query={main_topic.replace(' ', '+')}+ders",
                "duration": "15:00",
                "channel": "Matematik Kanalı"
            },
            {
                "title": f"{main_topic} - Soru Çözümü",
                "platform": "YouTube",
                "url": f"https://www.youtube.com/results?search_query={main_topic.replace(' ', '+')}+soru+çözümü",
                "duration": "20:00",
                "channel": "AYT Matematik"
            }
        ]
        
        video_content = "## 🎬 Önerilen Videolar\n\n"
        
        for video in video_suggestions:
            video_content += f"""### [{video['title']}]({video['url']})
- **Platform:** {video['platform']}
- **Süre:** {video['duration']}
- **Kanal:** {video['channel']}

"""
        
        blocks.append(ContentBlock(
            type=ContentType.VIDEO,
            title="🎬 Video Önerileri",
            content={"markdown": video_content, "videos": video_suggestions},
            duration_minutes=30,
            order=0,
            metadata={
                "videos": video_suggestions,
                "search_query": main_topic,
                "topic": main_topic
            }
        ))
        
        return blocks
    
    async def _generate_summary(
        self,
        package: Package,
        content_blocks: List[ContentBlock]
    ) -> ContentBlock:
        """Özet oluştur"""
        
        summary_content = f"""## 📋 {package.title} - Özet

### Bu Pakette Öğrendiklerimiz
{chr(10).join(f'- {topic}' for topic in package.topics)}

### Temel Kavramlar
{chr(10).join(f'- {obj}' for obj in package.learning_objectives)}

### Sonraki Adımlar
1. ✏️ Pratik egzersizleri tamamla
2. 📝 Mini testi çöz
3. 🔄 Zor konuları tekrar et
4. ➡️ Bir sonraki pakete geç

### İpucu
Konuyu pekiştirmek için Feynman tekniğini kullan: Öğrendiğini basit kelimelerle açıklamaya çalış!
"""
        
        return ContentBlock(
            type=ContentType.SUMMARY,
            title=f"📋 Özet",
            content={"markdown": summary_content, "text": summary_content},
            duration_minutes=2,
            order=999,
            is_required=True
        )
    
    def _is_math_content(self, package: Package) -> bool:
        """Matematik içeriği mi kontrol et"""
        math_keywords = [
            "matematik", "türev", "integral", "limit", "fonksiyon",
            "denklem", "geometri", "trigonometri", "logaritma",
            "polinom", "sayılar", "cebir"
        ]
        
        text = f"{package.title} {package.curriculum_section} {' '.join(package.topics)}".lower()
        
        return any(keyword in text for keyword in math_keywords)


# ==================== RAG CONTENT ENHANCER ====================

class RAGContentEnhancer:
    """RAG ile içerik zenginleştirici"""
    
    def __init__(self, rag_service=None):
        self.rag_service = rag_service
    
    async def enhance_content(
        self,
        content: str,
        topic: str,
        sources: Optional[List[str]] = None
    ) -> Tuple[str, List[Dict[str, str]]]:
        """İçeriği RAG ile zenginleştir"""
        
        if not self.rag_service:
            return content, []
        
        # RAG sorgusu
        try:
            query = f"{topic} hakkında ek bilgi ve örnekler"
            results = await self.rag_service.query(query, top_k=3)
            
            # Sonuçları içeriğe ekle
            if results:
                enhanced_content = content + "\n\n---\n\n## 📚 Ek Kaynaklar\n\n"
                
                citations = []
                for i, result in enumerate(results):
                    enhanced_content += f"### Kaynak {i+1}\n{result['content'][:500]}...\n\n"
                    citations.append({
                        "source": result.get("source", "Bilinmiyor"),
                        "relevance": result.get("score", 0)
                    })
                
                return enhanced_content, citations
        except:
            pass
        
        return content, []


# ==================== SINGLETON ====================

_content_generator: Optional[ContentGeneratorAgent] = None

def get_content_generator() -> ContentGeneratorAgent:
    global _content_generator
    if _content_generator is None:
        _content_generator = ContentGeneratorAgent()
    return _content_generator
