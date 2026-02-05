"""
📚 Few-Shot Examples Library
============================

Premium örnek yanıt kütüphanesi:
- Domain-specific examples
- High-quality response templates
- Semantic example selection
- Dynamic example injection

Author: Enterprise AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ExampleCategory(str, Enum):
    """Örnek kategorileri."""
    TECHNICAL = "technical"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    FACTUAL = "factual"
    CODING = "coding"
    MATH = "math"
    COMPARISON = "comparison"


@dataclass
class FewShotExample:
    """Tek bir few-shot örneği."""
    category: ExampleCategory
    query: str
    response: str
    keywords: List[str] = field(default_factory=list)
    quality_score: float = 0.9


# ============================================================================
# EXAMPLES LIBRARY
# ============================================================================

class ExamplesLibrary:
    """
    Premium few-shot example kütüphanesi.
    
    Features:
    - Kategorize edilmiş yüksek kaliteli örnekler
    - Keyword-based example selection
    - Dynamic injection to prompts
    """
    
    def __init__(self):
        self.examples = self._load_examples()
    
    def _load_examples(self) -> Dict[ExampleCategory, List[FewShotExample]]:
        """Örnek kütüphanesini yükle."""
        return {
            ExampleCategory.TECHNICAL: [
                FewShotExample(
                    category=ExampleCategory.TECHNICAL,
                    query="Docker nedir ve nasıl çalışır?",
                    response="""## Docker Nedir?

Docker, uygulamaları **container** adı verilen hafif, taşınabilir ve izole ortamlarda çalıştırmaya yarayan bir platformdur.

### Temel Kavramlar

| Kavram | Açıklama |
|--------|----------|
| **Image** | Container'ın blueprint'i (şablonu) |
| **Container** | Image'dan oluşturulan çalışan instance |
| **Dockerfile** | Image oluşturmak için talimat dosyası |
| **Registry** | Image'ların depolandığı yer (Docker Hub) |

### Nasıl Çalışır?

1. **Dockerfile** yazılır (uygulama gereksinimleri)
2. `docker build` ile **Image** oluşturulur
3. `docker run` ile **Container** başlatılır

```bash
# Dockerfile örneği
FROM python:3.11
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

### Avantajları
- ✅ Taşınabilirlik (her ortamda aynı çalışır)
- ✅ İzolasyon (bağımlılık çakışması yok)
- ✅ Hafiflik (VM'lerden çok daha hızlı)
- ✅ Ölçeklenebilirlik (kolay replikasyon)

### Kullanım Alanları
- Mikroservis mimarisi
- CI/CD pipeline'ları
- Geliştirme ortamı standardizasyonu
- Cloud deployment""",
                    keywords=["docker", "container", "kubernetes", "devops", "deployment"],
                    quality_score=0.95
                ),
                FewShotExample(
                    category=ExampleCategory.TECHNICAL,
                    query="REST API ve GraphQL arasındaki farklar nelerdir?",
                    response="""## REST API vs GraphQL Karşılaştırması

Her ikisi de API tasarım yaklaşımıdır, ancak farklı felsefelere sahiptir.

### Temel Farklar

| Özellik | REST API | GraphQL |
|---------|----------|---------|
| **Endpoint yapısı** | Çoklu endpoint (`/users`, `/posts`) | Tek endpoint (`/graphql`) |
| **Veri alma** | Sunucu belirler | İstemci belirler |
| **Over-fetching** | Sık görülür | Yok |
| **Under-fetching** | Sık görülür | Yok |
| **Versiyon** | URL'de (`/v1/users`) | Schema evolution |
| **Caching** | HTTP cache kolay | Daha karmaşık |

### REST API Örneği
```http
GET /api/users/123
Response: { id, name, email, address, phone, ... }
```
→ İhtiyacınız olmayan alanlar da gelir (over-fetching)

### GraphQL Örneği
```graphql
query {
  user(id: 123) {
    name
    email
  }
}
```
→ Sadece istediğiniz alanlar gelir

### Ne Zaman Hangisi?

**REST tercih edin:**
- Basit CRUD operasyonları
- HTTP caching önemli ise
- Takım GraphQL bilmiyorsa

**GraphQL tercih edin:**
- Karmaşık, ilişkisel veri
- Mobil uygulamalar (bandwidth kritik)
- Hızlı iterasyon gerekiyorsa""",
                    keywords=["rest", "api", "graphql", "backend", "web service"],
                    quality_score=0.92
                ),
            ],
            
            ExampleCategory.CODING: [
                FewShotExample(
                    category=ExampleCategory.CODING,
                    query="Python'da async/await nasıl kullanılır?",
                    response="""## Python Async/Await Kullanımı

`async`/`await`, Python'da asenkron programlama için kullanılır. I/O-bound işlemlerde (network, dosya) büyük performans artışı sağlar.

### Temel Kavramlar

```python
import asyncio

