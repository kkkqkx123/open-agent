"""
工具管理器实现

提供工具的加载、注册、查询和管理功能。
"""

import os
import importlib
import inspect
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path

from src.infrastructure.config_loader import IConfigLoader
from src.infrastructure.exceptions import InfrastructureError
from src.infrastructure.logger.logger import ILogger
from .interfaces import IToolManager
from src.domain.tools.base import BaseTool
from src.domain.tools.types.native_tool import NativeTool
from src.domain.tools.types.mcp_tool import MCPTool
from src.domain.tools.types.builtin_tool import BuiltinTool
from .config import (
    ToolConfig,
    NativeToolConfig,
    MCPToolConfig,
    BuiltinToolConfig,
    ToolSetConfig,
    ToolRegistryConfig,
)


class ToolManager(IToolManager):
    """工具管理器实现

    负责工具的加载、注册、查询和管理。
    """

    def __init__(self, config_loader: IConfigLoader, logger: ILogger):
        """初始化工具管理器

        Args:
            config_loader: 配置加载器
            logger: 日志记录器
        """
        self.config_loader = config_loader
        self.logger = logger
        self._tools: Dict[str, BaseTool] = {}
        self._tool_sets: Dict[str, ToolSetConfig] = {}
        self._loaded = False

    def load_tools(self) -> List[BaseTool]:
        """加载所有可用工具

        Returns:
            List[BaseTool]: 已加载的工具列表
        """
        if self._loaded:
            return list(self._tools.values())

        try:
            # 加载工具配置
            self.logger.info("Loading tool configs")
            self.logger.info("Calling _load_tool_configs")
            tool_configs = self._load_tool_configs()
            self.logger.info(f"Loaded {len(tool_configs)} tool configs")

            # 创建工具实例
            for config in tool_configs:
                if not config.enabled:
                    self.logger.info(f"跳过已禁用的工具: {config.name}")
                    continue

                try:
                    tool = self._create_tool(config)
                    if tool.name not in self._tools:
                        self._tools[tool.name] = tool
                        self.logger.info(f"已加载工具: {tool.name}")
                    else:
                        self.logger.warning(f"工具名称重复: {tool.name}")
                except Exception as e:
                    self.logger.error(f"加载工具失败 {config.name}: {str(e)}")

            # 加载工具集配置
            self._load_tool_sets()

            self._loaded = True
            self.logger.info(f"工具加载完成，共加载 {len(self._tools)} 个工具")

            return list(self._tools.values())

        except Exception as e:
            self.logger.error(f"工具加载失败: {str(e)}")
            raise InfrastructureError(f"工具加载失败: {str(e)}")

    def _load_tool_configs(self) -> List[ToolConfig]:
        """加载工具配置

        Returns:
            List[ToolConfig]: 工具配置列表
        """
        configs: List[ToolConfig] = []

        try:
            # 加载工具配置目录
            tools_config_dir = Path("configs/tools")
            self.logger.info(f"Checking tools config directory: {tools_config_dir}")
            self.logger.info(f"Tools config directory exists: {tools_config_dir.exists()}")
            self.logger.info(f"Tools config directory str: {str(tools_config_dir)}")
            if not tools_config_dir.exists():
                self.logger.warning("工具配置目录不存在: configs/tools")
                return configs

            # 遍历工具配置文件
            config_files = list(tools_config_dir.glob("*.yaml"))
            self.logger.info(f"Found {len(config_files)} config files")
            for config_file in config_files:
                try:
                    self.logger.info(f"Loading config from {config_file}")
                    self.logger.info(f"Config file str: {str(config_file)}")
                    config_data = self.config_loader.load(str(config_file))
                    tool_config = self._parse_tool_config(config_data)
                    configs.append(tool_config)
                except Exception as e:
                    self.logger.error(f"解析工具配置失败 {config_file}: {str(e)}")

        except Exception as e:
            self.logger.error(f"加载工具配置失败: {str(e)}")

        return configs

    def _parse_tool_config(self, config_data: Dict[str, Any]) -> ToolConfig:
        """解析工具配置

        Args:
            config_data: 配置数据

        Returns:
            ToolConfig: 工具配置对象

        Raises:
            ValueError: 配置格式错误
        """
        tool_type = config_data.get("tool_type")
        if not tool_type:
            raise ValueError("缺少tool_type配置")

        if tool_type == "native":
            return NativeToolConfig(**config_data)
        elif tool_type == "mcp":
            return MCPToolConfig(**config_data)
        elif tool_type == "builtin":
            return BuiltinToolConfig(**config_data)
        else:
            raise ValueError(f"未知的工具类型: {tool_type}")

    def _create_tool(self, config: ToolConfig) -> BaseTool:
        """根据配置创建工具实例

        Args:
            config: 工具配置

        Returns:
            BaseTool: 工具实例

        Raises:
            ValueError: 创建工具失败
        """
        if isinstance(config, NativeToolConfig):
            return NativeTool(config)
        elif isinstance(config, MCPToolConfig):
            return MCPTool(config)
        elif isinstance(config, BuiltinToolConfig):
            return self._create_builtin_tool(config)
        else:
            raise ValueError(f"未知的工具配置类型: {type(config)}")

    def _create_builtin_tool(self, config: BuiltinToolConfig) -> BuiltinTool:
        """创建内置工具

        Args:
            config: 内置工具配置

        Returns:
            BuiltinTool: 内置工具实例

        Raises:
            ValueError: 创建内置工具失败
        """
        if config.function_path:
            # 从路径加载函数
            func = self._load_function_from_path(config.function_path)
            return BuiltinTool(func, config)
        else:
            raise ValueError("内置工具缺少function_path配置")

    def _load_function_from_path(self, function_path: str) -> Any:
        """从路径加载函数

        Args:
            function_path: 函数路径，格式为 "module.submodule:function_name"

        Returns:
            Any: 函数对象

        Raises:
            ValueError: 加载函数失败
        """
        try:
            module_path, function_name = function_path.split(":")
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)

            if not callable(func):
                raise ValueError(f"指定路径不是可调用对象: {function_path}")

            return func

        except Exception as e:
            raise ValueError(f"加载函数失败 {function_path}: {str(e)}")

    def _load_tool_sets(self) -> None:
        """加载工具集配置"""
        try:
            # 加载工具集配置目录
            tool_sets_config_dir = Path("configs/tool-sets")
            if not tool_sets_config_dir.exists():
                self.logger.warning("工具集配置目录不存在: configs/tool-sets")
                return

            # 遍历工具集配置文件
            for config_file in tool_sets_config_dir.glob("*.yaml"):
                try:
                    config_data = self.config_loader.load(str(config_file))
                    tool_set_config = ToolSetConfig(**config_data)

                    if tool_set_config.enabled:
                        self._tool_sets[tool_set_config.name] = tool_set_config
                        self.logger.info(f"已加载工具集: {tool_set_config.name}")
                    else:
                        self.logger.info(f"跳过已禁用的工具集: {tool_set_config.name}")

                except Exception as e:
                    self.logger.error(f"解析工具集配置失败 {config_file}: {str(e)}")

        except Exception as e:
            self.logger.error(f"加载工具集配置失败: {str(e)}")

    def get_tool(self, name: str) -> BaseTool:
        """根据名称获取工具

        Args:
            name: 工具名称

        Returns:
            BaseTool: 工具实例

        Raises:
            ValueError: 工具不存在
        """
        if not self._loaded:
            self.load_tools()

        if name not in self._tools:
            raise ValueError(f"工具不存在: {name}")

        return self._tools[name]

    def get_tool_set(self, name: str) -> List[BaseTool]:
        """获取工具集

        Args:
            name: 工具集名称

        Returns:
            List[BaseTool]: 工具集中的工具列表

        Raises:
            ValueError: 工具集不存在
        """
        if not self._loaded:
            self.load_tools()

        if name not in self._tool_sets:
            raise ValueError(f"工具集不存在: {name}")

        tool_set_config = self._tool_sets[name]
        tools = []

        for tool_name in tool_set_config.tools:
            try:
                tool = self.get_tool(tool_name)
                tools.append(tool)
            except ValueError as e:
                self.logger.warning(f"工具集中工具不存在 {tool_name}: {str(e)}")

        return tools

    def register_tool(self, tool: BaseTool) -> None:
        """注册新工具

        Args:
            tool: 工具实例

        Raises:
            ValueError: 工具名称已存在
        """
        if tool.name in self._tools:
            raise ValueError(f"工具名称已存在: {tool.name}")

        self._tools[tool.name] = tool
        self.logger.info(f"已注册工具: {tool.name}")

    def list_tools(self) -> List[str]:
        """列出所有可用工具名称

        Returns:
            List[str]: 工具名称列表
        """
        if not self._loaded:
            self.load_tools()

        return list(self._tools.keys())

    def list_tool_sets(self) -> List[str]:
        """列出所有可用工具集名称

        Returns:
            List[str]: 工具集名称列表
        """
        if not self._loaded:
            self.load_tools()

        return list(self._tool_sets.keys())

    def reload_tools(self) -> List[BaseTool]:
        """重新加载所有工具

        Returns:
            List[BaseTool]: 重新加载后的工具列表
        """
        self._tools.clear()
        self._tool_sets.clear()
        self._loaded = False
        return self.load_tools()

    def get_tool_info(self, name: str) -> Dict[str, Any]:
        """获取工具详细信息

        Args:
            name: 工具名称

        Returns:
            Dict[str, Any]: 工具信息

        Raises:
            ValueError: 工具不存在
        """
        tool = self.get_tool(name)
        return tool.to_dict()

    def get_tool_set_info(self, name: str) -> Dict[str, Any]:
        """获取工具集详细信息

        Args:
            name: 工具集名称

        Returns:
            Dict[str, Any]: 工具集信息

        Raises:
            ValueError: 工具集不存在
        """
        if name not in self._tool_sets:
            raise ValueError(f"工具集不存在: {name}")

        tool_set_config = self._tool_sets[name]
        tools = self.get_tool_set(name)

        return {
            "name": tool_set_config.name,
            "description": tool_set_config.description,
            "tools": [tool.to_dict() for tool in tools],
            "enabled": tool_set_config.enabled,
            "metadata": tool_set_config.metadata,
        }
