"""
🔌 Plugin System - Enterprise AI Assistant
==========================================

Plugin sistemi ile AI asistanın yeteneklerini genişletme.

Her plugin aşağıdaki yapıyı takip etmelidir:
- PluginBase sınıfından türetilmeli
- name, version, description property'leri tanımlanmalı
- execute() metodu implement edilmeli
- Opsiyonel: setup(), teardown() metodları

Örnek kullanım:
    from plugins.base import PluginBase, PluginRegistry
    
    class MyPlugin(PluginBase):
        name = "my_plugin"
        version = "1.0.0"
        
        async def execute(self, input_data):
            return {"result": "processed"}
    
    # Plugin'i kaydet
    PluginRegistry.register(MyPlugin())
"""

from plugins.base import PluginBase, PluginRegistry, PluginMetadata

__all__ = [
    "PluginBase",
    "PluginRegistry", 
    "PluginMetadata",
]
