"""
Enterprise AI Assistant - Web Search Tool
İnternet araması aracı

DuckDuckGo ile ücretsiz web araması.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
import asyncio
from urllib.parse import quote_plus

from tools.base_tool import BaseTool, ToolResult


@dataclass
class SearchResult:
    """Arama sonucu."""
    title: str
    url: str
    snippet: str
    source: str = "web"


class WebSearchTool(BaseTool):
    """Web arama aracı - DuckDuckGo kullanır."""
    
    name: str = "web_search"
    description: str = "İnternette arama yapar ve sonuçları döndürür"
    
    def __init__(self, max_results: int = 5, timeout: int = 10):
        """
        Web search tool başlat.
        
        Args:
            max_results: Maksimum sonuç sayısı
            timeout: HTTP timeout (saniye)
        """
        self.max_results = max_results
        self.timeout = timeout
        self._client = None
    
    def get_schema(self) -> Dict[str, Any]:
        """Tool schema döndür."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Arama sorgusu",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maksimum sonuç sayısı",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }
    
    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP client al veya oluştur."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self._client
    
    async def search_duckduckgo(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        DuckDuckGo ile arama yap.
        
        Args:
            query: Arama sorgusu
            max_results: Maksimum sonuç
            
        Returns:
            Arama sonuçları listesi
        """
        try:
            # DuckDuckGo HTML arama
            encoded_query = quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            
            # Basit HTML parsing
            html = response.text
            results = []
            
            # Result class'ları bul
            import re
            
            # Title ve URL pattern
            pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            matches = re.findall(pattern, html)
            
            # Snippet pattern
            snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>([^<]*)</a>'
            snippets = re.findall(snippet_pattern, html)
            
            for i, (url_match, title) in enumerate(matches[:max_results]):
                snippet = snippets[i] if i < len(snippets) else ""
                
                # URL'yi temizle (DuckDuckGo redirect'i)
                if "uddg=" in url_match:
                    actual_url = url_match.split("uddg=")[-1].split("&")[0]
                    from urllib.parse import unquote
                    actual_url = unquote(actual_url)
                else:
                    actual_url = url_match
                
                results.append(SearchResult(
                    title=title.strip(),
                    url=actual_url,
                    snippet=snippet.strip(),
                    source="duckduckgo"
                ))
            
            return results
            
        except Exception as e:
            # Fallback: basit sonuç döndür
            return [SearchResult(
                title=f"Arama hatası: {query}",
                url="",
                snippet=f"Arama yapılamadı: {str(e)}",
                source="error"
            )]
    
    async def execute_async(self, query: str, max_results: int = None) -> ToolResult:
        """
        Asenkron arama yap.
        
        Args:
            query: Arama sorgusu
            max_results: Maksimum sonuç
            
        Returns:
            ToolResult
        """
        max_results = max_results or self.max_results
        
        try:
            results = await self.search_duckduckgo(query, max_results)
            
            if not results:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Sonuç bulunamadı",
                )
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": [
                        {
                            "title": r.title,
                            "url": r.url,
                            "snippet": r.snippet,
                            "source": r.source,
                        }
                        for r in results
                    ],
                    "count": len(results),
                },
                error=None,
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )
    
    def execute(self, query: str, max_results: int = None) -> ToolResult:
        """
        Senkron arama yap.
        
        Args:
            query: Arama sorgusu
            max_results: Maksimum sonuç
            
        Returns:
            ToolResult
        """
        return asyncio.run(self.execute_async(query, max_results))
    
    def format_results(self, results: List[SearchResult]) -> str:
        """
        Sonuçları okunabilir formata çevir.
        
        Args:
            results: Arama sonuçları
            
        Returns:
            Formatlanmış string
        """
        if not results:
            return "Sonuç bulunamadı."
        
        output = []
        for i, result in enumerate(results, 1):
            output.append(f"{i}. **{result.title}**")
            output.append(f"   URL: {result.url}")
            output.append(f"   {result.snippet}")
            output.append("")
        
        return "\n".join(output)
    
    async def close(self) -> None:
        """HTTP client'ı kapat."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
web_search_tool = WebSearchTool()
