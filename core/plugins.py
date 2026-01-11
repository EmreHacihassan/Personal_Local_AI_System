"""
Plugin System
=============

Endüstri standartlarında genişletilebilir plugin sistemi.
Modüler özellik ekleme ve 3rd party entegrasyonlar için.

Features:
- Dynamic plugin loading
- Plugin lifecycle management
- Hook system for extensibility
- Configuration per plugin
- Dependency resolution
- Hot reload support
"""

import importlib
import importlib.util
import inspect
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type
import json
import yaml

from .logger import get_logger

logger = get_logger("plugins")


class PluginStatus(Enum):
    """Plugin durumları"""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class HookPriority(Enum):
    """Hook öncelikleri"""
    FIRST = 0
    EARLY = 25
    NORMAL = 50
    LATE = 75
    LAST = 100


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str = ""
    author: str = ""
    website: str = ""
    dependencies: List[str] = field(default_factory=list)
    min_app_version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    config_schema: Dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PluginMetadata":
        return cls(
            name=data.get("name", "unknown"),
            version=data.get("version", "0.0.1"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            website=data.get("website", ""),
            dependencies=data.get("dependencies", []),
            min_app_version=data.get("min_app_version", "1.0.0"),
            tags=data.get("tags", []),
            config_schema=data.get("config_schema", {})
        )
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "website": self.website,
            "dependencies": self.dependencies,
            "min_app_version": self.min_app_version,
            "tags": self.tags,
            "config_schema": self.config_schema
        }


@dataclass
class HookRegistration:
    """Hook kaydı"""
    hook_name: str
    callback: Callable
    priority: HookPriority = HookPriority.NORMAL
    plugin_name: Optional[str] = None


class PluginInterface(ABC):
    """
    Plugin base class
    
    Tüm pluginler bu sınıftan türetilmelidir.
    """
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata'sını döndür"""
        pass
    
    def on_load(self, config: Dict[str, Any]) -> None:
        """Plugin yüklendiğinde çağrılır"""
        pass
    
    def on_activate(self) -> None:
        """Plugin aktifleştirildiğinde çağrılır"""
        pass
    
    def on_deactivate(self) -> None:
        """Plugin deaktif edildiğinde çağrılır"""
        pass
    
    def on_unload(self) -> None:
        """Plugin kaldırıldığında çağrılır"""
        pass
    
    def register_hooks(self, hook_manager: "HookManager") -> None:
        """Plugin hook'larını kaydet"""
        pass
    
    def get_tools(self) -> List[Dict]:
        """Plugin tarafından sağlanan araçları döndür (MCP formatında)"""
        return []
    
    def get_agents(self) -> List[Any]:
        """Plugin tarafından sağlanan ajanları döndür"""
        return []
    
    def get_api_routes(self) -> List[Any]:
        """Plugin tarafından sağlanan API route'larını döndür"""
        return []


class HookManager:
    """
    Hook yönetim sistemi
    
    Plugin'lerin uygulama akışına müdahale etmesini sağlar.
    """
    
    def __init__(self):
        self._hooks: Dict[str, List[HookRegistration]] = {}
    
    def register(
        self,
        hook_name: str,
        callback: Callable,
        priority: HookPriority = HookPriority.NORMAL,
        plugin_name: Optional[str] = None
    ):
        """Hook callback'i kaydet"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        
        registration = HookRegistration(
            hook_name=hook_name,
            callback=callback,
            priority=priority,
            plugin_name=plugin_name
        )
        
        self._hooks[hook_name].append(registration)
        
        # Sort by priority
        self._hooks[hook_name].sort(key=lambda h: h.priority.value)
        
        logger.debug(f"Hook registered: {hook_name} (priority: {priority.name})")
    
    def unregister(self, hook_name: str, plugin_name: str):
        """Plugin'in hook'larını kaldır"""
        if hook_name in self._hooks:
            self._hooks[hook_name] = [
                h for h in self._hooks[hook_name]
                if h.plugin_name != plugin_name
            ]
    
    def unregister_all(self, plugin_name: str):
        """Plugin'in tüm hook'larını kaldır"""
        for hook_name in self._hooks:
            self.unregister(hook_name, plugin_name)
    
    async def trigger(
        self,
        hook_name: str,
        *args,
        stop_on_result: bool = False,
        **kwargs
    ) -> List[Any]:
        """
        Hook'u tetikle
        
        Args:
            hook_name: Hook adı
            stop_on_result: İlk non-None sonuçta dur
            
        Returns:
            Callback sonuçları listesi
        """
        results = []
        
        if hook_name not in self._hooks:
            return results
        
        for registration in self._hooks[hook_name]:
            try:
                callback = registration.callback
                
                if inspect.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                
                results.append(result)
                
                if stop_on_result and result is not None:
                    break
            
            except Exception as e:
                logger.error(
                    f"Hook error in {hook_name} "
                    f"(plugin: {registration.plugin_name}): {e}"
                )
        
        return results
    
    def trigger_sync(
        self,
        hook_name: str,
        *args,
        stop_on_result: bool = False,
        **kwargs
    ) -> List[Any]:
        """Senkron hook tetikleme"""
        results = []
        
        if hook_name not in self._hooks:
            return results
        
        for registration in self._hooks[hook_name]:
            try:
                callback = registration.callback
                
                if inspect.iscoroutinefunction(callback):
                    logger.warning(f"Async callback skipped in sync trigger: {hook_name}")
                    continue
                
                result = callback(*args, **kwargs)
                results.append(result)
                
                if stop_on_result and result is not None:
                    break
            
            except Exception as e:
                logger.error(f"Hook error in {hook_name}: {e}")
        
        return results
    
    def get_hooks(self) -> Dict[str, int]:
        """Kayıtlı hook'ları listele"""
        return {name: len(hooks) for name, hooks in self._hooks.items()}


