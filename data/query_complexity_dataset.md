# 🎯 Sorgu Karmaşıklık Sınıflandırma Veri Seti
# Query Complexity Classification Dataset

Bu veri seti, kullanıcı sorgularını otomatik olarak **BASİT** veya **KAPSAMLI** olarak sınıflandırmak için kullanılır.

---

## 📊 Sınıflandırma Kriterleri

### BASİT (Simple) Yanıt Gerektiren Sorgular:
- Tek cümlelik yanıt yeterli
- Faktüel bilgi (tarih, sayı, isim)
- Evet/Hayır soruları
- Selamlaşma ve günlük konuşma
- Basit tanımlar
- Hızlı hesaplamalar
- Kısa kod parçacıkları
- Tek adımlı işlemler

### KAPSAMLI (Comprehensive) Yanıt Gerektiren Sorgular:
- Detaylı açıklama gerekli
- Öğretici/eğitici içerik
- Analiz ve karşılaştırma
- Rapor oluşturma
- Çok adımlı süreçler
- Araştırma gerektiren konular
- Proje planlaması
- Kod mimarisi tasarımı
- Strateji geliştirme

---

# 📝 VERİ SETİ

---

## 🟢 BASİT SORGULAR (Simple Queries)

### Kategori: Selamlaşma ve Günlük Konuşma

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 1 | Selam | BASİT | Selamlaşma |
| 2 | Merhaba | BASİT | Selamlaşma |
| 3 | Naber? | BASİT | Selamlaşma |
| 4 | Nasılsın? | BASİT | Selamlaşma |
| 5 | Günaydın | BASİT | Selamlaşma |
| 6 | İyi akşamlar | BASİT | Selamlaşma |
| 7 | Hey | BASİT | Selamlaşma |
| 8 | Selam, nasıl gidiyor? | BASİT | Selamlaşma |
| 9 | Ne haber? | BASİT | Selamlaşma |
| 10 | İyi misin? | BASİT | Selamlaşma |
| 11 | Merhaba, ben buradayım | BASİT | Selamlaşma |
| 12 | Hoş geldin | BASİT | Selamlaşma |
| 13 | Sana bir sorum var | BASİT | Selamlaşma |
| 14 | Yardımına ihtiyacım var | BASİT | Selamlaşma |
| 15 | Burada mısın? | BASİT | Selamlaşma |
| 16 | Beni duyuyor musun? | BASİT | Selamlaşma |
| 17 | Test | BASİT | Selamlaşma |
| 18 | Çalışıyor musun? | BASİT | Selamlaşma |
| 19 | Aktif misin? | BASİT | Selamlaşma |
| 20 | Hazır mısın? | BASİT | Selamlaşma |

### Kategori: Tarih ve Zaman Soruları

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 21 | Bugün günlerden ne? bunu bulmak için interneti tara | BASİT | Tarih |
| 22 | Saat kaç? | BASİT | Zaman |
| 23 | Bugün ayın kaçı? | BASİT | Tarih |
| 24 | Hangi yıldayız? | BASİT | Tarih |
| 25 | Bu hafta sonu mu? | BASİT | Tarih |
| 26 | Yarın hangi gün? | BASİT | Tarih |
| 27 | Dün ayın kaçıydı? | BASİT | Tarih |
| 28 | Şu an hangi ay? | BASİT | Tarih |
| 29 | Bugün tatil mi? | BASİT | Tarih |
| 30 | Ramazan ne zaman başlıyor? | BASİT | Tarih |
| 31 | Yılbaşına kaç gün var? | BASİT | Hesaplama |
| 32 | Bugün Cuma mı? | BASİT | Tarih |
| 33 | Hangi mevsimdeyiz? | BASİT | Tarih |
| 34 | 2025 yılı artık yıl mı? | BASİT | Bilgi |
| 35 | Şu anki tarih nedir? | BASİT | Tarih |

### Kategori: Basit Faktüel Sorular

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 36 | Türkiye'nin başkenti neresi? | BASİT | Coğrafya |
| 37 | Pi sayısı kaçtır? | BASİT | Matematik |
| 38 | Dünya'nın en yüksek dağı hangisi? | BASİT | Coğrafya |
| 39 | Su kaç derecede kaynar? | BASİT | Bilim |
| 40 | 1 kilometre kaç metre? | BASİT | Dönüşüm |
| 41 | Atatürk ne zaman doğdu? | BASİT | Tarih |
| 42 | En büyük gezegen hangisi? | BASİT | Astronomi |
| 43 | Türkiye'nin nüfusu kaç? | BASİT | İstatistik |
| 44 | İngilizce'de "merhaba" ne demek? | BASİT | Çeviri |
| 45 | Einstein'ın ünlü formülü nedir? | BASİT | Bilim |
| 46 | Bir yılda kaç gün var? | BASİT | Bilgi |
| 47 | Güneş sistemi kaç gezegenden oluşur? | BASİT | Astronomi |
| 48 | DNA'nın açılımı nedir? | BASİT | Bilim |
| 49 | İstanbul'un plaka kodu kaç? | BASİT | Bilgi |
| 50 | Türk Lirası sembolü nedir? | BASİT | Bilgi |
| 51 | Bir saatte kaç dakika var? | BASİT | Bilgi |
| 52 | Ay'a ilk kim ayak bastı? | BASİT | Tarih |
| 53 | En hızlı hayvan hangisi? | BASİT | Bilgi |
| 54 | Demir elementi sembolü nedir? | BASİT | Kimya |
| 55 | Fransa'nın başkenti neresi? | BASİT | Coğrafya |

### Kategori: Basit Hesaplamalar

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 56 | 5 + 7 kaç eder? | BASİT | Hesaplama |
| 57 | 144'ün karekökü kaçtır? | BASİT | Hesaplama |
| 58 | 15 x 8 = ? | BASİT | Hesaplama |
| 59 | 1000 / 25 kaç? | BASİT | Hesaplama |
| 60 | %20 indirimle 100 TL kaç olur? | BASİT | Hesaplama |
| 61 | 2^10 kaç eder? | BASİT | Hesaplama |
| 62 | 1 dolar kaç TL? | BASİT | Döviz |
| 63 | 50 mil kaç kilometre? | BASİT | Dönüşüm |
| 64 | 100 Fahrenheit kaç Celcius? | BASİT | Dönüşüm |
| 65 | 3.14 x 5^2 kaç? | BASİT | Hesaplama |
| 66 | 1 GB kaç MB? | BASİT | Dönüşüm |
| 67 | Üçgenin iç açıları toplamı kaç derece? | BASİT | Matematik |
| 68 | 7! (faktöriyel) kaç eder? | BASİT | Hesaplama |
| 69 | log₁₀(1000) kaçtır? | BASİT | Hesaplama |
| 70 | 25'in %40'ı kaç? | BASİT | Hesaplama |

