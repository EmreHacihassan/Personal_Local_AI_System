# Personal Local AI System - Proje Dökümantasyonu

Bu proje, temelinde basit bir local chatbot projesi gibi başlasa da, aslında "tek bir sistemden her şeye erişebilme" vizyonuyla gelişmiş, endüstri standartlarında özelliklere sahip bir **Personal Local AI System**.

Geliştirirken en büyük kısıtım donanımdı. Laptopumda **8GB VRAM'li RTX 4070** ekran kartım var. Bu yüzden donanımı en verimli şekilde kullanacak bir strateji izledim:
*   **Hız için:** `Qwen3:4b` modelini tereyağından kıl çeker gibi, çok kolayca çalıştırıyorum.
*   **Zeka ve Görsellik için:** `Qwen3-vl:8B` modelini hafif bir yanıt gecikmesiyle (latency) de olsa çalıştırabiliyorum.

## 🚧 Zorluklar ve "Computer Use" (Bilgisayar Kullanımı)
Geliştirmek hiç kolay olmadı, şu an hala çözemediğim bir sürü hata var. Özellikle üzerinde kafa patlattığım **"Computer Use"** özelliği... Amacım sisteme "yeni bir sekme aç, şunu arat, en üstteki linki aç" dediğimde bunu otonom olarak yapabilmesi. Vision yeteneği sayesinde şu an ekranımı anlık görüp analiz edebiliyor, ekranımla ilgili soruları cevaplayabiliyor. Aksiyon alma kısmı (tıklama, yazma) şu an yarım çalışıyor olsa da, üzerinde çalışmaya devam ediyorum.

## 🚀 Gelişmiş Local RAG Sistemi
Bu projede gelişmiş bir **RAG (Retrieval-Augmented Generation)** sistemi var. Bunun sayesinde verdiğim dosyaları tamamen local şekilde çalışabiliyorum.

Mesela final sınavlarına çalışırken birçok arkadaşım Google'ın NotebookLM'ini kullandı. **Ben ise kendi projemi kullandım.** Çünkü birçok alanda projemin NotebookLM'in sahip olmadığı özelliklere (gizlilik, dosya yönetimi, esneklik) sahip olduğunu biliyorum.

RAG'ın çalışma mantığını endüstriyel standartlara uygun kurdum. Bir şirket RAG kullanacağı zaman, verilerini veritabanına yükler ve kendi GPU'larından local LLM çalıştırır. Aslında verileri ve PDF'leri RAG kullanmadan, direkt prompt'a yapıştırarak da LLM'e okutabiliriz. Ama bu, tekerleği yeniden icat etmeye çalışmak gibi olurdu; bütün metni context'e eklemek LLM'in çok fazla token okumasına, yani GPU'yu boşa harcamasına ve sistemin yavaşlamasına sebep olur. Ben bunu optimize ederek kurdum.

## 🧠 AI İle Öğren: Deep Scholar 2.0
Projenin en önemli ve "bunu ben yaptım" dediğim bölümlerinden biri burası. Sıradan bir sohbet değil, **LangChain** ve **LangGraph** tabanlı bir **Multi-Agent** (Çoklu Ajan) sistemi çalışıyor.

Kullanıcı bir konu verdiğinde (örneğin "Kuantum Bilgisayarlar"), sistem bunu basitçe yanıtlamaz; bir akademisyen gibi araştırır. Süreç şöyle işliyor:
1.  **Researcher:** İnternetten ve akademik kaynaklardan (Semantic Scholar, arXiv) makaleler bulur. Hatta internet taramasını `BeautifulSoup` kütüphanesi ile DuckDuckGo üzerinden yapar.
2.  **Analyzer:** Bulunan kaynakları okur ve analiz eder.
3.  **Writer:** Toplanan bilgilerle taslak metin yazar.
4.  **Critic (Eleştirmen):** Yazılan metni acımasızca okur, hataları veya eksikleri bulur ("Bu argüman zayıf kalmış" der).
5.  **Editor:** Son hali düzenler ve akademik bir formata sokar.

**Sonuç:** 60 sayfaya kadar çıkabilen, akademik dilde, kaynakçalı (APA, IEEE vb.) tam bir rapor.

*   **Canlı İzleme:** AI'ın o an neyi araştırdığını ve düşündüğünü canlı izleyebiliyorum.
*   **Resilience (Dayanıklılık):** Sistem çökse bile `Checkpoint` sistemi sayesinde kaldığı yerden devam ediyor.
*   **Workspace:** Çalışma alanları oluşturup, RAG ile verdiğimiz dosyaları aktif veya deaktif edebiliyoruz.

## ⚡ Hibrit Model ve Human-in-the-Loop
Sistem sadece tek düze çalışmıyor. Normal chat arayüzünde de arkada bir multi-agent sistem var:
*   **Akıllı Router:** Gelen soruyu analiz eder.
*   **Basitse:** Hızlı modele (`Qwen3:4b`) yollar.
*   **Komplike ise:** Güçlü modele (`Qwen3-vl:8B`) yollar.

Buna ek olarak, manuel seçim şansım da var (**Human in the loop**). Yani kontrol her zaman bende.

## ⚙️ Teknik Altyapı Notları
Bu projenin bir "sistem" oluşu, aslında çok fazla ayrı projenin birleşiminden oluşan bir "Multi-Proje" mimarisi olmasından geliyor.

*   **Backend & Streaming:** Yanıtın gelmesi için bütün çıktının oluşturulmasını beklemek tam bir işkence olurdu. Profesyonel bir kullanım istediğim için backend'de **WebSocket** kütüphanesini kullandım. Bu sayede token-token yanıt aktarımı (streaming) sağlayabiliyorum. Kelimeler ekrana yağ gibi akıyor.
*   **Notlar ve Mind Map:** Klasörleme, dosya oluşturma ve PDF export özelliklerinin yanı sıra, bütün notlarım arasındaki ilişkileri görsel bir **Mind Map** (Zihin Haritası) üzerinde gözlemleyebiliyorum.

Hatalarıyla, eksikleriyle ama sunduğu o sınırsız yerel güçle, bu benim kişisel asistanım ve CV'me gururla eklediğim gerçek bir mühendislik çalışması.
