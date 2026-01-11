"""
Enterprise AI Assistant - Utility Functions
Yardımcı fonksiyonlar

Endüstri standardı utility implementasyonu.
"""

import re
import hashlib
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """
    Dosya adını güvenli hale getir.
    
    Args:
        filename: Orijinal dosya adı
        
    Returns:
        Güvenli dosya adı
    """
    # Normalize unicode
    filename = unicodedata.normalize("NFKD", filename)
    # Remove non-ASCII characters
    filename = filename.encode("ASCII", "ignore").decode()
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    # Remove unsafe characters
    filename = re.sub(r"[^\w\-_\.]", "", filename)
    # Limit length
    name, ext = Path(filename).stem[:100], Path(filename).suffix
    return f"{name}{ext}"


def generate_hash(content: str, length: int = 8) -> str:
    """
    İçerik için hash üret.
    
    Args:
        content: Hash'lenecek içerik
        length: Hash uzunluğu
        
    Returns:
        Hash string
    """
    return hashlib.md5(content.encode()).hexdigest()[:length]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Metni kısalt.
    
    Args:
        text: Orijinal metin
        max_length: Maksimum uzunluk
        suffix: Kısaltma soneki
        
    Returns:
        Kısaltılmış metin
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_bytes(size: int) -> str:
    """
    Byte'ı okunabilir formata çevir.
    
    Args:
        size: Byte cinsinden boyut
        
    Returns:
        Formatlanmış string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Süreyi okunabilir formata çevir.
    
    Args:
        seconds: Saniye cinsinden süre
        
    Returns:
        Formatlanmış string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def clean_text(text: str) -> str:
    """
    Metni temizle.
    
    Args:
        text: Orijinal metin
        
    Returns:
        Temizlenmiş metin
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)
    return text


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Metinden anahtar kelimeler çıkar (basit implementasyon).
    
    Args:
        text: Kaynak metin
        max_keywords: Maksimum anahtar kelime sayısı
        
    Returns:
        Anahtar kelime listesi
    """
    # Simple word frequency based extraction
    words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}\b', text.lower())
    
    # Stop words (Turkish + English basic)
    stop_words = {
        "ve", "veya", "ile", "için", "bir", "bu", "şu", "de", "da",
        "the", "and", "or", "for", "with", "this", "that", "is", "are",
        "olan", "olarak", "gibi", "kadar", "daha", "ancak", "fakat",
        "çünkü", "ama", "hem", "ya", "ki", "mi", "mı", "mu", "mü",
    }
    
    # Filter stop words
    words = [w for w in words if w not in stop_words]
    
    # Count frequencies
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, _ in sorted_words[:max_keywords]]


def split_into_sentences(text: str) -> List[str]:
    """
    Metni cümlelere ayır.
    
    Args:
        text: Kaynak metin
        
    Returns:
        Cümle listesi
    """
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    İki dict'i birleştir (deep merge).
    
    Args:
        dict1: İlk dict
        dict2: İkinci dict
        
    Returns:
        Birleştirilmiş dict
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def safe_get(data: Union[Dict, List], *keys: Any, default: Any = None) -> Any:
    """
    Güvenli nested veri erişimi.
    
    Args:
        data: Kaynak veri
        *keys: Erişim anahtarları
        default: Varsayılan değer
        
    Returns:
        Değer veya varsayılan
    """
    result = data
    for key in keys:
        try:
            if isinstance(result, dict):
                result = result.get(key, default)
            elif isinstance(result, (list, tuple)) and isinstance(key, int):
                result = result[key] if 0 <= key < len(result) else default
            else:
                return default
        except (KeyError, IndexError, TypeError):
            return default
    return result


def timestamp_now() -> str:
    """ISO format zaman damgası."""
    return datetime.now().isoformat()


def parse_bool(value: Any) -> bool:
    """
    Değeri bool'a çevir.
    
    Args:
        value: Kaynak değer
        
    Returns:
        Bool değer
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on", "evet", "doğru")
    return bool(value)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Listeyi parçalara ayır.
    
    Args:
        lst: Kaynak liste
        chunk_size: Parça boyutu
        
    Returns:
        Parçalara ayrılmış liste
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List, key: callable = None) -> List:
    """
    Listeden tekrarları kaldır (sırayı koru).
    
    Args:
        lst: Kaynak liste
        key: Karşılaştırma fonksiyonu
        
    Returns:
        Tekrarsız liste
    """
    seen = set()
    result = []
    for item in lst:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result
