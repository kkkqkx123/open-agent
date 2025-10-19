"""
原生能力工具实现

NativeTool用于调用外部API的工具，支持HTTP请求和认证。
"""

import json
import asyncio
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel

from ..base import BaseTool
from ..config import NativeToolConfig


class HTTPAuth(BaseModel):
    """HTTP认证配置"""

    auth_type: str  # "api_key", "bearer", "basic", "oauth"
    credentials: Dict[str, str]
    header_name: Optional[str] = None


class NativeTool(BaseTool):
    """原生能力工具

    用于调用外部API的工具，支持多种HTTP方法和认证方式。
    """

    def __init__(self, config: NativeToolConfig):
        """初始化原生工具

        Args:
            config: 原生工具配置
        """
        super().__init__(
            name=config.name,
            description=config.description,
            parameters_schema=config.parameters_schema,
        )
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话

        Returns:
            aiohttp.ClientSession: HTTP会话
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _close_session(self) -> None:
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _build_headers(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """构建HTTP请求头

        Args:
            parameters: 工具参数

        Returns:
            Dict[str, str]: HTTP请求头
        """
        headers = self.config.headers.copy()

        # 添加认证头
        if self.config.auth_method == "api_key" and self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        elif self.config.auth_method == "api_key_header" and self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        # 从参数中添加动态头
        if "headers" in parameters:
            headers.update(parameters["headers"])

        return headers

    def _build_url(self, parameters: Dict[str, Any]) -> str:
        """构建请求URL

        Args:
            parameters: 工具参数

        Returns:
            str: 完整的请求URL
        """
        base_url = self.config.api_url

        # 处理URL路径参数
        if "path_params" in parameters:
            path_params = parameters["path_params"]
            for key, value in path_params.items():
                base_url = base_url.replace(f"{{{key}}}", str(value))

        # 处理查询参数
        if "query_params" in parameters:
            query_params = parameters["query_params"]
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            separator = "&" if "?" in base_url else "?"
            base_url = f"{base_url}{separator}{query_string}"

        return base_url

    def _build_request_data(
        self, parameters: Dict[str, Any]
    ) -> Union[Dict[str, Any], str, None]:
        """构建请求数据

        Args:
            parameters: 工具参数

        Returns:
            Union[Dict[str, Any], str, None]: 请求数据
        """
        # 移除特殊参数
        clean_params = {
            k: v
            for k, v in parameters.items()
            if k not in ["headers", "path_params", "query_params"]
        }

        if not clean_params:
            return None

        # 根据Content-Type处理数据
        content_type = self.config.headers.get("Content-Type", "")

        if "application/json" in content_type:
            return clean_params
        elif "application/x-www-form-urlencoded" in content_type:
            return "&".join([f"{k}={v}" for k, v in clean_params.items()])
        else:
            return clean_params

    def _parse_response(
        self, response: aiohttp.ClientResponse, response_data: Any
    ) -> Any:
        """解析响应数据

        Args:
            response: HTTP响应对象
            response_data: 响应数据

        Returns:
            Any: 解析后的响应数据
        """
        # 检查响应状态
        if response.status >= 400:
            raise ValueError(f"HTTP请求失败: {response.status} {response.reason}")

        # 根据Content-Type解析数据
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            return response_data
        elif "text/" in content_type:
            return str(response_data)
        else:
            return response_data

    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具（通过异步实现）

        Args:
            **kwargs: 工具参数

        Returns:
            Any: 执行结果
        """
        # 在新事件循环中运行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.execute_async(**kwargs))
        finally:
            loop.close()

    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            Any: 执行结果
        """
        try:
            # 获取HTTP会话
            session = await self._get_session()

            # 构建请求
            headers = self._build_headers(kwargs)
            url = self._build_url(kwargs)
            data = self._build_request_data(kwargs)

            # 发送请求
            async with session.request(
                method=self.config.method,
                url=url,
                headers=headers,
                json=data if isinstance(data, dict) else None,
                data=data if not isinstance(data, dict) else None,
            ) as response:
                # 读取响应数据
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    response_data = await response.json()
                else:
                    response_data = await response.text()

                # 解析并返回结果
                return self._parse_response(response, response_data)

        except aiohttp.ClientError as e:
            raise ValueError(f"HTTP请求错误: {str(e)}")
        except asyncio.TimeoutError:
            raise ValueError(f"请求超时: {self.config.timeout}秒")
        except Exception as e:
            raise ValueError(f"工具执行错误: {str(e)}")
        finally:
            # 清理会话
            await self._close_session()

    async def __aenter__(self) -> "NativeTool":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口"""
        await self._close_session()
