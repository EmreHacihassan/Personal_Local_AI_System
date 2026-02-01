"""
Notes Vision - OCR ve Görsel Analiz Modülü
==========================================

LLaVA Vision modeli kullanarak:
- Görsellerden metin çıkarma (OCR)
- Matematiksel formül tanıma (LaTeX çıktı)  
- Görsel açıklama oluşturma

Tesseract yerine LLaVA tercih edildi çünkü:
- Kurulum gerektirmez (Ollama üzerinden çalışır)
- GPU hızlandırmalı
- Daha iyi Türkçe desteği
- Bağlam anlayışı (sadece metin değil, anlam da çıkarır)
"""

import base64
import logging
from pathlib import Path
from typing import Dict, Optional
import httpx

from core.config import settings

logger = logging.getLogger("notes_vision")


class NotesVision:
    """
    Not sistemleri için görsel analiz ve OCR işlemleri.
    LLaVA Vision modeli kullanır.
    """
    
    def __init__(self):
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        self.vision_model = "llava"  # veya llama3.2-vision:11b
        self.timeout = 60.0
        logger.info("NotesVision initialized")
    
    def _image_to_base64(self, image_path: str) -> Optional[str]:
        """Görsel dosyasını base64'e çevir."""
        try:
            path = Path(image_path)
            
            # Eğer /static/ ile başlıyorsa, data dizinine çevir
            if image_path.startswith("/static/"):
                relative_path = image_path.replace("/static/", "")
                path = settings.DATA_DIR / relative_path
            
            if not path.exists():
                logger.error(f"Image not found: {path}")
                return None
            
            with open(path, "rb") as f:
                image_data = f.read()
            
            return base64.b64encode(image_data).decode("utf-8")
        except Exception as e:
            logger.error(f"Image to base64 error: {e}")
            return None
    
    async def _call_vision_model(self, prompt: str, image_base64: str) -> Optional[str]:
        """LLaVA vision modelini çağır."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.vision_model,
                        "prompt": prompt,
                        "images": [image_base64],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Daha deterministik sonuçlar
                            "num_predict": 2048,
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    logger.error(f"Vision API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Vision model call error: {e}")
            return None
    
    async def extract_text_from_image(self, image_path: str) -> Dict:
        """
        Görseldan metin çıkar (OCR).
        
        Args:
            image_path: Görsel dosya yolu veya /static/ URL'i
            
        Returns:
            {
                "success": bool,
                "text": str,  # Çıkarılan metin
                "confidence": str,  # "high", "medium", "low"
                "language": str,  # Tespit edilen dil
            }
        """
        image_base64 = self._image_to_base64(image_path)
        if not image_base64:
            return {
                "success": False,
                "error": "Görsel dosyası bulunamadı veya okunamadı",
                "text": "",
            }
        
        prompt = """Bu görseldeki TÜM metni oku ve aynen yaz.

Kurallar:
1. Metni olduğu gibi, değiştirmeden yaz
2. Satır sonlarını koru
3. Başlık, paragraf yapısını koru
4. Sadece metni yaz, başka açıklama ekleme
5. Metin yoksa "METIN_YOK" yaz

Görseldeki metin:"""

        text = await self._call_vision_model(prompt, image_base64)
        
        if text is None:
            return {
                "success": False,
                "error": "Vision modeli yanıt vermedi",
                "text": "",
            }
        
        # "METIN_YOK" kontrolü
        if "METIN_YOK" in text.upper() or len(text.strip()) < 3:
            return {
                "success": True,
                "text": "",
                "message": "Görselde metin bulunamadı",
                "confidence": "high",
            }
        
        # Güven seviyesi tahmini (metin uzunluğuna göre basit heuristik)
        confidence = "high" if len(text) > 50 else "medium" if len(text) > 10 else "low"
        
        return {
            "success": True,
            "text": text.strip(),
            "confidence": confidence,
            "language": "tr",  # TODO: Dil tespiti eklenebilir
        }
    
    async def extract_latex_formula(self, image_path: str) -> Dict:
        """
        Görseldan matematiksel formül çıkar ve LaTeX formatında döndür.
        
        Args:
            image_path: Formül içeren görsel
            
        Returns:
            {
                "success": bool,
                "latex": str,  # LaTeX kodu
                "display_mode": bool,  # $$ vs $ için
                "explanation": str,  # Formülün açıklaması
            }
        """
        image_base64 = self._image_to_base64(image_path)
        if not image_base64:
            return {
                "success": False,
                "error": "Görsel dosyası bulunamadı",
                "latex": "",
            }
        
        prompt = """Bu görseldeki matematiksel formül veya denklemi LaTeX formatına çevir.

Kurallar:
1. Sadece LaTeX kodunu yaz ($ veya $$ işaretleri olmadan)
2. Formül yoksa "FORMUL_YOK" yaz
3. Karmaşık formüllerde \begin{equation} kullan
4. Türkçe karakterleri uygun LaTeX komutlarına çevir

LaTeX kodu:"""

        latex = await self._call_vision_model(prompt, image_base64)
        
        if latex is None:
            return {
                "success": False,
                "error": "Vision modeli yanıt vermedi",
                "latex": "",
            }
        
        if "FORMUL_YOK" in latex.upper():
            return {
                "success": True,
                "latex": "",
                "message": "Görselde formül bulunamadı",
            }
        
        # LaTeX kodunu temizle
        latex = latex.strip()
        # Eğer $$ veya $ ile sarılmışsa kaldır
        if latex.startswith("$$") and latex.endswith("$$"):
            latex = latex[2:-2].strip()
        elif latex.startswith("$") and latex.endswith("$"):
            latex = latex[1:-1].strip()
        
        # Display mode tespiti (çok satırlı veya büyük formül)
        display_mode = (
            "\\begin" in latex or 
            "\\frac" in latex or 
            "\\sum" in latex or
            "\\int" in latex or
            len(latex) > 50
        )
        
        return {
            "success": True,
            "latex": latex,
            "display_mode": display_mode,
            "formatted": f"$${latex}$$" if display_mode else f"${latex}$",
        }
    
    async def generate_image_description(
        self, 
        image_path: str, 
        language: str = "tr",
        detail_level: str = "medium"
    ) -> Dict:
        """
        Görsel için AI açıklama oluştur.
        
        Args:
            image_path: Görsel dosya yolu
            language: Açıklama dili ("tr" veya "en")
            detail_level: "brief", "medium", "detailed"
            
        Returns:
            {
                "success": bool,
                "description": str,
                "tags": List[str],  # Önerilen etiketler
                "alt_text": str,  # Erişilebilirlik için kısa açıklama
            }
        """
        image_base64 = self._image_to_base64(image_path)
        if not image_base64:
            return {
                "success": False,
                "error": "Görsel dosyası bulunamadı",
                "description": "",
            }
        
        detail_instructions = {
            "brief": "1-2 cümle ile kısa",
            "medium": "3-5 cümle ile orta detaylı",
            "detailed": "Detaylı paragraf şeklinde, tüm öğeleri açıkla",
        }
        
        lang_instruction = "Türkçe yaz." if language == "tr" else "Write in English."
        
        prompt = f"""Bu görseli {detail_instructions.get(detail_level, 'orta detaylı')} açıkla.
{lang_instruction}

Şu formatta yanıt ver:
AÇIKLAMA: [görsel açıklaması]
ETİKETLER: [virgülle ayrılmış 3-5 etiket]
ALT_METİN: [erişilebilirlik için 1 cümlelik kısa açıklama]"""

        result = await self._call_vision_model(prompt, image_base64)
        
        if result is None:
            return {
                "success": False,
                "error": "Vision modeli yanıt vermedi",
                "description": "",
            }
        
        # Yanıtı parse et
        description = ""
        tags = []
        alt_text = ""
        
        lines = result.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("AÇIKLAMA:") or line.startswith("DESCRIPTION:"):
                description = line.split(":", 1)[1].strip()
            elif line.startswith("ETİKETLER:") or line.startswith("TAGS:"):
                tags_str = line.split(":", 1)[1].strip()
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            elif line.startswith("ALT_METİN:") or line.startswith("ALT_TEXT:"):
                alt_text = line.split(":", 1)[1].strip()
        
        # Eğer parse edilemezse ham sonucu kullan
        if not description:
            description = result.strip()
        
        return {
            "success": True,
            "description": description,
            "tags": tags[:5],  # Maksimum 5 etiket
            "alt_text": alt_text or description[:100],
            "language": language,
        }
    
    async def analyze_diagram(self, image_path: str) -> Dict:
        """
        Diyagram/şema analizi yap.
        Akış diyagramları, organizasyon şemaları vb. için.
        """
        image_base64 = self._image_to_base64(image_path)
        if not image_base64:
            return {
                "success": False,
                "error": "Görsel dosyası bulunamadı",
            }
        
        prompt = """Bu diyagram veya şemayı analiz et.

Şu formatta yanıt ver:
TİP: [akış diyagramı / organizasyon şeması / zihin haritası / UML / diğer]
ÖĞELER: [ana öğeleri listele]
İLİŞKİLER: [öğeler arası ilişkileri açıkla]
ÖZET: [diyagramın ne anlattığını 2-3 cümle ile özetle]"""

        result = await self._call_vision_model(prompt, image_base64)
        
        if result is None:
            return {
                "success": False,
                "error": "Vision modeli yanıt vermedi",
            }
        
        return {
            "success": True,
            "analysis": result.strip(),
        }


# Singleton instance
_notes_vision_instance = None


def get_notes_vision() -> NotesVision:
    """NotesVision singleton instance döndür."""
    global _notes_vision_instance
    if _notes_vision_instance is None:
        _notes_vision_instance = NotesVision()
    return _notes_vision_instance