# async fonksiyon tanımlama
async def fetch_data(url: str) -> dict:
    # await ile asenkron işlem bekletme
    response = await aiohttp.get(url)
    return await response.json()
```

### Örnek: Paralel API Çağrıları

```python
import asyncio
import aiohttp

async def fetch_user(session, user_id: int):
    url = f"https://api.example.com/users/{user_id}"
    async with session.get(url) as response:
        return await response.json()

async def fetch_all_users(user_ids: list[int]):
    async with aiohttp.ClientSession() as session:
        # Tüm istekleri paralel başlat
        tasks = [fetch_user(session, uid) for uid in user_ids]
        # Hepsini bekle
        results = await asyncio.gather(*tasks)
        return results

# Çalıştır
users = asyncio.run(fetch_all_users([1, 2, 3, 4, 5]))
```

### Performans Karşılaştırması

| Yöntem | 5 API çağrısı |
|--------|---------------|
| Senkron (sıralı) | ~5 saniye |
| Asenkron (paralel) | ~1 saniye |

### Dikkat Edilecekler

⚠️ **CPU-bound işlemlerde faydasız** - Sadece I/O için
⚠️ **Tüm zincir async olmalı** - Senkron bir fonksiyon zinciri kırar
⚠️ **Event loop yönetimi** - `asyncio.run()` ile başlat""",
                    keywords=["async", "await", "asyncio", "python", "asenkron", "concurrent"],
                    quality_score=0.94
                ),
                FewShotExample(
                    category=ExampleCategory.CODING,
                    query="JavaScript'te closure nedir?",
                    response="""## JavaScript Closure Kavramı

Closure, bir fonksiyonun **tanımlandığı scope'taki** değişkenlere erişimini korumasıdır.

### Basit Örnek

```javascript
function createCounter() {
    let count = 0;  // Bu değişken closure'da "kapanır"
    
    return function() {
        count++;  // Dıştaki count'a erişebilir
        return count;
    };
}

const counter = createCounter();
console.log(counter()); // 1
console.log(counter()); // 2
console.log(counter()); // 3
```

`count` değişkeni fonksiyon döndükten sonra bile yaşamaya devam eder!

### Gerçek Dünya Kullanımı

**1. Private değişkenler oluşturma:**
```javascript
function createBankAccount(initialBalance) {
    let balance = initialBalance;  // Private
    
    return {
        deposit: (amount) => balance += amount,
        withdraw: (amount) => balance -= amount,
        getBalance: () => balance
    };
}

const account = createBankAccount(100);
account.deposit(50);
console.log(account.getBalance()); // 150
console.log(account.balance);      // undefined (erişilemez!)
```

**2. Event listener'larda:**
```javascript
function setupButtons() {
    for (let i = 0; i < 3; i++) {
        document.getElementById(`btn-${i}`).onclick = () => {
            console.log(`Button ${i} clicked`);  // Her buton doğru i'yi hatırlar
        };
    }
}
```

### Dikkat: Loop'larda `var` kullanmayın!

```javascript
// ❌ YANLIŞ - var ile
for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
// Çıktı: 3, 3, 3