### Kategori: Evet/Hayır Soruları

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 71 | Python nesne yönelimli bir dil mi? | BASİT | Evet/Hayır |
| 72 | JavaScript frontend'de kullanılır mı? | BASİT | Evet/Hayır |
| 73 | Balina bir memeli mi? | BASİT | Evet/Hayır |
| 74 | Ay Dünya'dan büyük mü? | BASİT | Evet/Hayır |
| 75 | HTML bir programlama dili mi? | BASİT | Evet/Hayır |
| 76 | 0 çift sayı mı? | BASİT | Evet/Hayır |
| 77 | Türkiye AB üyesi mi? | BASİT | Evet/Hayır |
| 78 | Su iletken midir? | BASİT | Evet/Hayır |
| 79 | Mars'ta su var mı? | BASİT | Evet/Hayır |
| 80 | Git bir versiyon kontrol sistemi mi? | BASİT | Evet/Hayır |
| 81 | Penguen uçabilir mi? | BASİT | Evet/Hayır |
| 82 | Rust memory-safe bir dil mi? | BASİT | Evet/Hayır |
| 83 | Linux açık kaynaklı mı? | BASİT | Evet/Hayır |
| 84 | TCP güvenilir bir protokol mü? | BASİT | Evet/Hayır |
| 85 | MongoDB NoSQL veritabanı mı? | BASİT | Evet/Hayır |

### Kategori: Basit Tanımlar

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 86 | API ne demek? | BASİT | Tanım |
| 87 | CPU nedir? | BASİT | Tanım |
| 88 | HTTP ne anlama gelir? | BASİT | Tanım |
| 89 | RAM nedir? | BASİT | Tanım |
| 90 | URL açılımı nedir? | BASİT | Tanım |
| 91 | SQL ne demek? | BASİT | Tanım |
| 92 | IDE nedir? | BASİT | Tanım |
| 93 | JSON ne anlama gelir? | BASİT | Tanım |
| 94 | AI ne demek? | BASİT | Tanım |
| 95 | GPU nedir? | BASİT | Tanım |
| 96 | SSH ne anlama gelir? | BASİT | Tanım |
| 97 | DNS nedir? | BASİT | Tanım |
| 98 | SSD ne demek? | BASİT | Tanım |
| 99 | IoT nedir? | BASİT | Tanım |
| 100 | VPN ne anlama gelir? | BASİT | Tanım |

### Kategori: Kısa Kod Soruları

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 101 | Python'da liste nasıl oluşturulur? | BASİT | Kod |
| 102 | JavaScript'te console.log ne işe yarar? | BASİT | Kod |
| 103 | for döngüsü syntax'ı nasıl? | BASİT | Kod |
| 104 | Python'da string nasıl ters çevrilir? | BASİT | Kod |
| 105 | if-else nasıl yazılır? | BASİT | Kod |
| 106 | Python'da dosya nasıl okunur? | BASİT | Kod |
| 107 | Array'e eleman nasıl eklenir? | BASİT | Kod |
| 108 | try-catch nasıl kullanılır? | BASİT | Kod |
| 109 | Python'da random sayı nasıl üretilir? | BASİT | Kod |
| 110 | Lambda fonksiyonu nasıl yazılır? | BASİT | Kod |
| 111 | String'i integer'a nasıl çeviririm? | BASİT | Kod |
| 112 | Dictionary'den değer nasıl alınır? | BASİT | Kod |
| 113 | List comprehension örneği ver | BASİT | Kod |
| 114 | while döngüsü nasıl yazılır? | BASİT | Kod |
| 115 | Python'da modül nasıl import edilir? | BASİT | Kod |

### Kategori: Hızlı Tavsiyeler

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 116 | En iyi Python IDE hangisi? | BASİT | Tavsiye |
| 117 | Git komutlarını nereden öğrenebilirim? | BASİT | Tavsiye |
| 118 | Hangi text editör kullanmalıyım? | BASİT | Tavsiye |
| 119 | JavaScript için iyi bir kaynak öner | BASİT | Tavsiye |
| 120 | Docker öğrenmek için video öner | BASİT | Tavsiye |
| 121 | Backend için hangi dili öğrenmeliyim? | BASİT | Tavsiye |
| 122 | CSS framework öner | BASİT | Tavsiye |
| 123 | Database için ne kullanmalıyım? | BASİT | Tavsiye |
| 124 | API test aracı öner | BASİT | Tavsiye |
| 125 | Kod formatlamak için araç öner | BASİT | Tavsiye |

### Kategori: Dosya ve Komut İşlemleri

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 126 | Klasör nasıl oluşturulur? | BASİT | Komut |
| 127 | Dosya nasıl silinir? | BASİT | Komut |
| 128 | Git commit nasıl yapılır? | BASİT | Komut |
| 129 | pip ile paket nasıl kurulur? | BASİT | Komut |
| 130 | npm start ne yapar? | BASİT | Komut |
| 131 | Docker container nasıl çalıştırılır? | BASİT | Komut |
| 132 | Terminalde dizin nasıl değiştirilir? | BASİT | Komut |
| 133 | Dosya nasıl kopyalanır? | BASİT | Komut |
| 134 | Python scripti nasıl çalıştırılır? | BASİT | Komut |
| 135 | Virtual environment nasıl aktifleştirilir? | BASİT | Komut |

### Kategori: Hata Çözümleri (Basit)

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 136 | ModuleNotFoundError hatası nedir? | BASİT | Hata |
| 137 | SyntaxError nasıl çözülür? | BASİT | Hata |
| 138 | 404 hatası ne anlama gelir? | BASİT | Hata |
| 139 | CORS hatası nedir? | BASİT | Hata |
| 140 | Null pointer exception nedir? | BASİT | Hata |
| 141 | 500 Internal Server Error ne demek? | BASİT | Hata |
| 142 | TypeError nasıl çözülür? | BASİT | Hata |
| 143 | Permission denied hatası nedir? | BASİT | Hata |
| 144 | IndentationError ne demek? | BASİT | Hata |
| 145 | Connection refused hatası nedir? | BASİT | Hata |

