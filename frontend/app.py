"""
Enterprise AI Assistant - Streamlit Frontend
Endüstri Standartlarında Kurumsal AI Çözümü

Ana kullanıcı arayüzü - Profesyonel Chat, Web Search, Döküman Yönetimi.
Perplexity AI tarzı modern tasarım.
"""

import streamlit as st
import requests
import uuid
import os
import json
from datetime import datetime
from pathlib import Path
import sys
import re
import time
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.session_manager import session_manager
from core.notes_manager import notes_manager

# ============ CONFIGURATION ============

# ✅ Port 8001 - Backend'in çalıştığı port
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001")

# ============ THEME DEFINITIONS ============

THEMES = {
    "klasik": {
        "name": "🎨 Klasik",
        "description": "Mor-mavi gradyan, profesyonel görünüm",
        "primary_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "primary_color": "#667eea",
        "secondary_color": "#764ba2",
        "bg_color": "#ffffff",
        "text_color": "#333333",
        "card_bg": "#f8f9fa",
        "border_color": "#e9ecef",
        "sidebar_bg": "#f8f9fa",
        "accent_color": "#667eea",
    },
    "gece": {
        "name": "🌙 Gece Modu",
        "description": "Koyu tema, göz yorgunluğunu azaltır",
        "primary_gradient": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
        "primary_color": "#6366f1",
        "secondary_color": "#8b5cf6",
        "bg_color": "#0f172a",
        "text_color": "#e2e8f0",
        "card_bg": "#1e293b",
        "border_color": "#334155",
        "sidebar_bg": "#1e293b",
        "accent_color": "#818cf8",
    },
    "okyanus": {
        "name": "🌊 Okyanus",
        "description": "Mavi tonları, sakinleştirici",
        "primary_gradient": "linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)",
        "primary_color": "#0ea5e9",
        "secondary_color": "#2563eb",
        "bg_color": "#f0f9ff",
        "text_color": "#0c4a6e",
        "card_bg": "#e0f2fe",
        "border_color": "#bae6fd",
        "sidebar_bg": "#e0f2fe",
        "accent_color": "#0284c7",
    },
    "orman": {
        "name": "🌲 Orman",
        "description": "Yeşil tonları, doğal ve huzurlu",
        "primary_gradient": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
        "primary_color": "#10b981",
        "secondary_color": "#059669",
        "bg_color": "#f0fdf4",
        "text_color": "#14532d",
        "card_bg": "#dcfce7",
        "border_color": "#bbf7d0",
        "sidebar_bg": "#dcfce7",
        "accent_color": "#059669",
    },
    "gunbatimi": {
        "name": "🌅 Gün Batımı",
        "description": "Turuncu-pembe, sıcak tonlar",
        "primary_gradient": "linear-gradient(135deg, #f97316 0%, #ec4899 100%)",
        "primary_color": "#f97316",
        "secondary_color": "#ec4899",
        "bg_color": "#fff7ed",
        "text_color": "#7c2d12",
        "card_bg": "#ffedd5",
        "border_color": "#fed7aa",
        "sidebar_bg": "#ffedd5",
        "accent_color": "#ea580c",
    },
    "lavanta": {
        "name": "💜 Lavanta",
        "description": "Mor tonları, zarif ve şık",
        "primary_gradient": "linear-gradient(135deg, #a855f7 0%, #7c3aed 100%)",
        "primary_color": "#a855f7",
        "secondary_color": "#7c3aed",
        "bg_color": "#faf5ff",
        "text_color": "#581c87",
        "card_bg": "#f3e8ff",
        "border_color": "#e9d5ff",
        "sidebar_bg": "#f3e8ff",
        "accent_color": "#9333ea",
    },
    "minimalist": {
        "name": "⬜ Minimalist",
        "description": "Siyah-beyaz, sade ve temiz",
        "primary_gradient": "linear-gradient(135deg, #374151 0%, #111827 100%)",
        "primary_color": "#374151",
        "secondary_color": "#111827",
        "bg_color": "#ffffff",
        "text_color": "#111827",
        "card_bg": "#f9fafb",
        "border_color": "#e5e7eb",
        "sidebar_bg": "#f9fafb",
        "accent_color": "#4b5563",
    },
    "kiraz": {
        "name": "🌸 Kiraz Çiçeği",
        "description": "Pembe tonları, tatlı ve enerjik",
        "primary_gradient": "linear-gradient(135deg, #f472b6 0%, #db2777 100%)",
        "primary_color": "#f472b6",
        "secondary_color": "#db2777",
        "bg_color": "#fdf2f8",
        "text_color": "#831843",
        "card_bg": "#fce7f3",
        "border_color": "#fbcfe8",
        "sidebar_bg": "#fce7f3",
        "accent_color": "#ec4899",
    },
}

# ============ MULTI-LANGUAGE SUPPORT ============

TRANSLATIONS = {
    "tr": {
        "app_title": "Enterprise AI Assistant",
        "new_chat": "➕ Yeni Sohbet",
        "chat_history": "💬 Sohbet Geçmişi",
        "search_placeholder": "Mesaj yazın...",
        "web_search": "🌐 Web Araması",
        "settings": "⚙️ Ayarlar",
        "documents": "📁 Dökümanlar",
        "notes": "📝 Notlar",
        "dashboard": "📊 Dashboard",
        "favorites": "⭐ Favoriler",
        "templates": "📋 Şablonlar",
        "pin": "📌 Sabitle",
        "unpin": "📌 Sabitlemeyi Kaldır",
        "delete": "🗑️ Sil",
        "edit": "✏️ Düzenle",
        "save": "💾 Kaydet",
        "cancel": "❌ İptal",
        "search": "🔍 Ara",
        "filter": "🔽 Filtrele",
        "export": "📤 Dışa Aktar",
        "regenerate": "🔄 Yeniden Oluştur",
        "copy": "📋 Kopyala",
        "add_to_favorites": "⭐ Favorilere Ekle",
        "remove_from_favorites": "⭐ Favorilerden Çıkar",
        "add_tag": "🏷️ Etiket Ekle",
        "set_category": "📂 Kategori Belirle",
        "short_response": "Kısa",
        "normal_response": "Normal",
        "detailed_response": "Detaylı",
        "keyboard_shortcuts": "⌨️ Klavye Kısayolları",
        "daily_summary": "📅 Günlük Özet",
        "statistics": "📊 İstatistikler",
        "no_messages": "Henüz mesaj yok",
        "no_favorites": "Henüz favori mesaj yok",
        "no_templates": "Henüz şablon yok",
        "loading": "Yükleniyor...",
        "success": "Başarılı!",
        "error": "Hata!",
        "confirm_delete": "Silmek istediğinize emin misiniz?",
        "categories": {
            "work": "💼 İş",
            "personal": "🏠 Kişisel",
            "research": "🔬 Araştırma",
            "coding": "💻 Kodlama",
            "learning": "📚 Öğrenme",
            "creative": "🎨 Yaratıcı",
            "other": "📌 Diğer",
        },
    },
    "en": {
        "app_title": "Enterprise AI Assistant",
        "new_chat": "➕ New Chat",
        "chat_history": "💬 Chat History",
        "search_placeholder": "Type a message...",
        "web_search": "🌐 Web Search",
        "settings": "⚙️ Settings",
        "documents": "📁 Documents",
        "notes": "📝 Notes",
        "dashboard": "📊 Dashboard",
        "favorites": "⭐ Favorites",
        "templates": "📋 Templates",
        "pin": "📌 Pin",
        "unpin": "📌 Unpin",
        "delete": "🗑️ Delete",
        "edit": "✏️ Edit",
        "save": "💾 Save",
        "cancel": "❌ Cancel",
        "search": "🔍 Search",
        "filter": "🔽 Filter",
        "export": "📤 Export",
        "regenerate": "🔄 Regenerate",
        "copy": "📋 Copy",
        "add_to_favorites": "⭐ Add to Favorites",
        "remove_from_favorites": "⭐ Remove from Favorites",
        "add_tag": "🏷️ Add Tag",
        "set_category": "📂 Set Category",
        "short_response": "Short",
        "normal_response": "Normal",
        "detailed_response": "Detailed",
        "keyboard_shortcuts": "⌨️ Keyboard Shortcuts",
        "daily_summary": "📅 Daily Summary",
        "statistics": "📊 Statistics",
        "no_messages": "No messages yet",
        "no_favorites": "No favorite messages yet",
        "no_templates": "No templates yet",
        "loading": "Loading...",
        "success": "Success!",
        "error": "Error!",
        "confirm_delete": "Are you sure you want to delete?",
        "categories": {
            "work": "💼 Work",
            "personal": "🏠 Personal",
            "research": "🔬 Research",
            "coding": "💻 Coding",
            "learning": "📚 Learning",
            "creative": "🎨 Creative",
            "other": "📌 Other",
        },
    },
    "de": {
        "app_title": "Enterprise AI Assistent",
        "new_chat": "➕ Neuer Chat",
        "chat_history": "💬 Chatverlauf",
        "search_placeholder": "Nachricht eingeben...",
        "web_search": "🌐 Websuche",
        "settings": "⚙️ Einstellungen",
        "documents": "📁 Dokumente",
        "notes": "📝 Notizen",
        "dashboard": "📊 Dashboard",
        "favorites": "⭐ Favoriten",
        "templates": "📋 Vorlagen",
        "pin": "📌 Anheften",
        "unpin": "📌 Lösen",
        "delete": "🗑️ Löschen",
        "edit": "✏️ Bearbeiten",
        "save": "💾 Speichern",
        "cancel": "❌ Abbrechen",
        "search": "🔍 Suchen",
        "filter": "🔽 Filtern",
        "export": "📤 Exportieren",
        "regenerate": "🔄 Neu generieren",
        "copy": "📋 Kopieren",
        "add_to_favorites": "⭐ Zu Favoriten",
        "remove_from_favorites": "⭐ Aus Favoriten entfernen",
        "add_tag": "🏷️ Tag hinzufügen",
        "set_category": "📂 Kategorie setzen",
        "short_response": "Kurz",
        "normal_response": "Normal",
        "detailed_response": "Ausführlich",
        "keyboard_shortcuts": "⌨️ Tastenkürzel",
        "daily_summary": "📅 Tägliche Zusammenfassung",
        "statistics": "📊 Statistiken",
        "no_messages": "Noch keine Nachrichten",
        "no_favorites": "Noch keine Favoriten",
        "no_templates": "Noch keine Vorlagen",
        "loading": "Laden...",
        "success": "Erfolg!",
        "error": "Fehler!",
        "confirm_delete": "Sind Sie sicher?",
        "categories": {
            "work": "💼 Arbeit",
            "personal": "🏠 Persönlich",
            "research": "🔬 Forschung",
            "coding": "💻 Programmierung",
            "learning": "📚 Lernen",
            "creative": "🎨 Kreativ",
            "other": "📌 Sonstiges",
        },
    },
}

def t(key: str) -> str:
    """Çeviri fonksiyonu."""
    lang = st.session_state.get("selected_language", "tr")
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])
    
    # Nested key desteği (örn: "categories.work")
    if "." in key:
        parts = key.split(".")
        value = translations
        for part in parts:
            value = value.get(part, key)
        return value
    
    return translations.get(key, key)

def get_theme_css(theme_id: str) -> str:
    """Seçilen temaya göre CSS oluştur."""
    theme = THEMES.get(theme_id, THEMES["klasik"])
    
    return f"""
<style>
    /* ===== THEME VARIABLES ===== */
    :root {{
        --primary-gradient: {theme["primary_gradient"]};
        --primary-color: {theme["primary_color"]};
        --secondary-color: {theme["secondary_color"]};
        --bg-color: {theme["bg_color"]};
        --text-color: {theme["text_color"]};
        --card-bg: {theme["card_bg"]};
        --border-color: {theme["border_color"]};
        --sidebar-bg: {theme["sidebar_bg"]};
        --accent-color: {theme["accent_color"]};
    }}
    
    /* ===== GENEL STILLER ===== */
    .stApp {{
        background-color: {theme["bg_color"]};
    }}
    .main-header {{
        font-size: 2.2rem;
        font-weight: 700;
        background: {theme["primary_gradient"]};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }}
    .sub-header {{
        font-size: 0.95rem;
        color: {theme["text_color"]}99;
        margin-bottom: 1.5rem;
    }}
    
    /* ===== CHAT MESAJLARI ===== */
    .chat-container {{
        max-width: 900px;
        margin: 0 auto;
    }}
    .user-message-box {{
        background: {theme["primary_gradient"]};
        color: white;
        padding: 1rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.8rem 0;
        margin-left: 15%;
        box-shadow: 0 2px 8px {theme["primary_color"]}40;
    }}
    .assistant-message-box {{
        background: {theme["card_bg"]};
        color: {theme["text_color"]};
        padding: 1rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.8rem 0;
        margin-right: 10%;
        border: 1px solid {theme["border_color"]};
    }}
    
    /* ===== PREMIUM KAYNAKLAR KUTUSU ===== */
    .sources-container {{
        background: {theme["card_bg"]};
        border: 1px solid {theme["border_color"]};
        border-radius: 16px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .sources-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid {theme["border_color"]};
    }}
    .sources-header-left {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .sources-header-icon {{
        font-size: 1.3rem;
    }}
    .sources-header-title {{
        font-weight: 700;
        color: {theme["text_color"]};
        font-size: 1rem;
    }}
    .sources-header-count {{
        background: {theme["primary_gradient"]};
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .sources-meta {{
        display: flex;
        gap: 12px;
        font-size: 0.75rem;
        color: {theme["text_color"]}99;
    }}
    .sources-meta-item {{
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    
    /* Kaynak Kartları */
    .source-card {{
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 0.9rem;
        background: {theme["bg_color"]};
        border-radius: 12px;
        margin-bottom: 0.6rem;
        border: 1px solid {theme["border_color"]};
        transition: all 0.2s ease;
        cursor: pointer;
    }}
    .source-card:hover {{
        border-color: {theme["primary_color"]};
        box-shadow: 0 4px 12px {theme["primary_color"]}25;
        transform: translateY(-1px);
    }}
    .source-card-number {{
        background: {theme["primary_gradient"]};
        color: white;
        width: 26px;
        height: 26px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 700;
        flex-shrink: 0;
    }}
    .source-card-content {{
        flex: 1;
        min-width: 0;
    }}
    .source-card-title {{
        font-weight: 600;
        color: {theme["text_color"]};
        font-size: 0.9rem;
        margin-bottom: 4px;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}
    .source-card-domain {{
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 6px;
    }}
    .source-card-favicon {{
        width: 14px;
        height: 14px;
        border-radius: 2px;
    }}
    .source-card-url {{
        font-size: 0.75rem;
        color: {theme["primary_color"]};
        text-decoration: none;
    }}
    .source-card-url:hover {{
        text-decoration: underline;
    }}
    .source-card-snippet {{
        font-size: 0.8rem;
        color: {theme["text_color"]}cc;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}
    .source-card-badges {{
        display: flex;
        gap: 6px;
        margin-top: 8px;
        flex-wrap: wrap;
    }}
    .source-badge {{
        display: inline-flex;
        align-items: center;
        gap: 3px;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 500;
    }}
    .badge-wiki {{ background: #e3f2fd; color: #1565c0; }}
    .badge-academic {{ background: #fce4ec; color: #c62828; }}
    .badge-news {{ background: #fff3e0; color: #ef6c00; }}
    .badge-official {{ background: #e8f5e9; color: #2e7d32; }}
    .badge-blog {{ background: #f3e5f5; color: #7b1fa2; }}
    .badge-forum {{ background: #e0f7fa; color: #00838f; }}
    .badge-reliability {{
        background: {theme["card_bg"]};
        color: {theme["text_color"]}99;
    }}
    
    /* Instant Answer Box */
    .instant-answer-box {{
        background: {theme["card_bg"]};
        border: 1px solid {theme["primary_color"]}50;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }}
    .instant-answer-header {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        color: {theme["primary_color"]};
        margin-bottom: 0.6rem;
        font-size: 0.95rem;
    }}
    .instant-answer-content {{
        color: {theme["text_color"]};
        font-size: 0.9rem;
        line-height: 1.6;
    }}
    .instant-answer-source {{
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 0.8rem;
        font-size: 0.75rem;
        color: {theme["text_color"]}99;
    }}
    
    /* Related Queries */
    .related-queries {{
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid {theme["border_color"]};
    }}
    .related-queries-title {{
        font-size: 0.8rem;
        font-weight: 600;
        color: {theme["text_color"]}99;
        margin-bottom: 0.6rem;
    }}
    .related-query-chip {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 0.35rem 0.8rem;
        background: {theme["bg_color"]};
        border: 1px solid {theme["border_color"]};
        border-radius: 20px;
        font-size: 0.8rem;
        color: {theme["text_color"]};
        margin: 0.2rem;
        cursor: pointer;
        transition: all 0.2s;
    }}
    .related-query-chip:hover {{
        border-color: {theme["primary_color"]};
        background: {theme["card_bg"]};
    }}
    
    /* Follow-up Questions */
    .followup-container {{
        background: {theme["card_bg"]};
        border: 1px solid {theme["accent_color"]}40;
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1rem;
    }}
    .followup-title {{
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 600;
        color: {theme["accent_color"]};
        font-size: 0.85rem;
        margin-bottom: 0.6rem;
    }}
    .followup-item {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0.5rem 0.8rem;
        background: {theme["bg_color"]};
        border-radius: 8px;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
        color: {theme["text_color"]};
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid transparent;
    }}
    .followup-item:hover {{
        border-color: {theme["accent_color"]};
        background: {theme["card_bg"]};
    }}
    
    /* Search Progress Stepper */
    .progress-stepper {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0.8rem 1rem;
        background: {theme["card_bg"]};
        border-radius: 10px;
        margin-bottom: 1rem;
    }}
    .progress-step {{
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8rem;
        color: {theme["text_color"]}66;
    }}
    .progress-step.active {{
        color: {theme["primary_color"]};
        font-weight: 600;
    }}
    .progress-step.completed {{
        color: #22c55e;
    }}
    .progress-connector {{
        width: 20px;
        height: 2px;
        background: {theme["border_color"]};
    }}
    .progress-connector.completed {{
        background: #22c55e;
    }}
    
    /* Response Stats */
    .response-stats {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.6rem 0;
        font-size: 0.75rem;
        color: {theme["text_color"]}99;
        border-top: 1px solid {theme["border_color"]};
        margin-top: 0.8rem;
    }}
    .stat-item {{
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    .stat-icon {{
        font-size: 0.85rem;
    }}
    
    /* ===== WEB SEARCH INFO ===== */
    .web-search-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: {theme["primary_gradient"]};
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }}
    .web-search-inactive {{
        background: {theme["card_bg"]};
        color: {theme["text_color"]}99;
    }}
    
    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {{
        background-color: {theme["sidebar_bg"]};
    }}
    .sidebar-session {{
        padding: 0.7rem 1rem;
        border-radius: 10px;
        margin: 0.3rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }}
    .sidebar-session:hover {{
        background: {theme["card_bg"]};
    }}
    .sidebar-session-active {{
        background: {theme["primary_color"]}15;
        border-color: {theme["primary_color"]}30;
    }}
    
    /* ===== STATUS INDICATORS ===== */
    .status-searching {{
        display: flex;
        align-items: center;
        gap: 8px;
        color: {theme["primary_color"]};
        font-size: 0.9rem;
        padding: 0.5rem;
        background: {theme["card_bg"]};
        border-radius: 8px;
        margin: 0.5rem 0;
    }}
    
    /* ===== MOD SEÇİCİ KUTUSU ===== */
    .mode-selector-box {{
        background: {theme["card_bg"]};
        border: 1px solid {theme["border_color"]};
        border-radius: 12px;
        padding: 0.8rem 1.2rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .mode-selector-box.web-active {{
        background: {theme["card_bg"]};
        border-color: {theme["primary_color"]}40;
    }}
    .mode-indicator {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        color: {theme["text_color"]}99;
    }}
    .mode-indicator.active {{
        color: {theme["primary_color"]};
        font-weight: 500;
    }}
    .mode-icon {{
        font-size: 1.1rem;
    }}
    
    /* ===== METRIC CARDS ===== */
    .metric-card {{
        background: {theme["bg_color"]};
        border: 1px solid {theme["border_color"]};
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }}
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        background: {theme["primary_gradient"]};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    /* ===== TAG STYLE ===== */
    .source-tag {{
        display: inline-block;
        background-color: {theme["card_bg"]};
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin: 0.2rem;
    }}
    
    /* ===== MESAJ DÜZENLEME ===== */
    .edit-message-btn {{
        opacity: 0.3;
        transition: opacity 0.2s;
    }}
    .edit-message-btn:hover {{
        opacity: 1;
    }}
    
    /* ===== TEMA ÖNIZLEME ===== */
    .theme-preview {{
        width: 100%;
        height: 60px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: white;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        border: 3px solid transparent;
    }}
    .theme-preview:hover {{
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .theme-preview.selected {{
        border-color: #22c55e;
        box-shadow: 0 0 0 3px #22c55e40;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    
    /* ===== STREAMLIT LOADING/RERUN EFEKTINI DEVRE DIŞI BIRAK ===== */
    /* Ana içeriğin soluklaşmasını engelle */
    .stApp > header + div > div {{
        opacity: 1 !important;
        transition: none !important;
    }}
    
    /* Running state sırasında dimming'i engelle */
    .stApp[data-teststate="running"] {{
        opacity: 1 !important;
    }}
    
    .stApp[data-teststate="running"] > * {{
        opacity: 1 !important;
        pointer-events: auto !important;
    }}
    
    /* Tüm elementlerin opacity geçişlerini kaldır */
    .element-container, .stMarkdown, .stButton, .stRadio, 
    .stSelectbox, .stTextInput, .stTextArea, .stCheckbox,
    .stToggle, .stExpander, .stContainer, .stColumns,
    [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"],
    [data-testid="column"], .row-widget {{
        opacity: 1 !important;
        transition: none !important;
    }}
    
    /* Sidebar soluklaşmasını engelle */
    section[data-testid="stSidebar"] {{
        opacity: 1 !important;
        transition: none !important;
    }}
    
    section[data-testid="stSidebar"] > div {{
        opacity: 1 !important;
    }}
    
    /* Chat mesajları için sabit opacity */
    .stChatMessage, [data-testid="stChatMessage"] {{
        opacity: 1 !important;
        transition: none !important;
    }}
    
    /* Main content dimming override */
    .main .block-container {{
        opacity: 1 !important;
        transition: none !important;
    }}
    
    /* Script runner running state override */
    div[data-testid="stAppViewContainer"] {{
        opacity: 1 !important;
        transition: none !important;
    }}
    
    /* Spinner dışındaki elementler her zaman görünür */
    .stSpinner ~ * {{
        opacity: 1 !important;
    }}
    
    /* Stale element stilini kaldır (grileşme efekti) */
    .stale-element {{
        opacity: 1 !important;
        filter: none !important;
    }}
    
    /* Form submit sırasında soluklaşmayı engelle */
    form {{
        opacity: 1 !important;
    }}
    
    /* Widget'lar disable olduğunda bile tam görünür */
    .stButton > button:disabled,
    .stTextInput > div > input:disabled,
    .stSelectbox > div:has(> div[aria-disabled="true"]) {{
        opacity: 0.7 !important;
    }}
    
    /* Geçiş animasyonlarını devre dışı bırak (performans için) */
    * {{
        -webkit-transition: none !important;
        -moz-transition: none !important;
        -o-transition: none !important;
        transition: none !important;
    }}
    
    /* Sadece hover efektleri için transition koru */
    .source-card:hover,
    .sidebar-session:hover,
    .theme-preview:hover,
    .related-query-chip:hover,
    .followup-item:hover {{
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease !important;
    }}
</style>
"""

