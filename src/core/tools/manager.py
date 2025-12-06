"""
工具管理器实现

支持新的工具类型层次结构的工具管理器和统一的错误处理。
"""

import asyncio
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.interfaces.tool.base import ITool, IToolManager, IToolFactory
from .factory import OptimizedToolFactory
from src.interfaces.tool.exceptions import ToolError, ToolRegistrationError
from src.infrastructure.error_management.impl.tools import (
    handle_tool_error, create_tool_error_context, ToolExecutionValidator
)

if TYPE_CHECKING:
    from .config import ToolConfig


class ToolManager(IToolManager):
    """工具管理器
    
    支持新工具类型层次结构的工具管理器。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化工具管理器
        
        Args:
            config: 工具管理器配置
        """
        self.config = config or {}
        self._tools: Dict[str, ITool] = {}  # 直接存储工具
        self._factory = OptimizedToolFactory()
        self._initialized = False
        self._active_sessions: Dict[str, Dict[str, ITool]] = {}  # session_id -> {tool_name: tool}
        self._validator = ToolExecutionValidator()
    
    @property
    def factory(self) -> IToolFactory:
        """获取工具工厂"""
        return self._factory
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    async def initialize(self) -> None:
        """初始化工具管理器

        加载配置中指定的所有工具。
        """
        if self._initialized:
            return

        # 加载配置中的工具
        await self._load_tools_from_config()

        self._initialized = True
    
    async def _load_tools_from_config(self) -> None:
        """从配置加载工具"""
        # 从配置中获取工具列表
        tools_config = self.config.get('tools', [])

        for tool_config in tools_config:
            try:
                # 验证工具配置
                if not await self.validate_tool_config(tool_config):
                    # 静默处理错误，继续加载其他工具
                    continue

                tool = self.factory.create_tool(tool_config)
                await self.register_tool(tool)
            except ToolRegistrationError as e:
                # 工具注册错误，使用错误处理器
                context = create_tool_error_context(
                    tool_call=None,  # 注册时没有工具调用
                    tool_config=tool_config,
                    operation="registration"
                )
                handle_tool_error(e, context)
            except Exception as e:
                # 其他错误，包装为工具错误
                tool_error = ToolRegistrationError(f"加载工具失败: {str(e)}")
                context = create_tool_error_context(
                    tool_call=None,
                    tool_config=tool_config,
                    operation="loading"
                )
                handle_tool_error(tool_error, context)
    
    async def register_tool(self, tool: ITool) -> None:
        """注册工具

        Args:
            tool: 要注册的工具

        Raises:
            ToolRegistrationError: 工具注册失败
        """
        try:
            # 验证工具
            if not self._validate_tool(tool):
                raise ToolRegistrationError(f"工具验证失败: {tool.name}")

            # 检查是否已存在
            if tool.name in self._tools:
                # 工具已存在，将被覆盖
                pass

            self._tools[tool.name] = tool

        except Exception as e:
            if isinstance(e, ToolRegistrationError):
                raise
            else:
                raise ToolRegistrationError(f"注册工具失败: {tool.name}, 错误: {str(e)}") from e
    
    def _validate_tool(self, tool: ITool) -> bool:
        """验证工具"""
        try:
            # 检查基本属性
            if not tool.name or not tool.name.strip():
                return False

            if not tool.description or not tool.description.strip():
                return False

            if not tool.parameters_schema:
                return False

            # 检查参数模式格式
            if not isinstance(tool.parameters_schema, dict):
                return False

            return True

        except Exception:
            return False
    
    async def unregister_tool(self, name: str) -> None:
        """注销工具

        Args:
            name: 工具名称
        """
        if name in self._tools:
            del self._tools[name]
    
    async def get_tool(self, name: str, session_id: Optional[str] = None) -> Optional[ITool]:
        """获取工具

        Args:
            name: 工具名称
            session_id: 会话ID（用于有状态工具）

        Returns:
            Optional[ITool]: 工具实例，如果不存在则返回None
        """
        try:
            # 首先检查是否有活跃的会话工具
            if session_id and session_id in self._active_sessions:
                session_tools = self._active_sessions[session_id]
                if name in session_tools:
                    return session_tools[name]

            # 从工具存储中获取工具
            tool = self._tools.get(name)
            if tool is None:
                return None

            # 如果是需要会话的有状态工具，初始化会话
            if hasattr(tool, 'initialize_context') and session_id:
                try:
                    tool.initialize_context(session_id)

                    # 将工具添加到活跃会话中
                    if session_id not in self._active_sessions:
                        self._active_sessions[session_id] = {}
                    self._active_sessions[session_id][name] = tool
                except Exception:
                    # 仍然返回工具，但静默处理错误
                    pass

            return tool

        except Exception:
            return None
    
    async def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self._tools.keys())
    
    async def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """执行工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            context: 执行上下文
            
        Returns:
            Any: 工具执行结果
            
        Raises:
            ToolError: 工具执行失败
        """
        session_id = context.get('session_id') if context else None
        
        try:
            # 获取工具实例
            tool = await self.get_tool(name, session_id)
            if not tool:
                raise ToolError(f"工具不存在: {name}")
            
            # 验证参数
            if not tool.validate_parameters(arguments):
                raise ToolError(f"工具参数验证失败: {name}")
            
            # 执行工具
            try:
                if hasattr(tool, 'execute_async'):
                    return await tool.execute_async(**arguments)
                else:
                    return tool.execute(**arguments)
            except ToolError:
                # 重新抛出工具错误
                raise
            except Exception as e:
                # 包装其他异常
                raise ToolError(f"工具执行失败: {name}, 错误: {str(e)}") from e
                
        except ToolError:
            # 重新抛出工具错误
            raise
        except Exception as e:
            # 包装其他异常
            raise ToolError(f"执行工具失败: {name}, 错误: {str(e)}") from e
    
    async def reload_tools(self) -> None:
        """重新加载所有工具

        清除当前工具并重新加载配置中的工具。

        Raises:
            ToolError: 重载失败
        """
        try:
            # 清理所有活跃会话
            for session_id, session_tools in self._active_sessions.items():
                for tool in session_tools.values():
                    try:
                        if hasattr(tool, 'cleanup_context'):
                            tool.cleanup_context()
                    except Exception:
                        # 静默处理清理错误
                        pass

            self._active_sessions.clear()

            # 清空工具存储
            self._tools.clear()

            # 重新加载工具
            await self._load_tools_from_config()

        except Exception as e:
            raise ToolError(f"工具重载失败: {str(e)}") from e
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[Dict[str, Any]]: 工具信息，如果不存在则返回None
        """
        tool = self._tools.get(name)
        if not tool:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters_schema": tool.parameters_schema,
            "type": getattr(tool, '__class__', type(tool)).__name__
        }
    
    async def validate_tool_config(self, config: Any) -> bool:
        """验证工具配置

        Args:
            config: 工具配置（可以是ToolConfig对象或Dict）

        Returns:
            bool: 验证是否通过
        """
        try:
            # 将配置转换为字典形式（支持对象和字典）
            config_dict: Dict[str, Any]
            if isinstance(config, dict):
                config_dict = config
            else:
                # 如果是对象，转换为字典
                config_dict = {
                    "name": getattr(config, "name", None),
                    "tool_type": getattr(config, "tool_type", None),
                    "description": getattr(config, "description", None),
                    "parameters_schema": getattr(config, "parameters_schema", None),
                }

            # 基本验证
            required_fields = ["name", "tool_type", "description", "parameters_schema"]
            validation_errors = []

            for field in required_fields:
                if field not in config_dict or config_dict[field] is None:
                    validation_errors.append(f"缺少必需字段: {field}")

            if validation_errors:
                return False

            # 验证工具名称
            name = config_dict["name"]
            if not isinstance(name, str) or not name.strip():
                return False

            # 验证参数schema格式
            parameters_schema = config_dict["parameters_schema"]
            if not isinstance(parameters_schema, dict):
                return False

            # 验证工具类型
            tool_type = config_dict["tool_type"]
            valid_types = ["builtin", "native", "rest", "mcp"]
            if tool_type not in valid_types:
                return False

            # 针对不同工具类型进行特定验证
            if tool_type in ["builtin", "native"]:
                function_path = config_dict.get("function_path")
                if not function_path:
                    return False

                # 验证函数路径格式
                if not isinstance(function_path, str) or ':' not in function_path:
                    return False

            if tool_type == "rest":
                api_url = config_dict.get("api_url")
                if not api_url:
                    return False

                # 验证URL格式
                if not isinstance(api_url, str) or not api_url.startswith(('http://', 'https://')):
                    return False

                if tool_type == "mcp":
                    mcp_url = config_dict.get("mcp_server_url")
                    if not mcp_url:
                        return False

            if tool_type == "mcp":
                mcp_url = config_dict.get("mcp_server_url")
                if not mcp_url:
                    return False

                # 验证URL格式
                if not isinstance(mcp_url, str) or not mcp_url.startswith(('http://', 'https://', 'ws://', 'wss://')):
                    return False

            return True

        except Exception:
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话信息
        """
        if session_id not in self._active_sessions:
            return None
        
        session_tools = self._active_sessions[session_id]
        info = {
            'session_id': session_id,
            'tool_count': len(session_tools),
            'tools': {}
        }
        
        for name, tool in session_tools.items():
            if hasattr(tool, 'get_context_info'):
                context_info = tool.get_context_info()
                info['tools'][name] = {  # type: ignore
                    'context_info': context_info,
                    'type': type(tool).__name__
                }
            else:
                info['tools'][name] = {  # type: ignore
                    'type': type(tool).__name__
                }
        
        return info
    
    async def cleanup_session(self, session_id: str) -> None:
        """清理会话

        Args:
            session_id: 会话ID

        Raises:
            ToolError: 清理失败
        """
        try:
            if session_id not in self._active_sessions:
                return

            session_tools = self._active_sessions[session_id]

            # 清理所有工具的上下文
            cleanup_errors = []
            for tool_name, tool in session_tools.items():
                try:
                    if hasattr(tool, 'cleanup_context'):
                        tool.cleanup_context()
                except Exception as e:
                    cleanup_errors.append(f"{tool_name}: {str(e)}")

            # 删除会话
            del self._active_sessions[session_id]

        except Exception as e:
            raise ToolError(f"清理会话失败: {session_id}, 错误: {str(e)}") from e
    
    def get_all_sessions(self) -> List[str]:
        """获取所有活跃会话ID列表
        
        Returns:
            List[str]: 活跃会话ID列表
        """
        return list(self._active_sessions.keys())