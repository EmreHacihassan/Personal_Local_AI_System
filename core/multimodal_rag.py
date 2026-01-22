"""
Multi-Modal RAG Engine
Handles PDF, Images, Audio, Video indexing and retrieval
100% Local Processing
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import base64

logger = logging.getLogger(__name__)


class MediaType(Enum):
    TEXT = "text"
    PDF = "pdf"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"


@dataclass
class MultiModalDocument:
    """A document that can contain multiple modalities"""
    id: str
    filename: str
    media_type: MediaType
    content: str  # Extracted text content
    embeddings: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Media-specific fields
    image_descriptions: List[str] = field(default_factory=list)
    audio_transcript: Optional[str] = None
    video_keyframes: List[Dict] = field(default_factory=list)


class MultiModalRAG:
    """
    Multi-Modal RAG Engine
    
    Features:
    - PDF parsing with layout understanding
    - Image analysis and description
    - Audio transcription (Whisper)
    - Video keyframe extraction and analysis
    - Cross-modal semantic search
    """
    
    def __init__(self, storage_dir: str = "data/multimodal"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.documents: Dict[str, MultiModalDocument] = {}
        self.index_path = self.storage_dir / "index.json"
        
        # Initialize components lazily
        self._pdf_processor = None
        self._image_analyzer = None
        self._audio_transcriber = None
        self._video_processor = None
        self._embedder = None
        
        self._load_index()
    
    def _load_index(self):
        """Load document index"""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for doc_data in data.get("documents", []):
                        doc = MultiModalDocument(
                            id=doc_data["id"],
                            filename=doc_data["filename"],
                            media_type=MediaType(doc_data["media_type"]),
                            content=doc_data.get("content", ""),
                            metadata=doc_data.get("metadata", {}),
                            chunks=doc_data.get("chunks", []),
                            created_at=datetime.fromisoformat(doc_data.get("created_at", datetime.now().isoformat())),
                            image_descriptions=doc_data.get("image_descriptions", []),
                            audio_transcript=doc_data.get("audio_transcript"),
                            video_keyframes=doc_data.get("video_keyframes", [])
                        )
                        self.documents[doc.id] = doc
                logger.info(f"Loaded {len(self.documents)} documents from index")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
    
    def _save_index(self):
        """Save document index"""
        try:
            data = {
                "documents": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "media_type": doc.media_type.value,
                        "content": doc.content[:10000],  # Truncate for index
                        "metadata": doc.metadata,
                        "chunks": doc.chunks[:50],  # Limit chunks in index
                        "created_at": doc.created_at.isoformat(),
                        "image_descriptions": doc.image_descriptions,
                        "audio_transcript": doc.audio_transcript[:5000] if doc.audio_transcript else None,
                        "video_keyframes": doc.video_keyframes[:20]
                    }
                    for doc in self.documents.values()
                ],
                "updated_at": datetime.now().isoformat()
            }
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def _get_file_hash(self, content: bytes) -> str:
        """Generate file hash for deduplication"""
        return hashlib.md5(content).hexdigest()
    
    def _detect_media_type(self, filename: str) -> MediaType:
        """Detect media type from filename"""
        ext = Path(filename).suffix.lower()
        
        if ext == '.pdf':
            return MediaType.PDF
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return MediaType.IMAGE
        elif ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
            return MediaType.AUDIO
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            return MediaType.VIDEO
        elif ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.rs', '.go']:
            return MediaType.CODE
        else:
            return MediaType.TEXT
    
    async def index_file(self, filepath: str, metadata: Optional[Dict] = None) -> MultiModalDocument:
        """
        Index a file of any supported type
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(path, 'rb') as f:
            content = f.read()
        
        file_hash = self._get_file_hash(content)
        doc_id = f"{path.stem}_{file_hash[:8]}"
        
        # Check if already indexed
        if doc_id in self.documents:
            logger.info(f"Document already indexed: {doc_id}")
            return self.documents[doc_id]
        
        media_type = self._detect_media_type(path.name)
        
        # Process based on type
        extracted_text = ""
        image_descriptions = []
        audio_transcript = None
        video_keyframes = []
        
        if media_type == MediaType.PDF:
            extracted_text, image_descriptions = await self._process_pdf(content)
        elif media_type == MediaType.IMAGE:
            image_descriptions = await self._process_image(content)
            extracted_text = "\n".join(image_descriptions)
        elif media_type == MediaType.AUDIO:
            audio_transcript = await self._process_audio(content, path.suffix)
            extracted_text = audio_transcript
        elif media_type == MediaType.VIDEO:
            video_keyframes, audio_transcript = await self._process_video(filepath)
            extracted_text = "\n".join([kf.get("description", "") for kf in video_keyframes])
            if audio_transcript:
                extracted_text += "\n\n" + audio_transcript
        elif media_type == MediaType.CODE:
            extracted_text = content.decode('utf-8', errors='ignore')
        else:
            extracted_text = content.decode('utf-8', errors='ignore')
        
        # Create chunks
        chunks = self._create_chunks(extracted_text)
        
        # Create document
        doc = MultiModalDocument(
            id=doc_id,
            filename=path.name,
            media_type=media_type,
            content=extracted_text,
            metadata=metadata or {},
            chunks=chunks,
            image_descriptions=image_descriptions,
            audio_transcript=audio_transcript,
            video_keyframes=video_keyframes
        )
        
        doc.metadata["file_size"] = len(content)
        doc.metadata["file_path"] = str(path.absolute())
        
        self.documents[doc_id] = doc
        self._save_index()
        
        logger.info(f"Indexed {media_type.value}: {path.name} ({len(chunks)} chunks)")
        
        return doc
    
    async def index_content(
        self, 
        content: bytes, 
        filename: str,
        metadata: Optional[Dict] = None
    ) -> MultiModalDocument:
        """Index content from memory"""
        temp_path = self.storage_dir / "temp" / filename
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        try:
            doc = await self.index_file(str(temp_path), metadata)
            return doc
        finally:
            # Cleanup temp file
            try:
                temp_path.unlink()
            except:
                pass
    
    async def _process_pdf(self, content: bytes) -> Tuple[str, List[str]]:
        """
        Process PDF with text and image extraction
        """
        extracted_text = ""
        image_descriptions = []
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(stream=content, filetype="pdf")
            
            for page_num, page in enumerate(doc):
                # Extract text
                text = page.get_text()
                extracted_text += f"\n--- Page {page_num + 1} ---\n{text}"
                
                # Extract images
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Analyze image
                        descriptions = await self._process_image(image_bytes)
                        if descriptions:
                            image_descriptions.extend(descriptions)
                            extracted_text += f"\n[Image {img_index + 1}: {descriptions[0]}]\n"
                    except Exception as e:
                        logger.warning(f"Failed to extract image from PDF: {e}")
            
            doc.close()
            
        except ImportError:
            logger.warning("PyMuPDF not installed, falling back to basic PDF parsing")
            # Fallback: try pdfminer
            try:
                from pdfminer.high_level import extract_text
                import io
                extracted_text = extract_text(io.BytesIO(content))
            except ImportError:
                logger.error("No PDF library available")
                extracted_text = "[PDF parsing libraries not available]"
        
        return extracted_text.strip(), image_descriptions
    
    async def _process_image(self, content: bytes) -> List[str]:
        """
        Analyze image using Vision AI
        """
        descriptions = []
        
        try:
            # Use Ollama with llava model
            import httpx
            
            # Encode image
            image_b64 = base64.b64encode(content).decode('utf-8')
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llava",
                        "prompt": """Analyze this image in detail. Describe:
1. Main subject and content
2. Text visible in the image (OCR)
3. Colors, layout, and composition
4. Any relevant context or meaning

Provide a comprehensive description for search indexing.""",
                        "images": [image_b64],
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    description = result.get("response", "")
                    if description:
                        descriptions.append(description)
                        
        except Exception as e:
            logger.warning(f"Image analysis failed: {e}")
            descriptions.append("[Image analysis unavailable]")
        
        return descriptions
    
    async def _process_audio(self, content: bytes, ext: str) -> str:
        """
        Transcribe audio using Whisper
        """
        try:
            from faster_whisper import WhisperModel
            import tempfile
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                model = WhisperModel("base", device="cpu", compute_type="int8")
                segments, info = model.transcribe(temp_path)
                
                transcript = ""
                for segment in segments:
                    transcript += f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}\n"
                
                return transcript.strip()
                
            finally:
                os.unlink(temp_path)
                
        except ImportError:
            logger.warning("faster-whisper not installed")
            return "[Audio transcription unavailable - install faster-whisper]"
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return f"[Transcription failed: {e}]"
    
    async def _process_video(self, filepath: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Process video: extract keyframes and transcribe audio
        """
        keyframes = []
        transcript = None
        
        try:
            import cv2
            
            cap = cv2.VideoCapture(filepath)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Extract keyframes (every 5 seconds)
            interval = int(fps * 5)
            frame_idx = 0
            
            while cap.isOpened() and len(keyframes) < 50:  # Max 50 keyframes
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx % interval == 0:
                    timestamp = frame_idx / fps
                    
                    # Encode frame
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    
                    # Analyze frame
                    descriptions = await self._process_image(frame_bytes)
                    
                    keyframes.append({
                        "timestamp": timestamp,
                        "frame_index": frame_idx,
                        "description": descriptions[0] if descriptions else ""
                    })
                
                frame_idx += 1
            
            cap.release()
            
            # Extract and transcribe audio
            try:
                import subprocess
                import tempfile
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    audio_path = f.name
                
                # Extract audio with ffmpeg
                subprocess.run([
                    'ffmpeg', '-i', filepath, '-vn', '-acodec', 'pcm_s16le',
                    '-ar', '16000', '-ac', '1', audio_path, '-y'
                ], capture_output=True, check=True)
                
                with open(audio_path, 'rb') as f:
                    audio_content = f.read()
                
                transcript = await self._process_audio(audio_content, '.wav')
                
                os.unlink(audio_path)
                
            except Exception as e:
                logger.warning(f"Audio extraction failed: {e}")
            
        except ImportError:
            logger.warning("OpenCV not installed for video processing")
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
        
        return keyframes, transcript
    
    def _create_chunks(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
        """Split text into overlapping chunks"""
        chunks = []
        
        if not text:
            return chunks
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_idx = 0
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "id": chunk_idx,
                        "content": current_chunk.strip(),
                        "char_start": len("\n\n".join([c["content"] for c in chunks])),
                        "char_end": len("\n\n".join([c["content"] for c in chunks])) + len(current_chunk)
                    })
                    chunk_idx += 1
                
                # Handle long paragraphs
                if len(para) > chunk_size:
                    words = para.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk) + len(word) <= chunk_size:
                            current_chunk += word + " "
                        else:
                            chunks.append({
                                "id": chunk_idx,
                                "content": current_chunk.strip(),
                                "char_start": 0,
                                "char_end": len(current_chunk)
                            })
                            chunk_idx += 1
                            current_chunk = word + " "
                else:
                    current_chunk = para + "\n\n"
        
        # Add remaining
        if current_chunk.strip():
            chunks.append({
                "id": chunk_idx,
                "content": current_chunk.strip(),
                "char_start": 0,
                "char_end": len(current_chunk)
            })
        
        return chunks
    
    async def search(
        self, 
        query: str, 
        media_types: Optional[List[MediaType]] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Semantic search across all indexed content
        """
        results = []
        
        # Filter by media type
        docs_to_search = list(self.documents.values())
        if media_types:
            docs_to_search = [d for d in docs_to_search if d.media_type in media_types]
        
        query_lower = query.lower()
        
        for doc in docs_to_search:
            # Simple keyword matching (replace with embeddings for production)
            score = 0
            matched_chunks = []
            
            # Search in content
            if query_lower in doc.content.lower():
                score += 5
            
            # Search in chunks
            for chunk in doc.chunks:
                chunk_content = chunk.get("content", "").lower()
                if query_lower in chunk_content:
                    score += 1
                    matched_chunks.append(chunk)
            
            # Search in image descriptions
            for desc in doc.image_descriptions:
                if query_lower in desc.lower():
                    score += 2
            
            # Search in audio transcript
            if doc.audio_transcript and query_lower in doc.audio_transcript.lower():
                score += 3
            
            # Search in video keyframes
            for kf in doc.video_keyframes:
                if query_lower in kf.get("description", "").lower():
                    score += 2
            
            if score > 0:
                results.append({
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "media_type": doc.media_type.value,
                    "score": score,
                    "matched_chunks": matched_chunks[:3],
                    "content_preview": doc.content[:500] if doc.content else "",
                    "metadata": doc.metadata
                })
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    async def ask(self, question: str, media_types: Optional[List[MediaType]] = None) -> Dict:
        """
        Ask a question and get AI-generated answer with sources
        """
        # Search for relevant content
        search_results = await self.search(question, media_types, top_k=5)
        
        if not search_results:
            return {
                "answer": "Belirtilen kriterlere uygun kaynak bulunamadı.",
                "sources": []
            }
        
        # Build context
        context_parts = []
        for result in search_results:
            doc = self.documents.get(result["document_id"])
            if doc:
                context_parts.append(f"[{doc.filename}]\n{doc.content[:2000]}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Generate answer with LLM
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": f"""Aşağıdaki kaynaklara dayanarak soruyu yanıtla.

Kaynaklar:
{context}

Soru: {question}

Yanıt:""",
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get("response", "")
                else:
                    answer = "LLM yanıt üretemedi."
                    
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            answer = f"Yanıt üretilirken hata oluştu: {e}"
        
        return {
            "answer": answer,
            "sources": [
                {
                    "document_id": r["document_id"],
                    "filename": r["filename"],
                    "media_type": r["media_type"],
                    "score": r["score"]
                }
                for r in search_results
            ]
        }
    
    def list_documents(self, media_type: Optional[MediaType] = None) -> List[Dict]:
        """List all indexed documents"""
        docs = list(self.documents.values())
        
        if media_type:
            docs = [d for d in docs if d.media_type == media_type]
        
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "media_type": doc.media_type.value,
                "chunk_count": len(doc.chunks),
                "has_images": len(doc.image_descriptions) > 0,
                "has_audio": doc.audio_transcript is not None,
                "has_video": len(doc.video_keyframes) > 0,
                "created_at": doc.created_at.isoformat(),
                "metadata": doc.metadata
            }
            for doc in docs
        ]
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document details"""
        doc = self.documents.get(doc_id)
        if not doc:
            return None
        
        return {
            "id": doc.id,
            "filename": doc.filename,
            "media_type": doc.media_type.value,
            "content": doc.content,
            "chunks": doc.chunks,
            "image_descriptions": doc.image_descriptions,
            "audio_transcript": doc.audio_transcript,
            "video_keyframes": doc.video_keyframes,
            "created_at": doc.created_at.isoformat(),
            "metadata": doc.metadata
        }
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save_index()
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get indexing statistics"""
        stats = {
            "total_documents": len(self.documents),
            "by_type": {},
            "total_chunks": 0,
            "total_images": 0,
            "total_keyframes": 0
        }
        
        for doc in self.documents.values():
            type_key = doc.media_type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            stats["total_chunks"] += len(doc.chunks)
            stats["total_images"] += len(doc.image_descriptions)
            stats["total_keyframes"] += len(doc.video_keyframes)
        
        return stats


# Singleton
_multimodal_rag = None

def get_multimodal_rag() -> MultiModalRAG:
    global _multimodal_rag
    if _multimodal_rag is None:
        _multimodal_rag = MultiModalRAG()
    return _multimodal_rag