### Kategori: Kısa Açıklamalar

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 146 | Git ile GitHub arasındaki fark nedir? | BASİT | Açıklama |
| 147 | Frontend ve backend farkı nedir? | BASİT | Açıklama |
| 148 | HTTP ile HTTPS farkı nedir? | BASİT | Açıklama |
| 149 | == ile === farkı nedir? | BASİT | Açıklama |
| 150 | Compiler ile interpreter farkı nedir? | BASİT | Açıklama |
| 151 | Stack ile queue farkı nedir? | BASİT | Açıklama |
| 152 | RAM ile ROM farkı nedir? | BASİT | Açıklama |
| 153 | SQL ile NoSQL farkı nedir? | BASİT | Açıklama |
| 154 | GET ile POST farkı nedir? | BASİT | Açıklama |
| 155 | Public ile private farkı nedir? | BASİT | Açıklama |

### Kategori: Durum Soruları

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 156 | Backend çalışıyor mu? | BASİT | Durum |
| 157 | Bağlantı var mı? | BASİT | Durum |
| 158 | Sistem aktif mi? | BASİT | Durum |
| 159 | Database bağlı mı? | BASİT | Durum |
| 160 | API erişilebilir mi? | BASİT | Durum |
| 161 | Server çalışıyor mu? | BASİT | Durum |
| 162 | Model yüklü mü? | BASİT | Durum |
| 163 | Cache temizlendi mi? | BASİT | Durum |
| 164 | Güncellemeler yüklendi mi? | BASİT | Durum |
| 165 | Port açık mı? | BASİT | Durum |

### Kategori: Onay ve Teşekkür

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 166 | Tamam, teşekkürler | BASİT | Onay |
| 167 | Anladım, sağol | BASİT | Onay |
| 168 | Bu kadar yeterli | BASİT | Onay |
| 169 | Teşekkür ederim | BASİT | Onay |
| 170 | Harika, eyvallah | BASİT | Onay |
| 171 | OK, hallettim | BASİT | Onay |
| 172 | Çok yardımcı oldun | BASİT | Onay |
| 173 | İşime yaradı | BASİT | Onay |
| 174 | Süpersin | BASİT | Onay |
| 175 | Çözdüm, teşekkürler | BASİT | Onay |

### Kategori: Kısa Web Aramaları

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 176 | Bugün hava nasıl? | BASİT | Web/Hava |
| 177 | Dolar kuru ne? | BASİT | Web/Finans |
| 178 | Bitcoin fiyatı kaç? | BASİT | Web/Finans |
| 179 | Euro kaç TL? | BASİT | Web/Finans |
| 180 | Altın fiyatı ne kadar? | BASİT | Web/Finans |
| 181 | Borsa bugün nasıl? | BASİT | Web/Finans |
| 182 | Türkiye-İtalya maçı ne zaman? | BASİT | Web/Spor |
| 183 | En son deprem nerede oldu? | BASİT | Web/Haber |
| 184 | Bugünkü dizi saatleri | BASİT | Web/Eğlence |
| 185 | Netflix'te yeni ne var? | BASİT | Web/Eğlence |

### Kategori: Basit Liste İstekleri

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 186 | 5 popüler programlama dili say | BASİT | Liste |
| 187 | 3 Python framework'ü say | BASİT | Liste |
| 188 | Renkler listesi ver | BASİT | Liste |
| 189 | Haftanın günleri | BASİT | Liste |
| 190 | Ayların isimleri | BASİT | Liste |
| 191 | 5 NoSQL veritabanı say | BASİT | Liste |
| 192 | Türkiye'nin 7 bölgesi | BASİT | Liste |
| 193 | HTTP metodları listesi | BASİT | Liste |
| 194 | Veri tipleri listesi | BASİT | Liste |
| 195 | 5 cloud provider say | BASİT | Liste |

### Kategori: Emoji ve Format

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 196 | Kalp emojisi ver | BASİT | Emoji |
| 197 | Gülen yüz emojisi | BASİT | Emoji |
| 198 | Onay işareti emojisi | BASİT | Emoji |
| 199 | Yıldız emojisi | BASİT | Emoji |
| 200 | Ateş emojisi | BASİT | Emoji |

---

## 🔵 KAPSAMLI SORGULAR (Comprehensive Queries)

### Kategori: Eğitim ve Öğretme

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 201 | Bana analitik geometri konusunu öğret | KAPSAMLI | Eğitim |
| 202 | Machine learning'i sıfırdan anlat | KAPSAMLI | Eğitim |
| 203 | Python'u baştan sona öğret | KAPSAMLI | Eğitim |
| 204 | Docker'ı detaylı olarak açıkla | KAPSAMLI | Eğitim |
| 205 | SQL'i temelinden ileri seviyeye öğret | KAPSAMLI | Eğitim |
| 206 | React.js'i kapsamlı olarak anlat | KAPSAMLI | Eğitim |
| 207 | Git ve versiyon kontrolünü öğret | KAPSAMLI | Eğitim |
| 208 | RESTful API tasarımını anlat | KAPSAMLI | Eğitim |
| 209 | Nesne yönelimli programlamayı öğret | KAPSAMLI | Eğitim |
| 210 | Algoritma ve veri yapılarını anlat | KAPSAMLI | Eğitim |
| 211 | Kubernetes'i detaylıca açıkla | KAPSAMLI | Eğitim |
| 212 | Mikroservis mimarisini öğret | KAPSAMLI | Eğitim |
| 213 | Siber güvenlik temellerini anlat | KAPSAMLI | Eğitim |
| 214 | Blockchain teknolojisini açıkla | KAPSAMLI | Eğitim |
| 215 | Deep learning'i öğret | KAPSAMLI | Eğitim |
| 216 | Natural Language Processing'i anlat | KAPSAMLI | Eğitim |
| 217 | Computer Vision'ı detaylıca açıkla | KAPSAMLI | Eğitim |
| 218 | Lineer cebiri baştan sona anlat | KAPSAMLI | Eğitim |
| 219 | İstatistik ve olasılık konularını öğret | KAPSAMLI | Eğitim |
| 220 | Diferansiyel denklemleri anlat | KAPSAMLI | Eğitim |
| 221 | Quantum computing'i açıkla | KAPSAMLI | Eğitim |
| 222 | Fonksiyonel programlamayı öğret | KAPSAMLI | Eğitim |
| 223 | System design'ı kapsamlı anlat | KAPSAMLI | Eğitim |
| 224 | DevOps süreçlerini detaylı açıkla | KAPSAMLI | Eğitim |
| 225 | AWS servislerini kapsamlı anlat | KAPSAMLI | Eğitim |
| 226 | GraphQL'i detaylıca öğret | KAPSAMLI | Eğitim |
| 227 | TypeScript'i baştan sona anlat | KAPSAMLI | Eğitim |
| 228 | Veritabanı tasarımını öğret | KAPSAMLI | Eğitim |
| 229 | Clean Code prensiplerini anlat | KAPSAMLI | Eğitim |
| 230 | Design patterns'ları detaylı açıkla | KAPSAMLI | Eğitim |
| 231 | SOLID prensiplerini öğret | KAPSAMLI | Eğitim |
| 232 | Test Driven Development'ı anlat | KAPSAMLI | Eğitim |
| 233 | CI/CD pipeline'ını kapsamlı açıkla | KAPSAMLI | Eğitim |
| 234 | Agile metodolojisini detaylı anlat | KAPSAMLI | Eğitim |
| 235 | Networking temellerini öğret | KAPSAMLI | Eğitim |
| 236 | Operating Systems konularını anlat | KAPSAMLI | Eğitim |
| 237 | Compiler tasarımını açıkla | KAPSAMLI | Eğitim |
| 238 | WebSocket ve real-time sistemleri öğret | KAPSAMLI | Eğitim |
| 239 | OAuth ve authentication'ı anlat | KAPSAMLI | Eğitim |
| 240 | Caching stratejilerini öğret | KAPSAMLI | Eğitim |

