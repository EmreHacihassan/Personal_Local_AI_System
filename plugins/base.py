"""
🔌 Plugin Base System
====================

Enterprise-grade plugin framework.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
from functools import wraps

logger = logging.getLogger(__name__)


# ============ ENUMS & TYPES ============

class PluginStatus(str, Enum):
    """Plugin durumları"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class PluginPriority(int, Enum):
    """Plugin öncelik seviyeleri"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 100


# ============ DATA CLASSES ============

@dataclass
class PluginMetadata:
    """Plugin metadata bilgileri"""
    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    priority: PluginPriority = PluginPriority.NORMAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "priority": self.priority.value,
        }


@dataclass
class PluginResult:
    """Plugin çalıştırma sonucu"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============ BASE PLUGIN CLASS ============

class PluginBase(ABC):
    """
    Tüm plugin'lerin base class'ı.
    
    Her plugin bu sınıftan türetilmeli ve gerekli metodları implement etmelidir.
    
    Örnek:
        class MyPlugin(PluginBase):
            name = "my_plugin"
            version = "1.0.0"
            description = "My awesome plugin"
            
            async def execute(self, input_data: Dict) -> PluginResult:
                result = self._process(input_data)
                return PluginResult(success=True, data=result)
    """
    
    # Override edilmesi gereken class attributes
    name: str = "base_plugin"
    version: str = "0.0.0"
    description: str = "Base plugin"
    author: str = ""
    
    def __init__(self):
        self.status: PluginStatus = PluginStatus.INACTIVE
        self.last_execution: Optional[datetime] = None
        self.execution_count: int = 0
        self.error_count: int = 0
        self._config: Dict[str, Any] = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata'sını döndür"""
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
        )
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Plugin'i yapılandır"""
        self._config.update(config)
        logger.info(f"Plugin {self.name} configured with: {list(config.keys())}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Config değeri al"""
        return self._config.get(key, default)
    
    async def setup(self) -> bool:
        """
        Plugin başlatma.
        
        Plugin aktif edilmeden önce çağrılır.
        Gerekli kaynakları başlatmak için override edin.
        
        Returns:
            bool: Başarılı mı
        """
        self.status = PluginStatus.ACTIVE
        logger.info(f"Plugin {self.name} v{self.version} activated")
        return True
    
    async def teardown(self) -> bool:
        """
        Plugin kapatma.
        
        Plugin deaktif edilirken çağrılır.
        Kaynakları temizlemek için override edin.
        
        Returns:
            bool: Başarılı mı
        """
        self.status = PluginStatus.INACTIVE
        logger.info(f"Plugin {self.name} deactivated")
        return True
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> PluginResult:
        """
        Plugin'in ana çalışma metodu.
        
        Args:
            input_data: Giriş verisi
            
        Returns:
            PluginResult: Çalışma sonucu
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> PluginResult:
        """
        Plugin'i çalıştır (wrapper with timing and error handling).
        """
        import time
        start_time = time.time()
        
        try:
            if self.status != PluginStatus.ACTIVE:
                return PluginResult(
                    success=False,
                    error=f"Plugin {self.name} is not active"
                )
            
            result = await self.execute(input_data)
            
            self.last_execution = datetime.now()
            self.execution_count += 1
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Plugin {self.name} error: {e}")
            return PluginResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Plugin istatistikleri"""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "error_rate": self.error_count / max(self.execution_count, 1),
        }


# ============ PLUGIN REGISTRY ============

