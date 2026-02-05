"""
💬 Premium Chat Engine
======================

Endüstri-seviyesi chat deneyimi.
Perplexity AI ve ChatGPT kalitesinde.

Özellikler:
- Auto Follow-up Questions: Otomatik takip soruları
- Conversation Summarization: Uzun sohbetleri özetle
- Smart Context Management: Akıllı bağlam yönetimi
- Source Cards: Zengin kaynak kartları
- Streaming Support: Gerçek zamanlı akış
- Memory Management: Uzun vadeli hafıza
"""

import asyncio
import json
import hashlib
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator
from collections import deque
import threading

# Premium Cache integration
try:
    from core.premium_cache import get_session_cache, SessionCache
    _session_cache: Optional[SessionCache] = None
    CACHE_ENABLED = True
except ImportError:
    _session_cache = None
    CACHE_ENABLED = False

logger = logging.getLogger(__name__)


# ============ ENUMS ============

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class ConversationState(Enum):
    ACTIVE = "active"
    STALE = "stale"
    SUMMARIZED = "summarized"
    ARCHIVED = "archived"


class FollowUpType(Enum):
    CLARIFICATION = "clarification"      # Netleştirme soruları
    DEEPENING = "deepening"              # Derinleştirme
    RELATED = "related"                  # İlgili konular
    PRACTICAL = "practical"              # Pratik sorular
    COMPARISON = "comparison"            # Karşılaştırma


# ============ DATA CLASSES ============

