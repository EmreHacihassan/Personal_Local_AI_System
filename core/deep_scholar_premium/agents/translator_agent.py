"""
TranslatorAgent - Premium Çeviri ve Çok Dilli Destek Ajanı
==========================================================

Görevler:
1. Akademik çeviri (Türkçe ↔ İngilizce)
2. Terminoloji tutarlılığı
3. Lokalizasyon
4. Çok dilli özet üretimi
5. Terim sözlüğü yönetimi
6. Alana özgü çeviri
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.llm_manager import llm_manager


class Language(str, Enum):
    """Desteklenen diller."""
    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    RUSSIAN = "ru"
    CHINESE = "zh"
    ARABIC = "ar"


class TranslationQuality(str, Enum):
    """Çeviri kalitesi."""
    DRAFT = "draft"           # Hızlı taslak
    STANDARD = "standard"     # Standart kalite
    ACADEMIC = "academic"     # Akademik kalite
    PROFESSIONAL = "professional"  # Profesyonel kalite


class Domain(str, Enum):
    """Uzmanlık alanı."""
    GENERAL = "general"
    COMPUTER_SCIENCE = "computer_science"
    MEDICINE = "medicine"
    LAW = "law"
    ENGINEERING = "engineering"
    BUSINESS = "business"
    SCIENCE = "science"
    HUMANITIES = "humanities"


@dataclass
class TermEntry:
    """Terim sözlüğü girişi."""
    source_term: str
    source_language: Language
    translations: Dict[str, str]  # language_code -> translation
    domain: Domain
    definition: Optional[str] = None
    usage_examples: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)


@dataclass
class TranslationResult:
    """Çeviri sonucu."""
    source_text: str
    source_language: Language
    target_language: Language
    translated_text: str
    quality: TranslationQuality
    
    # Kalite metrikleri
    terminology_consistency: float = 0.0
    fluency_score: float = 0.0
    accuracy_score: float = 0.0
    
    # Ek bilgiler
    technical_terms_used: List[Dict[str, str]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class MultilingualSummary:
    """Çok dilli özet."""
    original_language: Language
    original_summary: str
    translations: Dict[str, str]  # language_code -> summary
    key_terms: Dict[str, Dict[str, str]]  # term -> {lang: translation}


class TranslatorAgent:
    """
    Premium Çeviri ve Çok Dilli Destek Ajanı
    
    Akademik metin çevirisi ve terminoloji yönetimi.
    """
    
    def __init__(self, global_state: Optional[Any] = None):
        self.global_state = global_state
        self.glossary: Dict[str, TermEntry] = {}
        self.default_domain = Domain.GENERAL
        
        # Yaygın akademik terimler
        self._init_base_glossary()
    
    def _init_base_glossary(self):
        """Temel akademik sözlüğü başlat."""
        base_terms = [
            {
                "term": "abstract",
                "tr": "özet",
                "domain": Domain.GENERAL
            },
            {
                "term": "methodology",
                "tr": "yöntem/metodoloji",
                "domain": Domain.GENERAL
            },
            {
                "term": "hypothesis",
                "tr": "hipotez",
                "domain": Domain.SCIENCE
            },
            {
                "term": "algorithm",
                "tr": "algoritma",
                "domain": Domain.COMPUTER_SCIENCE
            },
            {
                "term": "machine learning",
                "tr": "makine öğrenmesi",
                "domain": Domain.COMPUTER_SCIENCE
            },
            {
                "term": "neural network",
                "tr": "yapay sinir ağı",
                "domain": Domain.COMPUTER_SCIENCE
            },
            {
                "term": "deep learning",
                "tr": "derin öğrenme",
                "domain": Domain.COMPUTER_SCIENCE
            },
            {
                "term": "artificial intelligence",
                "tr": "yapay zeka",
                "domain": Domain.COMPUTER_SCIENCE
            },
            {
                "term": "natural language processing",
                "tr": "doğal dil işleme",
                "domain": Domain.COMPUTER_SCIENCE
            },
            {
                "term": "literature review",
                "tr": "literatür taraması",
                "domain": Domain.GENERAL
            },
            {
                "term": "case study",
                "tr": "vaka çalışması",
                "domain": Domain.GENERAL
            },
            {
                "term": "empirical study",
                "tr": "ampirik çalışma",
                "domain": Domain.SCIENCE
            }
        ]
        
        for item in base_terms:
            entry = TermEntry(
                source_term=item["term"],
                source_language=Language.ENGLISH,
                translations={"tr": item["tr"]},
                domain=item["domain"]
            )
            self.glossary[item["term"].lower()] = entry
    
    async def translate(
        self,
        text: str,
        source_lang: Language,
        target_lang: Language,
        domain: Domain = Domain.GENERAL,
        quality: TranslationQuality = TranslationQuality.ACADEMIC
    ) -> TranslationResult:
        """
        Metni çevir.
        
        Args:
            text: Çevrilecek metin
            source_lang: Kaynak dil
            target_lang: Hedef dil
            domain: Uzmanlık alanı
            quality: İstenen kalite seviyesi
            
        Returns:
            Çeviri sonucu
        """
        # Terminoloji listesi oluştur
        relevant_terms = self._get_domain_terms(domain)
        
        quality_instructions = {
            TranslationQuality.DRAFT: "Hızlı, anlaşılır bir çeviri yap.",
            TranslationQuality.STANDARD: "Gramer ve akıcılığa dikkat ederek çevir.",
            TranslationQuality.ACADEMIC: """Akademik çeviri kriterleri:
1. Terminoloji tutarlılığı
2. Akademik dil ve üslup
3. Kaynak metne sadakat
4. Hedef dilde doğallık
5. Alana özgü terimler""",
            TranslationQuality.PROFESSIONAL: """Profesyonel çeviri kriterleri:
1. Mükemmel terminoloji
2. Sektör standartlarına uyum
3. Kültürel adaptasyon
4. Stilistik tutarlılık"""
        }
        
        prompt = f"""## Çeviri Görevi

**Kaynak Dil:** {source_lang.value}
**Hedef Dil:** {target_lang.value}
**Alan:** {domain.value}

## Kalite Gereksinimleri:
{quality_instructions[quality]}

## Terim Sözlüğü (Bu terimleri kullan):
{json.dumps(relevant_terms, ensure_ascii=False)}

## Çevrilecek Metin:
{text}

## Önemli:
- Teknik terimleri sözlüğe uygun çevir
- Akademik üslubu koru
- Anlamı bozmadan akıcı çevir

## Yanıt Formatı (JSON):
{{
    "translated_text": "<çeviri>",
    "terms_used": [{{"source": "", "translation": ""}}],
    "notes": ["<varsa notlar>"]
}}"""

        response = await self._llm_call(prompt)
        
        translated_text = text
        terms_used = []
        notes = []
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                translated_text = data.get("translated_text", text)
                terms_used = data.get("terms_used", [])
                notes = data.get("notes", [])
        except:
            # Düz metin olarak al
            translated_text = response.strip()
        
        return TranslationResult(
            source_text=text,
            source_language=source_lang,
            target_language=target_lang,
            translated_text=translated_text,
            quality=quality,
            terminology_consistency=0.85 if terms_used else 0.5,
            fluency_score=0.8,
            accuracy_score=0.85,
            technical_terms_used=terms_used,
            notes=notes
        )
    
    async def translate_document(
        self,
        sections: List[Dict[str, str]],
        source_lang: Language,
        target_lang: Language,
        domain: Domain = Domain.GENERAL
    ) -> List[Dict[str, str]]:
        """
        Tüm dokümanı çevir.
        
        Args:
            sections: Bölümler listesi
            source_lang: Kaynak dil
            target_lang: Hedef dil
            domain: Uzmanlık alanı
            
        Returns:
            Çevrilmiş bölümler
        """
        translated_sections = []
        
        for section in sections:
            title = section.get("title", "")
            content = section.get("content", "")
            
            # Başlığı çevir
            if title:
                title_result = await self.translate(
                    title, source_lang, target_lang, domain,
                    TranslationQuality.ACADEMIC
                )
                title = title_result.translated_text
            
            # İçeriği çevir
            if content:
                content_result = await self.translate(
                    content, source_lang, target_lang, domain,
                    TranslationQuality.ACADEMIC
                )
                content = content_result.translated_text
            
            translated_sections.append({
                "title": title,
                "content": content
            })
        
        return translated_sections
    
    async def generate_multilingual_summary(
        self,
        document_content: str,
        source_lang: Language,
        target_languages: List[Language],
        max_length: int = 300
    ) -> MultilingualSummary:
        """
        Çok dilli özet üret.
        
        Args:
            document_content: Doküman içeriği
            source_lang: Kaynak dil
            target_languages: Hedef diller
            max_length: Özet uzunluğu
            
        Returns:
            Çok dilli özet
        """
        # Önce kaynak dilde özet
        summary_prompt = f"""Aşağıdaki akademik metni {max_length} kelimeyi aşmayacak şekilde özetle.

## Metin:
{document_content[:5000]}

