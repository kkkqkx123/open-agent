"""
工具工厂实现

根据docs/tools/update.md中的建议，实现支持新工具类型的工厂和统一的错误处理。
"""

from typing import Any, Dict, List, Optional, Type
import importlib
from src.interfaces.dependency_injection import get_logger

from src.interfaces.tool.base import ITool, IToolFactory
from src.interfaces.tool.state_manager import IToolStateManager
from .types.builtin_tool import BuiltinTool
from .types.native_tool import NativeTool
from .types.rest_tool import RestTool
from .types.mcp_tool import MCPTool
from src.interfaces.tool.exceptions import ToolError, ToolRegistrationError
from src.infrastructure.error_management.impl.tools import handle_tool_error, create_tool_error_context
from src.core.config.models.tool_config import ToolType

logger = get_logger(__name__)


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
            
        Raises:
            ToolRegistrationError: 工具创建失败
        """
        try:
            # 验证配置
            self._validate_tool_config(tool_config)
            
            tool_type = tool_config.get('tool_type')
            tool_name = tool_config.get('name', 'unknown')
            
            logger.info(f"创建工具: {tool_name} (类型: {tool_type})")
            
            if tool_type == ToolType.BUILTIN.value:
                return self._create_builtin_tool(tool_config)
            elif tool_type == ToolType.NATIVE.value:
                return self._create_native_tool(tool_config)
            elif tool_type == ToolType.REST.value:
                return self._create_rest_tool(tool_config)
            elif tool_type == ToolType.MCP.value:
                return self._create_mcp_tool(tool_config)
            else:
                raise ToolRegistrationError(f"不支持的工具类型: {tool_type}")
                
        except ToolRegistrationError:
            # 重新抛出工具注册错误
            raise
        except Exception as e:
            # 包装其他异常
            tool_name = tool_config.get('name', 'unknown')
            tool_error = ToolRegistrationError(f"创建工具失败: {tool_name}, 错误: {str(e)}")
            
            # 使用错误处理器
            context = create_tool_error_context(
                tool_call=None,  # type: ignore
                tool_config=tool_config,
                operation="creation"
            )
            handle_tool_error(tool_error, context)
            
            raise tool_error from e
    
    def _validate_tool_config(self, tool_config: Dict[str, Any]) -> None:
        """验证工具配置"""
        if not isinstance(tool_config, dict):
            raise ToolRegistrationError("工具配置必须是字典类型")
        
        # 检查必需字段
        required_fields = ['name', 'tool_type', 'description']
        for field in required_fields:
            if field not in tool_config:
                raise ToolRegistrationError(f"工具配置缺少必需字段: {field}")
        
        # 验证字段类型
        if not isinstance(tool_config['name'], str) or not tool_config['name'].strip():
            raise ToolRegistrationError("工具名称必须是非空字符串")
        
        if not isinstance(tool_config['tool_type'], str):
            raise ToolRegistrationError("工具类型必须是字符串")
        
        if not isinstance(tool_config['description'], str) or not tool_config['description'].strip():
            raise ToolRegistrationError("工具描述必须是非空字符串")
    
    def _create_builtin_tool(self, config: Dict[str, Any]) -> BuiltinTool:
        """创建无状态内置工具"""
        try:
            # 验证内置工具特定配置
            if 'function_path' not in config:
                raise ToolRegistrationError("内置工具必须包含function_path")
            
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
            
        except Exception as e:
            if isinstance(e, ToolRegistrationError):
                raise
            else:
                raise ToolRegistrationError(f"创建内置工具失败: {str(e)}") from e
    
    def _create_native_tool(self, config: Dict[str, Any]) -> NativeTool:
        """创建有状态原生工具"""
        try:
            # 验证原生工具特定配置
            if 'function_path' not in config:
                raise ToolRegistrationError("原生工具必须包含function_path")
            
            if not self.state_manager:
                raise ToolRegistrationError(
                    "创建有状态工具(native)需要状态管理器。"
                    "请在工厂初始化时通过 state_manager 参数提供。"
                )
            
            # 加载函数
            func = self._load_function(config['function_path'])
            
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
            return NativeTool(func, config_obj, self.state_manager)
            
        except Exception as e:
            if isinstance(e, ToolRegistrationError):
                raise
            else:
                raise ToolRegistrationError(f"创建原生工具失败: {str(e)}") from e
    
    def _create_rest_tool(self, config: Dict[str, Any]) -> RestTool:
        """创建REST工具（业务逻辑上无状态，但技术上使用状态管理器进行连接复用等）"""
        try:
            # 验证REST工具特定配置
            if 'api_url' not in config:
                raise ToolRegistrationError("REST工具必须包含api_url")
            
            if not self.state_manager:
                raise ToolRegistrationError(
                    "创建REST工具需要状态管理器（用于连接复用等技术性功能）。"
                    "请在工厂初始化时通过 state_manager 参数提供。"
                )
            
            # 验证URL格式
            api_url = config['api_url']
            if not isinstance(api_url, str) or not api_url.startswith(('http://', 'https://')):
                raise ToolRegistrationError("REST工具的api_url必须是有效的HTTP/HTTPS URL")
            
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
            return RestTool(config_obj, self.state_manager)
            
        except Exception as e:
            if isinstance(e, ToolRegistrationError):
                raise
            else:
                raise ToolRegistrationError(f"创建REST工具失败: {str(e)}") from e
    
    def _create_mcp_tool(self, config: Dict[str, Any]) -> MCPTool:
        """创建有状态MCP工具"""
        try:
            # 验证MCP工具特定配置
            if 'mcp_server_url' not in config:
                raise ToolRegistrationError("MCP工具必须包含mcp_server_url")
            
            if not self.state_manager:
                raise ToolRegistrationError(
                    "创建有状态工具(mcp)需要状态管理器。"
                    "请在工厂初始化时通过 state_manager 参数提供。"
                )
            
            # 验证URL格式
            mcp_server_url = config['mcp_server_url']
            if not isinstance(mcp_server_url, str) or not mcp_server_url.startswith(('http://', 'https://', 'ws://', 'wss://')):
                raise ToolRegistrationError("MCP工具的mcp_server_url必须是有效的URL")
            
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
            return MCPTool(config_obj, self.state_manager)
            
        except Exception as e:
            if isinstance(e, ToolRegistrationError):
                raise
            else:
                raise ToolRegistrationError(f"创建MCP工具失败: {str(e)}") from e
    
    def _load_function(self, function_path: str):
        """加载函数"""
        module_path = None
        function_name = None
        
        try:
            if not isinstance(function_path, str) or ':' not in function_path:
                raise ToolRegistrationError(f"无效的函数路径格式: {function_path}")
            
            module_path, function_name = function_path.rsplit(':', 1)
            
            if not module_path or not function_name:
                raise ToolRegistrationError(f"无效的函数路径格式: {function_path}")
            
            module = importlib.import_module(module_path)
            
            if not hasattr(module, function_name):
                raise ToolRegistrationError(f"模块 {module_path} 中不存在函数 {function_name}")
            
            func = getattr(module, function_name)
            
            if not callable(func):
                raise ToolRegistrationError(f"{function_path} 不是可调用对象")
            
            return func
            
        except ImportError as e:
            raise ToolRegistrationError(f"无法导入模块 {module_path}: {str(e)}") from e
        except AttributeError as e:
            raise ToolRegistrationError(f"模块 {module_path} 中不存在函数 {function_name}: {str(e)}") from e
        except Exception as e:
            if isinstance(e, ToolRegistrationError):
                raise
            else:
                raise ToolRegistrationError(f"加载函数失败 {function_path}: {str(e)}") from e
    
    def register_tool_type(self, tool_type: str, tool_class: type) -> None:
        """注册工具类型
        
        Args:
            tool_type: 工具类型名称
            tool_class: 工具类
            
        Raises:
            ToolRegistrationError: 注册失败
        """
        try:
            if not isinstance(tool_type, str) or not tool_type.strip():
                raise ToolRegistrationError("工具类型名称必须是非空字符串")
            
            if not isinstance(tool_class, type):
                raise ToolRegistrationError("工具类必须是类型对象")
            
            # 检查是否实现了ITool接口
            from src.interfaces.tool.base import ITool
            if not issubclass(tool_class, ITool):
                raise ToolRegistrationError(f"工具类 {tool_class.__name__} 必须实现ITool接口")
            
            self._tool_types[tool_type] = tool_class
            logger.info(f"注册工具类型: {tool_type} -> {tool_class.__name__}")
            
        except ToolRegistrationError:
            raise
        except Exception as e:
            raise ToolRegistrationError(f"注册工具类型失败: {tool_type}, 错误: {str(e)}") from e
    
    def get_supported_types(self) -> List[str]:
        """获取支持的工具类型"""
        return list(self._tool_types.keys())