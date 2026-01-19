"""
Enterprise AI Assistant - Vector Store
Endüstri Standartlarında Kurumsal AI Çözümü

ChromaDB tabanlı vector veritabanı yönetimi.
Yeni ChromaDBManager entegrasyonu ile daha dayanıklı.

Features:
- Semantic search with scores
- Page-based retrieval
- Metadata filtering
- Batch operations
- Parent-child document support
- Embedding-based search
- Automatic corruption recovery
- Health monitoring
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import traceback

from .config import settings
from .embedding import embedding_manager
from .logger import get_logger
from .chromadb_manager import (
    ChromaDBManager,
    ChromaDBConfig,
    get_chromadb_manager,
)

logger = get_logger("vector_store")


class VectorStore:
    """
    Vector Store yönetim sınıfı - Endüstri standartlarına uygun.
    
    Yeni ChromaDBManager ile entegre, daha dayanıklı ve güvenli.
    
    Özellikler:
    - ChromaDB persistence (via ChromaDBManager)
    - Automatic recovery
    - Metadata filtering
    - Similarity search
    - Batch operations
    - Health monitoring
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        
        # Use ChromaDBManager
        config = ChromaDBConfig(
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
            auto_backup=True,
            auto_recovery=True,
            enable_wal_mode=True,
            max_retries=5,
        )
        
        self._manager = get_chromadb_manager(config)
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization."""
        if not self._initialized:
            if not self._manager.is_healthy:
                self._manager.initialize()
            self._initialized = True
    
    @property
    def collection(self):
        """Collection erişimi için backward compatibility."""
        self._ensure_initialized()
        return self._manager._collection
    
    @property
    def client(self):
        """Client erişimi için backward compatibility."""
        self._ensure_initialized()
        return self._manager._client
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        skip_duplicates: bool = True,
    ) -> List[str]:
        """
        Dökümanları vector store'a ekle.
        
        Args:
            documents: Döküman içerikleri
            metadatas: Metadata listesi (opsiyonel)
            ids: Döküman ID'leri (opsiyonel, otomatik oluşturulur)
            skip_duplicates: Duplicate dökümanları atla (varsayılan: True)
            
        Returns:
            Eklenen döküman ID'leri
        """
        self._ensure_initialized()
        
        if not documents:
            return []
        
        # Filter duplicates if enabled
        unique_docs = []
        unique_metadatas = []
        unique_ids = []
        skipped_count = 0
        
        for i, doc in enumerate(documents):
            # Generate content-based hash for duplicate detection
            content_hash = hashlib.md5(doc.strip().encode()).hexdigest()
            doc_id = ids[i] if ids else f"doc_{content_hash[:16]}"
            
            if skip_duplicates:
                # Check if document with this hash already exists
                existing = self._check_duplicate(content_hash, doc)
                if existing:
                    skipped_count += 1
                    logger.debug(f"Duplicate skipped: {content_hash[:8]}...")
                    continue
            
            unique_docs.append(doc)
            unique_metadatas.append(
                {**(metadatas[i] if metadatas else {}), "content_hash": content_hash}
            )
            unique_ids.append(doc_id)
        
        if not unique_docs:
            if skipped_count > 0:
                print(f"⏭️ {skipped_count} duplicate döküman atlandı, yeni döküman yok.")
            return []
        
        # Generate embeddings only for unique documents
        print(f"📊 {len(unique_docs)} döküman için embedding oluşturuluyor...")
        if skipped_count > 0:
            print(f"⏭️ {skipped_count} duplicate döküman atlandı.")
        
        try:
            embeddings = embedding_manager.embed_texts(unique_docs)
            
            # Add via manager
            self._manager.add_documents(
                documents=unique_docs,
                embeddings=embeddings,
                metadatas=unique_metadatas,
                ids=unique_ids,
            )
            
            print(f"✅ {len(unique_docs)} döküman eklendi")
            return unique_ids
            
        except Exception as e:
            logger.error(f"Add documents failed: {e}")
            logger.debug(traceback.format_exc())
            raise
    
    def _check_duplicate(
        self,
        content_hash: str,
        content: str,
        similarity_threshold: float = 0.98,
    ) -> bool:
        """
        Dökümanın duplicate olup olmadığını kontrol et.
        """
        try:
            # First, check by exact content hash in metadata
            existing = self._manager.get(
                where={"content_hash": content_hash},
                limit=1,
            )
            if existing and existing.get("ids"):
                return True
            
            # If no exact match, check by semantic similarity (for near-duplicates)
            if len(content) > 100:
                results = self.search_with_scores(
                    query=content[:500],
                    n_results=1,
                    score_threshold=similarity_threshold,
                )
                if results and results[0]["score"] >= similarity_threshold:
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Semantic search yap."""
        self._ensure_initialized()
        
        query_embedding = embedding_manager.embed_query(query)
        
        results = self._manager.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
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
        """Score ile birlikte semantic search yap."""
        results = self.search(query, n_results, where)
        
        scored_results = []
        for i, doc in enumerate(results["documents"]):
            distance = results["distances"][i]
            score = 1 - distance
            
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
        self._ensure_initialized()
        
        try:
            result = self._manager.get(
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
        except Exception as e:
            logger.warning(f"Get document failed: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """Döküman sil."""
        self._ensure_initialized()
        
        try:
            self._manager.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            return False
    
    def delete_documents(self, doc_ids: List[str]) -> int:
        """Birden fazla döküman sil."""
        self._ensure_initialized()
        
        try:
            self._manager.delete(ids=doc_ids)
            return len(doc_ids)
        except Exception as e:
            logger.error(f"Delete documents failed: {e}")
            return 0
    
    def delete_by_metadata(self, where: Dict[str, Any]) -> int:
        """Metadata'ya göre dökümanları sil."""
        self._ensure_initialized()
        
        try:
            results = self._manager.get(where=where)
            
            if results["ids"]:
                self._manager.delete(ids=results["ids"])
                return len(results["ids"])
            
            return 0
        except Exception as e:
            logger.error(f"delete_by_metadata failed: {e}")
            return 0
    
    def update_document(
        self,
        doc_id: str,
        document: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Döküman güncelle."""
        self._ensure_initialized()
        
        try:
            update_kwargs: Dict[str, Any] = {"ids": [doc_id]}
            
            if document:
                update_kwargs["documents"] = [document]
                update_kwargs["embeddings"] = [embedding_manager.embed_text(document)]
            
            if metadata:
                update_kwargs["metadatas"] = [metadata]
            
            self._manager.update(**update_kwargs)
            return True
        except Exception as e:
            logger.error(f"Update document failed: {e}")
            return False
    
    def count(self) -> int:
        """Toplam döküman sayısını döndür."""
        self._ensure_initialized()
        
        try:
            return self._manager.count()
        except Exception as e:
            logger.error(f"Count failed: {e}")
            return 0
    
    def clear(self) -> bool:
        """Tüm dökümanları sil."""
        self._ensure_initialized()
        
        try:
            self._manager.clear()
            return True
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Vector store istatistiklerini döndür."""
        self._ensure_initialized()
        
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "document_count": self.count(),
            "health": self._manager.get_status().get("health", {}),
        }
    
    def search_by_embedding(
        self,
        embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Hazır embedding ile search yap (HyDE için)."""
        self._ensure_initialized()
        
        try:
            results = self._manager.query(
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
                    "content": doc,
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
        """Sayfa numarasına göre chunk'ları getir."""
        self._ensure_initialized()
        
        try:
            where_filter: Dict[str, Any] = {"page_number": page_number}
            if source:
                where_filter = {
                    "$and": [
                        {"page_number": page_number},
                        {"source": {"$eq": source}},
                    ]
                }
            
            results = self._manager.get(
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
                    "score": 1.0,
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
        """Birden fazla sayfa numarasına göre chunk'ları getir."""
        all_chunks = []
        
        for page_num in page_numbers:
            chunks = self.get_by_page_number(page_num, source)
            all_chunks.extend(chunks)
        
        all_chunks.sort(key=lambda x: (
            x.get("metadata", {}).get("page_number", 0),
            x.get("metadata", {}).get("chunk_index", 0),
        ))
        
        return all_chunks[:max_results]
    
    def get_parent_chunk(self, child_id: str) -> Optional[Dict[str, Any]]:
        """Child chunk'ın parent'ını getir."""
        self._ensure_initialized()
        
        try:
            child_result = self._manager.get(
                ids=[child_id],
                include=["metadatas"],
            )
            
            if not child_result["metadatas"]:
                return None
            
            parent_id = child_result["metadatas"][0].get("parent_id")
            if not parent_id:
                return None
            
            return self.get_document(parent_id)
        except Exception as e:
            logger.error(f"Parent chunk error: {e}")
            return None
    
    def get_children_chunks(self, parent_id: str) -> List[Dict[str, Any]]:
        """Parent chunk'ın children'larını getir."""
        self._ensure_initialized()
        
        try:
            results = self._manager.get(
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
            
            children.sort(key=lambda x: x.get("metadata", {}).get("chunk_index", 0))
            return children
        except Exception as e:
            logger.error(f"Children chunks error: {e}")
            return []
    
    def get_unique_sources(self) -> List[str]:
        """Benzersiz kaynak listesini döndür."""
        self._ensure_initialized()
        
        try:
            all_data = self._manager.get(include=["metadatas"])
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
        self._ensure_initialized()
        
        try:
            all_data = self._manager.get(include=["metadatas"])
            
            stats: Dict[str, Any] = {
                "total_chunks": len(all_data.get("ids", [])),
                "sources": {},
                "page_count": {},
                "chunk_types": {"parent": 0, "child": 0, "standalone": 0},
            }
            
            for meta in all_data.get("metadatas", []):
                if not meta:
                    continue
                
                source = meta.get("source") or meta.get("filename", "unknown")
                if source not in stats["sources"]:
                    stats["sources"][source] = 0
                stats["sources"][source] += 1
                
                page = meta.get("page_number")
                if page:
                    page_key = f"{source}_page_{page}"
                    if page_key not in stats["page_count"]:
                        stats["page_count"][page_key] = 0
                    stats["page_count"][page_key] += 1
                
                chunk_type = meta.get("chunk_type", "standalone")
                if chunk_type in stats["chunk_types"]:
                    stats["chunk_types"][chunk_type] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Document stats error: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Sağlık kontrolü."""
        self._ensure_initialized()
        return self._manager.get_status()
    
    def is_healthy(self) -> bool:
        """Sağlık durumu."""
        return self._manager.is_healthy


# Singleton instance
vector_store = VectorStore()


def initialize_vector_store() -> bool:
    """Vector store'u başlat."""
    try:
        vector_store._ensure_initialized()
        return vector_store.is_healthy()
    except Exception as e:
        logger.error(f"Vector store initialization failed: {e}")
        return False
