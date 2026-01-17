"""
AI ile Öğren - Frontend Sayfası
Enterprise Learning Platform

Çalışma ortamları, dökümanlar, testler ve öğrenme araçları.
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Optional, List, Dict

# API Base URL
API_BASE = "http://localhost:8001"


def get_api(endpoint: str, params: dict = None) -> dict:
    """API GET isteği."""
    try:
        response = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Hatası: {e}")
        return {}


def post_api(endpoint: str, data: dict = None) -> dict:
    """API POST isteği."""
    try:
        response = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Hatası: {e}")
        return {}


def stream_api(endpoint: str, data: dict = None):
    """API streaming isteği."""
    try:
        response = requests.post(
            f"{API_BASE}{endpoint}", 
            json=data, 
            stream=True, 
            timeout=300
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        yield json.loads(line_str[6:])
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        yield {"type": "error", "message": str(e)}


def format_date(iso_date: str) -> str:
    """ISO tarihini formatla."""
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return iso_date


def render_workspace_list():
    """Çalışma ortamları listesi."""
    st.markdown("## 📚 Çalışma Ortamlarım")
    
    # Yeni oluştur butonu
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("➕ Yeni Oluştur", use_container_width=True, type="primary"):
            st.session_state.learning_view = "create_workspace"
            st.rerun()
    
    # Mevcut ortamları listele
    data = get_api("/api/learning/workspaces")
    workspaces = data.get("workspaces", [])
    
    if not workspaces:
        st.info("📭 Henüz çalışma ortamı yok. Yeni bir tane oluşturun!")
        return
    
    # Grid görünümü
    cols = st.columns(3)
    
    for idx, ws in enumerate(workspaces):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"### 📖 {ws['name']}")
                
                if ws.get('topic'):
                    st.caption(f"📌 {ws['topic']}")
                
                if ws.get('description'):
                    st.markdown(f"_{ws['description'][:100]}..._" if len(ws.get('description', '')) > 100 else f"_{ws['description']}_")
                
                # İstatistikler
                st.markdown(f"""
                <div style="font-size: 0.85em; color: #888;">
                    📄 {len(ws.get('documents', []))} döküman • 
                    📝 {len(ws.get('tests', []))} test • 
                    💬 {len(ws.get('chat_history', []))} mesaj
                </div>
                """, unsafe_allow_html=True)
                
                st.caption(f"🕐 {format_date(ws['updated_at'])}")
                
                if st.button("🚀 Çalışmaya Başla", key=f"open_{ws['id']}", use_container_width=True):
                    st.session_state.current_workspace_id = ws['id']
                    st.session_state.learning_view = "workspace_detail"
                    st.rerun()


def render_create_workspace():
    """Yeni çalışma ortamı oluşturma formu."""
    st.markdown("## ➕ Yeni Çalışma Ortamı")
    
    if st.button("⬅️ Geri"):
        st.session_state.learning_view = "list"
        st.rerun()
    
    with st.form("create_workspace"):
        name = st.text_input("📝 Çalışma Ortamı Adı *", placeholder="Örn: Makine Öğrenmesi Çalışması")
        topic = st.text_input("📌 Konu", placeholder="Örn: Supervised Learning, Neural Networks")
        description = st.text_area("📄 Açıklama", placeholder="Bu çalışma ortamının amacı...")
        
        # Kaynak seçimi
        st.markdown("### 📚 Başlangıç Kaynakları")
        st.caption("Daha sonra çalışma ortamı içinden de kaynak ekleyebilirsiniz.")
        
        submitted = st.form_submit_button("✅ Oluştur", type="primary", use_container_width=True)
        
        if submitted:
            if not name:
                st.error("Lütfen bir isim girin!")
            else:
                result = post_api("/api/learning/workspaces", {
                    "name": name,
                    "topic": topic,
                    "description": description
                })
                
                if result.get("success"):
                    st.success("✅ Çalışma ortamı oluşturuldu!")
                    st.session_state.current_workspace_id = result["workspace"]["id"]
                    st.session_state.learning_view = "workspace_detail"
                    st.rerun()


def render_workspace_detail():
    """Çalışma ortamı detay sayfası."""
    workspace_id = st.session_state.get("current_workspace_id")
    
    if not workspace_id:
        st.session_state.learning_view = "list"
        st.rerun()
        return
    
    data = get_api(f"/api/learning/workspaces/{workspace_id}")
    
    if not data.get("workspace"):
        st.error("Çalışma ortamı bulunamadı!")
        return
    
    workspace = data["workspace"]
    stats = data.get("stats", {})
    documents = data.get("documents", [])
    tests = data.get("tests", [])
    
    # Header
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"## 📖 {workspace['name']}")
        if workspace.get("topic"):
            st.caption(f"📌 Konu: {workspace['topic']}")
    
    with col2:
        if st.button("⬅️ Geri", use_container_width=True):
            st.session_state.learning_view = "list"
            st.rerun()
    
    # Sekmeler
    tabs = st.tabs([
        "🏠 Genel Bakış",
        "📚 Kaynaklar", 
        "📄 Çalışma Dökümanları",
        "📝 Testler",
        "💬 Chat"
    ])
    
    # === GENEL BAKIŞ ===
    with tabs[0]:
        render_workspace_overview(workspace, stats, documents, tests)
    
    # === KAYNAKLAR ===
    with tabs[1]:
        render_sources_tab(workspace_id)
    
    # === DÖKÜMANLAR ===
    with tabs[2]:
        render_documents_tab(workspace_id, documents)
    
    # === TESTLER ===
    with tabs[3]:
        render_tests_tab(workspace_id, tests)
    
    # === CHAT ===
    with tabs[4]:
        render_chat_tab(workspace_id)


def render_workspace_overview(workspace: dict, stats: dict, documents: list, tests: list):
    """Genel bakış sekmesi."""
    
    # İstatistik kartları
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Aktif Kaynaklar", stats.get("active_sources_count", 0))
    
    with col2:
        st.metric("📄 Dökümanlar", stats.get("documents_count", 0))
    
    with col3:
        st.metric("📝 Testler", stats.get("tests_count", 0))
    
    with col4:
        avg_score = stats.get("average_score", 0)
        st.metric("📊 Ortalama Puan", f"{avg_score}%" if avg_score else "-")
    
    st.divider()
    
    # Son aktiviteler
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📄 Son Dökümanlar")
        if documents:
            for doc in documents[:3]:
                status_icon = "✅" if doc.get("status") == "completed" else "⏳"
                st.markdown(f"- {status_icon} **{doc['title']}** ({doc['page_count']} sayfa)")
        else:
            st.caption("Henüz döküman yok")
    
    with col2:
        st.markdown("### 📝 Son Testler")
        if tests:
            for test in tests[:3]:
                status = test.get("status", "not_started")
                if status == "completed":
                    score = test.get("score", 0)
                    st.markdown(f"- ✅ **{test['title']}** - %{score:.0f}")
                else:
                    st.markdown(f"- 📝 **{test['title']}**")
        else:
            st.caption("Henüz test yok")


def render_sources_tab(workspace_id: str):
    """Kaynaklar sekmesi."""
    st.markdown("### 📚 Kaynak Yönetimi")
    st.caption("Aktif kaynaklar bu çalışma ortamındaki chat, döküman ve testlerde kullanılır.")
    
    data = get_api(f"/api/learning/workspaces/{workspace_id}/sources")
    sources = data.get("sources", [])
    
    if not sources:
        st.info("📭 Henüz yüklenmiş kaynak yok. Ana sayfadan döküman yükleyebilirsiniz.")
        return
    
    # Filtre
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Kaynak ara...", key="source_search")
    with col2:
        show_all = st.checkbox("Hepsini göster", value=True)
    
    # Kaynak listesi
    for source in sources:
        if search and search.lower() not in source['name'].lower():
            continue
        
        if not show_all and not source.get('active'):
            continue
        
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            icon = "📄" if source['type'] in ['PDF', 'DOCX', 'TXT'] else "📊" if source['type'] in ['XLSX', 'CSV'] else "📑"
            st.markdown(f"{icon} **{source['name']}** ({source['type']})")
        
        with col2:
            size_kb = source.get('size', 0) / 1024
            st.caption(f"{size_kb:.1f} KB")
        
        with col3:
            is_active = source.get('active', False)
            new_state = st.toggle(
                "Aktif", 
                value=is_active, 
                key=f"src_{source['id']}",
                help="Bu kaynağı çalışma ortamında kullan"
            )
            
            if new_state != is_active:
                post_api(f"/api/learning/workspaces/{workspace_id}/sources/toggle", {
                    "source_id": source['id'],
                    "active": new_state
                })
                st.rerun()


def render_documents_tab(workspace_id: str, documents: list):
    """Çalışma dökümanları sekmesi."""
    
    # Yeni döküman oluştur
    with st.expander("➕ Yeni Çalışma Dökümanı Oluştur", expanded=not documents):
        render_create_document_form(workspace_id)
    
    st.divider()
    
    # Mevcut dökümanlar
    if not documents:
        st.info("📭 Henüz çalışma dökümanı yok.")
        return
    
    st.markdown("### 📄 Oluşturulan Dökümanlar")
    
    for doc in documents:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                status_icon = {
                    "completed": "✅",
                    "generating": "⏳",
                    "failed": "❌"
                }.get(doc.get("status"), "📄")
                
                st.markdown(f"### {status_icon} {doc['title']}")
                st.caption(f"📌 {doc['topic']} • 📄 {doc['page_count']} sayfa • 🎨 {doc['style']}")
            
            with col2:
                st.caption(f"🕐 {format_date(doc['created_at'])}")
            
            with col3:
                if doc.get("status") == "completed":
                    if st.button("👁️ Görüntüle", key=f"view_doc_{doc['id']}"):
                        st.session_state.viewing_document_id = doc['id']
                        st.rerun()
            
            # Döküman içeriği görüntüleme
            if st.session_state.get("viewing_document_id") == doc['id']:
                st.divider()
                st.markdown(doc.get("content", "İçerik yükleniyor..."))
                
                if st.button("❌ Kapat", key=f"close_doc_{doc['id']}"):
                    st.session_state.viewing_document_id = None
                    st.rerun()


def render_create_document_form(workspace_id: str):
    """Döküman oluşturma formu."""
    
    # Stiller
    styles_data = get_api("/api/learning/documents/styles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("📝 Döküman Başlığı *", placeholder="Örn: Makine Öğrenmesi Temelleri")
        topic = st.text_input("📌 Konu *", placeholder="Örn: Supervised learning algoritmaları")
    
    with col2:
        page_count = st.slider("📄 Sayfa Sayısı", min_value=1, max_value=40, value=5)
        
        style_options = {v['name']: k for k, v in styles_data.items()} if styles_data else {
            "Detaylı": "detailed",
            "Akademik": "academic",
            "Sade": "casual",
            "Özet": "summary",
            "Sınav Hazırlık": "exam_prep"
        }
        style_name = st.selectbox("🎨 Yazım Stili", list(style_options.keys()))
        style = style_options.get(style_name, "detailed")
    
    custom_instructions = st.text_area(
        "📋 Özel Talimatlar",
        placeholder="Örn: Özellikle CNN ve RNN'lere odaklan. Kod örnekleri ekle. Her bölümde özet tablo olsun.",
        help="Dökümanın nasıl hazırlanmasını istediğinizi detaylıca açıklayın."
    )
    
    if st.button("🚀 Dökümanı Oluştur", type="primary", use_container_width=True):
        if not title or not topic:
            st.error("Başlık ve konu zorunludur!")
            return
        
        # Önce döküman meta verisi oluştur
        result = post_api(f"/api/learning/workspaces/{workspace_id}/documents", {
            "title": title,
            "topic": topic,
            "page_count": page_count,
            "style": style,
            "custom_instructions": custom_instructions
        })
        
        if result.get("success"):
            doc_id = result["document"]["id"]
            
            # Streaming ile içerik oluştur
            st.info("📝 Döküman oluşturuluyor... Bu işlem birkaç dakika sürebilir.")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            content_preview = st.empty()
            
            for event in stream_api(f"/api/learning/documents/{doc_id}/generate?custom_instructions={custom_instructions}"):
                event_type = event.get("type")
                
                if event_type == "status":
                    progress_bar.progress(event.get("progress", 0) / 100)
                    status_text.info(event.get("message", ""))
                
                elif event_type == "section_complete":
                    content_preview.markdown(f"✅ **{event.get('section_title')}** tamamlandı")
                
                elif event_type == "complete":
                    progress_bar.progress(100)
                    st.success(f"✅ Döküman başarıyla oluşturuldu! ({event.get('word_count', 0)} kelime)")
                    st.rerun()
                
                elif event_type == "error":
                    st.error(event.get("message", "Bir hata oluştu"))


def render_tests_tab(workspace_id: str, tests: list):
    """Testler sekmesi."""
    
    # Yeni test oluştur
    with st.expander("➕ Yeni Test Oluştur", expanded=not tests):
        render_create_test_form(workspace_id)
    
    st.divider()
    
    # Mevcut testler
    if not tests:
        st.info("📭 Henüz test yok.")
        return
    
    st.markdown("### 📝 Oluşturulan Testler")
    
    for test in tests:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            status = test.get("status", "not_started")
            
            with col1:
                status_icon = {
                    "completed": "✅",
                    "in_progress": "⏳",
                    "not_started": "📝"
                }.get(status, "📝")
                
                st.markdown(f"### {status_icon} {test['title']}")
                st.caption(f"📋 {test['question_count']} soru • 🎯 {test['difficulty']} • {test['test_type']}")
            
            with col2:
                if status == "completed":
                    score = test.get("score", 0)
                    st.metric("Puan", f"%{score:.0f}")
                else:
                    st.caption(f"🕐 {format_date(test['created_at'])}")
            
            with col3:
                if status == "not_started" and test.get("questions"):
                    if st.button("▶️ Başla", key=f"start_test_{test['id']}"):
                        st.session_state.active_test_id = test['id']
                        st.session_state.test_mode = "taking"
                        st.rerun()
                elif status == "in_progress":
                    if st.button("▶️ Devam Et", key=f"continue_test_{test['id']}"):
                        st.session_state.active_test_id = test['id']
                        st.session_state.test_mode = "taking"
                        st.rerun()
                elif status == "completed":
                    if st.button("👁️ Sonuçlar", key=f"results_test_{test['id']}"):
                        st.session_state.active_test_id = test['id']
                        st.session_state.test_mode = "results"
                        st.rerun()
    
    # Aktif test varsa göster
    if st.session_state.get("active_test_id"):
        st.divider()
        render_active_test(st.session_state.active_test_id)


def render_create_test_form(workspace_id: str):
    """Test oluşturma formu."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("📝 Test Başlığı *", placeholder="Örn: Makine Öğrenmesi Quiz 1")
        description = st.text_input("📄 Açıklama", placeholder="Bu testin amacı...")
    
    with col2:
        question_count = st.slider("📋 Soru Sayısı", min_value=5, max_value=50, value=10)
        
        test_types = {
            "Çoktan Seçmeli": "multiple_choice",
            "Doğru/Yanlış": "true_false",
            "Boşluk Doldurma": "fill_blank",
            "Kısa Cevap": "short_answer",
            "Karışık": "mixed"
        }
        test_type_name = st.selectbox("📝 Soru Türü", list(test_types.keys()))
        test_type = test_types[test_type_name]
    
    difficulty = st.select_slider(
        "🎯 Zorluk",
        options=["easy", "medium", "hard", "mixed"],
        value="mixed",
        format_func=lambda x: {"easy": "Kolay", "medium": "Orta", "hard": "Zor", "mixed": "Karışık"}[x]
    )
    
    custom_instructions = st.text_area(
        "📋 Özel Talimatlar",
        placeholder="Örn: Formül soruları olsun. Uygulama örnekleri içersin. Kavram tanımlarına odaklan.",
        help="Testin nasıl hazırlanmasını istediğinizi açıklayın."
    )
    
    if st.button("🚀 Testi Oluştur", type="primary", use_container_width=True):
        if not title:
            st.error("Başlık zorunludur!")
            return
        
        # Test meta verisi oluştur
        result = post_api(f"/api/learning/workspaces/{workspace_id}/tests", {
            "title": title,
            "description": description,
            "test_type": test_type,
            "question_count": question_count,
            "difficulty": difficulty,
            "custom_instructions": custom_instructions
        })
        
        if result.get("success"):
            test_id = result["test"]["id"]
            
            st.info("📝 Sorular oluşturuluyor...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for event in stream_api(f"/api/learning/tests/{test_id}/generate?custom_instructions={custom_instructions}"):
                event_type = event.get("type")
                
                if event_type == "status":
                    progress_bar.progress(event.get("progress", 0) / 100)
                    status_text.info(event.get("message", ""))
                
                elif event_type == "questions_batch":
                    status_text.success(f"✅ {event.get('total_so_far', 0)} soru oluşturuldu")
                
                elif event_type == "complete":
                    progress_bar.progress(100)
                    st.success(f"✅ Test başarıyla oluşturuldu! ({event.get('question_count', 0)} soru)")
                    st.rerun()
                
                elif event_type == "error":
                    st.error(event.get("message", "Bir hata oluştu"))


def render_active_test(test_id: str):
    """Aktif testi göster."""
    
    data = get_api(f"/api/learning/tests/{test_id}")
    test = data.get("test")
    
    if not test:
        st.error("Test bulunamadı!")
        return
    
    mode = st.session_state.get("test_mode", "taking")
    
    if mode == "results":
        render_test_results(test)
    else:
        render_test_taking(test)


def render_test_taking(test: dict):
    """Test çözme arayüzü."""
    
    st.markdown(f"### 📝 {test['title']}")
    
    questions = test.get("questions", [])
    user_answers = test.get("user_answers", {})
    
    current_q_idx = st.session_state.get("current_question", 0)
    
    if not questions:
        st.warning("Bu testte henüz soru yok!")
        return
    
    # İlerleme
    answered = len(user_answers)
    st.progress(answered / len(questions))
    st.caption(f"📊 {answered}/{len(questions)} soru cevaplandı")
    
    # Soru navigasyonu
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("⬅️ Önceki", disabled=current_q_idx == 0):
            st.session_state.current_question = current_q_idx - 1
            st.rerun()
    
    with col2:
        st.selectbox(
            "Soru seç",
            range(len(questions)),
            index=current_q_idx,
            format_func=lambda x: f"Soru {x + 1}{'✅' if questions[x].get('id') in user_answers else ''}",
            key="question_selector",
            on_change=lambda: setattr(st.session_state, 'current_question', st.session_state.question_selector)
        )
    
    with col3:
        if st.button("Sonraki ➡️", disabled=current_q_idx >= len(questions) - 1):
            st.session_state.current_question = current_q_idx + 1
            st.rerun()
    
    st.divider()
    
    # Aktif soru
    question = questions[current_q_idx]
    q_id = question.get("id")
    q_type = question.get("question_type")
    
    st.markdown(f"### Soru {current_q_idx + 1}")
    st.markdown(question.get("question", ""))
    
    # Cevap alanı
    current_answer = user_answers.get(q_id, "")
    
    if q_type in ["multiple_choice", "MULTIPLE_CHOICE"]:
        options = question.get("options", [])
        answer = st.radio("Cevabınız:", options, index=None, key=f"ans_{q_id}")
        if answer:
            # Sadece harf al (A, B, C, D)
            answer = answer[0] if answer else ""
    
    elif q_type in ["true_false", "TRUE_FALSE"]:
        answer = st.radio("Cevabınız:", ["Doğru", "Yanlış"], index=None, key=f"ans_{q_id}")
    
    elif q_type in ["fill_blank", "FILL_BLANK"]:
        answer = st.text_input("Cevabınız:", value=current_answer, key=f"ans_{q_id}")
    
    else:  # short_answer
        answer = st.text_area("Cevabınız:", value=current_answer, key=f"ans_{q_id}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Cevabı Kaydet", use_container_width=True):
            if answer:
                result = post_api(f"/api/learning/tests/{test['id']}/answer", {
                    "question_id": q_id,
                    "answer": answer
                })
                if result.get("success"):
                    st.success("✅ Cevap kaydedildi!")
                    st.rerun()
    
    with col2:
        # Anlamadığını sor
        if st.button("❓ Bu Soruyu Anlamadım", use_container_width=True):
            st.session_state[f"explain_{q_id}"] = True
            st.rerun()
    
    # Açıklama istendi mi?
    if st.session_state.get(f"explain_{q_id}"):
        st.divider()
        st.markdown("### 💡 Yardım Al")
        
        user_question = st.text_input("Ne anlamadınız?", placeholder="Örn: Bu kavramı anlamadım...")
        
        if st.button("🤔 Açıkla"):
            if user_question:
                result = post_api(f"/api/learning/tests/{test['id']}/explain", {
                    "question_id": q_id,
                    "user_question": user_question
                })
                
                if result.get("success"):
                    st.info(result.get("explanation", ""))
    
    # Testi bitir
    st.divider()
    if answered == len(questions):
        if st.button("🏁 Testi Bitir ve Sonuçları Gör", type="primary", use_container_width=True):
            result = post_api(f"/api/learning/tests/{test['id']}/complete")
            if result.get("success"):
                st.session_state.test_mode = "results"
                st.rerun()
    
    # Çık
    if st.button("❌ Testi Kapat"):
        st.session_state.active_test_id = None
        st.session_state.test_mode = None
        st.session_state.current_question = 0
        st.rerun()


def render_test_results(test: dict):
    """Test sonuçları."""
    
    st.markdown(f"### 📊 Test Sonuçları: {test['title']}")
    
    score = test.get("score", 0)
    
    # Skor gösterimi
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Puan", f"%{score:.0f}")
    
    with col2:
        questions = test.get("questions", [])
        user_answers = test.get("user_answers", {})
        
        correct = 0
        for q in questions:
            if user_answers.get(q["id"], "").strip().lower() == q.get("correct_answer", "").strip().lower():
                correct += 1
        
        st.metric("✅ Doğru", f"{correct}/{len(questions)}")
    
    with col3:
        st.metric("❌ Yanlış", f"{len(questions) - correct}/{len(questions)}")
    
    st.divider()
    
    # Soru detayları
    st.markdown("### 📋 Soru Detayları")
    
    for i, q in enumerate(test.get("questions", []), 1):
        q_id = q.get("id")
        user_ans = test.get("user_answers", {}).get(q_id, "-")
        correct_ans = q.get("correct_answer", "")
        is_correct = user_ans.strip().lower() == correct_ans.strip().lower()
        
        with st.expander(f"{'✅' if is_correct else '❌'} Soru {i}: {q.get('question', '')[:50]}..."):
            st.markdown(f"**Soru:** {q.get('question')}")
            
            if q.get("options"):
                st.markdown("**Seçenekler:**")
                for opt in q.get("options", []):
                    st.markdown(f"- {opt}")
            
            st.markdown(f"**Sizin Cevabınız:** {user_ans}")
            st.markdown(f"**Doğru Cevap:** {correct_ans}")
            st.markdown(f"**Açıklama:** {q.get('explanation', '-')}")
    
    if st.button("⬅️ Testlere Dön"):
        st.session_state.active_test_id = None
        st.session_state.test_mode = None
        st.rerun()


def render_chat_tab(workspace_id: str):
    """Chat sekmesi."""
    
    st.markdown("### 💬 Çalışma Asistanı")
    st.caption("Aktif kaynaklarınıza dayalı sorular sorun.")
    
    # Chat geçmişi
    history = get_api(f"/api/learning/workspaces/{workspace_id}/chat")
    messages = history.get("messages", [])
    
    # Mesajları göster
    chat_container = st.container(height=400)
    
    with chat_container:
        for msg in messages[-20:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            with st.chat_message(role):
                st.markdown(content)
                
                if msg.get("sources"):
                    st.caption(f"📚 Kaynaklar: {', '.join(msg['sources'])}")
    
    # Mesaj gönder
    user_input = st.chat_input("Sorunuzu yazın...")
    
    if user_input:
        # Kullanıcı mesajını göster
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
        
        # Yanıt al
        with chat_container:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                sources_placeholder = st.empty()
                
                full_response = ""
                sources = []
                
                for event in stream_api(f"/api/learning/workspaces/{workspace_id}/chat/stream", {"message": user_input}):
                    event_type = event.get("type")
                    
                    if event_type == "sources":
                        sources = event.get("sources", [])
                        if sources:
                            sources_placeholder.caption(f"📚 Kaynaklar: {', '.join(sources)}")
                    
                    elif event_type == "token":
                        full_response += event.get("content", "")
                        response_placeholder.markdown(full_response + "▌")
                    
                    elif event_type == "end":
                        response_placeholder.markdown(full_response)
                
                if not full_response:
                    response_placeholder.markdown("Yanıt alınamadı.")


def main():
    """Ana sayfa."""
    
    st.set_page_config(
        page_title="AI ile Öğren",
        page_icon="📚",
        layout="wide"
    )
    
    # Sidebar
    with st.sidebar:
        st.markdown("# 📚 AI ile Öğren")
        st.caption("Kişiselleştirilmiş öğrenme platformu")
        
        st.divider()
        
        # İstatistikler
        stats = get_api("/api/learning/stats")
        if stats:
            st.metric("📖 Çalışma Ortamları", stats.get("workspaces_count", 0))
            st.metric("📝 Tamamlanan Testler", stats.get("completed_tests", 0))
            
            avg = stats.get("average_score", 0)
            if avg:
                st.metric("📊 Ortalama Puan", f"%{avg:.0f}")
        
        st.divider()
        
        if st.button("🏠 Ana Sayfa", use_container_width=True):
            st.session_state.learning_view = "list"
            st.session_state.current_workspace_id = None
            st.rerun()
    
    # Session state
    if "learning_view" not in st.session_state:
        st.session_state.learning_view = "list"
    
    # Görünüm yönlendirme
    view = st.session_state.get("learning_view", "list")
    
    if view == "list":
        render_workspace_list()
    elif view == "create_workspace":
        render_create_workspace()
    elif view == "workspace_detail":
        render_workspace_detail()


if __name__ == "__main__":
    main()