### Kategori: Rapor Oluşturma

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 241 | 2025 yılındaki AI gelişmelerini kapsayan bir rapor oluştur | KAPSAMLI | Rapor |
| 242 | Türkiye'nin teknoloji sektörü hakkında detaylı rapor hazırla | KAPSAMLI | Rapor |
| 243 | Startup ekosistemi analiz raporu yaz | KAPSAMLI | Rapor |
| 244 | E-ticaret trendleri hakkında kapsamlı rapor hazırla | KAPSAMLI | Rapor |
| 245 | Siber güvenlik tehditleri raporu oluştur | KAPSAMLI | Rapor |
| 246 | Cloud computing market analizi yap | KAPSAMLI | Rapor |
| 247 | Fintech sektörü hakkında detaylı rapor yaz | KAPSAMLI | Rapor |
| 248 | Sürdürülebilirlik ve teknoloji raporu hazırla | KAPSAMLI | Rapor |
| 249 | Uzaktan çalışma trendleri analiz raporu | KAPSAMLI | Rapor |
| 250 | Mobil uygulama pazarı raporu oluştur | KAPSAMLI | Rapor |
| 251 | Yapay zeka etiği hakkında kapsamlı rapor yaz | KAPSAMLI | Rapor |
| 252 | Gaming industry analiz raporu hazırla | KAPSAMLI | Rapor |
| 253 | EdTech sektörü hakkında detaylı rapor | KAPSAMLI | Rapor |
| 254 | HealthTech gelişmeleri raporu oluştur | KAPSAMLI | Rapor |
| 255 | Metaverse ve Web3 analiz raporu yaz | KAPSAMLI | Rapor |
| 256 | Otonom araçlar teknolojisi raporu hazırla | KAPSAMLI | Rapor |
| 257 | 5G ve telekomünikasyon analizi yap | KAPSAMLI | Rapor |
| 258 | Open source ekosistemi raporu oluştur | KAPSAMLI | Rapor |
| 259 | Veri gizliliği ve KVKK raporu yaz | KAPSAMLI | Rapor |
| 260 | Programming languages popularity raporu | KAPSAMLI | Rapor |

### Kategori: Proje Geliştirme

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 261 | Sıfırdan bir e-ticaret sitesi nasıl yapılır? | KAPSAMLI | Proje |
| 262 | Full-stack web uygulaması geliştirme rehberi | KAPSAMLI | Proje |
| 263 | Mobil uygulama nasıl geliştirilir? | KAPSAMLI | Proje |
| 264 | Blog platformu nasıl oluşturulur? | KAPSAMLI | Proje |
| 265 | Chat uygulaması nasıl yapılır? | KAPSAMLI | Proje |
| 266 | API gateway nasıl tasarlanır? | KAPSAMLI | Proje |
| 267 | Authentication sistemi nasıl kurulur? | KAPSAMLI | Proje |
| 268 | Real-time dashboard nasıl yapılır? | KAPSAMLI | Proje |
| 269 | CI/CD pipeline nasıl kurulur? | KAPSAMLI | Proje |
| 270 | Microservices architecture nasıl tasarlanır? | KAPSAMLI | Proje |
| 271 | Monitoring ve logging sistemi nasıl kurulur? | KAPSAMLI | Proje |
| 272 | Search engine nasıl yapılır? | KAPSAMLI | Proje |
| 273 | Recommendation system nasıl geliştirilir? | KAPSAMLI | Proje |
| 274 | Payment integration nasıl yapılır? | KAPSAMLI | Proje |
| 275 | Multi-tenant SaaS uygulaması nasıl yapılır? | KAPSAMLI | Proje |
| 276 | GraphQL API nasıl tasarlanır? | KAPSAMLI | Proje |
| 277 | Serverless uygulama nasıl geliştirilir? | KAPSAMLI | Proje |
| 278 | PWA nasıl oluşturulur? | KAPSAMLI | Proje |
| 279 | Chrome extension nasıl yapılır? | KAPSAMLI | Proje |
| 280 | VS Code extension nasıl geliştirilir? | KAPSAMLI | Proje |
| 281 | Discord bot nasıl yapılır? | KAPSAMLI | Proje |
| 282 | Telegram bot nasıl geliştirilir? | KAPSAMLI | Proje |
| 283 | Web scraper nasıl yapılır? | KAPSAMLI | Proje |
| 284 | Data pipeline nasıl tasarlanır? | KAPSAMLI | Proje |
| 285 | ETL süreci nasıl oluşturulur? | KAPSAMLI | Proje |
| 286 | Machine learning model deployment nasıl yapılır? | KAPSAMLI | Proje |
| 287 | A/B testing sistemi nasıl kurulur? | KAPSAMLI | Proje |
| 288 | Feature flag sistemi nasıl tasarlanır? | KAPSAMLI | Proje |
| 289 | Rate limiting sistemi nasıl yapılır? | KAPSAMLI | Proje |
| 290 | Queue-based system nasıl tasarlanır? | KAPSAMLI | Proje |

