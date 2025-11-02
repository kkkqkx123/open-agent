"""
网页内容获取工具实现

提供从URL获取网页内容并将其转换为Markdown格式的功能。
"""

import asyncio
from typing import Dict, Any, Tuple, Optional
from urllib.parse import urlparse, urlunparse

import httpx
import markdownify
import readabilipy
from protego import Protego


def extract_content_from_html(html: str) -> str:
    """从HTML内容中提取并转换为Markdown格式。
    
    Args:
        html: 要处理的原始HTML内容
        
    Returns:
        简化后的Markdown版本内容
    """
    try:
        ret = readabilipy.simple_json_from_html_string(
            html, use_readability=True
        )
        if not ret["content"]:
            return "<error>Page could not be simplified from HTML</error>"
        content = markdownify.markdownify(
            ret["content"],
            heading_style=markdownify.ATX,
        )
        return content
    except Exception as e:
        return f"<error>Error processing HTML content: {str(e)}</error>"


def get_robots_txt_url(url: str) -> str:
    """获取指定网站URL的robots.txt URL。
    
    Args:
        url: 要获取robots.txt的网站URL
        
    Returns:
        robots.txt文件的URL
    """
    # 解析URL组件
    parsed = urlparse(url)
    
    # 重构基础URL，只包含scheme、netloc和/robots.txt路径
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    
    return robots_url


async def check_may_fetch_url(url: str, user_agent: str, proxy_url: Optional[str] = None) -> bool:
    """检查根据robots.txt文件，用户代理是否可以获取该URL。
    
    Args:
        url: 要检查的URL
        user_agent: 用户代理字符串
        proxy_url: 可选的代理URL
        
    Returns:
        如果允许获取则返回True，否则返回False
    """
    robot_txt_url = get_robots_txt_url(url)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                robot_txt_url,
                follow_redirects=True,
                headers={"User-Agent": user_agent},
            )
        except Exception:
            # 如果无法获取robots.txt，假设允许获取
            return True
            
        if response.status_code in (401, 403):
            # 如果robots.txt需要认证或被禁止访问，假设不允许自动获取
            return False
        elif 400 <= response.status_code < 500:
            # 如果是客户端错误，假设允许获取
            return True
            
        robot_txt = response.text
    
    # 处理robots.txt内容，移除注释行
    processed_robot_txt = "\n".join(
        line for line in robot_txt.splitlines() if not line.strip().startswith("#")
    )
    
    try:
        robot_parser = Protego.parse(processed_robot_txt)
        return robot_parser.can_fetch(str(url), user_agent)
    except Exception:
        # 如果解析robots.txt失败，假设允许获取
        return True


async def fetch_url_content(
    url: str, 
    user_agent: str = "ModularAgent/1.0", 
    force_raw: bool = False, 
    proxy_url: Optional[str] = None,
    ignore_robots_txt: bool = False
) -> Tuple[str, str]:
    """获取URL内容并以适合LLM的形式返回，以及带有状态信息的前缀字符串。
    
    Args:
        url: 要获取的URL
        user_agent: 用户代理字符串
        force_raw: 是否强制获取原始HTML内容而不简化
        proxy_url: 可选的代理URL
        ignore_robots_txt: 是否忽略robots.txt限制
        
    Returns:
        包含内容和前缀信息的元组 (content, prefix)
    """
    # 检查robots.txt
    if not ignore_robots_txt:
        allowed = await check_may_fetch_url(url, user_agent, proxy_url)
        if not allowed:
            return f"<error>According to the website's robots.txt policy, fetching this page is not allowed: {url}</error>", ""
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": user_agent},
                timeout=30,
            )
        except Exception as e:
            return f"<error>Failed to fetch {url}: {str(e)}</error>", ""
            
        if response.status_code >= 400:
            return f"<error>Failed to fetch {url} - Status code {response.status_code}</error>", ""
        
        page_raw = response.text
    
    content_type = response.headers.get("content-type", "")
    is_page_html = (
        "<html" in page_raw[:100].lower() or "text/html" in content_type.lower() or not content_type
    )
    
    if is_page_html and not force_raw:
        return extract_content_from_html(page_raw), ""
    
    return (
        page_raw,
        f"内容类型 {content_type} 无法简化为markdown，但这里是原始内容:\n",
    )


def fetch_url(
    url: str,
    max_length: int = 5000,
    start_index: int = 0,
    raw: bool = False,
    user_agent: str = "ModularAgent/1.0",
    ignore_robots_txt: bool = False,
    proxy_url: Optional[str] = None
) -> Dict[str, Any]:
    """获取URL内容的工具函数
    
    Args:
        url: 要获取的URL
        max_length: 返回的最大字符数
        start_index: 从这个字符索引开始返回输出，如果之前的获取被截断并且需要更多上下文时很有用
        raw: 获取请求页面的实际HTML内容，不进行简化
        user_agent: 用户代理字符串
        ignore_robots_txt: 是否忽略robots.txt限制
        proxy_url: 可选的代理URL
        
    Returns:
        包含获取结果的字典
    """
    # 验证输入参数
    if not url:
        raise ValueError("URL不能为空")
    
    if max_length <= 0 or max_length >= 1000000:
        raise ValueError("max_length必须在1到1000000之间")
    
    if start_index < 0:
        raise ValueError("start_index不能为负数")
    
    # 异步获取URL内容
    try:
        content, prefix = asyncio.run(fetch_url_content(
            url=url,
            user_agent=user_agent,
            force_raw=raw,
            proxy_url=proxy_url,
            ignore_robots_txt=ignore_robots_txt
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
        "start_index": start_index
    }


# 示例用法
if __name__ == "__main__":
    # 测试获取URL工具
    test_url = "https://httpbin.org/html"
    
    print("测试获取URL工具:")
    print(f"URL: {test_url}")
    
    try:
        result = fetch_url(test_url)
        print(f"获取结果: {result['content'][:200]}...")
    except ValueError as e:
        print(f"错误: {e}")