"""工作流状态实现

基于BaseState实现的工作流状态。
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Import LangChain message types - core dependency
from langchain_core.messages import (
    BaseMessage as LCBaseMessage,
    HumanMessage as LCHumanMessage,
    AIMessage as LCAIMessage,
    SystemMessage as LCSystemMessage,
    ToolMessage as LCToolMessage,
)

from src.interfaces.state.workflow import IWorkflowState
from .state_base import BaseState
from .message_base import (
    BaseMessage, HumanMessage, AIMessage, 
    SystemMessage, ToolMessage, MessageRole
)


class WorkflowState(BaseModel, IWorkflowState):
    """工作流状态实现
    
    基于BaseState和IWorkflowState接口的具体实现。
    """
    # 基础字段
    messages: List[Union[BaseMessage, LCBaseMessage]] = Field(default_factory=list)
    values: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    thread_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    iteration_count: int = 0
    current_node: Optional[str] = None
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 从旧架构迁移的字段
    input: Optional[str] = None
    output: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    max_iterations: int = 10
    errors: List[str] = Field(default_factory=list)
    complete: bool = False
    agent_id: str = ""
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    execution_result: Optional[Dict[str, Any]] = None
    workflow_id: str = ""
    workflow_name: str = ""
    workflow_config: Dict[str, Any] = Field(default_factory=dict)
    current_graph: str = ""
    analysis: Optional[str] = None
    decision: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    graph_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self) -> None:
        """初始化工作流状态"""
        super().__init__()
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._created_at: datetime = datetime.now()
        self._updated_at: datetime = datetime.now()
        self._id: Optional[str] = None
        self._complete: bool = False

    # IState interface implementation
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取状态数据"""
        return self.get_value(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置状态数据"""
        self.set_value(key, value)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self.metadata[key] = value
        self.updated_at = datetime.now()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        return self.thread_id or self.session_id
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self.thread_id = id
        self.session_id = id
        self.updated_at = datetime.now()
    
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        return self.created_at
    
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        return self.updated_at
    
    def is_complete(self) -> bool:
        """检查是否完成"""
        return self.complete
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self.complete = True
        self.end_time = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        # 处理消息列表，支持自定义消息和LangChain消息
        messages_data = []
        for msg in self.messages:
            if isinstance(msg, BaseMessage):
                # 自定义消息类型
                messages_data.append(msg.to_dict())
            elif hasattr(msg, 'content'):
                # LangChain消息类型
                messages_data.append({
                    "content": msg.content,
                    "role": getattr(msg, 'type', 'unknown')
                })
            else:
                # 未知消息类型
                messages_data.append({
                    "content": str(msg),
                    "role": "unknown"
                })
        
        return {
            "messages": messages_data,
            "values": self.values,
            "metadata": self.metadata,
            "thread_id": self.thread_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "iteration_count": self.iteration_count,
            "current_node": self.current_node,
            "execution_history": self.execution_history,
            "input": self.input,
            "output": self.output,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "max_iterations": self.max_iterations,
            "errors": self.errors,
            "complete": self.complete,
            "agent_id": self.agent_id,
            "agent_config": self.agent_config,
            "execution_result": self.execution_result,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_config": self.workflow_config,
            "current_graph": self.current_graph,
            "analysis": self.analysis,
            "decision": self.decision,
            "context": self.context,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "graph_states": self.graph_states,
            "custom_fields": self.custom_fields,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """从字典创建状态"""
        created_at_str = data.get("created_at")
        updated_at_str = data.get("updated_at")
        start_time_str = data.get("start_time")
        end_time_str = data.get("end_time")
        
        # 重建消息列表
        messages: List[Union[BaseMessage, LCBaseMessage]] = []
        for msg_data in data.get("messages", []):
            role = msg_data.get("role", "unknown")
            content = msg_data.get("content", "")
            
            if role == MessageRole.HUMAN:
                messages.append(HumanMessage(content=content))
            elif role == MessageRole.AI:
                messages.append(AIMessage(content=content))
            elif role == MessageRole.SYSTEM:
                messages.append(SystemMessage(content=content))
            elif role == MessageRole.TOOL:
                tool_call_id = msg_data.get("tool_call_id", "")
                messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
            else:
                messages.append(BaseMessage(content=content, role=role))
        
        instance = cls()
        instance.messages = messages
        instance.values = data.get("values", {})
        instance.metadata = data.get("metadata", {})
        instance.thread_id = data.get("thread_id")
        instance.session_id = data.get("session_id")
        instance.created_at = datetime.fromisoformat(created_at_str) if isinstance(created_at_str, str) else datetime.now()
        instance.updated_at = datetime.fromisoformat(updated_at_str) if isinstance(updated_at_str, str) else datetime.now()
        instance.iteration_count = data.get("iteration_count", 0)
        instance.current_node = data.get("current_node")
        instance.execution_history = data.get("execution_history", [])
        instance.input = data.get("input")
        instance.output = data.get("output")
        instance.tool_calls = data.get("tool_calls", [])
        instance.tool_results = data.get("tool_results", [])
        instance.max_iterations = data.get("max_iterations", 10)
        instance.errors = data.get("errors", [])
        instance.complete = data.get("complete", False)
        instance.agent_id = data.get("agent_id", "")
        instance.agent_config = data.get("agent_config", {})
        instance.execution_result = data.get("execution_result")
        instance.workflow_id = data.get("workflow_id", "")
        instance.workflow_name = data.get("workflow_name", "")
        instance.workflow_config = data.get("workflow_config", {})
        instance.current_graph = data.get("current_graph", "")
        instance.analysis = data.get("analysis")
        instance.decision = data.get("decision")
        instance.context = data.get("context", {})
        instance.start_time = datetime.fromisoformat(start_time_str) if isinstance(start_time_str, str) else datetime.now()
        instance.end_time = datetime.fromisoformat(end_time_str) if isinstance(end_time_str, str) else None
        instance.graph_states = data.get("graph_states", {})
        instance.custom_fields = data.get("custom_fields", {})
        
        return instance
    
    def clone(self) -> "WorkflowState":
        """克隆状态"""
        return self.from_dict(self.to_dict())
    
    def merge(self, other: "WorkflowState") -> None:
        """合并另一个状态"""
        self.messages.extend(other.messages)
        self.values.update(other.values)
        self.metadata.update(other.metadata)
        self.tool_calls.extend(other.tool_calls)
        self.tool_results.extend(other.tool_results)
        self.errors.extend(other.errors)
        self.execution_history.extend(other.execution_history)
        self.graph_states.update(other.graph_states)
        self.custom_fields.update(other.custom_fields)
        
        # Update non-mergeable fields if they are set in the other state
        if other.input is not None:
            self.input = other.input
        if other.output is not None:
            self.output = other.output
        if other.current_node is not None:
            self.current_node = other.current_node
        if other.execution_result is not None:
            self.execution_result = other.execution_result
        if other.analysis is not None:
            self.analysis = other.analysis
        if other.decision is not None:
            self.decision = other.decision
        if other.end_time is not None:
            self.end_time = other.end_time
        
        self.updated_at = datetime.now()

    # IWorkflowState interface implementation
    def get_messages(self) -> List[Union[BaseMessage, LCBaseMessage]]:
        """获取工作流状态中的消息列表"""
        return self.messages
    
    def add_message(self, message: Union[BaseMessage, LCBaseMessage]) -> None:
        """向工作流状态添加消息"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_last_message(self) -> Optional[Union[BaseMessage, LCBaseMessage]]:
        """获取工作流状态中的最后一条消息"""
        return self.messages[-1] if self.messages else None
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """从状态获取值"""
        return self.values.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """在状态中设置值"""
        self.values[key] = value
        self.updated_at = datetime.now()
    
    def get_current_node(self) -> Optional[str]:
        """获取工作流中的当前节点"""
        return self.current_node
    
    def set_current_node(self, node: str) -> None:
        """设置工作流中的当前节点"""
        self.current_node = node
        self.updated_at = datetime.now()
    
    def get_iteration_count(self) -> int:
        """获取当前迭代次数"""
        return self.iteration_count
    
    def increment_iteration(self) -> None:
        """增加迭代次数"""
        self.iteration_count += 1
        self.updated_at = datetime.now()
    
    def get_thread_id(self) -> Optional[str]:
        """获取线程ID"""
        return self.thread_id
    
    def set_thread_id(self, thread_id: str) -> None:
        """设置线程ID"""
        self.thread_id = thread_id
        self.updated_at = datetime.now()
    
    def get_session_id(self) -> Optional[str]:
        """获取会话ID"""
        return self.session_id
    
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID"""
        self.session_id = session_id
        self.updated_at = datetime.now()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取数据（向后兼容）"""
        # First check in values, then check in common fields
        if key in self.values:
            return self.values[key]
        
        # Check common fields
        if key == "current_step" or key == "current_node":
            return self.current_node
        elif key == "iteration_count":
            return self.iteration_count
        elif key == "messages":
            return self.messages
        elif key == "thread_id":
            return self.thread_id
        elif key == "session_id":
            return self.session_id
        elif key == "input":
            return self.input
        elif key == "output":
            return self.output
        elif key == "errors":
            return self.errors
        elif key == "complete":
            return self.complete
        elif key == "workflow_id":
            return self.workflow_id
        elif key == "workflow_name":
            return self.workflow_name
        elif key == "agent_id":
            return self.agent_id
        elif key == "analysis":
            return self.analysis
        elif key == "decision":
            return self.decision
        elif key == "context":
            return self.context
        elif key == "tool_calls":
            return self.tool_calls
        elif key == "tool_results":
            return self.tool_results
        elif key == "execution_result":
            return self.execution_result
        elif key == "graph_states":
            return self.graph_states
        elif key == "custom_fields":
            return self.custom_fields
        elif key == "metadata":
            return self.metadata
        elif key == "execution_history":
            return self.execution_history
        elif key == "start_time":
            return self.start_time
        elif key == "end_time":
            return self.end_time
        elif key == "created_at":
            return self.created_at
        elif key == "updated_at":
            return self.updated_at
        elif key == "max_iterations":
            return self.max_iterations
        elif key == "agent_config":
            return self.agent_config
        elif key == "workflow_config":
            return self.workflow_config
        elif key == "current_graph":
            return self.current_graph
        
        # Check in custom fields
        if key in self.custom_fields:
            return self.custom_fields[key]
        
        return default