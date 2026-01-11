"""
Enterprise AI Assistant - Streamlit Frontend
Endüstri Standartlarında Kurumsal AI Çözümü

Ana kullanıcı arayüzü - Chat, Döküman Yönetimi, Arama, Geçmiş.
"""

import streamlit as st
import requests
import uuid
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.session_manager import session_manager

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
    .history-item {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #1f77b4;
        cursor: pointer;
    }
    .history-item:hover {
        background-color: #e8f4f8;
    }
    .search-result {
        background-color: #fff8e1;
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #ffc107;
    }
    .session-selector {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.2rem 0;
        cursor: pointer;
    }
    .session-selector:hover {
        background-color: #bbdefb;
    }
</style>
""", unsafe_allow_html=True)


# ============ SESSION STATE ============

if "session_id" not in st.session_state:
    # Yeni session oluştur ve dosyaya kaydet
    new_session = session_manager.create_session()
    st.session_state.session_id = new_session.id

if "messages" not in st.session_state:
    # Mevcut session'ı yükle
    existing_session = session_manager.get_session(st.session_state.session_id)
    if existing_session:
        st.session_state.messages = [
            {
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
            }
            for m in existing_session.messages
        ]
    else:
        st.session_state.messages = []

if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"

if "viewing_session_id" not in st.session_state:
    st.session_state.viewing_session_id = None


# ============ HELPER FUNCTIONS ============

def save_message_to_session(role: str, content: str, sources: list = None):
    """Mesajı session dosyasına kaydet."""
    session_manager.add_message(
        st.session_state.session_id,
        role=role,
        content=content,
        sources=sources or [],
    )
    
    # İlk mesajda otomatik başlık oluştur
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
                "sources": m.sources,
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
        ["💬 Chat", "� Geçmiş", "📁 Dökümanlar", "🔍 Arama", "📊 Dashboard"],
        label_visibility="collapsed",
    )
    
    if page == "💬 Chat":
        st.session_state.current_page = "chat"
    elif page == "📜 Geçmiş":
        st.session_state.current_page = "history"
    elif page == "📁 Dökümanlar":
        st.session_state.current_page = "documents"
    elif page == "🔍 Arama":
        st.session_state.current_page = "search"
    elif page == "📊 Dashboard":
        st.session_state.current_page = "dashboard"
    
    st.markdown("---")
    
    # ============ SESSION SELECTOR ============
    st.markdown("### 📂 Son Konuşmalar")
    
    # Yeni konuşma butonu
    if st.button("➕ Yeni Konuşma", use_container_width=True):
        create_new_session()
        st.rerun()
    
    # Son 10 konuşmayı listele
    recent_sessions = session_manager.list_sessions(limit=10)
    
    for session_info in recent_sessions:
        session_id = session_info["id"]
        title = session_info["title"][:30] + "..." if len(session_info["title"]) > 30 else session_info["title"]
        msg_count = session_info.get("message_count", 0)
        is_current = session_id == st.session_state.session_id
        
        # Aktif session'ı vurgula
        if is_current:
            st.markdown(f"**🟢 {title}** ({msg_count})")
        else:
            if st.button(f"💬 {title} ({msg_count})", key=f"session_{session_id}", use_container_width=True):
                load_session(session_id)
                st.rerun()
    
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
        session_manager.delete_session(st.session_state.session_id)
        create_new_session()
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
        # Mesajı kaydet
        save_message_to_session("user", user_input)
        
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Geçmiş konuşma sorgularını kontrol et
        history_keywords = [
            "daha önce", "daha once", "önceden", "onceden",
            "geçmişte", "gecmiste", "önceki konuşma", "onceki konusma",
            "hatırla", "hatirla", "ne demiştim", "ne demistim",
            "konuşmuştuk", "konusmustuk", "bahsetmiştim", "bahsetmistim"
        ]
        
        is_history_query = any(kw in user_input.lower() for kw in history_keywords)
        
        # Geçmişten bağlam al
        history_context = ""
        if is_history_query:
            history_context = session_manager.get_context_for_query(
                user_input,
                current_session_id=st.session_state.session_id,
                max_results=5
            )
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Düşünüyorum..."):
                # Eğer geçmiş sorgusu ise, bağlamı mesaja ekle
                message_to_send = user_input
                if history_context:
                    message_to_send = f"""Kullanıcı geçmiş konuşmalardan bilgi soruyor.

{history_context}

Kullanıcının sorusu: {user_input}

