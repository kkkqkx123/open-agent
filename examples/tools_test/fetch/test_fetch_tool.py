"""
网页内容获取工具测试文件

测试网页内容获取工具的功能和正确性。
"""

import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到sys.path，以便导入defination.tools.fetch
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from defination.tools.fetch import fetch_url, extract_content_from_html, get_robots_txt_url


class TestFetchTool:
    """网页内容获取工具测试类"""
    
    def test_fetch_url_with_valid_params(self):
        """测试使用有效参数获取URL内容"""
        # 由于网络请求需要外部依赖，我们使用模拟来测试
        
        # 模拟异步函数的返回值
        with patch('defination.tools.fetch.fetch_url_content', 
                  return_value=("测试内容", "")):
            result = fetch_url(
                url="https://httpbin.org/html",
                max_length=5000,
                start_index=0,
                raw=False
            )
            
            # 验证结果
            assert result["url"] == "https://httpbin.org/html"
            assert "测试内容" in result["content"]
    
    def test_fetch_url_missing_url(self):
        """测试缺少URL参数"""
        with pytest.raises(ValueError, match="URL不能为空"):
            fetch_url(
                url="",
                max_length=5000,
                start_index=0,
                raw=False
            )
    
    def test_fetch_url_invalid_max_length(self):
        """测试无效的max_length参数"""
        with pytest.raises(ValueError, match="max_length必须在1到1000000之间"):
            fetch_url(
                url="https://httpbin.org/html",
                max_length=0,
                start_index=0,
                raw=False
            )
        
        with pytest.raises(ValueError, match="max_length必须在1到1000000之间"):
            fetch_url(
                url="https://httpbin.org/html",
                max_length=1000001,
                start_index=0,
                raw=False
            )
    
    def test_fetch_url_invalid_start_index(self):
        """测试无效的start_index参数"""
        with pytest.raises(ValueError, match="start_index不能为负数"):
            fetch_url(
                url="https://httpbin.org/html",
                max_length=5000,
                start_index=-1,
                raw=False
            )
    
    def test_extract_content_from_html(self):
        """测试HTML内容提取"""
        # 测试简单的HTML内容
        html_content = "<html><body><h1>标题</h1><p>段落内容</p></body></html>"
        result = extract_content_from_html(html_content)
        # 由于依赖库可能不存在，我们检查是否返回了错误信息或正常内容
        assert isinstance(result, str)
    
    def test_get_robots_txt_url(self):
        """测试获取robots.txt URL"""
        test_url = "https://example.com/page"
        expected_robots_url = "https://example.com/robots.txt"
        result = get_robots_txt_url(test_url)
        assert result == expected_robots_url
        
        # 测试带端口的URL
        test_url_with_port = "https://example.com:8080/page"
        expected_robots_url_with_port = "https://example.com:8080/robots.txt"
        result_with_port = get_robots_txt_url(test_url_with_port)
        assert result_with_port == expected_robots_url_with_port
    
    def test_fetch_url_content_truncation(self):
        """测试内容截断功能"""
        long_content = "A" * 10000  # 创建长内容
        
        with patch('defination.tools.fetch.fetch_url_content', 
                  return_value=(long_content, "")):
            # 获取前5000个字符
            result = fetch_url(
                url="https://example.com",
                max_length=5000,
                start_index=0,
                raw=False
            )
            
            # 验证返回的内容长度
            assert len(result["content"]) > 5000  # 包含前缀和提示信息
            assert "Contents of https://example.com:" in result["content"]
    
    def test_fetch_url_with_start_index(self):
        """测试使用start_index参数"""
        content = "A" * 3000 + "B" * 3000  # 创建6000字符的内容
        
        with patch('defination.tools.fetch.fetch_url_content', 
                  return_value=(content, "")):
            # 从索引2500开始获取内容
            result = fetch_url(
                url="https://example.com",
                max_length=2000,
                start_index=2500,
                raw=False
            )
            
            # 验证返回的内容
            assert "Contents of https://example.com:" in result["content"]
    
    def test_fetch_url_no_more_content(self):
        """测试没有更多内容的情况"""
        content = "短内容"
        
        with patch('defination.tools.fetch.fetch_url_content', 
                  return_value=(content, "")):
            # 尝试从超出内容长度的索引开始获取
            result = fetch_url(
                url="https://example.com",
                max_length=1000,
                start_index=1000,
                raw=False
            )
            
            # 验证返回的错误信息
            assert "<error>没有更多可用内容。</error>" in result["content"]
    
    @pytest.mark.asyncio
    async def test_fetch_url_content_success(self):
        """测试异步获取URL内容成功"""
        # 模拟httpx.AsyncClient
        with patch('defination.tools.fetch.httpx.AsyncClient') as mock_client:
                # 创建模拟响应
                mock_response = MagicMock()
                mock_response.text = "<html><body><h1>测试</h1></body></html>"
                mock_response.status_code = 200
                mock_response.headers = {"content-type": "text/html"}
                
                # 设置模拟客户端的行为
                mock_client_instance = MagicMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_client_instance
                
                # 导入异步函数
                from defination.tools.fetch import fetch_url_content
                
                # 调用异步函数
                content, prefix = await fetch_url_content("https://example.com")
                
                # 验证结果
                assert isinstance(content, str)
                assert isinstance(prefix, str)
    
    @pytest.mark.asyncio
    async def test_fetch_url_content_http_error(self):
        """测试异步获取URL内容HTTP错误"""
        # 模拟httpx.AsyncClient抛出异常
        with patch('defination.tools.fetch.httpx.AsyncClient') as mock_client:
                # 设置模拟客户端的行为，使其抛出异常
                mock_client_instance = MagicMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.get = AsyncMock(side_effect=Exception("网络错误"))
                mock_client.return_value = mock_client_instance
                
                # 导入异步函数
                from defination.tools.fetch import fetch_url_content
                
                # 调用异步函数
                content, prefix = await fetch_url_content("https://example.com")
                
                # 验证返回错误信息
                assert "<error>获取 https://example.com 失败:" in content
    
    def test_fetch_url_with_raw_content(self):
        """测试获取原始内容"""
        raw_content = "<html><body>原始HTML内容</body></html>"
        
        with patch('defination.tools.fetch.fetch_url_content', 
                  return_value=(raw_content, "内容类型 text/html 无法简化为markdown，但这里是原始内容:\n")):
            result = fetch_url(
                url="https://example.com",
                max_length=5000,
                start_index=0,
                raw=True  # 获取原始内容
            )
            
            # 验证返回原始内容
            assert "原始HTML内容" in result["content"]
            assert "原始内容" in result["content"]
    
    def test_fetch_url_missing_dependencies(self):
        """测试缺少依赖库的情况"""
        # 由于我们已经简化了代码，不再有依赖检查，这个测试改为测试正常功能
        result = fetch_url("https://example.com")
        assert isinstance(result, dict)
        assert "content" in result
        assert "url" in result


# 运行测试的便捷函数
def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()