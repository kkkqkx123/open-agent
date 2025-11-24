"""
工具工厂实现

根据docs/tools/update.md中的建议，实现支持新工具类型的工厂。
"""

from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum
import importlib
import logging

from src.interfaces.tool.base import ITool, IToolFactory
from src.interfaces.tool.state_manager import IToolStateManager
from .types.builtin_tool import BuiltinTool
from .types.native_tool import NativeTool
from .types.rest_tool import RestTool
from .types.mcp_tool import MCPTool


class ToolType(Enum):
    """工具类型枚举"""
    BUILTIN = "builtin"      # 无状态内置工具
    NATIVE = "native"        # 有状态原生工具
    REST = "rest"           # 有状态REST工具
    MCP = "mcp"            # 有状态MCP工具


class OptimizedToolFactory(IToolFactory):
    """优化后的工具工厂"""
    
    def __init__(self, state_manager: Optional[IToolStateManager] = None):
        """初始化工具工厂
        
        Args:
            state_manager: 默认状态管理器（用于有状态工具）
        """
        self.state_manager = state_manager
        self._tool_types: Dict[str, Type[ITool]] = {}
        self._register_tool_types()
    
    def _register_tool_types(self) -> None:
        """注册支持的工具类型"""
        self._tool_types[ToolType.BUILTIN.value] = BuiltinTool
        self._tool_types[ToolType.NATIVE.value] = NativeTool
        self._tool_types[ToolType.REST.value] = RestTool
        self._tool_types[ToolType.MCP.value] = MCPTool
    
    def create_tool(self, tool_config: Dict[str, Any]) -> ITool:
        """创建工具实例
        
        Args:
            tool_config: 工具配置
            
        Returns:
            ITool: 工具实例
        """
        tool_type = tool_config.get('tool_type')
        
        if tool_type == ToolType.BUILTIN.value:
            return self._create_builtin_tool(tool_config)
        elif tool_type == ToolType.NATIVE.value:
            return self._create_native_tool(tool_config)
        elif tool_type == ToolType.REST.value:
            return self._create_rest_tool(tool_config)
        elif tool_type == ToolType.MCP.value:
            return self._create_mcp_tool(tool_config)
        else:
            raise ValueError(f"不支持的工具类型: {tool_type}")
    
    def _create_builtin_tool(self, config: Dict[str, Any]) -> BuiltinTool:
        """创建无状态内置工具"""
        # 加载函数
        func = self._load_function(config['function_path'])
        
        # 创建配置对象
        class SimpleConfig:
            def __init__(self, config_dict):
                self.name = config_dict.get('name')
                self.description = config_dict.get('description')
                self.parameters_schema = config_dict.get('parameters_schema', {})
        
        config_obj = SimpleConfig(config)
        return BuiltinTool(func, config_obj)
    
    def _create_native_tool(self, config: Dict[str, Any]) -> NativeTool:
        """创建有状态原生工具"""
        # 加载函数
        func = self._load_function(config['function_path'])
        
        # 获取或创建状态管理器
        state_manager = self._get_state_manager(config.get('state_config', {}))
        
        # 创建配置对象
        class SimpleConfig(dict):
            def __init__(self, config_dict):
                super().__init__()
                self.name = config_dict.get('name')
                self.description = config_dict.get('description')
                self.parameters_schema = config_dict.get('parameters_schema', {})
                self['state_injection'] = config_dict.get('state_injection', True)
                self['state_parameter_name'] = config_dict.get('state_parameter_name', 'state')
            
            def get(self, key, default=None):
                return self[key] if key in self else default
        
        config_obj = SimpleConfig(config)
        return NativeTool(func, config_obj, state_manager)
    
    def _create_rest_tool(self, config: Dict[str, Any]) -> RestTool:
        """创建有状态REST工具"""
        # 获取或创建状态管理器
        state_manager = self._get_state_manager(config.get('state_config', {}))
        
        # 创建配置对象
        class SimpleConfig:
            def __init__(self, config_dict):
                self.name = config_dict.get('name')
                self.description = config_dict.get('description')
                self.parameters_schema = config_dict.get('parameters_schema', {})
                self.api_url = config_dict.get('api_url')
                self.method = config_dict.get('method', 'GET')
                self.headers = config_dict.get('headers', {})
                self.auth_method = config_dict.get('auth_method')
                self.api_key = config_dict.get('api_key')
                self.timeout = config_dict.get('timeout', 30)
        
        config_obj = SimpleConfig(config)
        return RestTool(config_obj, state_manager)
    
    def _create_mcp_tool(self, config: Dict[str, Any]) -> MCPTool:
        """创建有状态MCP工具"""
        # 获取或创建状态管理器
        state_manager = self._get_state_manager(config.get('state_config', {}))
        
        # 创建配置对象
        class SimpleConfig:
            def __init__(self, config_dict):
                self.name = config_dict.get('name')
                self.description = config_dict.get('description')
                self.parameters_schema = config_dict.get('parameters_schema', {})
                self.mcp_server_url = config_dict.get('mcp_server_url')
                self.timeout = config_dict.get('timeout', 30)
                self.dynamic_schema = config_dict.get('dynamic_schema', False)
        
        config_obj = SimpleConfig(config)
        return MCPTool(config_obj, state_manager)
    
    def _load_function(self, function_path: str):
        """加载函数"""
        try:
            module_path, function_name = function_path.rsplit(':', 1)
            module = importlib.import_module(module_path)
            return getattr(module, function_name)
        except Exception as e:
            raise ValueError(f"无法加载函数 {function_path}: {str(e)}")
    
    def _get_state_manager(self, state_config: Dict[str, Any]) -> IToolStateManager:
        """获取状态管理器"""
        if self.state_manager:
            return self.state_manager
        
        # 根据配置创建状态管理器
        manager_type = state_config.get('manager_type', 'memory')
        if manager_type == 'memory':
            from .state.memory_state_manager import MemoryStateManager
            return MemoryStateManager(state_config)
        else:
            # 默认使用内存状态管理器
            from .state.memory_state_manager import MemoryStateManager
            return MemoryStateManager({})
    
    def register_tool_type(self, tool_type: str, tool_class: type) -> None:
        """注册工具类型"""
        self._tool_types[tool_type] = tool_class
    
    def get_supported_types(self) -> List[str]:
        """获取支持的工具类型"""
        return list(self._tool_types.keys())