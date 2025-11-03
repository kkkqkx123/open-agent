"""
DuckDuckGo搜索工具测试文件

测试DuckDuckGo搜索工具的功能和正确性。
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, AsyncMock, MagicMock

# 添加项目根目录到sys.path，以便导入definition.tools.duckduckgo_search
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from definition.tools.duckduckgo_search import (
    duckduckgo_search, 
    fetch_web_content, 
    DuckDuckGoSearcher, 
    WebContentFetcher,
    SearchResult,
    RateLimiter
)


class TestDuckDuckGoSearchTool:
    """DuckDuckGo搜索工具测试类"""
    
    def test_duckduckgo_search_with_valid_params(self):
        """测试使用有效参数进行搜索"""
        # 模拟搜索结果
        mock_results = [
            SearchResult(
                title="Python Programming Language",
                link="https://www.python.org",
                snippet="Python is a programming language that lets you work quickly",
                position=1
            ),
            SearchResult(
                title="Python Tutorial",
                link="https://www.w3schools.com/python",
                snippet="Python is a popular programming language.",
                position=2
            )
        ]
        
        # 模拟异步搜索
        with patch('definition.tools.duckduckgo_search.DuckDuckGoSearcher.search') as mock_search:
            mock_search.return_value = mock_results
            
            result = duckduckgo_search("Python programming", max_results=5)
            
            # 验证结果
            assert result["query"] == "Python programming"
            assert result["results_count"] == 2
            assert "Python Programming Language" in result["formatted_results"]
            assert len(result["raw_results"]) == 2
            assert result["raw_results"][0]["title"] == "Python Programming Language"
    
    def test_duckduckgo_search_empty_query(self):
        """测试空查询字符串"""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            duckduckgo_search("", max_results=10)
    
    def test_duckduckgo_search_whitespace_query(self):
        """测试只包含空白字符的查询字符串"""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            duckduckgo_search("   ", max_results=10)
    
    def test_duckduckgo_search_invalid_max_results(self):
        """测试无效的最大结果数"""
        with pytest.raises(ValueError, match="Max results must be between 1 and 50"):
            duckduckgo_search("Python", max_results=0)
        
        with pytest.raises(ValueError, match="Max results must be between 1 and 50"):
            duckduckgo_search("Python", max_results=51)
    
    def test_duckduckgo_search_no_results(self):
        """测试没有搜索结果的情况"""
        # 模拟空结果
        with patch('definition.tools.duckduckgo_search.DuckDuckGoSearcher.search') as mock_search:
            mock_search.return_value = []
            
            result = duckduckgo_search("nonexistent query", max_results=10)
            
            # 验证结果
            assert result["query"] == "nonexistent query"
            assert result["results_count"] == 0
            assert "No results were found" in result["formatted_results"]
            assert len(result["raw_results"]) == 0
    
    def test_fetch_web_content_valid_url(self):
        """测试使用有效URL获取网页内容"""
        # 模拟网页内容
        mock_content = "This is a test webpage content with some text."
        
        # 模拟异步获取
        with patch('definition.tools.duckduckgo_search.WebContentFetcher.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = mock_content
            
            result = fetch_web_content("https://example.com")
            
            # 验证结果
            assert result["url"] == "https://example.com"
            assert result["content"] == mock_content
            assert result["content_length"] == len(mock_content)
            assert result["truncated"] == False
    
    def test_fetch_web_content_empty_url(self):
        """测试空URL"""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            fetch_web_content("")
    
    def test_fetch_web_content_invalid_url_format(self):
        """测试无效的URL格式"""
        with pytest.raises(ValueError, match="URL must start with http:// or https://"):
            fetch_web_content("example.com")
        
        with pytest.raises(ValueError, match="URL must start with http:// or https://"):
            fetch_web_content("ftp://example.com")
    
    def test_fetch_web_content_truncated_content(self):
        """测试内容被截断的情况"""
        # 模拟长内容（超过8000字符）
        mock_content = "a" * 8500
        
        with patch('definition.tools.duckduckgo_search.WebContentFetcher.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = mock_content
            
            result = fetch_web_content("https://example.com")
            
            # 验证结果
            assert result["url"] == "https://example.com"
            assert result["content"] == mock_content
            assert result["content_length"] == len(mock_content)
            assert result["truncated"] == True
    
    def test_search_result_dataclass(self):
        """测试SearchResult数据类"""
        result = SearchResult(
            title="Test Title",
            link="https://example.com",
            snippet="Test snippet",
            position=1
        )
        
        assert result.title == "Test Title"
        assert result.link == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.position == 1
    
    def test_rate_limiter(self):
        """测试速率限制器"""
        # 由于速率限制器涉及异步操作，我们只测试基本初始化
        rate_limiter = RateLimiter(requests_per_minute=30)
        assert rate_limiter.requests_per_minute == 30
        assert len(rate_limiter.requests) == 0
    
    @pytest.mark.asyncio
    async def test_duckduckgo_searcher_format_results(self):
        """测试搜索结果格式化"""
        searcher = DuckDuckGoSearcher()
        
        # 测试空结果
        formatted = searcher.format_results_for_llm([])
        assert "No results were found" in formatted
        
        # 测试有结果
        results = [
            SearchResult(
                title="Test Result",
                link="https://example.com",
                snippet="Test snippet",
                position=1
            )
        ]
        
        formatted = searcher.format_results_for_llm(results)
        assert "Found 1 search results" in formatted
        assert "Test Result" in formatted
        assert "https://example.com" in formatted
        assert "Test snippet" in formatted
    
    @pytest.mark.asyncio
    async def test_web_content_fetcher_error_handling(self):
        """测试网页内容获取器的错误处理"""
        fetcher = WebContentFetcher()
        
        # 测试超时错误
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            content = await fetcher.fetch_and_parse("https://example.com")
            assert "Error: The request timed out" in content
        
        # 测试HTTP错误
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.HTTPError("HTTP error")
            
            content = await fetcher.fetch_and_parse("https://example.com")
            assert "Error: Could not access the webpage" in content
        
        # 测试一般异常
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Unexpected error")
            
            content = await fetcher.fetch_and_parse("https://example.com")
            assert "Error: An unexpected error occurred" in content
    
    def test_duckduckgo_search_exception_handling(self):
        """测试搜索函数的异常处理"""
        # 模拟搜索过程中的异常
        with patch('definition.tools.duckduckgo_search.DuckDuckGoSearcher.search') as mock_search:
            mock_search.side_effect = Exception("Search error")
            
            with pytest.raises(ValueError, match="Search failed"):
                duckduckgo_search("Python", max_results=10)
    
    def test_fetch_web_content_exception_handling(self):
        """测试网页内容获取函数的异常处理"""
        # 模拟获取过程中的异常
        with patch('definition.tools.duckduckgo_search.WebContentFetcher.fetch_and_parse') as mock_fetch:
            mock_fetch.side_effect = Exception("Fetch error")
            
            with pytest.raises(ValueError, match="Failed to fetch web content"):
                fetch_web_content("https://example.com")


# 运行测试的便捷函数
def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()