### Kategori: Analiz ve Karşılaştırma

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 291 | React vs Vue vs Angular detaylı karşılaştırması | KAPSAMLI | Karşılaştırma |
| 292 | Python vs JavaScript: Hangisi daha iyi? | KAPSAMLI | Karşılaştırma |
| 293 | PostgreSQL vs MySQL vs MongoDB karşılaştırması | KAPSAMLI | Karşılaştırma |
| 294 | Docker vs Kubernetes: Ne zaman hangisi? | KAPSAMLI | Karşılaştırma |
| 295 | REST vs GraphQL detaylı analiz | KAPSAMLI | Karşılaştırma |
| 296 | AWS vs Azure vs GCP karşılaştırması | KAPSAMLI | Karşılaştırma |
| 297 | Monolith vs Microservices analizi | KAPSAMLI | Karşılaştırma |
| 298 | SQL vs NoSQL: Avantajlar ve dezavantajlar | KAPSAMLI | Karşılaştırma |
| 299 | Native vs Hybrid vs Cross-platform karşılaştırması | KAPSAMLI | Karşılaştırma |
| 300 | TCP vs UDP detaylı karşılaştırma | KAPSAMLI | Karşılaştırma |
| 301 | Git workflow'ları karşılaştırması | KAPSAMLI | Karşılaştırma |
| 302 | Scrum vs Kanban detaylı analiz | KAPSAMLI | Karşılaştırma |
| 303 | Jest vs Mocha vs Pytest karşılaştırması | KAPSAMLI | Karşılaştırma |
| 304 | Webpack vs Vite vs esbuild analizi | KAPSAMLI | Karşılaştırma |
| 305 | Redis vs Memcached karşılaştırması | KAPSAMLI | Karşılaştırma |
| 306 | Nginx vs Apache detaylı analiz | KAPSAMLI | Karşılaştırma |
| 307 | FastAPI vs Django vs Flask karşılaştırması | KAPSAMLI | Karşılaştırma |
| 308 | Next.js vs Nuxt.js vs SvelteKit analizi | KAPSAMLI | Karşılaştırma |
| 309 | Tailwind vs Bootstrap vs Material UI karşılaştırması | KAPSAMLI | Karşılaştırma |
| 310 | Prisma vs TypeORM vs Sequelize analizi | KAPSAMLI | Karşılaştırma |

### Kategori: Strateji ve Planlama

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 311 | Startup için teknoloji stratejisi oluştur | KAPSAMLI | Strateji |
| 312 | 6 aylık yazılım geliştirme roadmap'i hazırla | KAPSAMLI | Planlama |
| 313 | DevOps dönüşüm planı oluştur | KAPSAMLI | Strateji |
| 314 | Cloud migration stratejisi hazırla | KAPSAMLI | Strateji |
| 315 | Technical debt azaltma planı | KAPSAMLI | Planlama |
| 316 | Scaling stratejisi oluştur | KAPSAMLI | Strateji |
| 317 | Security hardening planı hazırla | KAPSAMLI | Planlama |
| 318 | Performance optimization stratejisi | KAPSAMLI | Strateji |
| 319 | Team growth ve hiring planı | KAPSAMLI | Planlama |
| 320 | Knowledge transfer stratejisi | KAPSAMLI | Strateji |
| 321 | Legacy system modernization planı | KAPSAMLI | Planlama |
| 322 | API versioning stratejisi | KAPSAMLI | Strateji |
| 323 | Data governance planı oluştur | KAPSAMLI | Planlama |
| 324 | Disaster recovery stratejisi hazırla | KAPSAMLI | Strateji |
| 325 | Cost optimization planı | KAPSAMLI | Planlama |
| 326 | Innovation ve R&D stratejisi | KAPSAMLI | Strateji |
| 327 | Open source contribution planı | KAPSAMLI | Planlama |
| 328 | Documentation stratejisi | KAPSAMLI | Strateji |
| 329 | Code review process planı | KAPSAMLI | Planlama |
| 330 | Testing strategy ve QA planı | KAPSAMLI | Strateji |

### Kategori: Problem Çözme (Karmaşık)

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 331 | Sistemimde memory leak var, nasıl debug ederim? | KAPSAMLI | Debug |
| 332 | Database performance sorunlarını nasıl çözerim? | KAPSAMLI | Optimizasyon |
| 333 | Microservices iletişim sorunlarını nasıl debug ederim? | KAPSAMLI | Debug |
| 334 | Race condition problemini nasıl tespit edip çözerim? | KAPSAMLI | Debug |
| 335 | N+1 query problemini nasıl çözerim? | KAPSAMLI | Optimizasyon |
| 336 | Deadlock sorununu nasıl tespit edip çözerim? | KAPSAMLI | Debug |
| 337 | High availability nasıl sağlanır? | KAPSAMLI | Mimari |
| 338 | Zero-downtime deployment nasıl yapılır? | KAPSAMLI | DevOps |
| 339 | DDoS saldırılarına karşı nasıl korunurum? | KAPSAMLI | Güvenlik |
| 340 | Data consistency sorunlarını nasıl çözerim? | KAPSAMLI | Veritabanı |
| 341 | Distributed system debugging nasıl yapılır? | KAPSAMLI | Debug |
| 342 | Container networking sorunlarını nasıl çözerim? | KAPSAMLI | DevOps |
| 343 | SSL/TLS certificate sorunlarını nasıl debug ederim? | KAPSAMLI | Güvenlik |
| 344 | Kubernetes pod crash loop nasıl çözülür? | KAPSAMLI | DevOps |
| 345 | WebSocket connection drop sorunları | KAPSAMLI | Debug |
| 346 | Cache invalidation problemleri nasıl çözülür? | KAPSAMLI | Optimizasyon |
| 347 | Time zone ve date handling sorunları | KAPSAMLI | Debug |
| 348 | Character encoding problemleri nasıl çözülür? | KAPSAMLI | Debug |
| 349 | CORS ve security header sorunları | KAPSAMLI | Güvenlik |
| 350 | Load balancer configuration sorunları | KAPSAMLI | DevOps |