// ✅ DOĞRU - let ile
for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
// Çıktı: 0, 1, 2
```""",
                    keywords=["closure", "javascript", "scope", "function", "kapanış"],
                    quality_score=0.93
                ),
            ],
            
            ExampleCategory.MATH: [
                FewShotExample(
                    category=ExampleCategory.MATH,
                    query="Türev nasıl hesaplanır?",
                    response="""## Türev Hesaplama

Türev, bir fonksiyonun **anlık değişim hızını** verir.

### Türev Tanımı

$$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$

### Temel Türev Kuralları

| Fonksiyon | Türev |
|-----------|-------|
| $c$ (sabit) | $0$ |
| $x^n$ | $n \\cdot x^{n-1}$ |
| $e^x$ | $e^x$ |
| $\\ln(x)$ | $\\frac{1}{x}$ |
| $\\sin(x)$ | $\\cos(x)$ |
| $\\cos(x)$ | $-\\sin(x)$ |

### Örnek Hesaplama

**Soru:** $f(x) = 3x^4 - 2x^2 + 5x - 7$ türevini bul.

**Çözüm:**
$$f'(x) = 3 \\cdot 4x^3 - 2 \\cdot 2x + 5 - 0$$
$$f'(x) = 12x^3 - 4x + 5$$

### Zincir Kuralı (Chain Rule)

Bileşik fonksiyonlar için:
$$\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)$$

**Örnek:** $y = (2x + 1)^3$

- Dış fonksiyon: $u^3$ → Türev: $3u^2$
- İç fonksiyon: $2x + 1$ → Türev: $2$
- Sonuç: $3(2x+1)^2 \\cdot 2 = 6(2x+1)^2$

### Uygulama Alanları
- 📈 Maks/min bulma (optimizasyon)
- 🚗 Hız/ivme hesaplama
- 📊 Eğim analizi
- 🤖 Machine Learning (gradient descent)""",
                    keywords=["türev", "derivative", "calculus", "matematik", "limit"],
                    quality_score=0.91
                ),
            ],
            
            ExampleCategory.ANALYTICAL: [
                FewShotExample(
                    category=ExampleCategory.ANALYTICAL,
                    query="Microservices mimarisinin avantaj ve dezavantajları nelerdir?",
                    response="""## Microservices Mimarisi Analizi

### Genel Bakış
Microservices, uygulamayı bağımsız, küçük servislere bölen bir mimari yaklaşımdır.

### ✅ Avantajlar

| Avantaj | Açıklama |
|---------|----------|
| **Bağımsız deployment** | Her servis ayrı deploy edilebilir |
| **Teknoloji çeşitliliği** | Servis başına farklı dil/framework |
| **Ölçeklenebilirlik** | Sadece gerekli servisi scale et |
| **Hata izolasyonu** | Bir servis çökerse diğerleri çalışır |
| **Takım özerkliği** | Küçük takımlar bağımsız çalışabilir |

### ❌ Dezavantajlar

| Dezavantaj | Açıklama |
|------------|----------|
| **Karmaşıklık** | Dağıtık sistem yönetimi zor |
| **Network latency** | Servisler arası iletişim maliyeti |
| **Data consistency** | Transaction yönetimi karmaşık |
| **Debugging zorluğu** | Distributed tracing gerekli |
| **Operasyonel yük** | Her servis için monitoring/logging |

### Ne Zaman Kullanmalı?

**Microservices uygundur:**
- ✅ Büyük, karmaşık uygulamalar
- ✅ Farklı ölçekleme gereksinimleri
- ✅ Çoklu takımlar
- ✅ Hızlı release döngüsü

**Monolith daha uygundur:**
- ❌ Küçük/orta projeler
- ❌ Startup MVP'leri
- ❌ Sınırlı DevOps kaynağı
- ❌ Basit domain

### Geçiş Stratejisi

1. **Strangler Fig Pattern** ile kademeli geçiş
2. Önce en bağımsız modülü ayır
3. API Gateway ekle
4. Monitoring/logging altyapısı kur

> 💡 **Tavsiye:** "Microservices first" değil, ihtiyaç oldukça geçiş yapın.""",
                    keywords=["microservices", "mimari", "architecture", "monolith", "dağıtık"],
                    quality_score=0.94
                ),
            ],
            
            ExampleCategory.FACTUAL: [
                FewShotExample(
                    category=ExampleCategory.FACTUAL,
                    query="Yapay zeka ve makine öğrenmesi arasındaki fark nedir?",
                    response="""## Yapay Zeka vs Makine Öğrenmesi

### Tanımlar

**Yapay Zeka (AI):**
İnsan zekasını taklit eden sistemlerin genel adı. Karar verme, problem çözme, öğrenme gibi yetenekleri kapsar.

**Makine Öğrenmesi (ML):**
Yapay zekanın bir alt dalı. Sistemlerin veriden öğrenmesini ve tahmin yapmasını sağlar.

### İlişki

```
┌─────────────────────────────────────┐
│           YAPAY ZEKA (AI)           │
│  ┌───────────────────────────────┐  │
│  │    MAKİNE ÖĞRENMESİ (ML)      │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │    DERİN ÖĞRENME (DL)   │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Karşılaştırma Tablosu

| Özellik | Yapay Zeka | Makine Öğrenmesi |
|---------|------------|------------------|
| **Kapsam** | Geniş (tüm zeki sistemler) | Dar (veriden öğrenme) |
| **Yaklaşım** | Kural tabanlı + öğrenme | Sadece öğrenme |
| **Örnek** | Uzman sistemler, robotik | Öneri sistemleri, sınıflandırma |
| **Veri gereksinimi** | Değişken | Mutlaka gerekli |

### Örnek Uygulamalar

