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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.session_manager import session_manager

# ============ CONFIGURATION ============

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ CUSTOM CSS - Modern Professional Design ============

st.markdown("""
<style>
    /* ===== GENEL STILLER ===== */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    
    /* ===== CHAT MESAJLARI ===== */
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
    }
    .user-message-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.8rem 0;
        margin-left: 15%;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
    }
    .assistant-message-box {
        background: #f8f9fa;
        color: #333;
        padding: 1rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.8rem 0;
        margin-right: 10%;
        border: 1px solid #e9ecef;
    }
    
    /* ===== KAYNAKLAR KUTUSU ===== */
    .sources-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border: 1px solid #dde1e6;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.8rem 0;
        margin-right: 10%;
    }
    .sources-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.8rem;
        font-size: 0.9rem;
    }
    .source-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 0.6rem;
        background: white;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid #e9ecef;
        transition: all 0.2s ease;
    }
    .source-item:hover {
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
    }
    .source-number {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        width: 22px;
        height: 22px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 600;
        flex-shrink: 0;
    }
    .source-content {
        flex: 1;
        min-width: 0;
    }
    .source-title {
        font-weight: 600;
        color: #333;
        font-size: 0.85rem;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .source-url {
        font-size: 0.75rem;
        color: #667eea;
        text-decoration: none;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
    }
    .source-url:hover {
        text-decoration: underline;
    }
    .source-snippet {
        font-size: 0.8rem;
        color: #666;
        margin-top: 4px;
        line-height: 1.4;
    }
    
    /* ===== WEB SEARCH INFO ===== */
    .web-search-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .web-search-inactive {
        background: #f1f3f4;
        color: #5f6368;
    }
    
    /* ===== SIDEBAR ===== */
    .sidebar-session {
        padding: 0.7rem 1rem;
        border-radius: 10px;
        margin: 0.3rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    .sidebar-session:hover {
        background: #f0f2f5;
    }
    .sidebar-session-active {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-color: #667eea30;
    }
    
    /* ===== STATUS INDICATORS ===== */
    .status-searching {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #667eea;
        font-size: 0.9rem;
        padding: 0.5rem;
        background: #f0f4ff;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* ===== MOD SEÇİCİ KUTUSU ===== */
    .mode-selector-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 0.8rem 1.2rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .mode-selector-box.web-active {
        background: linear-gradient(135deg, #e8f4fd 0%, #d0e8f9 100%);
        border-color: #667eea40;
    }
    .mode-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        color: #495057;
    }
    .mode-indicator.active {
        color: #667eea;
        font-weight: 500;
    }
    .mode-icon {
        font-size: 1.1rem;
    }
    
    /* ===== METRIC CARDS ===== */
    .metric-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* ===== TAG STYLE ===== */
    .source-tag {
        display: inline-block;
        background-color: #e8f5e9;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)


# ============ SESSION STATE INITIALIZATION ============

def init_session_state():
    """Session state'i başlat."""
    if "session_id" not in st.session_state:
        new_session = session_manager.create_session()
        st.session_state.session_id = new_session.id

    if "messages" not in st.session_state:
        existing_session = session_manager.get_session(st.session_state.session_id)
        if existing_session:
            st.session_state.messages = [
                {
                    "role": m.role,
                    "content": m.content,
                    "sources": m.sources if hasattr(m, 'sources') else [],
                    "web_sources": [],
                }
                for m in existing_session.messages
            ]
        else:
            st.session_state.messages = []

    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"
    
    if "web_search_enabled" not in st.session_state:
        st.session_state.web_search_enabled = False
    
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

init_session_state()


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
    """Session'ı yükle."""
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
        return True
    return False


def create_new_session():
    """Yeni session oluştur."""
    new_session = session_manager.create_session()
    st.session_state.session_id = new_session.id
    st.session_state.messages = []
    st.session_state.web_search_enabled = False


def api_request(method: str, endpoint: str, **kwargs):
    """API isteği yap."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, timeout=120, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ API'ye bağlanılamadı. Backend'in çalıştığından emin olun.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ İstek zaman aşımına uğradı.")
        return None
    except Exception as e:
        st.error(f"❌ Hata: {str(e)}")
        return None


def check_health():
    """Sistem sağlık kontrolü."""
    return api_request("GET", "/health")


def stream_chat_message(message: str, use_web_search: bool = False):
    """Streaming chat mesajı gönder."""
    endpoint = "/api/chat/web-stream" if use_web_search else "/api/chat/stream"
    
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "web_search": use_web_search,
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
            yield {"type": "error", "message": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        yield {"type": "error", "message": str(e)}


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
    """Döküman yükle."""
    file_type = file.type
    if not file_type:
        ext = Path(file.name).suffix.lower()
        type_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".csv": "text/csv",
            ".json": "application/json",
            ".html": "text/html",
        }
        file_type = type_map.get(ext, "application/octet-stream")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": (file.name, file, file_type)},
            timeout=300,
        )
        response.raise_for_status()
        return response.json()
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


def render_sources_box(sources: list):
    """Kaynaklar kutusunu render et - Perplexity tarzı."""
    if not sources:
        return
    
    sources_html = f"""
    <div class="sources-container">
        <div class="sources-header">
            <span>📚</span>
            <span>Kaynaklar</span>
            <span style="color: #888; font-weight: normal; font-size: 0.8rem;">({len(sources)} kaynak bulundu)</span>
        </div>
    """
    
    for i, source in enumerate(sources, 1):
        if isinstance(source, dict):
            title = source.get('title', f'Kaynak {i}')[:60]
            url = source.get('url', '#')
            snippet = source.get('snippet', '')[:180]
        else:
            title = f"Kaynak {i}"
            url = str(source)
            snippet = ""
        
        # URL'yi güvenli göster
        display_url = url[:60] + "..." if len(url) > 60 else url
        
        sources_html += f"""
        <div class="source-item">
            <div class="source-number">{i}</div>
            <div class="source-content">
                <div class="source-title">{title}</div>
                <a href="{url}" target="_blank" class="source-url" rel="noopener noreferrer">{display_url}</a>
                {f'<div class="source-snippet">{snippet}...</div>' if snippet else ''}
            </div>
        </div>
        """
    
    sources_html += "</div>"
    st.markdown(sources_html, unsafe_allow_html=True)


# ============ SIDEBAR ============

with st.sidebar:
    st.markdown("## 🤖 Enterprise AI")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "📍 Navigasyon",
        ["💬 Chat", "📜 Geçmiş", "📁 Dökümanlar", "🔍 Arama", "📊 Dashboard", "⚙️ Ayarlar"],
        label_visibility="collapsed",
    )
    
    page_map = {
        "💬 Chat": "chat",
        "📜 Geçmiş": "history",
        "📁 Dökümanlar": "documents",
        "🔍 Arama": "search",
        "📊 Dashboard": "dashboard",
        "⚙️ Ayarlar": "settings",
    }
    st.session_state.current_page = page_map.get(page, "chat")
    
    st.markdown("---")
    
    # ============ SESSION MANAGEMENT ============
    st.markdown("### 📂 Konuşmalar")
    
    if st.button("➕ Yeni Konuşma", use_container_width=True, type="primary"):
        create_new_session()
        st.rerun()
    
    st.markdown("")
    
    # Son konuşmalar
    recent_sessions = session_manager.list_sessions(limit=10)
    
    for session_info in recent_sessions:
        session_id = session_info["id"]
        title = session_info["title"][:25] + "..." if len(session_info["title"]) > 25 else session_info["title"]
        msg_count = session_info.get("message_count", 0)
        is_current = session_id == st.session_state.session_id
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            if is_current:
                st.markdown(f"🟢 **{title}**")
            else:
                if st.button(f"💬 {title}", key=f"s_{session_id}", use_container_width=True):
                    load_session(session_id)
                    st.rerun()
        
        with col2:
            st.caption(f"{msg_count}")
    
    st.markdown("---")
    
    # Health Status
    st.markdown("### 🔧 Sistem")
    health = check_health()
    
    if health:
        status = health.get("status", "unknown")
        if status == "healthy":
            st.success("✅ Aktif")
        else:
            st.warning(f"⚠️ {status}")
        
        components = health.get("components", {})
        cols = st.columns(2)
        with cols[0]:
            llm_ok = components.get("llm") == "healthy"
            st.markdown(f"{'🟢' if llm_ok else '🔴'} LLM")
        with cols[1]:
            vs_ok = components.get("vector_store") == "healthy"
            st.markdown(f"{'🟢' if vs_ok else '🔴'} VectorDB")
    else:
        st.error("🔴 Bağlantı yok")
    
    st.markdown("---")
    st.caption(f"Session: {st.session_state.session_id[:8]}...")
    st.caption(f"Mesaj: {len(st.session_state.messages)}")
    
    if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
        session_manager.delete_session(st.session_state.session_id)
        create_new_session()
        st.rerun()


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
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])
                    
                    # Web kaynakları varsa göster
                    web_sources = msg.get("web_sources", [])
                    if web_sources:
                        render_sources_box(web_sources)
                    
                    # Normal kaynaklar
                    sources = msg.get("sources", [])
                    if sources and not web_sources:
                        if isinstance(sources[0], str):
                            st.caption("📚 Kaynaklar: " + ", ".join(sources))
    
    # ===== MOD SEÇİCİ KUTUSU (INPUT ÜSTÜNDE) =====
    with st.container(border=True):
        col1, col2 = st.columns([1, 8])
        
        with col1:
            web_enabled = st.toggle(
                "🌐 Web",
                value=st.session_state.web_search_enabled,
                help="Web'de arama yaparak yanıt ver",
                key="web_toggle"
            )
            st.session_state.web_search_enabled = web_enabled
        
        with col2:
            if st.session_state.web_search_enabled:
                st.markdown("🌐 **Web Araması Aktif** - İnternetten güncel bilgi alınacak")
            else:
                st.markdown("💬 **Normal Mod** - Bilgi tabanı kullanılıyor")
    
    # ===== CHAT INPUT =====
    user_input = st.chat_input("Mesajınızı yazın...", key="main_chat_input", disabled=st.session_state.is_generating)
    
    if user_input:
        # Reset stop flag
        st.session_state.stop_generation = False
        st.session_state.is_generating = True
        
        # Kullanıcı mesajını ekle
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "sources": [],
            "web_sources": [],
        })
        save_message_to_session("user", user_input)
        
        # AI yanıtını al
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            sources_placeholder = st.empty()
            stop_button_placeholder = st.empty()
            
            full_response = ""
            web_sources = []
            was_stopped = False
            
            # Durdur butonu göster
            with stop_button_placeholder:
                if st.button("⏹️ Yanıtı Durdur", key="stop_gen_btn", type="secondary", use_container_width=True):
                    st.session_state.stop_generation = True
            
            # Stream yanıt
            for chunk in stream_chat_message(user_input, st.session_state.web_search_enabled):
                # Durdurma kontrolü
                if st.session_state.stop_generation:
                    was_stopped = True
                    full_response += "\n\n*[Yanıt kullanıcı tarafından durduruldu]*"
                    response_placeholder.markdown(full_response)
                    break
                
                chunk_type = chunk.get("type")
                
                if chunk_type == "status":
                    status_msg = chunk.get("message", "")
                    response_placeholder.markdown(f"*⏳ {status_msg}*")
                
                elif chunk_type == "sources":
                    web_sources = chunk.get("sources", [])
                    # Kaynakları hemen göster
                    if web_sources:
                        with sources_placeholder:
                            render_sources_box(web_sources)
                
                elif chunk_type == "token":
                    full_response += chunk.get("content", "")
                    response_placeholder.markdown(full_response + "▌")
                
                elif chunk_type == "warning":
                    st.warning(chunk.get("message", ""))
                
                elif chunk_type == "error":
                    st.error(f"Hata: {chunk.get('message')}")
                    break
                
                elif chunk_type == "end":
                    final_sources = chunk.get("sources", web_sources)
                    if final_sources:
                        web_sources = final_sources
                    break
            
            # Durdur butonunu kaldır
            stop_button_placeholder.empty()
            
            # Final render
            if full_response:
                response_placeholder.markdown(full_response)
                
                # Kaynakları tekrar göster (eğer varsa ve henüz gösterilmediyse)
                if web_sources:
                    with sources_placeholder:
                        render_sources_box(web_sources)
                
                # Mesajı kaydet
                source_urls = [s.get("url", "") if isinstance(s, dict) else str(s) for s in web_sources] if web_sources else []
                save_message_to_session("assistant", full_response, source_urls)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sources": source_urls,
                    "web_sources": web_sources,
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
    
    # Upload
    st.markdown("### 📤 Döküman Yükle")
    
    uploaded_file = st.file_uploader(
        "Döküman seçin",
        type=["pdf", "docx", "txt", "md", "csv", "json", "html"],
        help="Desteklenen: PDF, DOCX, TXT, MD, CSV, JSON, HTML",
        key="doc_uploader"
    )
    
    if uploaded_file:
        st.info(f"📄 {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        
        if st.button("📥 Yükle ve İndexle", type="primary", key="upload_btn"):
            with st.spinner("Döküman işleniyor..."):
                result = upload_document(uploaded_file)
                
                if result and result.get("success"):
                    st.success(f"✅ {result.get('message', 'Yüklendi!')}")
                    st.info(f"📊 {result.get('chunks_created', 0)} parça oluşturuldu")
                    st.balloons()
                else:
                    st.error(f"❌ {result.get('error', 'Yükleme başarısız')}")
    
    st.markdown("---")
    
    # Döküman listesi
    st.markdown("### 📋 Yüklenen Dökümanlar")
    
    docs = get_documents()
    
    if docs and docs.get("documents"):
        for doc in docs["documents"]:
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                st.markdown(f"📄 **{doc.get('filename', 'Bilinmeyen')}**")
            with col2:
                size_kb = doc.get('size', 0) / 1024
                st.text(f"{size_kb:.1f} KB")
            with col3:
                if st.button("🗑️", key=f"deldoc_{doc.get('document_id')}"):
                    delete_document(doc.get("document_id"))
                    st.rerun()
    else:
        st.info("📭 Henüz döküman yüklenmemiş")


# ============ SEARCH PAGE ============

elif st.session_state.current_page == "search":
    st.markdown("## 🔍 Bilgi Tabanında Arama")
    st.caption("Yüklenen dökümanlarda semantik arama yapın")
    
    search_query = st.text_input("🔎 Arama sorgusu", placeholder="Ne aramak istiyorsunuz?", key="kb_search")
    
    col1, col2 = st.columns([4, 1])
    with col2:
        top_k = st.number_input("Sonuç", min_value=1, max_value=20, value=5, key="kb_topk")
    
    if st.button("🔍 Ara", type="primary", key="kb_search_btn") and search_query:
        with st.spinner("Aranıyor..."):
            results = search_documents(search_query, top_k)
            
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


# ============ DASHBOARD PAGE ============

elif st.session_state.current_page == "dashboard":
    st.markdown("## 📊 Dashboard")
    st.caption("Sistem metrikleri ve istatistikler")
    
    stats = get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Döküman", stats.get("documents", 0) if stats else 0)
    
    with col2:
        st.metric("💬 Session", stats.get("sessions", 0) if stats else 0)
    
    with col3:
        st.metric("📨 Mesaj", stats.get("total_messages", 0) if stats else 0)
    
    with col4:
        st.metric("🔍 Arama", stats.get("total_searches", 0) if stats else 0)
    
    st.markdown("---")
    
    # Sistem durumu
    st.markdown("### 🔧 Sistem Durumu")
    
    health = check_health()
    if health:
        components = health.get("components", {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**LLM**")
            if components.get("llm") == "healthy":
                st.success("✅ Aktif")
            else:
                st.error("❌ Sorunlu")
        
        with col2:
            st.markdown("**Vector Store**")
            if components.get("vector_store") == "healthy":
                doc_count = components.get('document_count', 0)
                st.success(f"✅ Aktif ({doc_count} döküman)")
            else:
                st.error("❌ Sorunlu")
        
        with col3:
            st.markdown("**API**")
            if components.get("api") == "healthy":
                st.success("✅ Aktif")
            else:
                st.error("❌ Sorunlu")


# ============ SETTINGS PAGE ============

elif st.session_state.current_page == "settings":
    st.markdown("## ⚙️ Ayarlar")
    st.caption("Uygulama tercihlerini özelleştirin")
    
    st.markdown("### 🎨 Görünüm")
    
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
            st.info("Bu özellik yakında eklenecek")
    
    st.markdown("---")
    
    st.markdown("### ℹ️ Hakkında")
    st.markdown("""
    **Enterprise AI Assistant v1.1.0**
    
    Özellikler:
    - 🌐 Web Search ile güncel bilgi erişimi
    - 📚 RAG ile döküman tabanlı yanıtlar
    - 🤖 Multi-Agent sistem (Orchestrator, Research, Writer, Analyzer)
    - 📷 Görsel analiz (VLM desteği)
    - 💾 Kalıcı konuşma geçmişi
    - 🔍 Geçmiş konuşmalarda arama
    
    Teknolojiler: FastAPI, Streamlit, Ollama, ChromaDB, LangChain
    """)


# ============ FOOTER ============

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888; font-size: 0.8rem; padding: 1rem;">
        Enterprise AI Assistant v1.1.0 | 🌐 Web Search • 📚 RAG • 🤖 Multi-Agent | Endüstri Standartlarında AI
    </div>
    """,
    unsafe_allow_html=True,
)
