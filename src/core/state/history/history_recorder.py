"""状态历史记录器

提供记录状态变化的功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.interfaces.state.base import IState


class HistoryEntry:
    """历史记录条目
    
    表示一次状态变化的记录。
    """
    
    def __init__(self,
                 state_id: str,
                 operation: str,
                 data: Dict[str, Any],
                 context: Optional[Dict[str, Any]] = None,
                 timestamp: Optional[datetime] = None,
                 version: Optional[int] = None) -> None:
        """初始化历史记录条目
        
        Args:
            state_id: 状态ID
            operation: 操作类型
            data: 状态数据
            context: 上下文信息
            timestamp: 时间戳
            version: 版本号
        """
        self.id = str(uuid4())
        self.state_id = state_id
        self.operation = operation
        self.data = data.copy()
        self.context = context or {}
        self.timestamp = timestamp or datetime.now()
        self.version = version
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "id": self.id,
            "state_id": self.state_id,
            "operation": self.operation,
            "data": self.data,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """从字典创建历史记录条目
        
        Args:
            data: 字典数据
            
        Returns:
            HistoryEntry: 历史记录条目
        """
        timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        
        return cls(
            state_id=data["state_id"],
            operation=data["operation"],
            data=data["data"],
            context=data.get("context", {}),
            timestamp=timestamp,
            version=data.get("version")
        )


class StateHistoryRecorder:
    """状态历史记录器
    
    负责记录状态的变化历史。
    """
    
    def __init__(self) -> None:
        """初始化记录器"""
        self._version_counters: Dict[str, int] = {}
    
    def record_change(self,
                     state: IState,
                     operation: str = "update",
                     context: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """记录状态变化
        
        Args:
            state: 状态对象
            operation: 操作类型
            context: 上下文信息
            
        Returns:
            HistoryEntry: 历史记录条目
        """
        state_id = state.get_id() or "unknown"
        
        # 获取版本号
        version = self._get_next_version(state_id)
        
        # 创建历史记录
        entry = HistoryEntry(
            state_id=state_id,
            operation=operation,
            data=state.to_dict(),
            context=context,
            version=version
        )
        
        return entry
    
    def record_creation(self,
                       state: IState,
                       context: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """记录状态创建
        
        Args:
            state: 状态对象
            context: 上下文信息
            
        Returns:
            HistoryEntry: 历史记录条目
        """
        return self.record_change(state, "create", context)
    
    def record_update(self,
                     state: IState,
                     context: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """记录状态更新
        
        Args:
            state: 状态对象
            context: 上下文信息
            
        Returns:
            HistoryEntry: 历史记录条目
        """
        return self.record_change(state, "update", context)
    
    def record_deletion(self,
                       state: IState,
                       context: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """记录状态删除
        
        Args:
            state: 状态对象
            context: 上下文信息
            
        Returns:
            HistoryEntry: 历史记录条目
        """
        return self.record_change(state, "delete", context)
    
    def record_rollback(self,
                       state: IState,
                       target_version: int,
                       context: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """记录状态回滚
        
        Args:
            state: 状态对象
            target_version: 目标版本
            context: 上下文信息
            
        Returns:
            HistoryEntry: 历史记录条目
        """
        rollback_context = {
            "target_version": target_version,
            **(context or {})
        }
        
        return self.record_change(state, "rollback", rollback_context)
    
    def create_from_dict(self, data: Dict[str, Any]) -> HistoryEntry:
        """从字典创建历史记录条目
        
        Args:
            data: 字典数据
            
        Returns:
            HistoryEntry: 历史记录条目
        """
        entry = HistoryEntry.from_dict(data)
        
        # 更新版本计数器
        if entry.state_id and entry.version:
            current_version = self._version_counters.get(entry.state_id, 0)
            if entry.version > current_version:
                self._version_counters[entry.state_id] = entry.version
        
        return entry
    
    def _get_next_version(self, state_id: str) -> int:
        """获取下一个版本号
        
        Args:
            state_id: 状态ID
            
        Returns:
            int: 版本号
        """
        current_version = self._version_counters.get(state_id, 0)
        next_version = current_version + 1
        self._version_counters[state_id] = next_version
        return next_version
    
    def reset_version_counter(self, state_id: str) -> None:
        """重置版本计数器
        
        Args:
            state_id: 状态ID
        """
        self._version_counters[state_id] = 0
    
    def get_current_version(self, state_id: str) -> int:
        """获取当前版本号
        
        Args:
            state_id: 状态ID
            
        Returns:
            int: 当前版本号
        """
        return self._version_counters.get(state_id, 0)
    
    def get_all_version_counters(self) -> Dict[str, int]:
        """获取所有版本计数器
        
        Returns:
            Dict[str, int]: 版本计数器字典
        """
        return self._version_counters.copy()