**Yapay Zeka (ML olmadan):**
- Satranç motorları (Deep Blue)
- Uzman sistemler (tıbbi teşhis kuralları)

**Makine Öğrenmesi:**
- Spam filtreleme
- Netflix önerileri
- Görüntü tanıma (yüz tanıma)

### Özet

> 💡 Tüm ML sistemleri AI'dır, ama tüm AI sistemleri ML değildir. ML, AI'ın "veriden öğrenme" yeteneğine odaklanan özel bir dalıdır.""",
                    keywords=["yapay zeka", "makine öğrenmesi", "ai", "ml", "deep learning"],
                    quality_score=0.92
                ),
            ],
        }
    
    def get_examples(
        self,
        category: Optional[ExampleCategory] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 2,
    ) -> List[FewShotExample]:
        """
        Örnekleri filtrele ve döndür.
        
        Args:
            category: Kategori filtresi
            keywords: Keyword filtresi
            limit: Maksimum örnek sayısı
            
        Returns:
            Örnek listesi
        """
        results = []
        
        # Tüm örnekleri topla
        all_examples = []
        for cat, examples in self.examples.items():
            if category is None or cat == category:
                all_examples.extend(examples)
        
        # Keyword filtresi
        if keywords:
            keywords_lower = [k.lower() for k in keywords]
            scored_examples = []
            
            for ex in all_examples:
                # Keyword eşleşme skoru
                match_count = sum(
                    1 for kw in keywords_lower
                    if any(kw in ex_kw.lower() for ex_kw in ex.keywords)
                    or kw in ex.query.lower()
                )
                
                if match_count > 0:
                    scored_examples.append((ex, match_count))
            
            # Skora göre sırala
            scored_examples.sort(key=lambda x: x[1], reverse=True)
            results = [ex for ex, _ in scored_examples[:limit]]
        else:
            # Kalite skoruna göre sırala
            all_examples.sort(key=lambda x: x.quality_score, reverse=True)
            results = all_examples[:limit]
        
        return results
    
    def format_examples_for_prompt(
        self,
        examples: List[FewShotExample],
        include_separator: bool = True,
    ) -> str:
        """
        Örnekleri prompt formatında formatla.
        
        Args:
            examples: Örnek listesi
            include_separator: Ayırıcı eklensin mi
            
        Returns:
            Formatlanmış örnekler
        """
        if not examples:
            return ""
        
        parts = ["### Örnek Yanıtlar\n"]
        
        for i, ex in enumerate(examples, 1):
            parts.append(f"**Örnek {i}:**")
            parts.append(f"Soru: {ex.query}")
            parts.append(f"Yanıt:\n{ex.response}")
            
            if include_separator and i < len(examples):
                parts.append("\n---\n")
        
        return "\n".join(parts)
    
    def inject_into_prompt(
        self,
        system_prompt: str,
        query: str,
        max_examples: int = 2,
    ) -> str:
        """
        System prompt'a uygun örnekleri ekle.
        
        Args:
            system_prompt: Mevcut system prompt
            query: Kullanıcı sorusu
            max_examples: Maksimum örnek sayısı
            
        Returns:
            Örnekler eklenmiş prompt
        """
        # Sorgudan keyword çıkar
        query_words = query.lower().split()
        
        # Kategori tahmin et
        category = self._guess_category(query)
        
        # Örnekleri al
        examples = self.get_examples(
            category=category,
            keywords=query_words[:5],
            limit=max_examples,
        )
        
        if not examples:
            return system_prompt
        
        examples_text = self.format_examples_for_prompt(examples)
        
        return f"{system_prompt}\n\n{examples_text}"
    
    def _guess_category(self, query: str) -> Optional[ExampleCategory]:
        """Sorgu için kategori tahmin et."""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["kod", "code", "fonksiyon", "function", "python", "javascript"]):
            return ExampleCategory.CODING
        elif any(kw in query_lower for kw in ["hesapla", "formül", "matematik", "türev", "integral"]):
            return ExampleCategory.MATH
        elif any(kw in query_lower for kw in ["karşılaştır", "analiz", "avantaj", "dezavantaj", "fark"]):
            return ExampleCategory.ANALYTICAL
        elif any(kw in query_lower for kw in ["nedir", "ne demek", "açıkla", "tanım"]):
            return ExampleCategory.FACTUAL
        elif any(kw in query_lower for kw in ["api", "docker", "kubernetes", "database", "backend"]):
            return ExampleCategory.TECHNICAL
        
        return None


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

examples_library = ExamplesLibrary()


__all__ = [
    "ExamplesLibrary",
    "FewShotExample",
    "ExampleCategory",
    "examples_library",
]
