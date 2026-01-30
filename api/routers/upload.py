"""
Upload Router
=============

Dosya ve görsel yükleme işlemleri.
"""

import os
import shutil
import uuid
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

# Dizinleri oluştur
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


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
