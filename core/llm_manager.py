"""
Enterprise AI Assistant - LLM Manager
Endüstri Standartlarında Kurumsal AI Çözümü

Ollama tabanlı LLM yönetimi - model seçimi, fallback ve streaming desteği.

ENTERPRISE FEATURES:
- LLM Response Caching (SQLite-backed)
- Automatic retry with exponential backoff
- Primary/Backup model failover
- Token counting and context window management
- Streaming response support
- Performance metrics and monitoring
"""

import asyncio
import time
import hashlib
import logging
from typing import AsyncGenerator, Optional, Dict, Any, Iterator
from functools import lru_cache
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import settings

# Logger setup
logger = logging.getLogger(__name__)


class TokenCounter:
    """
    Token sayma utility'si.
    
    Ollama modelleri için yaklaşık token hesaplama.
    Gerçek uygulamada tiktoken veya model-specific tokenizer kullanılabilir.
    """
    
    # Ortalama karakter/token oranları (model türüne göre)
    CHAR_PER_TOKEN_RATIOS = {
        "llama": 4.0,
        "mistral": 4.0,
        "phi": 3.8,
        "gemma": 4.0,
        "qwen": 3.5,
        "deepseek": 4.0,
        "default": 4.0
    }
    
    @classmethod
    def estimate_tokens(cls, text: str, model_name: str = "default") -> int:
        """Metindeki yaklaşık token sayısını hesapla."""
        if not text:
            return 0
        
        # Model tipini bul
        model_type = "default"
        for key in cls.CHAR_PER_TOKEN_RATIOS:
            if key in model_name.lower():
                model_type = key
                break
        
        ratio = cls.CHAR_PER_TOKEN_RATIOS[model_type]
        return int(len(text) / ratio)
    
    @classmethod
    def estimate_messages_tokens(cls, messages: list, model_name: str = "default") -> int:
        """Mesaj listesindeki toplam token sayısını hesapla."""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")
            # Role için ek token (ortalama 4 token)
            total += 4 + cls.estimate_tokens(content, model_name)
        return total


class ContextWindowManager:
    """
    Context window yönetimi.
    
    Model'in context limitini aşmamak için mesajları yönetir.
    """
    
    # Model context limitleri (token)
    MODEL_CONTEXT_LIMITS = {
        "llama3.2": 131072,
        "llama3.1": 131072,
        "llama3": 8192,
        "llama2": 4096,
        "mistral": 32768,
        "mixtral": 32768,
        "phi3": 128000,
        "phi": 2048,
        "gemma3": 8192,
        "gemma2": 8192,
        "gemma": 8192,
        "qwen3": 32768,
        "qwen2.5": 32768,
        "qwen2": 32768,
        "qwen": 8192,
        "deepseek": 32768,
        "default": 8192
    }
    
    # Yanıt için ayrılacak minimum token
    RESPONSE_RESERVE = 2048
    
    @classmethod
    def get_context_limit(cls, model_name: str) -> int:
        """Model için context limitini al."""
        for key, limit in cls.MODEL_CONTEXT_LIMITS.items():
            if key in model_name.lower():
                return limit
        return cls.MODEL_CONTEXT_LIMITS["default"]
    
    @classmethod
    def truncate_messages(
        cls,
        messages: list,
        model_name: str,
        max_tokens: Optional[int] = None
    ) -> list:
        """
        Mesajları context limitine sığacak şekilde kırp.
        
        Strateji:
        1. System prompt her zaman korunur
        2. En son mesaj (user) korunur
        3. Ortadaki mesajlar gerekirse kırpılır
        """
        if not messages:
            return messages
        
        context_limit = max_tokens or cls.get_context_limit(model_name)
        available_tokens = context_limit - cls.RESPONSE_RESERVE
        
        # Toplam token hesapla
        total_tokens = TokenCounter.estimate_messages_tokens(messages, model_name)
        
        if total_tokens <= available_tokens:
            return messages
        
        # System prompt ve son mesajı ayır
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        # System prompt tokenları
        system_tokens = TokenCounter.estimate_messages_tokens(system_msgs, model_name)
        remaining = available_tokens - system_tokens
        
        # Son mesajdan başlayarak ekle
        kept_msgs = []
        current_tokens = 0
        
        for msg in reversed(other_msgs):
            msg_tokens = TokenCounter.estimate_messages_tokens([msg], model_name)
            if current_tokens + msg_tokens <= remaining:
                kept_msgs.insert(0, msg)
                current_tokens += msg_tokens
            else:
                # Mesajı kırpmayı dene
                if not kept_msgs:  # En az bir mesaj olmalı
                    truncated_content = msg["content"][:int(remaining * 3.5)]
                    kept_msgs.insert(0, {**msg, "content": truncated_content + "..."})
                break
        
        return system_msgs + kept_msgs