### Kategori: Kod İnceleme ve Refactoring

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 351 | Bu kodu review et ve iyileştirmeler öner | KAPSAMLI | Code Review |
| 352 | Bu fonksiyonu refactor et | KAPSAMLI | Refactoring |
| 353 | Bu class'ı SOLID prensiplere göre düzenle | KAPSAMLI | Refactoring |
| 354 | Bu kodu daha okunabilir hale getir | KAPSAMLI | Code Review |
| 355 | Bu algoritmayı optimize et | KAPSAMLI | Optimizasyon |
| 356 | Bu koda unit test yaz | KAPSAMLI | Testing |
| 357 | Bu kodu async/await ile yeniden yaz | KAPSAMLI | Refactoring |
| 358 | Bu monolith'i microservice'lere böl | KAPSAMLI | Mimari |
| 359 | Bu SQL query'yi optimize et | KAPSAMLI | Optimizasyon |
| 360 | Bu component'i reusable hale getir | KAPSAMLI | Refactoring |
| 361 | Bu kodu type-safe hale getir | KAPSAMLI | Refactoring |
| 362 | Bu legacy kodu modernize et | KAPSAMLI | Refactoring |
| 363 | Bu API endpoint'ini güvenli hale getir | KAPSAMLI | Güvenlik |
| 364 | Bu kodu daha testable yap | KAPSAMLI | Refactoring |
| 365 | Bu fonksiyonu error handling ile güçlendir | KAPSAMLI | Refactoring |

### Kategori: Mimari ve Tasarım

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 366 | E-ticaret uygulaması için mimari tasarla | KAPSAMLI | Mimari |
| 367 | Social media platformu için system design yap | KAPSAMLI | Mimari |
| 368 | Real-time chat uygulaması mimarisi | KAPSAMLI | Mimari |
| 369 | Video streaming platformu tasarımı | KAPSAMLI | Mimari |
| 370 | Payment processing system mimarisi | KAPSAMLI | Mimari |
| 371 | Notification system tasarımı | KAPSAMLI | Mimari |
| 372 | Analytics platform mimarisi | KAPSAMLI | Mimari |
| 373 | Content management system tasarımı | KAPSAMLI | Mimari |
| 374 | Search engine mimarisi | KAPSAMLI | Mimari |
| 375 | Recommendation engine tasarımı | KAPSAMLI | Mimari |
| 376 | URL shortener system design | KAPSAMLI | Mimari |
| 377 | Rate limiter tasarımı | KAPSAMLI | Mimari |
| 378 | Distributed cache system mimarisi | KAPSAMLI | Mimari |
| 379 | Message queue system tasarımı | KAPSAMLI | Mimari |
| 380 | File storage system mimarisi | KAPSAMLI | Mimari |
| 381 | Authentication service tasarımı | KAPSAMLI | Mimari |
| 382 | API gateway mimarisi | KAPSAMLI | Mimari |
| 383 | Logging and monitoring system tasarımı | KAPSAMLI | Mimari |
| 384 | Event-driven architecture tasarımı | KAPSAMLI | Mimari |
| 385 | CQRS ve Event Sourcing mimarisi | KAPSAMLI | Mimari |

### Kategori: Araştırma ve Keşif

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 386 | GPT-4 ve Claude arasındaki farkları araştır | KAPSAMLI | Araştırma |
| 387 | Transformer architecture'ı detaylı açıkla | KAPSAMLI | Araştırma |
| 388 | Vector database'leri araştır ve karşılaştır | KAPSAMLI | Araştırma |
| 389 | LLM fine-tuning yöntemlerini araştır | KAPSAMLI | Araştırma |
| 390 | RAG (Retrieval Augmented Generation) detaylı analiz | KAPSAMLI | Araştırma |
| 391 | Prompt engineering tekniklerini araştır | KAPSAMLI | Araştırma |
| 392 | AI agents ve orchestration araştırması | KAPSAMLI | Araştırma |
| 393 | Edge computing teknolojilerini araştır | KAPSAMLI | Araştırma |
| 394 | WebAssembly'nin geleceğini araştır | KAPSAMLI | Araştırma |
| 395 | Rust'ın popülerleşme nedenlerini araştır | KAPSAMLI | Araştırma |
| 396 | Zero-knowledge proof'ları araştır | KAPSAMLI | Araştırma |
| 397 | Homomorphic encryption'ı araştır | KAPSAMLI | Araştırma |
| 398 | Federated learning'i detaylı araştır | KAPSAMLI | Araştırma |
| 399 | MLOps best practices araştırması | KAPSAMLI | Araştırma |
| 400 | Low-code/No-code platformlarını araştır | KAPSAMLI | Araştırma |

### Kategori: Tutorial ve Rehber

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 401 | Sıfırdan production-ready API nasıl yazılır? | KAPSAMLI | Tutorial |
| 402 | Docker ile geliştirme ortamı kurma rehberi | KAPSAMLI | Rehber |
| 403 | AWS'de serverless uygulama deploy etme tutorial'ı | KAPSAMLI | Tutorial |
| 404 | Kubernetes cluster kurulum rehberi | KAPSAMLI | Rehber |
| 405 | GitHub Actions ile CI/CD kurma tutorial'ı | KAPSAMLI | Tutorial |
| 406 | PostgreSQL performance tuning rehberi | KAPSAMLI | Rehber |
| 407 | React application testing tutorial'ı | KAPSAMLI | Tutorial |
| 408 | Linux server hardening rehberi | KAPSAMLI | Rehber |
| 409 | SSL certificate kurulum tutorial'ı | KAPSAMLI | Tutorial |
| 410 | Nginx reverse proxy kurulum rehberi | KAPSAMLI | Rehber |
| 411 | Redis cluster kurulum tutorial'ı | KAPSAMLI | Tutorial |
| 412 | Elasticsearch kullanım rehberi | KAPSAMLI | Rehber |
| 413 | Prometheus ve Grafana monitoring tutorial'ı | KAPSAMLI | Tutorial |
| 414 | Terraform ile infrastructure as code rehberi | KAPSAMLI | Rehber |
| 415 | Jest ile test yazma tutorial'ı | KAPSAMLI | Tutorial |
| 416 | Clean architecture implementation rehberi | KAPSAMLI | Rehber |
| 417 | OAuth2 implementation tutorial'ı | KAPSAMLI | Tutorial |
| 418 | WebSocket implementation rehberi | KAPSAMLI | Rehber |
| 419 | GraphQL schema design tutorial'ı | KAPSAMLI | Tutorial |
| 420 | Database migration best practices rehberi | KAPSAMLI | Rehber |

