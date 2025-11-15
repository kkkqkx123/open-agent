"""
工具管理器实现

提供工具的加载、注册、查询和管理功能。
"""

import os
import importlib
import inspect
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path

from infrastructure.config.loader.file_config_loader import IConfigLoader
from src.infrastructure.exceptions import InfrastructureError
from src.infrastructure.logger.logger import ILogger
from .interfaces import IToolManager, IToolLoader, IToolAdapter, IToolCache
from src.domain.tools.interfaces import ITool, IToolRegistry
from src.domain.tools.types.native_tool import NativeTool
from src.domain.tools.types.mcp_tool import MCPTool
from src.domain.tools.types.builtin_tool import BuiltinToolFactory
from .config import (
    ToolConfig,
    NativeToolConfig,
    MCPToolConfig,
    BuiltinToolConfig,
    ToolSetConfig,
    ToolRegistryConfig,
)
# 从loaders模块导入DefaultToolLoader


class ToolManager(IToolManager, IToolRegistry):
    """工具管理器实现

    负责工具的加载、注册、查询和管理。
    """

    def __init__(
        self, 
        config_loader: Optional[IConfigLoader] = None, 
        logger: Optional[ILogger] = None,
        tool_loader: Optional[IToolLoader] = None,
        tool_cache: Optional[IToolCache] = None
    ):
        """初始化工具管理器

        Args:
            config_loader: 配置加载器（可选）
            logger: 日志记录器（可选）
            tool_loader: 工具加载器（可选）
            tool_cache: 工具缓存（可选）
        """
        self.config_loader = config_loader
        self.logger = logger
        # 如果没有提供tool_loader，则创建默认的DefaultToolLoader
        if tool_loader is None and config_loader is not None and logger is not None:
            from .loaders import DefaultToolLoader
            self.tool_loader = DefaultToolLoader(config_loader, logger)
        else:
            self.tool_loader = tool_loader
        self.tool_cache = tool_cache
        self._tools: Dict[str, ITool] = {}
        self._tool_sets: Dict[str, ToolSetConfig] = {}
        self._loaded = False

    def load_tools(self) -> List[ITool]:
        """加载所有可用工具

        Returns:
            List[ITool]: 已加载的工具列表
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
        try:
            self.logger.info("开始调用工具加载器加载工具配置")
            self.logger.info(f"工具加载器类型: {type(self.tool_loader)}")
            # 使用工具加载器加载工具配置
            result = self.tool_loader.load_from_config("tools")
            self.logger.info(f"工具加载器返回结果: {len(result)} 个配置")
            return result
        except Exception as e:
            self.logger.error(f"加载工具配置失败: {str(e)}")
            raise InfrastructureError(f"加载工具配置失败: {str(e)}")

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

    def _create_tool(self, config: ToolConfig) -> ITool:
        """根据配置创建工具实例

        Args:
            config: 工具配置

        Returns:
            ITool: 工具实例

        Raises:
            ValueError: 创建工具失败
        """
        # 检查缓存
        if self.tool_cache:
            cached_tool = self.tool_cache.get(config.name)
            if cached_tool:
                return cached_tool

        tool: ITool
        if isinstance(config, NativeToolConfig):
            tool = NativeTool(config)
        elif isinstance(config, MCPToolConfig):
            tool = MCPTool(config)
        elif isinstance(config, BuiltinToolConfig):
            tool = self._create_builtin_tool(config)
        else:
            raise ValueError(f"未知的工具配置类型: {type(config)}")

        # 缓存工具
        if self.tool_cache:
            self.tool_cache.set(config.name, tool)

        return tool

    def _create_builtin_tool(self, config: BuiltinToolConfig) -> ITool:
        """创建内置工具

        Args:
            config: 内置工具配置

        Returns:
            ITool: 内置工具实例

        Raises:
            ValueError: 创建内置工具失败
        """
        if config.function_path:
            # 从路径加载函数
            func = self._load_function_from_path(config.function_path)
            return BuiltinToolFactory.create_tool(func, config)
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

    def get_tool(self, name: str) -> ITool:
        """根据名称获取工具

        Args:
            name: 工具名称

        Returns:
            ITool: 工具实例

        Raises:
            ValueError: 工具不存在
        """
        if not self._loaded:
            self.load_tools()

        if name not in self._tools:
            raise ValueError(f"工具不存在: {name}")

        return self._tools[name]

    def get_tool_set(self, name: str) -> List[ITool]:
        """获取工具集

        Args:
            name: 工具集名称

        Returns:
            List[ITool]: 工具集中的工具列表

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

    def register_tool(self, tool: ITool) -> None:
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

    def unregister_tool(self, name: str) -> bool:
        """注销工具

        Args:
            name: 工具名称

        Returns:
            bool: 是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            self.logger.info(f"已注销工具: {name}")
            return True
        return False

    def reload_tools(self) -> List[ITool]:
        """重新加载所有工具

        Returns:
            List[ITool]: 重新加载后的工具列表
        """
        self._tools.clear()
        self._tool_sets.clear()
        self._loaded = False
        
        # 清除缓存
        if self.tool_cache:
            self.tool_cache.clear()
            
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
        return {
            "name": tool.name,
            "description": tool.description,
            "schema": tool.get_schema()
        }

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
            "tools": [self.get_tool_info(tool.name) for tool in tools],
            "enabled": tool_set_config.enabled,
            "metadata": tool_set_config.metadata,
        }


class DefaultToolLoader(IToolLoader):
    """默认工具加载器实现"""
    
    def __init__(self, config_loader: IConfigLoader, logger: ILogger):
        """初始化工具加载器
        
        Args:
            config_loader: 配置加载器
            logger: 日志记录器
        """
        self.config_loader = config_loader
        self.logger = logger
    
    def load_from_config(self, config_path: str) -> List[ToolConfig]:
        """从配置文件加载工具
        
        Args:
            config_path: 配置文件路径

        Returns:
            List[ToolConfig]: 加载的工具配置列表
        """
        configs: List[ToolConfig] = []
        self.logger.info(f"Loading tools from config path: {config_path}")

        try:
            # 加载工具配置目录
            tools_config_dir = Path(config_path)
            self.logger.info(f"Checking tools config directory: {tools_config_dir}")
            self.logger.info(f"Tools config directory exists: {tools_config_dir.exists()}")
            self.logger.info(f"Tools config directory str: {str(tools_config_dir)}")
            self.logger.info(f"Current working directory: {Path.cwd()}")
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
                    
                    # 解析工具配置
                    tool_type = config_data.get("tool_type")
                    if not tool_type:
                        raise ValueError("缺少tool_type配置")

                    tool_config: ToolConfig
                    if tool_type == "native":
                        tool_config = NativeToolConfig(**config_data)
                    elif tool_type == "mcp":
                        tool_config = MCPToolConfig(**config_data)
                    elif tool_type == "builtin":
                        tool_config = BuiltinToolConfig(**config_data)
                    else:
                        raise ValueError(f"未知的工具类型: {tool_type}")
                        
                    configs.append(tool_config)
                except Exception as e:
                    self.logger.error(f"解析工具配置失败 {config_file}: {str(e)}")

        except Exception as e:
            self.logger.error(f"加载工具配置失败: {str(e)}")

        return configs
    
    def load_from_module(self, module_path: str) -> List[ITool]:
        """从模块加载工具
        
        Args:
            module_path: 模块路径
            
        Returns:
            List[ITool]: 加载的工具列表
        """
        tools: List[ITool] = []
        
        try:
            module = importlib.import_module(module_path)
            
            # 查找模块中的ITool实现
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, ITool) and obj != ITool:
                    tool = obj()
                    tools.append(tool)
                    self.logger.info(f"从模块加载工具: {tool.name}")
                    
        except Exception as e:
            self.logger.error(f"从模块加载工具失败 {module_path}: {str(e)}")
            
        return tools


class DefaultToolCache(IToolCache):
    """默认工具缓存实现"""
    
    def __init__(self) -> None:
        """初始化工具缓存"""
        self._cache: Dict[str, ITool] = {}
        self._ttl: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[ITool]:
        """获取缓存的工具
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[ITool]: 工具实例，如果不存在则返回None
        """
        import time
        
        # 检查TTL
        if key in self._ttl:
            if time.time() > self._ttl[key]:
                self.invalidate(key)
                return None
                
        return self._cache.get(key)
    
    def set(self, key: str, tool: ITool, ttl: Optional[int] = None) -> None:
        """缓存工具
        
        Args:
            key: 缓存键
            tool: 工具实例
            ttl: 生存时间（秒）
        """
        import time
        
        self._cache[key] = tool
        if ttl:
            self._ttl[key] = time.time() + ttl
    
    def invalidate(self, key: str) -> bool:
        """使缓存失效
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功失效
        """
        removed = key in self._cache
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
        return removed
    
    def clear(self) -> None:
        """清除所有缓存"""
        self._cache.clear()
        self._ttl.clear()