@dataclass
class Message:
    """Chat mesajı"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Metadata
    message_id: str = ""
    tokens: int = 0
    
    # Sources (for assistant messages)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    
    # Follow-ups (for assistant messages)
    follow_ups: List[str] = field(default_factory=list)
    
    # Extra
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = hashlib.md5(
                f"{self.role.value}:{self.content}:{self.timestamp.isoformat()}".encode()
            ).hexdigest()[:12]
        if not self.tokens:
            self.tokens = len(self.content.split()) * 1.3  # Rough estimate


@dataclass
class SourceCard:
    """Zengin kaynak kartı"""
    title: str
    url: str
    domain: str
    snippet: str
    
    # Visual
    favicon: str = ""
    preview_image: str = ""
    
    # Quality
    quality_score: float = 0.5
    relevance_score: float = 0.5
    
    # Type
    source_type: str = "web"  # academic, news, official, blog
    type_icon: str = "🌐"
    
    # Citation
    citation_index: int = 0
    citation_key: str = ""  # [A], [B], [C.1]
    
    # Extra
    author: str = ""
    date: str = ""
    word_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "domain": self.domain,
            "snippet": self.snippet[:200],
            "favicon": self.favicon,
            "preview_image": self.preview_image,
            "quality_score": self.quality_score,
            "relevance_score": self.relevance_score,
            "source_type": self.source_type,
            "type_icon": self.type_icon,
            "citation_index": self.citation_index,
            "citation_key": self.citation_key,
            "author": self.author,
            "date": self.date,
        }


@dataclass
class FollowUpQuestion:
    """Takip sorusu"""
    question: str
    type: FollowUpType
    relevance_score: float = 0.8
    
    # Visual hint
    icon: str = "❓"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "type": self.type.value,
            "icon": self.icon,
            "relevance_score": self.relevance_score,
        }


@dataclass
class ConversationSummary:
    """Sohbet özeti"""
    summary: str
    key_topics: List[str]
    key_facts: List[str]
    user_intents: List[str]
    
    # Stats
    message_count: int = 0
    summarized_at: datetime = field(default_factory=datetime.now)
    token_count_before: int = 0
    token_count_after: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "key_topics": self.key_topics,
            "key_facts": self.key_facts,
            "user_intents": self.user_intents,
            "message_count": self.message_count,
            "summarized_at": self.summarized_at.isoformat(),
            "compression_ratio": self.token_count_after / max(1, self.token_count_before),
        }


# ============ FOLLOW-UP GENERATOR ============

class FollowUpGenerator:
    """
    Otomatik takip sorusu üreteci.
    
    Perplexity AI tarzında kullanıcıya yardımcı olacak
    akıllı takip soruları üretir.
    """
    
    # Template patterns by type
    TEMPLATES = {
        FollowUpType.CLARIFICATION: [
            "'{topic}' hakkında daha spesifik bir soru sormak ister misiniz?",
            "Hangi yönünü daha detaylı açıklamamı istersiniz?",
            "Bu konuda belirli bir örnek ister misiniz?",
        ],
        FollowUpType.DEEPENING: [
            "{topic} nasıl çalışır?",
            "{topic} örnekleri nelerdir?",
            "{topic} avantajları ve dezavantajları nelerdir?",
            "{topic} en iyi pratikleri nelerdir?",
        ],
        FollowUpType.RELATED: [
            "{related_topic} hakkında da bilgi almak ister misiniz?",
            "Bunun {related_topic} ile ilişkisi nedir?",
            "{topic} alternatiflerini inceleyelim mi?",
        ],
        FollowUpType.PRACTICAL: [
            "{topic} nasıl uygulanır?",
            "{topic} için adım adım rehber ister misiniz?",
            "Gerçek dünya {topic} örnekleri görelim mi?",
            "{topic} için başlangıç kılavuzu hazırlayayım mı?",
        ],
        FollowUpType.COMPARISON: [
            "{topic_a} vs {topic_b} karşılaştırması yapalım mı?",
            "Farklı {topic} seçeneklerini karşılaştıralım mı?",
            "Hangi {topic} sizin için daha uygun?",
        ],
    }
    
    # Icons for types
    TYPE_ICONS = {
        FollowUpType.CLARIFICATION: "🔍",
        FollowUpType.DEEPENING: "📚",
        FollowUpType.RELATED: "🔗",
        FollowUpType.PRACTICAL: "🛠️",
        FollowUpType.COMPARISON: "⚖️",
    }
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def generate(
        self,
        query: str,
        response: str,
        context: Optional[Dict] = None,
        num_questions: int = 3,
    ) -> List[FollowUpQuestion]:
        """
        Takip soruları üret.
        
        Args:
            query: Kullanıcının sorusu
            response: AI'ın yanıtı
            context: Ek bağlam (conversation history, sources)
            num_questions: Üretilecek soru sayısı
            
        Returns:
            List[FollowUpQuestion]
        """
        questions = []
        
        # 1. Extract topics from query and response
        topics = self._extract_topics(query, response)
        
        if not topics:
            topics = ["konu"]
        
        # 2. Try LLM-based generation first
        llm_questions = await self._generate_with_llm(query, response, topics, num_questions)
        if llm_questions:
            questions.extend(llm_questions)
        
        # 3. Template-based fallback
        if len(questions) < num_questions:
            template_questions = self._generate_from_templates(topics, num_questions - len(questions))
            questions.extend(template_questions)
        
        # 4. Score and sort
        questions = self._score_questions(questions, query, response)
        
        return questions[:num_questions]
    
    def _extract_topics(self, query: str, response: str) -> List[str]:
        """Konuları çıkar"""
        # Simple keyword extraction
        text = f"{query} {response}"
        
        # Common words to ignore
        stop_words = {
            "bir", "ve", "veya", "ile", "için", "bu", "şu", "o", "da", "de",
            "mi", "mı", "mu", "mü", "ne", "nasıl", "neden", "kim", "nerede",
            "çok", "daha", "en", "gibi", "kadar", "olarak", "olan", "oldu",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "to", "of", "and", "or", "in", "on", "at", "for", "with",
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}\b', text.lower())
        
        # Count frequencies
        freq = {}
        for word in words:
            if word not in stop_words:
                freq[word] = freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_words[:5]]
    
    async def _generate_with_llm(
        self,
        query: str,
        response: str,
        topics: List[str],
        num_questions: int
    ) -> List[FollowUpQuestion]:
        """LLM ile takip soruları üret"""
        if not self.llm_client:
            return []
        
        prompt = f"""Based on this conversation, generate {num_questions} follow-up questions 
that the user might want to ask next. Make them specific and helpful.

User Question: {query[:500]}
AI Response: {response[:1000]}
Main Topics: {', '.join(topics)}

Generate exactly {num_questions} follow-up questions in the same language as the user's question.
Format: One question per line, no numbering.

