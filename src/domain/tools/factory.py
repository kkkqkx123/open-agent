"""工具工厂实现

提供配置驱动的工具创建功能，支持多种工具类型的统一管理。
"""

from typing import Dict, Any, List, Optional, Type, Union
from abc import ABC
import logging

from .interfaces import ITool, IToolFactory

# 导入配置类（延迟导入以避免循环依赖）
try:
    from src.infrastructure.tools.config import NativeToolConfig, MCPToolConfig, BuiltinToolConfig
    _config_imported = True
except ImportError:
    # 如果无法导入，使用动态创建
    _config_imported = False

logger = logging.getLogger(__name__)


class ToolFactory(IToolFactory):
    """工具工厂实现
    
    负责根据配置创建不同类型的工具实例，支持配置驱动的工具管理。
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        state_manager: Optional[Any] = None
    ):
        """初始化工具工厂

        Args:
            config: 工厂配置
            state_manager: 状态管理器实例（可选）
        """
        self.config = config or {}
        self.state_manager = state_manager
        
        # 注册支持的工具类型（使用延迟导入避免循环依赖）
        self._tool_types: Dict[str, Type[ITool]] = {}
        self._register_default_tool_types()
        
        # 工具实例缓存（可选，用于性能优化）
        self._tool_cache: Dict[str, ITool] = {}
        
        logger.info("ToolFactory初始化完成")
    
    def _register_default_tool_types(self) -> None:
        """注册默认工具类型（延迟导入）"""
        try:
            from .types.native_tool import NativeTool
            self._tool_types["native"] = NativeTool
        except ImportError:
            logger.warning("无法导入 NativeTool")
        
        try:
            from .types.mcp_tool import MCPTool
            self._tool_types["mcp"] = MCPTool
        except ImportError:
            logger.warning("无法导入 MCPTool")
        
        try:
            from .types.builtin_tool import BuiltinTool
            self._tool_types["builtin"] = BuiltinTool
        except ImportError:
            logger.warning("无法导入 BuiltinTool")
    
    def create_tool(self, tool_config: Dict[str, Any]) -> ITool:
        """根据配置创建工具实例
        
        Args:
            tool_config: 工具配置字典
            
        Returns:
            ITool: 创建的工具实例
            
        Raises:
            ValueError: 当工具类型不支持或配置无效时
        """
        try:
            # 1. 解析和验证配置
            config = self._parse_config(tool_config)
            
            # 2. 检查缓存（如果启用）
            cache_key = self._generate_cache_key(config)
            if cache_key in self._tool_cache:
                logger.debug(f"从缓存获取工具: {config.name}")
                return self._tool_cache[cache_key]
            
            # 3. 创建工具实例
            tool = self._create_tool_instance(config)
            
            # 4. 缓存工具实例（如果启用）
            if self._should_cache_tool(config):
                self._tool_cache[cache_key] = tool
            
            logger.info(f"成功创建工具: {config.name} (类型: {config.tool_type})")
            return tool
            
        except Exception as e:
            logger.error(f"创建工具失败: {e}")
            raise ValueError(f"创建工具失败: {e}")
    
    def register_tool_type(self, tool_type: str, tool_class: Type[ITool]) -> None:
        """注册新的工具类型
        
        Args:
            tool_type: 工具类型名称
            tool_class: 工具类
            
        Raises:
            ValueError: 当工具类型已存在时
        """
        if tool_type in self._tool_types:
            raise ValueError(f"工具类型已存在: {tool_type}")
        
        if not issubclass(tool_class, ITool):
            raise ValueError(f"工具类必须实现ITool接口: {tool_class}")
        
        self._tool_types[tool_type] = tool_class
        logger.info(f"注册工具类型: {tool_type}")
    
    def get_supported_types(self) -> List[str]:
        """获取支持的工具类型列表
        
        Returns:
            List[str]: 支持的工具类型列表
        """
        return list(self._tool_types.keys())
    
    def clear_cache(self) -> None:
        """清除工具实例缓存"""
        self._tool_cache.clear()
        logger.info("清除工具缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        return {
            "cache_size": len(self._tool_cache),
            "cached_tools": list(self._tool_cache.keys())
        }
    
    def get_tool(self, tool_name: str) -> Optional[ITool]:
        """根据名称获取工具实例
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[ITool]: 工具实例，如果不存在则返回None
        """
        # 首先检查缓存
        for tool in self._tool_cache.values():
            if tool.name == tool_name:
                return tool
        
        # 如果缓存中没有，尝试创建
        # 这里需要从配置中获取工具配置，但ToolFactory本身不存储配置
        # 所以这个方法可能需要重新设计或者从外部获取配置
        logger.warning(f"工具 '{tool_name}' 未在缓存中找到，ToolFactory需要配置来创建工具")
        return None
    
    def create_tools_from_config(self, tools_config: List[Dict[str, Any]]) -> List[ITool]:
        """从配置列表创建多个工具实例
        
        Args:
            tools_config: 工具配置列表
            
        Returns:
            List[ITool]: 创建的工具实例列表
        """
        tools = []
        for tool_config in tools_config:
            try:
                tool = self.create_tool(tool_config)
                tools.append(tool)
            except Exception as e:
                logger.error(f"创建工具失败: {tool_config.get('name', 'unknown')}, 错误: {e}")
                # 可以选择继续创建其他工具，或者抛出异常
                continue
        
        return tools
    
    def _parse_config(self, tool_config: Dict[str, Any]) -> 'ToolConfig':
        """解析和验证工具配置
        
        Args:
            tool_config: 原始配置字典
            
        Returns:
            ToolConfig: 解析后的配置对象
            
        Raises:
            ValueError: 当配置无效时
        """
        try:
            # 验证必需字段
            if "tool_type" not in tool_config:
                raise ValueError("缺少必需字段: tool_type")
            
            if "name" not in tool_config:
                raise ValueError("缺少必需字段: name")
            
            # 创建配置对象
            config = ToolConfig(**tool_config)
            
            # 验证工具类型
            if config.tool_type not in self._tool_types:
                raise ValueError(f"不支持的工具类型: {config.tool_type}")
            
            return config
            
        except Exception as e:
            raise ValueError(f"配置解析失败: {e}")
    
    def _create_tool_instance(self, config: 'ToolConfig') -> ITool:
        """创建工具实例

        Args:
            config: 工具配置

        Returns:
            ITool: 工具实例
        """
        tool_class = self._tool_types[config.tool_type]

        try:
            # 根据工具类型创建实例
            if config.tool_type == "native":
                # NativeTool 需要一个配置对象，包含所有必需属性
                native_config = type('NativeToolConfig', (), {
                    'name': config.name,
                    'description': config.description,
                    'parameters_schema': config.parameters or {},
                    'api_url': getattr(config, 'api_url', 'https://example.com/api'),
                    'method': getattr(config, 'method', 'POST'),
                    'headers': getattr(config, 'headers', {}),
                    'auth_method': getattr(config, 'auth_method', 'api_key'),
                    'api_key': getattr(config, 'api_key', None),
                    'timeout': getattr(config, 'timeout', 30),
                    'enabled': getattr(config, 'enabled', True),
                    'retry_count': getattr(config, 'retry_count', 3),
                    'retry_delay': getattr(config, 'retry_delay', 1.0)
                })()
                return tool_class(native_config)  # type: ignore
            elif config.tool_type == "mcp":
                # MCPTool 需要一个配置对象，包含所有必需属性
                mcp_config = type('MCPToolConfig', (), {
                    'name': config.name,
                    'description': config.description,
                    'parameters_schema': config.parameters or {},
                    'mcp_server_url': getattr(config, 'mcp_server_url', 'http://localhost:8000'),
                    'dynamic_schema': getattr(config, 'dynamic_schema', False),
                    'timeout': getattr(config, 'timeout', 30),
                    'enabled': getattr(config, 'enabled', True),
                    'refresh_interval': getattr(config, 'refresh_interval', None)
                })()
                return tool_class(mcp_config)  # type: ignore
            elif config.tool_type == "builtin":
                # BuiltinTool 需要一个函数和配置对象
                builtin_func = getattr(config, 'function', lambda: None)
                builtin_config = type('BuiltinToolConfig', (), {
                    'name': config.name,
                    'description': config.description,
                    'parameters_schema': config.parameters or {},
                    'function_path': getattr(config, 'function_path', None),
                    'timeout': getattr(config, 'timeout', 30),
                    'enabled': getattr(config, 'enabled', True)
                })()
                return tool_class(builtin_func, builtin_config)  # type: ignore
            else:
                # 通用创建方式
                generic_config = type('GenericToolConfig', (), config.to_dict())()
                return tool_class(generic_config)  # type: ignore
        except Exception as e:
            logger.error(f"创建工具实例失败: {e}")
            raise ValueError(f"创建工具实例失败: {e}")
    
    def _generate_cache_key(self, config: 'ToolConfig') -> str:
        """生成缓存键
        
        Args:
            config: 工具配置
            
        Returns:
            str: 缓存键
        """
        # 使用配置的关键字段生成缓存键
        key_parts = [
            config.tool_type,
            config.name,
            str(sorted(config.parameters.items())) if config.parameters else ""
        ]
        return "|".join(key_parts)
    
    def _should_cache_tool(self, config: 'ToolConfig') -> bool:
        """判断是否应该缓存工具实例
        
        Args:
            config: 工具配置
            
        Returns:
            bool: 是否应该缓存
        """
        # 可以根据配置决定是否缓存
        # 目前默认缓存无状态工具
        return config.tool_type in ["builtin"]


class ToolConfig:
    """工具配置类"""
    
    def __init__(
        self,
        tool_type: str,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        """初始化工具配置
        
        Args:
            tool_type: 工具类型
            name: 工具名称
            description: 工具描述
            parameters: 工具参数
            **kwargs: 其他配置参数
        """
        self.tool_type = tool_type
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        
        # 根据工具类型存储特定配置
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        result = {
            "tool_type": self.tool_type,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
        
        # 添加其他属性
        for key, value in self.__dict__.items():
            if key not in ["tool_type", "name", "description", "parameters"]:
                result[key] = value
        
        return result


# 全局工具工厂实例
_global_factory: Optional[ToolFactory] = None


def get_global_factory() -> ToolFactory:
    """获取全局工具工厂实例
    
    Returns:
        ToolFactory: 全局工具工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = ToolFactory()
    return _global_factory


def set_global_factory(factory: ToolFactory) -> None:
    """设置全局工具工厂实例
    
    Args:
        factory: 工厂实例
    """
    global _global_factory
    _global_factory = factory


def create_tool(tool_config: Dict[str, Any]) -> ITool:
    """使用全局工厂创建工具的便捷函数
    
    Args:
        tool_config: 工具配置
        
    Returns:
        ITool: 工具实例
    """
    return get_global_factory().create_tool(tool_config)