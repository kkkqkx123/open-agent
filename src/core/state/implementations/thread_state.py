"""线程状态实现

提供线程状态的具体实现，继承自基础状态并实现线程特定功能。
"""

import uuid
from src.interfaces.dependency_injection import get_logger
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.interfaces.state.base import IState
from ..implementations.base_state import BaseStateImpl

# 由于中央接口层没有线程状态特化接口，使用基础接口作为替代
IThreadState = IState


logger = get_logger(__name__)


class ThreadState(BaseStateImpl, IThreadState):
    """线程状态实现
    
    继承自基础状态实现，添加线程特定的功能。
    """
    
    def __init__(self, **kwargs):
        """初始化线程状态"""
        super().__init__(**kwargs)
        
        # 线程特定字段
        self._session_id: Optional[str] = kwargs.get('session_id')
        self._thread_metadata: Dict[str, Any] = kwargs.get('thread_metadata', {})
        self._parent_thread_id: Optional[str] = kwargs.get('parent_thread_id')
        self._child_thread_ids: List[str] = kwargs.get('child_thread_ids', [])
        self._branch_point: Optional[Dict[str, Any]] = kwargs.get('branch_point')
        self._created_from_snapshot: Optional[str] = kwargs.get('created_from_snapshot')
    
    # IThreadState 接口实现
    def get_session_id(self) -> Optional[str]:
        """获取会话ID"""
        return self._session_id
    
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID"""
        self._session_id = session_id
        self._updated_at = datetime.now()
    
    def get_thread_metadata(self) -> Dict[str, Any]:
        """获取线程元数据"""
        return self._thread_metadata.copy()
    
    def set_thread_metadata(self, metadata: Dict[str, Any]) -> None:
        """设置线程元数据"""
        self._thread_metadata = metadata.copy()
        self._updated_at = datetime.now()
    
    def update_thread_metadata(self, updates: Dict[str, Any]) -> None:
        """更新线程元数据"""
        self._thread_metadata.update(updates)
        self._updated_at = datetime.now()
    
    def get_parent_thread_id(self) -> Optional[str]:
        """获取父线程ID"""
        return self._parent_thread_id
    
    def set_parent_thread_id(self, parent_thread_id: str) -> None:
        """设置父线程ID"""
        self._parent_thread_id = parent_thread_id
        self._updated_at = datetime.now()
    
    def get_child_thread_ids(self) -> List[str]:
        """获取子线程ID列表"""
        return self._child_thread_ids.copy()
    
    def add_child_thread_id(self, child_thread_id: str) -> None:
        """添加子线程ID"""
        if child_thread_id not in self._child_thread_ids:
            self._child_thread_ids.append(child_thread_id)
            self._updated_at = datetime.now()
    
    def remove_child_thread_id(self, child_thread_id: str) -> None:
        """移除子线程ID"""
        if child_thread_id in self._child_thread_ids:
            self._child_thread_ids.remove(child_thread_id)
            self._updated_at = datetime.now()
    
    def has_child_thread_id(self, child_thread_id: str) -> bool:
        """检查是否包含指定子线程ID"""
        return child_thread_id in self._child_thread_ids
    
    def get_child_count(self) -> int:
        """获取子线程数量"""
        return len(self._child_thread_ids)
    
    def get_branch_point(self) -> Optional[Dict[str, Any]]:
        """获取分支点信息"""
        return self._branch_point.copy() if self._branch_point else None
    
    def set_branch_point(self, branch_point: Dict[str, Any]) -> None:
        """设置分支点信息"""
        self._branch_point = branch_point.copy()
        self._updated_at = datetime.now()
    
    def is_branch(self) -> bool:
        """检查是否为分支线程"""
        return self._parent_thread_id is not None
    
    def get_created_from_snapshot(self) -> Optional[str]:
        """获取创建来源快照ID"""
        return self._created_from_snapshot
    
    def set_created_from_snapshot(self, snapshot_id: str) -> None:
        """设置创建来源快照ID"""
        self._created_from_snapshot = snapshot_id
        self._updated_at = datetime.now()
    
    # 线程特定方法
    def is_root_thread(self) -> bool:
        """检查是否为根线程"""
        return self._parent_thread_id is None
    
    def has_children(self) -> bool:
        """检查是否有子线程"""
        return len(self._child_thread_ids) > 0
    
    def get_thread_depth(self) -> int:
        """获取线程深度（根线程为0）"""
        if self.is_root_thread():
            return 0
        return 1  # 简化实现，实际可以递归计算
    
    def get_thread_path(self) -> List[str]:
        """获取线程路径（从根到当前线程）"""
        # 简化实现，实际需要递归构建
        path = [self._id] if self._id else []
        if self._parent_thread_id:
            path.insert(0, self._parent_thread_id)
        return path
    
    def is_sibling_of(self, other_thread_id: str) -> bool:
        """检查是否为兄弟线程"""
        return (self._parent_thread_id is not None and 
                self._parent_thread_id == 
                ThreadState.get_parent_thread_id_from_id(other_thread_id))
    
    @staticmethod
    def get_parent_thread_id_from_id(thread_id: str) -> Optional[str]:
        """从线程ID获取父线程ID（静态方法）"""
        # 这是一个简化的实现，实际需要从状态存储中获取
        return None
    
    def clear_child_threads(self) -> None:
        """清除所有子线程"""
        self._child_thread_ids.clear()
        self._updated_at = datetime.now()
    
    def set_child_thread_ids(self, child_thread_ids: List[str]) -> None:
        """设置子线程ID列表"""
        self._child_thread_ids = list(child_thread_ids)
        self._updated_at = datetime.now()
    
    def get_thread_info(self) -> Dict[str, Any]:
        """获取线程信息"""
        return {
            "id": self._id,
            "session_id": self._session_id,
            "parent_thread_id": self._parent_thread_id,
            "child_count": len(self._child_thread_ids),
            "is_root": self.is_root_thread(),
            "is_branch": self.is_branch(),
            "has_children": self.has_children(),
            "depth": self.get_thread_depth(),
            "created_from_snapshot": self._created_from_snapshot,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat()
        }
    
    def get_thread_hierarchy(self) -> Dict[str, Any]:
        """获取线程层次结构信息"""
        return {
            "id": self._id,
            "parent_id": self._parent_thread_id,
            "children": self._child_thread_ids.copy(),
            "depth": self.get_thread_depth(),
            "path": self.get_thread_path(),
            "is_root": self.is_root_thread(),
            "is_leaf": not self.has_children()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'session_id': self._session_id,
            'thread_metadata': self._thread_metadata,
            'parent_thread_id': self._parent_thread_id,
            'child_thread_ids': self._child_thread_ids,
            'branch_point': self._branch_point,
            'created_from_snapshot': self._created_from_snapshot
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThreadState':
        """从字典创建状态"""
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._session_id = data.get("session_id")
        instance._thread_metadata = data.get("thread_metadata", {})
        instance._parent_thread_id = data.get("parent_thread_id")
        instance._child_thread_ids = data.get("child_thread_ids", [])
        instance._branch_point = data.get("branch_point")
        instance._created_from_snapshot = data.get("created_from_snapshot")
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        # 处理时间
        created_at_str = data.get("created_at")
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        return instance
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"ThreadState(id={self._id}, session_id={self._session_id}, "
                f"children={len(self._child_thread_ids)})")
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"ThreadState(id={self._id}, session_id={self._session_id}, "
                f"parent={self._parent_thread_id}, children={len(self._child_thread_ids)}, "
                f"is_root={self.is_root_thread()}, is_branch={self.is_branch()})")


class BranchThreadState(ThreadState):
    """分支线程状态
    
    专门用于管理分支线程的状态。
    """
    
    def __init__(self, **kwargs):
        """初始化分支线程状态"""
        super().__init__(**kwargs)
        
        # 分支线程特定字段
        self._branch_reason: str = kwargs.get('branch_reason', '')
        self._branch_data: Dict[str, Any] = kwargs.get('branch_data', {})
        self._branch_timestamp: datetime = kwargs.get('branch_timestamp', datetime.now())
        self._merge_target_id: Optional[str] = kwargs.get('merge_target_id')
        self._merge_status: str = kwargs.get('merge_status', 'pending')  # pending, merged, rejected
    
    def get_branch_reason(self) -> str:
        """获取分支原因"""
        return self._branch_reason
    
    def set_branch_reason(self, reason: str) -> None:
        """设置分支原因"""
        self._branch_reason = reason
        self._updated_at = datetime.now()
    
    def get_branch_data(self) -> Dict[str, Any]:
        """获取分支数据"""
        return self._branch_data.copy()
    
    def set_branch_data(self, data: Dict[str, Any]) -> None:
        """设置分支数据"""
        self._branch_data = data.copy()
        self._updated_at = datetime.now()
    
    def update_branch_data(self, updates: Dict[str, Any]) -> None:
        """更新分支数据"""
        self._branch_data.update(updates)
        self._updated_at = datetime.now()
    
    def get_branch_timestamp(self) -> datetime:
        """获取分支时间戳"""
        return self._branch_timestamp
    
    def set_branch_timestamp(self, timestamp: datetime) -> None:
        """设置分支时间戳"""
        self._branch_timestamp = timestamp
        self._updated_at = datetime.now()
    
    def get_merge_target_id(self) -> Optional[str]:
        """获取合并目标ID"""
        return self._merge_target_id
    
    def set_merge_target_id(self, target_id: str) -> None:
        """设置合并目标ID"""
        self._merge_target_id = target_id
        self._updated_at = datetime.now()
    
    def get_merge_status(self) -> str:
        """获取合并状态"""
        return self._merge_status
    
    def set_merge_status(self, status: str) -> None:
        """设置合并状态"""
        self._merge_status = status
        self._updated_at = datetime.now()
    
    def is_merged(self) -> bool:
        """检查是否已合并"""
        return self._merge_status == 'merged'
    
    def is_merge_pending(self) -> bool:
        """检查是否待合并"""
        return self._merge_status == 'pending'
    
    def is_merge_rejected(self) -> bool:
        """检查是否合并被拒绝"""
        return self._merge_status == 'rejected'
    
    def mark_as_merged(self) -> None:
        """标记为已合并"""
        self._merge_status = 'merged'
        self._updated_at = datetime.now()
    
    def mark_as_rejected(self) -> None:
        """标记为合并被拒绝"""
        self._merge_status = 'rejected'
        self._updated_at = datetime.now()
    
    def get_branch_age(self) -> float:
        """获取分支年龄（秒）"""
        return (datetime.now() - self._branch_timestamp).total_seconds()
    
    def is_recent_branch(self, max_age_seconds: int = 3600) -> bool:
        """检查是否为最近创建的分支"""
        return self.get_branch_age() <= max_age_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'branch_reason': self._branch_reason,
            'branch_data': self._branch_data,
            'branch_timestamp': self._branch_timestamp.isoformat(),
            'merge_target_id': self._merge_target_id,
            'merge_status': self._merge_status
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BranchThreadState':
        """从字典创建状态"""
        # 首先创建父类实例，然后转换为子类类型
        thread_state = ThreadState.from_dict(data)
        instance: 'BranchThreadState' = cls.__new__(cls)
        
        # 复制父类属性
        instance._id = thread_state._id
        instance._data = thread_state._data
        instance._metadata = thread_state._metadata
        instance._complete = thread_state._complete
        instance._created_at = thread_state._created_at
        instance._updated_at = thread_state._updated_at
        
        # 复制 ThreadState 属性
        instance._session_id = thread_state._session_id
        instance._thread_metadata = thread_state._thread_metadata
        instance._parent_thread_id = thread_state._parent_thread_id
        instance._child_thread_ids = thread_state._child_thread_ids
        instance._branch_point = thread_state._branch_point
        instance._created_from_snapshot = thread_state._created_from_snapshot
        
        # 设置 BranchThreadState 特定属性
        instance._branch_reason = data.get("branch_reason", "")
        instance._branch_data = data.get("branch_data", {})
        instance._merge_target_id = data.get("merge_target_id")
        instance._merge_status = data.get("merge_status", "pending")
        
        # 处理时间
        branch_timestamp_str = data.get("branch_timestamp")
        if branch_timestamp_str:
            instance._branch_timestamp = datetime.fromisoformat(branch_timestamp_str)
        else:
            instance._branch_timestamp = datetime.now()
        
        return instance