"""
AI ile Öğren - Test Oluşturucu
Enterprise Test Generator

NotebookLM tarzı interaktif testler oluşturur.
"""

import json
import re
import uuid
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime

from core.config import settings
from core.llm_manager import llm_manager
from core.vector_store import vector_store
from core.learning_workspace import (
    learning_workspace_manager,
    Test,
    TestQuestion,
    TestType,
    TestStatus
)


class TestGenerator:
    """
    Test oluşturucu.
    
    Özellikler:
    - Çoktan seçmeli, doğru/yanlış, boşluk doldurma, kısa cevap
    - Zorluk seviyeleri (kolay, orta, zor, karışık)
    - Kaynak bazlı soru üretimi
    - Açıklama ve feedback
    - Anlamadığını sor özelliği
    """
    
    # Soru türü şablonları
    QUESTION_TEMPLATES = {
        TestType.MULTIPLE_CHOICE: {
            "name": "Çoktan Seçmeli",
            "description": "4 seçenekli, tek doğru cevaplı sorular",
            "option_count": 4
        },
        TestType.TRUE_FALSE: {
            "name": "Doğru/Yanlış",
            "description": "İfadenin doğruluğunu değerlendirme",
            "option_count": 2
        },
        TestType.FILL_BLANK: {
            "name": "Boşluk Doldurma",
            "description": "Eksik kelime/kavramı tamamlama",
            "option_count": 0
        },
        TestType.SHORT_ANSWER: {
            "name": "Kısa Cevap",
            "description": "1-3 cümlelik açık uçlu sorular",
            "option_count": 0
        },
        TestType.MIXED: {
            "name": "Karışık",
            "description": "Tüm soru türlerinden karışık",
            "option_count": 0
        }
    }
    
    DIFFICULTY_LEVELS = {
        "easy": {
            "name": "Kolay",
            "description": "Temel kavramlar, tanımlar",
            "complexity": "basit ve doğrudan"
        },
        "medium": {
            "name": "Orta",
            "description": "Uygulama ve anlama gerektiren",
            "complexity": "orta düzey analiz gerektiren"
        },
        "hard": {
            "name": "Zor",
            "description": "Analiz, sentez ve değerlendirme",
            "complexity": "derinlemesine düşünme ve analiz gerektiren"
        },
        "mixed": {
            "name": "Karışık",
            "description": "Tüm zorluk seviyelerinden",
            "complexity": "çeşitli zorluk seviyelerinde"
        }
    }
    
    def __init__(self):
        self.manager = learning_workspace_manager
    
    async def generate_test(
        self,
        test_id: str,
        active_source_ids: List[str] = None,
        custom_instructions: str = ""
    ) -> Generator[Dict, None, None]:
        """
        Test oluştur (streaming).
        
        Args:
            test_id: Test ID
            active_source_ids: Aktif kaynak ID'leri
            custom_instructions: Özel talimatlar
            
        Yields:
            Progress updates ve sorular
        """
        test = self.manager.get_test(test_id)
        if not test:
            yield {"type": "error", "message": "Test bulunamadı"}
            return
        
        try:
            # ===== PHASE 1: KAYNAK TOPLAMA =====
            yield {
                "type": "status",
                "phase": "gathering",
                "message": "📚 Kaynaklar toplanıyor...",
                "progress": 10
            }
            
            # Workspace bilgilerini al
            workspace = self.manager.get_workspace(test.workspace_id)
            topic = workspace.topic if workspace else "Genel"
            
            # RAG ile kaynak topla
            sources = await self._gather_sources(topic, active_source_ids)
            
            yield {
                "type": "sources",
                "count": len(sources),
                "message": f"📖 {len(sources)} kaynak bulundu",
                "progress": 20
            }
            
            # ===== PHASE 2: SORU ÜRETİMİ =====
            questions = []
            questions_per_batch = 5
            total_batches = (test.question_count + questions_per_batch - 1) // questions_per_batch
            
            for batch_idx in range(total_batches):
                start_q = batch_idx * questions_per_batch
                end_q = min(start_q + questions_per_batch, test.question_count)
                batch_count = end_q - start_q
                
                progress = 20 + int((batch_idx / total_batches) * 60)
                
                yield {
                    "type": "status",
                    "phase": "generating",
                    "message": f"✍️ Sorular oluşturuluyor ({start_q + 1}-{end_q}/{test.question_count})...",
                    "progress": progress
                }
                
                # Bu batch için soru üret
                batch_questions = await self._generate_questions(
                    test=test,
                    sources=sources,
                    count=batch_count,
                    existing_questions=questions,
                    custom_instructions=custom_instructions
                )
                
                questions.extend(batch_questions)
                
                yield {
                    "type": "questions_batch",
                    "batch_index": batch_idx,
                    "questions": [q.to_dict() for q in batch_questions],
                    "total_so_far": len(questions),
                    "progress": progress + 10
                }
            
            # ===== PHASE 3: FİNALİZE =====
            yield {
                "type": "status",
                "phase": "finalizing",
                "message": "🔧 Test tamamlanıyor...",
                "progress": 90
            }
            
            # Testi güncelle
            test.questions = [q.to_dict() for q in questions]
            test.status = TestStatus.NOT_STARTED
            self.manager.update_test(test)
            
            yield {
                "type": "complete",
                "message": "✅ Test başarıyla oluşturuldu!",
                "progress": 100,
                "test_id": test.id,
                "question_count": len(questions),
                "test_type": test.test_type.value,
                "difficulty": test.difficulty
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "message": f"❌ Hata oluştu: {str(e)}",
                "progress": -1
            }
    
    async def _gather_sources(
        self,
        topic: str,
        active_source_ids: List[str] = None
    ) -> List[Dict]:
        """Kaynak topla."""
        
        all_sources = []
        seen = set()
        
        try:
            results = vector_store.search_with_scores(
                query=topic,
                n_results=20,
                score_threshold=0.25
            )
            
            for result in results:
                content = result.get("document", "")
                content_hash = hash(content[:100])
                
                if content_hash in seen:
                    continue
                seen.add(content_hash)
                
                metadata = result.get("metadata", {})
                source_id = metadata.get("document_id", "")
                
                # Aktif kaynak filtresi
                if active_source_ids:
                    filename = metadata.get("original_filename", metadata.get("filename", ""))
                    if source_id not in active_source_ids and not any(sid in filename for sid in active_source_ids):
                        continue
                
                all_sources.append({
                    "content": content,
                    "source": metadata.get("original_filename", metadata.get("filename", "Bilinmeyen")),
                    "source_id": source_id,
                    "page": metadata.get("page")
                })
                
        except Exception as e:
            print(f"Source gathering error: {e}")
        
        return all_sources
    
    async def _generate_questions(
        self,
        test: Test,
        sources: List[Dict],
        count: int,
        existing_questions: List[TestQuestion],
        custom_instructions: str
    ) -> List[TestQuestion]:
        """Soru üret."""
        
        test_type_info = self.QUESTION_TEMPLATES.get(test.test_type, self.QUESTION_TEMPLATES[TestType.MIXED])
        difficulty_info = self.DIFFICULTY_LEVELS.get(test.difficulty, self.DIFFICULTY_LEVELS["mixed"])
        
        # Kaynak metni oluştur
        sources_text = ""
        for i, src in enumerate(sources[:15], 1):
            sources_text += f"\n[KAYNAK {i}] ({src['source']}):\n{src['content'][:600]}\n"
        
        # Mevcut soruları listele (tekrar önlemek için)
        existing_text = ""
        if existing_questions:
            existing_text = "\n\nZATEN OLUŞTURULMUŞ SORULAR (bunlardan farklı olmalı):\n"
            for q in existing_questions[-10:]:
                existing_text += f"- {q.question[:100]}\n"
        
        # Test türüne göre format
        if test.test_type == TestType.MULTIPLE_CHOICE:
            format_instruction = """Her soru için:
- Soru metni
- 4 seçenek (A, B, C, D)
- Doğru cevap (sadece harf)
- Açıklama (neden doğru/yanlış)"""
        elif test.test_type == TestType.TRUE_FALSE:
            format_instruction = """Her soru için:
- İfade metni
- Cevap: "Doğru" veya "Yanlış"
- Açıklama (neden doğru/yanlış)"""
        elif test.test_type == TestType.FILL_BLANK:
            format_instruction = """Her soru için:
- Cümle (boşluk ___ ile gösterilmeli)
- Doğru cevap
- Açıklama"""
        elif test.test_type == TestType.SHORT_ANSWER:
            format_instruction = """Her soru için:
- Soru metni
- Beklenen cevap (kısa)
- Açıklama (detaylı)"""
        else:  # MIXED
            format_instruction = """Karışık soru türleri oluştur:
- Çoktan seçmeli (4 seçenek)
- Doğru/Yanlış
- Boşluk doldurma
- Kısa cevap"""
        
        prompt = f"""Aşağıdaki kaynaklara dayanarak {count} adet {test_type_info['name']} sorusu oluştur.

KAYNAKLAR:
{sources_text}

TEST BİLGİLERİ:
- Test Türü: {test_type_info['name']} - {test_type_info['description']}
- Zorluk: {difficulty_info['name']} - {difficulty_info['complexity']}
- Soru Sayısı: {count}

{f'KULLANICI TALİMATLARI: {custom_instructions}' if custom_instructions else ''}
{existing_text}

FORMAT:
{format_instruction}

JSON formatında döndür:
```json
[
  {{
    "question": "Soru metni",
    "question_type": "{test.test_type.value}",
    "options": ["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4"],
    "correct_answer": "A",
    "explanation": "Bu cevabın doğru olmasının nedeni...",
    "difficulty": "medium",
    "source_ref": "KAYNAK 1"
  }}
]
```

Önemli:
- Sorular kaynaklardaki bilgilere dayansın
- Her sorunun açık ve net bir cevabı olsun
- Açıklamalar öğretici olsun
- Yanıltıcı seçenekler mantıklı ama yanlış olsun
- Sorular {difficulty_info['complexity']} olsun

Şimdi {count} soru oluştur:"""

        response = llm_manager.generate(prompt)
        
        # JSON parse
        questions = []
        try:
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                data = json.loads(response)
            
            for item in data:
                q_type = item.get("question_type", test.test_type.value)
                try:
                    q_type_enum = TestType(q_type)
                except:
                    q_type_enum = test.test_type
                
                question = TestQuestion(
                    id=str(uuid.uuid4()),
                    question=item.get("question", ""),
                    question_type=q_type_enum,
                    options=item.get("options", []),
                    correct_answer=item.get("correct_answer", ""),
                    explanation=item.get("explanation", ""),
                    difficulty=item.get("difficulty", "medium"),
                    source_ref=item.get("source_ref", "")
                )
                questions.append(question)
                
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            # Fallback: basit soru oluştur
            questions.append(TestQuestion(
                id=str(uuid.uuid4()),
                question="Kaynaklardan bir soru oluşturulamadı.",
                question_type=test.test_type,
                options=["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4"] if test.test_type == TestType.MULTIPLE_CHOICE else [],
                correct_answer="A",
                explanation="Lütfen testi yeniden oluşturun.",
                difficulty="medium"
            ))
        
        return questions
    
    async def explain_question(
        self,
        test_id: str,
        question_id: str,
        user_question: str
    ) -> str:
        """
        Soru hakkında açıklama yap (anlamadığını sor özelliği).
        
        Args:
            test_id: Test ID
            question_id: Soru ID
            user_question: Kullanıcının sorusu
            
        Returns:
            Açıklama metni
        """
        test = self.manager.get_test(test_id)
        if not test:
            return "Test bulunamadı."
        
        # Soruyu bul
        question_data = None
        for q in test.questions:
            if q.get("id") == question_id:
                question_data = q
                break
        
        if not question_data:
            return "Soru bulunamadı."
        
        prompt = f"""Bir öğrenci aşağıdaki test sorusu hakkında yardım istiyor.

TEST SORUSU:
{question_data.get('question', '')}

SEÇENEKLER:
{chr(10).join(question_data.get('options', []))}

DOĞRU CEVAP: {question_data.get('correct_answer', '')}

MEVCUT AÇIKLAMA:
{question_data.get('explanation', '')}

ÖĞRENCİNİN SORUSU:
"{user_question}"

Lütfen öğrenciye yardımcı ol:
1. Sorusunu net bir şekilde cevapla
2. Kavramı açıkla
3. Doğru cevabı verme, sadece anlamasına yardım et
4. Öğretici ve teşvik edici ol
5. Gerekirse örnekler ver

Yanıtını Türkçe yaz:"""

        response = llm_manager.generate(prompt)
        return response
    
    async def grade_answer(
        self,
        test_id: str,
        question_id: str,
        user_answer: str
    ) -> Dict:
        """
        Cevabı değerlendir (özellikle kısa cevap için).
        
        Returns:
            {is_correct, feedback, score}
        """
        test = self.manager.get_test(test_id)
        if not test:
            return {"is_correct": False, "feedback": "Test bulunamadı", "score": 0}
        
        # Soruyu bul
        question_data = None
        for q in test.questions:
            if q.get("id") == question_id:
                question_data = q
                break
        
        if not question_data:
            return {"is_correct": False, "feedback": "Soru bulunamadı", "score": 0}
        
        correct_answer = question_data.get("correct_answer", "")
        question_type = question_data.get("question_type", "")
        
        # Basit karşılaştırma (çoktan seçmeli, D/Y)
        if question_type in [TestType.MULTIPLE_CHOICE.value, TestType.TRUE_FALSE.value]:
            is_correct = user_answer.strip().upper() == correct_answer.strip().upper()
            return {
                "is_correct": is_correct,
                "feedback": question_data.get("explanation", ""),
                "score": 100 if is_correct else 0,
                "correct_answer": correct_answer
            }
        
        # Boşluk doldurma - basit karşılaştırma
        if question_type == TestType.FILL_BLANK.value:
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            return {
                "is_correct": is_correct,
                "feedback": question_data.get("explanation", ""),
                "score": 100 if is_correct else 0,
                "correct_answer": correct_answer
            }
        
        # Kısa cevap - LLM ile değerlendir
        prompt = f"""Aşağıdaki soruya verilen öğrenci cevabını değerlendir.

SORU:
{question_data.get('question', '')}

BEKLENEN CEVAP:
{correct_answer}

ÖĞRENCİNİN CEVABI:
{user_answer}

Değerlendirme kriterleri:
1. Kavram doğruluğu
2. İçerik bütünlüğü
3. Anahtar noktaların varlığı

JSON formatında döndür:
```json
{{
  "score": 0-100,
  "is_correct": true/false,
  "feedback": "Değerlendirme açıklaması"
}}
```"""

        response = llm_manager.generate(prompt)
        
        try:
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response)
            
            result["correct_answer"] = correct_answer
            return result
            
        except:
            # Fallback
            return {
                "is_correct": False,
                "feedback": "Değerlendirme yapılamadı. Manuel kontrol gerekli.",
                "score": 0,
                "correct_answer": correct_answer
            }
    
    def get_test_summary(self, test_id: str) -> Dict:
        """Test özeti."""
        test = self.manager.get_test(test_id)
        if not test:
            return {}
        
        return {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "test_type": test.test_type.value,
            "question_count": len(test.questions),
            "difficulty": test.difficulty,
            "status": test.status.value,
            "score": test.score,
            "created_at": test.created_at,
            "completed_at": test.completed_at
        }
    
    def get_available_types(self) -> Dict:
        """Kullanılabilir test türlerini döndür."""
        return {
            k.value: v for k, v in self.QUESTION_TEMPLATES.items()
        }
    
    def get_difficulty_levels(self) -> Dict:
        """Zorluk seviyelerini döndür."""
        return self.DIFFICULTY_LEVELS


# Singleton instance
test_generator = TestGenerator()
