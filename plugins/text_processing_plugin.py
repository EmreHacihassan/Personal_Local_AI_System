"""
📝 Text Processing Plugin
=========================

Metin işleme yetenekleri ekleyen plugin.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)


class TextProcessingPlugin(PluginBase):
    """
    Metin işleme plugin'i.
    
    Özet çıkarma, anahtar kelime analizi, duygu analizi gibi
    metin işleme yetenekleri ekler.
    """
    
    name = "text_processing"
    version = "1.0.0"
    description = "Metin işleme ve analiz yetenekleri"
    author = "Enterprise AI Team"
    
    async def execute(self, input_data: Dict[str, Any]) -> PluginResult:
        """
        Metin işle.
        
        Args:
            input_data: {
                "text": str,  # İşlenecek metin
                "operation": str,  # summarize, keywords, sentiment, clean
                "options": Dict  # İşlem opsiyonları
            }
        """
        text = input_data.get("text")
        operation = input_data.get("operation", "clean")
        options = input_data.get("options", {})
        
        if not text:
            return PluginResult(
                success=False,
                error="Text is required"
            )
        
        try:
            if operation == "summarize":
                result = await self._summarize(text, options)
            elif operation == "keywords":
                result = self._extract_keywords(text, options)
            elif operation == "sentiment":
                result = self._analyze_sentiment(text)
            elif operation == "clean":
                result = self._clean_text(text, options)
            elif operation == "stats":
                result = self._get_stats(text)
            else:
                return PluginResult(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
            
            return PluginResult(
                success=True,
                data=result
            )
            
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            return PluginResult(
                success=False,
                error=str(e)
            )
    
    async def _summarize(self, text: str, options: Dict) -> Dict[str, Any]:
        """Metni özetle (basit extractive summarization)"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # İlk ve son cümleleri al (basit yöntem)
        max_sentences = options.get("max_sentences", 3)
        
        if len(sentences) <= max_sentences:
            summary = ". ".join(sentences) + "."
        else:
            # İlk, orta ve son cümleleri al
            summary_sentences = [sentences[0]]
            if len(sentences) > 2:
                summary_sentences.append(sentences[len(sentences) // 2])
            summary_sentences.append(sentences[-1])
            summary = ". ".join(summary_sentences[:max_sentences]) + "."
        
        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": round(len(summary) / len(text), 2),
        }
    
    def _extract_keywords(self, text: str, options: Dict) -> Dict[str, Any]:
        """Anahtar kelimeleri çıkar"""
        # Basit TF-based keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Stop words
        stop_words = {
            'bir', 'bu', 've', 'de', 'da', 'ile', 'için', 'olan', 'olarak',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall',
            'that', 'this', 'these', 'those', 'it', 'its', 'i', 'you',
            'he', 'she', 'they', 'we', 'my', 'your', 'his', 'her', 'their',
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
            'up', 'about', 'into', 'over', 'after', 'and', 'but', 'or',
        }
        
        # Word frequency
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Top keywords
        max_keywords = options.get("max_keywords", 10)
        sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])
        keywords = [{"word": w, "count": c} for w, c in sorted_words[:max_keywords]]
        
        return {
            "keywords": keywords,
            "total_words": len(words),
            "unique_words": len(word_freq),
        }
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Basit duygu analizi"""
        # Basit keyword-based sentiment
        positive_words = {
            'güzel', 'harika', 'mükemmel', 'iyi', 'başarılı', 'mutlu',
            'great', 'good', 'excellent', 'amazing', 'wonderful', 'happy',
            'love', 'like', 'best', 'awesome', 'fantastic', 'beautiful',
        }
        
        negative_words = {
            'kötü', 'berbat', 'korkunç', 'üzücü', 'başarısız', 'mutsuz',
            'bad', 'terrible', 'awful', 'horrible', 'sad', 'hate',
            'worst', 'poor', 'disappointing', 'failed', 'ugly',
        }
        
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        positive_count = len(words & positive_words)
        negative_count = len(words & negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            sentiment = "neutral"
            score = 0.5
        elif positive_count > negative_count:
            sentiment = "positive"
            score = 0.5 + (positive_count - negative_count) / (2 * total)
        else:
            sentiment = "negative"
            score = 0.5 - (negative_count - positive_count) / (2 * total)
        
        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
        }
    
    def _clean_text(self, text: str, options: Dict) -> Dict[str, Any]:
        """Metni temizle"""
        original = text
        
        # Extra whitespace temizle
        if options.get("normalize_whitespace", True):
            text = re.sub(r'\s+', ' ', text).strip()
        
        # URL'leri temizle
        if options.get("remove_urls", False):
            text = re.sub(r'https?://\S+', '', text)
        
        # Email'leri temizle
        if options.get("remove_emails", False):
            text = re.sub(r'\S+@\S+\.\S+', '', text)
        
        # Özel karakterleri temizle
        if options.get("remove_special_chars", False):
            text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return {
            "cleaned_text": text,
            "original_length": len(original),
            "cleaned_length": len(text),
            "removed_chars": len(original) - len(text),
        }
    
    def _get_stats(self, text: str) -> Dict[str, Any]:
        """Metin istatistikleri"""
        words = re.findall(r'\b\w+\b', text)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 2),
            "avg_sentence_length": round(len(words) / max(len(sentences), 1), 2),
        }
