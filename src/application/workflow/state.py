"""工作流状态定义

重构后的状态管理系统，提供更清晰的状态定义和类型安全。
"""

from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict, TYPE_CHECKING, Union
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from src.domain.agent.config import AgentConfig


class WorkflowStatus(Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    HUMAN = "human"
    AI = "ai"
    TOOL = "tool"


@dataclass
class BaseMessage:
    """基础消息类"""
    content: str
    role: MessageRole
    type: str = "base"
    timestamp: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "role": self.role.value,
            "type": self.type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata
        }


@dataclass
class SystemMessage(BaseMessage):
    """系统消息"""
    role: MessageRole = MessageRole.SYSTEM
    type: str = "system"


@dataclass
class HumanMessage(BaseMessage):
    """人类消息"""
    role: MessageRole = MessageRole.HUMAN
    type: str = "human"
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class AIMessage(BaseMessage):
    """AI消息"""
    role: MessageRole = MessageRole.AI
    type: str = "ai"
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ToolMessage(BaseMessage):
    """工具消息"""
    role: MessageRole = MessageRole.TOOL
    type: str = "tool"
    tool_call_id: str = ""
    tool_name: str = ""


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


@dataclass
class WorkflowState:
    """工作流状态定义
    
    重构后的工作流状态，提供更清晰的结构和类型安全。
    """
    # 基本标识信息
    workflow_id: str = ""
    workflow_name: str = ""
    execution_id: str = ""
    
    # Agent相关状态
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
    
    # 工作流控制参数
    current_step: str = ""
    max_iterations: int = 10
    iteration_count: int = 0
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    # 时间信息
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = field(default_factory=datetime.now)
    
    # 错误和日志
    errors: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # 性能指标
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 自定义字段
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: BaseMessage) -> None:
        """添加消息"""
        self.messages.append(message)
        self._update_timestamp()
    
    def add_memory(self, message: BaseMessage) -> None:
        """添加记忆"""
        self.memory.append(message)
        self._update_timestamp()
    
    def add_tool_result(self, result: ToolResult) -> None:
        """添加工具执行结果"""
        self.tool_results.append(result)
        self._update_timestamp()
    
    def add_log(self, log: Dict[str, Any]) -> None:
        """添加日志"""
        log["timestamp"] = datetime.now().isoformat()
        self.logs.append(log)
        self._update_timestamp()
    
    def add_error(self, error: Dict[str, Any]) -> None:
        """添加错误"""
        error["timestamp"] = datetime.now().isoformat()
        self.errors.append(error)
        self._update_timestamp()
    
    def increment_iteration(self) -> None:
        """增加迭代计数"""
        self.iteration_count += 1
        self._update_timestamp()
    
    def set_status(self, status: WorkflowStatus) -> None:
        """设置工作流状态"""
        self.status = status
        if status == WorkflowStatus.RUNNING and self.start_time is None:
            self.start_time = datetime.now()
        elif status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            self.end_time = datetime.now()
        self._update_timestamp()
    
    def get_last_message(self) -> Optional[BaseMessage]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None
    
    def get_messages_by_role(self, role: MessageRole) -> List[BaseMessage]:
        """根据角色获取消息"""
        return [msg for msg in self.messages if msg.role == role]
    
    def has_tool_calls(self) -> bool:
        """检查是否有工具调用"""
        last_message = self.get_last_message()
        if isinstance(last_message, (HumanMessage, AIMessage)) and last_message.tool_calls:
            return bool(last_message.tool_calls)
        return False
    
    def get_execution_duration(self) -> Optional[float]:
        """获取执行持续时间（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    def is_max_iterations_reached(self) -> bool:
        """检查是否达到最大迭代次数"""
        return self.iteration_count >= self.max_iterations
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "execution_id": self.execution_id,
            "agent_id": self.agent_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "memory": [msg.to_dict() for msg in self.memory],
            "context": self.context,
            "current_task": self.current_task,
            "task_history": self.task_history,
            "tool_results": [result.to_dict() for result in self.tool_results],
            "current_step": self.current_step,
            "max_iterations": self.max_iterations,
            "iteration_count": self.iteration_count,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None,
            "errors": self.errors,
            "logs": self.logs,
            "execution_metrics": self.execution_metrics,
            "custom_fields": self.custom_fields
        }
    
    def _update_timestamp(self) -> None:
        """更新最后更新时间"""
        self.last_update_time = datetime.now()


# 为了向后兼容，保留AgentState别名
AgentState = WorkflowState


# 消息类型检查函数
def create_message(content: str, role: MessageRole, **kwargs) -> BaseMessage:
    """创建消息的工厂函数"""
    if role == MessageRole.SYSTEM:
        return SystemMessage(content=content, **kwargs)
    elif role == MessageRole.HUMAN:
        return HumanMessage(content=content, **kwargs)
    elif role == MessageRole.AI:
        return AIMessage(content=content, **kwargs)
    elif role == MessageRole.TOOL:
        return ToolMessage(content=content, **kwargs)
    else:
        return BaseMessage(content=content, role=role, **kwargs)


# 兼容LangChain消息类型的适配器
def adapt_langchain_message(message: Any) -> BaseMessage:
    """适配LangChain消息类型"""
    try:
        from langchain_core.messages import SystemMessage as LCSystemMessage, HumanMessage as LCHumanMessage, AIMessage as LCAIMessage
        if isinstance(message, LCSystemMessage):
            return SystemMessage(content=str(message.content))
        elif isinstance(message, LCHumanMessage):
            return HumanMessage(content=str(message.content), tool_calls=getattr(message, 'tool_calls', None))
        elif isinstance(message, LCAIMessage):
            return AIMessage(content=str(message.content), tool_calls=getattr(message, 'tool_calls', None))
        else:
            # 默认作为人类消息处理
            return HumanMessage(content=str(message))
    except ImportError:
        # 如果LangChain不可用，使用基础消息类型
        return HumanMessage(content=str(message))