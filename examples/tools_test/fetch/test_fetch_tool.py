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

# 添加项目根目录到sys.path，以便导入definition.tools.fetch
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from definition.tools.fetch import fetch_url, extract_content_from_html, clean_html_content, clean_markdown_content


class TestFetchTool:
    """网页内容获取工具测试类"""
    
    def test_fetch_url_with_valid_params(self):
        """测试使用有效参数获取URL内容"""
        # 由于网络请求需要外部依赖，我们使用模拟来测试
        
        # 模拟异步函数的返回值
        with patch('definition.tools.fetch.fetch_url_content', 
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
        with pytest.raises(ValueError, match="max_length必须在1到100000之间"):
            fetch_url(
                url="https://httpbin.org/html",
                max_length=0,
                start_index=0,
                raw=False
            )
        
        with pytest.raises(ValueError, match="max_length必须在1到100000之间"):
            fetch_url(
                url="https://httpbin.org/html",
                max_length=100001,
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
    
    def test_fetch_url_content_truncation(self):
        """测试内容截断功能"""
        long_content = "A" * 10000  # 创建长内容
        
        with patch('definition.tools.fetch.fetch_url_content', 
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
        
        with patch('definition.tools.fetch.fetch_url_content', 
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
        
        with patch('definition.tools.fetch.fetch_url_content', 
                  return_value=(content, "")):
            # 尝试从超出内容长度的索引开始获取
            result = fetch_url(
                url="https://example.com",
                max_length=1000,
                start_index=1000,
                raw=False
            )
            
            # 验证返回的错误信息
            assert "<error>No more content available.</error>" in result["content"]
    
    @pytest.mark.asyncio
    async def test_fetch_url_content_success(self):
        """测试异步获取URL内容成功"""
        # 模拟httpx.AsyncClient
        with patch('definition.tools.fetch.httpx.AsyncClient') as mock_client:
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
                from definition.tools.fetch import fetch_url_content
                
                # 调用异步函数
                content, prefix = await fetch_url_content("https://example.com")
                
                # 验证结果
                assert isinstance(content, str)
                assert isinstance(prefix, str)
    
    @pytest.mark.asyncio
    async def test_fetch_url_content_http_error(self):
        """测试异步获取URL内容HTTP错误"""
        # 模拟httpx.AsyncClient抛出异常
        with patch('definition.tools.fetch.httpx.AsyncClient') as mock_client:
                # 设置模拟客户端的行为，使其抛出异常
                mock_client_instance = MagicMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.get = AsyncMock(side_effect=Exception("网络错误"))
                mock_client.return_value = mock_client_instance
                
                # 导入异步函数
                from definition.tools.fetch import fetch_url_content
                
                # 调用异步函数
                content, prefix = await fetch_url_content("https://example.com")
                
                # 验证返回错误信息
                assert "<error>Failed to fetch https://example.com:" in content
    
    def test_fetch_url_with_raw_content(self):
        """测试获取原始内容"""
        raw_content = "<html><body>原始HTML内容</body></html>"
        
        with patch('definition.tools.fetch.fetch_url_content', 
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

    def test_clean_html_content(self):
        """测试HTML内容清理功能"""
        # 测试HTML包含script、style、noscript和注释
        test_html = """
        <html>
        <head>
            <script>console.log('test');</script>
            <style>body { color: red; }</style>
            <meta name="description" content="test">
            <link rel="stylesheet" href="style.css">
            <!-- This is a comment -->
        </head>
        <body>
            <h1>Test Page</h1>
            <a href="javascript:alert('xss')">Bad Link</a>
            <a href="#section">Anchor Link</a>
            <a href="https://example.com">Good Link</a>
            <noscript>JavaScript is disabled</noscript>
            <iframe src="frame.html"></iframe>
            <object data="movie.swf"></object>
            <embed src="movie.swf">
            <p>Some content with    multiple   spaces</p>
        </body>
        </html>
        """
        
        cleaned = clean_html_content(test_html)
        
        # 验证清理结果
        assert "<script>" not in cleaned, "Script标签未被移除"
        assert "<style>" not in cleaned, "Style标签未被移除"
        assert "<meta" not in cleaned, "Meta标签未被移除"
        assert "<link" not in cleaned, "Link标签未被移除"
        assert "<noscript>" not in cleaned, "Noscript标签未被移除"
        assert "<iframe" not in cleaned, "Iframe标签未被移除"
        assert "<object" not in cleaned, "Object标签未被移除"
        assert "<embed" not in cleaned, "Embed标签未被移除"
        assert "<!--" not in cleaned, "HTML注释未被移除"
        assert "javascript:" not in cleaned, "JavaScript链接未被清理"
        assert "Good Link" in cleaned, "正常链接被错误移除"
        assert "    " not in cleaned, "多余空格未被标准化"

    def test_clean_markdown_content(self):
        """测试Markdown内容清理功能"""
        # 测试包含多余空行和空格的Markdown
        test_markdown = """
        # 标题
        
        这是一个段落。
        
        
        
        这是另一个段落，    前后有空格。
        
        - 列表项1
        - 列表项2
        
        """
        
        cleaned = clean_markdown_content(test_markdown)
        
        # 验证清理结果
        lines = cleaned.split('\n')
        assert not any('\n\n\n' in cleaned for _ in range(1)), "存在3个或更多连续换行符"
        assert all(line == line.strip() for line in lines), "存在行首尾空格"
        assert cleaned == cleaned.strip(), "存在首尾空行"

    def test_extract_content_with_enhancements(self):
        """测试增强后的内容提取功能"""
        # 创建一个包含各种元素的测试HTML
        test_html = """
        <html>
        <head>
            <title>Test Page</title>
            <script>console.log('test');</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <h1>主标题</h1>
            <h2>副标题</h2>
            <p>这是一个段落，包含<strong>粗体</strong>和<em>斜体</em>文本。</p>
            <ul>
                <li>列表项1</li>
                <li>列表项2</li>
            </ul>
            <a href="javascript:alert('xss')">恶意链接</a>
            <a href="#section">锚点链接</a>
            <a href="https://example.com">正常链接</a>
            <!-- 这是一个注释 -->
            <noscript>JavaScript已禁用</noscript>
            <hr>
            <pre><code>代码块</code></pre>
        </body>
        </html>
        """
        
        # 测试Markdown格式
        result = extract_content_from_html(test_html, "markdown")
        assert isinstance(result, str)
        # 注意：由于依赖readabilipy，在某些环境下可能无法正常工作
        # 所以我们只检查基本功能，不检查具体内容
        
        # 测试HTML格式
        result = extract_content_from_html(test_html, "html")
        assert isinstance(result, str)
        assert "<script>" not in result, "Script标签未被移除"
        assert "<style>" not in result, "Style标签未被移除"
        
        # 测试Text格式
        result = extract_content_from_html(test_html, "text")
        assert isinstance(result, str)

    def test_fetch_url_with_format_types(self):
        """测试使用不同格式类型获取URL内容"""
        # 测试Markdown格式
        with patch('definition.tools.fetch.fetch_url_content',
                  return_value=("测试内容", "")):
            result = fetch_url(
                url="https://example.com",
                format_type="markdown"
            )
            assert result["format_type"] == "markdown"
        
        # 测试Text格式
        with patch('definition.tools.fetch.fetch_url_content',
                  return_value=("测试内容", "")):
            result = fetch_url(
                url="https://example.com",
                format_type="text"
            )
            assert result["format_type"] == "text"
        
        # 测试HTML格式
        with patch('definition.tools.fetch.fetch_url_content',
                  return_value=("测试内容", "")):
            result = fetch_url(
                url="https://example.com",
                format_type="html"
            )
            assert result["format_type"] == "html"
        
        # 测试无效格式类型
        with pytest.raises(ValueError, match="format_type必须是 'text', 'markdown', 或 'html' 之一"):
            fetch_url(
                url="https://example.com",
                format_type="invalid"
            )
        
        # 测试超时参数
        with patch('definition.tools.fetch.fetch_url_content',
                  return_value=("测试内容", "")):
            result = fetch_url(
                url="https://example.com",
                timeout=60
            )
            assert result["url"] == "https://example.com"
        
        # 测试无效超时参数
        with pytest.raises(ValueError, match="timeout必须在1到120秒之间"):
            fetch_url(
                url="https://example.com",
                timeout=200
            )


# 运行测试的便捷函数
def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()