"""
Enterprise AI Assistant - Vector Store
Endüstri Standartlarında Kurumsal AI Çözümü

ChromaDB tabanlı vector veritabanı yönetimi.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

from .config import settings
from .embedding import embedding_manager


class VectorStore:
    """
    Vector Store yönetim sınıfı - Endüstri standartlarına uygun.
    
    Özellikler:
    - ChromaDB persistence
    - Metadata filtering
    - Similarity search
    - Batch operations
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        
        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Dökümanları vector store'a ekle.
        
        Args:
            documents: Döküman içerikleri
            metadatas: Metadata listesi (opsiyonel)
            ids: Döküman ID'leri (opsiyonel, otomatik oluşturulur)
            
        Returns:
            Eklenen döküman ID'leri
        """
        if not documents:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Generate embeddings
        print(f"📊 {len(documents)} döküman için embedding oluşturuluyor...")
        embeddings = embedding_manager.embed_texts(documents)
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{}] * len(documents)
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        
        print(f"✅ {len(documents)} döküman eklendi")
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Semantic search yap.
        
        Args:
            query: Arama sorgusu
            n_results: Döndürülecek sonuç sayısı
            where: Metadata filtresi
            where_document: Döküman içerik filtresi
            
        Returns:
            Arama sonuçları (documents, metadatas, distances, ids)
        """
        # Generate query embedding
        query_embedding = embedding_manager.embed_query(query)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"],
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else [],
        }
    
    def search_with_scores(
        self,
        query: str,
        n_results: int = 5,
        score_threshold: float = 0.0,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score ile birlikte semantic search yap.
        
        Args:
            query: Arama sorgusu
            n_results: Döndürülecek sonuç sayısı
            score_threshold: Minimum benzerlik skoru (0-1)
            where: Metadata filtresi
            
        Returns:
            Sonuç listesi [{"document": str, "metadata": dict, "score": float, "id": str}]
        """
        results = self.search(query, n_results, where)
        
        scored_results = []
        for i, doc in enumerate(results["documents"]):
            # ChromaDB distance -> similarity score (cosine distance to similarity)
            distance = results["distances"][i]
            score = 1 - distance  # Convert distance to similarity
            
            if score >= score_threshold:
                scored_results.append({
                    "document": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    "score": score,
                    "id": results["ids"][i] if results["ids"] else None,
                })
        
        return scored_results
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """ID ile döküman getir."""
        try:
            result = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"],
            )
            
            if result["documents"]:
                return {
                    "id": doc_id,
                    "document": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }
            return None
        except Exception:
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """Döküman sil."""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False
    
    def delete_documents(self, doc_ids: List[str]) -> int:
        """Birden fazla döküman sil."""
        try:
            self.collection.delete(ids=doc_ids)
            return len(doc_ids)
        except Exception:
            return 0
    
    def update_document(
        self,
        doc_id: str,
        document: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Döküman güncelle."""
        try:
            update_kwargs = {"ids": [doc_id]}
            
            if document:
                update_kwargs["documents"] = [document]
                update_kwargs["embeddings"] = [embedding_manager.embed_text(document)]
            
            if metadata:
                update_kwargs["metadatas"] = [metadata]
            
            self.collection.update(**update_kwargs)
            return True
        except Exception:
            return False
    
    def count(self) -> int:
        """Toplam döküman sayısını döndür."""
        return self.collection.count()
    
    def clear(self) -> bool:
        """Tüm dökümanları sil."""
        try:
            # Get all IDs
            all_data = self.collection.get()
            if all_data["ids"]:
                self.collection.delete(ids=all_data["ids"])
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Vector store istatistiklerini döndür."""
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "document_count": self.count(),
        }


# Singleton instance
vector_store = VectorStore()
