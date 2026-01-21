"""
Enterprise AI Assistant - Premium Features V2
==============================================

4 Yeni Premium Özellik:
5. 🧠 AI-Powered Summarization
6. 🔍 Fuzzy Search & Spell Correction
7. 📈 Trend Analysis & Insights
8. 🎯 Smart Query Suggestions

Author: Enterprise AI Assistant
Version: 2.0.0
"""

import hashlib
import json
import math
import re
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import SequenceMatcher, get_close_matches
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from threading import Lock
import statistics
import heapq

from .logger import get_logger

logger = get_logger("premium_features_v2")


# =============================================================================
# 5. AI-POWERED SUMMARIZATION
# =============================================================================

@dataclass
class SummaryConfig:
    """Özetleme yapılandırması."""
    max_sentences: int = 5
    min_sentence_length: int = 20
    max_sentence_length: int = 300
    include_keywords: bool = True
    include_key_phrases: bool = True
    language: str = "auto"  # auto, tr, en


class AISummarizer:
    """
    AI-powered metin özetleme sistemi.
    
    Özellikler:
    - Extractive summarization (cümle seçimi)
    - Key phrase extraction
    - Bullet point generation
    - TL;DR generation
    - Multi-document summarization
    """
    
    # Sentence importance indicators
    IMPORTANCE_INDICATORS = {
        "tr": [
            "önemli", "kritik", "ana", "temel", "sonuç", "özet", "sonuç olarak",
            "özetle", "anahtar", "dikkat", "not", "uyarı", "öneri", "tavsiye"
        ],
        "en": [
            "important", "critical", "key", "main", "conclusion", "summary",
            "in summary", "therefore", "thus", "note", "warning", "recommendation"
        ]
    }
    
    # Stop words for TF-IDF
    STOP_WORDS_TR = {
        "bir", "ve", "veya", "için", "ile", "bu", "şu", "o", "da", "de", "ki",
        "ama", "fakat", "ancak", "çünkü", "eğer", "gibi", "kadar", "daha", "en",
        "çok", "az", "var", "yok", "olarak", "olan", "oldu", "olur", "ise"
    }
    
    STOP_WORDS_EN = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would", "could"
    }
    
    def __init__(self, config: Optional[SummaryConfig] = None):
        self.config = config or SummaryConfig()
        self._cache: Dict[str, Dict] = {}
        self._cache_lock = Lock()
        logger.info("AISummarizer initialized")
    
    def _detect_language(self, text: str) -> str:
        """Dil tespiti."""
        turkish_chars = set("ğüşıöçĞÜŞİÖÇ")
        if any(c in text for c in turkish_chars):
            return "tr"
        return "en"
    
    def _split_sentences(self, text: str) -> List[str]:
        """Metni cümlelere ayır."""
        # Handle common abbreviations
        text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|vs|vb|örn|bkz)\.\s*', r'\1<DOT> ', text)
        
        # Split by sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Restore dots
        sentences = [s.replace('<DOT>', '.') for s in sentences]
        
        # Filter by length
        sentences = [
            s.strip() for s in sentences
            if self.config.min_sentence_length <= len(s) <= self.config.max_sentence_length
        ]
        
        return sentences
    
    def _calculate_sentence_scores(
        self, 
        sentences: List[str], 
        language: str
    ) -> List[Tuple[int, float, str]]:
        """
        Her cümle için önem skoru hesapla.
        
        Returns:
            List of (index, score, sentence)
        """
        if not sentences:
            return []
        
        # Get word frequencies
        all_words = []
        for sentence in sentences:
            words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]+\b', sentence.lower())
            stop_words = self.STOP_WORDS_TR if language == "tr" else self.STOP_WORDS_EN
            words = [w for w in words if w not in stop_words and len(w) > 2]
            all_words.extend(words)
        
        word_freq = Counter(all_words)
        max_freq = max(word_freq.values()) if word_freq else 1
        
        # Normalize frequencies
        word_scores = {word: freq / max_freq for word, freq in word_freq.items()}
        
        # Calculate sentence scores
        scored_sentences = []
        importance_words = self.IMPORTANCE_INDICATORS.get(language, [])
        
        for idx, sentence in enumerate(sentences):
            words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]+\b', sentence.lower())
            
            # Base score: sum of word frequencies
            if words:
                base_score = sum(word_scores.get(w, 0) for w in words) / len(words)
            else:
                base_score = 0
            
            # Position bonus (first and last sentences)
            position_bonus = 0
            if idx == 0:
                position_bonus = 0.3
            elif idx == len(sentences) - 1:
                position_bonus = 0.2
            elif idx < 3:
                position_bonus = 0.1
            
            # Importance indicator bonus
            importance_bonus = 0
            sentence_lower = sentence.lower()
            for indicator in importance_words:
                if indicator in sentence_lower:
                    importance_bonus += 0.15
            
            # Length penalty (too short or too long)
            length = len(sentence)
            if length < 50:
                length_penalty = -0.1
            elif length > 200:
                length_penalty = -0.05
            else:
                length_penalty = 0
            
            # Final score
            final_score = base_score + position_bonus + importance_bonus + length_penalty
            scored_sentences.append((idx, final_score, sentence))
        
        return scored_sentences
    
    def _extract_key_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """Anahtar ifadeleri çıkar."""
        # Simple n-gram extraction
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]+\b', text.lower())
        
        # Bigrams
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        
        # Trigrams
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words)-2)]
        
        # Count and filter
        phrase_counts = Counter(bigrams + trigrams)
        
        # Filter by frequency
        key_phrases = [
            phrase for phrase, count in phrase_counts.most_common(top_n * 2)
            if count >= 2
        ][:top_n]
        
        return key_phrases
    
    def summarize(
        self, 
        text: str, 
        max_sentences: Optional[int] = None,
        format: str = "paragraph"  # paragraph, bullets, tldr
    ) -> Dict[str, Any]:
        """
        Ana özetleme fonksiyonu.
        
        Args:
            text: Özetlenecek metin
            max_sentences: Maksimum cümle sayısı
            format: Çıktı formatı (paragraph, bullets, tldr)
            
        Returns:
            {
                "summary": str,
                "key_points": List[str],
                "key_phrases": List[str],
                "original_length": int,
                "summary_length": int,
                "compression_ratio": float
            }
        """
        # Check cache
        cache_key = hashlib.md5(f"{text[:500]}:{format}".encode()).hexdigest()[:16]
        with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        max_sentences = max_sentences or self.config.max_sentences
        
        # Detect language
        language = self._detect_language(text) if self.config.language == "auto" else self.config.language
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        if not sentences:
            return {
                "summary": text[:500] + "..." if len(text) > 500 else text,
                "key_points": [],
                "key_phrases": [],
                "original_length": len(text),
                "summary_length": min(len(text), 500),
                "compression_ratio": 1.0
            }
        
        # Score sentences
        scored = self._calculate_sentence_scores(sentences, language)
        
        # Select top sentences
        top_sentences = sorted(scored, key=lambda x: x[1], reverse=True)[:max_sentences]
        
        # Re-order by original position
        top_sentences = sorted(top_sentences, key=lambda x: x[0])
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(text)
        
        # Build result based on format
        if format == "bullets":
            summary = "\n".join([f"• {s[2]}" for s in top_sentences])
        elif format == "tldr":
            # Very short summary
            if top_sentences:
                summary = top_sentences[0][2]
                if len(summary) > 200:
                    summary = summary[:200] + "..."
            else:
                summary = text[:200] + "..."
        else:  # paragraph
            summary = " ".join([s[2] for s in top_sentences])
        
        result = {
            "summary": summary,
            "key_points": [s[2] for s in top_sentences],
            "key_phrases": key_phrases,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": round(len(summary) / max(len(text), 1), 2),
            "sentence_count": len(top_sentences),
            "language": language
        }
        
        # Cache result
        with self._cache_lock:
            self._cache[cache_key] = result
            if len(self._cache) > 500:
                # Clear oldest entries
                keys_to_remove = list(self._cache.keys())[:100]
                for key in keys_to_remove:
                    del self._cache[key]
        
        return result
    
    def summarize_multiple(
        self, 
        texts: List[str], 
        max_sentences: int = 10
    ) -> Dict[str, Any]:
        """
        Birden fazla metni özetle.
        
        Multi-document summarization.
        """
        # Combine texts
        combined = "\n\n".join(texts)
        
        # Get individual key points
        all_key_points = []
        for text in texts:
            result = self.summarize(text, max_sentences=3)
            all_key_points.extend(result["key_points"])
        
        # Summarize combined
        main_summary = self.summarize(combined, max_sentences=max_sentences)
        
        # Deduplicate key points
        unique_points = list(dict.fromkeys(all_key_points))[:max_sentences]
        
        return {
            "combined_summary": main_summary["summary"],
            "key_points": unique_points,
            "document_count": len(texts),
            "total_original_length": sum(len(t) for t in texts),
            "compression_ratio": main_summary["compression_ratio"]
        }
    
    def generate_headline(self, text: str, max_length: int = 80) -> str:
        """Başlık oluştur."""
        # Get TL;DR
        tldr = self.summarize(text, max_sentences=1, format="tldr")
        headline = tldr["summary"]
        
        # Truncate if needed
        if len(headline) > max_length:
            headline = headline[:max_length-3] + "..."
        
        return headline


