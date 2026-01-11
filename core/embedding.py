"""
Enterprise AI Assistant - Embedding Manager
Endüstri Standartlarında Kurumsal AI Çözümü

Ollama tabanlı embedding üretimi - döküman ve sorgu vektörizasyonu.
"""

from typing import List, Optional
import ollama
import numpy as np

from .config import settings


class EmbeddingManager:
    """
    Embedding yönetim sınıfı - Endüstri standartlarına uygun.
    
    Özellikler:
    - Ollama embedding modeli desteği
    - Batch processing
    - Normalization
    - Caching (opsiyonel)
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model_name = model_name or settings.OLLAMA_EMBEDDING_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)
        self.dimension = settings.EMBEDDING_DIMENSION
    
    def check_model_available(self) -> bool:
        """Embedding model'in mevcut olup olmadığını kontrol et."""
        try:
            models = self.client.list()
            available_models = [m["name"] for m in models.get("models", [])]
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
    
    def embed_text(self, text: str) -> List[float]:
        """
        Tek bir metin için embedding üret.
        
        Args:
            text: Embedding yapılacak metin
            
        Returns:
            Embedding vektörü (float listesi)
        """
        try:
            response = self.client.embeddings(
                model=self.model_name,
                prompt=text,
            )
            return response["embedding"]
        except Exception as e:
            print(f"❌ Embedding hatası: {e}")
            raise
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Birden fazla metin için embedding üret.
        
        Args:
            texts: Embedding yapılacak metinler
            batch_size: Batch boyutu
            
        Returns:
            Embedding vektörleri listesi
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
            
            # Progress indicator
            progress = min(i + batch_size, len(texts))
            print(f"📊 Embedding progress: {progress}/{len(texts)}")
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Sorgu için embedding üret (arama optimizasyonu).
        
        Args:
            query: Arama sorgusu
            
        Returns:
            Query embedding vektörü
        """
        # Query prefix eklenebilir (model'e göre)
        return self.embed_text(query)
    
    def embed_document(self, document: str) -> List[float]:
        """
        Döküman için embedding üret (indexing optimizasyonu).
        
        Args:
            document: Döküman içeriği
            
        Returns:
            Document embedding vektörü
        """
        # Document prefix eklenebilir (model'e göre)
        return self.embed_text(document)
    
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
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "dimension": self.dimension,
            "model_available": self.check_model_available(),
        }


# Singleton instance
embedding_manager = EmbeddingManager()
