"""
🎯 Enterprise Token Manager
===========================

Premium token yönetimi sistemi:
- Gerçek tokenizer ile doğru token sayımı (tiktoken fallback)
- Token budget allocation
- Priority-based context truncation
- Token usage analytics

Author: Enterprise AI Team
Version: 1.0.0
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger(__name__)


# ============================================================================
# TOKEN COUNTER - ENTERPRISE GRADE
# ============================================================================

@dataclass
class TokenUsageStats:
    """Token kullanım istatistikleri."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0
    requests_count: int = 0
    avg_input_tokens: float = 0.0
    avg_output_tokens: float = 0.0
    peak_input_tokens: int = 0
    peak_output_tokens: int = 0
    
    def update(self, input_tokens: int, output_tokens: int, cached: bool = False):
        """İstatistikleri güncelle."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        if cached:
            self.total_cached_tokens += input_tokens
        self.requests_count += 1
        self.avg_input_tokens = self.total_input_tokens / self.requests_count
        self.avg_output_tokens = self.total_output_tokens / self.requests_count
        self.peak_input_tokens = max(self.peak_input_tokens, input_tokens)
        self.peak_output_tokens = max(self.peak_output_tokens, output_tokens)


class EnterpriseTokenManager:
    """
    Enterprise-grade token yönetimi.
    
    Features:
    - Model-specific tokenizer desteği
    - Real tokenizer (tiktoken) + fallback
    - Token budget management
    - Priority-based context truncation
    - Usage analytics
    """
    
    # Model-specific token limits
    MODEL_CONTEXT_LIMITS = {
        # Llama models
        "llama3.2": 131072,
        "llama3.1": 131072,
        "llama3": 8192,
        "llama2": 4096,
        # Mistral models
        "mistral": 32768,
        "mixtral": 32768,
        "mistral-nemo": 128000,
        # Qwen models
        "qwen3": 32768,
        "qwen2.5": 32768,
        "qwen2": 32768,
        "qwen": 8192,
        # Other models
        "phi3": 128000,
        "phi": 2048,
        "gemma3": 8192,
        "gemma2": 8192,
        "gemma": 8192,
        "deepseek": 65536,
        "deepseek-r1": 65536,
        "command-r": 128000,
        # Default
        "default": 8192,
    }
    
    # Approximate chars per token for fallback
    CHARS_PER_TOKEN = {
        "llama": 4.0,
        "mistral": 4.0,
        "qwen": 3.5,
        "phi": 3.8,
        "gemma": 4.0,
        "deepseek": 4.0,
        "default": 4.0,
    }
    
    def __init__(self):
        self._tokenizer = None
        self._tokenizer_type = "fallback"
        self._stats = TokenUsageStats()
        self._model_stats: Dict[str, TokenUsageStats] = {}
        self._init_tokenizer()
    
    def _init_tokenizer(self):
        """Tokenizer'ı başlat (tiktoken tercih edilir)."""
        try:
            import tiktoken
            # cl100k_base: GPT-4, GPT-3.5-turbo için kullanılan encoding
            # Llama ve diğer modeller için de iyi bir yaklaşım
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
            self._tokenizer_type = "tiktoken"
            logger.info("✅ tiktoken tokenizer initialized (cl100k_base)")
        except ImportError:
            logger.warning("⚠️ tiktoken not available, using character-based fallback")
            self._tokenizer = None
            self._tokenizer_type = "fallback"
    
    def count_tokens(self, text: str, model: str = "default") -> int:
        """
        Metindeki token sayısını hesapla.
        
        Args:
            text: Token sayılacak metin
            model: Model adı (daha doğru hesaplama için)
            
        Returns:
            Token sayısı
        """
        if not text:
            return 0
        
        if self._tokenizer_type == "tiktoken" and self._tokenizer:
            try:
                return len(self._tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"tiktoken encode error: {e}, using fallback")
        
        # Fallback: karakter tabanlı tahmin
        model_type = self._get_model_type(model)
        chars_per_token = self.CHARS_PER_TOKEN.get(model_type, 4.0)
        return int(len(text) / chars_per_token)
    
    def count_messages_tokens(self, messages: List[Dict[str, str]], model: str = "default") -> int:
        """
        Mesaj listesindeki toplam token sayısı.
        
        Her mesaj için ~4 token overhead eklenir (role, formatting).
        """
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            # Role için overhead: ~4 token
            total += 4 + self.count_tokens(content, model)
        return total
    
    def get_context_limit(self, model: str) -> int:
        """Model için context limit'i döndür."""
        model_lower = model.lower()
        
        for key, limit in self.MODEL_CONTEXT_LIMITS.items():
            if key in model_lower:
                return limit
        
        return self.MODEL_CONTEXT_LIMITS["default"]
    
    def _get_model_type(self, model: str) -> str:
        """Model tipini belirle."""
        model_lower = model.lower()
        for key in self.CHARS_PER_TOKEN.keys():
            if key in model_lower:
                return key
        return "default"
    
    # ========================================================================
    # TOKEN BUDGET MANAGEMENT
    # ========================================================================
    
    def allocate_budget(
        self,
        model: str,
        system_prompt_tokens: int = 0,
        reserve_output_tokens: int = 4096,
        min_context_tokens: int = 1000,
    ) -> Dict[str, int]:
        """
        Token budget'ını akıllıca dağıt.
        
        Args:
            model: Kullanılacak model
            system_prompt_tokens: System prompt için ayrılan tokenlar
            reserve_output_tokens: Yanıt için ayrılan tokenlar
            min_context_tokens: Minimum context token sayısı
            
        Returns:
            Budget dağılımı
        """
        total_limit = self.get_context_limit(model)
        
        # Önceliklere göre dağıt
        budget = {
            "total": total_limit,
            "system_prompt": system_prompt_tokens,
            "output_reserve": reserve_output_tokens,
            "available_for_context": 0,
            "history": 0,
            "rag": 0,
            "notes": 0,
        }
        
        available = total_limit - system_prompt_tokens - reserve_output_tokens
        budget["available_for_context"] = max(available, min_context_tokens)
        
        # Context'i bölümle (önerilen dağılım)
        # RAG: %50, History: %35, Notes: %15
        context_budget = budget["available_for_context"]
        budget["rag"] = int(context_budget * 0.50)
        budget["history"] = int(context_budget * 0.35)
        budget["notes"] = int(context_budget * 0.15)
        
        return budget
    
    # ========================================================================
    # PRIORITY-BASED CONTEXT TRUNCATION
    # ========================================================================
    
    def truncate_with_priority(
        self,
        items: List[Dict[str, Any]],
        max_tokens: int,
        model: str = "default",
        preserve_recent: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Öncelik skoruna göre context truncation.
        
        Args:
            items: Content ile priority score içeren item listesi
                   [{"content": str, "priority": float, "type": str}, ...]
            max_tokens: Maksimum token limiti
            model: Model adı
            preserve_recent: Son N item'ı her zaman koru
            
        Returns:
            Truncate edilmiş item listesi
        """
        if not items:
            return []
        
        # Her item için token sayısını hesapla
        for item in items:
            if "tokens" not in item:
                item["tokens"] = self.count_tokens(item.get("content", ""), model)
        
        # Total token check
        total_tokens = sum(item["tokens"] for item in items)
        if total_tokens <= max_tokens:
            return items
        
        # Son N item'ı ayır (bunlar korunacak)
        preserved = items[-preserve_recent:] if preserve_recent > 0 else []
        candidates = items[:-preserve_recent] if preserve_recent > 0 else items[:]
        
        preserved_tokens = sum(item["tokens"] for item in preserved)
        remaining_budget = max_tokens - preserved_tokens
        
        if remaining_budget <= 0:
            # Sadece preserved item'lar sığıyor
            return self._truncate_items(preserved, max_tokens, model)
        
        # Geri kalanları priority'ye göre sırala
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("priority", 0.5),
            reverse=True
        )
        
        # Budget'a sığana kadar ekle
        selected = []
        used_tokens = 0
        
        for item in sorted_candidates:
            if used_tokens + item["tokens"] <= remaining_budget:
                selected.append(item)
                used_tokens += item["tokens"]
        
        # Orijinal sırayı koru
        selected_set = set(id(item) for item in selected)
        result = [item for item in candidates if id(item) in selected_set]
        result.extend(preserved)
        
        return result
    
    def _truncate_items(
        self,
        items: List[Dict[str, Any]],
        max_tokens: int,
        model: str
    ) -> List[Dict[str, Any]]:
        """Item içeriklerini truncate et."""
        result = []
        remaining = max_tokens
        
        for item in items:
            tokens = item.get("tokens", self.count_tokens(item.get("content", ""), model))
            
            if tokens <= remaining:
                result.append(item)
                remaining -= tokens
            else:
                # İçeriği truncate et
                content = item.get("content", "")
                truncated_content = self._truncate_text(content, remaining, model)
                truncated_item = item.copy()
                truncated_item["content"] = truncated_content
                truncated_item["truncated"] = True
                result.append(truncated_item)
                break
        
        return result
    
    def _truncate_text(self, text: str, max_tokens: int, model: str) -> str:
        """Metni token limitine göre truncate et."""
        if self._tokenizer_type == "tiktoken" and self._tokenizer:
            try:
                tokens = self._tokenizer.encode(text)
                if len(tokens) <= max_tokens:
                    return text
                truncated_tokens = tokens[:max_tokens]
                return self._tokenizer.decode(truncated_tokens) + "..."
            except Exception:
                pass
        
        # Fallback
        chars_per_token = self.CHARS_PER_TOKEN.get(self._get_model_type(model), 4.0)
        max_chars = int(max_tokens * chars_per_token)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        cached: bool = False
    ):
        """Token kullanımını kaydet."""
        self._stats.update(input_tokens, output_tokens, cached)
        
        if model not in self._model_stats:
            self._model_stats[model] = TokenUsageStats()
        self._model_stats[model].update(input_tokens, output_tokens, cached)
    
    def get_stats(self) -> Dict[str, Any]:
        """Kullanım istatistiklerini döndür."""
        return {
            "global": {
                "total_input_tokens": self._stats.total_input_tokens,
                "total_output_tokens": self._stats.total_output_tokens,
                "total_cached_tokens": self._stats.total_cached_tokens,
                "requests_count": self._stats.requests_count,
                "avg_input_tokens": round(self._stats.avg_input_tokens, 2),
                "avg_output_tokens": round(self._stats.avg_output_tokens, 2),
                "peak_input_tokens": self._stats.peak_input_tokens,
                "peak_output_tokens": self._stats.peak_output_tokens,
            },
            "by_model": {
                model: {
                    "total_input_tokens": stats.total_input_tokens,
                    "total_output_tokens": stats.total_output_tokens,
                    "requests_count": stats.requests_count,
                }
                for model, stats in self._model_stats.items()
            },
            "tokenizer_type": self._tokenizer_type,
        }
    
    def reset_stats(self):
        """İstatistikleri sıfırla."""
        self._stats = TokenUsageStats()
        self._model_stats.clear()


# ============================================================================
# MESSAGE PRIORITIZER
# ============================================================================

class MessagePrioritizer:
    """
    Mesajlara öncelik skoru ata.
    
    Faktörler:
    - Recency (yeni mesajlar daha önemli)
    - Role (user > assistant)
    - Content relevance (soruyla alakalılık)
    - Information density (bilgi yoğunluğu)
    """
    
    ROLE_WEIGHTS = {
        "system": 1.0,
        "user": 0.9,
        "assistant": 0.7,
    }
    
    def __init__(self, token_manager: EnterpriseTokenManager):
        self.token_manager = token_manager
    
    def prioritize_messages(
        self,
        messages: List[Dict[str, str]],
        current_query: str = "",
        model: str = "default",
    ) -> List[Dict[str, Any]]:
        """
        Mesajlara öncelik skoru ata.
        
        Returns:
            Öncelik skoru eklenmiş mesaj listesi
        """
        total = len(messages)
        prioritized = []
        
        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            role = msg.get("role", "user")
            
            # Recency score (0.5 - 1.0)
            recency = 0.5 + (0.5 * (i / max(total - 1, 1)))
            
            # Role weight
            role_weight = self.ROLE_WEIGHTS.get(role, 0.5)
            
            # Content relevance (basit keyword overlap)
            relevance = self._calculate_relevance(content, current_query) if current_query else 0.5
            
            # Information density (unique words / total words)
            density = self._calculate_density(content)
            
            # Combined priority
            priority = (
                recency * 0.35 +
                role_weight * 0.25 +
                relevance * 0.25 +
                density * 0.15
            )
            
            prioritized.append({
                "role": role,
                "content": content,
                "priority": priority,
                "tokens": self.token_manager.count_tokens(content, model),
                "index": i,
            })
        
        return prioritized
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """Basit keyword-based relevance."""
        if not query or not content:
            return 0.5
        
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.5
        
        overlap = len(query_words & content_words)
        return min(1.0, 0.3 + (overlap / len(query_words)) * 0.7)
    
    def _calculate_density(self, content: str) -> float:
        """Information density hesapla."""
        if not content:
            return 0.0
        
        words = content.lower().split()
        if not words:
            return 0.0
        
        unique_words = set(words)
        density = len(unique_words) / len(words)
        
        # Normalize (0.3 - 1.0 range)
        return min(1.0, 0.3 + density * 0.7)


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

# Global token manager instance
token_manager = EnterpriseTokenManager()
message_prioritizer = MessagePrioritizer(token_manager)


__all__ = [
    "EnterpriseTokenManager",
    "MessagePrioritizer",
    "TokenUsageStats",
    "token_manager",
    "message_prioritizer",
]
