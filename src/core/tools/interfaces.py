"""
工具系统核心接口定义

定义了工具系统的核心业务接口和数据模型，确保模块间的松耦合设计。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Union, TYPE_CHECKING
from dataclasses import dataclass

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.infrastructure.llm.interfaces import ILLMClient
from langchain_core.messages import BaseMessage  # type: ignore

if TYPE_CHECKING:
    from .base import BaseTool


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
    def get_schema(self) -> Dict[str, Any]:
        """获取参数模式"""
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
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
    def parse_llm_response(self, response: BaseMessage) -> ToolCall:
        """解析LLM的工具调用响应"""
        pass


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