Follow-up Questions:"""
        
        try:
            llm_response = await self._call_llm(prompt)
            
            questions = []
            for line in llm_response.strip().split('\n'):
                line = line.strip()
                if line and '?' in line:
                    # Clean up
                    line = re.sub(r'^[\d\.\-\*\•]+\s*', '', line)
                    
                    # Determine type
                    q_type = self._classify_question_type(line)
                    
                    questions.append(FollowUpQuestion(
                        question=line,
                        type=q_type,
                        icon=self.TYPE_ICONS.get(q_type, "❓"),
                        relevance_score=0.8,
                    ))
            
            return questions
        except Exception as e:
            logger.warning(f"LLM follow-up generation failed: {e}")
            return []
    
    def _generate_from_templates(
        self,
        topics: List[str],
        num_questions: int
    ) -> List[FollowUpQuestion]:
        """Template'lerden takip soruları üret"""
        questions = []
        topic = topics[0] if topics else "konu"
        
        for q_type, templates in self.TEMPLATES.items():
            if len(questions) >= num_questions:
                break
            
            template = templates[0]  # Use first template
            
            try:
                question = template.format(
                    topic=topic,
                    related_topic=topics[1] if len(topics) > 1 else topic,
                    topic_a=topics[0] if topics else "A",
                    topic_b=topics[1] if len(topics) > 1 else "B",
                )
                
                questions.append(FollowUpQuestion(
                    question=question,
                    type=q_type,
                    icon=self.TYPE_ICONS.get(q_type, "❓"),
                    relevance_score=0.6,
                ))
            except Exception:
                continue
        
        return questions
    
    def _classify_question_type(self, question: str) -> FollowUpType:
        """Soru türünü sınıflandır"""
        q_lower = question.lower()
        
        if any(w in q_lower for w in ["nasıl yapılır", "adımlar", "how to", "steps"]):
            return FollowUpType.PRACTICAL
        elif any(w in q_lower for w in ["vs", "karşılaştır", "fark", "compare", "difference"]):
            return FollowUpType.COMPARISON
        elif any(w in q_lower for w in ["örnek", "detay", "açıkla", "example", "detail"]):
            return FollowUpType.DEEPENING
        elif any(w in q_lower for w in ["ilgili", "bağlantı", "related", "connection"]):
            return FollowUpType.RELATED
        else:
            return FollowUpType.CLARIFICATION
    
    def _score_questions(
        self,
        questions: List[FollowUpQuestion],
        query: str,
        response: str
    ) -> List[FollowUpQuestion]:
        """Soruları skorla ve sırala"""
        # Simple scoring based on diversity and relevance
        for i, q in enumerate(questions):
            # Diversity bonus for different types
            type_counts = {}
            for prev_q in questions[:i]:
                type_counts[prev_q.type] = type_counts.get(prev_q.type, 0) + 1
            
            if q.type not in type_counts:
                q.relevance_score += 0.1
            
            # Length check (not too short, not too long)
            if 20 < len(q.question) < 100:
                q.relevance_score += 0.05
        
        # Sort by score
        questions.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return questions
    
    async def _call_llm(self, prompt: str) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=300)
            except Exception:
                pass
        
        # Fallback to Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 200, "temperature": 0.7}
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception:
            pass
        
        return ""


# ============ CONVERSATION SUMMARIZER ============

