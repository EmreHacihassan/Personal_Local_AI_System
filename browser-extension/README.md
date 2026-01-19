# Enterprise AI Assistant - Browser Extension

## 🚀 Kurulum

### Chrome'a Yükleme

1. Chrome tarayıcısını açın
2. `chrome://extensions` adresine gidin
3. Sağ üst köşeden **"Geliştirici modu"** (Developer mode) seçeneğini aktif edin
4. **"Paketlenmemiş öğe yükle"** (Load unpacked) butonuna tıklayın
5. Bu `browser-extension` klasörünü seçin
6. Extension yüklendi! 🎉

### Edge'e Yükleme

1. Edge tarayıcısını açın
2. `edge://extensions` adresine gidin
3. Sol alt köşeden **"Geliştirici modu"** seçeneğini aktif edin
4. **"Paketlenmemiş öğe yükle"** butonuna tıklayın
5. Bu `browser-extension` klasörünü seçin

## 🎯 Kullanım

1. **Widget'ı Aç/Kapat**: Sağ alt köşedeki mor butona tıklayın
2. **Sürükle**: Butonu istediğiniz yere sürükleyebilirsiniz
3. **Sohbet**: Chat sayfasından AI ile konuşun
4. **Arama**: Belgelerinizde arama yapın
5. **RAG**: Gelişmiş RAG sorguları çalıştırın

## ⚙️ Özellikler

- ✅ Her sayfada çalışır (Google Scholar, YouTube, vs.)
- ✅ Drag & Drop ile konumlandırma
- ✅ Dark/Light tema desteği
- ✅ Türkçe/İngilizce dil desteği
- ✅ Web Search toggle
- ✅ RAG toggle
- ✅ Minimized mod
- ✅ Sohbet geçmişi
- ✅ Belge arama

## 🔧 Gereksinimler

- API'nin çalışır durumda olması gerekir (`http://localhost:8001`)
- Chrome, Edge veya Chromium tabanlı tarayıcı

## 📁 Dosya Yapısı

```
browser-extension/
├── manifest.json      # Extension manifest
├── background.js      # Background service worker
├── content.js         # Widget JavaScript
├── widget.css         # Widget stilleri
├── icons/             # Extension ikonları
│   ├── icon16.svg
│   ├── icon48.svg
│   └── icon128.svg
└── README.md          # Bu dosya
```

## 🐛 Sorun Giderme

### Widget görünmüyor
- Extension'ın aktif olduğundan emin olun
- Sayfayı yenileyin
- Console'da hata olup olmadığını kontrol edin

### API bağlantısı yok
- `http://localhost:8001` adresinde API'nin çalıştığından emin olun
- `run.py` ile sistemi başlatın

### Mesaj gönderilmiyor
- API'nin çalıştığından emin olun
- Console'da hata mesajlarını kontrol edin

## 📄 Lisans

MIT License - Enterprise AI Assistant
