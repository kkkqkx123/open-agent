"""Agent状态定义

定义了Agent执行过程中使用的状态结构，与WorkflowState解耦。
"""

from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict
from datetime import datetime
from enum import Enum

from ..tools.interfaces import ToolResult


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentMessage:
    """Agent消息"""
    content: str
    role: str
    timestamp: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Agent状态定义
    
    独立于WorkflowState的Agent状态，专注于Agent的执行过程。
    """
    # 基本标识信息
    agent_id: str = ""
    agent_type: str = ""
    
    # 消息相关
    messages: List[AgentMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # 任务相关
    current_task: Optional[str] = None
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 工具执行结果
    tool_results: List[ToolResult] = field(default_factory=list)
    
    # 控制信息
    current_step: str = ""
    max_iterations: int = 10
    iteration_count: int = 0
    status: AgentStatus = AgentStatus.IDLE
    
    # 时间信息
    start_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = field(default_factory=datetime.now)
    
    # 错误和日志
    errors: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # 性能指标
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 自定义字段
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: AgentMessage) -> None:
        """添加消息"""
        self.messages.append(message)
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
    
    def set_status(self, status: AgentStatus) -> None:
        """设置Agent状态"""
        self.status = status
        if status == AgentStatus.THINKING and self.start_time is None:
            self.start_time = datetime.now()
        elif status in [AgentStatus.COMPLETED, AgentStatus.ERROR]:
            # 可以在这里添加完成时间记录
            pass
        self._update_timestamp()
    
    def get_last_message(self) -> Optional[AgentMessage]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None
    
    def has_tool_calls(self) -> bool:
        """检查是否有工具调用"""
        last_message = self.get_last_message()
        if last_message and "tool_calls" in last_message.metadata:
            return bool(last_message.metadata["tool_calls"])
        return False
    
    def get_execution_duration(self) -> Optional[float]:
        """获取执行持续时间（秒）"""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    def is_max_iterations_reached(self) -> bool:
        """检查是否达到最大迭代次数"""
        return self.iteration_count >= self.max_iterations
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "messages": [
                {
                    "content": msg.content,
                    "role": msg.role,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "metadata": msg.metadata
                }
                for msg in self.messages
            ],
            "context": self.context,
            "current_task": self.current_task,
            "task_history": self.task_history,
            "tool_results": [result.__dict__ for result in self.tool_results],
            "current_step": self.current_step,
            "max_iterations": self.max_iterations,
            "iteration_count": self.iteration_count,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None,
            "errors": self.errors,
            "logs": self.logs,
            "execution_metrics": self.execution_metrics,
            "custom_fields": self.custom_fields
        }
    
    def _update_timestamp(self) -> None:
        """更新最后更新时间"""
        self.last_update_time = datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """从字典创建AgentState"""
        agent_state = cls()
        
        # 基本信息
        agent_state.agent_id = data.get("agent_id", "")
        agent_state.agent_type = data.get("agent_type", "")
        
        # 消息
        for msg_data in data.get("messages", []):
            message = AgentMessage(
                content=msg_data.get("content", ""),
                role=msg_data.get("role", ""),
                timestamp=datetime.fromisoformat(msg_data["timestamp"]) if msg_data.get("timestamp") else None,
                metadata=msg_data.get("metadata", {})
            )
            agent_state.messages.append(message)
        
        # 其他字段
        agent_state.context = data.get("context", {})
        agent_state.current_task = data.get("current_task")
        agent_state.task_history = data.get("task_history", [])
        agent_state.current_step = data.get("current_step", "")
        agent_state.max_iterations = data.get("max_iterations", 10)
        agent_state.iteration_count = data.get("iteration_count", 0)
        agent_state.status = AgentStatus(data.get("status", "idle"))
        
        # 时间信息
        if data.get("start_time"):
            agent_state.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("last_update_time"):
            agent_state.last_update_time = datetime.fromisoformat(data["last_update_time"])
        
        # 错误和日志
        agent_state.errors = data.get("errors", [])
        agent_state.logs = data.get("logs", [])
        
        # 性能指标和自定义字段
        agent_state.execution_metrics = data.get("execution_metrics", {})
        agent_state.custom_fields = data.get("custom_fields", {})
        
        return agent_state