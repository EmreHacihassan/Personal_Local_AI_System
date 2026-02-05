"""
📝 Conversation Summarizer
===========================

Uzun konuşmaları özetleme ve context yönetimi.

Features:
- Incremental summarization
- Key point extraction
- Topic tracking
- Memory-efficient context management
- Hierarchical summarization
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """Mesaj rolleri."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SummaryLevel(Enum):
    """Özet seviyeleri."""
    BRIEF = "brief"  # 1-2 cümle
    STANDARD = "standard"  # 3-5 cümle
    DETAILED = "detailed"  # Paragraph
    COMPREHENSIVE = "comprehensive"  # Full context


@dataclass
class Message:
    """Tek bir mesaj."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSegment:
    """Conversation segment (özet birimi)."""
    messages: List[Message]
    summary: Optional[str] = None
    key_points: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    importance_score: float = 0.5


@dataclass
class ConversationSummary:
    """Ana özet çıktısı."""
    brief_summary: str
    detailed_summary: str
    key_points: List[str]
    topics: List[str]
    message_count: int
    token_savings: int
    context_window: str  # LLM'e gönderilecek compressed context


class TopicTracker:
    """
    Konuşma konularını takip eder.
    """
    
    def __init__(self):
        self.topic_keywords = {
            "technical": {"code", "programming", "api", "database", "system"},
            "business": {"project", "deadline", "meeting", "budget", "team"},
            "learning": {"explain", "understand", "learn", "example", "how"},
            "creative": {"write", "create", "design", "story", "idea"},
            "support": {"help", "problem", "error", "fix", "issue"},
        }
    
    def extract_topics(self, text: str) -> List[str]:
        """Metinden konuları çıkar."""
        text_lower = text.lower()
        words = set(text_lower.split())
        
        found_topics = []
        for topic, keywords in self.topic_keywords.items():
            if words & keywords:
                found_topics.append(topic)
        
        return found_topics if found_topics else ["general"]
    
    def track_topic_shifts(
        self,
        messages: List[Message]
    ) -> List[Tuple[int, str]]:
        """Topic değişimlerini tespit et."""
        shifts = []
        current_topic = None
        
        for i, msg in enumerate(messages):
            topics = self.extract_topics(msg.content)
            main_topic = topics[0] if topics else "general"
            
            if main_topic != current_topic:
                shifts.append((i, main_topic))
                current_topic = main_topic
        
        return shifts


class KeyPointExtractor:
    """
    Önemli noktaları çıkarır.
    """
    
    def __init__(self):
        # Önemli ifade göstergeleri
        self.importance_indicators = [
            r"\b(important|critical|key|main|essential)\b",
            r"\b(önemli|kritik|ana|temel|asıl)\b",
            r"\b(must|should|need to|have to)\b",
            r"\b(conclusion|result|summary|decision)\b",
            r"\b(sonuç|karar|özet)\b",
            r"^(1\.|2\.|3\.|-|\*)",  # Liste başlangıcı
        ]
        
        # Question patterns
        self.question_patterns = [
            r"\?$",
            r"^(how|what|why|when|where|who)",
            r"^(nasıl|ne|neden|ne zaman|nerede|kim)",
        ]
    
    def extract_key_points(
        self,
        messages: List[Message],
        max_points: int = 5
    ) -> List[str]:
        """Key point'leri çıkar."""
        scored_sentences = []
        
        for msg in messages:
            sentences = self._split_sentences(msg.content)
            for sent in sentences:
                score = self._score_sentence(sent, msg.role)
                if score > 0.3:
                    scored_sentences.append((sent, score))
        
        # En önemli olanları seç
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        key_points = []
        for sent, score in scored_sentences[:max_points]:
            # Kısalt gerekirse
            if len(sent) > 150:
                sent = sent[:147] + "..."
            key_points.append(sent)
        
        return key_points
    
    def _split_sentences(self, text: str) -> List[str]:
        """Cümlelere ayır."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _score_sentence(self, sentence: str, role: MessageRole) -> float:
        """Cümle önem skoru."""
        score = 0.0
        sent_lower = sentence.lower()
        
        # Role bonus
        if role == MessageRole.ASSISTANT:
            score += 0.1  # Assistant yanıtları biraz daha önemli
        
        # Importance indicators
        for pattern in self.importance_indicators:
            if re.search(pattern, sent_lower, re.IGNORECASE):
                score += 0.2
        
        # Question penalty (sorular key point değil)
        for pattern in self.question_patterns:
            if re.search(pattern, sent_lower, re.IGNORECASE):
                score -= 0.3
        
        # Length factor
        word_count = len(sentence.split())
        if word_count < 5:
            score -= 0.2
        elif word_count > 30:
            score += 0.1
        
        return max(0.0, min(1.0, score))


class ConversationSummarizer:
    """
    Ana conversation summarizer.
    
    Uzun konuşmaları özetler ve context window'a sığdırır.
    """
    
    def __init__(
        self,
        max_context_tokens: int = 4096,
        segment_size: int = 10
    ):
        self.max_context_tokens = max_context_tokens
        self.segment_size = segment_size
        self.topic_tracker = TopicTracker()
        self.key_point_extractor = KeyPointExtractor()
        
        # Ortalama karakter/token oranı
        self._chars_per_token = 4
    
    def summarize(
        self,
        messages: List[Message],
        level: SummaryLevel = SummaryLevel.STANDARD
    ) -> ConversationSummary:
        """
        Konuşmayı özetle.
        
        Args:
            messages: Mesaj listesi
            level: Özet detay seviyesi
            
        Returns:
            ConversationSummary
        """
        if not messages:
            return ConversationSummary(
                brief_summary="",
                detailed_summary="",
                key_points=[],
                topics=[],
                message_count=0,
                token_savings=0,
                context_window=""
            )
        
        # 1. Segment'lere ayır
        segments = self._segment_conversation(messages)
        
        # 2. Her segment'i özetle
        for segment in segments:
            segment.summary = self._summarize_segment(segment)
            segment.key_points = self.key_point_extractor.extract_key_points(
                segment.messages, max_points=3
            )
            segment.topics = self._extract_segment_topics(segment)
        
        # 3. Ana özet oluştur
        brief_summary = self._create_brief_summary(segments)
        detailed_summary = self._create_detailed_summary(segments, level)
        
        # 4. Key points birleştir
        all_key_points = []
        for seg in segments:
            all_key_points.extend(seg.key_points)
        # Deduplicate ve limit
        key_points = list(dict.fromkeys(all_key_points))[:10]
        
        # 5. Topics birleştir
        all_topics = []
        for seg in segments:
            all_topics.extend(seg.topics)
        topics = list(dict.fromkeys(all_topics))
        
        # 6. Context window oluştur
        context_window = self._build_context_window(
            segments, messages, level
        )
        
        # 7. Token savings hesapla
        original_tokens = sum(
            len(m.content) // self._chars_per_token
            for m in messages
        )
        summary_tokens = len(context_window) // self._chars_per_token
        token_savings = max(0, original_tokens - summary_tokens)
        
        return ConversationSummary(
            brief_summary=brief_summary,
            detailed_summary=detailed_summary,
            key_points=key_points,
            topics=topics,
            message_count=len(messages),
            token_savings=token_savings,
            context_window=context_window
        )
    
    def incremental_summarize(
        self,
        existing_summary: Optional[str],
        new_messages: List[Message]
    ) -> str:
        """
        Incrementally add to existing summary.
        
        Mevcut özete yeni mesajları ekler.
        """
        if not new_messages:
            return existing_summary or ""
        
        # Yeni mesajları özetle
        new_summary = self._summarize_messages(new_messages)
        
        if not existing_summary:
            return new_summary
        
        # Birleştir
        combined = f"{existing_summary}\n\nRecent: {new_summary}"
        
        # Token kontrolü - gerekirse kısalt
        if len(combined) // self._chars_per_token > self.max_context_tokens // 2:
            combined = self._compress_summary(combined)
        
        return combined
    
    def get_sliding_window(
        self,
        messages: List[Message],
        recent_count: int = 5,
        include_summary: bool = True
    ) -> Tuple[str, List[Message]]:
        """
        Sliding window context: özet + son mesajlar.
        
        Args:
            messages: Tüm mesajlar
            recent_count: Dahil edilecek son mesaj sayısı
            include_summary: Özet dahil edilsin mi
            
        Returns:
            (summary, recent_messages)
        """
        if len(messages) <= recent_count:
            return "", messages
        
        # Eski mesajları özetle
        old_messages = messages[:-recent_count]
        recent_messages = messages[-recent_count:]
        
        if include_summary:
            summary = self._summarize_messages(old_messages)
        else:
            summary = ""
        
        return summary, recent_messages
    
    def _segment_conversation(
        self,
        messages: List[Message]
    ) -> List[ConversationSegment]:
        """Konuşmayı segment'lere ayır."""
        segments = []
        
        # Topic shift'lere göre ayır
        topic_shifts = self.topic_tracker.track_topic_shifts(messages)
        
        if len(topic_shifts) <= 1:
            # Tek topic, fixed-size segmentation
            for i in range(0, len(messages), self.segment_size):
                segment_messages = messages[i:i + self.segment_size]
                segments.append(ConversationSegment(
                    messages=segment_messages
                ))
        else:
            # Topic-based segmentation
            for i, (start_idx, topic) in enumerate(topic_shifts):
                end_idx = topic_shifts[i + 1][0] if i + 1 < len(topic_shifts) else len(messages)
                segment_messages = messages[start_idx:end_idx]
                if segment_messages:
                    segments.append(ConversationSegment(
                        messages=segment_messages,
                        topics=[topic]
                    ))
        
        return segments
    
    def _summarize_segment(self, segment: ConversationSegment) -> str:
        """Tek bir segment'i özetle."""
        if not segment.messages:
            return ""
        
        # User soruları
        questions = [
            m.content for m in segment.messages
            if m.role == MessageRole.USER
        ]
        
        # Assistant yanıtları
        answers = [
            m.content for m in segment.messages
            if m.role == MessageRole.ASSISTANT
        ]
        
        # Kısa özet oluştur
        summary_parts = []
        
        if questions:
            # İlk soruyu özetle
            q_summary = questions[0][:100]
            if len(questions[0]) > 100:
                q_summary += "..."
            summary_parts.append(f"User asked: {q_summary}")
        
        if answers:
            # İlk yanıtın özeti
            a_summary = self._extract_first_sentences(answers[0], 2)
            summary_parts.append(f"Response: {a_summary}")
        
        return " ".join(summary_parts)
    
    def _extract_segment_topics(
        self,
        segment: ConversationSegment
    ) -> List[str]:
        """Segment'ten topic çıkar."""
        all_text = " ".join(m.content for m in segment.messages)
        return self.topic_tracker.extract_topics(all_text)
    
    def _create_brief_summary(
        self,
        segments: List[ConversationSegment]
    ) -> str:
        """Kısa özet oluştur."""
        if not segments:
            return ""
        
        # İlk ve son segment'leri vurgula
        first = segments[0].summary or "Started conversation"
        last = segments[-1].summary or "Continued discussion"
        
        if len(segments) == 1:
            return first
        
        return f"{first} [...] {last}"
    
    def _create_detailed_summary(
        self,
        segments: List[ConversationSegment],
        level: SummaryLevel
    ) -> str:
        """Detaylı özet oluştur."""
        if not segments:
            return ""
        
        parts = []
        
        for i, seg in enumerate(segments):
            if seg.summary:
                if level == SummaryLevel.BRIEF:
                    parts.append(seg.summary)
                elif level == SummaryLevel.STANDARD:
                    parts.append(seg.summary)
                    if seg.key_points:
                        parts.append(f"  Key: {seg.key_points[0]}")
                else:  # DETAILED or COMPREHENSIVE
                    parts.append(f"Segment {i+1}: {seg.summary}")
                    for kp in seg.key_points[:2]:
                        parts.append(f"  - {kp}")
        
        return "\n".join(parts)
    
    def _build_context_window(
        self,
        segments: List[ConversationSegment],
        messages: List[Message],
        level: SummaryLevel
    ) -> str:
        """LLM için context window oluştur."""
        parts = []
        
        # Summary section
        if len(messages) > 5:
            summary = self._create_detailed_summary(segments, level)
            parts.append(f"[Conversation Summary]\n{summary}")
        
        # Recent messages
        recent = messages[-5:] if len(messages) > 5 else messages
        parts.append("\n[Recent Messages]")
        for msg in recent:
            role_prefix = "User" if msg.role == MessageRole.USER else "Assistant"
            parts.append(f"{role_prefix}: {msg.content}")
        
        return "\n".join(parts)
    
    def _summarize_messages(self, messages: List[Message]) -> str:
        """Mesaj listesini özetle."""
        if not messages:
            return ""
        
        # Basit extractive summary
        key_points = self.key_point_extractor.extract_key_points(
            messages, max_points=3
        )
        
        if key_points:
            return "Previous discussion: " + "; ".join(key_points)
        
        # Fallback: ilk ve son mesaj
        first = messages[0].content[:100]
        last = messages[-1].content[:100]
        return f"Discussed: {first}... Recently: {last}..."
    
    def _compress_summary(self, summary: str) -> str:
        """Özeti sıkıştır."""
        sentences = summary.split(". ")
        
        # Her cümlenin ilk yarısını al
        compressed = []
        for sent in sentences[:5]:  # Max 5 cümle
            words = sent.split()
            compressed.append(" ".join(words[:len(words)//2 + 1]))
        
        return ". ".join(compressed) + "."
    
    def _extract_first_sentences(self, text: str, count: int = 2) -> str:
        """İlk n cümleyi çıkar."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = " ".join(sentences[:count])
        
        if len(result) > 200:
            result = result[:197] + "..."
        
        return result


class ConversationMemoryManager:
    """
    Conversation memory yönetimi.
    
    Uzun konuşmalar için memory-efficient context sağlar.
    """
    
    def __init__(
        self,
        summarizer: Optional[ConversationSummarizer] = None,
        max_messages: int = 100
    ):
        self.summarizer = summarizer or ConversationSummarizer()
        self.max_messages = max_messages
        
        # Storage
        self.messages: List[Message] = []
        self.archived_summary: str = ""
        self.archived_count: int = 0
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Mesaj ekle ve gerekirse arşivle."""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata or {}
        ))
        
        # Max aşıldıysa arşivle
        if len(self.messages) > self.max_messages:
            self._archive_old_messages()
    
    def get_context(
        self,
        recent_count: int = 10
    ) -> str:
        """LLM için context al."""
        # Arşiv özeti
        context_parts = []
        
        if self.archived_summary:
            context_parts.append(f"[Previous Context ({self.archived_count} messages)]\n{self.archived_summary}")
        
        # Son mesajlar
        recent = self.messages[-recent_count:]
        context_parts.append("\n[Current Conversation]")
        for msg in recent:
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def get_full_summary(self) -> ConversationSummary:
        """Tam özet al."""
        return self.summarizer.summarize(self.messages)
    
    def _archive_old_messages(self):
        """Eski mesajları arşivle."""
        # Yarısını arşivle
        archive_count = len(self.messages) // 2
        to_archive = self.messages[:archive_count]
        self.messages = self.messages[archive_count:]
        
        # Özet oluştur
        new_summary = self.summarizer.incremental_summarize(
            self.archived_summary,
            to_archive
        )
        
        self.archived_summary = new_summary
        self.archived_count += archive_count
        
        logger.info(f"Archived {archive_count} messages, total archived: {self.archived_count}")
    
    def clear(self):
        """Tamamını temizle."""
        self.messages = []
        self.archived_summary = ""
        self.archived_count = 0


# Singleton instances
conversation_summarizer = ConversationSummarizer()