class ConversationSummarizer:
    """
    Sohbet özetleyici.
    
    Uzun sohbetleri özetleyerek context window'u optimize eder.
    """
    
    def __init__(
        self,
        llm_client=None,
        summary_threshold: int = 10,  # Bu kadar mesajdan sonra özetle
        max_context_tokens: int = 4000,  # Maksimum context token
    ):
        self.llm_client = llm_client
        self.summary_threshold = summary_threshold
        self.max_context_tokens = max_context_tokens
    
    async def summarize(
        self,
        messages: List[Message],
        preserve_recent: int = 4,  # Son N mesajı koru
    ) -> ConversationSummary:
        """
        Sohbeti özetle.
        
        Args:
            messages: Mesaj listesi
            preserve_recent: Korunacak son mesaj sayısı
            
        Returns:
            ConversationSummary
        """
        if len(messages) <= preserve_recent:
            return ConversationSummary(
                summary="Sohbet özetlenemeyecek kadar kısa.",
                key_topics=[],
                key_facts=[],
                user_intents=[],
                message_count=len(messages),
            )
        
        # Messages to summarize (exclude recent)
        to_summarize = messages[:-preserve_recent] if preserve_recent > 0 else messages
        
        # Calculate tokens before
        token_count_before = sum(m.tokens for m in to_summarize)
        
        # Extract key information
        key_topics = self._extract_key_topics(to_summarize)
        user_intents = self._extract_user_intents(to_summarize)
        key_facts = self._extract_key_facts(to_summarize)
        
        # Generate summary
        summary = await self._generate_summary(to_summarize, key_topics)
        
        # Calculate tokens after
        token_count_after = len(summary.split()) * 1.3
        
        return ConversationSummary(
            summary=summary,
            key_topics=key_topics,
            key_facts=key_facts,
            user_intents=user_intents,
            message_count=len(to_summarize),
            token_count_before=int(token_count_before),
            token_count_after=int(token_count_after),
        )
    
    def should_summarize(self, messages: List[Message]) -> bool:
        """Özetleme gerekli mi?"""
        if len(messages) < self.summary_threshold:
            return False
        
        total_tokens = sum(m.tokens for m in messages)
        return total_tokens > self.max_context_tokens * 0.8
    
    def _extract_key_topics(self, messages: List[Message]) -> List[str]:
        """Ana konuları çıkar"""
        all_text = " ".join(m.content for m in messages)
        
        # Simple keyword extraction
        stop_words = {"bir", "ve", "veya", "ile", "için", "bu", "şu", "the", "a", "an", "is", "are"}
        
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}\b', all_text.lower())
        freq = {}
        for word in words:
            if word not in stop_words:
                freq[word] = freq.get(word, 0) + 1
        
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:5]]
    
    def _extract_user_intents(self, messages: List[Message]) -> List[str]:
        """Kullanıcı niyetlerini çıkar"""
        intents = []
        
        for m in messages:
            if m.role == MessageRole.USER:
                content = m.content.lower()
                
                if any(w in content for w in ["nasıl", "how"]):
                    intents.append("öğrenme")
                elif any(w in content for w in ["nedir", "what is"]):
                    intents.append("tanım alma")
                elif any(w in content for w in ["örnek", "example"]):
                    intents.append("örnek isteme")
                elif any(w in content for w in ["yardım", "help"]):
                    intents.append("yardım isteme")
        
        return list(set(intents))[:3]
    
    def _extract_key_facts(self, messages: List[Message]) -> List[str]:
        """Önemli bilgileri çıkar"""
        facts = []
        
        for m in messages:
            if m.role == MessageRole.ASSISTANT:
                # Look for sentences with important markers
                sentences = m.content.split('.')
                for sent in sentences:
                    if any(w in sent.lower() for w in ["önemli", "dikkat", "not:", "important", "note:"]):
                        facts.append(sent.strip()[:100])
        
        return facts[:5]
    
    async def _generate_summary(
        self,
        messages: List[Message],
        key_topics: List[str]
    ) -> str:
        """LLM ile özet oluştur"""
        # Build conversation text
        conv_text = ""
        for m in messages:
            role = "User" if m.role == MessageRole.USER else "Assistant"
            conv_text += f"{role}: {m.content[:200]}...\n"
        
        prompt = f"""Summarize this conversation concisely. 
Focus on: main questions asked, key information provided, and conclusions reached.
Keep the summary under 200 words.

Key Topics: {', '.join(key_topics)}

Conversation:
{conv_text[:2000]}

Summary:"""
        
        try:
            summary = await self._call_llm(prompt)
            return summary.strip()
        except Exception:
            # Fallback: Simple extraction
            user_questions = [m.content[:100] for m in messages if m.role == MessageRole.USER][:3]
            return f"Kullanıcı şu konuları sordu: {'; '.join(user_questions)}"
    
    async def _call_llm(self, prompt: str) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=250)
            except Exception:
                pass
        
        # Fallback to Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 200, "temperature": 0.3}
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception:
            pass
        
        return "Özet oluşturulamadı."


# ============ SOURCE CARD GENERATOR ============