class PluginRegistry:
    """
    Plugin kayıt ve yönetim sistemi.
    
    Singleton pattern ile tek bir global registry sağlar.
    """
    
    _instance: Optional['PluginRegistry'] = None
    _plugins: Dict[str, PluginBase] = {}
    _hooks: Dict[str, List[Callable]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, plugin: PluginBase) -> bool:
        """
        Plugin kaydet.
        
        Args:
            plugin: Kaydedilecek plugin instance
            
        Returns:
            bool: Başarılı mı
        """
        if plugin.name in cls._plugins:
            logger.warning(f"Plugin {plugin.name} already registered, replacing")
        
        cls._plugins[plugin.name] = plugin
        logger.info(f"Plugin registered: {plugin.name} v{plugin.version}")
        return True
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """Plugin kaydını sil"""
        if name in cls._plugins:
            del cls._plugins[name]
            logger.info(f"Plugin unregistered: {name}")
            return True
        return False
    
    @classmethod
    def get(cls, name: str) -> Optional[PluginBase]:
        """Plugin al"""
        return cls._plugins.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, PluginBase]:
        """Tüm plugin'leri al"""
        return cls._plugins.copy()
    
    @classmethod
    def list_plugins(cls) -> List[PluginMetadata]:
        """Plugin listesi"""
        return [p.metadata for p in cls._plugins.values()]
    
    @classmethod
    async def activate(cls, name: str) -> bool:
        """Plugin'i aktif et"""
        plugin = cls.get(name)
        if plugin:
            return await plugin.setup()
        return False
    
    @classmethod
    async def deactivate(cls, name: str) -> bool:
        """Plugin'i deaktif et"""
        plugin = cls.get(name)
        if plugin:
            return await plugin.teardown()
        return False
    
    @classmethod
    async def activate_all(cls) -> Dict[str, bool]:
        """Tüm plugin'leri aktif et"""
        results = {}
        for name, plugin in cls._plugins.items():
            results[name] = await plugin.setup()
        return results
    
    @classmethod
    async def execute(cls, name: str, input_data: Dict[str, Any]) -> Optional[PluginResult]:
        """Belirli bir plugin'i çalıştır"""
        plugin = cls.get(name)
        if plugin:
            return await plugin.run(input_data)
        return None
    
    @classmethod
    async def execute_all(
        cls, 
        input_data: Dict[str, Any],
        filter_tags: Optional[List[str]] = None
    ) -> Dict[str, PluginResult]:
        """
        Tüm aktif plugin'leri çalıştır.
        
        Args:
            input_data: Giriş verisi
            filter_tags: Sadece bu tag'lere sahip plugin'leri çalıştır
            
        Returns:
            Dict[str, PluginResult]: Plugin sonuçları
        """
        results = {}
        
        for name, plugin in cls._plugins.items():
            if plugin.status != PluginStatus.ACTIVE:
                continue
            
            # Tag filtresi
            if filter_tags:
                plugin_tags = plugin.metadata.tags
                if not any(t in plugin_tags for t in filter_tags):
                    continue
            
            results[name] = await plugin.run(input_data)
        
        return results
    
    @classmethod
    def register_hook(cls, event: str, callback: Callable) -> None:
        """Event hook kaydet"""
        if event not in cls._hooks:
            cls._hooks[event] = []
        cls._hooks[event].append(callback)
    
    @classmethod
    async def trigger_hook(cls, event: str, *args, **kwargs) -> List[Any]:
        """Event hook'larını tetikle"""
        results = []
        for callback in cls._hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook {event} error: {e}")
        return results
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Registry istatistikleri"""
        active_count = sum(1 for p in cls._plugins.values() if p.status == PluginStatus.ACTIVE)
        
        return {
            "total_plugins": len(cls._plugins),
            "active_plugins": active_count,
            "registered_hooks": {k: len(v) for k, v in cls._hooks.items()},
            "plugins": [p.get_stats() for p in cls._plugins.values()],
        }


# ============ PLUGIN DECORATORS ============

def plugin_hook(event: str):
    """
    Decorator: Fonksiyonu hook olarak kaydet.
    
    Örnek:
        @plugin_hook("before_chat")
        async def my_hook(message):
            return modified_message
    """
    def decorator(fn):
        PluginRegistry.register_hook(event, fn)
        return fn
    return decorator


def requires_plugin(plugin_name: str):
    """
    Decorator: Belirli bir plugin'in aktif olmasını gerektirir.
    
    Örnek:
        @requires_plugin("web_search")
        async def search_web(query):
            ...
    """
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            plugin = PluginRegistry.get(plugin_name)
            if not plugin or plugin.status != PluginStatus.ACTIVE:
                raise RuntimeError(f"Required plugin '{plugin_name}' is not active")
            return await fn(*args, **kwargs)
        return wrapper
    return decorator


# ============ HOT RELOAD SYSTEM ============

import importlib
import importlib.util
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PluginReloader(FileSystemEventHandler):
    """Plugin hot-reload için dosya izleyici."""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.observer = None
        self._reload_callbacks: List[Callable] = []
    
    def on_modified(self, event):
        """Dosya değişikliği algılandı."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix != ".py":
            return
        
        if file_path.name.startswith("_"):
            return  # __init__.py vb. atla
        
        logger.info(f"Plugin file changed: {file_path.name}")
        asyncio.create_task(self._reload_plugin(file_path))
    
    async def _reload_plugin(self, file_path: Path):
        """Plugin'i yeniden yükle."""
        try:
            module_name = f"plugins.{file_path.stem}"
            
            # Mevcut plugin'i kaldır
            old_plugin_name = None
            for name, plugin in list(PluginRegistry._plugins.items()):
                if hasattr(plugin, '__module__') and plugin.__module__ == module_name:
                    await plugin.teardown()
                    PluginRegistry.unregister(name)
                    old_plugin_name = name
                    break
            
            # Modülü yeniden yükle
            if module_name in importlib.sys.modules:
                module = importlib.reload(importlib.sys.modules[module_name])
            else:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                importlib.sys.modules[module_name] = module
                spec.loader.exec_module(module)
            
            # Yeni plugin'i kaydet ve aktif et
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginBase) and 
                    attr is not PluginBase):
                    new_plugin = attr()
                    PluginRegistry.register(new_plugin)
                    await new_plugin.setup()
                    logger.info(f"Plugin reloaded: {new_plugin.name}")
                    break
            
            # Callback'leri çağır
            for callback in self._reload_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(old_plugin_name)
                    else:
                        callback(old_plugin_name)
                except Exception as e:
                    logger.error(f"Reload callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Plugin reload error: {e}")
    
    def start(self):
        """Hot-reload izlemeyi başlat."""
        if self.observer is not None:
            return
        
        self.observer = Observer()
        self.observer.schedule(self, str(self.plugins_dir), recursive=False)
        self.observer.start()
        logger.info(f"Plugin hot-reload started: {self.plugins_dir}")
    
    def stop(self):
        """Hot-reload izlemeyi durdur."""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Plugin hot-reload stopped")
    
    def on_reload(self, callback: Callable):
        """Reload event callback ekle."""
        self._reload_callbacks.append(callback)


