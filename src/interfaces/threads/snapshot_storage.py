"""线程快照存储适配器接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.threads.entities import ThreadSnapshot


class IThreadSnapshotStore(ABC):
    """线程快照存储适配器接口"""
    
    @abstractmethod
    async def get_snapshot(self, snapshot_id: str) -> Optional[ThreadSnapshot]:
        """获取快照"""
        pass
    
    @abstractmethod
    async def create_snapshot(self, snapshot: ThreadSnapshot) -> bool:
        """创建快照"""
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        pass
    
    @abstractmethod
    async def list_snapshots_by_thread(self, thread_id: str) -> List[ThreadSnapshot]:
        """按线程列快照"""
        pass
    
    @abstractmethod
    async def get_latest_snapshot(self, thread_id: str) -> Optional[ThreadSnapshot]:
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
    
    @abstractmethod
    async def search_snapshots(
        self, 
        query: str, 
        thread_id: Optional[str] = None,
        limit: int = 10
    ) -> List[ThreadSnapshot]:
        """搜索快照"""
        pass
    
    @abstractmethod
    async def cleanup_old_snapshots(self, max_age_days: int = 30) -> int:
        """清理旧快照"""
        pass