class LLMManager:
    """
    LLM yönetim sınıfı - Endüstri standartlarına uygun.
    
    ENTERPRISE FEATURES:
    - Primary/Backup model desteği
    - Automatic failover
    - Streaming response
    - Retry with exponential backoff
    - LLM Response Caching (2 saat TTL)
    - Token counting & context management
    - Performance metrics
    """
    
    def __init__(
        self,
        primary_model: Optional[str] = None,
        backup_model: Optional[str] = None,
        base_url: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 7200,  # 2 saat
    ):
        self.primary_model = primary_model or settings.OLLAMA_PRIMARY_MODEL
        self.backup_model = backup_model or settings.OLLAMA_BACKUP_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)
        self._current_model = self.primary_model
        
        # Caching
        self._cache_enabled = enable_cache
        self._cache_ttl = cache_ttl
        self._cache = None
        
        # Performance metrics
        self._metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_tokens_generated": 0,
            "total_latency_ms": 0,
            "errors": 0,
            "failovers": 0,
        }
    
    def _get_cache(self):
        """Lazy cache initialization."""
        if self._cache is None and self._cache_enabled:
            try:
                from .cache import cache_manager
                self._cache = cache_manager
            except ImportError:
                self._cache_enabled = False
        return self._cache
    
    def _generate_cache_key(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        """Cache key oluştur."""
        key_data = f"{prompt}|{system_prompt or ''}|{temperature}|{self._current_model}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def _get_cached_response(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> Optional[str]:
        """Cache'den yanıt al."""
        if not self._cache_enabled:
            return None
        
        cache = self._get_cache()
        if cache:
            cached = cache.get_cached_llm_response(
                query=f"{prompt}|{system_prompt or ''}",
                model=self._current_model
            )
            if cached:
                self._metrics["cache_hits"] += 1
                return cached
        
        self._metrics["cache_misses"] += 1
        return None
    
    def _cache_response(self, prompt: str, response: str, system_prompt: str = None) -> None:
        """Yanıtı cache'le."""
        if not self._cache_enabled:
            return
        
        cache = self._get_cache()
        if cache:
            cache.cache_llm_response(
                query=f"{prompt}|{system_prompt or ''}",
                response=response,
                model=self._current_model,
                ttl=self._cache_ttl
            )
    
    def check_model_available(self, model_name: str) -> bool:
        """Model'in mevcut olup olmadığını kontrol et."""
        try:
            result = self.client.list()
            # Handle both old (dict) and new (object) API formats
            if hasattr(result, 'models'):
                # New API: result.models is a list of Model objects
                available_models = [m.model for m in result.models]
            elif isinstance(result, dict):
                # Old API: result is a dict with 'models' key
                available_models = [m["name"] for m in result.get("models", [])]
            else:
                available_models = []
            
            # Check for exact match or partial match (with tags)
            return any(
                model_name in m or m.startswith(model_name.split(":")[0])
                for m in available_models
            )
        except Exception:
            return False
    
    def pull_model(self, model_name: str) -> bool:
        """Model'i indir."""
        try:
            print(f"📥 Model indiriliyor: {model_name}")
            self.client.pull(model_name)
            print(f"✅ Model indirildi: {model_name}")
            return True
        except Exception as e:
            print(f"❌ Model indirilemedi: {e}")
            return False
    
    def ensure_model(self, model_name: str) -> bool:
        """Model'in mevcut olduğundan emin ol, yoksa indir."""
        if not self.check_model_available(model_name):
            return self.pull_model(model_name)
        return True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 65536,  # 2^16 - unlimited local model
        use_cache: bool = True,
    ) -> str:
        """
        Senkron LLM yanıtı üret.
        
        Args:
            prompt: Kullanıcı prompt'u
            system_prompt: Sistem prompt'u (opsiyonel)
            temperature: Yaratıcılık seviyesi (0-1)
            max_tokens: Maksimum token sayısı
            use_cache: Cache kullanılsın mı
            
        Returns:
            LLM yanıtı
        """
        start_time = time.time()
        self._metrics["total_requests"] += 1
        
        # Cache kontrolü (sadece düşük temperature için)
        if use_cache and temperature <= 0.3:
            cached = self._get_cached_response(prompt, system_prompt, temperature)
            if cached:
                return cached
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # Context window management
        messages = ContextWindowManager.truncate_messages(messages, self._current_model)
        
        try:
            response = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    # GPU optimization settings from config
                    "num_gpu": settings.OLLAMA_NUM_GPU,  # All layers on GPU
                    "num_ctx": settings.OLLAMA_NUM_CTX,  # Context window
                    "num_batch": settings.OLLAMA_NUM_BATCH,  # Batch size for prompt
                },
            )
            
            # Qwen3 modeli hem thinking hem content döndürür
            # content asıl cevap, thinking düşünce süreci
            msg = response.get("message", {})
            if hasattr(msg, 'content') and msg.content:
                result = msg.content
            elif isinstance(msg, dict) and msg.get("content"):
                result = msg["content"]
            else:
                # Fallback - thinking varsa onu kullan
                if hasattr(msg, 'thinking') and msg.thinking:
                    result = msg.thinking
                elif isinstance(msg, dict) and msg.get("thinking"):
                    result = msg["thinking"]
                else:
                    result = str(msg) if msg else ""
            
            # Metrics güncelle
            latency = (time.time() - start_time) * 1000
            self._metrics["total_latency_ms"] += latency
            self._metrics["total_tokens_generated"] += TokenCounter.estimate_tokens(result, self._current_model)
            
            # Cache'le (düşük temperature için)
            if use_cache and temperature <= 0.3:
                self._cache_response(prompt, result, system_prompt)
            
            return result
        except Exception as e:
            self._metrics["errors"] += 1
            # Fallback to backup model
            if self._current_model != self.backup_model:
                print(f"⚠️ Primary model başarısız, backup deneniyor: {e}")
                self._current_model = self.backup_model
                self._metrics["failovers"] += 1
                return self.generate(prompt, system_prompt, temperature, max_tokens, use_cache)
            raise
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 65536,  # 2^16 - unlimited local model
    ) -> str:
        """Asenkron LLM yanıtı üret."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, system_prompt, temperature, max_tokens)
        )
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 65536,  # 2^16 - unlimited local model
    ) -> Iterator[str]:
        """
        Streaming LLM yanıtı üret (senkron).
        
        Yields:
            Token parçaları
        """
        start_time = time.time()
        self._metrics["total_requests"] += 1
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # Context window management
        messages = ContextWindowManager.truncate_messages(messages, self._current_model)
        
        try:
            stream = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    # GPU optimization settings from config
                    "num_gpu": settings.OLLAMA_NUM_GPU,
                    "num_ctx": settings.OLLAMA_NUM_CTX,
                    "num_batch": settings.OLLAMA_NUM_BATCH,
                },
                stream=True,
            )
            
            full_response = []
            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    full_response.append(content)
                    yield content
            
            # Metrics güncelle
            latency = (time.time() - start_time) * 1000
            self._metrics["total_latency_ms"] += latency
            self._metrics["total_tokens_generated"] += TokenCounter.estimate_tokens(
                "".join(full_response), self._current_model
            )
                    
        except Exception as e:
            self._metrics["errors"] += 1
            if self._current_model != self.backup_model:
                print(f"⚠️ Streaming failed, trying backup: {e}")
                self._current_model = self.backup_model
                self._metrics["failovers"] += 1
                yield from self.generate_stream(prompt, system_prompt, temperature, max_tokens)
            else:
                raise
    
    async def generate_stream_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 65536,
        model: Optional[str] = None,  # Model routing desteği
    ) -> AsyncGenerator[str, None]:
        """
        Async streaming LLM yanıtı üret.
        
        Async context'te streaming için kullanın.
        
        Args:
            prompt: Kullanıcı mesajı
            system_prompt: Sistem prompt'u (opsiyonel)
            temperature: Sıcaklık parametresi (0.0-1.0)
            max_tokens: Maksimum token sayısı
            model: Kullanılacak model (None ise _current_model)
        
        Yields:
            Token parçaları
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        start_time = time.time()
        self._metrics["total_requests"] += 1
        
        # Model seçimi - parametre verilmediyse mevcut modeli kullan
        target_model = model or self._current_model
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Qwen3 - thinking mode aktif, içerik ayrı gönderilecek
        # /think ile düşünme sürecini gösterebiliriz
        user_content = prompt
        
        messages.append({"role": "user", "content": user_content})
        
        # Context window management
        messages = ContextWindowManager.truncate_messages(messages, target_model)
        
        # Queue for thread-safe communication
        import queue
        import traceback
        chunk_queue: queue.Queue = queue.Queue()
        done_event = asyncio.Event()
        
        def stream_in_thread():
            """Thread'de streaming yap."""
            try:
                logger.debug(f"Streaming başlıyor: model={target_model}")
                logger.debug(f"Messages: {len(messages)} message(s)")
                
                stream = self.client.chat(
                    model=target_model,
                    messages=messages,
                    options={
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        # GPU optimization settings from config
                        "num_gpu": settings.OLLAMA_NUM_GPU,
                        "num_ctx": settings.OLLAMA_NUM_CTX,
                        "num_batch": settings.OLLAMA_NUM_BATCH,
                    },
                    stream=True,
                )
                
                logger.debug("Stream oluşturuldu, iterating...")
                chunk_count = 0
                in_thinking_block = False
                thinking_buffer = []
                
                for chunk in stream:
                    chunk_count += 1
                    if chunk_count == 1:
                        logger.debug(f"İlk chunk alındı: {type(chunk)}")
                    
                    if "message" in chunk:
                        msg = chunk["message"]
                        # Qwen3 thinking mode desteği - Dict'ten okuma
                        if isinstance(msg, dict):
                            # thinking veya content kontrol
                            if msg.get("thinking"):
                                # Thinking content - ayrı gönder
                                thinking_content = msg.get("thinking", "")
                                if thinking_content:
                                    chunk_queue.put({"type": "thinking", "content": thinking_content})
                                continue
                            
                            content = msg.get("content", "")
                            if content:
                                # <think>...</think> bloklarını yakala ve ayrı gönder
                                import re
                                
                                # Thinking bloğu başlangıcı
                                if "<think>" in content:
                                    in_thinking_block = True
                                    # <think> öncesi varsa gönder
                                    before_think = content.split("<think>")[0]
                                    if before_think.strip():
                                        chunk_queue.put({"type": "content", "content": before_think})
                                    # <think> sonrasını buffer'a ekle
                                    after_tag = content.split("<think>")[-1]
                                    if "</think>" not in after_tag:
                                        thinking_buffer.append(after_tag)
                                    else:
                                        # Aynı chunk'ta kapanış var
                                        parts = after_tag.split("</think>")
                                        thinking_text = parts[0]
                                        if thinking_text.strip():
                                            chunk_queue.put({"type": "thinking", "content": thinking_text})
                                        in_thinking_block = False
                                        # </think> sonrası varsa gönder
                                        if len(parts) > 1 and parts[1].strip():
                                            chunk_queue.put({"type": "content", "content": parts[1]})
                                    continue
                                
                                # Thinking bloğu içindeyiz
                                if in_thinking_block:
                                    if "</think>" in content:
                                        # Thinking bloğu kapanıyor
                                        parts = content.split("</think>")
                                        thinking_buffer.append(parts[0])
                                        full_thinking = "".join(thinking_buffer)
                                        if full_thinking.strip():
                                            chunk_queue.put({"type": "thinking", "content": full_thinking})
                                        thinking_buffer = []
                                        in_thinking_block = False
                                        # </think> sonrası varsa gönder
                                        if len(parts) > 1 and parts[1].strip():
                                            chunk_queue.put({"type": "content", "content": parts[1]})
                                    else:
                                        thinking_buffer.append(content)
                                    continue
                                
                                # Normal content
                                chunk_queue.put({"type": "content", "content": content})
                                if chunk_count <= 3:
                                    logger.debug(f"Content queue'ya eklendi: {len(content)} chars")
                        else:
                            # Object attribute erişimi
                            if hasattr(msg, 'thinking') and msg.thinking:
                                chunk_queue.put({"type": "thinking", "content": msg.thinking})
                            elif hasattr(msg, 'content') and msg.content:
                                chunk_queue.put({"type": "content", "content": msg.content})
                
                logger.debug(f"Stream tamamlandı: {chunk_count} chunk")
                chunk_queue.put(None)  # Signal completion
            except Exception as e:
                logger.error(f"Stream hatası: {e}")
                logger.debug(traceback.format_exc())
                chunk_queue.put(e)  # Signal error
        
        # Thread'i başlat
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        future = loop.run_in_executor(executor, stream_in_thread)
        
        full_response = []
        thinking_chunks = []
        try:
            while True:
                # Non-blocking queue check
                try:
                    chunk = chunk_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.01)  # Küçük bekleme
                    continue
                
                if chunk is None:
                    break  # Stream tamamlandı
                elif isinstance(chunk, Exception):
                    raise chunk
                else:
                    # Dict olarak yield et
                    if isinstance(chunk, dict):
                        if chunk.get("type") == "content":
                            full_response.append(chunk.get("content", ""))
                        elif chunk.get("type") == "thinking":
                            thinking_chunks.append(chunk.get("content", ""))
                        yield chunk
                    else:
                        # Eski format için backward compatibility
                        full_response.append(chunk)
                        yield {"type": "content", "content": chunk}
            
            # Metrics güncelle
            latency = (time.time() - start_time) * 1000
            self._metrics["total_latency_ms"] += latency
            self._metrics["total_tokens_generated"] += TokenCounter.estimate_tokens(
                "".join(full_response), self._current_model
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            if self._current_model != self.backup_model:
                print(f"⚠️ Async streaming failed, trying backup: {e}")
                self._current_model = self.backup_model
                self._metrics["failovers"] += 1
                async for chunk in self.generate_stream_async(prompt, system_prompt, temperature, max_tokens):
                    yield chunk
            else:
                raise
        finally:
            executor.shutdown(wait=False)
    
    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 65536,  # 2^16 - unlimited local model
    ) -> str:
        """
        Multi-turn chat desteği.
        
        Args:
            messages: Mesaj listesi [{"role": "user/assistant/system", "content": "..."}]
            temperature: Yaratıcılık seviyesi
            max_tokens: Maksimum token
            
        Returns:
            Assistant yanıtı
        """
        try:
            response = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            if self._current_model != self.backup_model:
                self._current_model = self.backup_model
                return self.chat(messages, temperature, max_tokens)
            raise
    
    def get_status(self) -> dict:
        """Sistem durumunu döndür."""
        avg_latency = (
            self._metrics["total_latency_ms"] / self._metrics["total_requests"]
            if self._metrics["total_requests"] > 0 else 0
        )
        cache_hit_rate = (
            self._metrics["cache_hits"] / (self._metrics["cache_hits"] + self._metrics["cache_misses"]) * 100
            if (self._metrics["cache_hits"] + self._metrics["cache_misses"]) > 0 else 0
        )
        
        return {
            "primary_model": self.primary_model,
            "backup_model": self.backup_model,
            "current_model": self._current_model,
            "base_url": self.base_url,
            "primary_available": self.check_model_available(self.primary_model),
            "backup_available": self.check_model_available(self.backup_model),
            "cache_enabled": self._cache_enabled,
            "metrics": {
                "total_requests": self._metrics["total_requests"],
                "cache_hits": self._metrics["cache_hits"],
                "cache_hit_rate": f"{cache_hit_rate:.1f}%",
                "total_tokens": self._metrics["total_tokens_generated"],
                "avg_latency_ms": f"{avg_latency:.1f}",
                "errors": self._metrics["errors"],
                "failovers": self._metrics["failovers"],
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Performance metrics döndür."""
        return self._metrics.copy()
    
    def reset_metrics(self) -> None:
        """Metrics'i sıfırla."""
        for key in self._metrics:
            self._metrics[key] = 0
    
    def generate_with_image(
        self,
        prompt: str,
        image_path: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 65536,  # 2^16 - unlimited local model
    ) -> str:
        """
        Görsel ile birlikte LLM yanıtı üret (VLM desteği).
        
        Args:
            prompt: Kullanıcı prompt'u
            image_path: Görsel dosya yolu
            system_prompt: Sistem prompt'u (opsiyonel)
            temperature: Yaratıcılık seviyesi
            max_tokens: Maksimum token sayısı
            
        Returns:
            LLM yanıtı
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Görsel ile birlikte mesaj
        messages.append({
            "role": "user",
            "content": prompt,
            "images": [image_path]
        })
        
        try:
            response = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            if self._current_model != self.backup_model:
                print(f"⚠️ Vision model başarısız, backup deneniyor: {e}")
                self._current_model = self.backup_model
                return self.generate_with_image(prompt, image_path, system_prompt, temperature, max_tokens)
            raise
    
    def generate_stream_with_image(
        self,
        prompt: str,
        image_path: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 65536,  # 2^16 - unlimited local model
    ):
        """
        Görsel ile streaming LLM yanıtı üret (VLM desteği).
        
        Yields:
            Token parçaları
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": prompt,
            "images": [image_path]
        })
        
        try:
            stream = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                stream=True,
            )
            
            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            if self._current_model != self.backup_model:
                print(f"⚠️ Vision streaming failed, trying backup: {e}")
                self._current_model = self.backup_model
                yield from self.generate_stream_with_image(prompt, image_path, system_prompt, temperature, max_tokens)
            else:
                raise


# Singleton instance
llm_manager = LLMManager()
