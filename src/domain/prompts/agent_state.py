"""Agent状态定义"""

from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.domain.agent.config import AgentConfig

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
    # Agent特定状态
    agent_id: str = ""
    agent_config: Optional['AgentConfig'] = None
    
    # 消息相关
    messages: List[BaseMessage] = field(default_factory=list)
    memory: List[BaseMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # 任务相关
    current_task: Optional[str] = None
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 工具执行结果
    tool_results: List[ToolResult] = field(default_factory=list)
    
    # 控制参数
    current_step: str = ""
    max_iterations: int = 10
    iteration_count: int = 0
    workflow_name: str = ""
    start_time: Optional[datetime] = None
    
    # 错误和日志
    errors: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_message(self, message: BaseMessage) -> None:
        """添加消息"""
        self.messages.append(message)
    
    def add_memory(self, message: BaseMessage) -> None:
        """添加记忆"""
        self.memory.append(message)
    
    def add_log(self, log: Dict[str, Any]) -> None:
        """添加日志"""
        self.logs.append(log)
    
    def add_error(self, error: Dict[str, Any]) -> None:
        """添加错误"""
        self.errors.append(error)


# 定义消息类型别名
if TYPE_CHECKING:
    try:
        from langchain_core.messages import SystemMessage as _SystemMessage, HumanMessage as _HumanMessage
        SystemMessage: type = _SystemMessage
        HumanMessage: type = _HumanMessage
    except ImportError:
        SystemMessage: type = None # type: ignore
        HumanMessage: type = None  # type: ignore
else:
    try:
        from langchain_core.messages import SystemMessage as _SystemMessage, HumanMessage as _HumanMessage  # type: ignore
        SystemMessage = _SystemMessage
        HumanMessage = _HumanMessage
    except ImportError:
        # 如果LangChain不可用，定义简单的消息类
        @dataclass
        class SystemMessage(BaseMessage):
            type: str = "system"

        @dataclass
        class HumanMessage(BaseMessage):
            type: str = "human"
            tool_calls: Optional[List[Dict[str, Any]]] = None