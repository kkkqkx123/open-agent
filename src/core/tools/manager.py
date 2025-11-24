"""
工具管理器实现

支持新的工具类型层次结构的工具管理器。
"""

import asyncio
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging

from src.interfaces.tool.base import ITool, IToolManager, IToolFactory
from .factory import OptimizedToolFactory

if TYPE_CHECKING:
    from .config import ToolConfig


logger = logging.getLogger(__name__)


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
        logger.info("ToolManager初始化完成")
    
    async def _load_tools_from_config(self) -> None:
        """从配置加载工具"""
        # 从配置中获取工具列表
        tools_config = self.config.get('tools', [])
        
        for tool_config in tools_config:
            try:
                tool = self.factory.create_tool(tool_config)
                await self.register_tool(tool)
                logger.info(f"成功加载工具: {tool.name}")
            except Exception as e:
                logger.error(f"加载工具失败: {tool_config.get('name', 'Unknown')}, 错误: {e}")
    
    async def register_tool(self, tool: ITool) -> None:
        """注册工具
        
        Args:
            tool: 要注册的工具
        """
        self._tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name}")
    
    async def unregister_tool(self, name: str) -> None:
        """注销工具
        
        Args:
            name: 工具名称
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"注销工具: {name}")
    
    async def get_tool(self, name: str, session_id: Optional[str] = None) -> Optional[ITool]:
        """获取工具
        
        Args:
            name: 工具名称
            session_id: 会话ID（用于有状态工具）
            
        Returns:
            Optional[ITool]: 工具实例，如果不存在则返回None
        """
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
            tool.initialize_context(session_id)
            
            # 将工具添加到活跃会话中
            if session_id not in self._active_sessions:
                self._active_sessions[session_id] = {}
            self._active_sessions[session_id][name] = tool
        
        return tool
    
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
        """
        session_id = context.get('session_id') if context else None
        
        # 获取工具实例
        tool = await self.get_tool(name, session_id)
        if not tool:
            raise ValueError(f"工具不存在: {name}")
        
        # 执行工具
        try:
            if hasattr(tool, 'execute_async'):
                return await tool.execute_async(**arguments)
            else:
                return tool.execute(**arguments)
        except Exception as e:
            logger.error(f"执行工具失败: {name}, 错误: {e}")
            raise
    
    async def reload_tools(self) -> None:
        """重新加载所有工具
        
        清除当前工具并重新加载配置中的工具。
        """
        # 清理所有活跃会话
        for session_id, session_tools in self._active_sessions.items():
            for tool in session_tools.values():
                if hasattr(tool, 'cleanup_context'):
                    tool.cleanup_context()
        
        self._active_sessions.clear()
        
        # 清空工具存储
        self._tools.clear()
        
        # 重新加载工具
        await self._load_tools_from_config()
        
        logger.info("工具重载完成")
    
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
            for field in required_fields:
                if field not in config_dict or config_dict[field] is None:
                    logger.error(f"工具配置缺少必需字段: {field}")
                    return False
            
            # 验证参数schema格式
            parameters_schema = config_dict["parameters_schema"]
            if not isinstance(parameters_schema, dict):
                logger.error("参数schema必须是字典格式")
                return False
            
            # 验证工具类型
            tool_type = config_dict["tool_type"]
            valid_types = ["builtin", "native", "rest", "mcp"]
            if tool_type not in valid_types:
                logger.error(f"无效的工具类型: {tool_type}")
                return False
            
            # 针对不同工具类型进行特定验证
            if tool_type in ["builtin", "native"]:
                if "function_path" not in config_dict or not getattr(config, "function_path", None) if not isinstance(config, dict) else config_dict.get("function_path"):
                    logger.error(f"{tool_type}工具必须包含function_path")
                    return False
            
            if tool_type in ["rest", "mcp"]:
                if tool_type == "rest":
                    api_url = config_dict.get("api_url") if isinstance(config, dict) else getattr(config, "api_url", None)
                    if not api_url:
                        logger.error("REST工具必须包含api_url")
                        return False
                
                if tool_type == "mcp":
                    mcp_url = config_dict.get("mcp_server_url") if isinstance(config, dict) else getattr(config, "mcp_server_url", None)
                    if not mcp_url:
                        logger.error("MCP工具必须包含mcp_server_url")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"工具配置验证失败: {e}")
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
                info['tools'][name] = {
                    'context_info': context_info,
                    'type': type(tool).__name__
                }
            else:
                info['tools'][name] = {
                    'type': type(tool).__name__
                }
        
        return info
    
    async def cleanup_session(self, session_id: str) -> None:
        """清理会话
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._active_sessions:
            session_tools = self._active_sessions[session_id]
            
            # 清理所有工具的上下文
            for tool in session_tools.values():
                if hasattr(tool, 'cleanup_context'):
                    tool.cleanup_context()
            
            # 删除会话
            del self._active_sessions[session_id]
            
            logger.info(f"清理会话: {session_id}")
    
    def get_all_sessions(self) -> List[str]:
        """获取所有活跃会话ID列表
        
        Returns:
            List[str]: 活跃会话ID列表
        """
        return list(self._active_sessions.keys())