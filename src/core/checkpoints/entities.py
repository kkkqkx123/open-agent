"""Checkpoint实体定义

定义checkpoint相关的数据实体。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class CheckpointData:
    """Checkpoint数据实体
    
    代表一个checkpoint的完整数据结构。
    """
    
    id: str
    thread_id: str
    session_id: str
    workflow_id: str
    state_data: Any
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'thread_id': self.thread_id,
            'session_id': self.session_id,
            'workflow_id': self.workflow_id,
            'state_data': self.state_data,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointData':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            thread_id=data['thread_id'],
            session_id=data.get('session_id', ''),
            workflow_id=data['workflow_id'],
            state_data=data['state_data'],
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )


@dataclass
class CheckpointConfig:
    """Checkpoint配置实体
    
    定义checkpoint系统的配置参数。
    """
    
    max_checkpoints_per_thread: int = 100
    enable_compression: bool = False
    enable_performance_monitoring: bool = False
    cleanup_threshold: int = 1000