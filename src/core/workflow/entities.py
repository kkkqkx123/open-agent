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

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'workflow_id': self.workflow_id,
            'execution_id': self.execution_id,
            'status': self.status,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
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
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
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