"""
Enterprise AI Assistant - Streamlit Frontend
Endüstri Standartlarında Kurumsal AI Çözümü

Ana kullanıcı arayüzü - Chat, Döküman Yönetimi, Arama.
"""

import streamlit as st
import requests
import uuid
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============ CONFIGURATION ============

API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    .source-tag {
        display: inline-block;
        background-color: #e8f5e9;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    .status-healthy {
        color: #4caf50;
    }
    .status-unhealthy {
        color: #f44336;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ============ SESSION STATE ============

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"


# ============ API HELPERS ============

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


def send_chat_message(message: str):
    """Chat mesajı gönder."""
    return api_request(
        "POST",
        "/api/chat",
        json={
            "message": message,
            "session_id": st.session_state.session_id,
        },
    )


def upload_document(file):
    """Döküman yükle."""
    return api_request(
        "POST",
        "/api/documents/upload",
        files={"file": (file.name, file, file.type)},
    )


def search_documents(query: str, top_k: int = 5):
    """Döküman ara."""
    return api_request(
        "POST",
        "/api/search",
        json={"query": query, "top_k": top_k},
    )


def get_documents():
    """Döküman listesi al."""
    return api_request("GET", "/api/documents")


def delete_document(doc_id: str):
    """Döküman sil."""
    return api_request("DELETE", f"/api/documents/{doc_id}")


def get_stats():
    """İstatistikleri al."""
    return api_request("GET", "/api/admin/stats")


# ============ SIDEBAR ============

with st.sidebar:
    st.markdown("## 🤖 Enterprise AI")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "📍 Navigasyon",
        ["💬 Chat", "📁 Dökümanlar", "🔍 Arama", "📊 Dashboard"],
        label_visibility="collapsed",
    )
    
    if page == "💬 Chat":
        st.session_state.current_page = "chat"
    elif page == "📁 Dökümanlar":
        st.session_state.current_page = "documents"
    elif page == "🔍 Arama":
        st.session_state.current_page = "search"
    elif page == "📊 Dashboard":
        st.session_state.current_page = "dashboard"
    
    st.markdown("---")
    
    # Health status
    st.markdown("### 🔧 Sistem Durumu")
    health = check_health()
    
    if health:
        status = health.get("status", "unknown")
        if status == "healthy":
            st.success("✅ Sistem aktif")
        else:
            st.warning(f"⚠️ Durum: {status}")
        
        components = health.get("components", {})
        col1, col2 = st.columns(2)
        with col1:
            llm_status = components.get("llm", "unknown")
            if llm_status == "healthy":
                st.markdown("🟢 LLM")
            else:
                st.markdown("🔴 LLM")
        with col2:
            vs_status = components.get("vector_store", "unknown")
            if vs_status == "healthy":
                st.markdown("🟢 VectorDB")
            else:
                st.markdown("🔴 VectorDB")
    else:
        st.error("🔴 Bağlantı yok")
    
    st.markdown("---")
    
    # Session info
    st.markdown("### 📋 Session")
    st.text(f"ID: {st.session_state.session_id[:8]}...")
    st.text(f"Mesaj: {len(st.session_state.messages)}")
    
    if st.button("🗑️ Sohbeti Temizle"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()


# ============ MAIN CONTENT ============

# Header
st.markdown('<p class="main-header">🤖 Enterprise AI Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Endüstri Standartlarında Kurumsal AI Çözümü</p>', unsafe_allow_html=True)


# ============ CHAT PAGE ============

if st.session_state.current_page == "chat":
    st.markdown("## 💬 AI Asistan ile Sohbet")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display messages
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])
                    if msg.get("sources"):
                        st.markdown("**📚 Kaynaklar:**")
                        for source in msg["sources"]:
                            st.markdown(f'<span class="source-tag">{source}</span>', unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Mesajınızı yazın...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Düşünüyorum..."):
                response = send_chat_message(user_input)
                
                if response:
                    ai_message = response.get("response", "Bir hata oluştu.")
                    sources = response.get("sources", [])
                    
                    st.write(ai_message)
                    
                    if sources:
                        st.markdown("**📚 Kaynaklar:**")
                        for source in sources:
                            st.markdown(f'<span class="source-tag">{source}</span>', unsafe_allow_html=True)
                    
                    # Add to messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ai_message,
                        "sources": sources,
                    })
                else:
                    st.error("Yanıt alınamadı. Lütfen tekrar deneyin.")
    
    # Example prompts
    st.markdown("---")
    st.markdown("### 💡 Örnek Sorular")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 İzin politikası nedir?"):
            st.session_state.messages.append({"role": "user", "content": "İzin politikamız nedir?"})
            st.rerun()
    
    with col2:
        if st.button("📧 Email taslağı hazırla"):
            st.session_state.messages.append({"role": "user", "content": "Müdüre toplantı daveti için email taslağı hazırla"})
            st.rerun()
    
    with col3:
        if st.button("📊 Rapor özetle"):
            st.session_state.messages.append({"role": "user", "content": "Son yüklenen raporu özetle"})
            st.rerun()


