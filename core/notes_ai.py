"""
🧠 Notes AI - Not Yapay Zeka Özellikleri
Not özetleme, etiket önerisi, ilgili not bulma, flashcard üretimi ve daha fazlası.
"""

import json
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from core.logger import get_logger
from core.notes_manager import NotesManager, Note, notes_manager

logger = get_logger("notes_ai")


@dataclass
class Flashcard:
    """Flashcard veri modeli."""
    id: str
    front: str  # Soru
    back: str   # Cevap
    note_id: str
    difficulty: str = "medium"  # easy, medium, hard
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class NoteRelation:
    """Not ilişkisi veri modeli."""
    from_note_id: str
    to_note_id: str
    relation_type: str = "link"  # link, similar, reference
    strength: float = 1.0  # 0-1 arası benzerlik/ilişki gücü
    
    def to_dict(self) -> Dict:
        return asdict(self)


class NotesAI:
    """
    Not Yapay Zeka Sınıfı
    
    AI destekli not özellikleri:
    - Not özetleme
    - Akıllı etiket önerisi
    - İlgili not bulma (semantik)
    - Soru-cevap (RAG)
    - Not zenginleştirme
    - Flashcard üretimi
    """
    
    def __init__(self, llm_service=None, rag_service=None, notes_manager: NotesManager = None):
        self.llm_service = llm_service
        self.rag_service = rag_service
        self._notes_manager = notes_manager
        
        # Lazy load LLM service
        if not self.llm_service:
            try:
                from core.llm_manager import get_llm_manager
                self.llm_service = get_llm_manager()
            except Exception as e:
                logger.warning(f"LLM servisi yüklenemedi: {e}")

    @property
    def notes_manager(self) -> NotesManager:
        """Lazy load notes_manager from singleton if not provided."""
        if self._notes_manager is None:
            from core.notes_manager import notes_manager as nm
            self._notes_manager = nm
        return self._notes_manager
    
    # ==================== AI ÖZETLEMEAsync ====================
    
    async def summarize_note(self, note_id: str, max_length: int = 200) -> Dict[str, Any]:
        """
        Notu AI ile özetle.
        
        Returns:
            {
                "summary": "Özet metni...",
                "key_points": ["Nokta 1", "Nokta 2"],
                "word_count": 150
            }
        """
        note = self.notes_manager.get_note(note_id)
        if not note:
            return {"error": "Not bulunamadı"}
        
        if not note.content or len(note.content.strip()) < 50:
            return {
                "summary": note.content,
                "key_points": [],
                "word_count": len(note.content.split())
            }
        
        if self.llm_service:
            try:
                prompt = f"""Aşağıdaki notu özetle. Maksimum {max_length} kelime kullan.

**Not Başlığı:** {note.title}
**Not İçeriği:**
{note.content}

Yanıtını JSON formatında ver:
{{
    "summary": "Özet metni...",
    "key_points": ["Önemli nokta 1", "Önemli nokta 2", "Önemli nokta 3"]
}}"""
                
                response = await self.llm_service.generate(prompt, json_mode=True)
                result = json.loads(response)
                result["word_count"] = len(note.content.split())
                return result
            except Exception as e:
                logger.error(f"AI özetleme hatası: {e}")
        
        # Fallback: Basit özetleme
        sentences = note.content.split('.')
        summary = '. '.join(sentences[:3]) + '.'
        return {
            "summary": summary[:500],
            "key_points": [s.strip() for s in sentences[:3] if s.strip()],
            "word_count": len(note.content.split())
        }
    
    # ==================== AKILLI ETİKET ÖNERİSİ ====================
    
    async def suggest_tags(self, note_id: str = None, content: str = None, max_tags: int = 5) -> List[str]:
        """
        Not içeriğine göre etiket öner.
        
        Args:
            note_id: Not ID (opsiyonel)
            content: Not içeriği (opsiyonel)
            max_tags: Maksimum etiket sayısı
        
        Returns:
            ["etiket1", "etiket2", ...]
        """
        if note_id:
            note = self.notes_manager.get_note(note_id)
            if note:
                content = f"{note.title} {note.content}"
        
        if not content or len(content.strip()) < 20:
            return []
        
        if self.llm_service:
            try:
                prompt = f"""Aşağıdaki metin için en uygun {max_tags} etiket öner.
Etiketler kısa, tek kelime veya iki kelimelik olmalı.

**Metin:**
{content[:2000]}

Yanıtını JSON formatında ver:
{{
    "tags": ["etiket1", "etiket2", "etiket3"]
}}"""
                
                response = await self.llm_service.generate(prompt, json_mode=True)
                result = json.loads(response)
                return result.get("tags", [])[:max_tags]
            except Exception as e:
                logger.error(f"Etiket önerisi hatası: {e}")
        
        # Fallback: Basit anahtar kelime çıkarma
        words = content.lower().split()
        word_freq = {}
        stop_words = {"ve", "veya", "ama", "ile", "için", "bir", "bu", "şu", "de", "da", "ki", "mi", "the", "a", "an", "is", "are", "was"}
        
        for word in words:
            word = re.sub(r'[^\w]', '', word)
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:max_tags]]
    
    # ==================== İLGİLİ NOT BULMA ====================
    
    async def find_related_notes(self, note_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Bir nota semantik olarak benzer notları bul.
        
        Returns:
            [{"note": Note, "similarity": 0.85}, ...]
        """
        note = self.notes_manager.get_note(note_id)
        if not note:
            return []
        
        all_notes = self.notes_manager.get_all_notes()
        if len(all_notes) <= 1:
            return []
        
        results = []
        query_text = f"{note.title} {note.content}"
        query_words = set(query_text.lower().split())
        
        for other_note in all_notes:
            if other_note.id == note_id:
                continue
            
            other_text = f"{other_note.title} {other_note.content}"
            other_words = set(other_text.lower().split())
            
            # Jaccard benzerliği
            intersection = len(query_words & other_words)
            union = len(query_words | other_words)
            similarity = intersection / union if union > 0 else 0
            
            # Tag benzerliği ekle
            if note.tags and other_note.tags:
                tag_intersection = len(set(note.tags) & set(other_note.tags))
                similarity += tag_intersection * 0.1
            
            if similarity > 0.1:
                results.append({
                    "note": other_note.to_dict(),
                    "similarity": round(min(similarity, 1.0), 2)
                })
        
        # Benzerliğe göre sırala
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:max_results]
    
    # ==================== NOT ZENGİNLEŞTİRME ====================
    
    async def enrich_note(self, note_id: str) -> Dict[str, Any]:
        """
        Notu AI ile zenginleştir - eksik bilgileri tamamla.
        
        Returns:
            {
                "enriched_content": "Zenginleştirilmiş içerik...",
                "added_sections": ["Tanım", "Örnekler"],
                "suggested_links": ["ilgili konu 1", "ilgili konu 2"]
            }
        """
        note = self.notes_manager.get_note(note_id)
        if not note:
            return {"error": "Not bulunamadı"}
        
        if self.llm_service:
            try:
                prompt = f"""Aşağıdaki notu zenginleştir. Eksik bilgileri ekle, kavramları açıkla, örnekler ver.

**Not Başlığı:** {note.title}
**Mevcut İçerik:**
{note.content}

Yanıtını JSON formatında ver:
{{
    "enriched_content": "Zenginleştirilmiş içerik (markdown formatında)...",
    "added_sections": ["Eklenen bölüm isimleri"],
    "suggested_links": ["Araştırılması önerilen ilgili konular"]
}}"""
                
                response = await self.llm_service.generate(prompt, json_mode=True)
                return json.loads(response)
            except Exception as e:
                logger.error(f"Not zenginleştirme hatası: {e}")
        
        return {
            "enriched_content": note.content,
            "added_sections": [],
            "suggested_links": []
        }
    
    # ==================== FLASHCARD ÜRETİMİ ====================
    
    async def generate_flashcards(self, note_id: str, count: int = 5) -> List[Flashcard]:
        """
        Nottan flashcard (çalışma kartı) üret.
        
        Returns:
            [Flashcard, ...]
        """
        import uuid
        
        note = self.notes_manager.get_note(note_id)
        if not note:
            return []
        
        flashcards = []
        
        if self.llm_service:
            try:
                prompt = f"""Aşağıdaki nottan {count} adet flashcard (çalışma kartı) oluştur.
Her kart bir soru ve cevap içermeli.

**Not Başlığı:** {note.title}
**Not İçeriği:**
{note.content}

Yanıtını JSON formatında ver:
{{
    "flashcards": [
        {{"front": "Soru 1?", "back": "Cevap 1", "difficulty": "easy"}},
        {{"front": "Soru 2?", "back": "Cevap 2", "difficulty": "medium"}},
        {{"front": "Soru 3?", "back": "Cevap 3", "difficulty": "hard"}}
    ]
}}

difficulty: easy, medium, hard olabilir."""
                
                response = await self.llm_service.generate(prompt, json_mode=True)
                result = json.loads(response)
                
                for fc_data in result.get("flashcards", []):
                    flashcard = Flashcard(
                        id=str(uuid.uuid4()),
                        front=fc_data.get("front", ""),
                        back=fc_data.get("back", ""),
                        note_id=note_id,
                        difficulty=fc_data.get("difficulty", "medium")
                    )
                    flashcards.append(flashcard)
                
                return flashcards
            except Exception as e:
                logger.error(f"Flashcard üretim hatası: {e}")
        
        # Fallback: Basit flashcard üretimi
        sentences = [s.strip() for s in note.content.split('.') if len(s.strip()) > 20]
        for i, sentence in enumerate(sentences[:count]):
            flashcard = Flashcard(
                id=str(uuid.uuid4()),
                front=f"{note.title} hakkında ne biliyorsun? (Konu {i+1})",
                back=sentence,
                note_id=note_id,
                difficulty="medium"
            )
            flashcards.append(flashcard)
        
        return flashcards
    
    # ==================== SORU-CEVAP (RAG) ====================
    
    async def ask_notes(
        self, 
        question: str, 
        note_ids: List[str] = None,
        include_all: bool = False
    ) -> Dict[str, Any]:
        """
        Notlara soru sor - RAG tabanlı soru-cevap.
        
        Args:
            question: Soru
            note_ids: Belirli notlar (opsiyonel)
            include_all: Tüm notları dahil et
        
        Returns:
            {
                "answer": "Cevap...",
                "sources": ["not1_id", "not2_id"],
                "confidence": 0.85
            }
        """
        # Notları topla
        if note_ids:
            notes = [self.notes_manager.get_note(nid) for nid in note_ids]
            notes = [n for n in notes if n]
        elif include_all:
            notes = self.notes_manager.get_all_notes()
        else:
            # Arama yap
            notes = self.notes_manager.search_notes(question)
        
        if not notes:
            return {
                "answer": "Bu konuda not bulunamadı.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Context oluştur
        context = ""
        source_ids = []
        for note in notes[:5]:  # Max 5 not
            context += f"## {note.title}\n{note.content}\n\n"
            source_ids.append(note.id)
        
        if self.llm_service:
            try:
                prompt = f"""Aşağıdaki notlara dayanarak soruyu cevapla.
Sadece notlarda bulunan bilgileri kullan.

**Notlar:**
{context}

**Soru:** {question}

Yanıtını JSON formatında ver:
{{
    "answer": "Detaylı cevap...",
    "confidence": 0.85
}}

confidence: 0-1 arası, cevabın notlara dayalı güvenilirliği."""
                
                response = await self.llm_service.generate(prompt, json_mode=True)
                result = json.loads(response)
                result["sources"] = source_ids
                return result
            except Exception as e:
                logger.error(f"RAG soru-cevap hatası: {e}")
        
        # Fallback
        return {
            "answer": f"Bu konuda {len(notes)} not bulundu. İlk not: {notes[0].title}",
            "sources": source_ids,
            "confidence": 0.5
        }
    
    # ==================== LİNK ÇIKARMA ====================
    
    def extract_wiki_links(self, content: str) -> List[str]:
        """
        Not içeriğinden [[wiki-style]] linkleri çıkar.
        
        Returns:
            ["Not Adı 1", "Not Adı 2"]
        """
        pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(pattern, content)
        return list(set(matches))
    
    def find_note_by_title(self, title: str) -> Optional[Note]:
        """
        Başlığa göre not bul.
        """
        all_notes = self.notes_manager.get_all_notes()
        title_lower = title.lower().strip()
        
        for note in all_notes:
            if note.title.lower().strip() == title_lower:
                return note
        
        return None


# ==================== SINGLETON ====================

_notes_ai: Optional[NotesAI] = None

def get_notes_ai(notes_manager=None) -> NotesAI:
    """NotesAI singleton instance'ı döndür."""
    global _notes_ai
    if _notes_ai is None:
        if notes_manager is None:
            from core.notes_manager import notes_manager as nm
            notes_manager = nm
        _notes_ai = NotesAI(notes_manager=notes_manager)
    return _notes_ai
