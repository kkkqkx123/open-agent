"""Thread快照数据存储"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...domain.threads.models import ThreadSnapshot


class IThreadSnapshotStore(ABC):
    """Thread快照存储接口"""
    
    @abstractmethod
    async def save_snapshot(self, snapshot: ThreadSnapshot) -> bool:
        """保存快照信息"""
        pass
    
    @abstractmethod
    async def get_snapshot(self, snapshot_id: str) -> Optional[ThreadSnapshot]:
        """获取快照信息"""
        pass
    
    @abstractmethod
    async def get_snapshots_by_thread(self, thread_id: str) -> List[ThreadSnapshot]:
        """获取thread的所有快照"""
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        pass


class ThreadSnapshotStore(IThreadSnapshotStore):
    """Thread快照存储实现（基于内存）"""
    
    def __init__(self):
        """初始化快照存储"""
        self._snapshots: Dict[str, ThreadSnapshot] = {}
        self._thread_snapshots: Dict[str, List[str]] = {}  # thread_id -> [snapshot_id]
    
    async def save_snapshot(self, snapshot: ThreadSnapshot) -> bool:
        """保存快照信息"""
        try:
            self._snapshots[snapshot.snapshot_id] = snapshot
            
            # 更新thread到快照的映射
            if snapshot.thread_id not in self._thread_snapshots:
                self._thread_snapshots[snapshot.thread_id] = []
            if snapshot.snapshot_id not in self._thread_snapshots[snapshot.thread_id]:
                self._thread_snapshots[snapshot.thread_id].append(snapshot.snapshot_id)
            
            return True
        except Exception:
            return False
    
    async def get_snapshot(self, snapshot_id: str) -> Optional[ThreadSnapshot]:
        """获取快照信息"""
        return self._snapshots.get(snapshot_id)
    
    async def get_snapshots_by_thread(self, thread_id: str) -> List[ThreadSnapshot]:
        """获取thread的所有快照"""
        snapshot_ids = self._thread_snapshots.get(thread_id, [])
        snapshots = []
        for snapshot_id in snapshot_ids:
            snapshot = self._snapshots.get(snapshot_id)
            if snapshot:
                snapshots.append(snapshot)
        return snapshots
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        if snapshot_id not in self._snapshots:
            return False
        
        snapshot = self._snapshots[snapshot_id]
        
        # 从thread映射中移除
        if snapshot.thread_id in self._thread_snapshots:
            if snapshot_id in self._thread_snapshots[snapshot.thread_id]:
                self._thread_snapshots[snapshot.thread_id].remove(snapshot_id)
        
        # 删除快照
        del self._snapshots[snapshot_id]
        return True