"""
工具系统核心接口定义

定义了工具管理、格式化和执行的核心接口，确保模块间的松耦合设计。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Union, TYPE_CHECKING
from dataclasses import dataclass

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...infrastructure.llm.interfaces import ILLMClient
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


class IToolManager(ABC):
    """工具管理器接口"""

    @abstractmethod
    def load_tools(self) -> List["BaseTool"]:
        """加载所有可用工具

        Returns:
            List[BaseTool]: 已加载的工具列表
        """
        pass

    @abstractmethod
    def get_tool(self, name: str) -> "BaseTool":
        """根据名称获取工具

        Args:
            name: 工具名称

        Returns:
            BaseTool: 工具实例

        Raises:
            ValueError: 工具不存在
        """
        pass

    @abstractmethod
    def get_tool_set(self, name: str) -> List["BaseTool"]:
        """获取工具集

        Args:
            name: 工具集名称

        Returns:
            List[BaseTool]: 工具集中的工具列表

        Raises:
            ValueError: 工具集不存在
        """
        pass

    @abstractmethod
    def register_tool(self, tool: "BaseTool") -> None:
        """注册新工具

        Args:
            tool: 工具实例

        Raises:
            ValueError: 工具名称已存在
        """
        pass

    @abstractmethod
    def list_tools(self) -> List[str]:
        """列出所有可用工具名称

        Returns:
            List[str]: 工具名称列表
        """
        pass

    @abstractmethod
    def list_tool_sets(self) -> List[str]:
        """列出所有可用工具集名称

        Returns:
            List[str]: 工具集名称列表
        """
        pass


class IToolFormatter(ABC):
    """工具格式化器接口"""

    @abstractmethod
    def format_for_llm(self, tools: Sequence["BaseTool"]) -> Dict[str, Any]:
        """将工具格式化为LLM可识别的格式

        Args:
            tools: 工具列表

        Returns:
            Dict[str, Any]: 格式化后的工具描述
        """
        pass

    @abstractmethod
    def detect_strategy(self, llm_client: "ILLMClient") -> str:
        """检测模型支持的输出策略

        Args:
            llm_client: LLM客户端实例

        Returns:
            str: 策略类型 ("function_calling" 或 "structured_output")
        """
        pass

    @abstractmethod
    def parse_llm_response(self, response: BaseMessage) -> ToolCall:
        """解析LLM的工具调用响应

        Args:
            response: LLM响应消息

        Returns:
            ToolCall: 解析后的工具调用

        Raises:
            ValueError: 响应格式不正确
        """
        pass


class IToolExecutor(ABC):
    """工具执行器接口"""

    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用

        Args:
            tool_call: 工具调用请求

        Returns:
            ToolResult: 执行结果
        """
        pass

    @abstractmethod
    async def execute_async(self, tool_call: ToolCall) -> ToolResult:
        """异步执行工具调用

        Args:
            tool_call: 工具调用请求

        Returns:
            ToolResult: 执行结果
        """
        pass

    @abstractmethod
    def execute_parallel(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """并行执行多个工具调用

        Args:
            tool_calls: 工具调用请求列表

        Returns:
            List[ToolResult]: 执行结果列表
        """
        pass

    @abstractmethod
    async def execute_parallel_async(
        self, tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """异步并行执行多个工具调用

        Args:
            tool_calls: 工具调用请求列表

        Returns:
            List[ToolResult]: 执行结果列表
        """
        pass
