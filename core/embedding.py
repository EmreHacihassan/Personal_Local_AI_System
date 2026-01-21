"""
Enterprise AI Assistant - Embedding Manager
Endüstri Standartlarında Kurumsal AI Çözümü

Ollama tabanlı embedding üretimi - döküman ve sorgu vektörizasyonu.

ENTERPRISE FEATURES:
- TRUE Batch Processing (single API call per batch)
- Thread-safe LRU Caching (2000 entries)
- Parallel embedding for large document sets
- Performance metrics and monitoring
- Automatic retry on failure
"""

import hashlib
import threading
import time
import os
from typing import List, Optional, Dict, Tuple
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
import ollama
import numpy as np

# GPU Support
try:
    import torch
    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        GPU_NAME = torch.cuda.get_device_name(0)
        GPU_MEMORY = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
    else:
        GPU_NAME = None
        GPU_MEMORY = 0
except ImportError:
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False
    GPU_NAME = None
    GPU_MEMORY = 0

# Sentence Transformers for GPU-accelerated embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .config import settings


class EmbeddingCache:
    """
    Thread-safe LRU embedding cache.
    
    Embedding hesaplaması pahalı bir işlem olduğundan,
    sık kullanılan sorgu/dokümanlar için cache tutulur.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, List[float]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def _hash_text(self, text: str) -> str:
        """Metin için unique hash oluştur."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:32]
    
    def get(self, text: str) -> Optional[List[float]]:
        """Cache'den embedding al."""
        key = self._hash_text(text)
        with self._lock:
            if key in self._cache:
                # LRU: Move to end
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None
    
    def set(self, text: str, embedding: List[float]) -> None:
        """Embedding'i cache'e ekle."""
        key = self._hash_text(text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    # Remove oldest
                    self._cache.popitem(last=False)
                self._cache[key] = embedding
    
    def clear(self) -> None:
        """Cache'i temizle."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, any]:
        """Cache istatistiklerini döndür."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.1f}%"
            }


