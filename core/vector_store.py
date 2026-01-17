"""
Enterprise AI Assistant - Vector Store
Endüstri Standartlarında Kurumsal AI Çözümü

ChromaDB tabanlı vector veritabanı yönetimi.

Features:
- Semantic search with scores
- Page-based retrieval
- Metadata filtering
- Batch operations
- Parent-child document support
- Embedding-based search
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

from .config import settings
from .embedding import embedding_manager
from .logger import get_logger

logger = get_logger("vector_store")


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
    
    def delete_by_metadata(self, where: Dict[str, Any]) -> int:
        """
        Metadata'ya göre dökümanları sil.
        
        Args:
            where: Metadata filtresi, örn: {"document_id": "abc123"}
            
        Returns:
            Silinen döküman sayısı
        """
        try:
            # Önce matching dokümanları bul
            results = self.collection.get(where=where)
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                return len(results["ids"])
            
            return 0
        except Exception as e:
            from .logger import get_logger
            logger = get_logger("vector_store")
            logger.error(f"delete_by_metadata failed: {e}")
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
    
    def search_by_embedding(
        self,
        embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hazır embedding ile search yap (HyDE için).
        
        Args:
            embedding: Query embedding
            n_results: Döndürülecek sonuç sayısı
            where: Metadata filtresi
            
        Returns:
            Sonuç listesi
        """
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            
            scored_results = []
            for i, doc in enumerate(results["documents"][0] if results["documents"] else []):
                distance = results["distances"][0][i] if results["distances"] else 1.0
                score = 1 - distance
                
                scored_results.append({
                    "document": doc,
                    "content": doc,  # Alias
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": score,
                    "id": results["ids"][0][i] if results["ids"] else None,
                })
            
            return scored_results
        except Exception as e:
            logger.error(f"Embedding search error: {e}")
            return []
    
    def get_by_page_number(
        self,
        page_number: int,
        source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Sayfa numarasına göre chunk'ları getir.
        
        Args:
            page_number: Sayfa numarası
            source: Kaynak dosya adı (opsiyonel)
            
        Returns:
            Chunk listesi
        """
        try:
            where_filter = {"page_number": page_number}
            if source:
                where_filter = {
                    "$and": [
                        {"page_number": page_number},
                        {"source": {"$eq": source}},
                    ]
                }
            
            results = self.collection.get(
                where=where_filter,
                include=["documents", "metadatas"],
            )
            
            chunks = []
            for i, doc in enumerate(results["documents"] if results["documents"] else []):
                chunks.append({
                    "id": results["ids"][i] if results["ids"] else None,
                    "document": doc,
                    "content": doc,
                    "text": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    "page_number": page_number,
                    "score": 1.0,  # Exact match
                })
            
            return chunks
        except Exception as e:
            logger.warning(f"Page search warning: {e}")
            return []
    
    def get_by_page_numbers(
        self,
        page_numbers: List[int],
        source: Optional[str] = None,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Birden fazla sayfa numarasına göre chunk'ları getir.
        
        Args:
            page_numbers: Sayfa numaraları listesi
            source: Kaynak dosya adı (opsiyonel)
            max_results: Maksimum sonuç sayısı
            
        Returns:
            Chunk listesi (sayfa numarasına göre sıralı)
        """
        all_chunks = []
        
        for page_num in page_numbers:
            chunks = self.get_by_page_number(page_num, source)
            all_chunks.extend(chunks)
        
        # Sayfa numarasına göre sırala
        all_chunks.sort(key=lambda x: (
            x.get("metadata", {}).get("page_number", 0),
            x.get("metadata", {}).get("chunk_index", 0),
        ))
        
        return all_chunks[:max_results]
    
    def get_parent_chunk(self, child_id: str) -> Optional[Dict[str, Any]]:
        """
        Child chunk'ın parent'ını getir.
        
        Args:
            child_id: Child chunk ID
            
        Returns:
            Parent chunk veya None
        """
        try:
            # Child'ın metadata'sını al
            child_result = self.collection.get(
                ids=[child_id],
                include=["metadatas"],
            )
            
            if not child_result["metadatas"]:
                return None
            
            parent_id = child_result["metadatas"][0].get("parent_id")
            if not parent_id:
                return None
            
            # Parent'ı al
            return self.get_document(parent_id)
        except Exception as e:
            logger.error(f"Parent chunk error: {e}")
            return None
    
    def get_children_chunks(self, parent_id: str) -> List[Dict[str, Any]]:
        """
        Parent chunk'ın children'larını getir.
        
        Args:
            parent_id: Parent chunk ID
            
        Returns:
            Children chunk listesi
        """
        try:
            results = self.collection.get(
                where={"parent_id": parent_id},
                include=["documents", "metadatas"],
            )
            
            children = []
            for i, doc in enumerate(results["documents"] if results["documents"] else []):
                children.append({
                    "id": results["ids"][i] if results["ids"] else None,
                    "document": doc,
                    "content": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
            
            # chunk_index'e göre sırala
            children.sort(key=lambda x: x.get("metadata", {}).get("chunk_index", 0))
            return children
        except Exception as e:
            logger.error(f"Children chunks error: {e}")
            return []
    
    def get_unique_sources(self) -> List[str]:
        """Benzersiz kaynak listesini döndür."""
        try:
            all_data = self.collection.get(include=["metadatas"])
            sources = set()
            
            for meta in all_data.get("metadatas", []):
                if meta:
                    source = meta.get("source") or meta.get("filename", "")
                    if source:
                        sources.add(source)
            
            return sorted(list(sources))
        except Exception as e:
            logger.error(f"Get sources error: {e}")
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Detaylı döküman istatistikleri."""
        try:
            all_data = self.collection.get(include=["metadatas"])
            
            stats = {
                "total_chunks": len(all_data.get("ids", [])),
                "sources": {},
                "page_count": {},
                "chunk_types": {"parent": 0, "child": 0, "standalone": 0},
            }
            
            for meta in all_data.get("metadatas", []):
                if not meta:
                    continue
                
                # Source stats
                source = meta.get("source") or meta.get("filename", "unknown")
                if source not in stats["sources"]:
                    stats["sources"][source] = 0
                stats["sources"][source] += 1
                
                # Page stats
                page = meta.get("page_number")
                if page:
                    page_key = f"{source}_page_{page}"
                    if page_key not in stats["page_count"]:
                        stats["page_count"][page_key] = 0
                    stats["page_count"][page_key] += 1
                
                # Chunk type stats
                chunk_type = meta.get("chunk_type", "standalone")
                if chunk_type in stats["chunk_types"]:
                    stats["chunk_types"][chunk_type] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Document stats error: {e}")
            return {"error": str(e)}


# Singleton instance
vector_store = VectorStore()