### Kategori: Kapsamlı Açıklamalar

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 421 | Event loop nasıl çalışır, detaylı açıkla | KAPSAMLI | Açıklama |
| 422 | JavaScript closure'ları derinlemesine anlat | KAPSAMLI | Açıklama |
| 423 | Database indexing nasıl çalışır? | KAPSAMLI | Açıklama |
| 424 | Garbage collection mekanizmasını açıkla | KAPSAMLI | Açıklama |
| 425 | TCP/IP protokolünü detaylı anlat | KAPSAMLI | Açıklama |
| 426 | Virtual memory nasıl çalışır? | KAPSAMLI | Açıklama |
| 427 | Cryptographic hashing'i detaylı açıkla | KAPSAMLI | Açıklama |
| 428 | DNS resolution sürecini anlat | KAPSAMLI | Açıklama |
| 429 | Load balancing algoritmalarını açıkla | KAPSAMLI | Açıklama |
| 430 | Consensus algorithms (Raft, Paxos) anlat | KAPSAMLI | Açıklama |
| 431 | CAP theorem'i detaylıca açıkla | KAPSAMLI | Açıklama |
| 432 | ACID properties'i derinlemesine anlat | KAPSAMLI | Açıklama |
| 433 | Database sharding'i detaylı açıkla | KAPSAMLI | Açıklama |
| 434 | Container isolation nasıl çalışır? | KAPSAMLI | Açıklama |
| 435 | Kernel vs User space'i anlat | KAPSAMLI | Açıklama |
| 436 | Process vs Thread farkını detaylı açıkla | KAPSAMLI | Açıklama |
| 437 | Memory management'ı derinlemesine anlat | KAPSAMLI | Açıklama |
| 438 | Compiler optimization tekniklerini açıkla | KAPSAMLI | Açıklama |
| 439 | JIT compilation nasıl çalışır? | KAPSAMLI | Açıklama |
| 440 | Reactive programming paradigmasını anlat | KAPSAMLI | Açıklama |

### Kategori: Döküman ve Spec Yazımı

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 441 | API documentation template oluştur | KAPSAMLI | Döküman |
| 442 | Technical specification document yaz | KAPSAMLI | Döküman |
| 443 | Architecture decision record (ADR) template | KAPSAMLI | Döküman |
| 444 | Project README template oluştur | KAPSAMLI | Döküman |
| 445 | Runbook template hazırla | KAPSAMLI | Döküman |
| 446 | Incident response playbook yaz | KAPSAMLI | Döküman |
| 447 | Code review guidelines dökümanı | KAPSAMLI | Döküman |
| 448 | Onboarding documentation hazırla | KAPSAMLI | Döküman |
| 449 | API design guidelines yaz | KAPSAMLI | Döküman |
| 450 | Security policy document oluştur | KAPSAMLI | Döküman |
| 451 | Change management procedure dökümanı | KAPSAMLI | Döküman |
| 452 | Deployment checklist hazırla | KAPSAMLI | Döküman |
| 453 | Testing strategy document yaz | KAPSAMLI | Döküman |
| 454 | Data retention policy oluştur | KAPSAMLI | Döküman |
| 455 | SLA (Service Level Agreement) template | KAPSAMLI | Döküman |

### Kategori: Kod Yazımı (Kapsamlı)

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 456 | Complete authentication system yaz | KAPSAMLI | Kod |
| 457 | Full CRUD API with validation yaz | KAPSAMLI | Kod |
| 458 | Real-time notification service kodu | KAPSAMLI | Kod |
| 459 | Complete e-commerce cart system | KAPSAMLI | Kod |
| 460 | User management module yaz | KAPSAMLI | Kod |
| 461 | File upload service with validation | KAPSAMLI | Kod |
| 462 | Rate limiting middleware yaz | KAPSAMLI | Kod |
| 463 | Complete logging service | KAPSAMLI | Kod |
| 464 | Search functionality with filters | KAPSAMLI | Kod |
| 465 | Pagination component with sorting | KAPSAMLI | Kod |
| 466 | Form validation library yaz | KAPSAMLI | Kod |
| 467 | State management solution | KAPSAMLI | Kod |
| 468 | API client with retry logic | KAPSAMLI | Kod |
| 469 | Caching layer implementation | KAPSAMLI | Kod |
| 470 | Database migration system yaz | KAPSAMLI | Kod |
| 471 | Job queue processing system | KAPSAMLI | Kod |
| 472 | WebSocket chat implementation | KAPSAMLI | Kod |
| 473 | OAuth provider integration | KAPSAMLI | Kod |
| 474 | Email templating system | KAPSAMLI | Kod |
| 475 | PDF generation service | KAPSAMLI | Kod |

### Kategori: Kariyer ve Kişisel Gelişim

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 476 | Junior'dan senior'a geçiş yol haritası | KAPSAMLI | Kariyer |
| 477 | Software architect olma rehberi | KAPSAMLI | Kariyer |
| 478 | Technical interview hazırlık planı | KAPSAMLI | Kariyer |
| 479 | Portfolio geliştirme stratejisi | KAPSAMLI | Kariyer |
| 480 | Open source contribution başlangıç rehberi | KAPSAMLI | Kariyer |
| 481 | Remote work productivity stratejileri | KAPSAMLI | Verimlilik |
| 482 | Technical writing skill development | KAPSAMLI | Gelişim |
| 483 | Public speaking for developers rehberi | KAPSAMLI | Gelişim |
| 484 | Side project management stratejisi | KAPSAMLI | Verimlilik |
| 485 | Burnout prevention ve recovery | KAPSAMLI | Wellbeing |
| 486 | Freelance geçiş stratejisi | KAPSAMLI | Kariyer |
| 487 | Tech lead olma yol haritası | KAPSAMLI | Kariyer |
| 488 | Startup vs corporate career karşılaştırması | KAPSAMLI | Kariyer |
| 489 | Continuous learning stratejisi | KAPSAMLI | Gelişim |
| 490 | Networking ve community building | KAPSAMLI | Kariyer |

### Kategori: Konsept ve Teori

| # | Sorgu | Kategori | Beklenen Yanıt Tipi |
|---|-------|----------|---------------------|
| 491 | Domain Driven Design'ı detaylı anlat | KAPSAMLI | Konsept |
| 492 | Hexagonal architecture'ı açıkla | KAPSAMLI | Konsept |
| 493 | Event sourcing pattern'ını anlat | KAPSAMLI | Konsept |
| 494 | CQRS pattern'ını detaylı açıkla | KAPSAMLI | Konsept |
| 495 | Saga pattern'ını anlat | KAPSAMLI | Konsept |
| 496 | Circuit breaker pattern'ı açıkla | KAPSAMLI | Konsept |
| 497 | Strangler fig pattern'ını anlat | KAPSAMLI | Konsept |
| 498 | Bulkhead pattern'ını açıkla | KAPSAMLI | Konsept |
| 499 | Retry pattern ve backoff strategies | KAPSAMLI | Konsept |
| 500 | Twelve-factor app methodology | KAPSAMLI | Konsept |

