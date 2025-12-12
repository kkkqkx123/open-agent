"""
工具管理服务

提供工具的注册、加载、执行和管理功能。
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from src.interfaces.dependency_injection import get_logger

from src.interfaces.tool.base import ITool, IToolRegistry, IToolManager
from src.interfaces.tool.config import ToolConfig as InterfaceToolConfig
from src.core.tools.factory import OptimizedToolFactory as ToolFactory
from src.core.config.models.tool_config import ToolRegistryConfig
from src.interfaces.tool.exceptions import ToolError

if TYPE_CHECKING:
    from src.interfaces.tool.config import ToolConfig

logger = get_logger(__name__)


class ToolManager(IToolManager):
    """工具管理器实现
    
    负责工具的注册、加载、执行和生命周期管理。
    """
    
    def __init__(
        self,
        registry: IToolRegistry,
        factory: ToolFactory,
        config: Optional[ToolRegistryConfig] = None
    ) -> None:
        """初始化工具管理器
        
        Args:
            registry: 工具注册表
            factory: 工具工厂
            config: 工具注册表配置
        """
        self._registry = registry
        self._factory = factory
        self._config = config or ToolRegistryConfig()
        self._tools: Dict[str, ITool] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化工具管理器
        
        加载配置中指定的所有工具。
        """
        if self._initialized:
            return
        
        logger.info("初始化工具管理器...")
        
        try:
            # 加载工具
            await self._load_tools_from_config()
            
            self._initialized = True
            logger.info(f"工具管理器初始化完成，加载了 {len(self._tools)} 个工具")
            
        except Exception as e:
            logger.error(f"工具管理器初始化失败: {e}")
            raise ToolError(f"工具管理器初始化失败: {e}")
    
    async def register_tool(self, tool: ITool) -> None:
        """注册工具
        
        Args:
            tool: 要注册的工具
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            self._registry.register_tool(tool)
            self._tools[tool.name] = tool
            logger.debug(f"工具 {tool.name} 注册成功")
            
        except Exception as e:
            logger.error(f"工具 {tool.name} 注册失败: {e}")
            raise ToolError(f"工具 {tool.name} 注册失败: {e}")
    
    async def unregister_tool(self, name: str) -> None:
        """注销工具
        
        Args:
            name: 工具名称
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            self._registry.unregister_tool(name)
            if name in self._tools:
                del self._tools[name]
            logger.debug(f"工具 {name} 注销成功")
            
        except Exception as e:
            logger.error(f"工具 {name} 注销失败: {e}")
            raise ToolError(f"工具 {name} 注销失败: {e}")
    
    async def get_tool(self, name: str) -> Optional[ITool]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[ITool]: 工具实例，如果不存在则返回None
        """
        if not self._initialized:
            await self.initialize()
        
        return self._tools.get(name)
    
    async def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        if not self._initialized:
            await self.initialize()
        
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
            ServiceError: 工具执行失败
        """
        if not self._initialized:
            await self.initialize()
        
        tool = self._tools.get(name)
        if not tool:
            raise ToolError(f"工具 {name} 未找到")
        
        try:
            logger.debug(f"执行工具 {name}，参数: {arguments}")
            result = tool.execute(arguments=arguments, context=context)
            logger.debug(f"工具 {name} 执行成功")
            return result
            
        except Exception as e:
            logger.error(f"工具 {name} 执行失败: {e}")
            raise ToolError(f"工具 {name} 执行失败: {e}")
    
    async def reload_tools(self) -> None:
        """重新加载所有工具
        
        清除当前工具并重新加载配置中的工具。
        """
        logger.info("重新加载工具...")
        
        try:
            # 清除当前工具
            self._tools.clear()
            
            # 重新初始化
            self._initialized = False
            await self.initialize()
            
            logger.info("工具重新加载完成")
            
        except Exception as e:
            logger.error(f"工具重新加载失败: {e}")
            raise ToolError(f"工具重新加载失败: {e}")
    
    async def _load_tools_from_config(self) -> None:
        """从配置加载工具"""
        if not self._config.tools:
            logger.info("配置中没有指定工具")
            return
        
        for tool_config in self._config.tools:
            try:
                # tool_config 现在已经是字典格式
                config_dict: Dict[str, Any] = tool_config  # type: ignore
                tool = self._factory.create_tool(config_dict)
                if tool:
                    await self.register_tool(tool)
                    
            except Exception as e:
                tool_name = tool_config.get('name', 'unknown') if isinstance(tool_config, dict) else 'unknown'
                logger.error(f"加载工具 {tool_name} 失败: {e}")
                # 非严格模式下，跳过失败的工具
                continue
    
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
            "schema": tool.get_schema(),
            "type": tool.__class__.__name__,
        }
    
    async def validate_tool_config(self, config: "ToolConfig") -> bool:
        """验证工具配置（委托给验证服务）
        
        Args:
            config: 工具配置对象
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 委托给验证服务进行验证
            # 这里应该通过依赖注入获取验证服务
            # 暂时通过工厂创建工具来验证
            config_dict: Dict[str, Any] = config.to_dict()  # type: ignore
            tool = self._factory.create_tool(config_dict)
            return tool is not None
            
        except Exception as e:
            logger.error(f"工具配置验证失败: {e}")
            return False
    
    @property
    def registry(self) -> IToolRegistry:
        """获取工具注册表"""
        return self._registry
    

    
    @property
    def factory(self) -> ToolFactory:
        """获取工具工厂"""
        return self._factory
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized