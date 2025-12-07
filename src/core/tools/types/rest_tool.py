"""
REST工具实现

RestTool用于调用外部REST API的工具，支持HTTP请求和认证。
"""

import json
import asyncio
import time
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel

from ..base_stateful import StatefulBaseTool


class HTTPAuth(BaseModel):
    """HTTP认证配置"""

    auth_type: str  # "api_key", "bearer", "basic", "oauth"
    credentials: Dict[str, str]
    header_name: Optional[str] = None


class RestTool(StatefulBaseTool):
    """REST工具

    用于调用外部REST API的工具，支持多种HTTP方法和认证方式。
    注意：虽然技术上使用状态管理器来维护HTTP会话连接和速率限制等，
    但业务逻辑上是无状态的，每次调用不依赖于之前的调用结果。
    """

    def __init__(self, config: Any, state_manager):
        """初始化REST工具
        
        Args:
            config: REST工具配置
            state_manager: 状态管理器
        """
        super().__init__(
            name=config.name,
            description=config.description,
            parameters_schema=config.parameters_schema,
            state_manager=state_manager,
            config=config
        )
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_persistent_session(self) -> aiohttp.ClientSession:
        """获取持久化HTTP会话"""
        # 检查连接状态
        conn_state = self.get_connection_state()
        
        if conn_state and conn_state.get("session_active") and self._session:
            if not self._session.closed:
                return self._session
        
        # 创建新会话并维护状态
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
        self.update_connection_state({
            "session_active": True,
            "created_at": time.time(),
            "last_used": time.time()
        })
        
        return self._session

    def _build_headers(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """构建HTTP请求头

        Args:
            parameters: 工具参数

        Returns:
            Dict[str, str]: HTTP请求头
        """
        headers: Dict[str, str] = self.config.headers.copy()

        # 添加认证头
        if self.config.auth_method == "api_key" and self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        elif self.config.auth_method == "api_key_header" and self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        # 从参数中添加动态头
        if "headers" in parameters:
            for key, value in parameters["headers"].items():
                headers[str(key)] = str(value)

        return headers

    def _build_url(self, parameters: Dict[str, Any]) -> str:
        """构建请求URL

        Args:
            parameters: 工具参数

        Returns:
            str: 完整的请求URL
        """
        base_url = str(self.config.api_url)

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
        if response.status >= 40:
            raise ValueError(f"HTTP请求失败: {response.status} {response.reason}")

        # 根据Content-Type解析数据
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            return response_data
        elif "text/" in content_type:
            return str(response_data)
        else:
            return response_data

    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            Any: 执行结果
        """
        try:
            # 获取HTTP会话
            session = await self._get_persistent_session()

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
                result = self._parse_response(response, response_data)

                # 更新连接状态
                conn_state = self.get_connection_state()
                self.update_connection_state({
                    'last_used': time.time(),
                    'request_count': (conn_state or {}).get('request_count', 0) + 1
                })

                return result

        except aiohttp.ClientError as e:
            raise ValueError(f"HTTP请求错误: {str(e)}")
        except asyncio.TimeoutError:
            raise ValueError(f"请求超时: {self.config.timeout}秒")
        except Exception as e:
            raise ValueError(f"工具执行错误: {str(e)}")
        finally:
            # 不关闭会话，保持持久化
            pass

    async def __aenter__(self) -> "RestTool":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口"""
        if self._session and not self._session.closed:
            await self._session.close()