---

## 📊 İSTATİSTİKLER

### Toplam Sorgu Sayısı: 500

| Kategori | Sayı | Yüzde |
|----------|------|-------|
| BASİT | 200 | 40% |
| KAPSAMLI | 300 | 60% |

### BASİT Kategorilerin Dağılımı

| Alt Kategori | Sayı |
|--------------|------|
| Selamlaşma ve Günlük Konuşma | 20 |
| Tarih ve Zaman Soruları | 15 |
| Basit Faktüel Sorular | 20 |
| Basit Hesaplamalar | 15 |
| Evet/Hayır Soruları | 15 |
| Basit Tanımlar | 15 |
| Kısa Kod Soruları | 15 |
| Hızlı Tavsiyeler | 10 |
| Dosya ve Komut İşlemleri | 10 |
| Hata Çözümleri (Basit) | 10 |
| Kısa Açıklamalar | 10 |
| Durum Soruları | 10 |
| Onay ve Teşekkür | 10 |
| Kısa Web Aramaları | 10 |
| Basit Liste İstekleri | 10 |
| Emoji ve Format | 5 |

### KAPSAMLI Kategorilerin Dağılımı

| Alt Kategori | Sayı |
|--------------|------|
| Eğitim ve Öğretme | 40 |
| Rapor Oluşturma | 20 |
| Proje Geliştirme | 30 |
| Analiz ve Karşılaştırma | 20 |
| Strateji ve Planlama | 20 |
| Problem Çözme (Karmaşık) | 20 |
| Kod İnceleme ve Refactoring | 15 |
| Mimari ve Tasarım | 20 |
| Araştırma ve Keşif | 15 |
| Tutorial ve Rehber | 20 |
| Kapsamlı Açıklamalar | 20 |
| Döküman ve Spec Yazımı | 15 |
| Kod Yazımı (Kapsamlı) | 20 |
| Kariyer ve Kişisel Gelişim | 15 |
| Konsept ve Teori | 10 |

---

## 🔍 SINIFLANDIRMA İPUÇLARI

### BASİT Yanıt İşaretleyicileri (Keywords/Patterns)

```
Anahtar Kelimeler:
- ne? (tek cevaplı)
- kaç?
- hangisi?
- var mı?
- mı/mi/mu/mü?
- nedir?
- nasıl? (tek satırlık)
- selam, merhaba, hey
- teşekkürler, sağol
- tamam, ok
- bugün, yarın, dün
- saat, tarih
- farkı nedir (2 şey)
- listele (5'ten az)
- say (5'ten az)

Karakter Sayısı: Genellikle < 50 karakter
Kelime Sayısı: Genellikle < 10 kelime
Cümle Yapısı: Tek soru cümlesi
```

### KAPSAMLI Yanıt İşaretleyicileri (Keywords/Patterns)

```
Anahtar Kelimeler:
- öğret
- anlat
- açıkla (detaylı)
- rapor oluştur/hazırla
- karşılaştır (2'den fazla)
- analiz et
- tasarla
- planla
- strateji
- roadmap
- rehber
- tutorial
- kapsamlı
- detaylı
- derinlemesine
- sıfırdan
- baştan sona
- step by step
- A'dan Z'ye
- nasıl yapılır (proje)
- system design
- mimari
- refactor et
- optimize et
- debug et
- araştır
- review et
- yol haritası
- kurulum rehberi
- best practices

Karakter Sayısı: Genellikle > 50 karakter
Kelime Sayısı: Genellikle > 10 kelime
Cümle Yapısı: Birden fazla beklenti içeren
```

---

## 🎯 KULLANIM KILAVUZU

### 1. Basit Yanıt Mode Aktivasyonu
Sistem aşağıdaki durumlarda **BASİT** mod kullanmalı:
- Tek faktüel bilgi sorulduğunda
- Evet/Hayır cevabı yeterli olduğunda
- Selamlaşma ve günlük konuşmada
- Basit hesaplama istendiğinde
- Kısa kod snippet'i istendiğinde
- Onay/teşekkür mesajlarında

### 2. Kapsamlı Yanıt Mode Aktivasyonu
Sistem aşağıdaki durumlarda **KAPSAMLI** mod kullanmalı:
- "Öğret", "anlat", "açıkla" fiilleri varsa
- Rapor/analiz istendiğinde
- Proje geliştirme sorusu olduğunda
- Karşılaştırma (3+ öğe) istendiğinde
- Strateji/planlama gerektiğinde
- Tutorial/rehber istendiğinde
- Code review/refactoring istendiğinde
- System design/mimari sorusu olduğunda

---

## 📝 EK: EDGE CASES

### Belirsiz Sorgular (Context'e Bağlı)

| Sorgu | Olası Kategori | Belirleyici Faktör |
|-------|----------------|-------------------|
| Python nedir? | BASİT | Sadece tanım isteniyorsa |
| Python nedir? | KAPSAMLI | Detaylı açıklama isteniyorsa |
| Error nasıl çözülür? | BASİT | Spesifik error için |
| Error handling nasıl yapılır? | KAPSAMLI | Genel yaklaşım için |
| Array nedir? | BASİT | Tanım için |
| Array'leri anlat | KAPSAMLI | Detaylı açıklama için |

### Hibrit Sorgular

Bazı sorgular hem basit hem kapsamlı olabilir. Bu durumda:
1. Kullanıcının önceki sorularına bak
2. Session context'ini değerlendir
3. Belirsizlik varsa orta uzunlukta yanıt ver
4. Gerekirse kullanıcıya sor: "Kısa mı detaylı mı açıklayayım?"

---

## 🔄 VERSİYON GEÇMİŞİ

| Versiyon | Tarih | Değişiklikler |
|----------|-------|---------------|
| 1.0 | 2026-01-20 | İlk versiyon - 500 sorgu |

---

## 📌 NOTLAR

1. Bu veri seti sürekli güncellenmeli ve genişletilmelidir
2. Kullanıcı geri bildirimleriyle iyileştirilmelidir
3. Yeni kategoriler eklendikçe güncellenmelidir
4. Farklı diller için versiyonlar oluşturulabilir
5. Machine learning modeli eğitimi için kullanılabilir

---

*Bu dosya Enterprise AI Assistant için otomatik sorgu sınıflandırma sistemi geliştirmek amacıyla oluşturulmuştur.*
