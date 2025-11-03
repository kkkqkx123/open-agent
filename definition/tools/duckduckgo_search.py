"""
DuckDuckGo搜索工具实现

提供使用DuckDuckGo搜索引擎进行网络搜索和获取网页内容的功能。
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import urllib.parse
import asyncio
from datetime import datetime, timedelta
import time
import re


@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    link: str
    snippet: str
    position: int


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def acquire(self):
        """获取请求许可，如果超过速率限制则等待"""
        now = datetime.now()
        # 移除超过1分钟的请求记录
        self.requests = [
            req for req in self.requests if now - req < timedelta(minutes=1)
        ]

        if len(self.requests) >= self.requests_per_minute:
            # 等待直到可以发出另一个请求
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.requests.append(now)


class DuckDuckGoSearcher:
    """DuckDuckGo搜索引擎"""
    
    BASE_URL = "https://html.duckduckgo.com/html"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self):
        self.rate_limiter = RateLimiter()

    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        """格式化搜索结果，便于LLM处理"""
        if not results:
            return "No results were found for your search query. This could be due to DuckDuckGo's bot detection or the query returned no matches. Please try rephrasing your search or try again in a few minutes."

        output = []
        output.append(f"Found {len(results)} search results:\n")

        for result in results:
            output.append(f"{result.position}. {result.title}")
            output.append(f"   URL: {result.link}")
            output.append(f"   Summary: {result.snippet}")
            output.append("")  # Empty line between results

        return "\n".join(output)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """执行DuckDuckGo搜索"""
        try:
            # 应用速率限制
            await self.rate_limiter.acquire()

            # 创建POST请求的表单数据
            data = {
                "q": query,
                "b": "",
                "kl": "",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL, data=data, headers=self.HEADERS, timeout=30.0
                )
                response.raise_for_status()

            # 解析HTML响应
            soup = BeautifulSoup(response.text, "html.parser")
            if not soup:
                return []

            results = []
            for result in soup.select(".result"):
                title_elem = result.select_one(".result__title")
                if not title_elem:
                    continue

                link_elem = title_elem.find("a")
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                link = link_elem.get("href", "")

                # 确保 link 是字符串
                if not isinstance(link, str):
                    link = str(link) if link else ""

                # 跳过广告结果
                if link and "y.js" in link:
                    continue

                # 清理DuckDuckGo重定向URL
                if link and link.startswith("//duckduckgo.com/l/?uddg="):
                    link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                results.append(
                    SearchResult(
                        title=title,
                        link=link,
                        snippet=snippet,
                        position=len(results) + 1,
                    )
                )

                if len(results) >= max_results:
                    break

            return results

        except httpx.TimeoutException:
            return []
        except httpx.HTTPError:
            return []
        except Exception:
            return []


class WebContentFetcher:
    """网页内容获取器"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=20)

    async def fetch_and_parse(self, url: str) -> str:
        """获取并解析网页内容"""
        try:
            await self.rate_limiter.acquire()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True,
                    timeout=30.0,
                )
                response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # 移除脚本和样式元素
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # 获取文本内容
            text = soup.get_text()

            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # 移除多余的空白字符
            text = re.sub(r"\s+", " ", text).strip()

            # 如果太长则截断
            if len(text) > 8000:
                text = text[:8000] + "... [content truncated]"

            return text

        except httpx.TimeoutException:
            return "Error: The request timed out while trying to fetch the webpage."
        except httpx.HTTPError as e:
            return f"Error: Could not access the webpage ({str(e)})"
        except Exception as e:
            return f"Error: An unexpected error occurred while fetching the webpage ({str(e)})"


# 全局实例
searcher = DuckDuckGoSearcher()
fetcher = WebContentFetcher()


def duckduckgo_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    """使用DuckDuckGo进行搜索
    
    Args:
        query: 搜索查询字符串
        max_results: 返回的最大结果数 (默认: 10)
        
    Returns:
        Dict[str, Any]: 包含搜索结果的字典
        
    Raises:
        ValueError: 当参数错误时抛出
    """
    # 验证输入参数
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if max_results < 1 or max_results > 50:
        raise ValueError("Max results must be between 1 and 50")
    
    try:
        # 运行异步搜索
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(searcher.search(query, max_results))
        loop.close()
        
        # 格式化结果
        formatted_results = searcher.format_results_for_llm(results)
        
        return {
            "query": query,
            "results_count": len(results),
            "formatted_results": formatted_results,
            "raw_results": [
                {
                    "title": result.title,
                    "link": result.link,
                    "snippet": result.snippet,
                    "position": result.position
                }
                for result in results
            ]
        }
    except Exception as e:
        raise ValueError(f"Search failed: {str(e)}")


def fetch_web_content(url: str) -> Dict[str, Any]:
    """获取网页内容
    
    Args:
        url: 要获取内容的网页URL
        
    Returns:
        Dict[str, Any]: 包含网页内容的字典
        
    Raises:
        ValueError: 当参数错误时抛出
    """
    # 验证输入参数
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    # 简单的URL格式验证
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("URL must start with http:// or https://")
    
    try:
        # 运行异步获取
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        content = loop.run_until_complete(fetcher.fetch_and_parse(url))
        loop.close()
        
        return {
            "url": url,
            "content": content,
            "content_length": len(content),
            "truncated": len(content) >= 8000
        }
    except Exception as e:
        raise ValueError(f"Failed to fetch web content: {str(e)}")


# 示例用法
if __name__ == "__main__":
    # 测试搜索功能
    test_query = "Python programming"
    
    print("Testing DuckDuckGo search tool:")
    print(f"Query: {test_query}")
    
    try:
        search_result = duckduckgo_search(test_query, max_results=5)
        print(f"Results count: {search_result['results_count']}")
        print("\nFormatted results:")
        print(search_result['formatted_results'])
    except ValueError as e:
        print(f"Error: {e}")
    
    # 测试网页内容获取功能
    test_url = "https://www.python.org"
    
    print("\n\nTesting web content fetch:")
    print(f"URL: {test_url}")
    
    try:
        content_result = fetch_web_content(test_url)
        print(f"Content length: {content_result['content_length']}")
        print(f"Truncated: {content_result['truncated']}")
        print("\nContent preview:")
        print(content_result['content'][:500] + "..." if len(content_result['content']) > 500 else content_result['content'])
    except ValueError as e:
        print(f"Error: {e}")