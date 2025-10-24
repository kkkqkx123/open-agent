"""
MCP工具实现

MCPTool用于通过MCP服务器提供的工具，支持与MCP服务器的通信。
"""

import json
import asyncio
from typing import Any, Dict, Optional, List
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel

from ..base import BaseTool



class MCPClient:
    """MCP客户端

    用于与MCP服务器通信的客户端。
    """

    def __init__(self, server_url: str, timeout: int = 30):
        """初始化MCP客户端

        Args:
            server_url: MCP服务器URL
            timeout: 请求超时时间
        """
        self.server_url = server_url
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话

        Returns:
            aiohttp.ClientSession: HTTP会话
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _close_session(self) -> None:
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """获取工具Schema

        Args:
            tool_name: 工具名称

        Returns:
            Dict[str, Any]: 工具Schema

        Raises:
            ValueError: 获取Schema失败
        """
        try:
            session = await self._get_session()

            url = urljoin(self.server_url, f"/tools/{tool_name}/schema")

            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"获取工具Schema失败: {response.status}")

                result: Dict[str, Any] = await response.json()
                return result

        except aiohttp.ClientError as e:
            raise ValueError(f"MCP客户端错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"获取工具Schema错误: {str(e)}")

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            Any: 执行结果

        Raises:
            ValueError: 执行工具失败
        """
        try:
            session = await self._get_session()

            url = urljoin(self.server_url, f"/tools/{tool_name}/execute")

            async with session.post(url, json=arguments) as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise ValueError(f"执行工具失败: {response.status} - {error_data}")

                return await response.json()

        except aiohttp.ClientError as e:
            raise ValueError(f"MCP客户端错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"执行工具错误: {str(e)}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具

        Returns:
            List[Dict[str, Any]]: 工具列表

        Raises:
            ValueError: 获取工具列表失败
        """
        try:
            session = await self._get_session()

            url = urljoin(self.server_url, "/tools")

            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"获取工具列表失败: {response.status}")

                result: List[Dict[str, Any]] = await response.json()
                return result

        except aiohttp.ClientError as e:
            raise ValueError(f"MCP客户端错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"获取工具列表错误: {str(e)}")

    async def __aenter__(self) -> "MCPClient":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口"""
        await self._close_session()


class MCPTool(BaseTool):
    """MCP工具

    通过MCP服务器提供的工具实现。
    """

    def __init__(self, config: Any):
        
        """初始化MCP工具

        Args:
            config: MCP工具配置
        """
        super().__init__(
            name=config.name,
            description=config.description,
            parameters_schema=config.parameters_schema,
        )
        self.config = config
        self.mcp_client = MCPClient(
            server_url=config.mcp_server_url, timeout=config.timeout
        )

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
            async with self.mcp_client:
                # 如果需要动态获取Schema
                if self.config.dynamic_schema:
                    schema = await self.mcp_client.get_tool_schema(self.name)
                    self.parameters_schema = schema

                # 执行工具
                result = await self.mcp_client.execute_tool(
                    tool_name=self.name, arguments=kwargs
                )

                return result

        except Exception as e:
            raise ValueError(f"MCP工具执行错误: {str(e)}")

    async def refresh_schema(self) -> None:
        """刷新工具Schema

        从MCP服务器重新获取最新的工具Schema。
        """
        try:
            async with self.mcp_client:
                schema = await self.mcp_client.get_tool_schema(self.name)
                self.parameters_schema = schema
        except Exception as e:
            raise ValueError(f"刷新Schema失败: {str(e)}")

    @classmethod
    async def from_mcp_server(
        cls, server_url: str, tool_name: str, timeout: int = 30
    ) -> "MCPTool":
        """从MCP服务器创建工具实例

        Args:
            server_url: MCP服务器URL
            tool_name: 工具名称
            timeout: 超时时间

        Returns:
            MCPTool: 工具实例

        Raises:
            ValueError: 创建工具失败
        """
        try:
            # 创建临时客户端获取工具信息
            async with MCPClient(server_url, timeout) as client:
                schema = await client.get_tool_schema(tool_name)

                # 创建配置
                from src.infrastructure.tools.config import MCPToolConfig
                config = MCPToolConfig(
                    name=tool_name,
                    tool_type="mcp",
                    description=schema.get("description", ""),
                    parameters_schema=schema.get("parameters", {}),
                    mcp_server_url=server_url,
                    timeout=timeout,
                    dynamic_schema=True,
                )

                return cls(config)

        except Exception as e:
            raise ValueError(f"从MCP服务器创建工具失败: {str(e)}")
