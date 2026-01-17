"""
🔍 Web Search Plugin
====================

Web arama yetenekleri ekleyen plugin.
"""

import logging
from typing import Any, Dict, List, Optional
from plugins.base import PluginBase, PluginResult, PluginPriority

logger = logging.getLogger(__name__)


class WebSearchPlugin(PluginBase):
    """
    Web arama plugin'i.
    
    DuckDuckGo veya diğer arama motorlarını kullanarak
    web araması yapar.
    """
    
    name = "web_search"
    version = "1.0.0"
    description = "Web arama yetenekleri ekler"
    author = "Enterprise AI Team"
    
    def __init__(self):
        super().__init__()
        self.search_engine = None
        self.max_results = 5
    
    async def setup(self) -> bool:
        """Search engine'i başlat"""
        try:
            from tools.web_search_engine import get_search_engine
            self.search_engine = get_search_engine()
            self.max_results = self.get_config("max_results", 5)
            
            await super().setup()
            logger.info(f"WebSearchPlugin initialized with max_results={self.max_results}")
            return True
            
        except ImportError as e:
            logger.error(f"Web search engine not available: {e}")
            return False
    
    async def execute(self, input_data: Dict[str, Any]) -> PluginResult:
        """
        Web araması yap.
        
        Args:
            input_data: {
                "query": str,  # Arama sorgusu
                "num_results": int,  # Sonuç sayısı (opsiyonel)
                "search_type": str,  # general, news, academic (opsiyonel)
            }
        """
        query = input_data.get("query")
        if not query:
            return PluginResult(
                success=False,
                error="Query is required"
            )
        
        num_results = input_data.get("num_results", self.max_results)
        search_type = input_data.get("search_type", "general")
        
        try:
            if self.search_engine:
                results = await self.search_engine.search(
                    query=query,
                    num_results=num_results,
                    search_type=search_type
                )
                
                return PluginResult(
                    success=True,
                    data={
                        "query": query,
                        "results": results,
                        "count": len(results),
                    }
                )
            else:
                return PluginResult(
                    success=False,
                    error="Search engine not initialized"
                )
                
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return PluginResult(
                success=False,
                error=str(e)
            )
