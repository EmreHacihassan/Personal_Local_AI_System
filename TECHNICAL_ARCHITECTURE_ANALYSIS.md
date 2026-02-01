# Personal Local AI System - Nihai Teknik Mimari ve Mühendislik Analizi

**Yazar:** AI Architecture Team
**Tarih:** 31 Ocak 2026
**Sistem Spesifikasyonu:** NVIDIA RTX 4070 (8GB VRAM) | Yerel Öncelikli Mimari

Bu döküman, **Personal Local AI System** projesinin en kapsamlı teknik incelemesini içerir. Bu analizde, sistemin kaynak kodlarında yer alan algoritmalar, mimari kararlar, veritabanı stratejileri ve mühendislik çözümleri, kod blokları kullanılmadan, tamamen teknik ve betimleyici bir dille detaylandırılmıştır. Raporun amacı, sistemin sadece "ne yaptığını" değil, "nasıl düşündüğünü", donanım limitlerini nasıl aştığını ve dağıtık bilişsel mimarisini nasıl yönettiğini ortaya koymaktır. Rapor, sistem başlatma süreçlerinden veri kalıcılığına, güvenlikten Graph RAG entegrasyonuna kadar her katmanı kapsar.

---

## 1. Mimari Felsefe ve Çekirdek Tasarım İlkeleri

Sıradan yekpare (monolitik) yapay zeka sistemlerinin aksine, bu proje **"Merkezi Zeka, Dağıtık Yürütme" (Centralized Intelligence, Distributed Execution)** felsefesi üzerine inşa edilmiştir. Bu yaklaşımın temel nedeni, tüketici sınıfı donanımların (8GB VRAM) getirdiği fiziksel sınırlardır. Tek bir devasa modelin (örneğin 70 milyar parametreli bir modelin) tüm bilişsel yükü tek başına sırtlanması yerine, sistem, her biri belirli bir görevde uzmanlaşmış daha küçük ve çevik modellerden oluşan bir **"Uzmanlar Ağı" (Network of Experts)** olarak tasarlanmıştır.

Bu tasarımda sistem, tek bir zeka gibi davranır ancak arka planda sürekli olarak modeller arası görev değişimi yapar. Kullanıcı arayüzü ile etkileşimde buluna "Chat Modeli", gerektiğinde yerini "Görüntü İşleme Modeline" veya "Kod Üretim Modeline" bırakır ve işlem bitince tekrar kontrolü devralır. Bu dinamik yükleme ve boşaltma stratejisi, sınırlı bellekte sınırsız yetenek illüzyonu yaratmanın anahtarıdır. Kullanıcıya kesintisiz ve tutarlı bir "persona" sunulurken, arka planda dinamik bir orkestrasyon motoru çalışır.

---

## 2. Sistem Başlatma ve Sağlık Kontrolleri (System Initialization & Health Checks)

Sistemin "ayağa kalkması" basit bir script çalışmasından çok daha karmaşıktır. Güvenilir ve hataya dayanıklı bir operasyon için çok katmanlı bir başlatma sekansı uygulanır.

### 2.1. Donanım Keşfi ve Yetenek Müzakeresi
Başlatma anında sistem önce **Donanım Teşhis Modülü**nü çalıştırır. Bu modül, mevcut GPU belleğini (VRAM), CUDA çekirdek sayısını ve sistem RAM'ini sorgular. Bu veriler, sistemin hangi "profilde" çalışacağını belirler. Örneğin, eğer kullanılabilir VRAM 6GB'ın altındaysa, sistem otomatik olarak "Low-Memory" moduna geçer; bu modda 8B modeller yerine 4B modeller varsayılan olarak seçilir ve görüntü işleme çözünürlüğü düşürülür. Bu "Yetenek Müzakeresi" (Capability Negotiation), sistemin farklı donanımlarda çökmeden çalışabilmesini sağlayan esneklik katmanıdır.

### 2.2. Servis Bağımlılık Ağacı
Arka uç servisleri (Veritabanı, LLM Motoru, WebSocket Sunucusu) rastgele değil, bir **Topolojik Bağımlılık Sırası** ile başlatılır. Önce "Yapılandırma Yöneticisi" yüklenir, ardından "Loglama Servisi" aktif edilir (böylece açılış hataları kaydedilebilir), sonra "Veritabanı Katmanı" bağlanır. En son adımda, en ağır yük olan "LLM Motoru" belleğe yüklenir. Eğer veritabanı bağlantısı başarısız olursa, sistem LLM'i yüklemeye çalışıp kaynak israf etmez; bunun yerine "Güvenli Mod"da açılarak kullanıcıya onarım araçları sunar.

