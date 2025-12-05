"""状态管理相关实体定义
 

定义状态快照、历史记录、差异和冲突等核心实体。
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum

# 从Interface层导入接口定义
from src.interfaces.state.entities import IStateSnapshot, IStateHistoryEntry


class TimestampUtils:
    """时间戳处理工具类"""
    
    @staticmethod
    def normalize_timestamp(timestamp: Union[str, datetime]) -> str:
        """标准化时间戳为字符串格式"""
        if isinstance(timestamp, str):
            return timestamp
        elif isinstance(timestamp, datetime):
            return timestamp.isoformat()
        else:
            raise ValueError(f"不支持的时间戳类型: {type(timestamp)}")
    
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> datetime:
        """解析时间戳字符串为datetime对象"""
        return datetime.fromisoformat(timestamp_str)


@dataclass
class StateSnapshot(IStateSnapshot):
    """状态快照实体
    
    表示某个时间点的状态完整快照。
    """
    _snapshot_id: str = field(repr=False)
    _thread_id: str = field(repr=False)
    _domain_state: Dict[str, Any] = field(repr=False)  # 序列化的域状态
    _timestamp: str = field(repr=False)  # 时间戳字符串
    _snapshot_name: str = field(repr=False)
    _metadata: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # 性能优化字段
    compressed_data: Optional[bytes] = None
    size_bytes: int = 0
    
    def __init__(self, snapshot_id: str, thread_id: str, domain_state: Dict[str, Any],
                 timestamp: str, snapshot_name: str, metadata: Optional[Dict[str, Any]] = None,
                 compressed_data: Optional[bytes] = None, size_bytes: int = 0):
        """初始化状态快照"""
        self._snapshot_id = snapshot_id
        self._thread_id = thread_id
        self._domain_state = domain_state
        self._timestamp = TimestampUtils.normalize_timestamp(timestamp)
        self._snapshot_name = snapshot_name or f"snapshot_{self._timestamp.replace(':', '').replace('-', '')}"
        self._metadata = metadata or {}
        self.compressed_data = compressed_data
        self.size_bytes = size_bytes
    
    @property
    def snapshot_id(self) -> str:
        """快照ID"""
        return self._snapshot_id
    
    @property
    def thread_id(self) -> str:
        """线程ID"""
        return self._thread_id
    
    @property
    def domain_state(self) -> Dict[str, Any]:
        """域状态数据"""
        return self._domain_state
    
    @property
    def timestamp(self) -> str:
        """时间戳"""
        return self._timestamp
    
    @property
    def snapshot_name(self) -> str:
        """快照名称"""
        return self._snapshot_name
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            字典表示的快照
        """
        return {
            "snapshot_id": self._snapshot_id,
            "thread_id": self._thread_id,
            "domain_state": self._domain_state,
            "timestamp": self._timestamp,
            "snapshot_name": self._snapshot_name,
            "metadata": self._metadata,
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
            thread_id=data["thread_id"],
            domain_state=data["domain_state"],
            timestamp=data["timestamp"],
            snapshot_name=data.get("snapshot_name", ""),
            metadata=data.get("metadata", {}),
            compressed_data=data.get("compressed_data"),
            size_bytes=data.get("size_bytes", 0)
        )


@dataclass
class StateHistoryEntry(IStateHistoryEntry):
    """状态历史记录实体
    
    表示一次状态变更的记录。
    """
    _history_id: str = field(repr=False)
    _thread_id: str = field(repr=False)
    _timestamp: str = field(repr=False)
    _action: str = field(repr=False)  # "state_change", "tool_call", "message_added", etc.
    _state_diff: Dict[str, Any] = field(repr=False)  # 状态变化差异
    _metadata: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # 性能优化字段
    compressed_diff: Optional[bytes] = None
    
    def __init__(self, history_id: str, thread_id: str, timestamp: str, action: str,
                 state_diff: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None,
                 compressed_diff: Optional[bytes] = None):
        """初始化历史记录条目"""
        self._history_id = history_id
        self._thread_id = thread_id
        self._timestamp = TimestampUtils.normalize_timestamp(timestamp)
        self._action = action
        self._state_diff = state_diff
        self._metadata = metadata or {}
        self.compressed_diff = compressed_diff
    
    @property
    def history_id(self) -> str:
        """历史记录ID"""
        return self._history_id
    
    @property
    def thread_id(self) -> str:
        """线程ID"""
        return self._thread_id
    
    @property
    def timestamp(self) -> str:
        """时间戳"""
        return self._timestamp
    
    @property
    def action(self) -> str:
        """动作类型"""
        return self._action
    
    @property
    def state_diff(self) -> Dict[str, Any]:
        """状态差异"""
        return self._state_diff
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            字典表示的历史记录
        """
        return {
            "history_id": self._history_id,
            "thread_id": self._thread_id,
            "timestamp": self._timestamp,
            "action": self._action,
            "state_diff": self._state_diff,
            "metadata": self._metadata
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
            thread_id=data["thread_id"],
            timestamp=data["timestamp"],
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


class ConflictType(str, Enum):
    """冲突类型枚举"""
    # 旧版本值（向后兼容）
    FIELD_MODIFICATION = "field_modification"      # 字段修改冲突
    LIST_OPERATION = "list_operation"              # 列表操作冲突
    STRUCTURE_CHANGE = "structure_change"          # 结构变化冲突
    VERSION_MISMATCH = "version_mismatch"          # 版本不匹配冲突
    
    # 新增值
    CONCURRENT_UPDATE = "concurrent_update"        # 并发更新冲突
    MERGE_CONFLICT = "merge_conflict"              # 合并冲突
    CONSTRAINT_VIOLATION = "constraint_violation"  # 约束违反
    UNKNOWN = "unknown"                            # 未知冲突


class ConflictResolutionStrategy(str, Enum):
    """冲突解决策略"""
    # 旧版本值（向后兼容）
    LAST_WRITE_WINS = "last_write_wins"           # 最后写入获胜
    FIRST_WRITE_WINS = "first_write_wins"         # 首次写入获胜
    MANUAL_RESOLUTION = "manual_resolution"       # 手动解决
    MERGE_CHANGES = "merge_changes"               # 合并变更
    REJECT_CONFLICT = "reject_conflict"           # 拒绝冲突变更
    
    # 新增值（向后兼容的别名）
    KEEP_MINE = "keep_mine"                       # 保留本地版本
    TAKE_THEIRS = "take_theirs"                   # 取用远程版本
    MERGE = "merge"                               # 合并
    MANUAL_REVIEW = "manual_review"               # 手动审查
    ABORT = "abort"                               # 中止


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
    thread_counts: Dict[str, int] = field(default_factory=dict)
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
            "thread_counts": self.thread_counts,
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
            thread_counts=data.get("thread_counts", {}),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        )