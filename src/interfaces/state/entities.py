"""状态相关抽象类型定义

定义状态管理相关的抽象数据类型，用于接口层解耦。
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class AbstractStateSnapshot(ABC):
    """状态快照抽象类型
    
    表示某个时间点的状态完整快照的抽象接口。
    """
    
    @property
    @abstractmethod
    def snapshot_id(self) -> str:
        """快照ID"""
        pass
    
    @property
    @abstractmethod
    def thread_id(self) -> str:
        """线程ID"""
        pass
    
    @property
    @abstractmethod
    def domain_state(self) -> Dict[str, Any]:
        """域状态数据"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> str:
        """时间戳"""
        pass
    
    @property
    @abstractmethod
    def snapshot_name(self) -> str:
        """快照名称"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        pass


class AbstractStateHistoryEntry(ABC):
    """状态历史记录抽象类型
    
    表示一次状态变更的记录的抽象接口。
    """
    
    @property
    @abstractmethod
    def history_id(self) -> str:
        """历史记录ID"""
        pass
    
    @property
    @abstractmethod
    def thread_id(self) -> str:
        """线程ID"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> str:
        """时间戳"""
        pass
    
    @property
    @abstractmethod
    def action(self) -> str:
        """动作类型"""
        pass
    
    @property
    @abstractmethod
    def state_diff(self) -> Dict[str, Any]:
        """状态差异"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        pass


class AbstractStateDiff(ABC):
    """状态差异抽象类型
    
    表示两个状态之间的差异的抽象接口。
    """
    
    @property
    @abstractmethod
    def added(self) -> Dict[str, Any]:
        """新增字段"""
        pass
    
    @property
    @abstractmethod
    def removed(self) -> Dict[str, Any]:
        """删除字段"""
        pass
    
    @property
    @abstractmethod
    def modified(self) -> Dict[str, Dict[str, Any]]:
        """修改字段"""
        pass
    
    @property
    @abstractmethod
    def unchanged(self) -> Dict[str, Any]:
        """未变更字段"""
        pass
    
    @abstractmethod
    def is_empty(self) -> bool:
        """检查差异是否为空"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        pass


class AbstractStateConflict(ABC):
    """状态冲突抽象类型"""
    
    @property
    @abstractmethod
    def conflict_type(self) -> str:
        """冲突类型"""
        pass
    
    @property
    @abstractmethod
    def conflicting_keys(self) -> List[str]:
        """冲突键列表"""
        pass
    
    @property
    @abstractmethod
    def resolution_strategy(self) -> str:
        """解决策略"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> str:
        """时间戳"""
        pass
    
    @property
    @abstractmethod
    def details(self) -> Dict[str, Any]:
        """详细信息"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        pass


class AbstractStateStatistics(ABC):
    """状态统计信息抽象类型
    
    包含状态管理的各种统计信息的抽象接口。
    """
    
    @property
    @abstractmethod
    def total_states(self) -> int:
        """总状态数"""
        pass
    
    @property
    @abstractmethod
    def total_snapshots(self) -> int:
        """总快照数"""
        pass
    
    @property
    @abstractmethod
    def total_history_entries(self) -> int:
        """总历史记录数"""
        pass
    
    @property
    @abstractmethod
    def storage_size_bytes(self) -> int:
        """存储大小（字节）"""
        pass
    
    @property
    @abstractmethod
    def thread_counts(self) -> Dict[str, int]:
        """线程计数"""
        pass
    
    @property
    @abstractmethod
    def last_updated(self) -> str:
        """最后更新时间"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        pass