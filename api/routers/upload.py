"""
Upload Router
=============

Dosya ve görsel yükleme işlemleri.
"""

import os
import shutil
import uuid
import mimetypes
from typing import List
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from core.config import settings
from core.logger import get_logger

logger = get_logger("upload_router")

router = APIRouter(prefix="/api/upload", tags=["Upload"])

# Upload dizinleri
UPLOAD_DIR = settings.DATA_DIR / "uploads"
IMAGES_DIR = UPLOAD_DIR / "images"
FILES_DIR = UPLOAD_DIR / "files"

# Dizinleri oluştur
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)

# Dosya metadata'larını saklamak için
FILES_METADATA_PATH = UPLOAD_DIR / "files_metadata.json"

def _load_files_metadata() -> dict:
    """Dosya metadata'larını yükle."""
    import json
    try:
        if FILES_METADATA_PATH.exists():
            with open(FILES_METADATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Files metadata load error: {e}")
    return {}

def _save_files_metadata(metadata: dict):
    """Dosya metadata'larını kaydet."""
    import json
    try:
        with open(FILES_METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Files metadata save error: {e}")


# ============== FILE UPLOAD (Premium Feature) ==============

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """
    Herhangi bir dosya yükle (PDF, DOCX, PPTX, ZIP, vb.).
    Max 500MB.
    """
    try:
        # Klasörün var olduğundan emin ol
        FILES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Dosya boyutu kontrolü
        file.file.seek(0, 2)  # Dosya sonuna git
        file_size = file.file.tell()  # Boyutu al
        file.file.seek(0)  # Başa dön
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Dosya çok büyük. Maximum: 500MB, Gönderilen: {file_size / (1024*1024):.2f}MB"
            )
        
        # Unique dosya adı oluştur
        file_id = str(uuid.uuid4())
        original_name = file.filename or "unknown"
        file_ext = Path(original_name).suffix.lower()
        new_filename = f"{file_id}{file_ext}"
        file_path = FILES_DIR / new_filename
        
        # MIME type belirle
        mime_type = file.content_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        
        # Dosyayı kaydet
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Metadata kaydet
        metadata = _load_files_metadata()
        metadata[file_id] = {
            "id": file_id,
            "name": new_filename,
            "original_name": original_name,
            "file_type": mime_type,
            "size": file_size,
            "uploaded_at": datetime.now().isoformat()
        }
        _save_files_metadata(metadata)
        
        # URL oluştur
        url = f"/static/uploads/files/{new_filename}"
        
        logger.info(f"Dosya yüklendi: {original_name} -> {new_filename} ({file_size} bytes)")
        
        return {
            "success": True,
            "id": file_id,
            "url": url,
            "name": new_filename,
            "original_name": original_name,
            "file_type": mime_type,
            "size": file_size,
            "uploaded_at": metadata[file_id]["uploaded_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dosya yükleme hatası: {str(e)}")


@router.get("/file/{file_id}")
async def download_file(file_id: str):
    """
    Dosyayı indir (orijinal dosya adıyla).
    """
    try:
        metadata = _load_files_metadata()
        
        if file_id not in metadata:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        file_info = metadata[file_id]
        file_path = FILES_DIR / file_info["name"]
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        return FileResponse(
            path=str(file_path),
            filename=file_info["original_name"],
            media_type=file_info.get("file_type", "application/octet-stream")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download error: {e}")
        raise HTTPException(status_code=500, detail=f"İndirme hatası: {str(e)}")


@router.delete("/file/{file_id}")
async def delete_file(file_id: str):
    """
    Dosyayı sil.
    """
    try:
        metadata = _load_files_metadata()
        
        if file_id not in metadata:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        file_info = metadata[file_id]
        file_path = FILES_DIR / file_info["name"]
        
        # Dosyayı sil
        if file_path.exists():
            os.remove(file_path)
        
        # Metadata'dan kaldır
        del metadata[file_id]
        _save_files_metadata(metadata)
        
        logger.info(f"Dosya silindi: {file_info['original_name']}")
        
        return {"success": True, "message": "Dosya silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Silme hatası: {str(e)}")


@router.get("/file/{file_id}/info")
async def get_file_info(file_id: str):
    """
    Dosya bilgilerini getir.
    """
    try:
        metadata = _load_files_metadata()
        
        if file_id not in metadata:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        return metadata[file_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File info error: {e}")
        raise HTTPException(status_code=500, detail=f"Bilgi hatası: {str(e)}")


@router.post("/image/base64")
async def upload_image_base64(data: dict):
    print("\n[DEBUG] === Base64 Upload Start ===")
    try:
        import os
        import base64
        import uuid
        
        # Veri kontrolü
        image_data = data.get("image", "")
        original_filename = data.get("filename", "image.png")
        print(f"[DEBUG] Filename: {original_filename}")
        print(f"[DEBUG] Data length: {len(image_data)}")

        if not image_data:
            print("[DEBUG] Error: No image data")
            raise HTTPException(status_code=400, detail="Görsel verisi eksik")

        # Klasör Yolu (Windows Garantili)
        # settings.DATA_DIR normalde C:/Users/LENOVO/AgenticData
        target_dir = os.path.normpath("C:/Users/LENOVO/AgenticData/uploads/images")
        if not os.path.exists(target_dir):
            print(f"[DEBUG] Creating directory: {target_dir}")
            os.makedirs(target_dir, exist_ok=True)

        # Base64 Decode
        if "," in image_data:
            header, encoded = image_data.split(",", 1)
            print(f"[DEBUG] Header found: {header}")
        else:
            encoded = image_data
            print("[DEBUG] No header found")

        # Uzantı ayarla
        ext = os.path.splitext(original_filename)[1].lower() or ".png"
        new_filename = f"{uuid.uuid4()}{ext}"
        full_path = os.path.join(target_dir, new_filename)
        print(f"[DEBUG] Target path: {full_path}")

        # Yazma İşlemi
        with open(full_path, "wb") as f:
            f.write(base64.b64decode(encoded))
        
        # Yazma Onayı
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print(f"[DEBUG] SUCCESS: File saved. Size: {file_size} bytes")
        else:
            print("[DEBUG] FAILURE: File not found after write!")
            raise Exception("Dosya diske yazılamadı")

        # URL Oluştur
        # Not: main.py'da settings.DATA_DIR (C:/Users/LENOVO/AgenticData) /static olarak mount edildi
        url = f"/static/uploads/images/{new_filename}"
        
        return {
            "url": url,
            "filename": new_filename,
            "original_name": original_filename
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[DEBUG] CRITICAL ERROR: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Base64 Upload Error: {error_msg}")

@router.get("/ping")
async def ping_upload():
    return {"status": "ok", "message": "Upload router is alive"}


# Eski endpoint (Multipart) - Geriye uyumluluk için kalsın ama try-except içinde
@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Görsel yükle ve URL döndür.
    """
    # Klasörün var olduğundan emin ol (Silinmiş olabilir)
    try:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Klasör oluşturma hatası: {e}")
        pass

    try:
        # İzin verilen uzantılar
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff", ".ico", ".heic"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Geçersiz dosya türü. İzin verilenler: {', '.join(allowed_extensions)}"
            )
        
        # Unique dosya adı
        file_id = str(uuid.uuid4())
        new_filename = f"{file_id}{file_ext}"
        file_path = IMAGES_DIR / new_filename
        
        # Dosyayı kaydet
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # URL oluştur (Frontend'in erişebileceği path)
        # Not: api/main.py'da /static mount edildiğinde:
        # http://localhost:8000/static/uploads/images/filename.jpg
        url = f"/static/uploads/images/{new_filename}"
        
        logger.info(f"Görsel yüklendi: {new_filename}")
        
        return {
            "url": url,
            "filename": new_filename,
            "original_name": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Traceback: {traceback_str}")
        
        # Hata detayını frontend'e dönmek için (Debug only)
        # Production'da bu kadar detay verilmez ama şu an sorunu çözmek için gerekli.
        error_detail = f"Server Error: {str(e)}"
        
        # Windows Permission Error check
        if "Permission denied" in str(e):
            error_detail += " (Dosya yazma izni yok. Klasör yollarını kontrol edin.)"
            
        raise HTTPException(status_code=500, detail=error_detail)
