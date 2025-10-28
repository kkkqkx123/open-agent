from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


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


@dataclass
class ThreadHistory:
    """Thread历史记录"""
    thread_id: str
    checkpoints: List[Dict[str, Any]]
    branches: List[ThreadBranch]
    snapshots: List[ThreadSnapshot]