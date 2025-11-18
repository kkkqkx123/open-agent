"""状态管理相关实体定义

定义状态快照、历史记录和差异等核心实体。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


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


@dataclass
class StateDiff:
    """状态差异实体
    
    表示两个状态之间的差异。
    """
    added: Dict[str, Any] = field(default_factory=dict)
    removed: Dict[str, Any] = field(default_factory=dict)
    modified: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    unchanged: Dict[str, Any] = field(default_factory=dict)
    
    def is_empty(self) -> bool:
        """检查差异是否为空
        
        Returns:
            如果没有差异则返回True
        """
        return not (self.added or self.removed or self.modified)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            字典表示的差异
        """
        return {
            "added": self.added,
            "removed": self.removed,
            "modified": self.modified,
            "unchanged": self.unchanged
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateDiff':
        """从字典创建差异实例
        
        Args:
            data: 字典数据
            
        Returns:
            差异实例
        """
        return cls(
            added=data.get("added", {}),
            removed=data.get("removed", {}),
            modified=data.get("modified", {}),
            unchanged=data.get("unchanged", {})
        )
    
    @classmethod
    def calculate(cls, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> 'StateDiff':
        """计算两个状态之间的差异
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            
        Returns:
            状态差异
        """
        diff = cls()
        
        # 检查新增和修改的键
        for key, new_value in new_state.items():
            if key not in old_state:
                diff.added[key] = new_value
            elif old_state[key] != new_value:
                diff.modified[key] = {
                    "old": old_state[key],
                    "new": new_value
                }
            else:
                diff.unchanged[key] = new_value
        
        # 检查删除的键
        for key in old_state:
            if key not in new_state:
                diff.removed[key] = old_state[key]
        
        return diff
    
    def apply_to_state(self, base_state: Dict[str, Any]) -> Dict[str, Any]:
        """将差异应用到基础状态
        
        Args:
            base_state: 基础状态
            
        Returns:
            应用差异后的状态
        """
        new_state = base_state.copy()
        
        # 应用删除
        for key in self.removed:
            if key in new_state:
                del new_state[key]
        
        # 应用修改和新增
        for key, value in self.added.items():
            new_state[key] = value
        
        for key, change in self.modified.items():
            if isinstance(change, dict) and "new" in change:
                new_state[key] = change["new"]
            else:
                new_state[key] = change
        
        return new_state


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