---

## 3. Hibrit Zeka ve Adaptif Yönlendirme Motoru (Adaptive MoE Router)

Sistemin beyni olarak nitelendirilebilecek modül, statik mantık operatörleri yerine olasılıksal hesaplamalar yapan **Adaptif Uzmanlar Karışımı (Adaptive Mixture of Experts)** yönlendiricisidir. Bu motorun temel görevi, gelen her kullanıcı sorgusu için maliyet, hız ve kalite üçgeninde en optimum yürütme yolunu belirlemektir.

### 3.1. Sorgu Analizinin Matematiği ve Özellik Çıkarımı
Kullanıcıdan gelen ham metin, herhangi bir yapay zeka modeline gönderilmeden önce, çok katmanlı bir analiz sürecinden geçer. Bu süreçte, sorgunun dilsel ve yapısal özellikleri çıkarılarak bir "Feature Vector" oluşturulur.

Sistem ilk olarak **Karmaşıklık Analizi** yapar. Bu analiz, sadece kelime sayısına bakmakla sınırlı değildir. Cümle içerisindeki mantıksal bağlaçların (çünkü, ancak, buna rağmen gibi) yoğunluğu ölçülür. Bu bağlaçların varlığı, sorgunun basit bir bilgi isteği değil, bir muhakeme (reasoning) süreci gerektirdiğini işaret eder. Ayrıca, sorgu içerisinde teknik terimlerin, kod bloklarının veya matematiksel notasyonların varlığı, alan tespiti için kritik ipuçları sağlar. Soru eklerinin ve soru zarflarının ("nedir" ile "nasıl" arasındaki fark gibi) analizi ile kullanıcının yüzeysel bir cevap mı yoksa derinlemesine bir açıklama mı beklediği matematiksel bir skora dönüştürülür.

### 3.2. Ağırlıklı Skorlama ve Karar Mekanizması
Analiz adımından elde edilen veriler, sistemde tanımlı her bir "Uzman" için bir uygunluk skoruna dönüştürülür. Bu skorlama algoritması, üç ana faktörün ağırlıklı toplamı üzerine kuruludur:

1.  **Yetenek Örtüşmesi (Capability Match):** Uzmanın sahip olduğu yetenekler (örneğin görsel algı, internet erişimi, kod yorumlama) ile sorgunun gereksinimleri karşılaştırılır. Eğer sorguda bir resim dosyası varsa, görüntü işleme yeteneği olmayan tüm metin tabanlı uzmanların skoru radikal şekilde düşürülür.
2.  **Kalite ve Karmaşıklık Dengesi (Quality-Complexity Logic):** Bu faktör, sistemin verimliliğini sağlar. Çok basit bir "Merhaba" mesajı için devasa bir modelin kullanılması sisteme "aşırı güç kullanımı" (overkill) cezası olarak yansır ve skor düşürülür. Tam tersine, karmaşık bir fizik problemi için küçük bir modelin seçilmesi "yetersiz güç" (underkill) cezası alır. Sistem, göreve en uygun "büyüklükteki" modeli seçmeye eğilimlidir.
3.  **Kullanıcı Tercihleri ve Strateji:** Kullanıcının o anki tercihi (Hız odaklı, Kalite odaklı veya Tasarruf odaklı) matematiksel bir önyargı (bias) olarak formüle eklenir. Eğer kullanıcı "Hız" modundaysa, daha küçük ve hızlı modeller yapay olarak daha yüksek puan alır.

### 3.3. Dinamik Bellek Yönetimi ve Yedekleme (Resilience)
8GB VRAM sınırı, aynı anda birden fazla modelin bellekte tutulmasını engeller. Yönlendirici, yeni bir uzmana geçiş yapmaya karar verdiğinde, "Just-in-Time" (Tam Zamanında) bellek takası prosedürünü başlatır. Önce, aktif olmayan modelin bellek adresleri serbest bırakılır, Python'un çöp toplayıcısı (Garbage Collector) tetiklenir ve GPU belleği tamamen temizlenir. Ardından, milisaniyeler içinde yeni model disken belleğe yüklenir.

