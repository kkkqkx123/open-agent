"""工作流实体

定义工作流系统的数据实体。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from .interfaces import IWorkflowState


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