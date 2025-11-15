from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class Thread:
    """Thread核心实体"""
    thread_id: str
    graph_id: str
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
    
    def update_status(self, new_status: str) -> None:
        """更新状态"""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """更新元数据"""
        self.metadata.update(updates)
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """检查是否活跃"""
        return self.status == "active"
    
    def is_error(self) -> bool:
        """检查是否错误状态"""
        return self.status == "error"


@dataclass
class ThreadBranch:
    """Thread分支信息"""
    branch_id: str
    source_thread_id: str
    source_checkpoint_id: str
    branch_name: str
    created_at: datetime
    metadata: Dict[str, Any]
    status: str = "active"
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class ThreadSnapshot:
    """Thread快照信息"""
    snapshot_id: str
    thread_id: str
    snapshot_name: str
    description: Optional[str]
    checkpoint_ids: List[str]
    created_at: datetime
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class ThreadHistory:
    """Thread历史记录"""
    thread_id: str
    checkpoints: List[Dict[str, Any]]
    branches: List[ThreadBranch]
    snapshots: List[ThreadSnapshot]


@dataclass
class ThreadState:
    """Thread状态"""
    thread_id: str
    state_data: Dict[str, Any]
    checkpoint_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)