Yukarıdaki geçmiş konuşmalardan elde edilen bilgileri kullanarak yanıt ver. Eğer ilgili bir şey bulamadıysan, bunu belirt."""
                
                response = send_chat_message(message_to_send)
                
                if response:
                    ai_message = response.get("response", "Bir hata oluştu.")
                    sources = response.get("sources", [])
                    
                    # Geçmiş kullanıldıysa belirt
                    if history_context:
                        sources = sources + ["Geçmiş Konuşmalar"]
                    
                    st.write(ai_message)
                    
                    if sources:
                        st.markdown("**📚 Kaynaklar:**")
                        for source in sources:
                            st.markdown(f'<span class="source-tag">{source}</span>', unsafe_allow_html=True)
                    
                    # Mesajı kaydet
                    save_message_to_session("assistant", ai_message, sources)
                    
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
            save_message_to_session("user", "İzin politikamız nedir?")
            st.rerun()
    
    with col2:
        if st.button("📧 Email taslağı hazırla"):
            st.session_state.messages.append({"role": "user", "content": "Müdüre toplantı daveti için email taslağı hazırla"})
            save_message_to_session("user", "Müdüre toplantı daveti için email taslağı hazırla")
            st.rerun()
    
    with col3:
        if st.button("🕐 Geçmişte ne sordum?"):
            st.session_state.messages.append({"role": "user", "content": "Daha önce sana hangi konularda sorular sordum?"})
            save_message_to_session("user", "Daha önce sana hangi konularda sorular sordum?")
            st.rerun()


# ============ HISTORY PAGE ============

elif st.session_state.current_page == "history":
    st.markdown("## 📜 Geçmiş Konuşmalar")
    
    # Arama bölümü
    st.markdown("### 🔎 Konuşmalarda Ara")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        history_search_query = st.text_input(
            "Arama",
            placeholder="Geçmiş konuşmalarda ne aramak istiyorsunuz?",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 Ara", use_container_width=True)
    
    if search_button and history_search_query:
        with st.spinner("Aranıyor..."):
            results = session_manager.search_all_sessions(history_search_query, limit=20)
            
            if results:
                st.success(f"✅ {len(results)} sonuç bulundu")
                
                for i, result in enumerate(results, 1):
                    role_icon = "👤" if result["role"] == "user" else "🤖"
                    date_str = result.get("timestamp", "")[:10] if result.get("timestamp") else ""
                    
                    with st.expander(f"{role_icon} {result['session_title'][:40]}... - {date_str}"):
                        st.markdown(f"**Mesaj:**\n{result['content'][:500]}{'...' if len(result['content']) > 500 else ''}")
                        
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            if st.button("📖 Konuşmaya Git", key=f"goto_{result['session_id']}_{i}"):
                                load_session(result["session_id"])
                                st.session_state.current_page = "chat"
                                st.rerun()
            else:
                st.warning("😔 Sonuç bulunamadı")
    
    st.markdown("---")
    
    # En çok konuşulan konular
    st.markdown("### 🏷️ En Çok Konuşulan Konular")
    
    topics = session_manager.get_all_topics(limit=15)
    
    if topics:
        topic_html = ""
        for topic, count in topics:
            topic_html += f'<span class="source-tag">{topic} ({count})</span> '
        st.markdown(topic_html, unsafe_allow_html=True)
    else:
        st.info("Henüz yeterli konuşma verisi yok")
    
    st.markdown("---")
    
    # Tüm konuşmalar listesi
    st.markdown("### 📋 Tüm Konuşmalar")
    
    all_sessions = session_manager.list_sessions(limit=50)
    
    if all_sessions:
        for session_info in all_sessions:
            session_id = session_info["id"]
            title = session_info["title"]
            created_at = session_info["created_at"][:10] if session_info.get("created_at") else ""
            msg_count = session_info.get("message_count", 0)
            preview = session_info.get("preview", "")[:100]
            
            with st.expander(f"📁 {title} ({msg_count} mesaj) - {created_at}"):
                if preview:
                    st.markdown(f"*{preview}...*")
                
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    if st.button("💬 Devam Et", key=f"continue_{session_id}"):
                        load_session(session_id)
                        st.session_state.current_page = "chat"
                        st.rerun()
                
                with col2:
                    if st.button("📖 Oku", key=f"view_{session_id}"):
                        st.session_state.viewing_session_id = session_id
                        st.rerun()
                
                with col3:
                    if st.button("📥 İndir", key=f"export_{session_id}"):
                        content = session_manager.export_session(session_id, "md")
                        if content:
                            st.download_button(
                                label="📄 Markdown İndir",
                                data=content,
                                file_name=f"konusma_{session_id[:8]}.md",
                                mime="text/markdown",
                                key=f"download_{session_id}"
                            )
                
                with col4:
                    if st.button("🗑️", key=f"delete_{session_id}"):
                        session_manager.delete_session(session_id)
                        st.success("Silindi!")
                        st.rerun()
                
                # Konuşma detayını göster
                if st.session_state.viewing_session_id == session_id:
                    st.markdown("---")
                    st.markdown("**Konuşma İçeriği:**")
                    
                    session = session_manager.get_session(session_id)
                    if session:
                        for msg in session.messages:
                            role_icon = "👤" if msg.role == "user" else "🤖"
                            timestamp = msg.timestamp[:19].replace("T", " ") if msg.timestamp else ""
                            st.markdown(f"**{role_icon} {timestamp}**")
                            st.markdown(msg.content)
                            st.markdown("---")
    else:
        st.info("📭 Henüz kayıtlı konuşma yok")


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