# =============================================================================
# 6. FUZZY SEARCH & SPELL CORRECTION
# =============================================================================

@dataclass
class FuzzySearchConfig:
    """Fuzzy search yapılandırması."""
    min_similarity: float = 0.6  # Minimum benzerlik skoru
    max_suggestions: int = 5
    enable_phonetic: bool = True  # Fonetik eşleşme
    enable_typo_tolerance: bool = True
    max_edit_distance: int = 2


class FuzzySearchEngine:
    """
    Fuzzy search ve yazım düzeltme motoru.
    
    Özellikler:
    - Levenshtein distance
    - Phonetic matching (Soundex benzeri)
    - Typo tolerance
    - Did-you-mean suggestions
    - Word segmentation
    """
    
    # Common typo patterns
    TYPO_PATTERNS = {
        # Keyboard adjacency (Turkish Q keyboard)
        'q': 'wa', 'w': 'qeas', 'e': 'wsdr', 'r': 'edft', 't': 'rfgy',
        'y': 'tghu', 'u': 'yhji', 'ı': 'ujko', 'i': 'ujko', 'o': 'ıklp', 'p': 'olğ',
        'a': 'qwsz', 's': 'awedxz', 'd': 'swerfcx', 'f': 'dertgvc',
        'g': 'ftyhvb', 'h': 'gyujbn', 'j': 'huıknm', 'k': 'jıolm',
        'l': 'kopış', 'z': 'asx', 'x': 'zsdc', 'c': 'xdfv', 'v': 'cfgb',
        'b': 'vghn', 'n': 'bhjm', 'm': 'njk'
    }
    
    # Turkish character mappings
    TR_CHAR_MAP = {
        'ğ': 'g', 'ü': 'u', 'ş': 's', 'ı': 'i', 'ö': 'o', 'ç': 'c',
        'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'İ': 'I', 'Ö': 'O', 'Ç': 'C'
    }
    
    def __init__(self, config: Optional[FuzzySearchConfig] = None):
        self.config = config or FuzzySearchConfig()
        self._vocabulary: Set[str] = set()
        self._word_frequencies: Dict[str, int] = defaultdict(int)
        self._bigrams: Dict[str, Set[str]] = defaultdict(set)
        self._lock = Lock()
        logger.info("FuzzySearchEngine initialized")
    
    def add_to_vocabulary(self, text: str):
        """Metinden kelime haznesine ekle."""
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]+\b', text.lower())
        
        with self._lock:
            for word in words:
                if len(word) >= 2:
                    self._vocabulary.add(word)
                    self._word_frequencies[word] += 1
                    
                    # Add bigrams for faster lookup
                    for i in range(len(word) - 1):
                        bigram = word[i:i+2]
                        self._bigrams[bigram].add(word)
    
    def add_words(self, words: List[str]):
        """Kelimeleri doğrudan ekle."""
        with self._lock:
            for word in words:
                word_lower = word.lower()
                if len(word_lower) >= 2:
                    self._vocabulary.add(word_lower)
                    self._word_frequencies[word_lower] += 1
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Levenshtein (edit) distance hesapla."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Insertions, deletions, substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _similarity_score(self, s1: str, s2: str) -> float:
        """Benzerlik skoru hesapla (0-1)."""
        if not s1 or not s2:
            return 0.0
        
        # Use SequenceMatcher for ratio
        ratio = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
        
        return ratio
    
    def _normalize_turkish(self, text: str) -> str:
        """Türkçe karakterleri normalize et."""
        result = text
        for tr_char, en_char in self.TR_CHAR_MAP.items():
            result = result.replace(tr_char, en_char)
        return result.lower()
    
    def _phonetic_code(self, word: str) -> str:
        """
        Basit fonetik kod oluştur (Soundex benzeri).
        
        Türkçe için uyarlanmış.
        """
        if not word:
            return ""
        
        word = self._normalize_turkish(word)
        
        # Keep first letter
        code = word[0].upper()
        
        # Phonetic mappings
        mappings = {
            'bfpv': '1', 'cgjkqsxz': '2', 'dt': '3',
            'l': '4', 'mn': '5', 'r': '6'
        }
        
        prev_code = ''
        for char in word[1:]:
            for group, num in mappings.items():
                if char in group:
                    if num != prev_code:
                        code += num
                        prev_code = num
                    break
            else:
                prev_code = ''
        
        # Pad or truncate to 4 characters
        code = code[:4].ljust(4, '0')
        
        return code
    
    def find_similar(
        self, 
        query: str, 
        candidates: Optional[List[str]] = None,
        top_n: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Benzer kelimeleri bul.
        
        Returns:
            List of (word, similarity_score)
        """
        top_n = top_n or self.config.max_suggestions
        candidates = candidates or list(self._vocabulary)
        
        if not candidates:
            return []
        
        query_lower = query.lower()
        query_normalized = self._normalize_turkish(query)
        query_phonetic = self._phonetic_code(query) if self.config.enable_phonetic else None
        
        results = []
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            
            # Skip if too different in length
            len_diff = abs(len(query_lower) - len(candidate_lower))
            if len_diff > self.config.max_edit_distance + 2:
                continue
            
            # Calculate similarity
            similarity = self._similarity_score(query_lower, candidate_lower)
            
            # Phonetic bonus
            if query_phonetic and self.config.enable_phonetic:
                candidate_phonetic = self._phonetic_code(candidate)
                if query_phonetic == candidate_phonetic:
                    similarity = min(similarity + 0.2, 1.0)
            
            # Normalized comparison bonus
            if self._normalize_turkish(query) == self._normalize_turkish(candidate):
                similarity = min(similarity + 0.15, 1.0)
            
            # Prefix match bonus
            if candidate_lower.startswith(query_lower[:3]) or query_lower.startswith(candidate_lower[:3]):
                similarity = min(similarity + 0.1, 1.0)
            
            if similarity >= self.config.min_similarity:
                # Frequency boost
                freq_boost = min(self._word_frequencies.get(candidate_lower, 0) / 100, 0.1)
                final_score = similarity + freq_boost
                results.append((candidate, min(final_score, 1.0)))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_n]
    
    def correct_spelling(self, word: str) -> Dict[str, Any]:
        """
        Yazım düzeltme.
        
        Returns:
            {
                "original": str,
                "corrected": str,
                "is_correct": bool,
                "suggestions": List[Tuple[str, float]],
                "confidence": float
            }
        """
        word_lower = word.lower()
        
        # Check if word is in vocabulary
        if word_lower in self._vocabulary:
            return {
                "original": word,
                "corrected": word,
                "is_correct": True,
                "suggestions": [],
                "confidence": 1.0
            }
        
        # Find similar words
        suggestions = self.find_similar(word)
        
        if suggestions:
            best_match, confidence = suggestions[0]
            
            # Only correct if confidence is high enough
            if confidence >= 0.7:
                return {
                    "original": word,
                    "corrected": best_match,
                    "is_correct": False,
                    "suggestions": suggestions,
                    "confidence": confidence
                }
        
        return {
            "original": word,
            "corrected": word,
            "is_correct": False,
            "suggestions": suggestions,
            "confidence": 0.0
        }
    
    def correct_text(self, text: str) -> Dict[str, Any]:
        """
        Tam metin düzeltme.
        """
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]+\b', text)
        corrections = []
        corrected_text = text
        
        for word in words:
            result = self.correct_spelling(word)
            if not result["is_correct"] and result["corrected"] != word:
                corrections.append({
                    "original": word,
                    "corrected": result["corrected"],
                    "confidence": result["confidence"]
                })
                # Replace in text (case-preserving)
                if word[0].isupper():
                    replacement = result["corrected"].capitalize()
                else:
                    replacement = result["corrected"]
                corrected_text = re.sub(
                    r'\b' + re.escape(word) + r'\b',
                    replacement,
                    corrected_text,
                    count=1
                )
        
        return {
            "original_text": text,
            "corrected_text": corrected_text,
            "corrections": corrections,
            "correction_count": len(corrections)
        }
    
    def did_you_mean(self, query: str) -> Optional[str]:
        """
        'Bunu mu demek istediniz?' önerisi.
        """
        words = query.lower().split()
        suggestions = []
        
        for word in words:
            if word not in self._vocabulary and len(word) >= 3:
                similar = self.find_similar(word, top_n=1)
                if similar and similar[0][1] >= 0.7:
                    suggestions.append(similar[0][0])
                else:
                    suggestions.append(word)
            else:
                suggestions.append(word)
        
        suggested_query = " ".join(suggestions)
        
        if suggested_query.lower() != query.lower():
            return suggested_query
        
        return None
    
    def fuzzy_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        field: str = "content"
    ) -> List[Dict[str, Any]]:
        """
        Dökümanlar üzerinde fuzzy search.
        
        Returns:
            Sorted list of matching documents with scores
        """
        query_words = set(query.lower().split())
        results = []
        
        for doc in documents:
            content = doc.get(field, "").lower()
            doc_words = set(content.split())
            
            # Calculate match score
            total_score = 0
            matched_words = 0
            
            for query_word in query_words:
                # Direct match
                if query_word in doc_words:
                    total_score += 1.0
                    matched_words += 1
                else:
                    # Fuzzy match
                    best_match = 0
                    for doc_word in doc_words:
                        if abs(len(query_word) - len(doc_word)) <= 2:
                            sim = self._similarity_score(query_word, doc_word)
                            if sim > best_match:
                                best_match = sim
                    
                    if best_match >= self.config.min_similarity:
                        total_score += best_match
                        matched_words += 1
            
            if matched_words > 0:
                avg_score = total_score / len(query_words)
                coverage = matched_words / len(query_words)
                final_score = avg_score * 0.7 + coverage * 0.3
                
                results.append({
                    **doc,
                    "fuzzy_score": round(final_score, 3),
                    "matched_words": matched_words,
                    "total_query_words": len(query_words)
                })
        
        # Sort by score
        results.sort(key=lambda x: x["fuzzy_score"], reverse=True)
        
        return results


# =============================================================================
# 7. TREND ANALYSIS & INSIGHTS
# =============================================================================

@dataclass
class TrendConfig:
    """Trend analizi yapılandırması."""
    window_size: int = 7  # Gün cinsinden
    min_data_points: int = 3
    anomaly_threshold: float = 2.0  # Standart sapma
    trend_sensitivity: float = 0.1


class TrendAnalyzer:
    """
    Trend analizi ve içgörü sistemi.
    
    Özellikler:
    - Time-series trend detection
    - Anomaly detection
    - Pattern recognition
    - Seasonal analysis
    - Forecasting (basit)
    - Comparative insights
    """
    
    def __init__(self, config: Optional[TrendConfig] = None):
        self.config = config or TrendConfig()
        self._data_points: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self._events: List[Dict[str, Any]] = []
        self._lock = Lock()
        logger.info("TrendAnalyzer initialized")
    
    def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Metrik kaydet."""
        ts = timestamp or datetime.now()
        with self._lock:
            self._data_points[metric_name].append((ts, value))
            # Keep last 30 days
            cutoff = datetime.now() - timedelta(days=30)
            self._data_points[metric_name] = [
                (t, v) for t, v in self._data_points[metric_name]
                if t > cutoff
            ]
    
    def record_event(self, event_type: str, data: Optional[Dict] = None):
        """Event kaydet."""
        with self._lock:
            self._events.append({
                "type": event_type,
                "timestamp": datetime.now(),
                "data": data or {}
            })
            # Keep last 1000 events
            if len(self._events) > 1000:
                self._events = self._events[-1000:]
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Trend hesapla: rising, falling, stable."""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Normalize by mean
        relative_slope = slope / max(abs(y_mean), 1)
        
        if relative_slope > self.config.trend_sensitivity:
            return "rising"
        elif relative_slope < -self.config.trend_sensitivity:
            return "falling"
        return "stable"
    
    def _detect_anomalies(self, values: List[float]) -> List[int]:
        """Anomali tespit et."""
        if len(values) < 3:
            return []
        
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        if stdev == 0:
            return []
        
        anomalies = []
        for i, v in enumerate(values):
            z_score = abs(v - mean) / stdev
            if z_score > self.config.anomaly_threshold:
                anomalies.append(i)
        
        return anomalies
    
    def _forecast_next(self, values: List[float], periods: int = 3) -> List[float]:
        """Basit forecasting (linear extrapolation)."""
        if len(values) < 2:
            return [values[-1]] * periods if values else [0] * periods
        
        # Simple moving average + trend
        recent = values[-min(7, len(values)):]
        avg = statistics.mean(recent)
        
        # Calculate trend
        if len(recent) >= 2:
            trend = (recent[-1] - recent[0]) / len(recent)
        else:
            trend = 0
        
        forecasts = []
        for i in range(1, periods + 1):
            forecast = avg + trend * i
            forecasts.append(round(forecast, 2))
        
        return forecasts
    
    def analyze_metric(self, metric_name: str) -> Dict[str, Any]:
        """
        Tek bir metriği analiz et.
        """
        with self._lock:
            data = self._data_points.get(metric_name, [])
        
        if len(data) < self.config.min_data_points:
            return {
                "metric": metric_name,
                "status": "insufficient_data",
                "data_points": len(data),
                "required": self.config.min_data_points
            }
        
        # Sort by timestamp
        data = sorted(data, key=lambda x: x[0])
        values = [v for _, v in data]
        timestamps = [t for t, _ in data]
        
        # Basic statistics
        current = values[-1]
        avg = statistics.mean(values)
        min_val = min(values)
        max_val = max(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Trend
        trend = self._calculate_trend(values)
        
        # Anomalies
        anomaly_indices = self._detect_anomalies(values)
        
        # Change from previous
        if len(values) >= 2:
            change = values[-1] - values[-2]
            change_pct = (change / values[-2] * 100) if values[-2] != 0 else 0
        else:
            change = 0
            change_pct = 0
        
        # Forecast
        forecast = self._forecast_next(values)
        
        return {
            "metric": metric_name,
            "status": "analyzed",
            "current": current,
            "statistics": {
                "mean": round(avg, 2),
                "min": min_val,
                "max": max_val,
                "stdev": round(stdev, 2),
                "data_points": len(values)
            },
            "trend": {
                "direction": trend,
                "change": round(change, 2),
                "change_percent": round(change_pct, 1)
            },
            "anomalies": {
                "count": len(anomaly_indices),
                "indices": anomaly_indices
            },
            "forecast": {
                "next_periods": forecast,
                "method": "linear_extrapolation"
            },
            "time_range": {
                "start": timestamps[0].isoformat() if timestamps else None,
                "end": timestamps[-1].isoformat() if timestamps else None
            }
        }
    
    def get_insights(self) -> Dict[str, Any]:
        """
        Tüm verilerden içgörüler üret.
        """
        insights = []
        
        with self._lock:
            metrics = dict(self._data_points)
            events = list(self._events)
        
        # Analyze each metric
        for metric_name in metrics:
            analysis = self.analyze_metric(metric_name)
            
            if analysis.get("status") != "analyzed":
                continue
            
            # Generate insights
            trend = analysis["trend"]["direction"]
            change_pct = analysis["trend"]["change_percent"]
            
            if trend == "rising" and change_pct > 20:
                insights.append({
                    "type": "significant_increase",
                    "metric": metric_name,
                    "message": f"📈 {metric_name} son dönemde %{change_pct:.1f} arttı",
                    "severity": "info"
                })
            elif trend == "falling" and change_pct < -20:
                insights.append({
                    "type": "significant_decrease",
                    "metric": metric_name,
                    "message": f"📉 {metric_name} son dönemde %{abs(change_pct):.1f} düştü",
                    "severity": "warning"
                })
            
            if analysis["anomalies"]["count"] > 0:
                insights.append({
                    "type": "anomaly_detected",
                    "metric": metric_name,
                    "message": f"⚠️ {metric_name} metriğinde {analysis['anomalies']['count']} anomali tespit edildi",
                    "severity": "warning"
                })
        
        # Event-based insights
        if events:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_events = [e for e in events if e["timestamp"] > one_hour_ago]
            
            event_counts = Counter(e["type"] for e in recent_events)
            
            for event_type, count in event_counts.most_common(3):
                if count >= 10:
                    insights.append({
                        "type": "high_activity",
                        "event": event_type,
                        "message": f"🔥 Son 1 saatte {count} adet '{event_type}' olayı gerçekleşti",
                        "severity": "info"
                    })
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total_insights": len(insights),
            "insights": insights,
            "metrics_analyzed": len(metrics),
            "events_analyzed": len(events)
        }
    
    def compare_periods(
        self, 
        metric_name: str, 
        period1_days: int = 7, 
        period2_days: int = 7
    ) -> Dict[str, Any]:
        """
        İki dönemi karşılaştır.
        """
        with self._lock:
            data = self._data_points.get(metric_name, [])
        
        now = datetime.now()
        period1_start = now - timedelta(days=period1_days)
        period2_start = period1_start - timedelta(days=period2_days)
        
        period1_data = [v for t, v in data if t >= period1_start]
        period2_data = [v for t, v in data if period2_start <= t < period1_start]
        
        if not period1_data or not period2_data:
            return {
                "metric": metric_name,
                "status": "insufficient_data"
            }
        
        avg1 = statistics.mean(period1_data)
        avg2 = statistics.mean(period2_data)
        
        change = avg1 - avg2
        change_pct = (change / avg2 * 100) if avg2 != 0 else 0
        
        return {
            "metric": metric_name,
            "period1": {
                "days": period1_days,
                "average": round(avg1, 2),
                "count": len(period1_data)
            },
            "period2": {
                "days": period2_days,
                "average": round(avg2, 2),
                "count": len(period2_data)
            },
            "comparison": {
                "change": round(change, 2),
                "change_percent": round(change_pct, 1),
                "trend": "improved" if change > 0 else "declined" if change < 0 else "stable"
            }
        }


# =============================================================================
# 8. SMART QUERY SUGGESTIONS
# =============================================================================

@dataclass
class QuerySuggestionConfig:
    """Sorgu öneri yapılandırması."""
    max_suggestions: int = 5
    min_query_length: int = 2
    enable_history: bool = True
    enable_trending: bool = True
    enable_related: bool = True
    history_weight: float = 0.3
    trending_weight: float = 0.3
    related_weight: float = 0.4


class SmartQuerySuggester:
    """
    Akıllı sorgu öneri sistemi.
    
    Özellikler:
    - Query autocomplete
    - Related query suggestions
    - Trending queries
    - Personalized suggestions (based on history)
    - Query expansion
    - Popular queries
    """
    
    def __init__(self, config: Optional[QuerySuggestionConfig] = None):
        self.config = config or QuerySuggestionConfig()
        self._query_history: List[Tuple[datetime, str]] = []
        self._query_counts: Dict[str, int] = defaultdict(int)
        self._query_success: Dict[str, float] = {}  # query -> success rate
        self._related_queries: Dict[str, Set[str]] = defaultdict(set)
        self._trending_window: List[Tuple[datetime, str]] = []
        self._lock = Lock()
        
        # Pre-defined query expansions
        self._expansions = {
            "nasıl": ["nasıl yapılır", "nasıl çalışır", "nasıl kullanılır"],
            "nedir": ["nedir", "ne işe yarar", "ne anlama gelir"],
            "how": ["how to", "how does", "how can"],
            "what": ["what is", "what are", "what does"],
            "python": ["python tutorial", "python code", "python example"],
            "api": ["api documentation", "api endpoint", "api usage"],
            "hata": ["hata çözümü", "hata mesajı", "hata ayıklama"],
            "error": ["error fix", "error message", "error handling"]
        }
        
        logger.info("SmartQuerySuggester initialized")
    
    def record_query(
        self, 
        query: str, 
        success: bool = True,
        related_queries: Optional[List[str]] = None
    ):
        """Sorgu kaydet."""
        query_lower = query.lower().strip()
        
        with self._lock:
            now = datetime.now()
            
            # Record in history
            self._query_history.append((now, query_lower))
            
            # Update counts
            self._query_counts[query_lower] += 1
            
            # Update success rate
            current_success = self._query_success.get(query_lower, 0.5)
            # Exponential moving average
            self._query_success[query_lower] = 0.8 * current_success + 0.2 * (1.0 if success else 0.0)
            
            # Update trending
            self._trending_window.append((now, query_lower))
            
            # Add related queries
            if related_queries:
                for related in related_queries:
                    self._related_queries[query_lower].add(related.lower())
            
            # Cleanup old data
            one_day_ago = now - timedelta(days=1)
            self._trending_window = [
                (t, q) for t, q in self._trending_window if t > one_day_ago
            ]
            
            # Limit history
            if len(self._query_history) > 10000:
                self._query_history = self._query_history[-5000:]
    
    def _get_prefix_matches(self, prefix: str) -> List[Tuple[str, float]]:
        """Prefix ile eşleşen sorguları bul."""
        prefix_lower = prefix.lower()
        matches = []
        
        for query, count in self._query_counts.items():
            if query.startswith(prefix_lower):
                # Score based on frequency and success
                success_rate = self._query_success.get(query, 0.5)
                score = (count / 100) * 0.5 + success_rate * 0.5
                matches.append((query, min(score, 1.0)))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:10]
    
    def _get_trending(self, limit: int = 5) -> List[Tuple[str, int]]:
        """Trending sorguları getir."""
        with self._lock:
            recent_queries = [q for _, q in self._trending_window]
        
        counter = Counter(recent_queries)
        return counter.most_common(limit)
    
    def _get_related(self, query: str, limit: int = 5) -> List[str]:
        """İlişkili sorguları getir."""
        query_lower = query.lower()
        related = set()
        
        # Direct relations
        if query_lower in self._related_queries:
            related.update(self._related_queries[query_lower])
        
        # Word-based relations
        query_words = set(query_lower.split())
        for stored_query in self._query_counts:
            stored_words = set(stored_query.split())
            overlap = len(query_words & stored_words)
            if overlap > 0 and stored_query != query_lower:
                related.add(stored_query)
        
        return list(related)[:limit]
    
    def _expand_query(self, query: str) -> List[str]:
        """Sorguyu genişlet."""
        expansions = []
        query_lower = query.lower()
        
        # Check predefined expansions
        for keyword, templates in self._expansions.items():
            if keyword in query_lower:
                for template in templates:
                    if template not in query_lower:
                        expanded = query_lower.replace(keyword, template)
                        expansions.append(expanded)
        
        # Add common suffixes
        if len(query_lower.split()) == 1:
            suffixes = ["örnek", "kullanım", "example", "tutorial"]
            for suffix in suffixes:
                expansions.append(f"{query_lower} {suffix}")
        
        return expansions[:5]
    
    def suggest(
        self, 
        partial_query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Ana öneri fonksiyonu.
        
        Args:
            partial_query: Yarım kalan sorgu
            context: Ek bağlam bilgisi
            
        Returns:
            {
                "suggestions": List[str],
                "autocomplete": List[str],
                "trending": List[str],
                "related": List[str],
                "expanded": List[str]
            }
        """
        if len(partial_query) < self.config.min_query_length:
            # Return trending only
            trending = self._get_trending(self.config.max_suggestions)
            return {
                "suggestions": [q for q, _ in trending],
                "autocomplete": [],
                "trending": [q for q, _ in trending],
                "related": [],
                "expanded": []
            }
        
        # Get different types of suggestions
        autocomplete = self._get_prefix_matches(partial_query)
        trending = self._get_trending(3)
        related = self._get_related(partial_query, 3)
        expanded = self._expand_query(partial_query)
        
        # Combine and rank
        all_suggestions = {}
        
        # Autocomplete (history-based)
        for query, score in autocomplete:
            all_suggestions[query] = score * self.config.history_weight
        
        # Trending
        for query, count in trending:
            current = all_suggestions.get(query, 0)
            all_suggestions[query] = current + (count / 10) * self.config.trending_weight
        
        # Related
        for query in related:
            current = all_suggestions.get(query, 0)
            all_suggestions[query] = current + 0.5 * self.config.related_weight
        
        # Sort and get top suggestions
        sorted_suggestions = sorted(
            all_suggestions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_suggestions = [q for q, _ in sorted_suggestions[:self.config.max_suggestions]]
        
        return {
            "suggestions": top_suggestions,
            "autocomplete": [q for q, _ in autocomplete[:5]],
            "trending": [q for q, _ in trending],
            "related": related,
            "expanded": expanded[:3]
        }
    
    def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """En popüler sorguları getir."""
        sorted_queries = sorted(
            self._query_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "query": query,
                "count": count,
                "success_rate": round(self._query_success.get(query, 0.5), 2)
            }
            for query, count in sorted_queries[:limit]
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler."""
        with self._lock:
            return {
                "total_queries": len(self._query_history),
                "unique_queries": len(self._query_counts),
                "trending_window_size": len(self._trending_window),
                "related_mappings": len(self._related_queries),
                "top_queries": self.get_popular_queries(5)
            }


# =============================================================================
# EXPORT ALL NEW FEATURES
# =============================================================================

__all__ = [
    "AISummarizer",
    "SummaryConfig",
    "FuzzySearchEngine",
    "FuzzySearchConfig",
    "TrendAnalyzer",
    "TrendConfig",
    "SmartQuerySuggester",
    "QuerySuggestionConfig",
]
