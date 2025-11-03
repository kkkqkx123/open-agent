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
from random import randint


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
        self.requests = []  # 存储请求时间戳
        self._lock = asyncio.Lock()  # 用于线程安全

    async def acquire(self):
        """获取请求许可，如果超过速率限制则等待"""
        async with self._lock:
            now = datetime.now()
            # 移除超过1分钟的请求记录
            self.requests = [
                req for req in self.requests if now - req < timedelta(minutes=1)
            ]

            if len(self.requests) >= self.requests_per_minute:
                # 计算需要等待的时间
                oldest_request = self.requests[0]
                wait_time = 60 - (now - oldest_request).total_seconds()
                if wait_time > 0:
                    # 等待直到可以发出另一个请求
                    await asyncio.sleep(wait_time)
                    # 重新获取当前时间并清理过期请求
                    now = datetime.now()
                    self.requests = [
                        req for req in self.requests if now - req < timedelta(minutes=1)
                    ]

            # 记录当前请求
            self.requests.append(now)
            
    def get_current_rate(self) -> int:
        """获取当前一分钟内的请求数"""
        now = datetime.now()
        recent_requests = [
            req for req in self.requests if now - req < timedelta(minutes=1)
        ]
        return len(recent_requests)
        
    def reset(self):
        """重置速率限制器"""
        self.requests = []


# 从fetch.py导入浏览器头部管理功能
from .fetch import get_browser_headers

class DuckDuckGoSearcher:
    """DuckDuckGo搜索引擎"""
    
    BASE_URL = "https://html.duckduckgo.com/html"
    
    # 默认超时设置
    DEFAULT_TIMEOUT = 30.0
    # 最大重试次数
    MAX_RETRIES = 3
    # 重试延迟（秒）
    RETRY_DELAY = 1.0

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
        # 获取浏览器请求头
        headers = get_browser_headers(randomize=True)
        
        # 应用速率限制
        await self.rate_limiter.acquire()

        # 创建POST请求的表单数据
        data = {
            "q": query,
            "b": "",
            "kl": "",
        }

        # 实现重试机制
        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.BASE_URL, data=data, headers=headers, timeout=self.DEFAULT_TIMEOUT
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
                if attempt < self.MAX_RETRIES - 1:  # 不是最后一次尝试
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))  # 指数退避
                    continue
                return []
            except httpx.HTTPStatusError as e:
                # 对于特定的HTTP状态码，我们可能想要立即返回而不是重试
                if e.response.status_code in [403, 404, 429]:
                    return []  # 直接返回空结果
                if attempt < self.MAX_RETRIES - 1:  # 不是最后一次尝试
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))  # 指数退避
                    continue
                return []
            except httpx.HTTPError:
                if attempt < self.MAX_RETRIES - 1:  # 不是最后一次尝试
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))  # 指数退避
                    continue
                return []
            except Exception:
                if attempt < self.MAX_RETRIES - 1:  # 不是最后一次尝试
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))  # 指数退避
                    continue
                return []

        return []  # 所有重试都失败了


class WebContentFetcher:
    """网页内容获取器"""
    
    # 默认超时设置
    DEFAULT_TIMEOUT = 30.0
    # 最大重试次数
    MAX_RETRIES = 3
    # 重试延迟（秒）
    RETRY_DELAY = 1.0
    
    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=20)

    async def fetch_and_parse(self, url: str) -> str:
        """获取并解析网页内容"""
        # 获取浏览器请求头
        headers = get_browser_headers(randomize=True)
        
        # 应用速率限制
        await self.rate_limiter.acquire()

        # 实现重试机制
        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url,
                        headers=headers,
                        follow_redirects=True,
                        timeout=self.DEFAULT_TIMEOUT,
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
                if attempt < self.MAX_RETRIES - 1:  # 不是最后一次尝试
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))  # 指数退避
                    continue
                return "Error: The request timed out while trying to fetch the webpage."
            except httpx.HTTPStatusError as e:
                # 对于特定的HTTP状态码，我们可能想要立即返回而不是重试
                if e.response.status_code in [403, 404, 429]:
                    return f"Error: Could not access the webpage (Status code: {e.response.status_code})"
                if attempt < self.MAX_RETRIES - 1:  # 不是最后一次尝试
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))  # 指数退避
                    continue
                return f"Error: Could not access the webpage (Status code: {e.response.status_code})"
            except httpx.HTTPError as e:
                if attempt < self.MAX_RETRIES - 1:  # 不是最后一次尝试
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))  # 指数退避
                    continue
                return f"Error: Could not access the webpage ({str(e)})"
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:  # 不是最后一次尝试
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))  # 指数退避
                    continue
                return f"Error: An unexpected error occurred while fetching the webpage ({str(e)})"

        return "Error: Failed to fetch the webpage after multiple attempts."


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
        print(f"\nRate limiter info: {searcher.rate_limiter.get_current_rate()} requests in the last minute")
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
        print(f"\nRate limiter info: {fetcher.rate_limiter.get_current_rate()} requests in the last minute")
    except ValueError as e:
        print(f"Error: {e}")
        
    # 测试速率限制功能
    print("\n\nTesting rate limiting:")
    print("Making 3 rapid requests to demonstrate rate limiting...")
    start_time = time.time()
    for i in range(3):
        try:
            result = duckduckgo_search(f"test query {i}", max_results=1)
            print(f"Request {i+1} completed")
        except ValueError as e:
            print(f"Error in request {i+1}: {e}")
    end_time = time.time()
    print(f"Time taken for 3 requests: {end_time - start_time:.2f} seconds")
    print(f"Current rate: {searcher.rate_limiter.get_current_rate()} requests in the last minute")