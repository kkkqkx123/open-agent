"""线程状态特化接口定义

定义专门用于线程状态管理的接口，继承自基础状态接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import IState


class IThreadState(IState):
    """线程状态接口
    
    继承自基础状态接口，添加线程特定的功能。
    """
    
    @abstractmethod
    def get_session_id(self) -> Optional[str]:
        """获取会话ID"""
        pass
    
    @abstractmethod
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID"""
        pass
    
    @abstractmethod
    def get_thread_metadata(self) -> Dict[str, Any]:
        """获取线程元数据"""
        pass
    
    @abstractmethod
    def set_thread_metadata(self, metadata: Dict[str, Any]) -> None:
        """设置线程元数据"""
        pass
    
    @abstractmethod
    def get_parent_thread_id(self) -> Optional[str]:
        """获取父线程ID"""
        pass
    
    @abstractmethod
    def set_parent_thread_id(self, parent_thread_id: str) -> None:
        """设置父线程ID"""
        pass
    
    @abstractmethod
    def get_child_thread_ids(self) -> List[str]:
        """获取子线程ID列表"""
        pass
    
    @abstractmethod
    def add_child_thread_id(self, child_thread_id: str) -> None:
        """添加子线程ID"""
        pass
    
    @abstractmethod
    def remove_child_thread_id(self, child_thread_id: str) -> None:
        """移除子线程ID"""
        pass
    
    @abstractmethod
    def get_branch_point(self) -> Optional[Dict[str, Any]]:
        """获取分支点信息"""
        pass
    
    @abstractmethod
    def set_branch_point(self, branch_point: Dict[str, Any]) -> None:
        """设置分支点信息"""
        pass
    
    @abstractmethod
    def is_branch(self) -> bool:
        """检查是否为分支线程"""
        pass
    
    @abstractmethod
    def get_created_from_snapshot(self) -> Optional[str]:
        """获取创建来源快照ID"""
        pass
    
    @abstractmethod
    def set_created_from_snapshot(self, snapshot_id: str) -> None:
        """设置创建来源快照ID"""
        pass


class IThreadStateManager(ABC):
    """线程状态管理器接口"""
    
    @abstractmethod
    def create_thread(self, session_id: str, **kwargs) -> IThreadState:
        """创建线程"""
        pass
    
    @abstractmethod
    def get_thread(self, thread_id: str) -> Optional[IThreadState]:
        """获取线程"""
        pass
    
    @abstractmethod
    def get_session_threads(self, session_id: str) -> List[IThreadState]:
        """获取会话的所有线程"""
        pass
    
    @abstractmethod
    def get_child_threads(self, parent_thread_id: str) -> List[IThreadState]:
        """获取子线程"""
        pass
    
    @abstractmethod
    def create_branch(self, parent_thread_id: str, branch_point: Dict[str, Any]) -> IThreadState:
        """创建分支线程"""
        pass
    
    @abstractmethod
    def save_thread(self, thread: IThreadState) -> bool:
        """保存线程"""
        pass
    
    @abstractmethod
    def delete_thread(self, thread_id: str) -> bool:
        """删除线程"""
        pass
    
    @abstractmethod
    def merge_thread(self, source_thread_id: str, target_thread_id: str) -> bool:
        """合并线程"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass