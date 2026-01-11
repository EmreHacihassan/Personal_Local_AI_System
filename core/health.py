"""
Enterprise AI Assistant - Health Check Module
Sistem sağlık kontrolü

Tüm bileşenlerin durumunu izler.
"""

import asyncio
import time
import psutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import httpx


class HealthStatus(str, Enum):
    """Sağlık durumu."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Bileşen sağlık bilgisi."""
    name: str
    status: HealthStatus
    message: str
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = None
    checked_at: datetime = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.now()
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
        }


class HealthChecker:
    """Sistem sağlık kontrolcüsü."""
    
    def __init__(self):
        """Health checker başlat."""
        self._last_check: Dict[str, ComponentHealth] = {}
        self._startup_time = datetime.now()
    
    async def check_ollama(self) -> ComponentHealth:
        """Ollama servisini kontrol et."""
        from core.config import settings
        
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                latency = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    
                    # Check if required models are available
                    has_primary = any(
                        settings.OLLAMA_PRIMARY_MODEL.split(":")[0] in m
                        for m in models
                    )
                    has_embed = any("nomic" in m or "embed" in m for m in models)
                    
                    if has_primary and has_embed:
                        status = HealthStatus.HEALTHY
                        message = "Ollama çalışıyor, tüm modeller mevcut"
                    elif has_primary:
                        status = HealthStatus.DEGRADED
                        message = "Embedding modeli eksik"
                    else:
                        status = HealthStatus.DEGRADED
                        message = f"Ana model ({settings.OLLAMA_PRIMARY_MODEL}) eksik"
                    
                    return ComponentHealth(
                        name="ollama",
                        status=status,
                        message=message,
                        latency_ms=latency,
                        details={"models": models, "model_count": len(models)},
                    )
                else:
                    return ComponentHealth(
                        name="ollama",
                        status=HealthStatus.UNHEALTHY,
                        message=f"HTTP {response.status_code}",
                        latency_ms=latency,
                    )
        except Exception as e:
            return ComponentHealth(
                name="ollama",
                status=HealthStatus.UNHEALTHY,
                message=f"Bağlantı hatası: {str(e)}",
            )
    
    async def check_chromadb(self) -> ComponentHealth:
        """ChromaDB'yi kontrol et."""
        from core.config import settings
        
        start = time.time()
        try:
            import chromadb
            
            client = chromadb.PersistentClient(
                path=str(settings.CHROMA_DB_PATH)
            )
            collections = client.list_collections()
            latency = (time.time() - start) * 1000
            
            return ComponentHealth(
                name="chromadb",
                status=HealthStatus.HEALTHY,
                message="ChromaDB çalışıyor",
                latency_ms=latency,
                details={
                    "collections": len(collections),
                    "path": str(settings.CHROMA_DB_PATH),
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="chromadb",
                status=HealthStatus.UNHEALTHY,
                message=f"Hata: {str(e)}",
            )
    
    def check_disk_space(self) -> ComponentHealth:
        """Disk alanını kontrol et."""
        from core.config import settings
        
        try:
            disk = psutil.disk_usage(str(settings.DATA_DIR))
            free_gb = disk.free / (1024 ** 3)
            total_gb = disk.total / (1024 ** 3)
            used_percent = disk.percent
            
            if free_gb < 1:
                status = HealthStatus.UNHEALTHY
                message = f"Kritik: {free_gb:.1f} GB boş alan"
            elif free_gb < 5:
                status = HealthStatus.DEGRADED
                message = f"Düşük: {free_gb:.1f} GB boş alan"
            else:
                status = HealthStatus.HEALTHY
                message = f"{free_gb:.1f} GB boş alan"
            
            return ComponentHealth(
                name="disk",
                status=status,
                message=message,
                details={
                    "free_gb": round(free_gb, 2),
                    "total_gb": round(total_gb, 2),
                    "used_percent": used_percent,
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthStatus.UNKNOWN,
                message=f"Kontrol edilemedi: {str(e)}",
            )
    
    def check_memory(self) -> ComponentHealth:
        """Bellek kullanımını kontrol et."""
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)
            total_gb = memory.total / (1024 ** 3)
            used_percent = memory.percent
            
            if used_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Kritik: %{used_percent:.1f} kullanımda"
            elif used_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Yüksek: %{used_percent:.1f} kullanımda"
            else:
                status = HealthStatus.HEALTHY
                message = f"%{used_percent:.1f} kullanımda"
            
            return ComponentHealth(
                name="memory",
                status=status,
                message=message,
                details={
                    "available_gb": round(available_gb, 2),
                    "total_gb": round(total_gb, 2),
                    "used_percent": used_percent,
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Kontrol edilemedi: {str(e)}",
            )
    
    def check_cpu(self) -> ComponentHealth:
        """CPU kullanımını kontrol et."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count()
            
            if cpu_percent > 90:
                status = HealthStatus.DEGRADED
                message = f"Yüksek: %{cpu_percent:.1f}"
            else:
                status = HealthStatus.HEALTHY
                message = f"%{cpu_percent:.1f} kullanımda"
            
            return ComponentHealth(
                name="cpu",
                status=status,
                message=message,
                details={
                    "percent": cpu_percent,
                    "cores": cpu_count,
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="cpu",
                status=HealthStatus.UNKNOWN,
                message=f"Kontrol edilemedi: {str(e)}",
            )
    
    def check_data_directories(self) -> ComponentHealth:
        """Veri dizinlerini kontrol et."""
        from core.config import settings
        
        dirs_to_check = [
            settings.DATA_DIR,
            settings.DATA_DIR / "sessions",
            settings.DATA_DIR / "uploads",
            settings.DATA_DIR / "cache",
            settings.CHROMA_DB_PATH,
        ]
        
        missing = []
        for d in dirs_to_check:
            if not d.exists():
                missing.append(str(d.name))
        
        if missing:
            return ComponentHealth(
                name="directories",
                status=HealthStatus.DEGRADED,
                message=f"Eksik dizinler: {', '.join(missing)}",
                details={"missing": missing},
            )
        
        return ComponentHealth(
            name="directories",
            status=HealthStatus.HEALTHY,
            message="Tüm dizinler mevcut",
            details={"checked": len(dirs_to_check)},
        )
    
    async def check_all(self) -> Dict[str, Any]:
        """
        Tüm bileşenleri kontrol et.
        
        Returns:
            Sağlık raporu
        """
        # Sync checks
        disk = self.check_disk_space()
        memory = self.check_memory()
        cpu = self.check_cpu()
        directories = self.check_data_directories()
        
        # Async checks
        ollama = await self.check_ollama()
        chromadb = await self.check_chromadb()
        
        components = [disk, memory, cpu, directories, ollama, chromadb]
        
        # Cache results
        for comp in components:
            self._last_check[comp.name] = comp
        
        # Determine overall status
        statuses = [c.status for c in components]
        
        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        uptime = (datetime.now() - self._startup_time).total_seconds()
        
        return {
            "status": overall.value,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": int(uptime),
            "components": {c.name: c.to_dict() for c in components},
        }
    
    def get_quick_status(self) -> Dict[str, str]:
        """
        Son kontrol sonuçlarından hızlı durum al.
        
        Returns:
            Hızlı durum özeti
        """
        return {
            name: health.status.value
            for name, health in self._last_check.items()
        }


# Singleton instance
health_checker = HealthChecker()


async def get_health_report() -> Dict[str, Any]:
    """Sağlık raporu al."""
    return await health_checker.check_all()
