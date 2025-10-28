"""Thread协作相关数据模型"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ThreadCollaboration:
    """Thread协作信息"""
    collaboration_id: str
    thread_ids: List[str]
    permissions: Dict[str, Any]
    created_at: datetime
    metadata: Dict[str, Any]
    status: str = "active"


@dataclass
class SharedThreadState:
    """共享的Thread状态"""
    shared_id: str
    source_thread_id: str
    target_thread_id: str
    checkpoint_id: str
    permissions: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None