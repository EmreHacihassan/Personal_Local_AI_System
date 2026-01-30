"""
MultilingualResearch - Çok Dilli Araştırma Sistemi
==================================================

Farklı dillerde kaynak araştırması yapıp, hedef dilde sentezler.

Özellikler:
- Cross-lingual research (TR→EN→TR)
- Multi-language source fusion
- Auto-translate citations
- Language-agnostic knowledge extraction
- Semantic alignment
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from core.llm_manager import llm_manager
from core.logger import get_logger

logger = get_logger("multilingual_research")


class SupportedLanguage(str, Enum):
    """Desteklenen diller."""
    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    CHINESE = "zh"
    JAPANESE = "ja"
    ARABIC = "ar"


@dataclass
class TranslatedSource:
    """Çevrilmiş kaynak."""
    original_text: str
    translated_text: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    source_info: Dict[str, Any]
    confidence: float
    key_concepts: List[str]


@dataclass
class MultilingualResearchResult:
    """Çok dilli araştırma sonucu."""
    topic: str
    target_language: SupportedLanguage
    sources_by_language: Dict[str, List[Dict]]
    translated_sources: List[TranslatedSource]
    synthesized_content: str
    key_findings: List[str]
    cross_language_insights: List[str]
    citation_translations: Dict[str, str]
    language_distribution: Dict[str, int]


class MultilingualResearchEngine:
    """
    Çok Dilli Araştırma Motoru
    
    Farklı dillerdeki kaynakları sentezleyerek
    tek dilde tutarlı çıktı üretir.
    """
    
    # Dil çiftleri için çeviri kalitesi (1.0 = mükemmel)
    TRANSLATION_QUALITY = {
        ("tr", "en"): 0.9,
        ("en", "tr"): 0.9,
        ("de", "en"): 0.95,
        ("fr", "en"): 0.95,
        ("en", "de"): 0.95,
        ("en", "fr"): 0.95,
        ("zh", "en"): 0.85,
        ("ja", "en"): 0.85,
    }
    
    def __init__(
        self,
        target_language: SupportedLanguage = SupportedLanguage.TURKISH,
        search_languages: Optional[List[SupportedLanguage]] = None
    ):
        self.target_language = target_language
        self.search_languages = search_languages or [
            SupportedLanguage.ENGLISH,
            SupportedLanguage.TURKISH
        ]
        
        # Ensure target is in search languages
        if target_language not in self.search_languages:
            self.search_languages.append(target_language)
        
        # Cache
        self.translation_cache: Dict[str, str] = {}
        self.concept_mappings: Dict[str, Dict[str, str]] = {}
    
    async def translate_text(
        self,
        text: str,
        source_lang: SupportedLanguage,
        target_lang: SupportedLanguage
    ) -> Tuple[str, float]:
        """
        Metin çevirisi.
        
        Args:
            text: Çevrilecek metin
            source_lang: Kaynak dil
            target_lang: Hedef dil
        
        Returns:
            (çevrilmiş_metin, güven_skoru)
        """
        if source_lang == target_lang:
            return text, 1.0
        
        # Cache kontrolü
        cache_key = f"{source_lang.value}:{target_lang.value}:{hash(text[:100])}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key], 0.9
        
        lang_names = {
            SupportedLanguage.TURKISH: "Türkçe",
            SupportedLanguage.ENGLISH: "İngilizce",
            SupportedLanguage.GERMAN: "Almanca",
            SupportedLanguage.FRENCH: "Fransızca",
            SupportedLanguage.SPANISH: "İspanyolca",
            SupportedLanguage.CHINESE: "Çince",
            SupportedLanguage.JAPANESE: "Japonca",
            SupportedLanguage.ARABIC: "Arapça",
        }
        
        source_name = lang_names.get(source_lang, source_lang.value)
        target_name = lang_names.get(target_lang, target_lang.value)
        
        prompt = f"""Aşağıdaki metni {source_name} dilinden {target_name} diline çevir.
Akademik ve teknik terimleri doğru çevir. Anlam bütünlüğünü koru.

Kaynak Metin:
{text[:2000]}

Çeviri ({target_name}):"""
        
        try:
            translated = await llm_manager.generate_async(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2500
            )
            
            # Kalite tahmini
            quality = self.TRANSLATION_QUALITY.get(
                (source_lang.value, target_lang.value),
                0.75
            )
            
            # Cache kaydet
            self.translation_cache[cache_key] = translated
            
            return translated.strip(), quality
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text, 0.3
    
    async def extract_key_concepts(
        self,
        text: str,
        language: SupportedLanguage
    ) -> List[str]:
        """Anahtar kavramları çıkar."""
        prompt = f"""Aşağıdaki akademik metinden anahtar kavramları çıkar.
Her kavram için tek kelime veya kısa ifade kullan.

Metin ({language.value}):
{text[:1500]}

Anahtar Kavramlar (virgülle ayırarak):"""
        
        try:
            response = await llm_manager.generate_async(
                prompt=prompt,
                temperature=0.2,
                max_tokens=200
            )
            
            concepts = [c.strip() for c in response.split(",") if c.strip()]
            return concepts[:15]
            
        except Exception as e:
            logger.error(f"Concept extraction error: {e}")
            return []
    
    async def research_multilingual(
        self,
        topic: str,
        mock_sources: Optional[Dict[str, List[Dict]]] = None
    ) -> MultilingualResearchResult:
        """
        Çok dilli araştırma yap.
        
        Args:
            topic: Araştırma konusu
            mock_sources: Test için mock kaynaklar
        
        Returns:
            MultilingualResearchResult
        """
        sources_by_language: Dict[str, List[Dict]] = mock_sources or {}
        translated_sources: List[TranslatedSource] = []
        all_concepts: List[str] = []
        
        # Her dil için kaynakları işle
        for lang in self.search_languages:
            lang_sources = sources_by_language.get(lang.value, [])
            
            for source in lang_sources:
                source_text = source.get("content", source.get("text", ""))
                
                if not source_text:
                    continue
                
                # Kavramları çıkar
                concepts = await self.extract_key_concepts(source_text, lang)
                all_concepts.extend(concepts)
                
                # Hedef dile çevir
                if lang != self.target_language:
                    translated_text, confidence = await self.translate_text(
                        source_text,
                        lang,
                        self.target_language
                    )
                else:
                    translated_text = source_text
                    confidence = 1.0
                
                translated_sources.append(TranslatedSource(
                    original_text=source_text,
                    translated_text=translated_text,
                    source_language=lang,
                    target_language=self.target_language,
                    source_info=source,
                    confidence=confidence,
                    key_concepts=concepts
                ))
        
        # Dil dağılımı
        language_distribution = {}
        for lang_code, sources in sources_by_language.items():
            language_distribution[lang_code] = len(sources)
        
        # Sentez oluştur
        synthesized_content = await self._synthesize_sources(
            topic,
            translated_sources
        )
        
        # Anahtar bulgular
        key_findings = await self._extract_findings(synthesized_content)
        
        # Cross-language insights
        cross_insights = await self._identify_cross_language_insights(
            translated_sources
        )
        
        # Citation çevirileri
        citation_translations = {}
        for ts in translated_sources:
            original_title = ts.source_info.get("title", "")
            if original_title and ts.source_language != self.target_language:
                translated_title, _ = await self.translate_text(
                    original_title,
                    ts.source_language,
                    self.target_language
                )
                citation_translations[original_title] = translated_title
        
        return MultilingualResearchResult(
            topic=topic,
            target_language=self.target_language,
            sources_by_language=sources_by_language,
            translated_sources=translated_sources,
            synthesized_content=synthesized_content,
            key_findings=key_findings,
            cross_language_insights=cross_insights,
            citation_translations=citation_translations,
            language_distribution=language_distribution
        )
    
    async def _synthesize_sources(
        self,
        topic: str,
        sources: List[TranslatedSource]
    ) -> str:
        """Kaynakları sentezle."""
        if not sources:
            return ""
        
        # En iyi 5 kaynaktan sentez yap
        top_sources = sorted(
            sources,
            key=lambda x: x.confidence,
            reverse=True
        )[:5]
        
        source_texts = "\n\n---\n\n".join([
            f"[Kaynak {i+1} - {s.source_language.value}]\n{s.translated_text[:800]}"
            for i, s in enumerate(top_sources)
        ])
        
        lang_name = "Türkçe" if self.target_language == SupportedLanguage.TURKISH else self.target_language.value
        
        prompt = f"""Aşağıdaki farklı dillerdeki kaynaklardan elde edilen bilgileri sentezle.
{lang_name} dilinde tutarlı ve akademik bir metin oluştur.

Konu: {topic}

Kaynaklar:
{source_texts}

Sentez ({lang_name}, 3-4 paragraf):"""
        
        try:
            synthesis = await llm_manager.generate_async(
                prompt=prompt,
                temperature=0.4,
                max_tokens=1500
            )
            return synthesis.strip()
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return ""
    
    async def _extract_findings(self, content: str) -> List[str]:
        """Anahtar bulguları çıkar."""
        prompt = f"""Aşağıdaki metinden ana bulguları listele.
Her bulgu için kısa ve öz bir madde yaz.

Metin:
{content[:1500]}

Ana Bulgular (5-7 madde):"""
        
        try:
            response = await llm_manager.generate_async(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Maddeleri ayır
            findings = []
            for line in response.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("•") or line[0].isdigit()):
                    finding = re.sub(r'^[-•\d.)\s]+', '', line).strip()
                    if finding:
                        findings.append(finding)
            
            return findings[:7]
            
        except Exception as e:
            logger.error(f"Findings extraction error: {e}")
            return []
    
    async def _identify_cross_language_insights(
        self,
        sources: List[TranslatedSource]
    ) -> List[str]:
        """Diller arası içgörüleri belirle."""
        insights = []
        
        # Dillere göre kavramları grupla
        concepts_by_lang: Dict[str, List[str]] = {}
        for source in sources:
            lang = source.source_language.value
            if lang not in concepts_by_lang:
                concepts_by_lang[lang] = []
            concepts_by_lang[lang].extend(source.key_concepts)
        
        # Ortak kavramları bul
        if len(concepts_by_lang) > 1:
            all_concept_sets = [set(c) for c in concepts_by_lang.values()]
            common_concepts = all_concept_sets[0]
            for cs in all_concept_sets[1:]:
                common_concepts = common_concepts.intersection(cs)
            
            if common_concepts:
                insights.append(
                    f"🌐 Tüm dillerde ortak kavramlar: {', '.join(list(common_concepts)[:5])}"
                )
        
        # Dil bazlı unique kavramları bul
        for lang, concepts in concepts_by_lang.items():
            other_concepts = set()
            for other_lang, other_c in concepts_by_lang.items():
                if other_lang != lang:
                    other_concepts.update(other_c)
            
            unique = set(concepts) - other_concepts
            if unique:
                insights.append(
                    f"📚 {lang.upper()} kaynaklarına özgü: {', '.join(list(unique)[:3])}"
                )
        
        return insights
    
    def to_event(self, result: MultilingualResearchResult) -> Dict[str, Any]:
        """WebSocket event formatına dönüştür."""
        return {
            "type": "multilingual_research",
            "timestamp": datetime.now().isoformat(),
            "topic": result.topic,
            "target_language": result.target_language.value,
            "source_count": sum(len(s) for s in result.sources_by_language.values()),
            "language_distribution": result.language_distribution,
            "key_findings": result.key_findings[:5],
            "cross_language_insights": result.cross_language_insights,
            "message": f"🌐 {len(result.translated_sources)} kaynak {len(result.language_distribution)} dilden sentezlendi"
        }
