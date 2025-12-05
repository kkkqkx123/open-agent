"""状态实体接口定义

定义状态管理中使用的实体接口，遵循分层架构原则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from ..common_domain import ISerializable


class IStateSnapshot(ISerializable, ABC):
    """状态快照接口
    
    定义状态快照的基本契约。
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
    


class IStateHistoryEntry(ISerializable, ABC):
    """状态历史记录接口
    
    定义状态历史记录的基本契约。
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
    


class IStateConflict(ISerializable, ABC):
    """状态冲突接口
    
    定义状态冲突的基本契约。
    """
    
    @property
    @abstractmethod
    def conflict_id(self) -> str:
        """冲突ID"""
        pass
    
    @property
    @abstractmethod
    def thread_id(self) -> str:
        """线程ID"""
        pass
    


class IStateStatistics(ISerializable, ABC):
    """状态统计接口
    
    定义状态统计的基本契约。
    """
    