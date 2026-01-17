"""
AI ile Öğren - Çalışma Dökümanı Oluşturucu
Enterprise Study Document Generator

Çok sayfalı, kaynakçalı, profesyonel çalışma dökümanları üretir.
"""

import json
import time
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from core.config import settings
from core.llm_manager import llm_manager
from core.vector_store import vector_store
from core.learning_workspace import (
    learning_workspace_manager, 
    StudyDocument, 
    DocumentStatus,
    SourceReference
)


@dataclass
class DocumentSection:
    """Döküman bölümü."""
    title: str
    content: str
    page_number: int
    references: List[Dict]  # Satır bazlı referanslar


class StudyDocumentGenerator:
    """
    Çalışma dökümanı oluşturucu.
    
    Özellikler:
    - Çok sayfalı döküman üretimi (max 40 sayfa)
    - Thinking/reasoning süreçleri
    - Satır bazlı kaynakça
    - Revizyon ve geliştirme
    - Streaming progress
    """
    
    # Sayfa başına ortalama kelime sayısı
    WORDS_PER_PAGE = 400
    
    # Stil şablonları
    STYLES = {
        "academic": {
            "name": "Akademik",
            "description": "Formal, akademik dil. Detaylı açıklamalar.",
            "tone": "formal ve akademik",
            "structure": "giriş, ana bölümler, sonuç formatında"
        },
        "casual": {
            "name": "Sade",
            "description": "Anlaşılır, günlük dil. Kolay okunur.",
            "tone": "samimi ve anlaşılır",
            "structure": "konuşma dilinde, örneklerle zenginleştirilmiş"
        },
        "detailed": {
            "name": "Detaylı",
            "description": "Kapsamlı, derinlemesine. Her detay açıklanır.",
            "tone": "kapsamlı ve açıklayıcı",
            "structure": "adım adım, her kavram detaylı açıklanmış"
        },
        "summary": {
            "name": "Özet",
            "description": "Kısa ve öz. Sadece önemli noktalar.",
            "tone": "özet ve net",
            "structure": "madde işaretleri, kısa paragraflar"
        },
        "exam_prep": {
            "name": "Sınav Hazırlık",
            "description": "Sınava yönelik. Önemli noktalar vurgulanır.",
            "tone": "öğretici ve vurgulayıcı",
            "structure": "önemli kavramlar, formüller, hatırlatmalar"
        }
    }
    
    def __init__(self):
        self.manager = learning_workspace_manager
    
    # Thread pool for CPU-bound LLM calls
    _executor = ThreadPoolExecutor(max_workers=2)
    
    def generate_document_sync(
        self,
        document_id: str,
        active_source_ids: List[str] = None,
        custom_instructions: str = "",
        web_search: str = "auto",
        cancel_check: callable = None
    ) -> Dict:
        """
        Çalışma dökümanı oluştur (SYNCHRONOUS - thread içinde kullanım için).
        
        Args:
            document_id: Döküman ID
            active_source_ids: Aktif kaynak ID'leri
            custom_instructions: Kullanıcının özel talimatları
            web_search: Web arama modu
            cancel_check: İptal kontrolü için callable (True döndürürse iptal)
            
        Returns:
            Sonuç dict: {"success": bool, "message": str, ...}
        """
        import traceback
        
        doc = self.manager.get_document(document_id)
        if not doc:
            return {"success": False, "message": "Döküman bulunamadı"}
        
        try:
            doc.status = DocumentStatus.GENERATING
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Üretim başladı")
            self.manager.update_document(doc)
            
            # ===== PHASE 1: PLANNING =====
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Outline oluşturuluyor...")
            self.manager.update_document(doc)
            
            outline = self._create_outline_sync(doc, custom_instructions)
            
            if cancel_check and cancel_check():
                raise Exception("İptal edildi")
            
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Outline oluşturuldu: {len(outline)} bölüm")
            self.manager.update_document(doc)
            
            # ===== PHASE 2: RESEARCH =====
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Araştırma yapılıyor...")
            self.manager.update_document(doc)
            
            research_data = self._gather_research_sync(
                doc.topic, 
                outline,
                active_source_ids,
                web_search
            )
            
            if cancel_check and cancel_check():
                raise Exception("İptal edildi")
            
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Araştırma tamamlandı: {len(research_data)} kaynak")
            self.manager.update_document(doc)
            
            # ===== PHASE 3: CONTENT GENERATION =====
            all_content = []
            all_references = []
            current_line = 1
            
            for i, section in enumerate(outline):
                if cancel_check and cancel_check():
                    raise Exception("İptal edildi")
                
                doc.generation_log.append(f"[{datetime.now().isoformat()}] Bölüm {i+1}/{len(outline)} yazılıyor: {section['title']}")
                self.manager.update_document(doc)
                
                section_content, section_refs = self._generate_section_sync(
                    doc,
                    section,
                    research_data,
                    custom_instructions,
                    current_line
                )
                
                all_content.append({
                    "title": section["title"],
                    "content": section_content,
                    "page_start": section.get("page_start", 1),
                    "page_end": section.get("page_end", 1)
                })
                
                all_references.extend(section_refs)
                current_line += len(section_content.split('\n'))
                
                doc.generation_log.append(f"[{datetime.now().isoformat()}] Bölüm tamamlandı: {section['title']}")
                self.manager.update_document(doc)
            
            # ===== PHASE 4: FINALIZE =====
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Döküman birleştiriliyor...")
            self.manager.update_document(doc)
            
            final_content = self._combine_sections(all_content)
            bibliography = self._create_bibliography(all_references)
            
            doc.content = final_content + "\n\n" + bibliography
            doc.references = all_references
            doc.outline = {"sections": outline}
            doc.status = DocumentStatus.COMPLETED
            doc.completed_at = datetime.now().isoformat()
            doc.generation_log.append(f"[{datetime.now().isoformat()}] ✅ Döküman başarıyla tamamlandı!")
            
            self.manager.update_document(doc)
            
            return {
                "success": True,
                "message": "Döküman başarıyla oluşturuldu",
                "document_id": doc.id,
                "word_count": len(final_content.split()),
                "page_count": doc.page_count,
                "references_count": len(all_references)
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"[StudyDocGenerator] Error: {error_trace}")
            
            doc.status = DocumentStatus.FAILED
            doc.generation_log.append(f"[{datetime.now().isoformat()}] ❌ HATA: {str(e)}")
            self.manager.update_document(doc)
            
            return {
                "success": False,
                "message": f"Hata: {str(e)}",
                "error": str(e),
                "trace": error_trace
            }
    
    def _create_outline_sync(self, doc: StudyDocument, custom_instructions: str) -> List[Dict]:
        """Synchronous outline oluştur."""
        style_info = self.STYLES.get(doc.style, self.STYLES["detailed"])
        words_needed = doc.page_count * self.WORDS_PER_PAGE
        
        prompt = f"""Aşağıdaki konu için {doc.page_count} sayfalık bir çalışma dökümanının içerik planını oluştur.

KONU: {doc.topic}
BAŞLIK: {doc.title}
SAYFA SAYISI: {doc.page_count}
TOPLAM KELİME HEDEFİ: ~{words_needed} kelime
YAZI STİLİ: {style_info['name']} - {style_info['description']}

{f'KULLANICI TALİMATLARI: {custom_instructions}' if custom_instructions else ''}

JSON formatında döndür:
[
  {{"title": "Giriş", "subtopics": ["..."], "page_start": 1, "page_end": 1, "key_points": ["..."]}},
  ...
]

Sadece JSON döndür, başka açıklama ekleme."""
        
        response = llm_manager.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                parsed = json.loads(json_match.group(0))
            else:
                parsed = json.loads(response)
            
            if isinstance(parsed, dict):
                for key in ["sections", "outline", "document_structure"]:
                    if key in parsed:
                        parsed = parsed[key]
                        break
            
            normalized = []
            for section in parsed:
                if isinstance(section, dict):
                    normalized.append({
                        "title": section.get("title", section.get("section_title", "Bölüm")),
                        "subtopics": section.get("subtopics", []),
                        "page_start": section.get("page_start", 1),
                        "page_end": section.get("page_end", 1),
                        "key_points": section.get("key_points", [])
                    })
            
            return normalized if normalized else self._default_outline(doc)
        except Exception as e:
            print(f"[Outline Parse Error] {e}")
            return self._default_outline(doc)
    
    def _gather_research_sync(
        self,
        topic: str,
        outline: List[Dict],
        active_source_ids: List[str] = None,
        web_search: str = "auto"
    ) -> List[Dict]:
        """Synchronous araştırma yap."""
        all_research = []
        seen_content = set()
        
        search_queries = [topic]
        for section in outline:
            search_queries.append(section["title"])
            search_queries.extend(section.get("subtopics", [])[:3])
        
        search_queries = list(set(search_queries))[:10]
        
        # RAG araştırma
        for query in search_queries:
            try:
                results = vector_store.search_with_scores(
                    query=query,
                    n_results=5,
                    score_threshold=0.3
                )
                
                for result in results:
                    content = result.get("document", "")
                    content_hash = hash(content[:200])
                    
                    if content_hash in seen_content:
                        continue
                    seen_content.add(content_hash)
                    
                    metadata = result.get("metadata", {})
                    
                    all_research.append({
                        "content": content,
                        "source": metadata.get("original_filename", metadata.get("filename", "Bilinmeyen")),
                        "source_id": metadata.get("document_id", ""),
                        "page": metadata.get("page"),
                        "score": result.get("score", 0),
                        "type": "local"
                    })
            except Exception as e:
                print(f"[RAG Error] {query}: {e}")
        
        # Web araştırma (opsiyonel)
        if web_search == "on" or (web_search == "auto" and len(all_research) < 5):
            try:
                from tools.web_search_engine import PremiumWebSearchEngine
                web_engine = PremiumWebSearchEngine()
                
                for query in search_queries[:2]:
                    try:
                        web_result = web_engine.search(query, num_results=3)
                        
                        if hasattr(web_result, 'results'):
                            for wr in web_result.results:
                                content = getattr(wr, 'full_content', None) or getattr(wr, 'snippet', '') or ''
                                if not content:
                                    continue
                                
                                content_hash = hash(content[:200])
                                if content_hash in seen_content:
                                    continue
                                seen_content.add(content_hash)
                                
                                all_research.append({
                                    "content": content[:1500],
                                    "source": getattr(wr, 'title', '') or getattr(wr, 'url', 'Web'),
                                    "source_id": getattr(wr, 'url', ''),
                                    "page": None,
                                    "score": getattr(wr, 'reliability_score', 0.5),
                                    "type": "web"
                                })
                    except Exception as e:
                        print(f"[Web Search Error] {query}: {e}")
            except ImportError:
                pass
            except Exception as e:
                print(f"[Web Search Import Error] {e}")
        
        all_research.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_research[:30]
    
    def _generate_section_sync(
        self,
        doc: StudyDocument,
        section: Dict,
        research_data: List[Dict],
        custom_instructions: str,
        start_line: int
    ) -> tuple:
        """Synchronous bölüm içeriği oluştur."""
        style_info = self.STYLES.get(doc.style, self.STYLES["detailed"])
        
        # Bu bölüm için kaynak filtrele
        section_keywords = [section["title"].lower()]
        section_keywords.extend([s.lower() for s in section.get("subtopics", [])])
        
        relevant_sources = []
        for r in research_data:
            content_lower = r["content"].lower()
            if any(kw in content_lower for kw in section_keywords):
                relevant_sources.append(r)
        
        if len(relevant_sources) < 3:
            relevant_sources = research_data[:8]
        
        # Kaynak metni
        sources_text = ""
        for i, src in enumerate(relevant_sources[:8], 1):
            sources_text += f"\n[KAYNAK {i}] ({src['source']}):\n{src['content'][:600]}\n"
        
        page_count = section.get("page_end", 1) - section.get("page_start", 1) + 1
        word_target = page_count * self.WORDS_PER_PAGE
        
        prompt = f"""Bu bölüm için çalışma dökümanı içeriği yaz.

DÖKÜMAN: {doc.title}
BÖLÜM: {section['title']}
ALT KONULAR: {', '.join(section.get('subtopics', []))}
YAZI STİLİ: {style_info['tone']}
KELİME HEDEFİ: ~{word_target} kelime

{f'TALIMATLAR: {custom_instructions}' if custom_instructions else ''}

KAYNAKLAR:
{sources_text}

Markdown formatında, akıcı ve öğretici içerik yaz. Kaynaklara [KAYNAK X] ile atıfta bulun."""

        content = llm_manager.generate(prompt)
        
        # Referansları çıkar
        import re
        references = []
        ref_pattern = r'\[KAYNAK (\d+)\]'
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, start=start_line):
            matches = re.findall(ref_pattern, line)
            for match in matches:
                src_idx = int(match) - 1
                if 0 <= src_idx < len(relevant_sources):
                    src = relevant_sources[src_idx]
                    references.append({
                        "source_name": src["source"],
                        "source_id": src.get("source_id", ""),
                        "page": src.get("page"),
                        "line_number": line_num
                    })
        
        clean_content = re.sub(r'\[KAYNAK \d+\]', '', content)
        return clean_content.strip(), references
    
    def _combine_sections(self, sections: List[Dict]) -> str:
        """Bölümleri birleştir."""
        content_parts = []
        for section in sections:
            content_parts.append(f"## {section['title']}\n\n{section['content']}")
        return "\n\n---\n\n".join(content_parts)
    
    async def generate_document(
        self,
        document_id: str,
        active_source_ids: List[str] = None,
        custom_instructions: str = "",
        web_search: str = "auto"  # off, auto, on
    ) -> AsyncGenerator[Dict, None]:
        """
        Çalışma dökümanı oluştur (streaming).
        
        Args:
            document_id: Döküman ID
            active_source_ids: Aktif kaynak ID'leri (RAG filtresi)
            custom_instructions: Kullanıcının özel talimatları
            web_search: Web arama modu - "off", "auto", "on"
            
        Yields:
            Progress updates ve içerik
        """
        doc = self.manager.get_document(document_id)
        if not doc:
            yield {"type": "error", "message": "Döküman bulunamadı"}
            return
        
        try:
            # ===== PHASE 1: PLANNING =====
            yield {
                "type": "status",
                "phase": "planning",
                "message": "📋 Döküman planlanıyor...",
                "progress": 5
            }
            
            # Konuya göre içerik planı oluştur
            outline = await self._create_outline(doc, custom_instructions)
            
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Outline oluşturuldu: {len(outline)} bölüm")
            self.manager.update_document(doc)
            
            yield {
                "type": "outline",
                "data": outline,
                "message": f"📝 {len(outline)} bölümlük plan hazırlandı",
                "progress": 10
            }
            
            # ===== PHASE 2: RESEARCH =====
            # Web search moduna göre mesaj
            web_msg = ""
            if web_search == "on":
                web_msg = " (🌐 Web dahil)"
            elif web_search == "auto":
                web_msg = " (🤖 Gerekirse web)"
            
            yield {
                "type": "status",
                "phase": "research",
                "message": f"🔍 Kaynaklar araştırılıyor{web_msg}...",
                "progress": 15
            }
            
            # RAG ile kaynak topla (web search modu ile)
            research_data = await self._gather_research(
                doc.topic, 
                outline,
                active_source_ids,
                web_search  # Web search modunu aktar
            )
            
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Araştırma tamamlandı: {len(research_data)} kaynak")
            self.manager.update_document(doc)
            
            yield {
                "type": "research",
                "sources_count": len(research_data),
                "message": f"📚 {len(research_data)} kaynak bulundu",
                "progress": 25
            }
            
            # ===== PHASE 3: CONTENT GENERATION =====
            all_content = []
            all_references = []
            current_line = 1
            
            total_sections = len(outline)
            
            for i, section in enumerate(outline):
                section_progress = 25 + int((i / total_sections) * 60)
                
                yield {
                    "type": "status",
                    "phase": "generating",
                    "message": f"✍️ Bölüm {i+1}/{total_sections}: {section['title']}",
                    "progress": section_progress
                }
                
                # Bölüm içeriği oluştur
                section_content, section_refs = await self._generate_section(
                    doc,
                    section,
                    research_data,
                    custom_instructions,
                    current_line
                )
                
                all_content.append({
                    "title": section["title"],
                    "content": section_content,
                    "page_start": section.get("page_start", 1),
                    "page_end": section.get("page_end", 1)
                })
                
                all_references.extend(section_refs)
                current_line += len(section_content.split('\n'))
                
                # Streaming content update
                yield {
                    "type": "section_complete",
                    "section_index": i,
                    "section_title": section["title"],
                    "content_preview": section_content[:500] + "..." if len(section_content) > 500 else section_content,
                    "progress": section_progress + 5
                }
                
                doc.generation_log.append(f"[{datetime.now().isoformat()}] Bölüm tamamlandı: {section['title']}")
                self.manager.update_document(doc)
            
            # ===== PHASE 4: REFINEMENT =====
            yield {
                "type": "status",
                "phase": "refining",
                "message": "🔧 Döküman düzenleniyor ve iyileştiriliyor...",
                "progress": 88
            }
            
            # Final düzenleme
            final_content = await self._refine_document(all_content, doc.style)
            
            # ===== PHASE 5: BIBLIOGRAPHY =====
            yield {
                "type": "status",
                "phase": "bibliography",
                "message": "📖 Kaynakça oluşturuluyor...",
                "progress": 95
            }
            
            # Kaynakça oluştur
            bibliography = self._create_bibliography(all_references)
            
            # ===== FINALIZE =====
            doc.content = final_content + "\n\n" + bibliography
            doc.references = all_references
            doc.status = DocumentStatus.COMPLETED
            doc.completed_at = datetime.now().isoformat()
            doc.generation_log.append(f"[{datetime.now().isoformat()}] Döküman tamamlandı")
            
            self.manager.update_document(doc)
            
            yield {
                "type": "complete",
                "message": "✅ Döküman başarıyla oluşturuldu!",
                "progress": 100,
                "document_id": doc.id,
                "word_count": len(final_content.split()),
                "page_count": doc.page_count,
                "references_count": len(all_references)
            }
            
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.generation_log.append(f"[{datetime.now().isoformat()}] HATA: {str(e)}")
            self.manager.update_document(doc)
            
            yield {
                "type": "error",
                "message": f"❌ Hata oluştu: {str(e)}",
                "progress": -1
            }
    
    async def _create_outline(
        self, 
        doc: StudyDocument,
        custom_instructions: str
    ) -> List[Dict]:
        """Döküman için içerik planı oluştur."""
        
        style_info = self.STYLES.get(doc.style, self.STYLES["detailed"])
        words_needed = doc.page_count * self.WORDS_PER_PAGE
        
        prompt = f"""Aşağıdaki konu için {doc.page_count} sayfalık bir çalışma dökümanının içerik planını oluştur.

KONU: {doc.topic}
BAŞLIK: {doc.title}
SAYFA SAYISI: {doc.page_count}
TOPLAM KELİME HEDEFİ: ~{words_needed} kelime
YAZI STİLİ: {style_info['name']} - {style_info['description']}

{f'KULLANICI TALİMATLARI: {custom_instructions}' if custom_instructions else ''}

Her bölüm için şunları belirt:
1. Bölüm başlığı
2. Alt başlıklar
3. Tahmini sayfa aralığı
4. Kapsanacak ana noktalar

JSON formatında döndür:
```json
[
  {{
    "title": "Bölüm Başlığı",
    "subtopics": ["Alt konu 1", "Alt konu 2"],
    "page_start": 1,
    "page_end": 2,
    "key_points": ["Nokta 1", "Nokta 2"]
  }}
]
```

Önemli:
- Giriş ve Sonuç bölümleri mutlaka olmalı
- Her bölüm mantıksal akış içinde olmalı
- Sayfa dağılımı dengeli olmalı
- Toplam sayfa sayısı {doc.page_count} olmalı"""
        
        # Run LLM in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self._executor,
            lambda: llm_manager.generate(prompt)
        )
        
        # JSON parse
        try:
            # JSON bloğunu bul
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                parsed = json.loads(response)
            
            # LLM bazen dict içinde "document_structure" ile döndürür
            if isinstance(parsed, dict):
                if "document_structure" in parsed:
                    outline = parsed["document_structure"]
                elif "sections" in parsed:
                    outline = parsed["sections"]
                elif "outline" in parsed:
                    outline = parsed["outline"]
                else:
                    # Dict'i listeye çevir
                    outline = list(parsed.values())[0] if parsed else []
            else:
                outline = parsed
            
            # Alanları normalize et (section_title -> title)
            normalized = []
            for section in outline:
                if isinstance(section, dict):
                    normalized.append({
                        "title": section.get("title") or section.get("section_title", "Bölüm"),
                        "subtopics": section.get("subtopics", []),
                        "page_start": section.get("page_start", 1),
                        "page_end": section.get("page_end", 1),
                        "key_points": section.get("key_points", [])
                    })
            
            return normalized if normalized else self._default_outline(doc)
        except (json.JSONDecodeError, Exception):
            return self._default_outline(doc)
    
    def _default_outline(self, doc: StudyDocument) -> List[Dict]:
        """Fallback outline oluştur."""
        return [
            {"title": "Giriş", "subtopics": [doc.topic], "page_start": 1, "page_end": 1, "key_points": []},
            {"title": "Ana İçerik", "subtopics": [doc.topic], "page_start": 2, "page_end": doc.page_count - 1, "key_points": []},
            {"title": "Sonuç", "subtopics": ["Özet"], "page_start": doc.page_count, "page_end": doc.page_count, "key_points": []}
        ]
    
    async def _gather_research(
        self,
        topic: str,
        outline: List[Dict],
        active_source_ids: List[str] = None,
        web_search: str = "auto"  # off, auto, on
    ) -> List[Dict]:
        """RAG ve Web ile kaynak topla."""
        
        all_research = []
        seen_content = set()
        
        # Her bölüm için arama yap
        search_queries = [topic]
        for section in outline:
            search_queries.append(section["title"])
            search_queries.extend(section.get("subtopics", []))
            search_queries.extend(section.get("key_points", []))
        
        # Unique queries
        search_queries = list(set(search_queries))[:15]  # Max 15 sorgu
        
        # ========== RAG ARAŞTIRMA ==========
        for query in search_queries:
            try:
                # RAG araması
                results = vector_store.search_with_scores(
                    query=query,
                    n_results=5,
                    score_threshold=0.3
                )
                
                for result in results:
                    content = result.get("document", "")
                    content_hash = hash(content[:200])
                    
                    if content_hash in seen_content:
                        continue
                    seen_content.add(content_hash)
                    
                    metadata = result.get("metadata", {})
                    source_id = metadata.get("document_id", "")
                    
                    # Aktif kaynak filtresi
                    if active_source_ids and source_id not in active_source_ids:
                        # Kaynak ID yoksa filename'e bak
                        filename = metadata.get("original_filename", metadata.get("filename", ""))
                        if not any(sid in filename for sid in active_source_ids):
                            continue
                    
                    all_research.append({
                        "content": content,
                        "source": metadata.get("original_filename", metadata.get("filename", "Bilinmeyen")),
                        "source_id": source_id,
                        "page": metadata.get("page"),
                        "score": result.get("score", 0),
                        "query": query,
                        "type": "local"  # Yerel kaynak
                    })
            except Exception as e:
                print(f"RAG research error for '{query}': {e}")
        
        # ========== WEB ARAŞTIRMA ==========
        do_web_search = False
        
        if web_search == "on":
            do_web_search = True
        elif web_search == "auto":
            # Yerel kaynaklar yetersizse web'e başvur
            if len(all_research) < 10:
                do_web_search = True
                print(f"Auto web search: {len(all_research)} yerel kaynak bulundu, web araması yapılıyor...")
        
        if do_web_search:
            try:
                # Web search modülünü import et
                from tools.web_search_engine import PremiumWebSearchEngine
                
                web_engine = PremiumWebSearchEngine()
                
                # Ana konu için web araması
                web_queries = [topic] + search_queries[:5]  # İlk 5 sorgu
                
                for query in web_queries[:3]:  # Max 3 web sorgusu
                    try:
                        web_result = web_engine.search(query, num_results=5)
                        
                        for wr in web_result.results:
                            url = wr.url
                            content = wr.full_content or wr.snippet or ""
                            
                            if not content:
                                continue
                            
                            content_hash = hash(content[:200])
                            if content_hash in seen_content:
                                continue
                            seen_content.add(content_hash)
                            
                            all_research.append({
                                "content": content[:2000],  # Max 2000 karakter
                                "source": wr.title or url,
                                "source_id": url,
                                "page": None,
                                "score": wr.reliability_score or 0.5,
                                "query": query,
                                "type": "web",  # Web kaynağı
                                "url": url
                            })
                    except Exception as e:
                        print(f"Web search error for '{query}': {e}")
                        
            except ImportError:
                print("Web search modülü bulunamadı, sadece RAG kullanılıyor")
            except Exception as e:
                print(f"Web search genel hata: {e}")
        
        # Skora göre sırala
        all_research.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return all_research[:50]  # Max 50 kaynak
    
    async def _generate_section(
        self,
        doc: StudyDocument,
        section: Dict,
        research_data: List[Dict],
        custom_instructions: str,
        start_line: int
    ) -> tuple:
        """Bölüm içeriği oluştur."""
        
        style_info = self.STYLES.get(doc.style, self.STYLES["detailed"])
        
        # Bu bölüm için relevand kaynakları filtrele
        section_keywords = [section["title"].lower()]
        section_keywords.extend([s.lower() for s in section.get("subtopics", [])])
        section_keywords.extend([s.lower() for s in section.get("key_points", [])])
        
        relevant_sources = []
        for r in research_data:
            content_lower = r["content"].lower()
            if any(kw in content_lower for kw in section_keywords):
                relevant_sources.append(r)
        
        # En az 5 kaynak
        if len(relevant_sources) < 5:
            relevant_sources = research_data[:10]
        
        # Kaynak metni oluştur
        sources_text = ""
        for i, src in enumerate(relevant_sources[:10], 1):
            sources_text += f"\n[KAYNAK {i}] ({src['source']}"
            if src.get('page'):
                sources_text += f", s.{src['page']}"
            sources_text += f"):\n{src['content'][:800]}\n"
        
        # Sayfa hedefi
        page_count = section.get("page_end", 1) - section.get("page_start", 1) + 1
        word_target = page_count * self.WORDS_PER_PAGE
        
        prompt = f"""Aşağıdaki bölüm için çalışma dökümanı içeriği yaz.

DÖKÜMAN BAŞLIĞI: {doc.title}
KONU: {doc.topic}
BÖLÜM: {section['title']}
ALT KONULAR: {', '.join(section.get('subtopics', []))}
ANA NOKTALAR: {', '.join(section.get('key_points', []))}

YAZI STİLİ: {style_info['tone']}
YAPI: {style_info['structure']}
KELİME HEDEFİ: ~{word_target} kelime

{f'KULLANICI TALİMATLARI: {custom_instructions}' if custom_instructions else ''}

KAYNAKLAR:
{sources_text}

KURALLAR:
1. Kaynaklardaki bilgileri kullan ve [KAYNAK X] şeklinde referans ver
2. Akıcı ve öğretici bir dil kullan
3. Gerekirse örnekler ekle
4. Markdown formatında yaz (başlıklar, listeler, vurgular)
5. İçerik metin içinde referans belirtmeli: "... bu konuda [KAYNAK 1] belirtmektedir ki..."
6. Hedef kelime sayısına yaklaş

Şimdi bu bölümün içeriğini yaz:"""

        # Run LLM in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            self._executor,
            lambda: llm_manager.generate(prompt)
        )
        
        # Referansları çıkar
        import re
        references = []
        ref_pattern = r'\[KAYNAK (\d+)\]'
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, start=start_line):
            matches = re.findall(ref_pattern, line)
            for match in matches:
                src_idx = int(match) - 1
                if 0 <= src_idx < len(relevant_sources):
                    src = relevant_sources[src_idx]
                    references.append({
                        "source_name": src["source"],
                        "source_id": src.get("source_id", ""),
                        "page": src.get("page"),
                        "line_number": line_num,
                        "line_content": line[:100]
                    })
        
        # [KAYNAK X] ifadelerini temizle
        clean_content = re.sub(r'\[KAYNAK \d+\]', '', content)
        
        return clean_content.strip(), references
    
    async def _refine_document(
        self,
        sections: List[Dict],
        style: str
    ) -> str:
        """Dökümanı düzenle ve birleştir."""
        
        full_content = ""
        
        for section in sections:
            full_content += f"\n\n## {section['title']}\n\n"
            full_content += section['content']
        
        # Basit düzenleme (büyük LLM çağrısı yapmadan)
        # Tekrar eden boşlukları temizle
        import re
        full_content = re.sub(r'\n{3,}', '\n\n', full_content)
        full_content = re.sub(r' {2,}', ' ', full_content)
        
        return full_content.strip()
    
    def _create_bibliography(self, references: List[Dict]) -> str:
        """Satır bazlı kaynakça oluştur."""
        
        if not references:
            return ""
        
        bibliography = "\n\n---\n\n# 📚 KAYNAKÇA\n\n"
        bibliography += "Bu çalışma dökümanında kullanılan kaynaklar ve ilgili satırlar:\n\n"
        
        # Kaynağa göre grupla
        sources_map = {}
        for ref in references:
            source_name = ref.get("source_name", "Bilinmeyen")
            if source_name not in sources_map:
                sources_map[source_name] = {
                    "page": ref.get("page"),
                    "lines": []
                }
            sources_map[source_name]["lines"].append(ref.get("line_number", 0))
        
        # Kaynakları listele
        for i, (source_name, info) in enumerate(sources_map.items(), 1):
            lines = sorted(set(info["lines"]))
            lines_str = ", ".join(str(l) for l in lines[:10])
            if len(lines) > 10:
                lines_str += f" ve {len(lines) - 10} satır daha"
            
            bibliography += f"**[{i}]** {source_name}"
            if info.get("page"):
                bibliography += f" (Sayfa {info['page']})"
            bibliography += f"\n   → Kullanıldığı satırlar: {lines_str}\n\n"
        
        return bibliography
    
    def get_available_styles(self) -> Dict:
        """Kullanılabilir stilleri döndür."""
        return self.STYLES


# Singleton instance
study_document_generator = StudyDocumentGenerator()