class EmbeddingManager:
    """
    Embedding yönetim sınıfı - Endüstri standartlarına uygun.
    
    ENTERPRISE FEATURES:
    - GPU-Accelerated embeddings (CUDA support)
    - Sentence Transformers for local GPU inference
    - Ollama embedding modeli desteği (fallback)
    - TRUE Batch processing (parallel API calls)
    - L2 Normalization
    - Thread-safe LRU Caching
    - Performance metrics
    - Automatic retry on failure
    
    GPU OPTIMIZATION (RTX 4070 8GB):
    - Automatic GPU detection and utilization
    - Mixed precision (FP16) for faster inference
    - Batch size optimization for GPU memory
    - Memory-efficient processing
    - Config-driven settings
    """
    
    # Cache sabitleri
    CACHE_MAX_SIZE = 2000  # Maksimum cache girişi
    
    # Parallel processing
    MAX_WORKERS = 4  # Parallel thread sayısı
    
    # GPU Models (sentence-transformers) - Quality Rankings
    GPU_EMBEDDING_MODELS = {
        "default": "all-MiniLM-L6-v2",  # Fast, 384 dim, English
        "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",  # 384 dim, 50+ languages, BEST for Turkish
        "large": "all-mpnet-base-v2",  # Better quality, 768 dim, English only
        "turkish": "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr",  # Turkish optimized
    }
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        enable_cache: bool = True,
        use_gpu: bool = None,
        gpu_model: str = None,
        batch_size: int = None,
    ):
        self.model_name = model_name or settings.OLLAMA_EMBEDDING_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)
        self.dimension = settings.EMBEDDING_DIMENSION
        
        # GPU Configuration from settings
        _use_gpu_setting = getattr(settings, 'USE_GPU_EMBEDDING', True)
        _gpu_model_setting = getattr(settings, 'GPU_EMBEDDING_MODEL', 'multilingual')
        _batch_size_setting = getattr(settings, 'GPU_BATCH_SIZE', 64)
        
        # Allow override from constructor
        self._use_gpu = (use_gpu if use_gpu is not None else _use_gpu_setting) and CUDA_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE
        self._gpu_model_name = self.GPU_EMBEDDING_MODELS.get(gpu_model or _gpu_model_setting, gpu_model or _gpu_model_setting)
        self._sentence_model = None
        self._device = "cuda" if self._use_gpu else "cpu"
        
        # Batch sizes from config
        self.GPU_BATCH_SIZE = batch_size or _batch_size_setting
        self.CPU_BATCH_SIZE = 16  # CPU için sabit
        
        # Lazy loading flag - model will be loaded on first use
        self._gpu_model_loaded = False
        self._lazy_load_enabled = True  # Enable lazy loading for faster startup
        
        # Don't initialize GPU model immediately - lazy load on first use
        # if self._use_gpu:
        #     self._init_gpu_model()
        
        # Cache
        self._cache_enabled = enable_cache
        self._cache = EmbeddingCache(max_size=self.CACHE_MAX_SIZE) if enable_cache else None
        
        # Thread pool for parallel processing
        self._executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS)
        
        # Performance metrics
        self._metrics = {
            "total_embeddings": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_latency_ms": 0,
            "errors": 0,
            "batch_calls": 0,
            "gpu_embeddings": 0,
            "cpu_embeddings": 0,
        }
    
    def _init_gpu_model(self):
        """GPU embedding modelini başlat (lazy loading)."""
        if self._gpu_model_loaded:
            return  # Already loaded
            
        try:
            print(f"🚀 GPU Embedding Model yükleniyor: {self._gpu_model_name}")
            print(f"   GPU: {GPU_NAME} ({GPU_MEMORY:.1f} GB)")
            
            # Offline modda çalış - HuggingFace Hub'a bağlanma
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            # Önce local_files_only ile dene
            try:
                self._sentence_model = SentenceTransformer(
                    self._gpu_model_name,
                    device=self._device,
                    local_files_only=True
                )
            except OSError as cache_error:
                # Model cache'de yok, internet varsa indir
                print(f"⚠️ Model cache'de yok, indiriliyor...")
                os.environ.pop('HF_HUB_OFFLINE', None)
                os.environ.pop('TRANSFORMERS_OFFLINE', None)
                
                self._sentence_model = SentenceTransformer(
                    self._gpu_model_name,
                    device=self._device
                )
                
                # Tekrar offline mode
                os.environ['HF_HUB_OFFLINE'] = '1'
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            # Mixed precision for faster inference
            if self._device == "cuda":
                self._sentence_model.half()  # FP16
            
            # Update dimension based on model
            self.dimension = self._sentence_model.get_sentence_embedding_dimension()
            
            self._gpu_model_loaded = True
            print(f"✅ GPU Embedding hazır! Dimension: {self.dimension}")
            
        except Exception as e:
            print(f"⚠️ GPU model yüklenemedi, Ollama'ya fallback: {e}")
            self._use_gpu = False
            self._sentence_model = None
            self._gpu_model_loaded = True  # Mark as attempted
    
    def _ensure_gpu_model(self):
        """Lazy load GPU model if needed."""
        if self._use_gpu and not self._gpu_model_loaded:
            self._init_gpu_model()
    
    def check_model_available(self) -> bool:
        """Embedding model'in mevcut olup olmadığını kontrol et."""
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
            
            return any(
                self.model_name in m or m.startswith(self.model_name.split(":")[0])
                for m in available_models
            )
        except Exception:
            return False
    
    def pull_model(self) -> bool:
        """Embedding model'ini indir."""
        try:
            print(f"📥 Embedding model indiriliyor: {self.model_name}")
            self.client.pull(self.model_name)
            print(f"✅ Embedding model indirildi: {self.model_name}")
            return True
        except Exception as e:
            print(f"❌ Embedding model indirilemedi: {e}")
            return False
    
    def ensure_model(self) -> bool:
        """Model'in mevcut olduğundan emin ol."""
        if not self.check_model_available():
            return self.pull_model()
        return True
    
    def embed_text(self, text: str, use_cache: bool = True, max_retries: int = 3) -> List[float]:
        """
        Tek bir metin için embedding üret.
        GPU varsa sentence-transformers, yoksa Ollama kullanır.
        
        Args:
            text: Embedding yapılacak metin
            use_cache: Cache kullanılsın mı
            max_retries: Hata durumunda tekrar deneme sayısı
            
        Returns:
            Embedding vektörü (float listesi)
        """
        start_time = time.time()
        
        # Cache kontrolü
        if use_cache and self._cache_enabled and self._cache:
            cached = self._cache.get(text)
            if cached is not None:
                self._metrics["cache_hits"] += 1
                return cached
        
        self._metrics["cache_misses"] += 1
        
        # Lazy load GPU model if needed
        self._ensure_gpu_model()
        
        # GPU ile embedding (öncelikli)
        if self._use_gpu and self._sentence_model is not None:
            try:
                with torch.no_grad():
                    embedding = self._sentence_model.encode(
                        text,
                        convert_to_numpy=True,
                        normalize_embeddings=True
                    ).tolist()
                
                # Metrics güncelle
                self._metrics["total_embeddings"] += 1
                self._metrics["gpu_embeddings"] += 1
                self._metrics["total_latency_ms"] += (time.time() - start_time) * 1000
                
                # Cache'e ekle
                if use_cache and self._cache_enabled and self._cache:
                    self._cache.set(text, embedding)
                
                return embedding
            except Exception as e:
                print(f"⚠️ GPU embedding hatası, Ollama'ya fallback: {e}")
        
        # Ollama ile embedding (fallback)
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings(
                    model=self.model_name,
                    prompt=text,
                )
                embedding = response["embedding"]
                
                # Metrics güncelle
                self._metrics["total_embeddings"] += 1
                self._metrics["cpu_embeddings"] += 1
                self._metrics["total_latency_ms"] += (time.time() - start_time) * 1000
                
                # Cache'e ekle
                if use_cache and self._cache_enabled and self._cache:
                    self._cache.set(text, embedding)
                
                return embedding
            except Exception as e:
                last_error = e
                self._metrics["errors"] += 1
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        print(f"❌ Embedding hatası ({max_retries} deneme sonrası): {last_error}")
        raise last_error
    
    def _embed_single_for_batch(self, text: str) -> Tuple[str, List[float]]:
        """Batch processing için tek metin embed et."""
        embedding = self.embed_text(text, use_cache=False, max_retries=2)
        return (text, embedding)
    
    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = None,
        use_cache: bool = True,
        parallel: bool = True
    ) -> List[List[float]]:
        """
        Birden fazla metin için embedding üret.
        
        GPU BATCH PROCESSING:
        - GPU varsa tek seferde batch embedding (çok hızlı)
        - CPU için parallel API calls
        - Cache hit'ler ayrı işlenir
        
        Args:
            texts: Embedding yapılacak metinler
            batch_size: Batch boyutu (None = otomatik)
            use_cache: Cache kullanılsın mı
            parallel: Parallel processing kullanılsın mı
            
        Returns:
            Embedding vektörleri listesi
        """
        if not texts:
            return []
        
        # Batch size: GPU için büyük, CPU için küçük
        if batch_size is None:
            batch_size = self.GPU_BATCH_SIZE if self._use_gpu else self.CPU_BATCH_SIZE
        
        start_time = time.time()
        embeddings = [None] * len(texts)  # Sırayı korumak için
        texts_to_embed = []  # Cache'de olmayan metinler
        text_indices = []  # Orijinal index'leri
        
        # 1. Cache kontrolü - hit'leri ayır
        for i, text in enumerate(texts):
            if use_cache and self._cache_enabled and self._cache:
                cached = self._cache.get(text)
                if cached is not None:
                    embeddings[i] = cached
                    self._metrics["cache_hits"] += 1
                    continue
            
            texts_to_embed.append(text)
            text_indices.append(i)
            self._metrics["cache_misses"] += 1
        
        # 2. Cache'de olmayanları embed et
        if texts_to_embed:
            self._metrics["batch_calls"] += 1
            
            # Lazy load GPU model if needed
            self._ensure_gpu_model()
            
            # GPU BATCH PROCESSING (öncelikli - çok hızlı)
            if self._use_gpu and self._sentence_model is not None:
                try:
                    print(f"🚀 GPU Batch Embedding: {len(texts_to_embed)} metin...")
                    
                    with torch.no_grad():
                        # Batch processing with optimal batch size
                        all_embeddings = []
                        for i in range(0, len(texts_to_embed), batch_size):
                            batch = texts_to_embed[i:i+batch_size]
                            batch_embeddings = self._sentence_model.encode(
                                batch,
                                convert_to_numpy=True,
                                normalize_embeddings=True,
                                batch_size=len(batch),
                                show_progress_bar=False
                            )
                            all_embeddings.extend(batch_embeddings.tolist())
                    
                    # Sonuçları yerleştir
                    for idx, emb_idx in enumerate(text_indices):
                        embeddings[emb_idx] = all_embeddings[idx]
                        
                        # Cache'e ekle
                        if use_cache and self._cache_enabled and self._cache:
                            self._cache.set(texts_to_embed[idx], all_embeddings[idx])
                    
                    self._metrics["gpu_embeddings"] += len(texts_to_embed)
                    self._metrics["total_embeddings"] += len(texts_to_embed)
                    
                    total_time = time.time() - start_time
                    rate = len(texts_to_embed) / total_time if total_time > 0 else 0
                    print(f"✅ GPU Batch tamamlandı: {len(texts_to_embed)} metin, {total_time:.2f}s ({rate:.0f}/s)")
                    
                    return embeddings
                    
                except Exception as e:
                    print(f"⚠️ GPU batch hatası, sequential'a fallback: {e}")
            
            # CPU PARALLEL PROCESSING (fallback)
            use_parallel = parallel and len(texts_to_embed) > 1
            
            if use_parallel:
                # PARALLEL PROCESSING - ThreadPoolExecutor ile
                try:
                    futures = {}
                    for idx, text in zip(text_indices, texts_to_embed):
                        future = self._executor.submit(self._embed_single_for_batch, text)
                        futures[future] = idx
                    
                    for future in as_completed(futures):
                        idx = futures[future]
                        try:
                            text, embedding = future.result(timeout=30)
                            embeddings[idx] = embedding
                            
                            # Cache'e ekle
                            if use_cache and self._cache_enabled and self._cache:
                                self._cache.set(text, embedding)
                        except Exception as e:
                            print(f"⚠️ Parallel embedding error at index {idx}: {e}")
                            # Fallback: zero vector
                            embeddings[idx] = [0.0] * self.dimension
                except Exception as e:
                    print(f"⚠️ Parallel processing failed, falling back to sequential: {e}")
                    use_parallel = False
            
            # Sequential processing - tek metin için veya parallel başarısız olunca
            if not use_parallel:
                # SEQUENTIAL PROCESSING
                for i, (idx, text) in enumerate(zip(text_indices, texts_to_embed)):
                    try:
                        embedding = self.embed_text(text, use_cache=use_cache)
                        embeddings[idx] = embedding
                    except Exception as e:
                        print(f"⚠️ Embedding error at index {idx}: {e}")
                        embeddings[idx] = [0.0] * self.dimension
                    
                    # Progress indicator (her 10 metin için)
                    if (i + 1) % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = (i + 1) / elapsed if elapsed > 0 else 0
                        print(f"📊 Embedding progress: {i + 1}/{len(texts_to_embed)} ({rate:.1f}/s)")
        
        # 3. Sonuç kontrolü
        total_time = time.time() - start_time
        print(f"✅ Embedded {len(texts)} texts in {total_time:.2f}s (cache hits: {len(texts) - len(texts_to_embed)})")
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Sorgu için embedding üret (arama optimizasyonu).
        Cache'lenir çünkü aynı sorgular tekrarlanabilir.
        
        Args:
            query: Arama sorgusu
            
        Returns:
            Query embedding vektörü
        """
        return self.embed_text(query, use_cache=True)
    
    def embed_document(self, document: str, use_cache: bool = False) -> List[float]:
        """
        Döküman için embedding üret (indexing optimizasyonu).
        Default olarak cache'lenmez çünkü dokümanlar genelde tek sefer işlenir.
        
        Args:
            document: Döküman içeriği
            use_cache: Cache kullanılsın mı
            
        Returns:
            Document embedding vektörü
        """
        return self.embed_text(document, use_cache=use_cache)
    
    @staticmethod
    def normalize(embedding: List[float]) -> List[float]:
        """Embedding vektörünü normalize et (L2 normalization)."""
        arr = np.array(embedding)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """İki vektör arasındaki cosine similarity hesapla."""
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def get_status(self) -> dict:
        """Embedding manager durumunu döndür."""
        avg_latency = (
            self._metrics["total_latency_ms"] / self._metrics["total_embeddings"]
            if self._metrics["total_embeddings"] > 0 else 0
        )
        total_cache_ops = self._metrics["cache_hits"] + self._metrics["cache_misses"]
        cache_hit_rate = (
            self._metrics["cache_hits"] / total_cache_ops * 100
            if total_cache_ops > 0 else 0
        )
        
        status = {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "dimension": self.dimension,
            "model_available": self.check_model_available(),
            "cache_enabled": self._cache_enabled,
            # GPU Info
            "gpu": {
                "available": CUDA_AVAILABLE,
                "enabled": self._use_gpu,
                "name": GPU_NAME,
                "memory_gb": GPU_MEMORY,
                "device": self._device,
                "model": self._gpu_model_name if self._use_gpu else None,
            },
            "metrics": {
                "total_embeddings": self._metrics["total_embeddings"],
                "gpu_embeddings": self._metrics.get("gpu_embeddings", 0),
                "cpu_embeddings": self._metrics.get("cpu_embeddings", 0),
                "cache_hits": self._metrics["cache_hits"],
                "cache_hit_rate": f"{cache_hit_rate:.1f}%",
                "avg_latency_ms": f"{avg_latency:.1f}",
                "batch_calls": self._metrics["batch_calls"],
                "errors": self._metrics["errors"],
            }
        }
        
        if self._cache_enabled and self._cache:
            status["cache_stats"] = self._cache.get_stats()
        
        return status
    
    def get_metrics(self) -> Dict:
        """Performance metrics döndür."""
        return self._metrics.copy()
    
    def reset_metrics(self) -> None:
        """Metrics'i sıfırla."""
        for key in self._metrics:
            self._metrics[key] = 0
    
    def clear_cache(self) -> None:
        """Embedding cache'ini temizle."""
        if self._cache:
            self._cache.clear()
    
    def get_cache_stats(self) -> Optional[Dict]:
        """Cache istatistiklerini döndür."""
        if self._cache:
            return self._cache.get_stats()
        return None


# Singleton instance
embedding_manager = EmbeddingManager()
