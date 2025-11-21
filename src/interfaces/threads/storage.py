"""线程存储适配器接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.interfaces.common import (
    AbstractThreadData, 
    AbstractThreadBranchData, 
    AbstractThreadSnapshotData
)


class IThreadStore(ABC):
    """统一线程存储适配器接口 - 合并线程、分支、快照存储"""
    
    # 线程相关操作
    @abstractmethod
    async def get_thread(self, thread_id: str) -> Optional[AbstractThreadData]:
        """获取线程"""
        pass
    
    @abstractmethod
    async def create_thread(self, thread: AbstractThreadData) -> bool:
        """创建线程"""
        pass
    
    @abstractmethod
    async def update_thread(self, thread_id: str, thread: AbstractThreadData) -> bool:
        """更新线程"""
        pass
    
    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程"""
        pass
    
    @abstractmethod
    async def list_threads_by_session(self, session_id: str) -> List[AbstractThreadData]:
        """按会话列线程"""
        pass
    
    @abstractmethod
    async def search_threads(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AbstractThreadData]:
        """搜索线程"""
        pass
    
    @abstractmethod
    async def get_thread_count_by_session(self, session_id: str) -> int:
        """获取会话线程数量"""
        pass
    
    # 分支相关操作
    @abstractmethod
    async def get_branch(self, branch_id: str) -> Optional[AbstractThreadBranchData]:
        """获取分支"""
        pass
    
    @abstractmethod
    async def create_branch(self, branch: AbstractThreadBranchData) -> bool:
        """创建分支"""
        pass
    
    @abstractmethod
    async def update_branch(self, branch_id: str, branch: AbstractThreadBranchData) -> bool:
        """更新分支"""
        pass
    
    @abstractmethod
    async def delete_branch(self, branch_id: str) -> bool:
        """删除分支"""
        pass
    
    @abstractmethod
    async def list_branches_by_thread(self, thread_id: str) -> List[AbstractThreadBranchData]:
        """按线程列分支"""
        pass
    
    @abstractmethod
    async def get_main_branch(self, thread_id: str) -> Optional[AbstractThreadBranchData]:
        """获取主分支"""
        pass
    
    @abstractmethod
    async def merge_branch(self, source_branch_id: str, target_branch_id: str) -> bool:
        """合并分支"""
        pass
    
    # 快照相关操作
    @abstractmethod
    async def get_snapshot(self, snapshot_id: str) -> Optional[AbstractThreadSnapshotData]:
        """获取快照"""
        pass
    
    @abstractmethod
    async def create_snapshot(self, snapshot: AbstractThreadSnapshotData) -> bool:
        """创建快照"""
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        pass
    
    @abstractmethod
    async def list_snapshots_by_thread(self, thread_id: str) -> List[AbstractThreadSnapshotData]:
        """按线程列快照"""
        pass
    
    @abstractmethod
    async def get_latest_snapshot(self, thread_id: str) -> Optional[AbstractThreadSnapshotData]:
        """获取最新快照"""
        pass
    
    @abstractmethod
    async def compare_snapshots(
        self, 
        snapshot_id1: str, 
        snapshot_id2: str
    ) -> Dict[str, Any]:
        """比较快照"""
        pass
    
    # 清理操作
    @abstractmethod
    async def cleanup_old_threads(self, max_age_days: int = 30) -> int:
        """清理旧线程"""
        pass
    
    @abstractmethod
    async def cleanup_old_branches(self, max_age_days: int = 30) -> int:
        """清理旧分支"""
        pass
    
    @abstractmethod
    async def cleanup_old_snapshots(self, max_age_days: int = 30) -> int:
        """清理旧快照"""
        pass