@dataclass
class LoadedPlugin:
    """Yüklenmiş plugin bilgisi"""
    instance: PluginInterface
    module: Any
    path: Path
    status: PluginStatus = PluginStatus.LOADED
    config: Dict = field(default_factory=dict)
    loaded_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


class PluginManager:
    """
    Plugin yönetim sistemi
    
    Features:
    - Plugin discovery
    - Dynamic loading/unloading
    - Configuration management
    - Dependency resolution
    - Hot reload
    """
    
    # Bilinen hook isimleri
    HOOKS = {
        # Chat hooks
        "pre_chat": "Chat mesajı işlenmeden önce",
        "post_chat": "Chat mesajı işlendikten sonra",
        "on_stream_token": "Streaming token alındığında",
        
        # RAG hooks
        "pre_retrieve": "RAG retrieval öncesi",
        "post_retrieve": "RAG retrieval sonrası",
        "pre_index": "Döküman indexleme öncesi",
        "post_index": "Döküman indexleme sonrası",
        
        # Agent hooks
        "pre_agent_call": "Agent çağrısı öncesi",
        "post_agent_call": "Agent çağrısı sonrası",
        "on_tool_use": "Tool kullanıldığında",
        
        # System hooks
        "on_startup": "Uygulama başlangıcında",
        "on_shutdown": "Uygulama kapanışında",
        "on_error": "Hata oluştuğunda",
        
        # Session hooks
        "on_session_start": "Session başlangıcında",
        "on_session_end": "Session bitişinde"
    }
    
    def __init__(
        self,
        plugins_dir: Optional[Path] = None,
        config_file: Optional[Path] = None
    ):
        self.plugins_dir = plugins_dir or Path("plugins")
        self.config_file = config_file or Path("configs/plugins.yaml")
        
        self._plugins: Dict[str, LoadedPlugin] = {}
        self._hook_manager = HookManager()
        self._config: Dict[str, Dict] = {}
        
        # Create plugins directory if not exists
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Plugin konfigürasyonunu yükle"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                if self.config_file.suffix == '.yaml':
                    self._config = yaml.safe_load(f) or {}
                else:
                    self._config = json.load(f)
        
        logger.debug(f"Plugin config loaded: {len(self._config)} entries")
    
    def _save_config(self):
        """Plugin konfigürasyonunu kaydet"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            if self.config_file.suffix == '.yaml':
                yaml.dump(self._config, f, default_flow_style=False)
            else:
                json.dump(self._config, f, indent=2)
    
    @property
    def hook_manager(self) -> HookManager:
        """Hook manager'a erişim"""
        return self._hook_manager
    
    def discover_plugins(self) -> List[Path]:
        """Plugin dizinindeki plugin'leri keşfet"""
        plugins = []
        
        if not self.plugins_dir.exists():
            return plugins
        
        # Look for plugin directories with __init__.py
        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                init_file = item / "__init__.py"
                plugin_file = item / "plugin.py"
                
                if init_file.exists() or plugin_file.exists():
                    plugins.append(item)
            
            # Single file plugins
            elif item.suffix == '.py' and not item.name.startswith('_'):
                plugins.append(item)
        
        logger.info(f"Discovered {len(plugins)} plugins")
        
        return plugins
    
    def _load_plugin_module(self, path: Path) -> Any:
        """Plugin modülünü yükle"""
        if path.is_dir():
            # Package plugin
            plugin_file = path / "plugin.py"
            if plugin_file.exists():
                module_path = plugin_file
            else:
                module_path = path / "__init__.py"
        else:
            module_path = path
        
        module_name = f"plugins.{path.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin: {path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return module
    
    def _find_plugin_class(self, module: Any) -> Optional[Type[PluginInterface]]:
        """Modülde plugin sınıfını bul"""
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj) and
                issubclass(obj, PluginInterface) and
                obj is not PluginInterface
            ):
                return obj
        
        return None
    
    def load_plugin(self, path: Path) -> Optional[LoadedPlugin]:
        """Plugin'i yükle"""
        try:
            # Load module
            module = self._load_plugin_module(path)
            
            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            
            if plugin_class is None:
                raise ValueError(f"No PluginInterface subclass found in {path}")
            
            # Create instance
            instance = plugin_class()
            metadata = instance.metadata
            
            # Check dependencies
            for dep in metadata.dependencies:
                if dep not in self._plugins:
                    logger.warning(f"Plugin {metadata.name} depends on {dep} which is not loaded")
            
            # Get config
            config = self._config.get(metadata.name, {})
            
            # Call on_load
            instance.on_load(config)
            
            # Register hooks
            instance.register_hooks(self._hook_manager)
            
            # Create loaded plugin
            loaded = LoadedPlugin(
                instance=instance,
                module=module,
                path=path,
                status=PluginStatus.LOADED,
                config=config
            )
            
            self._plugins[metadata.name] = loaded
            
            logger.info(f"Plugin loaded: {metadata.name} v{metadata.version}")
            
            return loaded
        
        except Exception as e:
            logger.error(f"Failed to load plugin {path}: {e}")
            
            # Create error entry
            loaded = LoadedPlugin(
                instance=None,  # type: ignore
                module=None,
                path=path,
                status=PluginStatus.ERROR,
                error=str(e)
            )
            
            return loaded
    
    def unload_plugin(self, name: str) -> bool:
        """Plugin'i kaldır"""
        if name not in self._plugins:
            return False
        
        loaded = self._plugins[name]
        
        try:
            # Call on_deactivate if active
            if loaded.status == PluginStatus.ACTIVE:
                loaded.instance.on_deactivate()
            
            # Call on_unload
            loaded.instance.on_unload()
            
            # Unregister hooks
            self._hook_manager.unregister_all(name)
            
            # Remove from plugins
            del self._plugins[name]
            
            # Remove module from sys.modules
            module_name = f"plugins.{loaded.path.stem}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            logger.info(f"Plugin unloaded: {name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to unload plugin {name}: {e}")
            return False
    
    def activate_plugin(self, name: str) -> bool:
        """Plugin'i aktifleştir"""
        if name not in self._plugins:
            return False
        
        loaded = self._plugins[name]
        
        if loaded.status != PluginStatus.LOADED:
            return False
        
        try:
            loaded.instance.on_activate()
            loaded.status = PluginStatus.ACTIVE
            
            logger.info(f"Plugin activated: {name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to activate plugin {name}: {e}")
            loaded.status = PluginStatus.ERROR
            loaded.error = str(e)
            return False
    
    def deactivate_plugin(self, name: str) -> bool:
        """Plugin'i deaktif et"""
        if name not in self._plugins:
            return False
        
        loaded = self._plugins[name]
        
        if loaded.status != PluginStatus.ACTIVE:
            return False
        
        try:
            loaded.instance.on_deactivate()
            loaded.status = PluginStatus.LOADED
            
            logger.info(f"Plugin deactivated: {name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to deactivate plugin {name}: {e}")
            return False
    
    def reload_plugin(self, name: str) -> bool:
        """Plugin'i yeniden yükle (hot reload)"""
        if name not in self._plugins:
            return False
        
        loaded = self._plugins[name]
        path = loaded.path
        was_active = loaded.status == PluginStatus.ACTIVE
        
        # Unload
        self.unload_plugin(name)
        
        # Reload
        new_loaded = self.load_plugin(path)
        
        if new_loaded and new_loaded.status == PluginStatus.LOADED:
            # Reactivate if was active
            if was_active:
                self.activate_plugin(name)
            
            return True
        
        return False
    
    def load_all(self) -> Dict[str, bool]:
        """Tüm keşfedilen plugin'leri yükle"""
        results = {}
        
        for path in self.discover_plugins():
            loaded = self.load_plugin(path)
            
            if loaded:
                name = loaded.instance.metadata.name if loaded.instance else path.stem
                results[name] = loaded.status == PluginStatus.LOADED
        
        return results
    
    def activate_all(self) -> Dict[str, bool]:
        """Tüm yüklü plugin'leri aktifleştir"""
        results = {}
        
        for name in list(self._plugins.keys()):
            results[name] = self.activate_plugin(name)
        
        return results
    
    def get_plugin(self, name: str) -> Optional[LoadedPlugin]:
        """Plugin bilgisini al"""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, LoadedPlugin]:
        """Tüm plugin'leri al"""
        return self._plugins.copy()
    
    def get_active_plugins(self) -> List[str]:
        """Aktif plugin isimlerini al"""
        return [
            name for name, loaded in self._plugins.items()
            if loaded.status == PluginStatus.ACTIVE
        ]
    
    def get_all_tools(self) -> List[Dict]:
        """Tüm aktif plugin'lerin araçlarını topla"""
        tools = []
        
        for name in self.get_active_plugins():
            loaded = self._plugins[name]
            plugin_tools = loaded.instance.get_tools()
            
            for tool in plugin_tools:
                tool["_plugin"] = name
            
            tools.extend(plugin_tools)
        
        return tools
    
    def get_all_agents(self) -> List[Any]:
        """Tüm aktif plugin'lerin ajanlarını topla"""
        agents = []
        
        for name in self.get_active_plugins():
            loaded = self._plugins[name]
            agents.extend(loaded.instance.get_agents())
        
        return agents
    
    def get_all_api_routes(self) -> List[Any]:
        """Tüm aktif plugin'lerin API route'larını topla"""
        routes = []
        
        for name in self.get_active_plugins():
            loaded = self._plugins[name]
            routes.extend(loaded.instance.get_api_routes())
        
        return routes
    
    def update_plugin_config(self, name: str, config: Dict) -> bool:
        """Plugin konfigürasyonunu güncelle"""
        self._config[name] = config
        self._save_config()
        
        if name in self._plugins:
            self._plugins[name].config = config
            # Optionally reload plugin
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Plugin istatistiklerini al"""
        return {
            "total": len(self._plugins),
            "active": len(self.get_active_plugins()),
            "by_status": {
                status.value: sum(
                    1 for p in self._plugins.values()
                    if p.status == status
                )
                for status in PluginStatus
            },
            "available_hooks": len(self.HOOKS),
            "registered_hooks": self._hook_manager.get_hooks()
        }


# Global plugin manager instance
plugin_manager = PluginManager()


# ========================
# Example Plugin Template
# ========================

class ExamplePlugin(PluginInterface):
    """Örnek plugin şablonu"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example-plugin",
            version="1.0.0",
            description="Örnek plugin",
            author="Developer",
            tags=["example"]
        )
    
    def on_load(self, config: Dict[str, Any]) -> None:
        logger.info("Example plugin loaded")
    
    def on_activate(self) -> None:
        logger.info("Example plugin activated")
    
    def register_hooks(self, hook_manager: HookManager) -> None:
        hook_manager.register(
            "pre_chat",
            self._on_pre_chat,
            priority=HookPriority.NORMAL,
            plugin_name=self.metadata.name
        )
    
    def _on_pre_chat(self, message: str) -> Optional[str]:
        """Pre-chat hook - mesajı modifiye edebilir"""
        return None  # None = değişiklik yok
    
    def get_tools(self) -> List[Dict]:
        return [
            {
                "name": "example_tool",
                "description": "Örnek araç",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"}
                    }
                }
            }
        ]


__all__ = [
    "PluginInterface",
    "PluginMetadata",
    "PluginManager",
    "PluginStatus",
    "HookManager",
    "HookPriority",
    "LoadedPlugin",
    "plugin_manager",
    "ExamplePlugin"
]
