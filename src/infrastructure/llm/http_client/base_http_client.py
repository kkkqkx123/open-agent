"""基础HTTP客户端实现

提供HTTP通信的基础功能，包括连接池管理、重试机制、错误处理等。
"""

import asyncio
import httpx
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from src.interfaces.llm.http_client import IHttpClient
from src.interfaces.dependency_injection import get_logger
from src.infrastructure.llm.utils.header_validator import HeaderProcessor


class BaseHttpClient(IHttpClient):
    """基础HTTP客户端实现
    
    提供HTTP通信的基础功能，包括：
    - 连接池管理
    - 自动重试机制
    - 超时控制
    - 错误处理
    - 日志记录
    """
    
    def __init__(
        self,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        pool_connections: int = 10,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """初始化基础HTTP客户端
        
        Args:
            base_url: 基础URL
            default_headers: 默认请求头
            timeout: 默认超时时间（秒）
            max_retries: 最大重试次数
            pool_connections: 连接池大小
            retry_delay: 重试延迟时间（秒）
            backoff_factor: 退避因子
        """
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.logger = get_logger(__name__)
        
        # 初始化头部处理器
        self.header_processor = HeaderProcessor()
        
        # 配置HTTP客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.default_headers,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_keepalive_connections=pool_connections,
                max_connections=pool_connections * 2
            )
        )
        
        self.logger.info(f"初始化HTTP客户端: {self.base_url}")
    
    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """发送POST请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            headers: 请求头
            timeout: 超时时间
            
        Returns:
            httpx.Response: HTTP响应对象
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = {**self.default_headers, **(headers or {})}
        
        # 验证和处理请求头
        resolved_headers, sanitized_headers, is_valid, errors = \
            self.header_processor.process_headers(request_headers)
        
        if not is_valid:
            error_msg = f"请求头验证失败: {', '.join(errors)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 记录请求信息（脱敏）
        self.logger.debug(
            f"发送POST请求: {url}",
            extra={
                "headers": sanitized_headers,
                "data_keys": list(data.keys()) if isinstance(data, dict) else [],
                "timeout": timeout or self.timeout
            }
        )
        
        # 执行重试逻辑
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                start_time = datetime.now()
                response = await self.client.post(
                    url=url,
                    json=data,
                    headers=resolved_headers,
                    timeout=timeout or self.timeout
                )
                
                # 记录响应信息
                response_time = (datetime.now() - start_time).total_seconds()
                self.logger.debug(
                    f"收到响应: {response.status_code}",
                    extra={
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "headers": dict(response.headers)
                    }
                )
                
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                # 检查是否应该重试
                if self._should_retry_on_status(e.response.status_code) and attempt < self.max_retries:
                    wait_time = self._calculate_retry_delay(attempt)
                    self.logger.warning(
                        f"HTTP状态错误，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"HTTP状态错误，不再重试: {e}")
                    raise
                    
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self._calculate_retry_delay(attempt)
                    self.logger.warning(
                        f"网络错误，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"网络错误，不再重试: {e}")
                    raise
        
        # 如果所有重试都失败，抛出最后一个异常
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("请求失败，未知错误")
    
    async def stream_post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """发送流式POST请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            headers: 请求头
            timeout: 超时时间
            
        Yields:
            str: 流式响应数据片段
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = {**self.default_headers, **(headers or {})}
        
        # 验证和处理请求头
        resolved_headers, sanitized_headers, is_valid, errors = \
            self.header_processor.process_headers(request_headers)
        
        if not is_valid:
            error_msg = f"请求头验证失败: {', '.join(errors)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.debug(
            f"发送流式POST请求: {url}",
            extra={
                "headers": sanitized_headers,
                "data_keys": list(data.keys()) if isinstance(data, dict) else []
            }
        )
        
        try:
            start_time = datetime.now()
            async with self.client.stream(
                method="POST",
                url=url,
                json=data,
                headers=resolved_headers,
                timeout=timeout or self.timeout
            ) as response:
                # 记录响应信息
                response_time = (datetime.now() - start_time).total_seconds()
                self.logger.debug(
                    f"开始流式响应: {response.status_code}",
                    extra={
                        "status_code": response.status_code,
                        "response_time": response_time
                    }
                )
                
                response.raise_for_status()
                
                chunk_count = 0
                async for chunk in response.aiter_text():
                    chunk_count += 1
                    if chunk.strip():  # 只返回非空块
                        yield chunk
                
                self.logger.debug(f"流式响应完成，共 {chunk_count} 个数据块")
                        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"流式请求HTTP错误: {e}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"流式请求网络错误: {e}")
            raise
        except Exception as e:
            self.logger.error(f"流式请求未知错误: {e}")
            raise
    
    def set_auth_header(self, token: str) -> None:
        """设置认证头部
        
        Args:
            token: 认证令牌
        """
        self.default_headers["Authorization"] = f"Bearer {token}"
        # 更新客户端的默认头部
        self.client.headers.update(self.default_headers)
        self.logger.debug("已设置Authorization头部")
    
    def set_base_url(self, url: str) -> None:
        """设置基础URL
        
        Args:
            url: 基础URL
        """
        self.base_url = url.rstrip('/')
        self.client.base_url = url
        self.logger.info(f"已更新基础URL: {self.base_url}")
    
    async def close(self) -> None:
        """关闭客户端连接
        
        清理资源，关闭连接池等。
        """
        if hasattr(self, 'client') and self.client:
            await self.client.aclose()
            self.logger.info("HTTP客户端连接已关闭")
    
    def _should_retry_on_status(self, status_code: int) -> bool:
        """判断是否应该根据状态码重试
        
        Args:
            status_code: HTTP状态码
            
        Returns:
            bool: 是否应该重试
        """
        # 可重试的状态码
        retryable_status_codes = {
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
        return status_code in retryable_status_codes
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """计算重试延迟时间
        
        Args:
            attempt: 当前尝试次数（从0开始）
            
        Returns:
            float: 延迟时间（秒）
        """
        return self.retry_delay * (self.backoff_factor ** attempt)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()