Sistem ayrıca bir **Yedekleme Zinciri (Fallback Chain)** mekanizmasına sahiptir. Eğer seçilen birincil uzman, bellek yetersizliği veya çökme gibi bir nedenle yanıt veremezse, sistem kullanıcıya hata göstermek yerine sessizce ve otomatik olarak listedeki ikinci en uygun uzmana geçer. Bu, kesintisiz bir kullanıcı deneyimi için kritik bir güvenlik ağıdır.

---

## 4. Deep Scholar 2.0: Fraktal Araştırma ve Sentez Motoru

Deep Scholar, basit bir arama motoru sarmalayıcısı değil, akademik araştırma metodolojisini simüle eden, durumu koruyan (stateful) bir çoklu ajan sistemidir.

### 4.1. Fraktal Genişleme (Fractal Expansion) Teorisi
İnsan araştırmacılar bir tezi nasıl yazıyorsa, sistem de aynı yöntemi izler. Bir konu lineer bir metin yığını olarak değil, hiyerarşik bir ağaç yapısı olarak modellenir. Sistem, ana konuyu önce temel bölümlere ayırır. Ardından, her bölümü kendi içinde bağımsız bir araştırma konusu gibi ele alarak alt başlıklara böler. Bu "Böl ve Yönet" stratejisi, sistemin binlerce sayfalık bilgiyle boğulmadan, her seferinde sadece küçük ve odaklanmış bir bilgi parçası üzerinde çalışmasını sağlar.

### 4.2. Entropi Tabanlı Bilgi Kazancı (Information Gain)
Sınırsız internet erişimi, bilgi kirliliği riskini beraberinde getirir. Deep Scholar, okuduğu makalelerin değerini ölçmek için Bilgi Teorisi'nden (Information Theory) ödünç alınan "Bilgi Kazancı" algoritmasını kullanır. Sistem, o ana kadar edindiği bilgilerin anlamsal bir özetini vektör uzayında tutar. Yeni makale mevcut bilgiye çok benzerse elenir; farklıysa (yüksek entropi) sisteme eklenir.

---

## 5. İleri Seviye RAG (Retrieval-Augmented Generation) Stratejileri

Proje, tek tip bir RAG yerine, sorgunun doğasına göre şekillenen **"Agentic RAG"** mimarisini kullanır.

### 5.1. Çok Katmanlı Erişim Stratejileri
Sistem, aşağıdaki algoritmaları duruma göre hibrit olarak kullanır:

#### A. Varsayımsal Döküman Gömme (HyDE)
Kullanıcı sorguları genellikle kısadır. HyDE ile sistem, soruya önce "hayali" bir cevap üretir. Bu hayali cevabın vektörü, veritabanındaki gerçek dökümanların vektörleriyle (konu bütünlüğü açısından) çok daha iyi eşleşir. Bu, anlamsal boşluğu (Semantic Gap) doldurur.

#### B. Çoklu Sorgu Genişletme (Multi-Query Expansion)
"RAG nedir?" sorusu, sistem tarafından "Vektör veritabanlı erişim", "LLM bağlam yönetimi" ve "Bilgi getirme teknikleri" gibi 3 farklı alt sorguya bölünür. Her biri ayrı ayrı aranır ve sonuçlar **Reciprocal Rank Fusion (RRF)** ile birleştirilir. Bu, eksik veya hatalı sorularda bile doğru dökümanı bulmayı garantiler.

#### C. Adım Geri Atma (Step-Back Prompting)
Çok spesifik teknik sorularda, sistem önce "Adım Geri Atarak" genel prensipleri arar. Örneğin, bir API'nin spesifik bir hata kodu sorulduğunda, önce o API'nin genel hata işleme dokümantasyonunu arar, sonra spesifik koda odaklanır.

#### D. Ebeveyn Döküman Erişimi (Parent Document Retrieval)
Küçük metin parçalarını (Chunks) aramak kolaydır ama anlamak zordur. Sistem "Ara: Küçük Parça, Oku: Büyük Parça" prensibini uygular. Bir cümle bulunduğunda, LLM'e o cümle değil, o cümlenin ait olduğu tüm paragraf veya sayfa (Ebeveyn) verilir.

### 5.2. Kendini Onaran Veritabanı (Self-Healing DB)
Veritabanı indeksleri bozulabilir. Sistem, açılışta CRC kontrolleri yapar. HNSW grafiği bozuksa, ham veriden indeksi arka planda sessizce yeniden inşa eder.

---

## 6. Graph RAG ve Bilgi Grafiği Mimarisi (Knowledge Graph)

Proje, sadece metin benzerliğine dayalı Vektör RAG'i değil, yapısal ilişkileri anlayan **Graph RAG** teknolojisini de içerir.

