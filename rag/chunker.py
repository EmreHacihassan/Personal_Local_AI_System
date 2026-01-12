"""
Enterprise AI Assistant - Document Chunker
Endüstri Standartlarında Kurumsal AI Çözümü

Akıllı döküman parçalama - RecursiveCharacterTextSplitter ve semantic chunking.
Sayfa takibi ve bağlamsal bölümleme desteği ile.
"""

from typing import List, Dict, Any, Optional
import re
import hashlib

import sys
sys.path.append('..')

from core.config import settings


class Chunk:
    """Chunk veri yapısı."""
    
    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_index: int = 0,
    ):
        self.content = content
        self.metadata = metadata or {}
        self.chunk_index = chunk_index
        self.word_count = len(content.split())
        self.char_count = len(content)
        
        # Unique chunk ID
        self.chunk_id = self._generate_chunk_id()
    
    def _generate_chunk_id(self) -> str:
        """Chunk için benzersiz ID oluştur."""
        source = self.metadata.get("source", "unknown")
        content_hash = hashlib.md5(self.content[:200].encode()).hexdigest()[:8]
        return f"{source}_{self.chunk_index}_{content_hash}"
    
    def __repr__(self) -> str:
        return f"Chunk(index={self.chunk_index}, chars={self.char_count})"


