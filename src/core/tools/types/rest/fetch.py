"""
网页内容获取工具实现

提供从URL获取网页内容并将其转换为多种格式的功能。
"""

import asyncio
import re
import random
from typing import Dict, Any, Tuple, Optional, List
from urllib.parse import urlparse, urlunparse

import httpx
import markdownify
import readabilipy

# 导入BeautifulSoup用于文本提取(需要移除时将BS4_AVAILABLE设置为False即可)
from bs4 import BeautifulSoup
BS4_AVAILABLE = True

# 常量定义
MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5MB
DEFAULT_TIMEOUT = 30  # 30 seconds
MAX_TIMEOUT = 120  # 2 minutes

# User-Agent 轮换列表 - 包含主流浏览器及其不同版本和操作系统
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    
    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
    
    # Chrome on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Safari on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    
    # Chrome on Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Firefox on Linux
    'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
    
    # Edge on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
]

# 基础浏览器请求头配置
BASE_BROWSER_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# 可选的请求头列表，用于随机化
OPTIONAL_HEADERS = {
    'DNT': ['1', None],  # Do Not Track
    'Sec-GPC': ['1', None],  # Global Privacy Control
    'Save-Data': ['on', None],  # Data Saver mode
    'Pragma': ['no-cache', None],  # HTTP/1.0 cache control
}

def get_browser_headers(
    custom_user_agent: Optional[str] = None,
    referer_url: Optional[str] = None,
    randomize: bool = True
) -> dict:
    """获取模拟浏览器的请求头，支持User-Agent轮换和请求头随机化
    
    Args:
        custom_user_agent: 自定义用户代理字符串，如果提供则不使用轮换
        referer_url: 可选的Referer URL
        randomize: 是否随机化可选请求头
        
    Returns:
        包含浏览器请求头的字典
    """
    # 从基础请求头开始
    headers = BASE_BROWSER_HEADERS.copy()
    
    # 设置User-Agent
    if custom_user_agent:
        headers['User-Agent'] = custom_user_agent
    else:
        # 随机选择一个User-Agent
        headers['User-Agent'] = random.choice(USER_AGENTS)
    
    # 设置Referer（如果提供）
    if referer_url:
        headers['Referer'] = referer_url
    
    # 随机化可选请求头
    if randomize:
        for header_name, values in OPTIONAL_HEADERS.items():
            # 随机决定是否包含此头部以及使用哪个值
            if random.random() < 0.5:  # 50%的概率包含此头部
                value = random.choice(values)
                if value is not None:
                    headers[header_name] = value
    
    return headers


def get_random_user_agent() -> str:
    """获取随机的User-Agent字符串
    
    Returns:
        随机选择的User-Agent字符串
    """
    return random.choice(USER_AGENTS)


def convert_http_to_https(url: str) -> str:
    """将HTTP URL转换为HTTPS URL
    
    Args:
        url: 原始URL
        
    Returns:
        HTTPS URL
    """
    parsed = urlparse(url)
    if parsed.scheme == 'http':
        # 创建HTTPS版本的URL
        https_parsed = parsed._replace(scheme='https')
        return urlunparse(https_parsed)
    return url


def is_http_url(url: str) -> bool:
    """检查URL是否为HTTP协议
    
    Args:
        url: 要检查的URL
        
    Returns:
        如果是HTTP协议返回True，否则返回False
    """
    parsed = urlparse(url)
    return parsed.scheme == 'http'


def extract_content_from_html(html: str, format_type: str = "markdown") -> str:
    """从HTML内容中提取并转换为指定格式。
    
    Args:
        html: 要处理的原始HTML内容
        format_type: 返回格式类型 ("text", "markdown", "html")
        
    Returns:
        指定格式的内容
    """
    try:
        # 首先进行HTML清理，移除不需要的元素
        cleaned_html = clean_html_content(html)
        
        if format_type == "html":
            return cleaned_html
        
        # 使用readabilipy提取主要内容
        # 通过抑制警告来避免Node.js相关的警告信息
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ret = readabilipy.simple_json_from_html_string(
                cleaned_html, use_readability=True
            )
        if not ret["content"]:
            return "<error>Page could not be simplified from HTML</error>"
        
        if format_type == "text":
            # 提取纯文本内容
            if BS4_AVAILABLE and BeautifulSoup:
                soup = BeautifulSoup(ret["content"], "html.parser")
                return soup.get_text()
            else:
                # 如果没有BeautifulSoup，使用简单的正则表达式提取文本
                import re
                # 移除script和style标签及其内容
                text = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', '', ret["content"], flags=re.IGNORECASE)
                # 移除所有HTML标签
                text = re.sub(r'<[^>]+>', '', text)
                # 清理多余的空白字符
                text = re.sub(r'\s+', ' ', text).strip()
                return text
        
        # 使用markdownify转换为Markdown，应用增强配置
        content = markdownify.markdownify(
            ret["content"],
            heading_style=markdownify.ATX,
            bullets="-",  # 使用-作为列表标记
        )
        
        # 进行Markdown后处理清理
        content = clean_markdown_content(content)
        
        return content
    except Exception as e:
        return f"<error>Error processing HTML content: {str(e)}</error>"


