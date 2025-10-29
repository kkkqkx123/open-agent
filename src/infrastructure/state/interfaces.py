"""状态存储接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class StateSnapshot:
    """状态快照"""
    snapshot_id: str
    agent_id: str
    domain_state: Dict[str, Any]  # 序列化的域状态
    timestamp: datetime
    snapshot_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 性能优化字段
    compressed_data: Optional[bytes] = None
    size_bytes: int = 0


@dataclass
class StateHistoryEntry:
    """状态历史记录"""
    history_id: str
    agent_id: str
    timestamp: datetime
    action: str  # "state_change", "tool_call", "message_added", etc.
    state_diff: Dict[str, Any]  # 状态变化差异
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 性能优化字段
    compressed_diff: Optional[bytes] = None


class IStateSnapshotStore(ABC):
    """状态快照存储接口"""

    @abstractmethod
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """保存快照"""
        pass

    @abstractmethod
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载快照"""
        pass

    @abstractmethod
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定Agent的快照列表"""
        pass


class IStateHistoryManager(ABC):
    """状态历史管理器接口"""

    @abstractmethod
    def record_state_change(self, agent_id: str, old_state: Dict[str, Any],
                           new_state: Dict[str, Any], action: str) -> str:
        """记录状态变化"""
        pass

    @abstractmethod
    def get_state_history(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取状态历史"""
        pass