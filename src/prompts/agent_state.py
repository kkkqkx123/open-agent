"""Agent状态定义"""

from dataclasses import dataclass, field
from typing import List, Any, Optional

# Define BaseMessage for fallback when LangChain is not available
@dataclass
class BaseMessage:
    content: str
    type: str = "base"


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None


@dataclass
class AgentState:
    """Agent状态定义"""
    messages: List[object] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    current_step: str = ""
    max_iterations: int = 10
    
    def add_message(self, message: object) -> None:
        """添加消息"""
        self.messages.append(message)


try:
    from langchain_core.messages import SystemMessage, HumanMessage  # type: ignore
except ImportError:
    # 如果LangChain不可用，定义简单的消息类
    @dataclass
    class SystemMessage(BaseMessage):
        type: str = "system"

    @dataclass
    class HumanMessage(BaseMessage):
        type: str = "human"