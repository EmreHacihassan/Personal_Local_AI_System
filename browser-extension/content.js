// Enterprise AI Assistant - Content Script
// Her sayfada çalışan ana widget scripti

(function() {
  'use strict';

  // =================== CONFIG ===================
  const API_BASE = 'http://localhost:8001';
  const WIDGET_ID = 'enterprise-ai-widget';
  const STORAGE_KEY = 'eai_widget_state';

  // =================== STATE ===================
  let state = {
    isOpen: false,
    isMinimized: false,
    position: { x: window.innerWidth - 80, y: window.innerHeight - 80 },
    messages: [],
    isLoading: false,
    currentPage: 'home',
    theme: 'light',
    language: 'tr',
    webSearchEnabled: false,
    ragEnabled: true
  };

  // =================== UTILITY FUNCTIONS ===================
  function loadState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        state = { ...state, ...parsed };
      }
    } catch (e) {
      console.warn('State yüklenemedi:', e);
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        position: state.position,
        theme: state.theme,
        language: state.language,
        webSearchEnabled: state.webSearchEnabled,
        ragEnabled: state.ragEnabled
      }));
    } catch (e) {
      console.warn('State kaydedilemedi:', e);
    }
  }

  function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // =================== API FUNCTIONS ===================
  async function checkApiHealth() {
    try {
      const response = await fetch(`${API_BASE}/health`, { timeout: 3000 });
      return response.ok;
    } catch {
      return false;
    }
  }

  async function sendMessage(content) {
    try {
      const response = await fetch(`${API_BASE}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          web_search: state.webSearchEnabled,
          use_rag: state.ragEnabled
        })
      });

      if (!response.ok) throw new Error('API error');
      return await response.json();
    } catch (error) {
      console.error('Mesaj gönderilemedi:', error);
      throw error;
    }
  }

  async function searchDocuments(query) {
    try {
      const response = await fetch(`${API_BASE}/api/v1/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Search error');
      return await response.json();
    } catch (error) {
      console.error('Arama başarısız:', error);
      throw error;
    }
  }

  // =================== UI CREATION ===================
  function createWidget() {
    // Zaten varsa kaldır
    const existing = document.getElementById(WIDGET_ID);
    if (existing) existing.remove();

    // Ana container
    const container = document.createElement('div');
    container.id = WIDGET_ID;
    container.innerHTML = getWidgetHTML();
    document.body.appendChild(container);

    // Event listeners ekle
    setupEventListeners();
    
    // Position uygula
    updateButtonPosition();
    
    // API durumunu kontrol et
    checkApiHealth().then(healthy => {
      const indicator = document.querySelector('.eai-status-indicator');
      if (indicator) {
        indicator.className = `eai-status-indicator ${healthy ? 'online' : 'offline'}`;
        indicator.title = healthy ? 'API Bağlı' : 'API Bağlantısı Yok';
      }
    });
  }

  function getWidgetHTML() {
    const t = state.language === 'tr';
    
    return `
      <!-- Floating Button -->
      <div class="eai-floating-button" id="eai-fab">
        <div class="eai-fab-pulse"></div>
        <div class="eai-fab-pulse delay"></div>
        <div class="eai-fab-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </div>
        <div class="eai-status-indicator"></div>
        <div class="eai-fab-tooltip">${t ? '✨ AI Asistan' : '✨ AI Assistant'}</div>
      </div>

      <!-- Widget Panel -->
      <div class="eai-panel ${state.isOpen ? 'open' : ''} ${state.isMinimized ? 'minimized' : ''}" id="eai-panel">
        <!-- Header -->
        <div class="eai-header" id="eai-header">
          <div class="eai-header-left">
            <button class="eai-btn-icon" id="eai-back" style="display: none;">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 18l-6-6 6-6"></path>
              </svg>
            </button>
            <div class="eai-header-grip">⋮⋮</div>
            <span class="eai-header-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="eai-sparkle">
                <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"></path>
              </svg>
              <span id="eai-page-title">${t ? 'Ana Sayfa' : 'Home'}</span>
            </span>
          </div>
          <div class="eai-header-right">
            <button class="eai-btn-icon" id="eai-minimize" title="${t ? 'Küçült' : 'Minimize'}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
              </svg>
            </button>
            <button class="eai-btn-icon" id="eai-close" title="${t ? 'Kapat' : 'Close'}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <!-- Sidebar -->
        <div class="eai-sidebar" id="eai-sidebar">
          <button class="eai-nav-item active" data-page="home">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            </svg>
            <span>${t ? 'Ana Sayfa' : 'Home'}</span>
          </button>
          <button class="eai-nav-item" data-page="chat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>${t ? 'Sohbet' : 'Chat'}</span>
          </button>
          <button class="eai-nav-item" data-page="search">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="M21 21l-4.35-4.35"></path>
            </svg>
            <span>${t ? 'Ara' : 'Search'}</span>
          </button>
          <button class="eai-nav-item" data-page="rag">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"></path>
              <path d="M12 6v6l4 2"></path>
            </svg>
            <span>RAG</span>
          </button>
          <button class="eai-nav-item" data-page="settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            <span>${t ? 'Ayarlar' : 'Settings'}</span>
          </button>
        </div>

        <!-- Content Area -->
        <div class="eai-content" id="eai-content">
          ${getPageContent('home')}
        </div>

        <!-- Minimized Bar -->
        <div class="eai-minimized-bar" id="eai-minimized-bar">
          <span>☝️ ${t ? 'Genişletmek için tıklayın' : 'Click to expand'}</span>
        </div>
      </div>
    `;
  }

  function getPageContent(page) {
    const t = state.language === 'tr';
    
    switch (page) {
      case 'home':
        return `
          <div class="eai-page-home">
            <div class="eai-welcome">
              <div class="eai-welcome-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"></path>
                </svg>
              </div>
              <h2>${t ? 'Hoş Geldiniz!' : 'Welcome!'}</h2>
              <p>${t ? 'AI Asistanınız hazır. Ne yapmak istersiniz?' : 'Your AI Assistant is ready. What would you like to do?'}</p>
            </div>
            <div class="eai-quick-actions">
              <button class="eai-action-card" data-page="chat">
                <div class="eai-action-icon blue">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                </div>
                <span>${t ? 'Sohbet Başlat' : 'Start Chat'}</span>
              </button>
              <button class="eai-action-card" data-page="search">
                <div class="eai-action-icon orange">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="M21 21l-4.35-4.35"></path>
                  </svg>
                </div>
                <span>${t ? 'Arama Yap' : 'Search'}</span>
              </button>
              <button class="eai-action-card" data-page="rag">
                <div class="eai-action-icon purple">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"></path>
                    <path d="M12 6v6l4 2"></path>
                  </svg>
                </div>
                <span>${t ? 'RAG Sorgula' : 'RAG Query'}</span>
              </button>
              <button class="eai-action-card" id="eai-open-app">
                <div class="eai-action-icon green">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                </div>
                <span>${t ? 'Tam Uygulama' : 'Full App'}</span>
              </button>
            </div>
            <div class="eai-current-page-info">
              <div class="eai-page-icon">🌐</div>
              <div class="eai-page-details">
                <span class="eai-page-label">${t ? 'Şu anki sayfa' : 'Current page'}</span>
                <span class="eai-page-url">${window.location.hostname}</span>
              </div>
            </div>
          </div>
        `;

      case 'chat':
        return `
          <div class="eai-page-chat">
            <div class="eai-messages" id="eai-messages">
              ${state.messages.length === 0 ? `
                <div class="eai-empty-chat">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                  <p>${t ? 'Sohbete başlamak için bir mesaj yazın' : 'Type a message to start chatting'}</p>
                </div>
              ` : state.messages.map(m => `
                <div class="eai-message ${m.role}">
                  <div class="eai-message-content">${formatMessage(m.content)}</div>
                  <div class="eai-message-time">${new Date(m.timestamp).toLocaleTimeString()}</div>
                </div>
              `).join('')}
            </div>
            <div class="eai-input-area">
              <div class="eai-input-options">
                <button class="eai-option-btn ${state.webSearchEnabled ? 'active' : ''}" id="eai-web-toggle" title="Web Search">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                  </svg>
                  Web
                </button>
                <button class="eai-option-btn ${state.ragEnabled ? 'active' : ''}" id="eai-rag-toggle" title="RAG">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"></path>
                  </svg>
                  RAG
                </button>
              </div>
              <div class="eai-input-wrapper">
                <textarea id="eai-input" placeholder="${t ? 'Mesajınızı yazın...' : 'Type your message...'}" rows="1"></textarea>
                <button class="eai-send-btn" id="eai-send" ${state.isLoading ? 'disabled' : ''}>
                  ${state.isLoading ? `
                    <svg class="eai-spinner" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="60" stroke-dashoffset="20"></circle>
                    </svg>
                  ` : `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"></path>
                    </svg>
                  `}
                </button>
              </div>
            </div>
          </div>
        `;

      case 'search':
        return `
          <div class="eai-page-search">
            <div class="eai-search-box">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="M21 21l-4.35-4.35"></path>
              </svg>
              <input type="text" id="eai-search-input" placeholder="${t ? 'Belgelerinizde arayın...' : 'Search in your documents...'}">
              <button class="eai-search-btn" id="eai-search-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"></path>
                </svg>
              </button>
            </div>
            <div class="eai-search-results" id="eai-search-results">
              <div class="eai-search-placeholder">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                </svg>
                <p>${t ? 'Belgelerinizde arama yapmak için yukarıya yazın' : 'Type above to search in your documents'}</p>
              </div>
            </div>
          </div>
        `;

      case 'rag':
        return `
          <div class="eai-page-rag">
            <div class="eai-rag-config">
              <h3>${t ? 'RAG Ayarları' : 'RAG Settings'}</h3>
              <div class="eai-rag-options">
                <div class="eai-rag-option">
                  <label>${t ? 'Strateji' : 'Strategy'}</label>
                  <select id="eai-rag-strategy">
                    <option value="naive">Naive RAG</option>
                    <option value="hyde">HyDE</option>
                    <option value="fusion">Fusion RAG</option>
                    <option value="rerank">Rerank</option>
                  </select>
                </div>
                <div class="eai-rag-option">
                  <label>Top K</label>
                  <input type="number" id="eai-rag-topk" value="5" min="1" max="20">
                </div>
              </div>
            </div>
            <div class="eai-rag-query">
              <textarea id="eai-rag-input" placeholder="${t ? 'RAG sorgunuzu yazın...' : 'Enter your RAG query...'}" rows="3"></textarea>
              <button class="eai-rag-btn" id="eai-rag-btn">${t ? 'Sorgula' : 'Query'}</button>
            </div>
            <div class="eai-rag-results" id="eai-rag-results"></div>
          </div>
        `;

      case 'settings':
        return `
          <div class="eai-page-settings">
            <div class="eai-setting-group">
              <h3>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="5"></circle>
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"></path>
                </svg>
                ${t ? 'Tema' : 'Theme'}
              </h3>
              <div class="eai-theme-options">
                <button class="eai-theme-btn ${state.theme === 'light' ? 'active' : ''}" data-theme="light">☀️ Light</button>
                <button class="eai-theme-btn ${state.theme === 'dark' ? 'active' : ''}" data-theme="dark">🌙 Dark</button>
              </div>
            </div>
            <div class="eai-setting-group">
              <h3>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                </svg>
                ${t ? 'Dil' : 'Language'}
              </h3>
              <div class="eai-lang-options">
                <button class="eai-lang-btn ${state.language === 'tr' ? 'active' : ''}" data-lang="tr">🇹🇷 Türkçe</button>
                <button class="eai-lang-btn ${state.language === 'en' ? 'active' : ''}" data-lang="en">🇬🇧 English</button>
              </div>
            </div>
            <div class="eai-setting-group">
              <h3>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
                API
              </h3>
              <div class="eai-api-status" id="eai-api-status">
                <span class="eai-status-dot"></span>
                <span>${t ? 'Bağlantı kontrol ediliyor...' : 'Checking connection...'}</span>
              </div>
            </div>
          </div>
        `;

      default:
        return '<div class="eai-page-empty">Page not found</div>';
    }
  }

  function formatMessage(content) {
    // Basit markdown formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }

  // =================== EVENT HANDLERS ===================
  function setupEventListeners() {
    // Floating button click
    const fab = document.getElementById('eai-fab');
    if (fab) {
      fab.addEventListener('click', togglePanel);
      makeDraggable(fab);
    }

    // Close button
    const closeBtn = document.getElementById('eai-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        state.isOpen = false;
        updatePanelVisibility();
      });
    }

    // Minimize button
    const minimizeBtn = document.getElementById('eai-minimize');
    if (minimizeBtn) {
      minimizeBtn.addEventListener('click', () => {
        state.isMinimized = !state.isMinimized;
        updatePanelVisibility();
      });
    }

    // Minimized bar click
    const minimizedBar = document.getElementById('eai-minimized-bar');
    if (minimizedBar) {
      minimizedBar.addEventListener('click', () => {
        state.isMinimized = false;
        updatePanelVisibility();
      });
    }

    // Navigation
    document.querySelectorAll('.eai-nav-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const page = btn.dataset.page;
        navigateToPage(page);
      });
    });

    // Quick action cards
    document.querySelectorAll('.eai-action-card[data-page]').forEach(btn => {
      btn.addEventListener('click', () => {
        const page = btn.dataset.page;
        navigateToPage(page);
      });
    });

    // Open full app
    const openAppBtn = document.getElementById('eai-open-app');
    if (openAppBtn) {
      openAppBtn.addEventListener('click', () => {
        window.open('http://localhost:3000', '_blank');
      });
    }

    // Chat input
    const chatInput = document.getElementById('eai-input');
    const sendBtn = document.getElementById('eai-send');
    if (chatInput && sendBtn) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSendMessage();
        }
      });
      sendBtn.addEventListener('click', handleSendMessage);

      // Auto-resize textarea
      chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + 'px';
      });
    }

    // Toggle buttons
    const webToggle = document.getElementById('eai-web-toggle');
    if (webToggle) {
      webToggle.addEventListener('click', () => {
        state.webSearchEnabled = !state.webSearchEnabled;
        webToggle.classList.toggle('active', state.webSearchEnabled);
        saveState();
      });
    }

    const ragToggle = document.getElementById('eai-rag-toggle');
    if (ragToggle) {
      ragToggle.addEventListener('click', () => {
        state.ragEnabled = !state.ragEnabled;
        ragToggle.classList.toggle('active', state.ragEnabled);
        saveState();
      });
    }

    // Search
    const searchInput = document.getElementById('eai-search-input');
    const searchBtn = document.getElementById('eai-search-btn');
    if (searchInput && searchBtn) {
      searchBtn.addEventListener('click', handleSearch);
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleSearch();
      });
    }

    // Theme buttons
    document.querySelectorAll('.eai-theme-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        state.theme = btn.dataset.theme;
        document.querySelectorAll('.eai-theme-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        applyTheme();
        saveState();
      });
    });

    // Language buttons
    document.querySelectorAll('.eai-lang-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        state.language = btn.dataset.lang;
        document.querySelectorAll('.eai-lang-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        saveState();
        // Reload widget with new language
        createWidget();
        state.isOpen = true;
        navigateToPage('settings');
      });
    });

    // Header draggable
    const header = document.getElementById('eai-header');
    if (header) {
      makePanelDraggable(header);
    }

    // Back button
    const backBtn = document.getElementById('eai-back');
    if (backBtn) {
      backBtn.addEventListener('click', () => navigateToPage('home'));
    }
  }

  async function handleSendMessage() {
    const input = document.getElementById('eai-input');
    const content = input?.value?.trim();
    
    if (!content || state.isLoading) return;

    // Add user message
    const userMessage = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    state.messages.push(userMessage);
    updateChatUI();
    input.value = '';
    input.style.height = 'auto';

    // Send to API
    state.isLoading = true;
    updateChatUI();

    try {
      const response = await sendMessage(content);
      const assistantMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.content || response.response || 'Yanıt alınamadı.',
        timestamp: new Date().toISOString()
      };
      state.messages.push(assistantMessage);
    } catch (error) {
      const errorMessage = {
        id: generateId(),
        role: 'assistant',
        content: state.language === 'tr' 
          ? 'Bir hata oluştu. API bağlantısını kontrol edin.' 
          : 'An error occurred. Check the API connection.',
        timestamp: new Date().toISOString()
      };
      state.messages.push(errorMessage);
    }

    state.isLoading = false;
    updateChatUI();
  }

  async function handleSearch() {
    const input = document.getElementById('eai-search-input');
    const resultsContainer = document.getElementById('eai-search-results');
    const query = input?.value?.trim();

    if (!query || !resultsContainer) return;

    resultsContainer.innerHTML = '<div class="eai-loading">Aranıyor...</div>';

    try {
      const response = await searchDocuments(query);
      const results = response.results || [];

      if (results.length === 0) {
        resultsContainer.innerHTML = `
          <div class="eai-no-results">
            <p>${state.language === 'tr' ? 'Sonuç bulunamadı' : 'No results found'}</p>
          </div>
        `;
      } else {
        resultsContainer.innerHTML = results.map(r => `
          <div class="eai-search-result">
            <div class="eai-result-content">${r.content?.substring(0, 200)}...</div>
            <div class="eai-result-meta">
              <span class="eai-result-score">${Math.round((r.score || 0) * 100)}%</span>
              <span class="eai-result-source">${r.source || 'Unknown'}</span>
            </div>
          </div>
        `).join('');
      }
    } catch (error) {
      resultsContainer.innerHTML = `
        <div class="eai-error">
          <p>${state.language === 'tr' ? 'Arama başarısız' : 'Search failed'}</p>
        </div>
      `;
    }
  }

  function updateChatUI() {
    const content = document.getElementById('eai-content');
    if (content && state.currentPage === 'chat') {
      content.innerHTML = getPageContent('chat');
      setupEventListeners();
      
      // Scroll to bottom
      const messages = document.getElementById('eai-messages');
      if (messages) {
        messages.scrollTop = messages.scrollHeight;
      }
    }
  }

  function navigateToPage(page) {
    state.currentPage = page;
    
    // Update nav items
    document.querySelectorAll('.eai-nav-item').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.page === page);
    });
    
    // Update content
    const content = document.getElementById('eai-content');
    if (content) {
      content.innerHTML = getPageContent(page);
      setupEventListeners();
    }
    
    // Update title
    const titles = {
      home: state.language === 'tr' ? 'Ana Sayfa' : 'Home',
      chat: state.language === 'tr' ? 'Sohbet' : 'Chat',
      search: state.language === 'tr' ? 'Ara' : 'Search',
      rag: 'RAG',
      settings: state.language === 'tr' ? 'Ayarlar' : 'Settings'
    };
    const titleEl = document.getElementById('eai-page-title');
    if (titleEl) titleEl.textContent = titles[page] || page;
    
    // Show/hide back button
    const backBtn = document.getElementById('eai-back');
    if (backBtn) {
      backBtn.style.display = page === 'home' ? 'none' : 'flex';
    }

    // Check API status on settings page
    if (page === 'settings') {
      checkApiHealth().then(healthy => {
        const statusEl = document.getElementById('eai-api-status');
        if (statusEl) {
          statusEl.className = `eai-api-status ${healthy ? 'online' : 'offline'}`;
          statusEl.innerHTML = `
            <span class="eai-status-dot"></span>
            <span>${healthy 
              ? (state.language === 'tr' ? 'API Bağlı' : 'API Connected') 
              : (state.language === 'tr' ? 'API Bağlantısı Yok' : 'API Not Connected')
            }</span>
          `;
        }
      });
    }
  }

  function togglePanel() {
    state.isOpen = !state.isOpen;
    updatePanelVisibility();
  }

  function updatePanelVisibility() {
    const panel = document.getElementById('eai-panel');
    const fab = document.getElementById('eai-fab');
    
    if (panel) {
      panel.classList.toggle('open', state.isOpen);
      panel.classList.toggle('minimized', state.isMinimized);
    }
    
    if (fab) {
      fab.style.display = state.isOpen ? 'none' : 'flex';
    }
  }

  function updateButtonPosition() {
    const fab = document.getElementById('eai-fab');
    if (fab) {
      fab.style.left = state.position.x + 'px';
      fab.style.top = state.position.y + 'px';
    }
  }

  function applyTheme() {
    const widget = document.getElementById(WIDGET_ID);
    if (widget) {
      widget.setAttribute('data-theme', state.theme);
    }
  }

  // =================== DRAG FUNCTIONALITY ===================
  function makeDraggable(element) {
    let isDragging = false;
    let startX, startY, startLeft, startTop;

    element.addEventListener('mousedown', startDrag);
    element.addEventListener('touchstart', startDrag, { passive: false });

    function startDrag(e) {
      if (e.target.closest('.eai-fab-icon')) {
        // Click on icon = toggle panel
        return;
      }
      
      isDragging = true;
      const rect = element.getBoundingClientRect();
      startLeft = rect.left;
      startTop = rect.top;
      
      if (e.type === 'mousedown') {
        startX = e.clientX;
        startY = e.clientY;
      } else {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
      }
      
      document.addEventListener('mousemove', drag);
      document.addEventListener('mouseup', stopDrag);
      document.addEventListener('touchmove', drag, { passive: false });
      document.addEventListener('touchend', stopDrag);
    }

    function drag(e) {
      if (!isDragging) return;
      e.preventDefault();
      
      let clientX, clientY;
      if (e.type === 'mousemove') {
        clientX = e.clientX;
        clientY = e.clientY;
      } else {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
      }
      
      const deltaX = clientX - startX;
      const deltaY = clientY - startY;
      
      let newX = startLeft + deltaX;
      let newY = startTop + deltaY;
      
      // Keep in bounds
      newX = Math.max(0, Math.min(newX, window.innerWidth - 60));
      newY = Math.max(0, Math.min(newY, window.innerHeight - 60));
      
      element.style.left = newX + 'px';
      element.style.top = newY + 'px';
      
      state.position = { x: newX, y: newY };
    }

    function stopDrag() {
      isDragging = false;
      saveState();
      document.removeEventListener('mousemove', drag);
      document.removeEventListener('mouseup', stopDrag);
      document.removeEventListener('touchmove', drag);
      document.removeEventListener('touchend', stopDrag);
    }
  }

  function makePanelDraggable(header) {
    let isDragging = false;
    let startX, startY;
    const panel = document.getElementById('eai-panel');

    header.addEventListener('mousedown', (e) => {
      if (e.target.closest('button')) return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      header.style.cursor = 'grabbing';
      
      document.addEventListener('mousemove', drag);
      document.addEventListener('mouseup', stopDrag);
    });

    function drag(e) {
      if (!isDragging || !panel) return;
      
      const deltaX = e.clientX - startX;
      const deltaY = e.clientY - startY;
      
      const rect = panel.getBoundingClientRect();
      let newRight = window.innerWidth - rect.right - deltaX;
      let newBottom = window.innerHeight - rect.bottom - deltaY;
      
      newRight = Math.max(0, Math.min(newRight, window.innerWidth - 400));
      newBottom = Math.max(0, Math.min(newBottom, window.innerHeight - 500));
      
      panel.style.right = newRight + 'px';
      panel.style.bottom = newBottom + 'px';
      
      startX = e.clientX;
      startY = e.clientY;
    }

    function stopDrag() {
      isDragging = false;
      header.style.cursor = 'grab';
      document.removeEventListener('mousemove', drag);
      document.removeEventListener('mouseup', stopDrag);
    }
  }

  // =================== MESSAGE HANDLING ===================
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'toggleWidget') {
      togglePanel();
      sendResponse({ success: true });
    }
  });

  // =================== INITIALIZATION ===================
  function init() {
    loadState();
    createWidget();
    applyTheme();
    
    console.log('🤖 Enterprise AI Assistant loaded');
  }

  // Wait for DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
