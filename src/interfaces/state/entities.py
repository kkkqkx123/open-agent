"""状态相关实体定义

定义状态管理系统的核心实体，包括状态快照、历史记录、差异和冲突等。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


@dataclass
class StateSnapshot:
    """状态快照实体
    
    表示某个时间点的状态完整快照。
    """
    snapshot_id: str
    agent_id: str
    domain_state: Dict[str, Any]  # 序列化的域状态
    timestamp: datetime
    snapshot_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 性能优化字段
    compressed_data: Optional[bytes] = None
    size_bytes: int = 0
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.snapshot_name:
            self.snapshot_name = f"snapshot_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            字典表示的快照
        """
        return {
            "snapshot_id": self.snapshot_id,
            "agent_id": self.agent_id,
            "domain_state": self.domain_state,
            "timestamp": self.timestamp.isoformat(),
            "snapshot_name": self.snapshot_name,
            "metadata": self.metadata,
            "size_bytes": self.size_bytes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """从字典创建快照实例
        
        Args:
            data: 字典数据
            
        Returns:
            快照实例
        """
        return cls(
            snapshot_id=data["snapshot_id"],
            agent_id=data["agent_id"],
            domain_state=data["domain_state"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            snapshot_name=data.get("snapshot_name", ""),
            metadata=data.get("metadata", {}),
            compressed_data=data.get("compressed_data"),
            size_bytes=data.get("size_bytes", 0)
        )


@dataclass
class StateHistoryEntry:
    """状态历史记录实体
    
    表示一次状态变更的记录。
    """
    history_id: str
    agent_id: str
    timestamp: datetime
    action: str  # "state_change", "tool_call", "message_added", etc.
    state_diff: Dict[str, Any]  # 状态变化差异
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 性能优化字段
    compressed_diff: Optional[bytes] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.metadata:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            字典表示的历史记录
        """
        return {
            "history_id": self.history_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "state_diff": self.state_diff,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateHistoryEntry':
        """从字典创建历史记录实例
        
        Args:
            data: 字典数据
            
        Returns:
            历史记录实例
        """
        return cls(
            history_id=data["history_id"],
            agent_id=data["agent_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action=data["action"],
            state_diff=data["state_diff"],
            metadata=data.get("metadata", {}),
            compressed_diff=data.get("compressed_diff")
        )


class ConflictType(Enum):
    """冲突类型枚举"""
    FIELD_MODIFICATION = "field_modification"      # 字段修改冲突
    LIST_OPERATION = "list_operation"              # 列表操作冲突
    STRUCTURE_CHANGE = "structure_change"          # 结构变化冲突
    VERSION_MISMATCH = "version_mismatch"          # 版本不匹配冲突


class ConflictResolutionStrategy(Enum):
    """冲突解决策略"""
    LAST_WRITE_WINS = "last_write_wins"           # 最后写入获胜
    FIRST_WRITE_WINS = "first_write_wins"         # 首次写入获胜
    MANUAL_RESOLUTION = "manual_resolution"       # 手动解决
    MERGE_CHANGES = "merge_changes"               # 合并变更
    REJECT_CONFLICT = "reject_conflict"           # 拒绝冲突变更


@dataclass
class StateConflict:
    """状态冲突实体"""
    conflict_type: ConflictType
    conflicting_keys: List[str]
    resolution_strategy: ConflictResolutionStrategy
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            字典表示的冲突
        """
        return {
            "conflict_type": self.conflict_type.value,
            "conflicting_keys": self.conflicting_keys,
            "resolution_strategy": self.resolution_strategy.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateConflict':
        """从字典创建冲突实例
        
        Args:
            data: 字典数据
            
        Returns:
            冲突实例
        """
        return cls(
            conflict_type=ConflictType(data["conflict_type"]),
            conflicting_keys=data["conflicting_keys"],
            resolution_strategy=ConflictResolutionStrategy(data["resolution_strategy"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            details=data.get("details", {})
        )


@dataclass
class StateStatistics:
    """状态统计信息实体
    
    包含状态管理的各种统计信息。
    """
    total_states: int = 0
    total_snapshots: int = 0
    total_history_entries: int = 0
    storage_size_bytes: int = 0
    agent_counts: Dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            字典表示的统计信息
        """
        return {
            "total_states": self.total_states,
            "total_snapshots": self.total_snapshots,
            "total_history_entries": self.total_history_entries,
            "storage_size_bytes": self.storage_size_bytes,
            "agent_counts": self.agent_counts,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateStatistics':
        """从字典创建统计信息实例
        
        Args:
            data: 字典数据
            
        Returns:
            统计信息实例
        """
        return cls(
            total_states=data.get("total_states", 0),
            total_snapshots=data.get("total_snapshots", 0),
            total_history_entries=data.get("total_history_entries", 0),
            storage_size_bytes=data.get("storage_size_bytes", 0),
            agent_counts=data.get("agent_counts", {}),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        )