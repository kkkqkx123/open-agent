"""
工具系统核心接口定义

定义了工具系统的核心业务接口和数据模型，确保模块间的松耦合设计。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Union, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..llm import ILLMClient
    from .config import ToolConfig
    from ..messages import IBaseMessage


@dataclass
class ToolCall:
    """工具调用请求"""

    name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None
    timeout: Optional[int] = None


@dataclass
class ToolResult:
    """工具执行结果"""

    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    tool_name: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ITool(ABC):
    """工具接口定义"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """参数Schema"""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """执行工具"""
        pass

    @abstractmethod
    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """获取参数模式"""
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        pass

    @abstractmethod
    def initialize_context(self, session_id: Optional[str] = None) -> Optional[str]:
        """初始化工具上下文"""
        pass

    @abstractmethod
    def cleanup_context(self) -> bool:
        """清理工具上下文"""
        pass

    @abstractmethod
    def get_context_info(self) -> Optional[Dict[str, Any]]:
        """获取上下文信息"""
        pass


class IToolRegistry(ABC):
    """工具注册表接口"""

    @abstractmethod
    def register_tool(self, tool: ITool) -> None:
        """注册工具"""
        pass

    @abstractmethod
    def get_tool(self, name: str) -> Optional[ITool]:
        """获取工具"""
        pass

    @abstractmethod
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        pass

    @abstractmethod
    def unregister_tool(self, name: str) -> bool:
        """注销工具"""
        pass


class IToolFormatter(ABC):
    """工具格式化器接口"""

    @abstractmethod
    def format_for_llm(self, tools: Sequence[ITool]) -> Dict[str, Any]:
        """将工具格式化为LLM可识别的格式"""
        pass

    @abstractmethod
    def detect_strategy(self, llm_client: "ILLMClient") -> str:
        """检测模型支持的输出策略"""
        pass

    @abstractmethod
    def parse_llm_response(self, response: "IBaseMessage") -> ToolCall:
        """解析LLM的工具调用响应"""
        pass

    def parse_llm_response_batch(self, response: "IBaseMessage") -> List[ToolCall]:
        """解析LLM的工具调用响应（批量）
        
        默认实现：调用单次解析并返回列表
        
        Args:
            response: LLM响应消息
            
        Returns:
            List[ToolCall]: 解析后的工具调用列表
        """
        try:
            tool_call = self.parse_llm_response(response)
            return [tool_call]
        except ValueError:
            return []


class IToolExecutor(ABC):
    """工具执行器接口"""

    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass

    @abstractmethod
    async def execute_async(self, tool_call: ToolCall) -> ToolResult:
        """异步执行工具调用"""
        pass

    @abstractmethod
    def execute_parallel(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """并行执行多个工具调用"""
        pass

    @abstractmethod
    async def execute_parallel_async(
        self, tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """异步并行执行多个工具调用"""
        pass


class IToolManager(ABC):
    """工具管理器接口
    
    定义工具管理器的核心功能，包括工具的注册、加载、执行和生命周期管理。
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化工具管理器
        
        加载配置中指定的所有工具。
        """
        pass
    
    @abstractmethod
    async def register_tool(self, tool: ITool) -> None:
        """注册工具
        
        Args:
            tool: 要注册的工具
        """
        pass
    
    @abstractmethod
    async def unregister_tool(self, name: str) -> None:
        """注销工具
        
        Args:
            name: 工具名称
        """
        pass
    
    @abstractmethod
    async def get_tool(self, name: str) -> Optional[ITool]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[ITool]: 工具实例，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def reload_tools(self) -> None:
        """重新加载所有工具
        
        清除当前工具并重新加载配置中的工具。
        """
        pass
    
    @abstractmethod
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[Dict[str, Any]]: 工具信息，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def validate_tool_config(self, config: "ToolConfig") -> bool:
        """验证工具配置
        
        Args:
            config: 工具配置
            
        Returns:
            bool: 验证是否通过
        """
        pass
    
    @property
    @abstractmethod
    def registry(self) -> IToolRegistry:
        """获取工具注册表"""
        pass
    
    # 移除不存在的loader属性
    # @property
    # @abstractmethod
    # def loader(self) -> "ToolLoader":
    #     """获取工具加载器"""
    #     pass
    
    @property
    @abstractmethod
    def factory(self) -> "IToolFactory":
        """获取工具工厂"""
        pass
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        pass


class IToolFactory(ABC):
    """工具工厂接口"""

    @abstractmethod
    def create_tool(self, tool_config: Dict[str, Any]) -> ITool:
        """创建工具实例"""
        pass

    @abstractmethod
    def register_tool_type(self, tool_type: str, tool_class: type) -> None:
        """注册工具类型"""
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的工具类型"""
        pass