def clean_html_content(html: str) -> str:
    """清理HTML内容，移除不需要的元素和标签。
    
    Args:
        html: 原始HTML内容
        
    Returns:
        清理后的HTML内容
    """
    # 移除script标签及其内容
    html = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
    
    # 移除style标签及其内容
    html = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
    
    # 移除meta标签
    html = re.sub(r'<meta[^>]*>', '', html, flags=re.IGNORECASE)
    
    # 移除link标签
    html = re.sub(r'<link[^>]*>', '', html, flags=re.IGNORECASE)
    
    # 移除noscript标签及其内容
    html = re.sub(r'<noscript[^>]*>[\s\S]*?</noscript>', '', html, flags=re.IGNORECASE)
    
    # 移除iframe标签及其内容
    html = re.sub(r'<iframe[^>]*>[\s\S]*?</iframe>', '', html, flags=re.IGNORECASE)
    
    # 移除object和embed标签及其内容
    html = re.sub(r'<(object|embed)[^>]*>[\s\S]*?</\1>', '', html, flags=re.IGNORECASE)
    # 单独处理可能没有闭合标签的embed
    html = re.sub(r'<embed[^>]*/?>', '', html, flags=re.IGNORECASE)
    
    # 移除HTML注释
    html = re.sub(r'<!--[\s\S]*?-->', '', html)
    
    # 清理链接：移除javascript:链接和锚点链接
    def clean_link_match(match):
        href = match.group(1)
        if not href or href.startswith('javascript:') or href.startswith('#'):
            # 返回只有文本内容的链接
            link_text = match.group(2)
            return link_text
        return match.group(0)  # 保持原样
    
    html = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', clean_link_match, html, flags=re.IGNORECASE)
    
    # 标准化空白字符
    html = re.sub(r'\s+', ' ', html).strip()
    
    return html


def clean_markdown_content(markdown: str) -> str:
    """清理Markdown内容，移除多余的空行和空格。
    
    Args:
        markdown: 原始Markdown内容
        
    Returns:
        清理后的Markdown内容
    """
    # 移除每行首尾的空格
    lines = markdown.split('\n')
    lines = [line.strip() for line in lines]
    
    # 重新组合
    markdown = '\n'.join(lines)
    
    # 移除多余的换行符（3个或更多连续换行符替换为2个）
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    # 移除首尾空行
    markdown = markdown.strip()
    
    return markdown


async def fetch_url_content(
    url: str,
    user_agent: Optional[str] = None,
    force_raw: bool = False,
    proxy_url: Optional[str] = None,
    format_type: str = "markdown",
    timeout: Optional[int] = None,
    referer_url: Optional[str] = None,
    randomize_headers: bool = True,
) -> Tuple[str, str]:
    """获取URL内容并以适合LLM的形式返回，以及带有状态信息的前缀字符串。
    
    Args:
        url: 要获取的URL
        user_agent: 可选的用户代理字符串，如果不提供则随机选择
        force_raw: 是否强制获取原始HTML内容而不简化
        proxy_url: 可选的代理URL
        format_type: 返回格式类型 ("text", "markdown", "html")
        timeout: 可选的超时时间（秒）
        referer_url: 可选的Referer URL
        randomize_headers: 是否随机化请求头
        
    Returns:
        包含内容和前缀信息的元组 (content, prefix)
    """
    # 准备请求头，使用新的增强功能
    headers = get_browser_headers(
        custom_user_agent=user_agent,
        referer_url=referer_url,
        randomize=randomize_headers
    )
    
    # 设置超时时间
    timeout = min((timeout or DEFAULT_TIMEOUT), MAX_TIMEOUT)
    
    # 如果是HTTP URL，尝试HTTPS版本
    original_url = url
    response = None
    
    if is_http_url(url):
        https_url = convert_http_to_https(url)
        # 首先尝试HTTPS版本
        try:
            async with httpx.AsyncClient(proxy=proxy_url) as client:
                response = await client.get(
                    https_url,
                    follow_redirects=True,
                    headers=headers,
                    timeout=timeout,
                )
                if response.status_code < 400:
                    url = https_url  # 使用HTTPS URL
                else:
                    # 如果HTTPS失败，回退到HTTP
                    url = original_url
        except Exception:
            # 如果HTTPS连接失败，回退到HTTP
            url = original_url
    
    # 如果还没有成功获取响应，执行HTTP请求
    if response is None:
        async with httpx.AsyncClient(proxy=proxy_url) as client:
            try:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers=headers,
                    timeout=timeout,
                )
            except Exception as e:
                return f"<error>Failed to fetch {url}: {str(e)}</error>", ""
    
    # 检查状态码
    if response.status_code >= 400:
        return f"<error>Failed to fetch {url} - Status code {response.status_code}</error>", ""
    
    # 检查内容长度
    content_length = response.headers.get("content-length")
    if content_length and int(content_length) > MAX_RESPONSE_SIZE:
        return f"<error>Response too large (exceeds {MAX_RESPONSE_SIZE} bytes limit)</error>", ""
    
    page_raw = response.text
    if len(page_raw.encode('utf-8')) > MAX_RESPONSE_SIZE:
        return f"<error>Response too large (exceeds {MAX_RESPONSE_SIZE} bytes limit)</error>", ""

    content_type = response.headers.get("content-type", "")
    is_page_html = (
        "<html" in page_raw[:100].lower() or "text/html" in content_type.lower() or not content_type
    )
    
    if is_page_html and not force_raw:
        return extract_content_from_html(page_raw, format_type), ""
    
    return (
        page_raw,
        f"内容类型 {content_type} 无法简化为{format_type}，但这里是原始内容:\n",
    )