# ============ PLUGIN WHITELIST ============

class PluginWhitelist:
    """
    Plugin whitelist yönetimi.
    
    Sadece izin verilen plugin'lerin yüklenmesini sağlar.
    """
    
    _whitelist: set = set()
    _enabled: bool = False
    
    @classmethod
    def enable(cls, plugins: Optional[List[str]] = None):
        """Whitelist'i etkinleştir."""
        cls._enabled = True
        if plugins:
            cls._whitelist = set(plugins)
        logger.info(f"Plugin whitelist enabled: {cls._whitelist or 'all blocked'}")
    
    @classmethod
    def disable(cls):
        """Whitelist'i devre dışı bırak."""
        cls._enabled = False
        cls._whitelist.clear()
        logger.info("Plugin whitelist disabled")
    
    @classmethod
    def add(cls, plugin_name: str):
        """Plugin'i whitelist'e ekle."""
        cls._whitelist.add(plugin_name)
    
    @classmethod
    def remove(cls, plugin_name: str):
        """Plugin'i whitelist'ten çıkar."""
        cls._whitelist.discard(plugin_name)
    
    @classmethod
    def is_allowed(cls, plugin_name: str) -> bool:
        """Plugin'e izin var mı?"""
        if not cls._enabled:
            return True
        return plugin_name in cls._whitelist
    
    @classmethod
    def get_whitelist(cls) -> List[str]:
        """Mevcut whitelist'i döndür."""
        return list(cls._whitelist)


# ============ SECURE PLUGIN REGISTRATION ============

_original_register = PluginRegistry.register

@classmethod
def _secure_register(cls, plugin: PluginBase) -> bool:
    """Whitelist kontrolü ile plugin kaydet."""
    if not PluginWhitelist.is_allowed(plugin.name):
        logger.warning(f"Plugin '{plugin.name}' blocked by whitelist")
        return False
    return _original_register.__func__(cls, plugin)

# Override register metodu
PluginRegistry.register = _secure_register


# ============ GLOBAL RELOADER INSTANCE ============

plugin_reloader = PluginReloader()
