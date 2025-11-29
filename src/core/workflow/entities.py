"""工作流实体

定义工作流系统的数据实体。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.interfaces import IWorkflowState


@dataclass
class Workflow:
    """工作流实体"""
    workflow_id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """工作流执行实体"""
    execution_id: str
    workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeExecution:
    """节点执行实体"""
    execution_id: str
    node_id: str
    node_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_state: Optional[IWorkflowState] = None
    output_state: Optional[IWorkflowState] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowState(IWorkflowState):
    """工作流状态实体"""
    workflow_id: str
    execution_id: str
    status: str = "running"
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    _metadata: Dict[str, Any] = field(default_factory=dict)
    _messages: List[Any] = field(default_factory=list)
    _state_id: Optional[str] = None
    _is_complete: bool = False
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置数据"""
        self.data[key] = value
        self.updated_at = datetime.now()
    
    def update_data(self, updates: Dict[str, Any]) -> None:
        """更新数据"""
        self.data.update(updates)
        self.updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self._metadata[key] = value
        self.updated_at = datetime.now()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        return self._state_id or self.execution_id
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._state_id = id
    
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        return self.created_at
    
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        return self.updated_at
    
    def is_complete(self) -> bool:
        """检查是否完成"""
        return self._is_complete
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self._is_complete = True
        self.updated_at = datetime.now()
    
    @property
    def messages(self) -> List[Any]:
        """获取消息列表"""
        return self._messages
    
    @property
    def fields(self) -> Dict[str, Any]:
        """获取字段字典"""
        return self.data
    
    @property
    def values(self) -> Dict[str, Any]:
        """获取状态值字典"""
        return self.data
    
    @property
    def iteration_count(self) -> int:
        """获取迭代计数"""
        return self._metadata.get('iteration_count', 0)
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        return self.data.get(key, default)
    
    def set_field(self, key: str, value: Any) -> 'WorkflowState':
        """设置字段值，返回新实例"""
        new_data = self.data.copy()
        new_data[key] = value
        return WorkflowState(
            workflow_id=self.workflow_id,
            execution_id=self.execution_id,
            status=self.status,
            data=new_data,
            created_at=self.created_at,
            updated_at=datetime.now(),
            _metadata=self._metadata.copy(),
            _messages=self._messages.copy(),
            _state_id=self._state_id,
            _is_complete=self._is_complete
        )
    
    def with_messages(self, messages: List[Any]) -> 'WorkflowState':
        """创建包含新消息的状态"""
        return WorkflowState(
            workflow_id=self.workflow_id,
            execution_id=self.execution_id,
            status=self.status,
            data=self.data.copy(),
            created_at=self.created_at,
            updated_at=datetime.now(),
            _metadata=self._metadata.copy(),
            _messages=messages,
            _state_id=self._state_id,
            _is_complete=self._is_complete
        )
    
    def with_metadata(self, metadata: Dict[str, Any]) -> 'WorkflowState':
        """创建包含新元数据的状态"""
        return WorkflowState(
            workflow_id=self.workflow_id,
            execution_id=self.execution_id,
            status=self.status,
            data=self.data.copy(),
            created_at=self.created_at,
            updated_at=datetime.now(),
            _metadata=metadata.copy(),
            _messages=self._messages.copy(),
            _state_id=self._state_id,
            _is_complete=self._is_complete
        )
    
    def add_message(self, message: Any) -> None:
        """添加消息"""
        self._messages.append(message)
        self.updated_at = datetime.now()
    
    def get_messages(self) -> List[Any]:
        """获取消息列表"""
        return self._messages.copy()
    
    def get_last_message(self) -> Any | None:
        """获取最后一条消息"""
        return self._messages[-1] if self._messages else None
    
    def copy(self) -> 'WorkflowState':
        """创建深拷贝"""
        return WorkflowState(
            workflow_id=self.workflow_id,
            execution_id=self.execution_id,
            status=self.status,
            data=self.data.copy(),
            created_at=self.created_at,
            updated_at=self.updated_at,
            _metadata=self._metadata.copy(),
            _messages=self._messages.copy(),
            _state_id=self._state_id,
            _is_complete=self._is_complete
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值（字典式访问）"""
        return self.data.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """设置状态值"""
        self.data[key] = value
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'workflow_id': self.workflow_id,
            'execution_id': self.execution_id,
            'status': self.status,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            '_metadata': self._metadata,
            '_messages': self._messages,
            '_state_id': self._state_id,
            '_is_complete': self._is_complete
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """从字典创建实例"""
        return cls(
            workflow_id=data['workflow_id'],
            execution_id=data['execution_id'],
            status=data.get('status', 'running'),
            data=data.get('data', {}),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now(),
            _metadata=data.get('_metadata', {}),
            _messages=data.get('_messages', []),
            _state_id=data.get('_state_id'),
            _is_complete=data.get('_is_complete', False)
        )


@dataclass
class ExecutionResult:
    """执行结果实体"""
    success: bool
    state: IWorkflowState
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowMetadata:
    """工作流元数据"""
    workflow_id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)