class SourceCardGenerator:
    """
    Zengin kaynak kartları oluşturucu.
    
    Perplexity AI tarzında görsel kaynak kartları.
    """
    
    # Source type icons
    TYPE_ICONS = {
        "academic": "🎓",
        "news": "📰",
        "official": "🏛️",
        "wiki": "📚",
        "blog": "✍️",
        "forum": "💬",
        "code": "💻",
        "video": "🎬",
        "social": "🐦",
        "ecommerce": "🛒",
        "web": "🌐",
    }
    
    # Domain classifications
    DOMAIN_TYPES = {
        "wikipedia.org": "wiki",
        "arxiv.org": "academic",
        "scholar.google": "academic",
        "github.com": "code",
        "stackoverflow.com": "code",
        "reddit.com": "forum",
        "twitter.com": "social",
        "youtube.com": "video",
        "medium.com": "blog",
        "bbc.com": "news",
        "reuters.com": "news",
        "cnn.com": "news",
        "gov": "official",
        "edu": "academic",
    }
    
    def generate_cards(
        self,
        sources: List[Dict[str, Any]],
        max_cards: int = 6,
    ) -> List[SourceCard]:
        """
        Kaynak kartları oluştur.
        
        Args:
            sources: Kaynak listesi
            max_cards: Maksimum kart sayısı
            
        Returns:
            List[SourceCard]
        """
        cards = []
        
        for i, source in enumerate(sources[:max_cards], 1):
            card = self._create_card(source, i)
            cards.append(card)
        
        return cards
    
    def _create_card(self, source: Dict[str, Any], index: int) -> SourceCard:
        """Tek bir kart oluştur"""
        url = source.get("url", "")
        domain = self._extract_domain(url)
        source_type = self._classify_source(url, domain)
        
        # Generate citation key
        citation_key = self._generate_citation_key(index)
        
        # Get favicon
        favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
        
        return SourceCard(
            title=source.get("title", "Untitled")[:100],
            url=url,
            domain=domain,
            snippet=source.get("snippet", "")[:200],
            favicon=favicon,
            quality_score=source.get("quality_score", source.get("reliability_score", 0.5)),
            relevance_score=source.get("relevance_score", source.get("score", 0.5)),
            source_type=source_type,
            type_icon=self.TYPE_ICONS.get(source_type, "🌐"),
            citation_index=index,
            citation_key=citation_key,
            author=source.get("author", ""),
            date=source.get("date", source.get("published_date", "")),
            word_count=source.get("word_count", 0),
        )
    
    def _extract_domain(self, url: str) -> str:
        """Domain çıkar"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return "unknown"
    
    def _classify_source(self, url: str, domain: str) -> str:
        """Kaynağı sınıflandır"""
        url_lower = url.lower()
        domain_lower = domain.lower()
        
        for pattern, source_type in self.DOMAIN_TYPES.items():
            if pattern in domain_lower or pattern in url_lower:
                return source_type
        
        return "web"
    
    def _generate_citation_key(self, index: int) -> str:
        """Citation key oluştur (A, B, C...)"""
        if index <= 26:
            return chr(64 + index)  # A=65
        else:
            first = chr(64 + (index - 1) // 26)
            second = chr(65 + (index - 1) % 26)
            return f"{first}{second}"
    
    def format_citations_for_response(
        self,
        cards: List[SourceCard],
        format: str = "inline"
    ) -> str:
        """
        Yanıt için citation formatı.
        
        Args:
            cards: Kaynak kartları
            format: "inline", "footnote", "endnote"
            
        Returns:
            Formatlanmış citation metni
        """
        if format == "inline":
            return self._format_inline(cards)
        elif format == "footnote":
            return self._format_footnote(cards)
        else:  # endnote
            return self._format_endnote(cards)
    
    def _format_inline(self, cards: List[SourceCard]) -> str:
        """Inline citation formatı"""
        lines = []
        for card in cards:
            lines.append(f"[{card.citation_key}]: {card.title} ({card.domain})")
        return "\n".join(lines)
    
    def _format_footnote(self, cards: List[SourceCard]) -> str:
        """Footnote formatı"""
        lines = ["", "---", "**Kaynaklar:**"]
        for card in cards:
            lines.append(f"[{card.citation_key}] {card.title}. {card.url}")
        return "\n".join(lines)
    
    def _format_endnote(self, cards: List[SourceCard]) -> str:
        """Endnote formatı"""
        lines = ["", "---", "📚 **KAYNAKLAR**", ""]
        for card in cards:
            author = f"{card.author}. " if card.author else ""
            date = f"({card.date}). " if card.date else ""
            lines.append(f"**[{card.citation_key}]** {author}{date}{card.title}. {card.domain}")
            lines.append(f"   URL: {card.url}")
            lines.append("")
        return "\n".join(lines)


# ============ CONTEXT MANAGER ============

class SmartContextManager:
    """
    Akıllı bağlam yöneticisi.
    
    - Context window optimizasyonu
    - Relevant history selection
    - Memory management
    - Session Persistence (disk cache)
    """
    
    def __init__(
        self,
        max_tokens: int = 4096,
        summarizer: Optional[ConversationSummarizer] = None,
        enable_persistence: bool = True,
    ):
        self.max_tokens = max_tokens
        self.summarizer = summarizer or ConversationSummarizer()
        self.enable_persistence = enable_persistence and CACHE_ENABLED
        
        # Memory
        self.summaries: Dict[str, ConversationSummary] = {}
        self.important_facts: List[str] = []
        
        # Initialize session cache
        if self.enable_persistence:
            global _session_cache
            if _session_cache is None:
                _session_cache = get_session_cache()
    
    def save_session(
        self,
        session_id: str,
        messages: List[Message],
        metadata: Dict[str, Any] = None,
    ):
        """Session'\u0131 disk'e kaydet"""
        if not self.enable_persistence:
            return
        
        try:
            # Serialize messages
            serialized_messages = []
            for m in messages:
                msg_dict = {
                    "role": m.role.value,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "message_id": m.message_id,
                    "tokens": m.tokens,
                    "sources": m.sources,
                    "follow_ups": m.follow_ups,
                }
                serialized_messages.append(msg_dict)
            
            # Build session data
            session_data = {
                "session_id": session_id,
                "messages": serialized_messages,
                "message_count": len(messages),
                "created_at": messages[0].timestamp.isoformat() if messages else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": metadata or {},
            }
            
            # Add summary if exists
            if session_id in self.summaries:
                summary = self.summaries[session_id]
                session_data["summary"] = summary.to_dict()
            
            # Save to cache
            _session_cache.save_session(session_id, session_data)
            logger.debug(f"Session saved: {session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save session {session_id}: {e}")
    
    def load_session(self, session_id: str) -> Optional[Tuple[List[Message], Dict]]:
        """Session'\u0131 disk'ten yükle"""
        if not self.enable_persistence:
            return None
        
        try:
            session_data = _session_cache.get_session(session_id)
            if not session_data:
                return None
            
            # Deserialize messages
            messages = []
            for msg_dict in session_data.get("messages", []):
                msg = Message(
                    role=MessageRole(msg_dict["role"]),
                    content=msg_dict["content"],
                    timestamp=datetime.fromisoformat(msg_dict["timestamp"]),
                    message_id=msg_dict.get("message_id", ""),
                    tokens=msg_dict.get("tokens", 0),
                    sources=msg_dict.get("sources", []),
                    follow_ups=msg_dict.get("follow_ups", []),
                )
                messages.append(msg)
            
            # Load summary if exists
            if "summary" in session_data:
                s = session_data["summary"]
                self.summaries[session_id] = ConversationSummary(
                    summary=s.get("summary", ""),
                    key_topics=s.get("key_topics", []),
                    key_facts=s.get("key_facts", []),
                    user_intents=s.get("user_intents", []),
                    message_count=s.get("message_count", 0),
                )
            
            logger.debug(f"Session loaded: {session_id} ({len(messages)} messages)")
            return messages, session_data.get("metadata", {})
            
        except Exception as e:
            logger.warning(f"Failed to load session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str):
        """Session'\u0131 sil"""
        if self.enable_persistence:
            _session_cache.delete_session(session_id)
        
        if session_id in self.summaries:
            del self.summaries[session_id]
        
        logger.debug(f"Session deleted: {session_id}")
    
    async def build_context(
        self,
        session_id: str,
        messages: List[Message],
        current_query: str,
        sources: List[Dict] = None,
    ) -> str:
        """
        Optimize edilmiş context oluştur.
        
        Args:
            session_id: Oturum ID
            messages: Mesaj geçmişi
            current_query: Mevcut sorgu
            sources: RAG kaynakları
            
        Returns:
            Optimize edilmiş context string
        """
        context_parts = []
        
        # 1. Summary (if exists)
        if session_id in self.summaries:
            summary = self.summaries[session_id]
            context_parts.append(f"""### Önceki Sohbet Özeti:
{summary.summary}
Ana Konular: {', '.join(summary.key_topics)}
""")
        
        # 2. Recent conversation (last N messages)
        recent_messages = self._select_relevant_messages(messages, current_query)
        if recent_messages:
            context_parts.append("### Son Konuşma:")
            for m in recent_messages:
                role = "Kullanıcı" if m.role == MessageRole.USER else "Asistan"
                context_parts.append(f"{role}: {m.content[:500]}")
        
        # 3. Sources
        if sources:
            context_parts.append("\n### İlgili Kaynaklar:")
            for i, s in enumerate(sources[:20], 1):
                content = s.get("content") or s.get("document", "")
                context_parts.append(f"[{i}] {s.get('title', 'Kaynak')}: {content[:500]}...")
        
        # 4. Important facts from memory
        if self.important_facts:
            context_parts.append(f"\n### Önemli Bilgiler:\n" + "\n".join(self.important_facts[:5]))
        
        # Build final context
        context = "\n\n".join(context_parts)
        
        # Truncate if needed
        if len(context.split()) > self.max_tokens * 0.75:
            context = self._truncate_context(context)
        
        return context
    
    def _select_relevant_messages(
        self,
        messages: List[Message],
        current_query: str,
        max_messages: int = 10,
    ) -> List[Message]:
        """İlgili mesajları seç"""
        if len(messages) <= max_messages:
            return messages
        
        # Always keep last few messages
        recent = messages[-4:]
        
        # Score older messages by relevance
        query_words = set(current_query.lower().split())
        scored = []
        
        for m in messages[:-4]:
            score = 0
            content_words = set(m.content.lower().split())
            overlap = len(query_words & content_words)
            score += overlap * 2
            
            # Bonus for user questions
            if m.role == MessageRole.USER:
                score += 1
            
            scored.append((m, score))
        
        # Sort by score and take top
        scored.sort(key=lambda x: x[1], reverse=True)
        relevant = [m for m, _ in scored[:max_messages - 4]]
        
        # Combine and sort by timestamp
        all_messages = relevant + list(recent)
        all_messages.sort(key=lambda x: x.timestamp)
        
        return all_messages
    
    def _truncate_context(self, context: str) -> str:
        """Context'i akıllıca kısalt"""
        lines = context.split('\n')
        
        # Keep headers and first line of each section
        truncated = []
        for i, line in enumerate(lines):
            if line.startswith('#') or line.startswith('**'):
                truncated.append(line)
            elif i > 0 and lines[i-1].startswith('#'):
                truncated.append(line[:200] + "...")
            elif len(truncated) < 20:
                truncated.append(line[:100])
        
        return '\n'.join(truncated)
    
    async def update_memory(
        self,
        session_id: str,
        messages: List[Message],
    ):
        """Hafızayı güncelle"""
        # Check if summarization needed
        if self.summarizer.should_summarize(messages):
            summary = await self.summarizer.summarize(messages)
            self.summaries[session_id] = summary
            
            # Extract important facts
            self.important_facts.extend(summary.key_facts)
            self.important_facts = self.important_facts[-10:]  # Keep last 10