### 6.1. Varlık ve İlişki Çıkarımı (The ETL Pipeline)
Her metin, iki aşamalı bir işlemle grafa dönüştürülür:
1.  **Varlık Çıkarımı:** Regex ve LLM kullanılarak metindeki Kişiler, Kurumlar, Teknolojiler ve Kavramlar düğüm (Node) olarak çıkarılır.
2.  **İlişki İnşası:** Bu varlıklar arasındaki "Çalışır", "Üretir", "Konumlanmıştır" gibi bağlar (Edge) analiz edilir. Örn: `Apple --[ÜRETİR]--> iPhone`.

### 6.2. Graf Üzerinde Akıl Yürütme algoritmaları
*   **Çoklu Sekme (Multi-Hop):** A -> B -> C ilişkisini takip ederek, A ve C arasındaki gizli bağı bulur.
*   **En Kısa Yol:** İki alakasız görünen kavramın (örn. Biyoloji ve Kuantum Fiziği) ortak bir atıf üzerinden nasıl bağlandığını keşfeder.
*   **Topluluk Tespiti (Community Detection):** Veri setindeki ana kümeleri (Cluster) belirleyerek kullanıcının "Bana bu verisetindeki ana temaları özetle" isteğine yanıt verir.

### 6.3. Hibrit Erişim
Sorgu anında, hem Vektör (Anlamsal) hem de Graf (İlişkisel) sonuçlar alınır ve birleştirilir. Bu, en kapsamlı bağlamı sağlar.

---

## 7. Akıllı Döküman İşleme ve OCR

Sistem "Garbage In, Garbage Out" prensibini bilir ve veriyi temizlemek için endüstriyel bir ETL hattı kurar.

### 7.1. Yapısal Analiz
PDF'ler düz metin olarak değil, yapısal bloklar (Başlık, Tablo, Liste) olarak okunur. Tablolar Markdown formatına çevrilerek satır-sütun ilişkisi korunur.

### 7.2. Çok Katmanlı OCR
1.  **Doğrudan:** Metin katmanı varsa hızla okunur.
2.  **Tesseract:** Görüntü tabanlı PDF'ler için yerel OCR motoru çalışır.
3.  **Vision LLM:** El yazısı gibi zorlu metinler, Vision modeline gönderilerek okunur.

---

## 8. Gerçek Zamanlı Görsel Algı (Real-Time Vision)

### 8.1. Akıllı Yakalama
CPU'yu yormamak için **Algısal Hashing** (Perceptual Hashing) kullanılır. Ekran görüntüsü alınır, hash'lenir ve bir önceki kareyle karşılaştırılır. Değişim yoksa yapay zeka uyur. Değişim varsa uyanır.

### 8.2. Bağlamsal Analiz
Model, ekrana boş bir gözle bakmaz. "Hata Ara" modunda kırmızı kutulara, "Arayüz Analiz" modunda butonlara odaklanması için özel Sistem İstemleri (System Prompts) ile yönlendirilir.

---

## 9. Asenkron Akış ve İletişim (WebSocket & Streaming)

HTTP istek-cevap modeli yerine, tam çift yönlü WebSocket kullanılır.
*   **Token Streaming:** Modelin ürettiği her harf anında kullanıcıya iletilir (Düşük algılanan gecikme).
*   **İptal Yayılımı:** "Durdur" denildiğinde, sinyal tüm ajanlara yayılır ve GPU bellekleri anında temizlenir.

---

## 10. Güvenlik ve Veri Kalıcılığı

*   **Veri İzolasyonu:** LLM, "Sandbox" içinde çalışır. Sadece izin verilen klasörlere erişebilir.
*   **Dosya Kilitleme:** Veritabanına aynı anda yazmaya çalışan süreçler, "File Lock" mekanizması ile sıraya sokulur (Veri bütünlüğü).
*   **Write-Ahead Logging (WAL):** Yazma işlemi sırasında elektrik kesilse bile veri kaybı olmaz.

---

## 11. Sonuç

Bu analiz, Personal Local AI System projesinin basit bir bot olmadığını, aksine; kendi kendini yöneten, veriyi anlayan (Vektör+Graf), gören (Vision), araştıran (Deep Scholar) ve hatalardan ders çıkaran otonom bir **Bilişsel İşletim Sistemi** olduğunu kanıtlamaktadır. Tüm bunlar, 8GB VRAM gibi kısıtlı bir kaynakta çalışacak şekilde optimize edilmiştir.