# ============ DOCUMENTS PAGE ============

elif st.session_state.current_page == "documents":
    st.markdown("## 📁 Döküman Yönetimi")
    
    # Upload section
    st.markdown("### 📤 Döküman Yükle")
    
    uploaded_file = st.file_uploader(
        "Döküman seçin",
        type=["pdf", "docx", "txt", "md", "csv", "json", "html"],
        help="Desteklenen formatlar: PDF, DOCX, TXT, MD, CSV, JSON, HTML",
    )
    
    if uploaded_file:
        if st.button("📥 Yükle ve İndexle"):
            with st.spinner("Döküman işleniyor..."):
                result = upload_document(uploaded_file)
                
                if result and result.get("success"):
                    st.success(f"✅ {result.get('message')}")
                    st.info(f"📊 {result.get('chunks_created')} parça oluşturuldu")
                else:
                    st.error("❌ Yükleme başarısız")
    
    st.markdown("---")
    
    # Document list
    st.markdown("### 📋 Yüklenen Dökümanlar")
    
    docs = get_documents()
    
    if docs and docs.get("documents"):
        for doc in docs["documents"]:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"📄 **{doc.get('filename', 'Bilinmeyen')}**")
            
            with col2:
                size_kb = doc.get("size", 0) / 1024
                st.text(f"{size_kb:.1f} KB")
            
            with col3:
                if st.button("🗑️", key=f"del_{doc.get('document_id')}"):
                    delete_document(doc.get("document_id"))
                    st.rerun()
    else:
        st.info("📭 Henüz döküman yüklenmemiş")


# ============ SEARCH PAGE ============

elif st.session_state.current_page == "search":
    st.markdown("## 🔍 Bilgi Tabanında Arama")
    
    search_query = st.text_input("🔎 Arama sorgusu", placeholder="Ne aramak istiyorsunuz?")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        top_k = st.number_input("Sonuç sayısı", min_value=1, max_value=20, value=5)
    
    if st.button("🔍 Ara") and search_query:
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
                            st.markdown("**Metadata:**")
                            st.json(metadata)
            else:
                st.warning("😔 Sonuç bulunamadı")


# ============ DASHBOARD PAGE ============

elif st.session_state.current_page == "dashboard":
    st.markdown("## 📊 Dashboard")
    
    stats = get_stats()
    
    if stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="📄 Toplam Döküman",
                value=stats.get("documents", 0),
            )
        
        with col2:
            st.metric(
                label="💬 Aktif Session",
                value=stats.get("sessions", 0),
            )
        
        with col3:
            st.metric(
                label="📨 Toplam Mesaj",
                value=stats.get("total_messages", 0),
            )
    
    st.markdown("---")
    
    # System info
    st.markdown("### 🔧 Sistem Bilgisi")
    
    health = check_health()
    if health:
        components = health.get("components", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**LLM Durumu**")
            llm_status = components.get("llm", "unknown")
            if llm_status == "healthy":
                st.success("✅ Aktif")
            else:
                st.error(f"❌ {llm_status}")
        
        with col2:
            st.markdown("**Vector Store**")
            vs_status = components.get("vector_store", "unknown")
            if vs_status == "healthy":
                st.success(f"✅ Aktif ({components.get('document_count', 0)} döküman)")
            else:
                st.error(f"❌ {vs_status}")


# ============ FOOTER ============

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        Enterprise AI Assistant v1.0.0 | Endüstri Standartlarında Kurumsal AI Çözümü
    </div>
    """,
    unsafe_allow_html=True,
)