def fetch_url(
    url: str,
    max_length: int = 5000,
    start_index: int = 0,
    raw: bool = False,
    user_agent: Optional[str] = None,
    proxy_url: Optional[str] = None,
    format_type: str = "markdown",
    timeout: Optional[int] = None,
    referer_url: Optional[str] = None,
    randomize_headers: bool = True,
) -> Dict[str, Any]:
    """获取URL内容的工具函数
    
    Args:
        url: 要获取的URL
        max_length: 返回的最大字符数
        start_index: 从这个字符索引开始返回输出，如果之前的获取被截断并且需要更多上下文时很有用
        raw: 获取请求页面的实际HTML内容，不进行简化
        user_agent: 可选的用户代理字符串，如果不提供则随机选择
        proxy_url: 可选的代理URL
        format_type: 返回格式类型 ("text", "markdown", "html")
        timeout: 可选的超时时间（秒，最大120秒）
        referer_url: 可选的Referer URL
        randomize_headers: 是否随机化请求头
        
    Returns:
        包含获取结果的字典
    """
    # 验证输入参数
    if not url:
        raise ValueError("URL不能为空")
    
    if max_length <= 0 or max_length >= 50000:
        raise ValueError("max_length必须在1到50000之间")
    
    if start_index < 0:
        raise ValueError("start_index不能为负数")
    
    if format_type not in ["text", "markdown", "html"]:
        raise ValueError("format_type必须是 'text', 'markdown', 或 'html' 之一")
    
    if timeout is not None and (timeout <= 0 or timeout > MAX_TIMEOUT):
        raise ValueError(f"timeout必须在1到{MAX_TIMEOUT}秒之间")
    
    # 异步获取URL内容
    try:
        content, prefix = asyncio.run(fetch_url_content(
            url=url,
            user_agent=user_agent,
            force_raw=raw,
            proxy_url=proxy_url,
            format_type=format_type,
            timeout=timeout,
            referer_url=referer_url,
            randomize_headers=randomize_headers,
        ))
    except Exception as e:
        raise ValueError(f"获取URL内容失败: {str(e)}")
    
    # 处理内容截断
    original_length = len(content)
    if start_index >= original_length:
        content = "<error>No more content available.</error>"
    else:
        truncated_content = content[start_index : start_index + max_length]
        if not truncated_content:
            content = "<error>No more content available.</error>"
        else:
            content = truncated_content
            actual_content_length = len(truncated_content)
            remaining_content = original_length - (start_index + actual_content_length)
            # 如果还有剩余内容，添加继续获取的提示
            if actual_content_length == max_length and remaining_content > 0:
                next_start = start_index + actual_content_length
                content += f"\n\n<error>Content truncated. Call fetch tool with start_index parameter value {next_start} to get more content.</error>"
    
    return {
        "url": url,
        "content": f"{prefix}Contents of {url}:\n{content}",
        "original_length": original_length,
        "returned_length": len(content),
        "start_index": start_index,
        "format_type": format_type,
    }