# ============ PREMIUM CHAT ENGINE ============

class PremiumChatEngine:
    """
    Premium Chat Engine.
    
    Tüm premium chat özelliklerini birleştirir.
    Session persistence ile kalıcı oturumlar.
    """
    
    def __init__(self, llm_client=None, enable_persistence: bool = True):
        self.llm_client = llm_client
        self.enable_persistence = enable_persistence
        
        # Components
        self.follow_up_generator = FollowUpGenerator(llm_client)
        self.summarizer = ConversationSummarizer(llm_client)
        self.source_card_generator = SourceCardGenerator()
        self.context_manager = SmartContextManager(
            summarizer=self.summarizer,
            enable_persistence=enable_persistence
        )
        
        # Active sessions (memory cache)
        self._sessions: Dict[str, List[Message]] = {}
    
    def get_or_create_session(self, session_id: str) -> List[Message]:
        """Session al veya oluştur (persistence ile)"""
        # Memory cache check
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # Try loading from disk
        loaded = self.context_manager.load_session(session_id)
        if loaded:
            messages, metadata = loaded
            self._sessions[session_id] = messages
            logger.info(f"Session loaded from disk: {session_id}")
            return messages
        
        # Create new session
        self._sessions[session_id] = []
        return self._sessions[session_id]
    
    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        sources: List[Dict] = None,
        follow_ups: List[str] = None,
        auto_save: bool = True,
    ) -> Message:
        """Session'a mesaj ekle"""
        messages = self.get_or_create_session(session_id)
        
        msg = Message(
            role=role,
            content=content,
            sources=sources or [],
            follow_ups=follow_ups or [],
        )
        
        messages.append(msg)
        
        # Auto-save to disk
        if auto_save and self.enable_persistence:
            self.save_session(session_id)
        
        return msg
    
    def save_session(self, session_id: str, metadata: Dict = None):
        """Session'ı disk'e kaydet"""
        if session_id not in self._sessions:
            return
        
        self.context_manager.save_session(
            session_id,
            self._sessions[session_id],
            metadata
        )
    
    def clear_session(self, session_id: str):
        """Session'ı temizle ve sil"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        self.context_manager.delete_session(session_id)
    
    async def process_response(
        self,
        query: str,
        response: str,
        sources: List[Dict] = None,
        messages: List[Message] = None,
        session_id: str = "",
    ) -> Dict[str, Any]:
        """
        Yanıtı işle ve premium özellikler ekle.
        
        Args:
            query: Kullanıcı sorusu
            response: AI yanıtı
            sources: Kullanılan kaynaklar
            messages: Mesaj geçmişi
            session_id: Oturum ID
            
        Returns:
            Dict with enhanced response data
        """
        result = {
            "response": response,
            "follow_ups": [],
            "source_cards": [],
            "citations": "",
            "metadata": {},
        }
        
        # 1. Generate follow-up questions
        follow_ups = await self.follow_up_generator.generate(query, response)
        result["follow_ups"] = [f.to_dict() for f in follow_ups]
        
        # 2. Generate source cards
        if sources:
            cards = self.source_card_generator.generate_cards(sources)
            result["source_cards"] = [c.to_dict() for c in cards]
            result["citations"] = self.source_card_generator.format_citations_for_response(
                cards, format="footnote"
            )
        
        # 3. Update memory
        if messages and session_id:
            await self.context_manager.update_memory(session_id, messages)
        
        # 4. Check if summary needed
        if messages and self.summarizer.should_summarize(messages):
            result["metadata"]["needs_summarization"] = True
        
        return result
    
    async def build_context(
        self,
        session_id: str,
        messages: List[Message],
        query: str,
        sources: List[Dict] = None,
    ) -> str:
        """Optimize edilmiş context oluştur"""
        return await self.context_manager.build_context(
            session_id, messages, query, sources
        )


# ============ SINGLETON ============

_chat_engine: Optional[PremiumChatEngine] = None

def get_premium_chat_engine() -> PremiumChatEngine:
    global _chat_engine
    if _chat_engine is None:
        _chat_engine = PremiumChatEngine()
    return _chat_engine


# ============ TEST ============

async def test_chat_engine():
    """Test premium chat engine"""
    print("Testing Premium Chat Engine...")
    
    engine = get_premium_chat_engine()
    
    query = "Python'da async programlama nasıl yapılır?"
    response = """Python'da async programlama asyncio modülü ile yapılır. 
    async/await syntax'ı kullanılır. Önce async def ile bir coroutine tanımlanır,
    sonra await ile çağrılır. asyncio.run() ile ana coroutine başlatılır."""
    
    sources = [
        {"title": "Python asyncio docs", "url": "https://docs.python.org/asyncio", "snippet": "Official docs"},
        {"title": "Real Python Tutorial", "url": "https://realpython.com/async-io", "snippet": "Tutorial"},
    ]
    
    result = await engine.process_response(query, response, sources)
    
    print(f"\nFollow-ups:")
    for f in result["follow_ups"]:
        print(f"  {f['icon']} {f['question']}")
    
    print(f"\nSource Cards:")
    for c in result["source_cards"]:
        print(f"  [{c['citation_key']}] {c['type_icon']} {c['title']}")
    
    print(f"\nCitations:\n{result['citations']}")


if __name__ == "__main__":
    asyncio.run(test_chat_engine())