class DocumentChunker:
    """
    Döküman parçalama sınıfı - Endüstri standartlarına uygun.
    
    Stratejiler:
    - Recursive: Hiyerarşik ayraçlarla bölme
    - Fixed: Sabit boyutlu parçalama
    - Semantic: Anlam tabanlı bölme
    - Markdown: Header tabanlı bölme
    - Page-aware: Sayfa sınırlarını koruyarak bölme
    """
    
    # Sayfa işaretçileri
    PAGE_MARKERS = [
        r'\[PAGE:\s*(\d+)\]',
        r'---\s*Page\s*(\d+)\s*---',
        r'\n\s*-{3,}\s*(\d+)\s*-{3,}\n',
        r'Sayfa\s*(\d+)',
        r'Page\s*(\d+)',
    ]
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Default separators for recursive splitting
        self.separators = [
            "\n\n\n",  # Multiple newlines (section breaks)
            "\n\n",    # Paragraph breaks
            "\n",      # Line breaks
            ". ",      # Sentences
            "! ",
            "? ",
            "; ",
            ", ",      # Clauses
            " ",       # Words
            "",        # Characters
        ]
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        strategy: str = "recursive",
    ) -> List[Chunk]:
        """
        Metni parçalara ayır.
        
        Args:
            text: Parçalanacak metin
            metadata: Temel metadata (her chunk'a kopyalanır)
            strategy: Parçalama stratejisi (recursive, fixed, sentence, page_aware)
            
        Returns:
            Chunk listesi
        """
        if not text.strip():
            return []
        
        if strategy == "recursive":
            return self._recursive_chunk(text, metadata)
        elif strategy == "fixed":
            return self._fixed_chunk(text, metadata)
        elif strategy == "sentence":
            return self._sentence_chunk(text, metadata)
        elif strategy == "page_aware":
            return self._page_aware_chunk(text, metadata)
        else:
            return self._recursive_chunk(text, metadata)
    
    def chunk_documents(
        self,
        documents: List[Any],
        strategy: str = "recursive",
    ) -> List[Chunk]:
        """
        Document listesini chunk'lara ayır.
        
        Args:
            documents: Document listesi (Document.content ve Document.metadata)
            strategy: Parçalama stratejisi
            
        Returns:
            Chunk listesi
        """
        all_chunks = []
        
        for doc_idx, doc in enumerate(documents):
            # Sayfa numarası metadata'da varsa kullan
            doc_metadata = doc.metadata.copy() if doc.metadata else {}
            doc_metadata["document_index"] = doc_idx
            
            # PDF'ler için sayfa bazlı strateji
            file_type = doc_metadata.get("file_type", "")
            if file_type == ".pdf" and self._has_page_markers(doc.content):
                chunks = self._page_aware_chunk(doc.content, doc_metadata)
            else:
                chunks = self.chunk_text(
                    text=doc.content,
                    metadata=doc_metadata,
                    strategy=strategy,
                )
            
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _has_page_markers(self, text: str) -> bool:
        """Metinde sayfa işaretçileri var mı kontrol et."""
        for pattern in self.PAGE_MARKERS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _extract_page_number(self, text: str) -> Optional[int]:
        """Metinden sayfa numarasını çıkar."""
        for pattern in self.PAGE_MARKERS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    pass
        return None
    
    def _page_aware_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """
        Sayfa sınırlarını koruyarak parçala.
        Her chunk'a sayfa numarası metadata'sı ekle.
        """
        chunks = []
        current_page = 1
        chunk_index = 0
        
        # Sayfa işaretçilerine göre böl
        page_pattern = r'(\[PAGE:\s*\d+\]|---\s*Page\s*\d+\s*---|Sayfa\s*\d+|Page\s*\d+)'
        segments = re.split(page_pattern, text, flags=re.IGNORECASE)
        
        current_content = []
        current_length = 0
        
        for segment in segments:
            if not segment.strip():
                continue
            
            # Sayfa işaretçisi mi kontrol et
            page_num = self._extract_page_number(segment)
            if page_num:
                current_page = page_num
                continue
            
            # Segment çok uzunsa recursive olarak böl
            if len(segment) > self.chunk_size:
                # Önce mevcut içeriği kaydet
                if current_content:
                    chunk_text = "\n".join(current_content)
                    chunk_metadata = (metadata or {}).copy()
                    chunk_metadata["chunk_index"] = chunk_index
                    chunk_metadata["page"] = current_page
                    chunk_metadata["page_number"] = current_page
                    chunk_metadata["strategy"] = "page_aware"
                    
                    chunks.append(Chunk(
                        content=chunk_text.strip(),
                        metadata=chunk_metadata,
                        chunk_index=chunk_index,
                    ))
                    chunk_index += 1
                    current_content = []
                    current_length = 0
                
                # Uzun segmenti recursive olarak böl
                sub_chunks = self._recursive_chunk(segment, metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata["page"] = current_page
                    sub_chunk.metadata["page_number"] = current_page
                    sub_chunk.chunk_index = chunk_index
                    sub_chunk.metadata["chunk_index"] = chunk_index
                    chunks.append(sub_chunk)
                    chunk_index += 1
            
            elif current_length + len(segment) > self.chunk_size:
                # Mevcut içeriği kaydet
                if current_content:
                    chunk_text = "\n".join(current_content)
                    chunk_metadata = (metadata or {}).copy()
                    chunk_metadata["chunk_index"] = chunk_index
                    chunk_metadata["page"] = current_page
                    chunk_metadata["page_number"] = current_page
                    chunk_metadata["strategy"] = "page_aware"
                    
                    chunks.append(Chunk(
                        content=chunk_text.strip(),
                        metadata=chunk_metadata,
                        chunk_index=chunk_index,
                    ))
                    chunk_index += 1
                
                # Overlap için son paragrafı tut
                if self.chunk_overlap > 0 and current_content:
                    overlap_text = current_content[-1]
                    if len(overlap_text) <= self.chunk_overlap:
                        current_content = [overlap_text]
                        current_length = len(overlap_text)
                    else:
                        current_content = []
                        current_length = 0
                else:
                    current_content = []
                    current_length = 0
                
                current_content.append(segment)
                current_length += len(segment)
            else:
                current_content.append(segment)
                current_length += len(segment)
        
        # Kalan içeriği ekle
        if current_content:
            chunk_text = "\n".join(current_content)
            if chunk_text.strip():
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata["chunk_index"] = chunk_index
                chunk_metadata["page"] = current_page
                chunk_metadata["page_number"] = current_page
                chunk_metadata["strategy"] = "page_aware"
                
                chunks.append(Chunk(
                    content=chunk_text.strip(),
                    metadata=chunk_metadata,
                    chunk_index=chunk_index,
                ))
        
        # Total chunks güncelle
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)
        
        return chunks
    
    def _recursive_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """
        Recursive character text splitter - LangChain tarzı.
        """
        chunks = self._split_recursive(text, self.separators)
        
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            chunk_metadata["strategy"] = "recursive"
            
            result.append(Chunk(
                content=chunk_text,
                metadata=chunk_metadata,
                chunk_index=i,
            ))
        
        return result
    
    def _split_recursive(
        self,
        text: str,
        separators: List[str],
    ) -> List[str]:
        """Recursive splitting logic."""
        final_chunks = []
        
        # Find the best separator
        separator = separators[-1]  # Default to last (empty string)
        for sep in separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break
        
        # Split by separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
        
        # Process splits
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = len(split) + len(separator)
            
            if current_length + split_length > self.chunk_size:
                if current_chunk:
                    chunk_text = separator.join(current_chunk)
                    
                    # If chunk is still too large, recurse with next separator
                    if len(chunk_text) > self.chunk_size:
                        remaining_seps = separators[separators.index(separator) + 1:]
                        if remaining_seps:
                            final_chunks.extend(
                                self._split_recursive(chunk_text, remaining_seps)
                            )
                        else:
                            final_chunks.append(chunk_text)
                    else:
                        final_chunks.append(chunk_text)
                    
                    # Handle overlap
                    if self.chunk_overlap > 0 and len(current_chunk) > 1:
                        overlap_text = separator.join(current_chunk[-2:])
                        if len(overlap_text) <= self.chunk_overlap:
                            current_chunk = current_chunk[-2:]
                            current_length = len(overlap_text)
                        else:
                            current_chunk = [current_chunk[-1]]
                            current_length = len(current_chunk[0])
                    else:
                        current_chunk = []
                        current_length = 0
            
            current_chunk.append(split)
            current_length += split_length
        
        # Add remaining
        if current_chunk:
            final_chunks.append(separator.join(current_chunk))
        
        return [c for c in final_chunks if c.strip()]
    
    def _fixed_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Sabit boyutlu parçalama."""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Find a good break point
            if end < len(text):
                # Try to break at sentence
                for sep in [". ", "! ", "? ", "\n", " "]:
                    last_sep = chunk_text.rfind(sep)
                    if last_sep > self.chunk_size * 0.5:
                        chunk_text = chunk_text[:last_sep + len(sep)]
                        end = start + len(chunk_text)
                        break
            
            if chunk_text.strip():
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata["chunk_index"] = chunk_index
                chunk_metadata["strategy"] = "fixed"
                
                chunks.append(Chunk(
                    content=chunk_text.strip(),
                    metadata=chunk_metadata,
                    chunk_index=chunk_index,
                ))
                chunk_index += 1
            
            # Move with overlap
            start = end - self.chunk_overlap
        
        # Update total_chunks
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)
        
        return chunks
    
    def _sentence_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Cümle tabanlı parçalama."""
        # Split into sentences
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata["chunk_index"] = chunk_index
                chunk_metadata["strategy"] = "sentence"
                
                chunks.append(Chunk(
                    content=chunk_text,
                    metadata=chunk_metadata,
                    chunk_index=chunk_index,
                ))
                chunk_index += 1
                
                # Reset with overlap (keep last sentence)
                if self.chunk_overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[0])
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space
        
        # Add remaining
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata["chunk_index"] = chunk_index
            chunk_metadata["strategy"] = "sentence"
            
            chunks.append(Chunk(
                content=chunk_text,
                metadata=chunk_metadata,
                chunk_index=chunk_index,
            ))
        
        # Update total_chunks
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)
        
        return chunks
    
    def chunk_markdown(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """
        Markdown header'larına göre parçala.
        """
        # Find headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = text.split('\n')
        
        chunks = []
        current_content = []
        current_headers = {}
        chunk_index = 0
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Save previous chunk
                if current_content:
                    chunk_text = '\n'.join(current_content).strip()
                    if chunk_text:
                        chunk_metadata = (metadata or {}).copy()
                        chunk_metadata.update(current_headers)
                        chunk_metadata["chunk_index"] = chunk_index
                        chunk_metadata["strategy"] = "markdown"
                        
                        chunks.append(Chunk(
                            content=chunk_text,
                            metadata=chunk_metadata,
                            chunk_index=chunk_index,
                        ))
                        chunk_index += 1
                
                # Update headers
                level = len(header_match.group(1))
                header_text = header_match.group(2)
                
                # Clear lower level headers
                current_headers = {
                    k: v for k, v in current_headers.items()
                    if int(k[1:]) < level
                }
                current_headers[f"h{level}"] = header_text
                current_content = [line]
            else:
                current_content.append(line)
        
        # Add remaining
        if current_content:
            chunk_text = '\n'.join(current_content).strip()
            if chunk_text:
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata.update(current_headers)
                chunk_metadata["chunk_index"] = chunk_index
                chunk_metadata["strategy"] = "markdown"
                
                chunks.append(Chunk(
                    content=chunk_text,
                    metadata=chunk_metadata,
                    chunk_index=chunk_index,
                ))
        
        # Update total_chunks
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)
        
        return chunks


# Singleton instance
document_chunker = DocumentChunker()
