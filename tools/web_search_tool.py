"""
Web Search Tool
===============

Web arama aracı - DuckDuckGo API kullanır.
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlencode

import httpx

from .base_tool import BaseTool


class WebSearchTool(BaseTool):
    """
    DuckDuckGo tabanlı web arama aracı
    
    Özellikler:
    - Anında cevaplar (Instant Answers)
    - Web araması
    - Haber araması
    - Sonuç filtreleme
    """
    
    name = "web_search"
    description = "Web'de arama yapar ve sonuçları döndürür. Güncel bilgiler için kullanın."
    
    # DuckDuckGo endpoints
    INSTANT_ANSWER_API = "https://api.duckduckgo.com/"
    HTML_SEARCH_URL = "https://html.duckduckgo.com/html/"
    
    def __init__(
        self,
        max_results: int = 5,
        timeout: float = 10.0,
        region: str = "tr-tr",
        safe_search: str = "moderate"
    ):
        super().__init__()
        self.max_results = max_results
        self.timeout = timeout
        self.region = region
        self.safe_search = safe_search
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP client al veya oluştur"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                follow_redirects=True
            )
        return self._client
    
    async def _instant_answer(self, query: str) -> Optional[Dict[str, Any]]:
        """DuckDuckGo Instant Answer API'yi sorgula"""
        client = await self._get_client()
        
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
            "no_redirect": 1
        }
        
        try:
            response = await client.get(
                self.INSTANT_ANSWER_API,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Abstract varsa döndür
                if data.get("Abstract"):
                    return {
                        "type": "instant_answer",
                        "title": data.get("Heading", ""),
                        "abstract": data.get("Abstract", ""),
                        "source": data.get("AbstractSource", ""),
                        "url": data.get("AbstractURL", ""),
                        "image": data.get("Image", ""),
                        "related_topics": [
                            {
                                "text": t.get("Text", ""),
                                "url": t.get("FirstURL", "")
                            }
                            for t in data.get("RelatedTopics", [])[:5]
                            if isinstance(t, dict) and "Text" in t
                        ]
                    }
                
                # Infobox varsa
                if data.get("Infobox"):
                    return {
                        "type": "infobox",
                        "title": data.get("Heading", ""),
                        "content": data.get("Infobox", {}).get("content", []),
                        "url": data.get("AbstractURL", "")
                    }
        
        except Exception:
            pass
        
        return None
    
    async def _html_search(self, query: str) -> List[Dict[str, str]]:
        """HTML sayfasından arama sonuçlarını çek"""
        client = await self._get_client()
        
        data = {
            "q": query,
            "kl": self.region,
            "kp": "-1" if self.safe_search == "off" else "1"
        }
        
        results = []
        
        try:
            response = await client.post(
                self.HTML_SEARCH_URL,
                data=data
            )
            
            if response.status_code == 200:
                html = response.text
                
                # Basit regex ile sonuçları parse et
                # result__a class'ı link içerir
                link_pattern = r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
                snippet_pattern = r'class="result__snippet"[^>]*>([^<]+)</a>'
                
                links = re.findall(link_pattern, html)
                snippets = re.findall(snippet_pattern, html)
                
                for i, (url, title) in enumerate(links[:self.max_results]):
                    result = {
                        "title": title.strip(),
                        "url": url,
                        "snippet": snippets[i].strip() if i < len(snippets) else ""
                    }
                    results.append(result)
        
        except Exception:
            pass
        
        return results
    
    async def _run(
        self,
        query: str,
        search_type: str = "general",
        num_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Web araması yap
        
        Args:
            query: Arama sorgusu
            search_type: Arama tipi (general, news, instant)
            num_results: Döndürülecek sonuç sayısı
            
        Returns:
            Arama sonuçları
        """
        max_results = num_results or self.max_results
        
        try:
            results = {
                "query": query,
                "search_type": search_type,
                "timestamp": datetime.now().isoformat(),
                "instant_answer": None,
                "results": []
            }
            
            # Önce instant answer dene
            if search_type in ["general", "instant"]:
                instant = await self._instant_answer(query)
                if instant:
                    results["instant_answer"] = instant
            
            # HTML arama yap
            if search_type in ["general", "news"]:
                search_results = await self._html_search(query)
                results["results"] = search_results[:max_results]
            
            results["success"] = bool(results["instant_answer"] or results["results"])
            results["total_results"] = len(results["results"])
            
            return results
        
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e)
            }
    
    async def close(self):
        """HTTP client'ı kapat"""
        if self._client:
            await self._client.aclose()
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Arama sorgusu"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["general", "news", "instant"],
                        "default": "general",
                        "description": "Arama tipi"
                    },
                    "num_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Döndürülecek sonuç sayısı"
                    }
                },
                "required": ["query"]
            }
        }


# Tool instance
web_search_tool = WebSearchTool()