# Page configuration
st.set_page_config(
    page_title="Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============ SESSION STATE INITIALIZATION ============
# RADIKAL ÇÖZÜM: URL query params ile session kontrolü
# - URL'de ?s=xxx varsa → o session yüklenir
# - URL temiz ise → HER ZAMAN yeni, boş session

def init_session_state():
    """
    Session state'i başlat - RADIKAL VERSİYON.
    
    Mantık:
    1. URL'de ?s=session_id varsa → o session'ı yükle
    2. URL temiz ise → YENİ session oluştur (eski konuşmayı yükleme!)
    3. Sidebar'dan tıklama → URL'ye ?s=xxx eklenir
    """
    # URL'den session parametresini al
    query_params = st.query_params
    url_session_id = query_params.get("s", None)
    
    # _page_load_id: Her tam sayfa yüklemesinde (F5, yeni sekme) farklı olur
    # Bu sayede sayfa yenilendiğinde yeni session başlatılır
    import hashlib
    page_load_marker = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    
    if "_last_page_load" not in st.session_state:
        st.session_state._last_page_load = page_load_marker
        st.session_state._force_new_session = True
    
    # URL'de session ID varsa → o session'ı yükle
    if url_session_id:
        # URL parametresi değiştiyse session'ı güncelle
        if st.session_state.get("_loaded_url_session") != url_session_id:
            existing = session_manager.get_session(url_session_id)
            if existing:
                st.session_state.session_id = url_session_id
                st.session_state.messages = [
                    {
                        "role": m.role,
                        "content": m.content,
                        "sources": m.sources if hasattr(m, 'sources') else [],
                        "web_sources": [],
                    }
                    for m in existing.messages
                ]
                st.session_state._loaded_url_session = url_session_id
                st.session_state._force_new_session = False
            else:
                # Session bulunamadı, yeni oluştur
                _create_fresh_session()
    
    # URL temiz ve yeni sayfa yüklemesi → YENİ SESSION
    elif st.session_state.get("_force_new_session", True):
        _create_fresh_session()
        st.session_state._force_new_session = False
    
    # Session ID yoksa → yeni oluştur
    elif "session_id" not in st.session_state:
        _create_fresh_session()
    
    # Mesajlar yoksa → boş liste
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Diğer state değişkenlerini init et
    _init_other_states()


def _create_fresh_session():
    """Tamamen yeni, boş session oluştur."""
    new_session = session_manager.create_session()
    st.session_state.session_id = new_session.id
    st.session_state.messages = []
    st.session_state._loaded_url_session = None
    # URL'yi temizle (eski session parametresini kaldır)
    st.query_params.clear()


def _init_other_states():
    """Diğer session state değişkenlerini init et."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"
    
    if "web_search_enabled" not in st.session_state:
        st.session_state.web_search_enabled = False
    
    if "response_mode" not in st.session_state:
        st.session_state.response_mode = "normal"  # "normal" veya "detailed"
    
    if "complexity_level" not in st.session_state:
        st.session_state.complexity_level = "auto"  # "auto", "simple", "moderate", "advanced", "comprehensive"
    
    if "viewing_session_id" not in st.session_state:
        st.session_state.viewing_session_id = None
    
    if "pending_sources" not in st.session_state:
        st.session_state.pending_sources = []
    
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    
    if "auto_scroll" not in st.session_state:
        st.session_state.auto_scroll = True
    
    if "show_timestamps" not in st.session_state:
        st.session_state.show_timestamps = False
    
    if "stop_generation" not in st.session_state:
        st.session_state.stop_generation = False
    
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    
    if "editing_note_id" not in st.session_state:
        st.session_state.editing_note_id = None
    
    if "note_category_filter" not in st.session_state:
        st.session_state.note_category_filter = "Tümü"
    
    # Tema seçimi
    if "selected_theme" not in st.session_state:
        st.session_state.selected_theme = "klasik"
    
    # Mesaj düzenleme için
    if "editing_message_index" not in st.session_state:
        st.session_state.editing_message_index = None
    
    # Yeni özellikler için session state
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "tr"  # tr, en, de
    
    if "response_length" not in st.session_state:
        st.session_state.response_length = "normal"  # short, normal, detailed
    
    if "show_keyboard_shortcuts" not in st.session_state:
        st.session_state.show_keyboard_shortcuts = False
    
    if "search_filters" not in st.session_state:
        st.session_state.search_filters = {
            "date_from": "",
            "date_to": "",
            "tags": [],
            "category": "",
            "pinned_only": False,
            "favorites_only": False,
        }
    
    if "show_templates" not in st.session_state:
        st.session_state.show_templates = False
    
    if "active_template_category" not in st.session_state:
        st.session_state.active_template_category = "Tümü"

init_session_state()

# Apply selected theme CSS
st.markdown(get_theme_css(st.session_state.selected_theme), unsafe_allow_html=True)

# ===== GLOBAL ANTI-FLICKER CSS =====
# Bu CSS, Streamlit'in rerun sırasındaki soluklaşma efektini tamamen devre dışı bırakır
st.markdown("""
<style>
    /* Streamlit'in running state sırasındaki opacity değişikliğini engelle */
    .stApp, .stApp > *, .main, .main > *, 
    [data-testid="stAppViewContainer"], 
    [data-testid="stAppViewContainer"] > *,
    .block-container, .block-container > * {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
    
    /* Element container'ların soluklaşmasını engelle */
    .element-container {
        opacity: 1 !important;
        transition: none !important;
    }
    
    /* Stale durumundaki elementler için */
    [data-stale="true"], .stale {
        opacity: 1 !important;
        filter: none !important;
    }
    
    /* Running indicator animasyonunu gizle (opsiyonel) */
    .stStatusWidget, [data-testid="stStatusWidget"] {
        display: none !important;
    }
    
    /* Script run sırasında blur/dim efektini engelle */
    .withScreencast > div:first-child {
        opacity: 1 !important;
    }
    
    /* Sidebar hiçbir zaman soluklaşmasın */
    [data-testid="stSidebar"], 
    [data-testid="stSidebar"] * {
        opacity: 1 !important;
        transition: none !important;
    }
    
    /* Button ve input elementleri her zaman interaktif görünsün */
    button, input, select, textarea {
        opacity: 1 !important;
        pointer-events: auto !important;
    }
    
    /* Chat input özellikle korunsun */
    [data-testid="stChatInput"], 
    [data-testid="stChatInput"] * {
        opacity: 1 !important;
    }
</style>
""", unsafe_allow_html=True)


# ============ HELPER FUNCTIONS ============

def save_message_to_session(role: str, content: str, sources: list = None):
    """Mesajı session dosyasına kaydet."""
    session_manager.add_message(
        st.session_state.session_id,
        role=role,
        content=content,
        sources=sources or [],
    )
    
    if role == "user" and len(st.session_state.messages) == 0:
        session_manager.auto_title_session(st.session_state.session_id, content)


def load_session(session_id: str):
    """Session'ı yükle ve URL'yi güncelle."""
    session = session_manager.get_session(session_id)
    if session:
        st.session_state.session_id = session_id
        st.session_state.messages = [
            {
                "role": m.role,
                "content": m.content,
                "sources": m.sources if hasattr(m, 'sources') else [],
                "web_sources": [],
            }
            for m in session.messages
        ]
        st.session_state._loaded_url_session = session_id
        st.session_state._force_new_session = False
        # URL'ye session parametresi ekle (sayfa yenilenince aynı session açılsın)
        st.query_params["s"] = session_id
        return True
    return False


def create_new_session():
    """Yeni session oluştur ve URL'yi temizle."""
    new_session = session_manager.create_session()
    st.session_state.session_id = new_session.id
    st.session_state.messages = []
    st.session_state.web_search_enabled = False
    st.session_state._loaded_url_session = None
    st.session_state._force_new_session = False
    # URL'den session parametresini temizle
    st.query_params.clear()


# ============ HTTP SESSION WITH CONNECTION POOLING ============
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
import concurrent.futures

@st.cache_resource
def get_http_session():
    """
    Connection pooling ile HTTP session oluştur.
    Bu session tüm API isteklerinde kullanılır ve performansı artırır.
    """
    session = requests.Session()
    
    # Retry stratejisi - daha agresif, daha az deneme
    retry_strategy = Retry(
        total=1,  # Sadece 1 retry
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"]
    )
    
    # Connection pooling adapter
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=retry_strategy
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


# ============ GLOBAL HEALTH STATE (NON-BLOCKING) ============
# Bu, health check'in UI'ı bloklamaması için kullanılır

class HealthStateManager:
    """
    Non-blocking health state manager.
    Health check'i arka planda yapar, UI'ı bloklamaz.
    """
    def __init__(self):
        self._health_cache = None
        self._last_check = 0
        self._check_interval = 60  # 60 saniye cache
        self._is_checking = False
        self._lock = threading.Lock()
    
    def get_health(self, force_refresh: bool = False) -> dict:
        """
        Cached health durumunu döndür.
        Arka planda güncelleme yapar, hiçbir zaman bloklamaz.
        """
        current_time = time.time()
        
        # Cache geçerli mi?
        if not force_refresh and self._health_cache is not None:
            if current_time - self._last_check < self._check_interval:
                return self._health_cache
        
        # İlk çağrı veya cache expired - arka planda güncelle
        if not self._is_checking:
            self._trigger_background_check()
        
        # Mevcut cache'i döndür (varsa) veya varsayılan değer
        return self._health_cache or self._get_default_health()
    
    def _trigger_background_check(self):
        """Arka planda health check başlat."""
        with self._lock:
            if self._is_checking:
                return
            self._is_checking = True
        
        # ThreadPoolExecutor ile arka planda çalıştır
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        executor.submit(self._do_health_check)
        executor.shutdown(wait=False)
    
    def _do_health_check(self):
        """Gerçek health check - arka planda çalışır."""
        try:
            session = requests.Session()
            response = session.get(
                f"{API_BASE_URL}/health",
                timeout=2  # Çok kısa timeout - 2 saniye
            )
            if response.status_code == 200:
                self._health_cache = response.json()
                self._last_check = time.time()
        except Exception:
            # Hata olsa bile eski cache'i koru veya varsayılan kullan
            if self._health_cache is None:
                self._health_cache = self._get_default_health()
        finally:
            self._is_checking = False
    
    def _get_default_health(self) -> dict:
        """Varsayılan health durumu - backend bağlantısı yokken."""
        return {
            "status": "unknown",
            "components": {
                "llm": "unknown",
                "vector_store": "unknown",
                "api": "unknown"
            },
            "cached": True
        }

# Global health manager instance
_health_manager = HealthStateManager()


def api_request(method: str, endpoint: str, **kwargs):
    """API isteği yap (connection pooling ile)."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        session = get_http_session()
        
        # Default timeout - daha kısa
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30  # 120'den 30'a düşürüldü
        
        response = session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return None  # Sessizce None döndür, error gösterme
    except requests.exceptions.Timeout:
        return None  # Sessizce None döndür
    except Exception:
        return None  # Sessizce None döndür


def check_health_fast() -> dict:
    """
    HIZLI ve NON-BLOCKING health check.
    Asla UI'ı bloklamaz, her zaman anında döner.
    """
    return _health_manager.get_health()


@st.cache_data(ttl=120)  # 120 saniye cache - daha uzun
def check_health():
    """
    Sistem sağlık kontrolü - cached ve hızlı timeout ile.
    Artık non-blocking manager kullanıyor.
    """
    return check_health_fast()


# ============ WEBSOCKET CLIENT ============

class WebSocketClient:
    """
    Enterprise WebSocket Client with Auto-Reconnect + Resume.
    
    Mimari Prensibi:
    - WebSocket her an kapanabilir - bu normal
    - Kopma olduğunda client sessizce reconnect eder
    - Resume ile kaldığı yerden devam eder
    - Kullanıcı kopma hissetmez
    
    Özellikler:
    - Bidirectional communication
    - Düşük latency  
    - Stop komutu anında gönderilir
    - Keepalive otomatik
    - Otomatik yeniden bağlanma (max 5 deneme)
    - Resume desteği (stream_id + last_index ile)
    - Sessiz hata yönetimi (UI'ı bloklamaz)
    """
    
    def __init__(self):
        self.ws = None
        self.connected = False
        self.client_id = None
        self._max_retries = 5
        self._retry_delay = 0.3  # saniye - hızlı retry
        self._last_error = None
        self._current_stream_id = None
        self._last_token_index = -1
        self._received_tokens = []  # Resume için token geçmişi
    
    def connect(self, retry_count: int = 0) -> bool:
        """WebSocket bağlantısı kur (otomatik retry ile)."""
        try:
            import websocket
        except ImportError:
            return False  # websocket-client yüklü değil
        
        if self.connected and self.ws:
            return True
        
        try:
            self.client_id = st.session_state.session_id or str(uuid.uuid4())
            ws_url = API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
            ws_url = f"{ws_url}/ws/v2/{self.client_id}"
            
            self.ws = websocket.create_connection(
                ws_url,
                timeout=3,  # Daha kısa timeout
                enable_multithread=True
            )
            self.connected = True
            self._last_error = None
            
            # Bağlantı onayını bekle
            response = self.ws.recv()
            data = json.loads(response)
            if data.get("type") == "connected":
                return True
            
        except Exception as e:
            self.connected = False
            self.ws = None
            self._last_error = str(e)
            
            # Retry mekanizması
            if retry_count < self._max_retries:
                time.sleep(self._retry_delay)
                return self.connect(retry_count + 1)
            
            return False
        
        return False
    
    def disconnect(self):
        """WebSocket bağlantısını kapat."""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            self.connected = False
    
    def send_stop(self):
        """Stop komutu gönder."""
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps({"type": "stop"}))
            except:
                pass
    
    def stream_chat(self, message: str, session_id: str, web_search: bool = False, response_mode: str = "normal", complexity_level: str = "auto"):
        """
        WebSocket üzerinden streaming chat (auto-reconnect + resume ile).
        
        Kopma olursa:
        1. Sessizce reconnect eder
        2. Resume ile eksik token'ları alır  
        3. Kullanıcı fark etmez
        """
        try:
            import websocket
        except ImportError:
            yield {"type": "fallback_to_http"}
            return
        
        # State'i sıfırla
        self._current_stream_id = None
        self._last_token_index = -1
        self._received_tokens = []
        
        if not self.connect():
            yield {"type": "fallback_to_http"}
            return
        
        try:
            # Chat mesajı gönder
            self.ws.send(json.dumps({
                "type": "chat",
                "message": message,
                "session_id": session_id,
                "web_search": web_search,
                "response_mode": response_mode,
                "complexity_level": complexity_level
            }))
            
            # Yanıtları al
            reconnect_attempts = 0
            max_reconnect = 3
            
            while True:
                try:
                    response = self.ws.recv()
                    if not response:
                        continue
                    
                    reconnect_attempts = 0  # Başarılı mesaj, reset
                    data = json.loads(response)
                    msg_type = data.get("type")
                    
                    # Stream ID'yi kaydet (resume için)
                    if msg_type == "start":
                        self._current_stream_id = data.get("stream_id")
                        yield {"type": "status", "message": "Bağlantı kuruldu", "phase": "connect"}
                    
                    elif msg_type == "token":
                        token_index = data.get("index", self._last_token_index + 1)
                        content = data.get("content", "")
                        
                        # Duplicate kontrolü (resume sonrası)
                        if token_index > self._last_token_index:
                            self._last_token_index = token_index
                            self._received_tokens.append(content)
                            yield {"type": "token", "content": content}
                    
                    elif msg_type == "resume_data":
                        # Resume yanıtı - eksik token'ları işle
                        for token_data in data.get("tokens", []):
                            t_index = token_data.get("index", 0)
                            t_content = token_data.get("content", "")
                            if t_index > self._last_token_index:
                                self._last_token_index = t_index
                                self._received_tokens.append(t_content)
                                yield {"type": "token", "content": t_content}
                        
                        # Stream tamamlandıysa
                        if data.get("is_complete"):
                            status = data.get("status", "completed")
                            if status == "completed":
                                yield {"type": "end", "timing": {"total_ms": 0}, "stats": {}}
                            elif status == "stopped":
                                yield {"type": "stopped", "elapsed_ms": 0}
                            break
                    
                    elif msg_type == "status":
                        yield {"type": "status", "message": data.get("message", ""), "phase": data.get("phase", "")}
                    
                    elif msg_type == "sources":
                        yield {"type": "sources", "sources": data.get("sources", [])}
                    
                    elif msg_type == "end":
                        stats = data.get("stats", {})
                        yield {
                            "type": "end",
                            "timing": {"total_ms": stats.get("duration_ms", 0)},
                            "stats": stats
                        }
                        break
                    
                    elif msg_type == "stopped":
                        yield {"type": "stopped", "elapsed_ms": data.get("elapsed_ms", 0)}
                        break
                    
                    elif msg_type == "error":
                        yield {"type": "error", "message": data.get("message", "Bilinmeyen hata")}
                        break
                    
                    elif msg_type == "ping":
                        self.ws.send(json.dumps({"type": "pong"}))
                    
                    elif msg_type == "pong":
                        continue
                
                except websocket.WebSocketTimeoutException:
                    continue
                    
                except websocket.WebSocketConnectionClosedException:
                    # Bağlantı koptu - resume dene
                    if reconnect_attempts < max_reconnect and self._current_stream_id:
                        reconnect_attempts += 1
                        self.connected = False
                        self.ws = None
                        
                        # Kısa bekle ve reconnect
                        time.sleep(self._retry_delay * reconnect_attempts)
                        
                        if self.connect():
                            # Resume isteği gönder
                            self.ws.send(json.dumps({
                                "type": "resume",
                                "stream_id": self._current_stream_id,
                                "from_index": self._last_token_index + 1,
                                "session_id": session_id
                            }))
                            continue  # Döngüye devam
                    
                    # Resume başarısız
                    yield {"type": "error", "message": "Bağlantı koptu"}
                    break
                    
                except Exception as e:
                    yield {"type": "error", "message": str(e)}
                    break
                    
        except Exception as e:
            yield {"type": "error", "message": str(e)}


# Global WebSocket client
_ws_client = None

def get_ws_client():
    """WebSocket client singleton."""
    global _ws_client
    if _ws_client is None:
        _ws_client = WebSocketClient()
    return _ws_client


def stream_chat_message(message: str, use_web_search: bool = False, response_mode: str = "normal", complexity_level: str = "auto"):
    """
    Streaming chat mesajı gönder.
    
    WebSocket kullanılabiliyorsa WebSocket, yoksa HTTP Streaming.
    Otomatik fallback mekanizması ile kesintisiz çalışır.
    
    Args:
        complexity_level: "auto", "simple", "moderate", "advanced", "comprehensive"
    """
    use_http_fallback = False
    
    # Önce WebSocket dene (web search hariç)
    if not use_web_search:
        try:
            import websocket
            ws_available = True
        except ImportError:
            ws_available = False
        
        if ws_available:
            ws_client = get_ws_client()
            for event in ws_client.stream_chat(
                message, 
                st.session_state.session_id, 
                use_web_search, 
                response_mode,
                complexity_level
            ):
                # Fallback sinyali kontrolü
                if event.get("type") == "fallback_to_http":
                    use_http_fallback = True
                    break
                yield event
            
            # WebSocket başarılı olduysa çık
            if not use_http_fallback:
                return
    else:
        use_http_fallback = True
    
    # HTTP Streaming (fallback veya web search için)
    endpoint = "/api/chat/web-stream" if use_web_search else "/api/chat/stream"
    
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "web_search": use_web_search,
                "response_mode": response_mode,
                "complexity_level": complexity_level,
            },
            stream=True,
            timeout=180,
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        try:
                            data = json.loads(line_text[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
        else:
            yield {"type": "error", "message": f"Sunucu yanıt vermedi (HTTP {response.status_code}). Lütfen tekrar deneyin."}
    
    except requests.exceptions.ConnectionError:
        yield {"type": "error", "message": "⚠️ Backend bağlantısı kurulamadı. Lütfen sistemin çalıştığından emin olun."}
    except requests.exceptions.Timeout:
        yield {"type": "error", "message": "⚠️ İstek zaman aşımına uğradı. Lütfen tekrar deneyin."}
    except requests.exceptions.RequestException as e:
        yield {"type": "error", "message": f"Bağlantı hatası: {str(e)[:100]}"}


def stream_vision_message(message: str, image_file):
    """Görsel ile streaming chat mesajı gönder."""
    try:
        files = {"image": (image_file.name, image_file.getvalue(), image_file.type)}
        data = {
            "message": message,
            "session_id": st.session_state.session_id,
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/chat/vision",
            data=data,
            files=files,
            stream=True,
            timeout=120,
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        try:
                            data = json.loads(line_text[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
        else:
            yield {"type": "error", "message": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        yield {"type": "error", "message": str(e)}


def upload_document(file):
    """Döküman yükle - ROBUST VERSION."""
    file_type = file.type
    if not file_type:
        ext = Path(file.name).suffix.lower()
        type_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".ppt": "application/vnd.ms-powerpoint",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".csv": "text/csv",
            ".json": "application/json",
            ".html": "text/html",
        }
        file_type = type_map.get(ext, "application/octet-stream")
    
    # Dosya boyutuna göre dinamik timeout
    file_size_mb = file.size / (1024 * 1024) if file.size else 0
    base_timeout = 60
    # Her 10MB için 60 saniye ekle
    timeout = base_timeout + int(file_size_mb / 10) * 60
    timeout = min(timeout, 600)  # Max 10 dakika
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": (file.name, file, file_type)},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"success": False, "error": f"Timeout ({timeout}s): Dosya çok büyük, işlem uzun sürdü"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Bağlantı hatası: Backend'e ulaşılamadı"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_documents(query: str, top_k: int = 5):
    """Döküman ara."""
    return api_request("POST", "/api/search", json={"query": query, "top_k": top_k})


def get_documents():
    """Döküman listesi al."""
    return api_request("GET", "/api/documents")


def delete_document(doc_id: str):
    """Döküman sil."""
    return api_request("DELETE", f"/api/documents/{doc_id}")


def get_stats():
    """İstatistikleri al."""
    return api_request("GET", "/api/admin/stats")


def render_sources_box(sources: list, metadata: dict = None):
    """
    Premium kaynaklar kutusunu render et - Perplexity tarzı.
    
    Features:
    - Instant Answer gösterimi
    - Kaynak kartları (tip badge, güvenilirlik)
    - İlgili aramalar
    - Follow-up sorular
    """
    if not sources:
        return
    
    # Metadata'dan ek bilgiler
    instant_answer = metadata.get("instant_answer") if metadata else None
    knowledge_panel = metadata.get("knowledge_panel") if metadata else None
    related_queries = metadata.get("related_queries", []) if metadata else []
    search_time = metadata.get("search_time_ms", 0) if metadata else 0
    providers = metadata.get("providers", []) if metadata else []
    cached = metadata.get("cached", False) if metadata else False
    
    # Kaynak türü ikon ve badge mapping
    type_config = {
        "wiki": {"icon": "📚", "badge": "badge-wiki", "label": "Wikipedia"},
        "academic": {"icon": "🎓", "badge": "badge-academic", "label": "Akademik"},
        "news": {"icon": "📰", "badge": "badge-news", "label": "Haber"},
        "official": {"icon": "🏛️", "badge": "badge-official", "label": "Resmi"},
        "blog": {"icon": "✍️", "badge": "badge-blog", "label": "Blog"},
        "forum": {"icon": "💬", "badge": "badge-forum", "label": "Forum"},
        "unknown": {"icon": "🌐", "badge": "", "label": "Web"}
    }
    
    sources_html = '<div class="sources-container">'
    
    # Header
    sources_html += f'''
    <div class="sources-header">
        <div class="sources-header-left">
            <span class="sources-header-icon">📚</span>
            <span class="sources-header-title">Kaynaklar</span>
            <span class="sources-header-count">{len(sources)} kaynak</span>
        </div>
        <div class="sources-meta">
    '''
    
    if search_time:
        sources_html += f'<span class="sources-meta-item">⏱️ {search_time}ms</span>'
    if providers:
        sources_html += f'<span class="sources-meta-item">🔍 {", ".join(providers)}</span>'
    if cached:
        sources_html += '<span class="sources-meta-item">💾 Önbellek</span>'
    
    sources_html += '</div></div>'
    
    # Instant Answer varsa
    if instant_answer:
        ia_title = instant_answer.get('title', '')
        ia_abstract = instant_answer.get('abstract', '')
        ia_source = instant_answer.get('source', '')
        ia_url = instant_answer.get('url', '')
        
        sources_html += f'''
        <div class="instant-answer-box">
            <div class="instant-answer-header">
                <span>💡</span>
                <span>Hızlı Cevap</span>
            </div>
            <div class="instant-answer-content">{ia_abstract[:500]}</div>
            <div class="instant-answer-source">
                <span>📖</span>
                <a href="{ia_url}" target="_blank" style="color: #1565c0; text-decoration: none;">{ia_source}</a>
            </div>
        </div>
        '''
    
    # Kaynak kartları
    for i, source in enumerate(sources, 1):
        if isinstance(source, dict):
            title = source.get('title', f'Kaynak {i}')[:80]
            url = source.get('url', '#')
            domain = source.get('domain', urlparse(url).netloc if url != '#' else '')
            snippet = source.get('snippet', '')[:200]
            source_type = source.get('type', 'unknown')
            reliability = source.get('reliability', 0.5)
            word_count = source.get('word_count', 0)
        else:
            title = f"Kaynak {i}"
            url = str(source)
            domain = urlparse(url).netloc
            snippet = ""
            source_type = "unknown"
            reliability = 0.5
            word_count = 0
        
        config = type_config.get(source_type, type_config["unknown"])
        
        # Güvenilirlik yıldızları
        stars = "⭐" * min(5, max(1, int(reliability * 5)))
        
        # Favicon URL
        favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
        
        # Badge HTML'lerini ayrı oluştur (iç içe f-string sorununu önlemek için)
        type_badge_html = ""
        if config["badge"]:
            type_badge_html = f'<span class="source-badge {config["badge"]}">{config["icon"]} {config["label"]}</span>'
        
        reliability_badge_html = f'<span class="source-badge badge-reliability">{stars}</span>'
        
        word_count_badge_html = ""
        if word_count and word_count > 0:
            word_count_badge_html = f'<span class="source-badge" style="background:#f5f5f5;color:#888">{word_count} kelime</span>'
        
        snippet_html = ""
        if snippet:
            snippet_html = f'<div class="source-card-snippet">{snippet}...</div>'
        
        sources_html += f'''
        <div class="source-card" onclick="window.open('{url}', '_blank')">
            <div class="source-card-number">{i}</div>
            <div class="source-card-content">
                <div class="source-card-title">{title}</div>
                <div class="source-card-domain">
                    <img src="{favicon}" class="source-card-favicon" onerror="this.style.display='none'" />
                    <a href="{url}" target="_blank" class="source-card-url" onclick="event.stopPropagation()">{domain}</a>
                </div>
                {snippet_html}
                <div class="source-card-badges">
                    {type_badge_html}
                    {reliability_badge_html}
                    {word_count_badge_html}
                </div>
            </div>
        </div>
        '''
    
    # İlgili aramalar
    if related_queries:
        sources_html += '''
        <div class="related-queries">
            <div class="related-queries-title">🔎 İlgili Aramalar</div>
            <div>
        '''
        for query in related_queries[:5]:
            sources_html += f'<span class="related-query-chip">🔍 {query[:50]}</span>'
        sources_html += '</div></div>'
    
    sources_html += '</div>'
    
    st.markdown(sources_html, unsafe_allow_html=True)


def render_follow_up_questions(questions: list):
    """Follow-up sorularını render et"""
    if not questions:
        return
    
    html = '''
    <div class="followup-container">
        <div class="followup-title">
            <span>💡</span>
            <span>Devam Soruları</span>
        </div>
    '''
    
    for q in questions[:4]:
        html += f'<div class="followup-item"><span>→</span> {q}</div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_response_stats(timing: dict, word_count: int, sources_used: int, confidence: float):
    """Yanıt istatistiklerini render et"""
    total_ms = timing.get("total_ms", 0)
    search_ms = timing.get("search_ms", 0)
    gen_ms = timing.get("generation_ms", 0)
    
    # Süreyi formatla
    if total_ms > 60000:
        time_str = f"{total_ms // 60000}dk {(total_ms % 60000) // 1000}sn"
    else:
        time_str = f"{total_ms / 1000:.1f}sn"
    
    # Güven seviyesi
    if confidence >= 0.8:
        conf_label = "Yüksek"
        conf_color = "#22c55e"
    elif confidence >= 0.5:
        conf_label = "Orta"
        conf_color = "#f59e0b"
    else:
        conf_label = "Düşük"
        conf_color = "#ef4444"
    
    html = f'''
    <div class="response-stats">
        <span class="stat-item"><span class="stat-icon">⏱️</span> {time_str}</span>
        <span class="stat-item"><span class="stat-icon">📝</span> {word_count} kelime</span>
        <span class="stat-item"><span class="stat-icon">📚</span> {sources_used} kaynak</span>
        <span class="stat-item"><span class="stat-icon" style="color:{conf_color}">●</span> Güven: {conf_label}</span>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


# ============ SIDEBAR ============

with st.sidebar:
    st.markdown("## 🤖 Enterprise AI")
    st.markdown("---")
    
    # Navigation - AI ile Öğren eklendi
    page = st.radio(
        "📍 Navigasyon",
        ["💬 Chat", "📝 Notlar", "📜 Geçmiş", "📁 Dökümanlar", "🔍 Arama", "📚 AI ile Öğren", "⭐ Favoriler", "📋 Şablonlar", "📊 Dashboard", "⚙️ Ayarlar"],
        label_visibility="collapsed",
    )
    
    page_map = {
        "💬 Chat": "chat",
        "📝 Notlar": "notes",
        "📜 Geçmiş": "history",
        "📁 Dökümanlar": "documents",
        "🔍 Arama": "search",
        "📚 AI ile Öğren": "learning",
        "⭐ Favoriler": "favorites",
        "📋 Şablonlar": "templates",
        "📊 Dashboard": "dashboard",
        "⚙️ Ayarlar": "settings",
    }
    st.session_state.current_page = page_map.get(page, "chat")
    
    st.markdown("---")
    
    # ============ SESSION MANAGEMENT ============
    st.markdown("### 📂 Konuşmalar")
    
    col_new, col_filter = st.columns([2, 1])
    with col_new:
        if st.button("➕ Yeni", use_container_width=True, type="primary", on_click=create_new_session):
            pass  # on_click otomatik rerun yapar
    with col_filter:
        show_pinned_only = st.toggle("📌", help="Sadece sabitlenmiş")
    
    st.markdown("")
    
    # Son konuşmalar
    recent_sessions = session_manager.list_sessions(limit=15)
    
    # Filtre uygula
    if show_pinned_only:
        recent_sessions = [s for s in recent_sessions if s.get("is_pinned")]
    
    for session_info in recent_sessions:
        session_id = session_info["id"]
        title = session_info["title"][:22] + "..." if len(session_info["title"]) > 22 else session_info["title"]
        msg_count = session_info.get("message_count", 0)
        is_current = session_id == st.session_state.session_id
        is_pinned = session_info.get("is_pinned", False)
        tags = session_info.get("tags", [])
        category = session_info.get("category", "")
        
        # Session kartı
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                pin_icon = "📌 " if is_pinned else ""
                if is_current:
                    st.markdown(f"🟢 **{pin_icon}{title}**")
                else:
                    st.button(f"💬 {pin_icon}{title}", key=f"s_{session_id}", use_container_width=True,
                             on_click=load_session, args=(session_id,))
            
            with col2:
                # Pin/Unpin butonu
                pin_label = "📍" if is_pinned else "📌"
                st.button(pin_label, key=f"pin_{session_id}", help="Sabitle/Kaldır",
                         on_click=lambda sid=session_id: session_manager.toggle_pin(sid))
            
            with col3:
                # Silme butonu - callback ile
                def delete_session_callback(sid, is_curr):
                    session_manager.delete_session(sid)
                    if is_curr:
                        create_new_session()
                
                st.button("🗑️", key=f"del_{session_id}", help="Sil",
                         on_click=delete_session_callback, args=(session_id, is_current))
            
            # Etiketler göster
            if tags:
                tags_str = " ".join([f"`{t}`" for t in tags[:3]])
                st.caption(tags_str)
    
    st.markdown("---")
    
    # Mevcut sohbet için hızlı ayarlar
    if st.session_state.current_page == "chat":
        with st.expander("🏷️ Sohbet Ayarları", expanded=False):
            # Kategori seçimi
            categories = list(TRANSLATIONS["tr"]["categories"].values())
            current_session = session_manager.get_session(st.session_state.session_id)
            current_category = current_session.category if current_session else ""
            
            new_category = st.selectbox(
                "Kategori",
                [""] + categories,
                index=categories.index(current_category) + 1 if current_category in categories else 0,
                key="session_category"
            )
            if new_category != current_category:
                session_manager.set_category(st.session_state.session_id, new_category)
            
            # Etiket ekleme
            new_tag = st.text_input("Yeni etiket", placeholder="Etiket yazın...", key="new_tag_input")
            
            def add_tag_callback():
                tag = st.session_state.new_tag_input
                if tag:
                    session_manager.add_tag(st.session_state.session_id, tag)
            
            st.button("➕ Ekle", key="add_tag_btn", on_click=add_tag_callback)
            
            # Mevcut etiketler
            if current_session and current_session.tags:
                st.caption("Mevcut etiketler:")
                for tag in current_session.tags:
                    col_tag, col_del = st.columns([4, 1])
                    with col_tag:
                        st.markdown(f"`{tag}`")
                    with col_del:
                        st.button("×", key=f"del_tag_{tag}",
                                 on_click=lambda t=tag: session_manager.remove_tag(st.session_state.session_id, t))
    
    st.markdown("---")
    
    # Yanıt Uzunluğu Ayarı
    st.markdown("### 📏 Yanıt Uzunluğu")
    response_options = {
        "short": "🔹 Kısa",
        "normal": "🔸 Normal",
        "detailed": "🔶 Detaylı"
    }
    st.session_state.response_length = st.radio(
        "Yanıt uzunluğu",
        options=list(response_options.keys()),
        format_func=lambda x: response_options[x],
        index=list(response_options.keys()).index(st.session_state.response_length),
        label_visibility="collapsed",
        horizontal=True,
    )
    
    st.markdown("---")
    
    # Health Status - NON-BLOCKING, anında render
    st.markdown("### 🔧 Sistem")
    
    # Fast health check - hiçbir zaman beklemez
    health = check_health_fast()
    
    if health:
        status = health.get("status", "unknown")
        is_cached = health.get("cached", False)
        
        if status == "healthy":
            st.success("✅ Aktif")
        elif status == "unknown":
            st.info("🔄 Kontrol ediliyor..." if not is_cached else "⚪ Bağlanıyor...")
        else:
            st.warning(f"⚠️ {status}")
        
        components = health.get("components", {})
        cols = st.columns(2)
        with cols[0]:
            llm_status = components.get("llm", "unknown")
            if llm_status == "healthy":
                st.markdown("🟢 LLM")
            elif llm_status == "unknown":
                st.markdown("⚪ LLM")
            else:
                st.markdown("🔴 LLM")
        with cols[1]:
            vs_status = components.get("vector_store", "unknown")
            if vs_status == "healthy":
                st.markdown("🟢 VectorDB")
            elif vs_status == "unknown":
                st.markdown("⚪ VectorDB")
            else:
                st.markdown("🔴 VectorDB")
    else:
        st.info("⚪ Bağlanıyor...")
    
    st.markdown("---")
    st.caption(f"Session: {st.session_state.session_id[:8]}...")
    st.caption(f"Mesaj: {len(st.session_state.messages)}")
    
    # Klavye Kısayolları butonu
    if st.button("⌨️ Klavye Kısayolları", use_container_width=True):
        st.session_state.show_keyboard_shortcuts = True


# ============ MAIN CONTENT ============

# Header
st.markdown('<p class="main-header">🤖 Enterprise AI Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Endüstri Standartlarında Kurumsal AI Çözümü • Web Search • RAG • Multi-Agent</p>', unsafe_allow_html=True)


# ============ CHAT PAGE ============

if st.session_state.current_page == "chat":
    
    # ===== GÖRSEL YÜKLEME =====
    with st.expander("📷 Görsel Analizi (VLM)", expanded=False):
        uploaded_image = st.file_uploader(
            "Görsel yükle",
            type=["jpg", "jpeg", "png", "gif", "webp"],
            help="AI görsel analizi için resim yükleyin",
            key="vision_uploader"
        )
        if uploaded_image:
            st.image(uploaded_image, caption="Yüklenen Görsel", width=250)
            vision_prompt = st.text_input("Görsel hakkında soru", placeholder="Bu görselde ne var?", key="vision_prompt")
            if st.button("🔍 Analiz Et", use_container_width=True, key="vision_analyze"):
                if vision_prompt:
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"📷 {vision_prompt}",
                        "sources": [],
                        "web_sources": [],
                    })
                    save_message_to_session("user", f"📷 {vision_prompt}")
                    
                    # Vision analizi yap
                    with st.spinner("Görsel analiz ediliyor..."):
                        full_response = ""
                        for chunk in stream_vision_message(vision_prompt, uploaded_image):
                            if chunk.get("type") == "token":
                                full_response += chunk.get("content", "")
                            elif chunk.get("type") == "error":
                                st.error(f"Hata: {chunk.get('message')}")
                                break
                        
                        if full_response:
                            save_message_to_session("assistant", full_response, ["Görsel Analizi"])
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": full_response,
                                "sources": ["Görsel Analizi"],
                                "web_sources": [],
                            })
                    st.rerun()
    
    st.markdown("---")
    
    # ===== MESAJLAR =====
    chat_container = st.container()
    
    with chat_container:
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    # Düzenleme modunda mı kontrol et
                    if st.session_state.editing_message_index == i:
                        # Düzenleme formu
                        edit_col1, edit_col2 = st.columns([6, 1])
                        with edit_col1:
                            edited_content = st.text_area(
                                "Mesajı düzenle",
                                value=msg["content"],
                                key=f"edit_msg_{i}",
                                height=100,
                                label_visibility="collapsed"
                            )
                        with edit_col2:
                            def save_edit(idx):
                                content = st.session_state.get(f"edit_msg_{idx}", "")
                                st.session_state.messages[idx]["content"] = content
                                st.session_state.messages = st.session_state.messages[:idx+1]
                                st.session_state.editing_message_index = None
                                st.session_state.pending_edit_message = content
                            
                            st.button("✅", key=f"save_edit_{i}", help="Kaydet ve yeniden gönder",
                                     on_click=save_edit, args=(i,))
                            st.button("❌", key=f"cancel_edit_{i}", help="İptal",
                                     on_click=lambda: setattr(st.session_state, 'editing_message_index', None))
                    else:
                        # Normal görünüm
                        msg_col1, msg_col2 = st.columns([20, 1])
                        with msg_col1:
                            st.write(msg["content"])
                        with msg_col2:
                            st.button("✏️", key=f"edit_btn_{i}", help="Mesajı düzenle",
                                     on_click=lambda idx=i: setattr(st.session_state, 'editing_message_index', idx))
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
                    
                    # Web kaynakları varsa göster
                    web_sources = msg.get("web_sources", [])
                    if web_sources:
                        msg_metadata = msg.get("metadata", {})
                        render_sources_box(web_sources, msg_metadata)
                    
                    # Normal kaynaklar
                    sources = msg.get("sources", [])
                    if sources and not web_sources:
                        if isinstance(sources[0], str):
                            st.caption("📚 Kaynaklar: " + ", ".join(sources))
                    
                    # Mesaj aksiyon butonları
                    is_favorite = msg.get("is_favorite", False)
                    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 6])
                    
                    with btn_col1:
                        fav_icon = "⭐" if is_favorite else "☆"
                        
                        def toggle_fav(idx, current_fav):
                            st.session_state.messages[idx]["is_favorite"] = not current_fav
                            session_manager.toggle_message_favorite(st.session_state.session_id, idx)
                        
                        st.button(fav_icon, key=f"fav_{i}", help="Favorilere ekle/çıkar",
                                 on_click=toggle_fav, args=(i, is_favorite))
                    
                    with btn_col2:
                        def regenerate_response(idx):
                            if idx > 0:
                                prev_user_msg = None
                                for j in range(idx - 1, -1, -1):
                                    if st.session_state.messages[j]["role"] == "user":
                                        prev_user_msg = st.session_state.messages[j]["content"]
                                        break
                                if prev_user_msg:
                                    st.session_state.messages = st.session_state.messages[:idx]
                                    st.session_state.pending_edit_message = prev_user_msg
                        
                        st.button("🔄", key=f"regen_{i}", help="Yanıtı yeniden üret",
                                 on_click=regenerate_response, args=(i,))
                    
                    with btn_col3:
                        if st.button("📋", key=f"copy_{i}", help="Panoya kopyala"):
                            st.toast("Mesaj panoya kopyalandı!", icon="✅")
    
    # ===== ŞABLON SEÇİCİ =====
    templates = session_manager.get_templates()
    if templates:
        with st.expander("📋 Hızlı Şablonlar", expanded=False):
            template_cols = st.columns(4)
            for idx, template in enumerate(templates[:8]):  # Max 8 şablon göster
                with template_cols[idx % 4]:
                    def use_template(tmpl_content, tmpl_id):
                        st.session_state.template_to_use = tmpl_content
                        session_manager.increment_template_use(tmpl_id)
                    
                    st.button(f"📝 {template['title'][:15]}", key=f"quick_template_{template['id']}", 
                             use_container_width=True, on_click=use_template, 
                             args=(template["content"], template["id"]))
    
    # Şablon kullanılacaksa göster
    if "template_to_use" in st.session_state and st.session_state.template_to_use:
        st.info(f"📋 **Şablon yüklendi.** Aşağıdaki kutuya yapıştırın veya düzenleyin.")
        st.code(st.session_state.template_to_use[:200] + "..." if len(st.session_state.template_to_use) > 200 else st.session_state.template_to_use)
        col_use, col_cancel = st.columns(2)
        with col_cancel:
            st.button("❌ İptal", use_container_width=True, 
                     on_click=lambda: setattr(st.session_state, 'template_to_use', None))
    
    # ===== MOD SEÇİCİ KUTUSU (INPUT ÜSTÜNDE) =====
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 1, 6])
        
        with col1:
            web_enabled = st.toggle(
                "🌐 Web",
                value=st.session_state.web_search_enabled,
                help="Web'de arama yaparak yanıt ver",
                key="web_toggle"
            )
            st.session_state.web_search_enabled = web_enabled
        
        with col2:
            detailed_mode = st.toggle(
                "📝 Detaylı",
                value=st.session_state.response_mode == "detailed",
                help="Daha uzun ve kapsamlı yanıtlar al",
                key="detailed_toggle"
            )
            st.session_state.response_mode = "detailed" if detailed_mode else "normal"
        
        with col3:
            # Complexity Level Seçici
            complexity_options = {
                "auto": "🤖 Otomatik",
                "simple": "🟢 Basit",
                "moderate": "🟡 Orta",
                "advanced": "🟠 İleri",
                "comprehensive": "🔴 Kapsamlı"
            }
            
            selected_complexity = st.selectbox(
                "Yanıt Seviyesi",
                options=list(complexity_options.keys()),
                format_func=lambda x: complexity_options[x],
                index=list(complexity_options.keys()).index(st.session_state.complexity_level),
                help="Otomatik: Makine karar verir | Basit: Hızlı yanıt | Orta: Dengeli | İleri: Detaylı analiz | Kapsamlı: Tam araştırma",
                key="complexity_select",
                label_visibility="collapsed"
            )
            st.session_state.complexity_level = selected_complexity
    
    # Mode bilgisi
    with st.container():
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            mode_texts = []
            if st.session_state.web_search_enabled:
                mode_texts.append("🌐 Web")
            if st.session_state.response_mode == "detailed":
                mode_texts.append("📝 Detaylı")
            if mode_texts:
                st.caption(" • ".join(mode_texts))
        with col_info2:
            level_info = complexity_options.get(st.session_state.complexity_level, "🤖 Otomatik")
            st.caption(f"Seviye: {level_info}")
    
    # ===== CHAT INPUT =====
    user_input = st.chat_input("Mesajınızı yazın...", key="main_chat_input", disabled=st.session_state.is_generating)
    
    # Düzenlenen mesaj varsa onu kullan
    if "pending_edit_message" in st.session_state and st.session_state.pending_edit_message:
        user_input = st.session_state.pending_edit_message
        st.session_state.pending_edit_message = None
        # Düzenleme durumunda mesaj zaten listede, ekleme yapma
        skip_add_message = True
    else:
        skip_add_message = False
    
    if user_input:
        import time
        start_time = time.time()
        
        # Reset stop flag
        st.session_state.stop_generation = False
        st.session_state.is_generating = True
        
        # ✅ ÖNCE kullanıcı mesajını HEMEN ekle - prompt kaybolmasın!
        if not skip_add_message:
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "sources": [],
                "web_sources": [],
            })
            save_message_to_session("user", user_input)
        
        # ✅ Kullanıcı mesajını HEMEN render et (AI yanıtı gelmeden önce görünsün)
        with st.chat_message("user"):
            st.write(user_input)
        
        # AI yanıtını al
        with st.chat_message("assistant"):
            # Status container (loading/complete indicator)
            status_container = st.container()
            response_placeholder = st.empty()
            sources_placeholder = st.empty()
            stop_button_placeholder = st.empty()
            
            full_response = ""
            error_message = None  # ✅ Hata mesajını tutmak için
            web_sources = []
            was_stopped = False
            response_started = False
            
            # Durdur butonu göster
            with stop_button_placeholder:
                if st.button("⏹️ Yanıtı Durdur", key="stop_gen_btn", type="secondary", use_container_width=True):
                    st.session_state.stop_generation = True
            
            # ✅ CANLI SÜRE SAYACI - JavaScript ile gerçek zamanlı güncelleme
            with status_container:
                loading_placeholder = st.empty()
                # JavaScript ile canlı sayaç - her saniye güncellenir
                timer_id = f"timer_{int(time.time() * 1000)}"
                loading_placeholder.markdown(
                    f'''
                    <div id="{timer_id}" style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
                        padding: 8px 12px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                        border-radius: 8px; border-left: 3px solid #667eea;">
                        <div class="loading-spinner"></div>
                        <span style="color: #495057; font-size: 0.9rem; font-weight: 500;">Yanıt hazırlanıyor...</span>
                        <span id="{timer_id}_time" style="color: #868e96; font-size: 0.85rem; margin-left: auto; font-family: monospace;">
                            ⏱️ 0.0s
                        </span>
                    </div>
                    <style>
                        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                        .loading-spinner {{ width: 18px; height: 18px; border: 2px solid #e0e0e0;
                            border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }}
                    </style>
                    <script>
                        (function() {{
                            var startTime = Date.now();
                            var timerEl = document.getElementById("{timer_id}_time");
                            if (timerEl) {{
                                var interval = setInterval(function() {{
                                    var elapsed = (Date.now() - startTime) / 1000;
                                    if (elapsed < 60) {{
                                        timerEl.textContent = "⏱️ " + elapsed.toFixed(1) + "s";
                                    }} else {{
                                        var mins = Math.floor(elapsed / 60);
                                        var secs = Math.floor(elapsed % 60);
                                        timerEl.textContent = "⏱️ " + mins + "m " + secs + "s";
                                    }}
                                    // Stop after 5 minutes max
                                    if (elapsed > 300) clearInterval(interval);
                                }}, 100);
                                // Store interval for cleanup
                                window.currentTimerInterval = interval;
                            }}
                        }})();
                    </script>
                    ''',
                    unsafe_allow_html=True
                )
            
            # Stream yanıt
            search_metadata = {}
            follow_up_questions = []
            response_timing = {}
            confidence_score = 0.8
            
            for chunk in stream_chat_message(user_input, st.session_state.web_search_enabled, st.session_state.response_mode, st.session_state.complexity_level):
                # ✅ Her chunk'ta süreyi güncelle (final için)
                current_elapsed = time.time() - start_time
                elapsed_str = f"{current_elapsed:.1f}s" if current_elapsed < 60 else f"{int(current_elapsed//60)}m {int(current_elapsed%60)}s"
                
                # Durdurma kontrolü
                if st.session_state.stop_generation:
                    was_stopped = True
                    # Backend'e stop mesajı gönder
                    try:
                        ws_client = get_ws_client()
                        ws_client.send_stop()
                    except:
                        pass
                    # O ana kadar oluşan yanıtı koru ve göster
                    if full_response:
                        full_response += "\n\n*[Yanıt durduruldu]*"
                        response_placeholder.markdown(full_response)
                    break
                
                chunk_type = chunk.get("type")
                
                if chunk_type == "status":
                    status_msg = chunk.get("message", "")
                    phase = chunk.get("phase", "")
                    
                    # Faz bazlı ikon
                    phase_icons = {
                        "search": "🔍",
                        "analyze": "📊",
                        "context": "📝",
                        "generate": "✨"
                    }
                    icon = phase_icons.get(phase, "⏳")
                    
                    # ✅ Status güncellemesi - JavaScript sayaç devam eder
                    status_timer_id = f"status_{int(time.time() * 1000)}"
                    loading_placeholder.markdown(
                        f'''
                        <div id="{status_timer_id}" style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
                            padding: 8px 12px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                            border-radius: 8px; border-left: 3px solid #667eea;">
                            <div class="loading-spinner"></div>
                            <span style="color: #495057; font-size: 0.9rem; font-weight: 500;">{icon} {status_msg}</span>
                            <span id="{status_timer_id}_time" style="color: #868e96; font-size: 0.85rem; margin-left: auto; font-family: monospace;">
                                ⏱️ {elapsed_str}
                            </span>
                        </div>
                        <style>
                            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                            .loading-spinner {{ width: 18px; height: 18px; border: 2px solid #e0e0e0;
                                border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }}
                        </style>
                        <script>
                            (function() {{
                                var baseTime = {current_elapsed};
                                var startTime = Date.now();
                                var timerEl = document.getElementById("{status_timer_id}_time");
                                if (timerEl && !window.statusTimerRunning) {{
                                    window.statusTimerRunning = true;
                                    setInterval(function() {{
                                        var elapsed = baseTime + (Date.now() - startTime) / 1000;
                                        if (elapsed < 60) {{
                                            timerEl.textContent = "⏱️ " + elapsed.toFixed(1) + "s";
                                        }} else {{
                                            var mins = Math.floor(elapsed / 60);
                                            var secs = Math.floor(elapsed % 60);
                                            timerEl.textContent = "⏱️ " + mins + "m " + secs + "s";
                                        }}
                                    }}, 100);
                                }}
                            }})();
                        </script>
                        ''',
                        unsafe_allow_html=True
                    )
                
                elif chunk_type == "sources":
                    web_sources = chunk.get("sources", [])
                    # Metadata'yı kaydet
                    search_metadata = {
                        "instant_answer": chunk.get("instant_answer"),
                        "knowledge_panel": chunk.get("knowledge_panel"),
                        "related_queries": chunk.get("related_queries", []),
                        "search_time_ms": chunk.get("search_time_ms", 0),
                        "providers": chunk.get("providers", []),
                        "cached": chunk.get("cached", False)
                    }
                    
                    # Premium kaynakları göster
                    if web_sources:
                        with sources_placeholder:
                            render_sources_box(web_sources, search_metadata)
                
                elif chunk_type == "metadata":
                    # Intent ve style bilgisi
                    intent = chunk.get("intent", "")
                    style = chunk.get("style", "")
                    source_count = chunk.get("source_count", 0)
                
                elif chunk_type == "token":
                    if not response_started:
                        response_started = True
                    # ✅ Yazılıyor durumu - yeşil spinner + JavaScript canlı süre
                    token_timer_id = f"token_{int(time.time() * 1000)}"
                    loading_placeholder.markdown(
                        f'''
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
                            padding: 8px 12px; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                            border-radius: 8px; border-left: 3px solid #22c55e;">
                            <div class="loading-spinner-green"></div>
                            <span style="color: #166534; font-size: 0.9rem; font-weight: 500;">✍️ Yazılıyor...</span>
                            <span id="{token_timer_id}_time" style="color: #15803d; font-size: 0.85rem; margin-left: auto; font-family: monospace;">
                                ⏱️ {elapsed_str}
                            </span>
                        </div>
                        <style>
                            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                            .loading-spinner-green {{ width: 18px; height: 18px; border: 2px solid #bbf7d0;
                                border-top: 2px solid #22c55e; border-radius: 50%; animation: spin 1s linear infinite; }}
                        </style>
                        <script>
                            (function() {{
                                var baseTime = {current_elapsed};
                                var startTime = Date.now();
                                var timerEl = document.getElementById("{token_timer_id}_time");
                                if (timerEl) {{
                                    setInterval(function() {{
                                        var elapsed = baseTime + (Date.now() - startTime) / 1000;
                                        if (elapsed < 60) {{
                                            timerEl.textContent = "⏱️ " + elapsed.toFixed(1) + "s";
                                        }} else {{
                                            var mins = Math.floor(elapsed / 60);
                                            var secs = Math.floor(elapsed % 60);
                                            timerEl.textContent = "⏱️ " + mins + "m " + secs + "s";
                                        }}
                                    }}, 100);
                                }}
                            }})();
                        </script>
                        ''',
                        unsafe_allow_html=True
                    )
                    full_response += chunk.get("content", "")
                    response_placeholder.markdown(full_response + "▌")
                
                elif chunk_type == "warning":
                    st.warning(chunk.get("message", ""))
                
                elif chunk_type == "error":
                    # ✅ HATA MESAJINI KAYDET - kalıcı olarak chat'te gösterilecek
                    error_message = chunk.get('message', 'Bilinmeyen hata')
                    break
                
                elif chunk_type == "stopped":
                    # Backend tarafından durduruldu - yanıtı koru
                    was_stopped = True
                    if full_response:
                        full_response += "\n\n*[Yanıt durduruldu]*"
                        response_placeholder.markdown(full_response)
                    break
                
                elif chunk_type == "end":
                    # Final bilgileri al
                    final_sources = chunk.get("sources", web_sources)
                    if final_sources:
                        web_sources = final_sources
                    
                    follow_up_questions = chunk.get("follow_up_questions", [])
                    confidence_score = chunk.get("confidence_score", 0.8)
                    response_timing = chunk.get("timing", {})
                    break
            
            # Durdur butonunu kaldır
            stop_button_placeholder.empty()
            
            # Yanıt süresini hesapla
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            if minutes > 0:
                time_str = f"{minutes} dk {seconds} sn"
            else:
                time_str = f"{seconds} sn"
            
            # ✅ HATA DURUMU - Kalıcı hata mesajı göster
            if error_message:
                # Kırmızı hata durumu göster
                loading_placeholder.markdown(
                    f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; '
                    f'padding: 10px 14px; background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); '
                    f'border-radius: 8px; border-left: 3px solid #ef4444;">'
                    f'<span style="color: #dc2626; font-size: 1.2rem;">❌</span>'
                    f'<span style="color: #991b1b; font-size: 0.9rem; font-weight: 500;">Bağlantı Hatası</span>'
                    f'<span style="color: #b91c1c; font-size: 0.85rem; margin-left: auto;">⏱️ {time_str}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                # Hata detayını göster
                response_placeholder.markdown(
                    f'<div style="padding: 16px; background: #fef2f2; border-radius: 8px; '
                    f'border: 1px solid #fecaca; margin: 10px 0;">'
                    f'<div style="color: #dc2626; font-weight: 600; margin-bottom: 8px;">⚠️ Sunucuya bağlanılamadı</div>'
                    f'<div style="color: #7f1d1d; font-size: 0.9rem;">{error_message}</div>'
                    f'<div style="color: #991b1b; font-size: 0.85rem; margin-top: 10px;">'
                    f'💡 <b>Çözüm:</b> Backend sunucusunun çalıştığından emin olun (port 8001)</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                # ✅ Hata mesajını chat'e KALICI olarak ekle
                error_content = f"❌ **Bağlantı Hatası**\n\n{error_message}\n\n*Sunucu yanıt vermedi. Backend'in çalıştığından emin olun.*"
                save_message_to_session("assistant", error_content, [])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_content,
                    "sources": [],
                    "web_sources": [],
                    "is_error": True
                })
            
            # Normal yanıt render
            elif full_response:
                response_placeholder.markdown(full_response)
                
                # Kaynakları tekrar göster (eğer varsa ve henüz gösterilmediyse)
                if web_sources:
                    with sources_placeholder:
                        render_sources_box(web_sources, search_metadata)
                
                # Follow-up sorular (web search modunda)
                if follow_up_questions and st.session_state.web_search_enabled:
                    render_follow_up_questions(follow_up_questions)
                
                # Response istatistikleri
                if response_timing and st.session_state.web_search_enabled:
                    render_response_stats(
                        response_timing,
                        len(full_response.split()),
                        len(web_sources),
                        confidence_score
                    )
                
                # Loading'i yeşil tik ile değiştir - PROFESYONEl GÖRÜNÜM
                if was_stopped:
                    loading_placeholder.markdown(
                        f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; '
                        f'padding: 8px 12px; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); '
                        f'border-radius: 8px; border-left: 3px solid #f59e0b;">'
                        f'<span style="color: #d97706; font-size: 1.1rem;">⚠️</span>'
                        f'<span style="color: #92400e; font-size: 0.9rem; font-weight: 500;">Durduruldu</span>'
                        f'<span style="color: #b45309; font-size: 0.85rem; margin-left: auto; font-family: monospace;">⏱️ {time_str}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    # ✅ TOPLAM SÜRE - elapsed_time kullan (her zaman doğru)
                    total_seconds = elapsed_time
                    if total_seconds >= 60:
                        mins = int(total_seconds // 60)
                        secs = int(total_seconds % 60)
                        time_display = f"{mins}dk {secs}sn"
                    else:
                        time_display = f"{total_seconds:.1f}sn"
                    
                    # Word count
                    word_count = len(full_response.split()) if full_response else 0
                    
                    # ✅ YEŞİL TİK - Profesyonel tamamlandı görünümü + detaylı istatistik
                    loading_placeholder.markdown(
                        f'''
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
                            padding: 10px 14px; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                            border-radius: 8px; border-left: 3px solid #22c55e;">
                            <span style="color: #22c55e; font-size: 1.3rem;">✓</span>
                            <span style="color: #166534; font-size: 0.9rem; font-weight: 600;">Tamamlandı</span>
                            <span style="color: #15803d; font-size: 0.8rem; opacity: 0.8;">({word_count} kelime)</span>
                            <span style="color: #166534; font-size: 0.9rem; margin-left: auto; font-family: 'SF Mono', Monaco, monospace; font-weight: 600;">
                                ⏱️ {time_display}
                            </span>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                
                # Mesajı kaydet
                source_urls = [s.get("url", "") if isinstance(s, dict) else str(s) for s in web_sources] if web_sources else []
                save_message_to_session("assistant", full_response, source_urls)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sources": source_urls,
                    "web_sources": web_sources,
                    "metadata": search_metadata,
                    "follow_ups": follow_up_questions
                })
        
        # Reset flags
        st.session_state.is_generating = False
        st.session_state.stop_generation = False
        st.rerun()
    
    # ===== ÖRNEK SORULAR =====
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Örnek Sorular")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 İzin politikası nedir?", use_container_width=True, key="ex1"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "İzin politikası nedir?",
                    "sources": [],
                    "web_sources": [],
                })
                save_message_to_session("user", "İzin politikası nedir?")
                st.rerun()
        
        with col2:
            if st.button("📧 Email taslağı hazırla", use_container_width=True, key="ex2"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "Toplantı daveti için email taslağı hazırla",
                    "sources": [],
                    "web_sources": [],
                })
                save_message_to_session("user", "Toplantı daveti için email taslağı hazırla")
                st.rerun()
        
        with col3:
            if st.button("🕐 Geçmişte ne sordum?", use_container_width=True, key="ex3"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "Daha önce sana hangi konularda sorular sordum?",
                    "sources": [],
                    "web_sources": [],
                })
                save_message_to_session("user", "Daha önce sana hangi konularda sorular sordum?")
                st.rerun()


# ============ HISTORY PAGE ============

elif st.session_state.current_page == "history":
    st.markdown("## 📜 Geçmiş Konuşmalar")
    
    # Arama kutusu
    st.markdown("### 🔎 Tüm Konuşmalarda Ara")
    st.caption("Geçmiş konuşmalarınızda RAG ile semantik arama yapın")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        history_query = st.text_input(
            "Arama",
            placeholder="Geçmiş konuşmalarda ara...",
            label_visibility="collapsed",
            key="history_search"
        )
    
    with col2:
        search_btn = st.button("🔍 Ara", use_container_width=True, key="history_search_btn")
    
    if search_btn and history_query:
        with st.spinner("Konuşmalar taranıyor..."):
            results = session_manager.search_all_sessions(history_query, limit=20)
            
            if results:
                st.success(f"✅ {len(results)} sonuç bulundu")
                
                for i, result in enumerate(results, 1):
                    role_icon = "👤" if result["role"] == "user" else "🤖"
                    date_str = result.get("timestamp", "")[:10] if result.get("timestamp") else ""
                    
                    with st.expander(f"{role_icon} {result['session_title'][:40]}... - {date_str}"):
                        st.markdown(f"**Mesaj:**")
                        st.markdown(f"> {result['content'][:500]}...")
                        
                        col_a, col_b = st.columns([3, 1])
                        with col_b:
                            if st.button("📖 Konuşmaya Git", key=f"goto_{result['session_id']}_{i}"):
                                load_session(result["session_id"])
                                st.session_state.current_page = "chat"
                                st.rerun()
            else:
                st.warning("😔 Sonuç bulunamadı")
    
    st.markdown("---")
    
    # En çok konuşulan konular
    st.markdown("### 🏷️ Popüler Konular")
    
    try:
        topics = session_manager.get_all_topics(limit=15)
        if topics:
            tags_html = ""
            for topic, count in topics:
                tags_html += f'<span class="source-tag">{topic} ({count})</span> '
            st.markdown(tags_html, unsafe_allow_html=True)
        else:
            st.info("Henüz yeterli konuşma verisi yok")
    except:
        st.info("Konu analizi için yeterli veri yok")
    
    st.markdown("---")
    
    # Tüm konuşmalar
    st.markdown("### 📋 Tüm Konuşmalar")
    
    all_sessions = session_manager.list_sessions(limit=50)
    
    if all_sessions:
        for session_info in all_sessions:
            session_id = session_info["id"]
            title = session_info["title"]
            created = session_info["created_at"][:10] if session_info.get("created_at") else ""
            msg_count = session_info.get("message_count", 0)
            
            with st.expander(f"📁 {title} ({msg_count} mesaj) - {created}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💬 Devam Et", key=f"cont_{session_id}"):
                        load_session(session_id)
                        st.session_state.current_page = "chat"
                        st.rerun()
                
                with col2:
                    if st.button("📖 Oku", key=f"read_{session_id}"):
                        st.session_state.viewing_session_id = session_id
                
                with col3:
                    if st.button("🗑️ Sil", key=f"del_{session_id}"):
                        session_manager.delete_session(session_id)
                        st.success("Silindi!")
                        st.rerun()
                
                # Detay göster
                if st.session_state.viewing_session_id == session_id:
                    st.markdown("---")
                    session = session_manager.get_session(session_id)
                    if session:
                        for msg in session.messages:
                            icon = "👤" if msg.role == "user" else "🤖"
                            st.markdown(f"**{icon}** {msg.content[:300]}{'...' if len(msg.content) > 300 else ''}")
                            st.markdown("---")
    else:
        st.info("📭 Henüz konuşma yok")


# ============ DOCUMENTS PAGE ============

elif st.session_state.current_page == "documents":
    st.markdown("## 📁 Döküman Yönetimi")
    st.caption("RAG bilgi tabanına döküman yükleyin ve yönetin")
    
    # İstatistikler
    try:
        stats_response = api_request("GET", "/api/admin/stats")
        if stats_response and not stats_response.get("error"):
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.metric("📚 Toplam Döküman", stats_response.get("documents", {}).get("total", 0))
            with stat_col2:
                st.metric("📦 Toplam Chunk", stats_response.get("documents", {}).get("chunks", 0))
            with stat_col3:
                st.metric("💾 Toplam Boyut", f"{stats_response.get('documents', {}).get('total_size_mb', 0):.1f} MB")
    except Exception:
        pass
    
    st.markdown("---")
    
    # Upload
    st.markdown("### 📤 Döküman Yükle")
    
    uploaded_files = st.file_uploader(
        "Döküman seçin (birden fazla seçebilirsiniz)",
        type=["pdf", "docx", "doc", "txt", "md", "csv", "json", "html", "pptx", "ppt", "xlsx", "xls"],
        help="Desteklenen formatlar: PDF, Word (DOC/DOCX), PowerPoint (PPT/PPTX), Excel (XLS/XLSX), TXT, MD, CSV, JSON, HTML. Maksimum dosya boyutu: 200MB",
        key="doc_uploader",
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Seçilen dosyaları listele
        total_size = sum(f.size for f in uploaded_files)
        
        st.markdown(f"**📋 Seçilen: {len(uploaded_files)} dosya ({total_size / (1024*1024):.2f} MB)**")
        
        with st.expander("📂 Dosya Detayları", expanded=False):
            for f in uploaded_files:
                ext = Path(f.name).suffix.lower()
                if ext == ".pdf":
                    icon = "📕"
                elif ext in [".docx", ".doc"]:
                    icon = "📘"
                elif ext in [".pptx", ".ppt"]:
                    icon = "📙"
                elif ext in [".xlsx", ".xls"]:
                    icon = "📗"
                else:
                    icon = "📄"
                st.text(f"{icon} {f.name} ({f.size / 1024:.1f} KB)")
        
        if st.button(f"🚀 {len(uploaded_files)} Dosyayı Yükle ve İndeksle", type="primary", key="upload_btn", use_container_width=True):
            progress_bar = st.progress(0)
            status_container = st.empty()
            detail_container = st.empty()
            result_container = st.container()
            
            success_count = 0
            error_count = 0
            total_chunks = 0
            errors = []
            successes = []
            
            total_files = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                file_size_mb = uploaded_file.size / (1024 * 1024)
                
                with status_container:
                    st.info(f"⏳ İşleniyor: **{uploaded_file.name}** ({i+1}/{total_files})")
                
                with detail_container:
                    if file_size_mb > 5:
                        st.caption(f"📦 Büyük dosya ({file_size_mb:.1f} MB) - işlem uzun sürebilir...")
                    else:
                        st.caption(f"📦 {file_size_mb:.2f} MB")
                
                progress_bar.progress((i) / total_files, text=f"Yükleniyor... {i+1}/{total_files}")
                
                start_time = time.time()
                result = upload_document(uploaded_file)
                elapsed = time.time() - start_time
                
                if result and result.get("success"):
                    success_count += 1
                    chunks = result.get('chunks_created', 0)
                    total_chunks += chunks
                    successes.append(f"✅ {uploaded_file.name}: {chunks} parça ({elapsed:.1f}s)")
                else:
                    error_count += 1
                    error_msg = result.get('error', 'Bilinmeyen hata') if result else 'Yanıt alınamadı'
                    errors.append(f"{uploaded_file.name}: {error_msg[:100]}")
                
                progress_bar.progress((i + 1) / total_files, text=f"Tamamlandı: {i+1}/{total_files}")
            
            progress_bar.empty()
            status_container.empty()
            detail_container.empty()
            
            with result_container:
                if success_count > 0:
                    st.success(f"✅ **{success_count}/{total_files}** dosya başarıyla yüklendi! ({total_chunks} parça oluşturuldu)")
                    if success_count == total_files:
                        st.balloons()
                    with st.expander("📋 Başarılı Yüklemeler", expanded=False):
                        for s in successes:
                            st.write(s)
                
                if error_count > 0:
                    st.warning(f"⚠️ **{error_count}** dosya yüklenemedi")
                    with st.expander("❌ Hata Detayları", expanded=True):
                        for err in errors:
                            st.error(err)
                            
            st.rerun()
    
    st.markdown("---")
    
    # Döküman listesi
    st.markdown("### 📋 Yüklenen Dökümanlar")
    
    # Yenile butonu
    refresh_col1, refresh_col2 = st.columns([6, 1])
    with refresh_col2:
        if st.button("🔄", key="refresh_docs", help="Listeyi yenile"):
            st.rerun()
    
    docs = get_documents()
    
    if docs and docs.get("documents"):
        for doc in docs["documents"]:
            filename = doc.get('filename', 'Bilinmeyen')
            ext = Path(filename).suffix.lower() if filename else ""
            
            # Dosya ikonu
            if ext == ".pdf":
                icon = "📕"
            elif ext in [".docx", ".doc"]:
                icon = "📘"
            elif ext in [".pptx", ".ppt"]:
                icon = "📙"
            elif ext in [".xlsx", ".xls"]:
                icon = "📗"
            elif ext in [".txt", ".md"]:
                icon = "📄"
            else:
                icon = "📁"
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([5, 2, 2, 1])
                
                with col1:
                    st.markdown(f"{icon} **{filename}**")
                with col2:
                    size_bytes = doc.get('size', 0)
                    if size_bytes > 1024 * 1024:
                        st.caption(f"📦 {size_bytes / (1024*1024):.1f} MB")
                    else:
                        st.caption(f"📦 {size_bytes / 1024:.1f} KB")
                with col3:
                    uploaded_at = doc.get('uploaded_at', '')
                    if uploaded_at:
                        date_str = uploaded_at[:10] if len(uploaded_at) >= 10 else uploaded_at
                        st.caption(f"📅 {date_str}")
                with col4:
                    if st.button("🗑️", key=f"deldoc_{doc.get('document_id')}", help="Dökümanı sil"):
                        delete_document(doc.get("document_id"))
                        st.toast(f"✅ {filename} silindi")
                        st.rerun()
    else:
        st.info("📭 Henüz döküman yüklenmemiş. Yukarıdan dosya seçerek yükleme yapabilirsiniz.")


# ============ SEARCH PAGE - ADVANCED ============

elif st.session_state.current_page == "search":
    st.markdown("## 🔍 Gelişmiş Arama")
    st.caption("Konuşmalar, mesajlar ve dökümanlarda kapsamlı arama")
    
    # Arama sekmeleri
    search_tab1, search_tab2 = st.tabs(["💬 Konuşmalarda Ara", "📁 Dökümanlarda Ara"])
    
    with search_tab1:
        st.markdown("### 💬 Konuşma ve Mesaj Araması")
        
        # Arama kutusu ve filtreler
        search_col1, search_col2 = st.columns([3, 1])
        
        with search_col1:
            search_query = st.text_input(
                "🔎 Arama metni",
                placeholder="Aramak istediğiniz kelime veya cümle...",
                key="advanced_search_query"
            )
        
        with search_col2:
            search_in = st.multiselect(
                "Ara:",
                ["Mesajlar", "Başlıklar"],
                default=["Mesajlar", "Başlıklar"],
                key="search_in_options"
            )
        
        # Gelişmiş filtreler
        with st.expander("🎛️ Gelişmiş Filtreler", expanded=False):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                # Tarih aralığı
                st.markdown("**📅 Tarih Aralığı**")
                date_range = st.date_input(
                    "Tarih aralığı",
                    value=[],
                    key="search_date_range",
                    label_visibility="collapsed"
                )
                
                start_date = date_range[0].isoformat() if date_range and len(date_range) > 0 else None
                end_date = date_range[1].isoformat() if date_range and len(date_range) > 1 else None
            
            with filter_col2:
                # Etiketler
                st.markdown("**🏷️ Etiketler**")
                all_tags = session_manager.get_all_tags()
                selected_tags = st.multiselect(
                    "Etiket filtresi",
                    options=all_tags,
                    key="search_tags",
                    label_visibility="collapsed"
                )
            
            with filter_col3:
                # Kategori
                st.markdown("**📂 Kategori**")
                all_categories = session_manager.get_all_categories()
                selected_category = st.selectbox(
                    "Kategori",
                    options=["Tümü"] + all_categories,
                    key="search_category",
                    label_visibility="collapsed"
                )
                selected_category = None if selected_category == "Tümü" else selected_category
            
            filter_col4, filter_col5 = st.columns(2)
            
            with filter_col4:
                pinned_only = st.checkbox("📌 Sadece sabitlenmiş", key="search_pinned")
            
            with filter_col5:
                favorites_only = st.checkbox("⭐ Sadece favoriler", key="search_favorites")
        
        # Arama butonu
        if st.button("🔍 Ara", type="primary", key="advanced_search_btn", use_container_width=True):
            if search_query:
                with st.spinner("Aranıyor..."):
                    results = session_manager.advanced_search(
                        query=search_query,
                        start_date=start_date,
                        end_date=end_date,
                        tags=selected_tags if selected_tags else None,
                        category=selected_category,
                        pinned_only=pinned_only,
                        favorites_only=favorites_only
                    )
                    
                    if results:
                        st.success(f"✅ {len(results)} sonuç bulundu")
                        
                        for result in results:
                            session_info = result["session"]
                            matched_messages = result.get("matched_messages", [])
                            
                            with st.container(border=True):
                                # Başlık ve meta bilgi
                                col_title, col_meta = st.columns([3, 1])
                                
                                with col_title:
                                    pin_icon = "📌 " if session_info.get("is_pinned") else ""
                                    st.markdown(f"### {pin_icon}{session_info['title']}")
                                    
                                    # Etiketler
                                    tags = session_info.get("tags", [])
                                    if tags:
                                        st.markdown(" ".join([f"`{tag}`" for tag in tags]))
                                
                                with col_meta:
                                    st.caption(session_info.get("created_at", "")[:10])
                                    st.caption(f"💬 {session_info.get('message_count', 0)} mesaj")
                                
                                # Eşleşen mesajlar
                                if matched_messages:
                                    st.markdown("**Eşleşen mesajlar:**")
                                    for msg in matched_messages[:3]:
                                        role_icon = "👤" if msg["role"] == "user" else "🤖"
                                        content_preview = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                                        
                                        # Arama terimini vurgula
                                        highlighted = content_preview.replace(
                                            search_query,
                                            f"**{search_query}**"
                                        )
                                        st.markdown(f"{role_icon} {highlighted}")
                                
                                # Konuşmayı aç butonu
                                if st.button("💬 Konuşmaya Git", key=f"goto_{session_info['id']}"):
                                    load_session(session_info["id"])
                                    st.session_state.current_page = "chat"
                                    st.rerun()
                    else:
                        st.warning("😔 Sonuç bulunamadı. Farklı arama terimleri deneyin.")
            else:
                st.warning("⚠️ Lütfen arama metni girin")
    
    with search_tab2:
        st.markdown("### 📁 Bilgi Tabanında Arama")
        st.caption("Yüklenen dökümanlarda semantik arama yapın")
        
        kb_search_query = st.text_input("🔎 Arama sorgusu", placeholder="Ne aramak istiyorsunuz?", key="kb_search")
        
        col1, col2 = st.columns([4, 1])
        with col2:
            top_k = st.number_input("Sonuç", min_value=1, max_value=20, value=5, key="kb_topk")
        
        if st.button("🔍 Ara", type="primary", key="kb_search_btn") and kb_search_query:
            with st.spinner("Aranıyor..."):
                results = search_documents(kb_search_query, top_k)
                
                if results and results.get("results"):
                    st.markdown(f"### 📊 {results.get('total', 0)} Sonuç Bulundu")
                    
                    for i, result in enumerate(results["results"], 1):
                        with st.expander(f"📄 Sonuç {i} - Skor: {result.get('score', 0):.2f}"):
                            st.markdown(result.get("document", ""))
                            
                            metadata = result.get("metadata", {})
                            if metadata:
                                st.markdown("---")
                                st.json(metadata)
                else:
                    st.warning("😔 Sonuç bulunamadı")


# ============ FAVORITES PAGE ============

elif st.session_state.current_page == "favorites":
    st.markdown("## ⭐ Favori Mesajlar")
    st.caption("Kaydettiğiniz önemli mesajlar")
    
    # Tüm favorileri al
    favorites = session_manager.get_all_favorites()
    
    if favorites:
        st.success(f"📌 Toplam {len(favorites)} favori mesajınız var")
        
        # Filtreleme
        filter_col1, filter_col2 = st.columns([3, 1])
        with filter_col1:
            fav_search = st.text_input("🔎 Favorilerde ara", placeholder="Filtrele...", key="fav_search")
        with filter_col2:
            fav_role = st.selectbox("Rol", ["Tümü", "👤 Kullanıcı", "🤖 Asistan"], key="fav_role")
        
        # Favorileri göster
        for fav in favorites:
            session_info = fav["session"]
            message = fav["message"]
            message_index = fav["message_index"]
            
            # Filtrele
            if fav_search and fav_search.lower() not in message["content"].lower():
                continue
            if fav_role == "👤 Kullanıcı" and message["role"] != "user":
                continue
            if fav_role == "🤖 Asistan" and message["role"] != "assistant":
                continue
            
            with st.container(border=True):
                # Header
                col1, col2, col3 = st.columns([4, 2, 1])
                
                with col1:
                    role_icon = "👤" if message["role"] == "user" else "🤖"
                    st.markdown(f"### {role_icon} {message['role'].title()}")
                
                with col2:
                    st.caption(f"📂 {session_info['title'][:30]}...")
                
                with col3:
                    # Favoriden çıkar
                    if st.button("❌", key=f"unfav_{session_info['id']}_{message_index}", help="Favoriden çıkar"):
                        session_manager.toggle_message_favorite(session_info["id"], message_index)
                        st.rerun()
                
                # Mesaj içeriği
                st.markdown(message["content"])
                
                # Aksiyonlar
                action_col1, action_col2 = st.columns([1, 5])
                with action_col1:
                    if st.button("💬 Konuşmaya Git", key=f"goto_fav_{session_info['id']}_{message_index}"):
                        load_session(session_info["id"])
                        st.session_state.current_page = "chat"
                        st.rerun()
                
                st.markdown("---")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">⭐</div>
            <h3>Henüz favori mesajınız yok</h3>
            <p>Mesajları favorilere eklemek için mesajın altındaki ⭐ butonuna tıklayın.</p>
        </div>
        """, unsafe_allow_html=True)


# ============ TEMPLATES PAGE ============

elif st.session_state.current_page == "templates":
    st.markdown("## 📋 Mesaj Şablonları")
    st.caption("Sık kullandığınız mesajları şablon olarak kaydedin")
    
    # Şablon sekmeleri
    template_tab1, template_tab2 = st.tabs(["📄 Şablonlarım", "➕ Yeni Şablon"])
    
    with template_tab1:
        # Şablonları al
        templates = session_manager.get_templates()
        
        if templates:
            # Kategori filtresi
            categories = list(set([t.get("category", "Genel") for t in templates]))
            
            filter_col1, filter_col2 = st.columns([2, 3])
            with filter_col1:
                selected_cat = st.selectbox(
                    "Kategori",
                    ["Tümü"] + categories,
                    key="template_category_filter"
                )
            with filter_col2:
                template_search = st.text_input("🔎 Şablonlarda ara", key="template_search")
            
            st.markdown("---")
            
            # Şablonları göster
            for template in templates:
                # Filtrele
                if selected_cat != "Tümü" and template.get("category") != selected_cat:
                    continue
                if template_search and template_search.lower() not in template["title"].lower() and template_search.lower() not in template["content"].lower():
                    continue
                
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"### 📝 {template['title']}")
                        st.caption(f"📁 {template.get('category', 'Genel')} • 🔢 {template.get('use_count', 0)} kullanım")
                    
                    with col2:
                        if st.button("📋 Kopyala", key=f"copy_template_{template['id']}"):
                            st.session_state.template_to_use = template["content"]
                            st.session_state.current_page = "chat"
                            st.toast("✅ Şablon kopyalandı! Chat sayfasında kullanabilirsiniz.")
                            st.rerun()
                    
                    with col3:
                        if st.button("✏️ Düzenle", key=f"edit_template_{template['id']}"):
                            st.session_state.editing_template = template
                    
                    with col4:
                        if st.button("🗑️", key=f"del_template_{template['id']}", help="Sil"):
                            session_manager.delete_template(template["id"])
                            st.success("✅ Şablon silindi")
                            st.rerun()
                    
                    # İçerik önizleme
                    preview = template["content"][:200] + "..." if len(template["content"]) > 200 else template["content"]
                    st.markdown(f"```\n{preview}\n```")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <h3>Henüz şablonunuz yok</h3>
                <p>Sık kullandığınız mesajları şablon olarak kaydetmek için "Yeni Şablon" sekmesini kullanın.</p>
            </div>
            """, unsafe_allow_html=True)
    
    with template_tab2:
        st.markdown("### ➕ Yeni Şablon Oluştur")
        
        # Düzenleme modunda mı kontrol et
        editing = st.session_state.get("editing_template")
        
        with st.form("template_form"):
            template_title = st.text_input(
                "Şablon Adı",
                value=editing["title"] if editing else "",
                placeholder="Örn: Kod İnceleme İsteği"
            )
            
            template_category = st.selectbox(
                "Kategori",
                ["Genel", "Kod", "Yazı", "Analiz", "Çeviri", "Özet", "Diğer"],
                index=["Genel", "Kod", "Yazı", "Analiz", "Çeviri", "Özet", "Diğer"].index(editing.get("category", "Genel")) if editing else 0
            )
            
            template_content = st.text_area(
                "Şablon İçeriği",
                value=editing["content"] if editing else "",
                height=200,
                placeholder="Şablon metnini buraya yazın...\n\nDeğişkenler için {{değişken}} kullanabilirsiniz."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True):
                    if template_title and template_content:
                        if editing:
                            # Güncelle
                            session_manager.delete_template(editing["id"])
                        
                        session_manager.save_template(template_title, template_content, template_category)
                        st.success("✅ Şablon kaydedildi!")
                        st.session_state.editing_template = None
                        st.rerun()
                    else:
                        st.error("⚠️ Lütfen başlık ve içerik girin")
            
            with col2:
                if editing and st.form_submit_button("❌ İptal", use_container_width=True):
                    st.session_state.editing_template = None
                    st.rerun()
        
        # Örnek şablonlar
        st.markdown("---")
        st.markdown("### 💡 Örnek Şablonlar")
        
        example_templates = [
            {
                "title": "Kod İncelemesi",
                "category": "Kod",
                "content": "Lütfen aşağıdaki kodu incele ve şu kriterlere göre değerlendir:\n\n1. Kod kalitesi ve okunabilirlik\n2. Performans optimizasyonları\n3. Güvenlik açıkları\n4. Best practice önerileri\n\nKod:\n```\n{{kod}}\n```"
            },
            {
                "title": "E-posta Taslağı",
                "category": "Yazı",
                "content": "Aşağıdaki bilgilere göre profesyonel bir e-posta taslağı oluştur:\n\nKonu: {{konu}}\nAlıcı: {{alıcı}}\nTon: {{profesyonel/arkadaşça}}\nAna mesaj: {{mesaj}}"
            },
            {
                "title": "Metin Özeti",
                "category": "Özet",
                "content": "Aşağıdaki metni {{dil}} dilinde, {{uzunluk}} cümleyle özetle:\n\n{{metin}}"
            }
        ]
        
        for ex in example_templates:
            with st.expander(f"📝 {ex['title']}"):
                st.markdown(f"**Kategori:** {ex['category']}")
                st.code(ex["content"])
                if st.button(f"➕ Bu şablonu ekle", key=f"add_ex_{ex['title']}"):
                    session_manager.save_template(ex["title"], ex["content"], ex["category"])
                    st.success("✅ Şablon eklendi!")
                    st.rerun()


# ============ DASHBOARD PAGE - ENHANCED ============

elif st.session_state.current_page == "dashboard":
    st.markdown("## 📊 Dashboard")
    st.caption("Detaylı kullanım istatistikleri ve sistem metrikleri")
    
    # Backend istatistikleri
    backend_stats = get_stats()
    
    # Session manager istatistikleri
    usage_stats = session_manager.get_statistics()
    
    # Ana metrikler
    st.markdown("### 📈 Genel Bakış")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "💬 Toplam Sohbet",
            usage_stats.get("total_sessions", 0),
            help="Tüm konuşmalar"
        )
    
    with col2:
        st.metric(
            "📨 Toplam Mesaj",
            usage_stats.get("total_messages", 0),
            help="Tüm mesajlar"
        )
    
    with col3:
        st.metric(
            "📌 Sabitlenmiş",
            usage_stats.get("pinned_sessions", 0),
            help="Sabitlenmiş sohbetler"
        )
    
    with col4:
        st.metric(
            "⭐ Favoriler",
            usage_stats.get("favorite_messages", 0),
            help="Favori mesajlar"
        )
    
    with col5:
        st.metric(
            "📄 Döküman",
            backend_stats.get("documents", 0) if backend_stats else 0,
            help="Yüklenen dökümanlar"
        )
    
    st.markdown("---")
    
    # İki sütunlu detaylı görünüm
    left_col, right_col = st.columns(2)
    
    with left_col:
        # Kullanım Dağılımı
        st.markdown("### 📊 Mesaj Dağılımı")
        
        message_breakdown = usage_stats.get("message_breakdown", {})
        user_msgs = message_breakdown.get("user", 0)
        assistant_msgs = message_breakdown.get("assistant", 0)
        
        if user_msgs + assistant_msgs > 0:
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[go.Pie(
                labels=['👤 Kullanıcı', '🤖 Asistan'],
                values=[user_msgs, assistant_msgs],
                hole=.4,
                marker_colors=['#667eea', '#22c55e']
            )])
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Henüz yeterli veri yok")
        
        # Kategori dağılımı
        st.markdown("### 📂 Kategori Dağılımı")
        categories = usage_stats.get("categories", {})
        
        if categories:
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                st.progress(count / max(categories.values()), text=f"{cat}: {count}")
        else:
            st.info("Henüz kategori atanmamış")
    
    with right_col:
        # Popüler etiketler
        st.markdown("### 🏷️ Popüler Etiketler")
        tags = usage_stats.get("tags", {})
        
        if tags:
            # Tag cloud benzeri görünüm
            tag_html = ""
            for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]:
                size = min(1.5, 0.8 + count * 0.1)
                tag_html += f'<span style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 4px 12px; border-radius: 15px; margin: 3px; display: inline-block; font-size: {size}rem;">{tag} ({count})</span>'
            
            st.markdown(f'<div style="line-height: 2.5;">{tag_html}</div>', unsafe_allow_html=True)
        else:
            st.info("Henüz etiket eklenmemiş")
        
        # Şablon kullanımı
        st.markdown("### 📋 Şablon Kullanımı")
        template_usage = usage_stats.get("template_usage", {})
        
        if template_usage:
            for template_name, count in sorted(template_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
                st.markdown(f"📝 **{template_name}**: {count} kullanım")
        else:
            st.info("Henüz şablon kullanılmamış")
    
    st.markdown("---")
    
    # Sistem durumu - NON-BLOCKING
    st.markdown("### 🔧 Sistem Durumu")
    
    health = check_health_fast()  # Non-blocking!
    is_cached = health.get("cached", False) if health else True
    components = health.get("components", {}) if health else {}
    
    sys_col1, sys_col2, sys_col3, sys_col4 = st.columns(4)
    
    with sys_col1:
        st.markdown("**🤖 LLM**")
        llm_status = components.get("llm", "unknown")
        if llm_status == "healthy":
            st.success("✅ Aktif")
        elif llm_status == "unknown":
            st.info("⚪ Kontrol ediliyor...")
        else:
            st.error("❌ Sorunlu")
    
    with sys_col2:
        st.markdown("**📚 Vector Store**")
        vs_status = components.get("vector_store", "unknown")
        if vs_status == "healthy":
            doc_count = components.get('document_count', 0)
            st.success(f"✅ Aktif ({doc_count})")
        elif vs_status == "unknown":
            st.info("⚪ Kontrol ediliyor...")
        else:
            st.error("❌ Sorunlu")
    
    with sys_col3:
        st.markdown("**🌐 API**")
        api_status = components.get("api", "unknown")
        if api_status == "healthy":
            st.success("✅ Aktif")
        elif api_status == "unknown":
            st.info("⚪ Kontrol ediliyor...")
        else:
            st.error("❌ Sorunlu")
    
    with sys_col4:
        st.markdown("**💾 Depolama**")
        st.success("✅ Aktif")
    
    st.markdown("---")
    
    # Son aktiviteler
    st.markdown("### 🕐 Son Aktiviteler")
    
    recent_sessions = session_manager.list_sessions(limit=5)
    
    if recent_sessions:
        for session in recent_sessions:
            col1, col2, col3 = st.columns([4, 2, 1])
            
            with col1:
                pin_icon = "📌 " if session.get("is_pinned") else ""
                st.markdown(f"💬 {pin_icon}**{session['title'][:40]}**")
            
            with col2:
                st.caption(session.get("created_at", "")[:16].replace("T", " "))
            
            with col3:
                st.caption(f"{session.get('message_count', 0)} mesaj")
    else:
        st.info("Henüz aktivite yok")
    
    st.markdown("---")
    
    # Günlük özet (placeholder)
    st.markdown("### 📅 Günlük Özet")
    
    today_stats_col1, today_stats_col2, today_stats_col3 = st.columns(3)
    
    with today_stats_col1:
        st.metric("Bugünkü Sohbetler", "—")
    
    with today_stats_col2:
        st.metric("Bugünkü Mesajlar", "—")
    
    with today_stats_col3:
        st.metric("Ortalama Yanıt Süresi", "—")


# ============ NOTES PAGE - File Manager Style ============

elif st.session_state.current_page == "notes":
    
    # Session state for notes navigation
    if "current_folder_id" not in st.session_state:
        st.session_state.current_folder_id = None
    if "open_note_id" not in st.session_state:
        st.session_state.open_note_id = None
    if "notes_view_mode" not in st.session_state:
        st.session_state.notes_view_mode = "grid"  # grid or list
    if "show_new_folder_form" not in st.session_state:
        st.session_state.show_new_folder_form = False
    if "show_new_note_form" not in st.session_state:
        st.session_state.show_new_note_form = False
    
    # Custom CSS for file manager
    st.markdown("""
    <style>
    .folder-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 10px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #90caf9;
    }
    .folder-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
    }
    .folder-icon { font-size: 1.5rem; }
    .folder-name { font-weight: 600; color: #1565c0; }
    .folder-meta { font-size: 0.75rem; color: #666; }
    
    .note-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%);
        border-radius: 10px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #ffd54f;
    }
    .note-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
    }
    .note-item.pinned {
        background: linear-gradient(135deg, #ffe0b2 0%, #ffcc80 100%);
        border-color: #ff9800;
    }
    .note-icon { font-size: 1.5rem; }
    .note-name { font-weight: 600; color: #f57c00; }
    .note-meta { font-size: 0.75rem; color: #666; }
    
    .breadcrumb {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 0;
        font-size: 0.9rem;
        color: #666;
        flex-wrap: wrap;
    }
    .breadcrumb-item {
        color: #667eea;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
    }
    .breadcrumb-item:hover {
        background: #f0f4ff;
    }
    .breadcrumb-separator { color: #999; }
    
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #999;
    }
    .empty-state-icon { font-size: 4rem; margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)
    
    # ===== NOT AÇIK MI? =====
    if st.session_state.open_note_id:
        note = notes_manager.get_note(st.session_state.open_note_id)
        
        if note:
            # Üst bar
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("⬅️ Geri", use_container_width=True):
                    st.session_state.open_note_id = None
                    st.rerun()
            with col2:
                st.markdown(f"### 📝 {note.title}")
            
            st.markdown("---")
            
            # Not düzenleme formu
            with st.form("edit_note_form"):
                edit_title = st.text_input("Başlık", value=note.title)
                edit_content = st.text_area("İçerik", value=note.content, height=300)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    color_map = {"yellow": "🟡 Sarı", "green": "🟢 Yeşil", "blue": "🔵 Mavi", 
                                 "pink": "🩷 Pembe", "purple": "🟣 Mor", "orange": "🟠 Turuncu",
                                 "red": "🔴 Kırmızı", "gray": "⚪ Gri"}
                    color_options = list(color_map.values())
                    current_color_idx = list(color_map.keys()).index(note.color) if note.color in color_map else 0
                    edit_color = st.selectbox("Renk", color_options, index=current_color_idx)
                with col2:
                    edit_tags = st.text_input("Etiketler", value=", ".join(note.tags))
                with col3:
                    edit_pinned = st.checkbox("📌 Sabitli", value=note.pinned)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True):
                        reverse_color = {v: k for k, v in color_map.items()}
                        tags_list = [t.strip() for t in edit_tags.split(",") if t.strip()]
                        notes_manager.update_note(
                            note.id,
                            title=edit_title,
                            content=edit_content,
                            color=reverse_color.get(edit_color, "yellow"),
                            tags=tags_list,
                            pinned=edit_pinned
                        )
                        st.success("✅ Not kaydedildi!")
                        st.rerun()
                with col2:
                    if st.form_submit_button("🗑️ Sil", use_container_width=True):
                        notes_manager.delete_note(note.id)
                        st.session_state.open_note_id = None
                        st.success("Not silindi!")
                        st.rerun()
                with col3:
                    if st.form_submit_button("❌ Kapat", use_container_width=True):
                        st.session_state.open_note_id = None
                        st.rerun()
            
            # Metadata
            st.markdown("---")
            st.caption(f"Oluşturulma: {note.created_at[:16]} | Son güncelleme: {note.updated_at[:16]}")
        else:
            st.session_state.open_note_id = None
            st.rerun()
    
    else:
        # ===== DOSYA YÖNETİCİSİ GÖRÜNÜMÜ =====
        st.markdown("## 📁 Notlarım")
        
        # Breadcrumb navigasyonu
        path = notes_manager.get_folder_path(st.session_state.current_folder_id)
        
        breadcrumb_cols = st.columns([1, 6])
        with breadcrumb_cols[0]:
            if st.button("🏠 Ana", key="goto_root", help="Ana dizine git"):
                st.session_state.current_folder_id = None
                st.rerun()
        
        with breadcrumb_cols[1]:
            if path:
                breadcrumb_text = " / ".join([f"📁 {f.name}" for f in path])
                st.markdown(f"**Konum:** {breadcrumb_text}")
        
        st.markdown("---")
        
        # Üst araç çubuğu
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            search_query = st.text_input("🔍 Ara", placeholder="Not veya klasör ara...", label_visibility="collapsed", key="notes_search")
        
        with col2:
            if st.button("📁 Yeni Klasör", use_container_width=True):
                st.session_state.show_new_folder_form = True
                st.session_state.show_new_note_form = False
        
        with col3:
            if st.button("📝 Yeni Not", type="primary", use_container_width=True):
                st.session_state.show_new_note_form = True
                st.session_state.show_new_folder_form = False
        
        with col4:
            if st.session_state.current_folder_id:
                if st.button("⬆️ Üst Klasör", use_container_width=True):
                    current = notes_manager.get_folder(st.session_state.current_folder_id)
                    st.session_state.current_folder_id = current.parent_id if current else None
                    st.rerun()
        
        with col5:
            view_icon = "📋" if st.session_state.notes_view_mode == "grid" else "⊞"
            if st.button(view_icon, help="Görünümü değiştir", use_container_width=True):
                st.session_state.notes_view_mode = "list" if st.session_state.notes_view_mode == "grid" else "grid"
                st.rerun()
        
        # ===== YENİ KLASÖR FORMU =====
        if st.session_state.show_new_folder_form:
            with st.container(border=True):
                st.markdown("### 📁 Yeni Klasör Oluştur")
                col1, col2 = st.columns(2)
                with col1:
                    new_folder_name = st.text_input("Klasör adı", key="new_folder_name")
                with col2:
                    folder_icons = ["📁", "📂", "🗂️", "💼", "📚", "🎯", "💡", "⭐", "❤️", "🔒"]
                    new_folder_icon = st.selectbox("İkon", folder_icons, key="new_folder_icon")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Oluştur", type="primary", use_container_width=True, key="create_folder_btn"):
                        if new_folder_name:
                            notes_manager.create_folder(
                                name=new_folder_name,
                                parent_id=st.session_state.current_folder_id,
                                icon=new_folder_icon
                            )
                            st.session_state.show_new_folder_form = False
                            st.success(f"✅ '{new_folder_name}' klasörü oluşturuldu!")
                            st.rerun()
                with col2:
                    if st.button("❌ İptal", use_container_width=True, key="cancel_folder_btn"):
                        st.session_state.show_new_folder_form = False
                        st.rerun()
        
        # ===== YENİ NOT FORMU =====
        if st.session_state.show_new_note_form:
            with st.container(border=True):
                st.markdown("### 📝 Yeni Not Oluştur")
                new_note_title = st.text_input("Not başlığı", key="new_note_title")
                new_note_content = st.text_area("İçerik (opsiyonel)", height=100, key="new_note_content")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Oluştur", type="primary", use_container_width=True, key="create_note_btn"):
                        if new_note_title:
                            note = notes_manager.create_note(
                                title=new_note_title,
                                content=new_note_content,
                                folder_id=st.session_state.current_folder_id
                            )
                            st.session_state.show_new_note_form = False
                            st.session_state.open_note_id = note.id  # Hemen aç
                            st.success(f"✅ '{new_note_title}' notu oluşturuldu!")
                            st.rerun()
                with col2:
                    if st.button("❌ İptal", use_container_width=True, key="cancel_note_btn"):
                        st.session_state.show_new_note_form = False
                        st.rerun()
        
        st.markdown("---")
        
        # ===== KLASÖRLER VE NOTLAR =====
        folders = notes_manager.list_folders(st.session_state.current_folder_id)
        notes = notes_manager.list_notes(folder_id=st.session_state.current_folder_id, search_query=search_query if search_query else None)
        
        # Arama varsa tüm notlarda ara
        if search_query:
            all_notes = notes_manager.search_notes(search_query)
            notes = all_notes
            folders = []  # Arama modunda klasörleri gösterme
        
        if not folders and not notes:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📂</div>
                <h3>Bu klasör boş</h3>
                <p>Yeni bir klasör veya not oluşturmak için yukarıdaki butonları kullanın.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Grid veya Liste görünümü
            if st.session_state.notes_view_mode == "grid":
                cols = st.columns(3)
                col_idx = 0
                
                # Önce klasörler
                for folder in folders:
                    with cols[col_idx % 3]:
                        with st.container(border=True):
                            col_a, col_b = st.columns([4, 1])
                            with col_a:
                                if st.button(f"{folder.icon} {folder.name}", key=f"folder_{folder.id}", use_container_width=True):
                                    st.session_state.current_folder_id = folder.id
                                    st.rerun()
                            with col_b:
                                if st.button("🗑️", key=f"del_folder_{folder.id}", help="Sil"):
                                    notes_manager.delete_folder(folder.id)
                                    st.rerun()
                            
                            # Klasör içi bilgi
                            sub_count = len(notes_manager.list_folders(folder.id))
                            note_count = notes_manager.get_notes_count(folder.id)
                            st.caption(f"📁 {sub_count} klasör, 📝 {note_count} not")
                    col_idx += 1
                
                # Sonra notlar
                for note in notes:
                    with cols[col_idx % 3]:
                        with st.container(border=True):
                            pin_icon = "📌 " if note.pinned else ""
                            col_a, col_b = st.columns([4, 1])
                            with col_a:
                                if st.button(f"📝 {pin_icon}{note.title[:20]}", key=f"note_{note.id}", use_container_width=True):
                                    st.session_state.open_note_id = note.id
                                    st.rerun()
                            with col_b:
                                if st.button("🗑️", key=f"del_note_{note.id}", help="Sil"):
                                    notes_manager.delete_note(note.id)
                                    st.rerun()
                            
                            # Not önizleme
                            preview = note.content[:50] + "..." if len(note.content) > 50 else note.content
                            st.caption(preview if preview else "Boş not")
                    col_idx += 1
            
            else:  # Liste görünümü
                # Klasörler
                for folder in folders:
                    col1, col2, col3 = st.columns([5, 2, 1])
                    with col1:
                        if st.button(f"{folder.icon} {folder.name}", key=f"folder_list_{folder.id}", use_container_width=True):
                            st.session_state.current_folder_id = folder.id
                            st.rerun()
                    with col2:
                        st.caption(f"📁 {len(notes_manager.list_folders(folder.id))} | 📝 {notes_manager.get_notes_count(folder.id)}")
                    with col3:
                        if st.button("🗑️", key=f"del_folder_list_{folder.id}"):
                            notes_manager.delete_folder(folder.id)
                            st.rerun()
                
                # Notlar
                for note in notes:
                    col1, col2, col3 = st.columns([5, 2, 1])
                    with col1:
                        pin_icon = "📌 " if note.pinned else ""
                        if st.button(f"📝 {pin_icon}{note.title}", key=f"note_list_{note.id}", use_container_width=True):
                            st.session_state.open_note_id = note.id
                            st.rerun()
                    with col2:
                        st.caption(note.updated_at[:10])
                    with col3:
                        if st.button("🗑️", key=f"del_note_list_{note.id}"):
                            notes_manager.delete_note(note.id)
                            st.rerun()
        
        # İstatistikler
        st.markdown("---")
        stats = notes_manager.get_stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📝 Toplam Not", stats["total_notes"])
        with col2:
            st.metric("📁 Toplam Klasör", stats["total_folders"])
        with col3:
            st.metric("📌 Sabitli", stats["pinned_notes"])
        with col4:
            if st.button("📤 Dışa Aktar"):
                export_data = notes_manager.export_all("json")
                st.download_button(
                    "⬇️ İndir (JSON)",
                    export_data,
                    file_name=f"notlar_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )


# ============ SETTINGS PAGE ============

elif st.session_state.current_page == "settings":
    st.markdown("## ⚙️ Ayarlar")
    st.caption("Uygulama tercihlerini özelleştirin")
    
    # ============ DİL VE BÖLGE ============
    st.markdown("### 🌍 Dil ve Bölge")
    
    col_lang1, col_lang2 = st.columns([2, 3])
    with col_lang1:
        languages = {
            "tr": "🇹🇷 Türkçe",
            "en": "🇬🇧 English",
            "de": "🇩🇪 Deutsch"
        }
        selected_lang = st.selectbox(
            "Uygulama Dili",
            options=list(languages.keys()),
            format_func=lambda x: languages[x],
            index=list(languages.keys()).index(st.session_state.selected_language),
            key="language_selector"
        )
        if selected_lang != st.session_state.selected_language:
            st.session_state.selected_language = selected_lang
            st.rerun()
    
    with col_lang2:
        st.info("💡 Dil değişikliği arayüz metinlerini etkiler. AI yanıtları her zaman sorunuzun dilinde olur.")
    
    st.markdown("---")
    
    # ============ YANIT TERCİHLERİ ============
    st.markdown("### 📏 Yanıt Tercihleri")
    
    col_resp1, col_resp2 = st.columns(2)
    
    with col_resp1:
        response_lengths = {
            "short": ("🔹 Kısa", "Özet ve kısa yanıtlar"),
            "normal": ("🔸 Normal", "Dengeli ve orta uzunlukta"),
            "detailed": ("🔶 Detaylı", "Kapsamlı ve açıklayıcı")
        }
        
        st.markdown("**Varsayılan Yanıt Uzunluğu**")
        new_length = st.radio(
            "Varsayılan Yanıt Uzunluğu",
            options=list(response_lengths.keys()),
            format_func=lambda x: response_lengths[x][0],
            index=list(response_lengths.keys()).index(st.session_state.response_length),
            label_visibility="collapsed",
            horizontal=True
        )
        if new_length != st.session_state.response_length:
            st.session_state.response_length = new_length
        
        st.caption(response_lengths[new_length][1])
    
    with col_resp2:
        st.markdown("**Yanıt Stili**")
        response_styles = ["Profesyonel", "Arkadaşça", "Akademik", "Teknik"]
        selected_style = st.selectbox(
            "Yanıt Stili",
            response_styles,
            index=0,
            label_visibility="collapsed"
        )
    
    st.markdown("---")
    
    # ============ BİLDİRİMLER ============
    st.markdown("### 🔔 Bildirimler")
    
    col_notif1, col_notif2 = st.columns(2)
    
    with col_notif1:
        desktop_notifications = st.toggle(
            "🖥️ Masaüstü Bildirimleri",
            value=False,
            help="AI yanıtı tamamlandığında bildirim gönder"
        )
        if desktop_notifications:
            st.caption("Tarayıcı izni gerekli")
    
    with col_notif2:
        sound_notifications = st.toggle(
            "🔊 Sesli Bildirimler",
            value=False,
            help="Yanıt tamamlandığında ses çal"
        )
    
    st.markdown("---")
    
    st.markdown("### 🚀 Başlangıç")
    
    # Windows Startup kontrolü
    import os
    startup_path = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EnterpriseAI.lnk")
    startup_enabled = os.path.exists(startup_path)
    
    def toggle_autostart(enable: bool):
        """Windows başlangıcına ekle/çıkar"""
        try:
            if enable:
                # Startup kısayolu oluştur
                import subprocess
                vbs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "startup.vbs")
                ps_command = f'''
                $WshShell = New-Object -ComObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut("{startup_path}")
                $Shortcut.TargetPath = "{vbs_path}"
                $Shortcut.WorkingDirectory = "{os.path.dirname(vbs_path)}"
                $Shortcut.Description = "Enterprise AI Assistant"
                $Shortcut.WindowStyle = 7
                $Shortcut.Save()
                '''
                subprocess.run(["powershell", "-Command", ps_command], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                return True
            else:
                # Startup kısayolunu sil
                if os.path.exists(startup_path):
                    os.remove(startup_path)
                return True
        except Exception as e:
            st.error(f"Hata: {e}")
            return False
    
    new_startup_state = st.toggle(
        "💻 Bilgisayar açıldığında otomatik başlat",
        value=startup_enabled,
        help="Windows başladığında Enterprise AI Assistant otomatik olarak arka planda başlar ve tarayıcı açılır"
    )
    
    if new_startup_state != startup_enabled:
        if toggle_autostart(new_startup_state):
            if new_startup_state:
                st.success("✅ Otomatik başlatma etkinleştirildi! Bilgisayar açıldığında uygulama otomatik başlayacak.")
            else:
                st.info("ℹ️ Otomatik başlatma devre dışı bırakıldı.")
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🎨 Görünüm")
    
    # Tema Seçimi
    st.markdown("**🖌️ Tema Seçimi**")
    st.caption("Uygulamanın renklerini ve görünümünü özelleştirin")
    
    # Tema grid'i - 4 sütun, 2 satır
    theme_cols = st.columns(4)
    theme_keys = list(THEMES.keys())
    
    for idx, theme_id in enumerate(theme_keys):
        theme = THEMES[theme_id]
        col_idx = idx % 4
        
        with theme_cols[col_idx]:
            # Tema önizleme kartı
            is_selected = st.session_state.selected_theme == theme_id
            selected_class = "selected" if is_selected else ""
            
            st.markdown(f"""
            <div class="theme-preview {selected_class}" style="background: {theme['primary_gradient']};">
                {theme['name']}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(
                "✓ Seçili" if is_selected else "Seç",
                key=f"theme_{theme_id}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
                disabled=is_selected
            ):
                st.session_state.selected_theme = theme_id
                st.rerun()
            
            st.caption(theme['description'])
            
            # Her 4 temada bir yeni satır başlat
            if idx == 3:
                st.markdown("")
                theme_cols = st.columns(4)
    
    st.markdown("")
    st.markdown("**⚙️ Diğer Ayarlar**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.show_timestamps = st.toggle(
            "⏰ Zaman damgalarını göster",
            value=st.session_state.show_timestamps,
            help="Mesajlarda tarih/saat göster"
        )
    
    with col2:
        st.session_state.auto_scroll = st.toggle(
            "📜 Otomatik kaydır",
            value=st.session_state.auto_scroll,
            help="Yeni mesajlarda otomatik aşağı kaydır"
        )
    
    st.markdown("---")
    
    st.markdown("### ⌨️ Klavye Kısayolları")
    
    shortcuts_enabled = st.toggle(
        "Klavye kısayollarını etkinleştir",
        value=True,
        help="Hızlı işlemler için klavye kısayolları"
    )
    
    if shortcuts_enabled:
        with st.expander("📋 Kısayol Listesi", expanded=False):
            st.markdown("""
            | Kısayol | İşlem |
            |---------|-------|
            | `Ctrl + Enter` | Mesaj gönder |
            | `Ctrl + N` | Yeni sohbet |
            | `Ctrl + S` | Sohbeti kaydet |
            | `Ctrl + /` | Arama |
            | `Ctrl + D` | Detaylı mod aç/kapat |
            | `Ctrl + W` | Web araması aç/kapat |
            | `Esc` | İptal / Modal kapat |
            """)
    
    st.markdown("---")
    
    st.markdown("### 🔧 API Ayarları")
    
    current_api = st.text_input(
        "API URL",
        value=API_BASE_URL,
        help="Backend API adresi",
        disabled=True
    )
    
    st.markdown("---")
    
    st.markdown("### 🗑️ Veri Yönetimi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Tüm Konuşmaları Sil", type="secondary"):
            if st.checkbox("Emin misiniz?", key="confirm_delete_all"):
                count = session_manager.clear_all_sessions()
                create_new_session()
                st.success(f"✅ {count} konuşma silindi")
                st.rerun()
    
    with col2:
        if st.button("📤 Tüm Verileri Dışa Aktar"):
            # Export fonksiyonalitesi
            all_sessions = session_manager.list_sessions(limit=1000)
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_sessions": len(all_sessions),
                "sessions": []
            }
            for sess_info in all_sessions:
                full_session = session_manager.get_session(sess_info["id"])
                if full_session:
                    export_data["sessions"].append(full_session.to_dict())
            
            import json
            export_json = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button(
                "⬇️ JSON İndir",
                export_json,
                file_name=f"enterprise_ai_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    st.markdown("---")
    
    st.markdown("### ℹ️ Hakkında")
    st.markdown("""
    **Enterprise AI Assistant v2.0.0**
    
    Özellikler:
    - 🌐 Web Search ile güncel bilgi erişimi
    - 📚 RAG ile döküman tabanlı yanıtlar
    - 🤖 Multi-Agent sistem (Orchestrator, Research, Writer, Analyzer)
    - 📷 Görsel analiz (VLM desteği)
    - 💾 Kalıcı konuşma geçmişi
    - 🔍 Gelişmiş arama ve filtreleme
    - ⭐ Favori mesajlar
    - 📋 Mesaj şablonları
    - 🌍 Çoklu dil desteği
    - 📌 Sohbet sabitleme ve etiketleme
    - 📊 Detaylı kullanım istatistikleri
    
    Teknolojiler: FastAPI, Streamlit, Ollama, ChromaDB, LangChain
    """)


# ============ KEYBOARD SHORTCUTS MODAL ============

if st.session_state.show_keyboard_shortcuts:
    @st.dialog("⌨️ Klavye Kısayolları")
    def show_shortcuts_modal():
        st.markdown("""
        ### 💬 Sohbet
        | Kısayol | İşlem |
        |---------|-------|
        | `Ctrl + Enter` | Mesaj gönder |
        | `Ctrl + N` | Yeni sohbet başlat |
        | `Ctrl + D` | Detaylı mod aç/kapat |
        | `Ctrl + W` | Web araması aç/kapat |
        | `Esc` | Yanıt üretmeyi durdur |
        
        ### 🔍 Navigasyon
        | Kısayol | İşlem |
        |---------|-------|
        | `Ctrl + /` | Arama sayfasına git |
        | `Ctrl + H` | Geçmiş sayfasına git |
        | `Ctrl + ,` | Ayarlar sayfasına git |
        
        ### 📝 Düzenleme
        | Kısayol | İşlem |
        |---------|-------|
        | `Ctrl + C` | Seçili metni kopyala |
        | `Ctrl + A` | Tümünü seç |
        """)
        
        if st.button("Kapat", type="primary", use_container_width=True):
            st.session_state.show_keyboard_shortcuts = False
            st.rerun()
    
    show_shortcuts_modal()


# ============ LEARNING PAGE ============

elif st.session_state.current_page == "learning":
    # API functions - Connection pooling kullanarak hızlı
    _learning_session = get_http_session()  # Global HTTP session kullan
    
    def learning_api_get(endpoint: str, params: dict = None) -> dict:
        try:
            response = _learning_session.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=3)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def learning_api_post(endpoint: str, data: dict = None) -> dict:
        try:
            response = _learning_session.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=8)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def learning_api_delete(endpoint: str) -> dict:
        try:
            response = _learning_session.delete(f"{API_BASE_URL}{endpoint}", timeout=3)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def learning_api_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Generic API request helper for PUT, PATCH, etc."""
        try:
            if method.upper() == "PUT":
                response = _learning_session.put(f"{API_BASE_URL}{endpoint}", json=data, timeout=8)
            elif method.upper() == "PATCH":
                response = _learning_session.patch(f"{API_BASE_URL}{endpoint}", json=data, timeout=8)
            elif method.upper() == "POST":
                response = _learning_session.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=8)
            elif method.upper() == "DELETE":
                response = _learning_session.delete(f"{API_BASE_URL}{endpoint}", timeout=3)
            else:
                response = _learning_session.get(f"{API_BASE_URL}{endpoint}", params=data, timeout=3)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response else {"detail": str(e)}
            return {"error": str(e), **error_detail}
        except Exception as e:
            return {"error": str(e)}
    
    def learning_api_stream(endpoint: str, data: dict = None):
        """Streaming API çağrısı - SSE desteği."""
        try:
            response = _learning_session.post(
                f"{API_BASE_URL}{endpoint}",
                json=data,
                stream=True,
                timeout=300,
                headers={"Accept": "text/event-stream"}
            )
            response.raise_for_status()
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])
                            yield event_data
                        except json.JSONDecodeError:
                            yield {"type": "chunk", "content": line[6:]}
                    elif line.strip():
                        yield {"type": "chunk", "content": line}
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    # Session state for learning
    if "learning_view" not in st.session_state:
        st.session_state.learning_view = "list"  # list, workspace, generating, reading
    if "current_workspace_id" not in st.session_state:
        st.session_state.current_workspace_id = None
    if "workspace_tab" not in st.session_state:
        st.session_state.workspace_tab = 0
    # Döküman oluşturma için ek state'ler
    if "generating_document_id" not in st.session_state:
        st.session_state.generating_document_id = None
    if "pending_doc_config" not in st.session_state:
        st.session_state.pending_doc_config = None
    if "reading_document_id" not in st.session_state:
        st.session_state.reading_document_id = None
    if "generated_content" not in st.session_state:
        st.session_state.generated_content = ""
    
    # =============== DÖKÜMAN OLUŞTURMA SAYFASI ===============
    if st.session_state.learning_view == "generating":
        doc_config = st.session_state.pending_doc_config or {}
        
        # Geri butonu
        col_back, col_title = st.columns([1, 5])
        with col_back:
            if st.button("⬅️ Geri", key="back_from_gen"):
                st.session_state.learning_view = "workspace"
                st.session_state.generating_document_id = None
                st.session_state.pending_doc_config = None
                st.rerun()
        
        with col_title:
            st.markdown("## 🔄 Döküman Oluşturuluyor...")
        
        st.markdown("---")
        
        # Döküman bilgileri
        with st.container(border=True):
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.markdown(f"**📖 Başlık:** {doc_config.get('title', 'Döküman')}")
                st.markdown(f"**📌 Konu:** {doc_config.get('topic', '-')}")
            with info_col2:
                st.markdown(f"**📄 Sayfa Sayısı:** {doc_config.get('page_count', 5)}")
                st.markdown(f"**✍️ Stil:** {doc_config.get('style', 'detailed')}")
            
            # Web arama durumu
            web_mode = doc_config.get('web_search', 'auto')
            web_icon = {"off": "🔒", "auto": "🤖", "on": "🌐"}.get(web_mode, "❓")
            web_label = {"off": "Kapalı", "auto": "Otomatik", "on": "Açık"}.get(web_mode, "Bilinmiyor")
            st.markdown(f"**{web_icon} Web Araması:** {web_label}")
        
        st.markdown("---")
        
        # Thinking/Reasoning süreci gösterimi
        st.markdown("### 🧠 AI Düşünme Süreci")
        
        thinking_container = st.container()
        progress_bar = st.progress(0, text="Başlatılıyor...")
        status_text = st.empty()
        
        # Log container
        with st.expander("📋 Detaylı İşlem Logları", expanded=True):
            log_container = st.empty()
        
        # İçerik önizleme
        st.markdown("### 📝 Oluşturulan İçerik")
        content_container = st.empty()
        
        # Oluşturma işlemi
        logs = []
        full_content = ""
        document_id = st.session_state.generating_document_id
        
        try:
            if not document_id:
                # 1. Önce döküman kaydı oluştur
                logs.append(f"⏱️ [{datetime.now().strftime('%H:%M:%S')}] Döküman kaydı oluşturuluyor...")
                with log_container:
                    st.code("\n".join(logs), language="text")
                
                progress_bar.progress(5, text="Döküman kaydı oluşturuluyor...")
                
                create_result = learning_api_post(
                    f"/api/learning/workspaces/{st.session_state.current_workspace_id}/documents",
                    doc_config
                )
                
                if create_result.get("error"):
                    st.error(f"❌ Döküman oluşturulamadı: {create_result.get('error')}")
                    if st.button("🔄 Tekrar Dene"):
                        st.rerun()
                    st.stop()
                
                document_id = create_result.get("document", {}).get("id")
                st.session_state.generating_document_id = document_id
                
                logs.append(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Döküman kaydı oluşturuldu: {document_id[:8]}...")
                with log_container:
                    st.code("\n".join(logs), language="text")
            
            # 2. İçerik oluşturmayı başlat (background task)
            logs.append(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] AI içerik üretimi başlatılıyor...")
            with log_container:
                st.code("\n".join(logs), language="text")
            
            progress_bar.progress(10, text="AI düşünüyor...")
            
            # Web search modunu doc_config'den al
            web_search_mode = doc_config.get("web_search", "auto")
            
            # Backend'e üretimi başlat komutu gönder
            start_result = learning_api_post(
                f"/api/learning/documents/{document_id}/generate",
                {
                    "custom_instructions": doc_config.get("custom_instructions", ""),
                    "web_search": web_search_mode
                }
            )
            
            if start_result.get("error"):
                st.error(f"❌ Üretim başlatılamadı: {start_result.get('error')}")
                if st.button("🔄 Tekrar Dene", key="retry_start"):
                    st.rerun()
                st.stop()
            
            logs.append(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Arka plan görevi başlatıldı")
            with log_container:
                st.code("\n".join(logs), language="text")
            
            # 3. Polling ile durum takibi
            import time
            poll_count = 0
            last_log_count = 0
            
            # İptal butonu için placeholder
            cancel_col1, cancel_col2 = st.columns([3, 1])
            with cancel_col2:
                cancel_button = st.button("❌ İptal Et", key="cancel_generation", type="secondary")
            
            if cancel_button:
                cancel_result = learning_api_post(f"/api/learning/documents/{document_id}/cancel", {})
                if cancel_result.get("success"):
                    st.warning("⏸️ Üretim iptal edildi")
                    st.session_state.generating_document_id = None
                    st.session_state.learning_view = "workspace"
                    time.sleep(1)
                    st.rerun()
            
            polling_placeholder = st.empty()
            
            while True:
                poll_count += 1
                
                # Döküman durumunu kontrol et
                doc_result = learning_api_get(f"/api/learning/documents/{document_id}")
                doc_data = doc_result.get("document", {})
                
                status = doc_data.get("status", "generating")
                gen_logs = doc_data.get("generation_log", [])
                content = doc_data.get("content", "")
                
                # Yeni logları ekle
                if len(gen_logs) > last_log_count:
                    for log_entry in gen_logs[last_log_count:]:
                        logs.append(f"📋 {log_entry}")
                    last_log_count = len(gen_logs)
                    with log_container:
                        st.code("\n".join(logs[-25:]), language="text")
                
                # Progress güncelle
                dots = "." * ((poll_count % 3) + 1)
                if status == "generating":
                    progress_val = min(15 + (poll_count * 2), 85)
                    progress_bar.progress(progress_val, text=f"🧠 AI çalışıyor{dots} ({poll_count * 3}s)")
                    with status_text:
                        st.info(f"⏳ Döküman oluşturuluyor... ({len(gen_logs)} aşama tamamlandı)")
                    
                    # İçerik varsa göster
                    if content:
                        with content_container:
                            st.markdown(content[:5000] + ("..." if len(content) > 5000 else ""))
                
                elif status == "completed":
                    logs.append(f"🎉 [{datetime.now().strftime('%H:%M:%S')}] Döküman başarıyla tamamlandı!")
                    with log_container:
                        st.code("\n".join(logs), language="text")
                    
                    progress_bar.progress(100, text="Tamamlandı!")
                    with status_text:
                        st.success("✅ Döküman başarıyla oluşturuldu!")
                    
                    # İçeriği kaydet
                    st.session_state.generated_content = content
                    st.session_state.reading_document_id = document_id
                    
                    # Okuma sayfasına yönlendir
                    st.session_state.learning_view = "reading"
                    st.session_state.generating_document_id = None
                    st.session_state.pending_doc_config = None
                    time.sleep(1)
                    st.rerun()
                
                elif status == "failed":
                    error_msg = gen_logs[-1] if gen_logs else "Bilinmeyen hata"
                    logs.append(f"❌ [{datetime.now().strftime('%H:%M:%S')}] HATA: {error_msg}")
                    with log_container:
                        st.code("\n".join(logs), language="text")
                    
                    with status_text:
                        st.error(f"❌ Döküman oluşturma başarısız: {error_msg}")
                    
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        if st.button("🔄 Tekrar Dene", key="retry_failed"):
                            # Restart endpoint'ini çağır
                            restart_result = learning_api_post(f"/api/learning/documents/{document_id}/restart", {
                                "custom_instructions": doc_config.get("custom_instructions", ""),
                                "web_search": doc_config.get("web_search", "auto")
                            })
                            if restart_result.get("success"):
                                st.rerun()
                    with col_r2:
                        if st.button("⬅️ Geri Dön", key="back_failed"):
                            st.session_state.generating_document_id = None
                            st.session_state.learning_view = "workspace"
                            st.rerun()
                    break
                
                elif status == "cancelled":
                    logs.append(f"⏸️ [{datetime.now().strftime('%H:%M:%S')}] Üretim iptal edildi")
                    with log_container:
                        st.code("\n".join(logs), language="text")
                    
                    with status_text:
                        st.warning("⏸️ Döküman üretimi iptal edildi")
                    
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        if st.button("🔄 Yeniden Başlat", key="restart_cancelled"):
                            restart_result = learning_api_post(f"/api/learning/documents/{document_id}/restart", {
                                "custom_instructions": doc_config.get("custom_instructions", ""),
                                "web_search": doc_config.get("web_search", "auto")
                            })
                            if restart_result.get("success"):
                                st.rerun()
                    with col_c2:
                        if st.button("⬅️ Geri Dön", key="back_cancelled"):
                            st.session_state.generating_document_id = None
                            st.session_state.learning_view = "workspace"
                            st.rerun()
                    break
                
                # 3 saniye bekle
                time.sleep(3)
                
                # Maksimum 20 dakika bekle (400 poll)
                if poll_count > 400:
                    logs.append(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] Zaman aşımı!")
                    with log_container:
                        st.code("\n".join(logs), language="text")
                    with status_text:
                        st.warning("⏰ Döküman oluşturma çok uzun sürdü. Lütfen daha sonra kontrol edin.")
                    break
        
        except Exception as e:
            logs.append(f"💥 [{datetime.now().strftime('%H:%M:%S')}] Kritik hata: {str(e)}")
            with log_container:
                st.code("\n".join(logs), language="text")
            st.error(f"Bir hata oluştu: {str(e)}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Tekrar Dene", key="retry_error"):
                    st.session_state.generating_document_id = None
                    st.rerun()
            with col2:
                if st.button("⬅️ Geri Dön", key="back_error"):
                    st.session_state.learning_view = "workspace"
                    st.rerun()
    
    # =============== DÖKÜMAN OKUMA SAYFASI ===============
    elif st.session_state.learning_view == "reading":
        doc_id = st.session_state.reading_document_id
        
        # Döküman bilgilerini al
        doc_data = learning_api_get(f"/api/learning/documents/{doc_id}")
        doc = doc_data.get("document", {})
        
        # Header
        col_back, col_title, col_actions = st.columns([1, 4, 2])
        
        with col_back:
            if st.button("⬅️ Geri", key="back_from_read"):
                st.session_state.learning_view = "workspace"
                st.session_state.reading_document_id = None
                st.session_state.generated_content = ""
                st.rerun()
        
        with col_title:
            st.markdown(f"## 📖 {doc.get('title', 'Döküman')}")
        
        with col_actions:
            st.caption(f"📄 {doc.get('page_count', 0)} sayfa")
        
        st.markdown("---")
        
        # Döküman meta bilgileri
        with st.container(border=True):
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            with meta_col1:
                st.markdown(f"**📌 Konu:** {doc.get('topic', '-')}")
            with meta_col2:
                st.markdown(f"**✍️ Stil:** {doc.get('style', '-')}")
            with meta_col3:
                status_icon = "✅" if doc.get('status') == 'completed' else "⏳"
                st.markdown(f"**Durum:** {status_icon} {doc.get('status', '-')}")
        
        st.markdown("---")
        
        # İçerik
        content = doc.get("content") or st.session_state.generated_content or "İçerik henüz oluşturulmamış."
        
        # İçerik gösterimi - Markdown formatında
        st.markdown("### 📚 İçerik")
        
        with st.container(border=True):
            st.markdown(content)
        
        # Referanslar varsa göster
        references = doc.get("references", [])
        if references:
            st.markdown("---")
            st.markdown("### 📖 Kaynakça")
            with st.container(border=True):
                for i, ref in enumerate(references, 1):
                    if isinstance(ref, dict):
                        st.markdown(f"{i}. {ref.get('source', 'Kaynak')} - Satır {ref.get('line', '?')}")
                    else:
                        st.markdown(f"{i}. {ref}")
        
        st.markdown("---")
        
        # ====== DÖKÜMAN DÜZENLEME BÖLÜMÜ ======
        if "edit_document_mode" not in st.session_state:
            st.session_state.edit_document_mode = False
        
        if st.session_state.edit_document_mode:
            st.markdown("### ✏️ Dökümanı Düzenle")
            with st.container(border=True):
                edit_col1, edit_col2 = st.columns(2)
                with edit_col1:
                    new_title = st.text_input("📖 Başlık", value=doc.get('title', ''), key="edit_title")
                    new_topic = st.text_area("📌 Konu", value=doc.get('topic', ''), height=80, key="edit_topic")
                with edit_col2:
                    new_page_count = st.number_input("📄 Sayfa Sayısı", min_value=1, max_value=40, value=doc.get('page_count', 5), key="edit_pages")
                    style_options = ["detailed", "summary", "academic", "casual", "exam_prep"]
                    current_style = doc.get('style', 'detailed')
                    style_idx = style_options.index(current_style) if current_style in style_options else 0
                    new_style = st.selectbox("✍️ Stil", options=style_options, index=style_idx, key="edit_style")
                
                st.markdown("---")
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                with btn_col1:
                    if st.button("💾 Kaydet", use_container_width=True, type="primary", key="save_edit_btn"):
                        # Sadece değişiklikleri kaydet
                        update_data = {}
                        if new_title != doc.get('title'):
                            update_data['title'] = new_title
                        if new_topic != doc.get('topic'):
                            update_data['topic'] = new_topic
                        if new_page_count != doc.get('page_count'):
                            update_data['page_count'] = new_page_count
                        if new_style != doc.get('style'):
                            update_data['style'] = new_style
                        
                        if update_data:
                            result = learning_api_request(f"/api/learning/documents/{doc_id}", method="PUT", data=update_data)
                            if result.get("success"):
                                st.success(f"✅ {result.get('message', 'Kaydedildi')}")
                                st.session_state.edit_document_mode = False
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"❌ Hata: {result.get('detail', result.get('error', 'Bilinmeyen hata'))}")
                        else:
                            st.info("ℹ️ Değişiklik yapılmadı")
                            st.session_state.edit_document_mode = False
                            st.rerun()
                
                with btn_col2:
                    if st.button("🔄 Kaydet & Yeniden Oluştur", use_container_width=True, key="save_restart_btn"):
                        # Düzenle ve yeniden başlat
                        update_data = {
                            'title': new_title,
                            'topic': new_topic,
                            'page_count': new_page_count,
                            'style': new_style
                        }
                        result = learning_api_post(f"/api/learning/documents/{doc_id}/edit-and-restart", data=update_data)
                        if result.get("success"):
                            st.success("✅ Düzenlendi ve üretim başlatıldı!")
                            st.session_state.edit_document_mode = False
                            st.session_state.learning_view = "generating"
                            st.session_state.generating_document_id = doc_id
                            st.session_state.pending_doc_config = {
                                "title": new_title,
                                "topic": new_topic,
                                "page_count": new_page_count,
                                "style": new_style,
                                "web_search": "auto"
                            }
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"❌ Hata: {result.get('detail', result.get('error', 'Bilinmeyen hata'))}")
                
                with btn_col3:
                    if st.button("❌ İptal", use_container_width=True, key="cancel_edit_btn"):
                        st.session_state.edit_document_mode = False
                        st.rerun()
        
        # Alt aksiyonlar
        col_a1, col_a2, col_a3, col_a4, col_a5 = st.columns(5)
        with col_a1:
            # 📥 Markdown İndirme
            doc_title_safe = re.sub(r'[^\w\s-]', '', doc.get('title', 'dokuman')).strip().replace(' ', '_')
            st.download_button(
                label="📥 Markdown İndir",
                data=content,
                file_name=f"{doc_title_safe}.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_md_btn"
            )
        
        with col_a2:
            # 📄 TXT İndirme
            txt_content = content.replace('## ', '\n\n=== ').replace('### ', '\n--- ').replace('**', '').replace('*', '')
            st.download_button(
                label="📄 TXT İndir",
                data=txt_content,
                file_name=f"{doc_title_safe}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_txt_btn"
            )
        
        with col_a3:
            if st.button("✏️ Düzenle", use_container_width=True, key="edit_doc_btn"):
                st.session_state.edit_document_mode = True
                st.rerun()
        
        with col_a4:
            if st.button("🔄 Yeniden Oluştur", use_container_width=True, key="regenerate_btn"):
                # Restart endpoint'ini çağır
                result = learning_api_post(f"/api/learning/documents/{doc_id}/restart", data={})
                if result.get("success"):
                    st.session_state.learning_view = "generating"
                    st.session_state.generating_document_id = doc_id
                    st.session_state.pending_doc_config = {
                        "title": doc.get("title", "Döküman"),
                        "topic": doc.get("topic", ""),
                        "page_count": doc.get("page_count", 5),
                        "style": doc.get("style", "detailed"),
                        "custom_instructions": "",
                        "web_search": "auto"
                    }
                    st.rerun()
                else:
                    st.error(f"Hata: {result.get('message', 'Bilinmeyen hata')}")
        
        with col_a5:
            if st.button("🗑️ Sil", use_container_width=True, type="secondary", key="delete_doc_btn"):
                st.session_state.confirm_delete_doc = True
                st.rerun()
        
        # Silme onayı
        if st.session_state.get("confirm_delete_doc", False):
            st.warning("⚠️ Bu dökümanı silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.")
            del_col1, del_col2 = st.columns(2)
            with del_col1:
                if st.button("✅ Evet, Sil", use_container_width=True, type="primary", key="confirm_del_yes"):
                    result = learning_api_delete(f"/api/learning/documents/{doc_id}")
                    if result.get("success"):
                        st.success("✅ Döküman silindi!")
                        st.session_state.confirm_delete_doc = False
                        st.session_state.learning_view = "workspace"
                        st.session_state.reading_document_id = None
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ Hata: {result.get('error', 'Silinemedi')}")
            with del_col2:
                if st.button("❌ İptal", use_container_width=True, key="confirm_del_no"):
                    st.session_state.confirm_delete_doc = False
                    st.rerun()
    
    # =============== WORKSPACE LİSTE GÖRÜNÜMÜ ===============
    elif st.session_state.learning_view == "list":
        st.markdown("## 📚 AI ile Öğren")
        st.markdown("*Kişiselleştirilmiş öğrenme platformu - Çalışma dökümanları, testler ve AI destekli öğrenme*")
        st.markdown("---")
        
        # Ana sekmeler
        main_tabs = st.tabs(["🏠 Çalışma Ortamlarım", "➕ Yeni Oluştur"])
        
        with main_tabs[0]:
            # Workspace listesi
            data = learning_api_get("/api/learning/workspaces")
            
            if "error" in data:
                st.warning(f"⚠️ Backend bağlantısı kurulamadı. Learning API henüz hazır olmayabilir.")
                st.info("💡 Bu özellik için backend'in çalışıyor olması gerekir.")
            else:
                workspaces = data.get("workspaces", [])
                
                if not workspaces:
                    st.info("📭 Henüz çalışma ortamı yok. Yeni bir tane oluşturun!")
                else:
                    # Grid görünümü
                    cols = st.columns(3)
                    for idx, ws in enumerate(workspaces):
                        with cols[idx % 3]:
                            with st.container(border=True):
                                st.markdown(f"### 📖 {ws.get('name', 'İsimsiz')}")
                                
                                if ws.get('topic'):
                                    st.caption(f"📌 {ws.get('topic')}")
                                
                                if ws.get('description'):
                                    desc = ws.get('description', '')
                                    st.markdown(f"_{desc[:100]}..._" if len(desc) > 100 else f"_{desc}_")
                                
                                # İstatistikler
                                doc_count = len(ws.get('documents', []))
                                test_count = len(ws.get('tests', []))
                                chat_count = len(ws.get('chat_history', []))
                                st.caption(f"📄 {doc_count} döküman • 📝 {test_count} test • 💬 {chat_count} mesaj")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("🚀 Aç", key=f"open_ws_{ws.get('id')}", use_container_width=True):
                                        st.session_state.current_workspace_id = ws.get('id')
                                        st.session_state.learning_view = "workspace"
                                        st.session_state.workspace_tab = 0
                                        st.rerun()
                                with col2:
                                    if st.button("🗑️", key=f"del_ws_{ws.get('id')}", use_container_width=True):
                                        learning_api_delete(f"/api/learning/workspaces/{ws.get('id')}")
                                        st.rerun()
        
        with main_tabs[1]:
            # Yeni çalışma ortamı oluştur
            st.markdown("### ➕ Yeni Çalışma Ortamı")
            
            with st.form("create_workspace_form"):
                name = st.text_input("📝 Çalışma Ortamı Adı *", placeholder="Örn: Makine Öğrenmesi Çalışması")
                topic = st.text_input("📌 Konu", placeholder="Örn: Supervised Learning, Neural Networks")
                description = st.text_area("📄 Açıklama", placeholder="Bu çalışma ortamının amacı...")
                
                submitted = st.form_submit_button("✅ Oluştur", type="primary", use_container_width=True)
                
                if submitted:
                    if not name:
                        st.error("Lütfen bir isim girin!")
                    else:
                        result = learning_api_post("/api/learning/workspaces", {
                            "name": name,
                            "topic": topic,
                            "description": description
                        })
                        
                        if result.get("success"):
                            st.toast("✅ Çalışma ortamı oluşturuldu!")
                            st.session_state.current_workspace_id = result.get("workspace", {}).get("id")
                            st.session_state.learning_view = "workspace"
                            st.rerun()
                        else:
                            st.error(f"Hata: {result.get('error', 'Bilinmeyen hata')}")
    
    # =============== WORKSPACE DETAY GÖRÜNÜMÜ (AYRI ARAYÜZ) ===============
    elif st.session_state.learning_view == "workspace" and st.session_state.current_workspace_id:
        ws_data = learning_api_get(f"/api/learning/workspaces/{st.session_state.current_workspace_id}")
        
        if "error" in ws_data or not ws_data.get("workspace"):
            st.error("Çalışma ortamı bulunamadı!")
            if st.button("⬅️ Geri Dön"):
                st.session_state.learning_view = "list"
                st.session_state.current_workspace_id = None
                st.rerun()
        else:
            workspace = ws_data["workspace"]
            
            # Üst bar - Workspace başlığı ve geri butonu
            header_col1, header_col2 = st.columns([5, 1])
            with header_col1:
                st.markdown(f"## 📖 {workspace.get('name', 'Çalışma Ortamı')}")
                if workspace.get('topic'):
                    st.caption(f"📌 Konu: {workspace.get('topic')}")
            with header_col2:
                if st.button("⬅️ Geri", use_container_width=True, type="secondary"):
                    st.session_state.learning_view = "list"
                    st.session_state.current_workspace_id = None
                    st.rerun()
            
            st.markdown("---")
            
            # Ana sekmeler - Çalışma Ortamı İçeriği
            ws_tabs = st.tabs(["📚 Kaynaklar", "📄 Dökümanlar", "📝 Testler", "💬 Chat"])
            
            # ===== KAYNAKLAR SEKMESİ =====
            with ws_tabs[0]:
                st.markdown("### 📚 Kaynak Yönetimi")
                st.info("RAG sistemindeki dökümanları bu çalışma ortamı için aktif/deaktif edebilirsiniz.")
                
                # Tüm yüklü dökümanları getir
                sources_data = learning_api_get(f"/api/learning/workspaces/{st.session_state.current_workspace_id}/sources")
                
                if "error" in sources_data:
                    st.warning("Kaynaklar yüklenirken hata oluştu.")
                else:
                    sources = sources_data.get("sources", [])
                    active_count = sources_data.get("active_count", 0)
                    
                    # İstatistik
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("📁 Toplam Kaynak", len(sources))
                    with col_stat2:
                        st.metric("✅ Aktif Kaynak", active_count)
                    with col_stat3:
                        st.metric("❌ Deaktif Kaynak", len(sources) - active_count)
                    
                    st.markdown("---")
                    
                    if not sources:
                        st.caption("Henüz kaynak yüklenmemiş. Dökümanlar sayfasından dosya yükleyebilirsiniz.")
                    else:
                        # Toplu işlem butonları
                        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
                        with btn_col1:
                            if st.button("✅ Tümünü Aktif Yap", use_container_width=True, key="bulk_activate_btn"):
                                result = learning_api_post(
                                    f"/api/learning/workspaces/{st.session_state.current_workspace_id}/sources/bulk-toggle",
                                    {"active": True}
                                )
                                if result.get('success'):
                                    st.toast(f"✅ {result.get('toggled_count', 0)} kaynak aktif edildi")
                                st.rerun()
                        with btn_col2:
                            if st.button("❌ Tümünü Deaktif Yap", use_container_width=True, key="bulk_deactivate_btn"):
                                result = learning_api_post(
                                    f"/api/learning/workspaces/{st.session_state.current_workspace_id}/sources/bulk-toggle",
                                    {"active": False}
                                )
                                if result.get('success'):
                                    st.toast(f"❌ {result.get('toggled_count', 0)} kaynak deaktif edildi")
                                st.rerun()
                        
                        st.markdown("#### 📄 Yüklenen Dökümanlar")
                        
                        # Kaynak listesi
                        for source in sources:
                            with st.container(border=True):
                                src_col1, src_col2, src_col3 = st.columns([4, 1, 1])
                                
                                with src_col1:
                                    # Dosya ikonu
                                    file_type = source.get('type', 'FILE').upper()
                                    if file_type == 'PDF':
                                        icon = "📕"
                                    elif file_type in ['DOCX', 'DOC']:
                                        icon = "📘"
                                    elif file_type in ['PPTX', 'PPT']:
                                        icon = "📙"
                                    elif file_type in ['XLSX', 'XLS']:
                                        icon = "📗"
                                    elif file_type == 'TXT':
                                        icon = "📄"
                                    else:
                                        icon = "📁"
                                    
                                    st.markdown(f"{icon} **{source.get('name', 'Kaynak')}**")
                                    
                                    # Dosya boyutu
                                    size_bytes = source.get('size', 0)
                                    if size_bytes > 1024 * 1024:
                                        size_str = f"{size_bytes / (1024*1024):.1f} MB"
                                    else:
                                        size_str = f"{size_bytes / 1024:.1f} KB"
                                    
                                    st.caption(f"📏 {size_str}")
                                
                                with src_col2:
                                    st.caption(file_type)
                                
                                with src_col3:
                                    is_active = source.get('active', False)
                                    new_state = st.toggle(
                                        "Aktif" if is_active else "Deaktif",
                                        value=is_active,
                                        key=f"src_toggle_{source.get('id')}"
                                    )
                                    if new_state != is_active:
                                        learning_api_post(
                                            f"/api/learning/workspaces/{st.session_state.current_workspace_id}/sources/toggle",
                                            {"source_id": source.get('id'), "active": new_state}
                                        )
                                        st.rerun()
            
            # ===== DÖKÜMANLAR SEKMESİ =====
            with ws_tabs[1]:
                st.markdown("### 📄 Çalışma Dökümanları")
                st.caption("AI tarafından oluşturulan çalışma dökümanları")
                
                with st.expander("➕ Yeni Döküman Oluştur", expanded=True):
                    doc_title = st.text_input("Başlık *", placeholder="Örn: ML Temelleri", key="doc_title_ws")
                    doc_topic = st.text_input("Konu *", placeholder="Örn: Supervised Learning", key="doc_topic_ws")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        doc_pages = st.slider("Sayfa Sayısı", 1, 40, 5, key="doc_pages_ws")
                    with col2:
                        doc_style = st.selectbox(
                            "Yazım Stili",
                            ["detailed", "academic", "casual", "summary", "exam_prep"],
                            format_func=lambda x: {
                                "detailed": "📖 Detaylı",
                                "academic": "🎓 Akademik",
                                "casual": "💬 Günlük",
                                "summary": "📋 Özet",
                                "exam_prep": "📝 Sınav Hazırlık"
                            }.get(x, x),
                            key="doc_style_ws"
                        )
                    
                    # 🌐 Web Arama Seçeneği
                    st.markdown("---")
                    st.markdown("**🌐 Web Araması**")
                    web_search_option = st.radio(
                        "Web'den ek bilgi al",
                        ["off", "auto", "on"],
                        format_func=lambda x: {
                            "off": "🔒 Kapalı - Sadece yüklü kaynaklardan",
                            "auto": "🤖 Otomatik - AI karar versin",
                            "on": "🌐 Açık - Web'i de tara"
                        }.get(x, x),
                        horizontal=True,
                        index=1,  # Default: auto
                        key="doc_web_search_ws"
                    )
                    if web_search_option == "auto":
                        st.caption("💡 AI, yüklü kaynaklarda yeterli bilgi bulamazsa web'de arama yapar.")
                    elif web_search_option == "on":
                        st.caption("🌐 Hem yüklü kaynaklar hem de web kaynakları kullanılacak.")
                    else:
                        st.caption("🔒 Sadece yüklediğiniz dökümanlardan bilgi alınacak.")
                    
                    st.markdown("---")
                    
                    doc_instructions = st.text_area(
                        "Özel Talimatlar",
                        placeholder="Örn: Kod örnekleri ekle, tablolarla açıkla...",
                        key="doc_instructions_ws"
                    )
                    
                    if st.button("🚀 Dökümanı Oluştur", type="primary", use_container_width=True, key="create_doc_btn_ws"):
                        if doc_title and doc_topic:
                            # Döküman konfigürasyonunu kaydet ve oluşturma sayfasına yönlendir
                            st.session_state.pending_doc_config = {
                                "title": doc_title,
                                "topic": doc_topic,
                                "page_count": doc_pages,
                                "style": doc_style,
                                "custom_instructions": doc_instructions,
                                "web_search": web_search_option  # off, auto, on
                            }
                            st.session_state.generating_document_id = None
                            st.session_state.learning_view = "generating"
                            st.rerun()
                        else:
                            st.warning("⚠️ Başlık ve konu gereklidir!")
                
                st.markdown("---")
                
                # Mevcut dökümanlar
                st.markdown("#### 📚 Oluşturulan Dökümanlar")
                documents = ws_data.get("documents", [])
                if documents:
                    for doc in documents:
                        with st.container(border=True):
                            doc_col1, doc_col2, doc_col3 = st.columns([4, 1, 1])
                            with doc_col1:
                                status_icon = "✅" if doc.get('status') == 'completed' else "⏳"
                                st.markdown(f"{status_icon} **{doc.get('title', 'Döküman')}**")
                                st.caption(f"📄 {doc.get('page_count', 0)} sayfa • {doc.get('style', 'N/A')} • {doc.get('topic', '')}")
                            with doc_col2:
                                if doc.get('status') == 'completed':
                                    if st.button("👁️ Oku", key=f"view_doc_{doc.get('id')}", use_container_width=True):
                                        # Okuma sayfasına yönlendir
                                        st.session_state.reading_document_id = doc.get('id')
                                        st.session_state.learning_view = "reading"
                                        st.rerun()
                                else:
                                    if st.button("🚀 Oluştur", key=f"gen_doc_{doc.get('id')}", use_container_width=True):
                                        # Oluşturma sayfasına yönlendir
                                        st.session_state.pending_doc_config = {
                                            "title": doc.get("title", "Döküman"),
                                            "topic": doc.get("topic", ""),
                                            "page_count": doc.get("page_count", 5),
                                            "style": doc.get("style", "detailed"),
                                            "custom_instructions": ""
                                        }
                                        st.session_state.generating_document_id = doc.get('id')
                                        st.session_state.learning_view = "generating"
                                        st.rerun()
                            with doc_col3:
                                if st.button("🗑️", key=f"del_doc_{doc.get('id')}", help="Dökümanı sil"):
                                    learning_api_delete(f"/api/learning/documents/{doc.get('id')}")
                                    st.rerun()
                else:
                    st.info("📭 Henüz döküman oluşturulmamış. Yukarıdan yeni bir tane oluşturun!")
            
            # ===== TESTLER SEKMESİ =====
            with ws_tabs[2]:
                st.markdown("### 📝 Testler")
                st.caption("Öğrenmenizi test edin ve pekiştirin")
                
                with st.expander("➕ Yeni Test Oluştur", expanded=False):
                    test_title = st.text_input("Test Başlığı *", placeholder="Örn: ML Quiz 1", key="test_title_ws")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        test_count = st.slider("Soru Sayısı", 5, 50, 10, key="test_count_ws")
                        test_type = st.selectbox(
                            "Soru Türü",
                            ["mixed", "multiple_choice", "true_false", "fill_blank", "short_answer"],
                            format_func=lambda x: {
                                "mixed": "🎲 Karışık",
                                "multiple_choice": "📋 Çoktan Seçmeli",
                                "true_false": "✅ Doğru/Yanlış",
                                "fill_blank": "📝 Boşluk Doldurma",
                                "short_answer": "💬 Kısa Cevap"
                            }.get(x, x),
                            key="test_type_ws"
                        )
                    with col2:
                        test_difficulty = st.selectbox(
                            "Zorluk",
                            ["mixed", "easy", "medium", "hard"],
                            format_func=lambda x: {
                                "mixed": "🎲 Karışık",
                                "easy": "🟢 Kolay",
                                "medium": "🟡 Orta",
                                "hard": "🔴 Zor"
                            }.get(x, x),
                            key="test_difficulty_ws"
                        )
                    
                    if st.button("🚀 Testi Oluştur", type="primary", use_container_width=True, key="create_test_btn_ws"):
                        if test_title:
                            with st.spinner("Test oluşturuluyor..."):
                                result = learning_api_post(
                                    f"/api/learning/workspaces/{st.session_state.current_workspace_id}/tests",
                                    {
                                        "title": test_title,
                                        "test_type": test_type,
                                        "question_count": test_count,
                                        "difficulty": test_difficulty
                                    }
                                )
                                if result.get("success"):
                                    st.toast("✅ Test oluşturuldu!")
                                    st.rerun()
                                else:
                                    st.error(f"Hata: {result.get('error', 'Bilinmeyen hata')}")
                        else:
                            st.warning("Test başlığı gereklidir!")
                
                st.markdown("---")
                
                # Mevcut testler
                tests = ws_data.get("tests", [])
                if tests:
                    for test in tests:
                        with st.container(border=True):
                            test_col1, test_col2, test_col3 = st.columns([3, 1, 1])
                            
                            with test_col1:
                                status = test.get("status", "pending")
                                if status == "completed":
                                    status_icon = "✅"
                                elif status == "in_progress":
                                    status_icon = "⏳"
                                else:
                                    status_icon = "📝"
                                
                                st.markdown(f"{status_icon} **{test.get('title', 'Test')}**")
                                st.caption(f"📋 {test.get('question_count', 0)} soru • {test.get('difficulty', 'N/A')}")
                            
                            with test_col2:
                                if status == "completed":
                                    score = test.get('score', 0)
                                    if score >= 80:
                                        st.success(f"🏆 %{score:.0f}")
                                    elif score >= 60:
                                        st.warning(f"📊 %{score:.0f}")
                                    else:
                                        st.error(f"📉 %{score:.0f}")
                            
                            with test_col3:
                                if status == "pending":
                                    if st.button("🚀 Başlat", key=f"start_test_{test.get('id')}", use_container_width=True):
                                        st.info("Test başlatılıyor...")
                                elif status == "in_progress":
                                    if st.button("📝 Devam", key=f"cont_test_{test.get('id')}", use_container_width=True):
                                        st.info("Teste devam ediliyor...")
                                else:
                                    if st.button("👁️ Görüntüle", key=f"view_test_{test.get('id')}", use_container_width=True):
                                        st.info("Test sonuçları gösteriliyor...")
                else:
                    st.info("📭 Henüz test oluşturulmamış. Yukarıdan yeni bir tane oluşturun!")
            
            # ===== CHAT SEKMESİ =====
            with ws_tabs[3]:
                st.markdown("### 💬 Çalışma Asistanı")
                
                # Aktif kaynak sayısını göster
                active_sources = workspace.get("active_sources", [])
                if active_sources:
                    st.success(f"✅ {len(active_sources)} aktif kaynak ile çalışıyor")
                else:
                    st.warning("⚠️ Aktif kaynak yok. Kaynaklar sekmesinden kaynak ekleyin.")
                
                st.caption("Bu çalışma ortamının aktif kaynaklarına dayalı sorular sorun.")
                
                st.markdown("---")
                
                # Chat geçmişi container
                chat_container = st.container(height=400)
                
                with chat_container:
                    chat_history = workspace.get("chat_history", [])
                    
                    if not chat_history:
                        st.info("💬 Henüz mesaj yok. Aşağıdan bir soru sorarak başlayın!")
                    else:
                        for msg in chat_history:
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            sources_used = msg.get("sources", [])
                            
                            with st.chat_message(role):
                                st.markdown(content)
                                if sources_used and role == "assistant":
                                    st.caption(f"📚 Kaynaklar: {', '.join(sources_used)}")
                
                # Chat input
                user_input = st.chat_input("Sorunuzu yazın...", key="learning_chat_input_ws")
                
                if user_input:
                    with st.spinner("Yanıt hazırlanıyor..."):
                        result = learning_api_post(
                            f"/api/learning/workspaces/{st.session_state.current_workspace_id}/chat",
                            {"message": user_input}
                        )
                        if result.get("success"):
                            st.rerun()
                        else:
                            st.error(f"Hata: {result.get('error', 'Bilinmeyen hata')}")


# ============ FOOTER ============

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888; font-size: 0.8rem; padding: 1rem;">
        Enterprise AI Assistant v2.0.0 | 🌐 Web Search • 📚 RAG • 🤖 Multi-Agent • 📚 AI ile Öğren | Endüstri Standartlarında AI
    </div>
    """,
    unsafe_allow_html=True,
)