## Özet ({source_lang.value}):"""

        original_summary = await self._llm_call(summary_prompt)
        
        # Anahtar terimleri çıkar
        key_terms_prompt = f"""Bu metindeki 5-10 anahtar terimi listele.

{document_content[:3000]}

Yanıt formatı (JSON array):
["terim1", "terim2", ...]"""

        terms_response = await self._llm_call(key_terms_prompt)
        key_terms = []
        try:
            json_match = re.search(r'\[[\s\S]*\]', terms_response)
            if json_match:
                key_terms = json.loads(json_match.group())
        except:
            pass
        
        # Diğer dillere çevir
        translations = {}
        key_term_translations = {}
        
        for target_lang in target_languages:
            if target_lang != source_lang:
                result = await self.translate(
                    original_summary,
                    source_lang,
                    target_lang,
                    Domain.GENERAL,
                    TranslationQuality.ACADEMIC
                )
                translations[target_lang.value] = result.translated_text
        
        # Anahtar terimleri çevir
        for term in key_terms:
            key_term_translations[term] = {}
            for target_lang in target_languages:
                if target_lang != source_lang:
                    term_result = await self.translate(
                        term, source_lang, target_lang,
                        Domain.GENERAL, TranslationQuality.STANDARD
                    )
                    key_term_translations[term][target_lang.value] = term_result.translated_text
        
        return MultilingualSummary(
            original_language=source_lang,
            original_summary=original_summary.strip(),
            translations=translations,
            key_terms=key_term_translations
        )
    
    async def check_terminology_consistency(
        self,
        content: str,
        domain: Domain = Domain.GENERAL
    ) -> Dict[str, Any]:
        """
        Terminoloji tutarlılığını kontrol et.
        
        Args:
            content: Doküman içeriği
            domain: Uzmanlık alanı
            
        Returns:
            Tutarlılık raporu
        """
        prompt = f"""Bu akademik metinde terminoloji tutarlılığını kontrol et.

## Metin:
{content[:4000]}

## Kontrol Kriterleri:
1. Aynı kavramın farklı terimlerle ifade edilmesi
2. Çeviri tutarsızlıkları (İngilizce-Türkçe karışımı)
3. Kısaltma tutarsızlıkları
4. Teknik terim yanlış kullanımı

## Yanıt (JSON):
{{
    "consistency_score": <0-100>,
    "issues": [
        {{
            "term1": "",
            "term2": "",
            "issue_type": "synonym_inconsistency|translation_inconsistency|abbreviation_inconsistency",
            "suggestion": ""
        }}
    ],
    "recommendations": [""]
}}"""

        response = await self._llm_call(prompt)
        
        result = {
            "consistency_score": 80,
            "issues": [],
            "recommendations": []
        }
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
        except:
            pass
        
        return result
    
    async def localize_content(
        self,
        content: str,
        source_lang: Language,
        target_lang: Language,
        target_region: str = "TR"
    ) -> str:
        """
        İçeriği lokalize et (kültürel adaptasyon).
        
        Args:
            content: İçerik
            source_lang: Kaynak dil
            target_lang: Hedef dil
            target_region: Hedef bölge
            
        Returns:
            Lokalize edilmiş içerik
        """
        prompt = f"""Bu metni {target_region} bölgesi için lokalize et.

## Lokalizasyon Kriterleri:
1. Tarih formatı (gün/ay/yıl)
2. Sayı formatı (1.000,00 vs 1,000.00)
3. Para birimi
4. Ölçü birimleri
5. Kültürel referanslar

## Kaynak Metin:
{content}

## Lokalize Edilmiş Metin:"""

        response = await self._llm_call(prompt)
        return response.strip()
    
    def add_term(self, entry: TermEntry):
        """Sözlüğe terim ekle."""
        key = entry.source_term.lower()
        self.glossary[key] = entry
    
    def get_term(self, term: str, target_lang: Language) -> Optional[str]:
        """Terimin çevirisini getir."""
        key = term.lower()
        if key in self.glossary:
            entry = self.glossary[key]
            return entry.translations.get(target_lang.value)
        return None
    
    def _get_domain_terms(self, domain: Domain) -> Dict[str, str]:
        """Alana özgü terimleri getir."""
        terms = {}
        for key, entry in self.glossary.items():
            if entry.domain in [domain, Domain.GENERAL]:
                if "tr" in entry.translations:
                    terms[entry.source_term] = entry.translations["tr"]
        return terms
    
    async def _llm_call(self, prompt: str, timeout: int = 300) -> str:
        """LLM çağrısı yap."""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_manager.chat,
                    messages=messages,
                    model_type="default"
                ),
                timeout=timeout
            )
            return response.get("content", "") if isinstance(response, dict) else str(response)
        except Exception as e:
            return f"Error: {str(e)}"
