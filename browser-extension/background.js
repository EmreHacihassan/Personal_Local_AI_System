// Enterprise AI Assistant - Background Service Worker
// Arka plan servisi - widget durumunu yönetir

// Default ayarlar
const DEFAULT_SETTINGS = {
  enabled: true,
  apiUrl: 'http://localhost:8001',
  position: { x: null, y: null },
  theme: 'light',
  language: 'tr'
};

// Extension yüklendiğinde
chrome.runtime.onInstalled.addListener(() => {
  console.log('🤖 Enterprise AI Assistant yüklendi');
  
  // Varsayılan ayarları kaydet
  chrome.storage.local.get('settings', (result) => {
    if (!result.settings) {
      chrome.storage.local.set({ settings: DEFAULT_SETTINGS });
    }
  });
});

// Extension ikonuna tıklandığında
chrome.action.onClicked.addListener((tab) => {
  // Content script'e mesaj gönder - widget'ı aç/kapat
  chrome.tabs.sendMessage(tab.id, { action: 'toggleWidget' });
});

// Content script'ten gelen mesajları dinle
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSettings') {
    chrome.storage.local.get('settings', (result) => {
      sendResponse(result.settings || DEFAULT_SETTINGS);
    });
    return true; // Async response için
  }
  
  if (request.action === 'saveSettings') {
    chrome.storage.local.set({ settings: request.settings }, () => {
      sendResponse({ success: true });
    });
    return true;
  }
  
  if (request.action === 'checkApiHealth') {
    fetch(`${request.apiUrl}/health`)
      .then(res => res.json())
      .then(data => sendResponse({ healthy: true, data }))
      .catch(err => sendResponse({ healthy: false, error: err.message }));
    return true;
  }
});
