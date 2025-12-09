"""状态快照管理器

提供状态快照的创建、存储、恢复和管理功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.interfaces.state.base import IState
from src.infrastructure.state import ISnapshotStorage, MemorySnapshotStorage
from .snapshot_creator import StateSnapshotCreator
from .snapshot_restorer import StateSnapshotRestorer


class StateSnapshotManager:
    """状态快照管理器
    
    提供完整的状态快照管理功能，包括创建、存储、恢复和管理。
    """
    
    def __init__(self, 
                 storage: Optional[ISnapshotStorage] = None,
                 auto_cleanup: bool = True,
                 max_snapshots: int = 100) -> None:
        """初始化快照管理器
        
        Args:
            storage: 快照存储后端
            auto_cleanup: 是否自动清理旧快照
            max_snapshots: 最大快照数量
        """
        self._storage = storage or MemorySnapshotStorage()
        self._auto_cleanup = auto_cleanup
        self._max_snapshots = max_snapshots
        self._creator = StateSnapshotCreator()
        self._restorer = StateSnapshotRestorer()
    
    def create_snapshot(self, 
                       state: IState,
                       name: Optional[str] = None,
                       description: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> str:
        """创建状态快照
        
        Args:
            state: 状态对象
            name: 快照名称
            description: 快照描述
            tags: 快照标签
            
        Returns:
            str: 快照ID
        """
        # 创建快照
        snapshot = self._creator.create_snapshot(state, name, description, tags)
        
        # 存储快照
        self._storage.save_snapshot(snapshot)
        
        # 自动清理
        if self._auto_cleanup:
            state_id = state.get_id()
            if state_id is not None:
                self._cleanup_old_snapshots(state_id)
        
        return snapshot.id
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[IState]:
        """恢复快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[IState]: 恢复的状态对象
        """
        # 获取快照
        snapshot = self._storage.get_snapshot(snapshot_id)
        
        if snapshot is None:
            return None
        
        # 恢复状态
        return self._restorer.restore_state(snapshot)
    
    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """获取快照信息
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[Dict[str, Any]]: 快照信息
        """
        snapshot = self._storage.get_snapshot(snapshot_id)
        
        if snapshot is None:
            return None
        
        return snapshot.to_dict()
    
    def list_snapshots(self, 
                      state_id: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出快照
        
        Args:
            state_id: 状态ID（可选）
            tags: 标签过滤（可选）
            limit: 限制数量（可选）
            
        Returns:
            List[Dict[str, Any]]: 快照列表
        """
        snapshots = self._storage.list_snapshots(state_id, tags, limit)
        
        return [snapshot.to_dict() for snapshot in snapshots]
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 是否删除成功
        """
        return self._storage.delete_snapshot(snapshot_id)
    
    def delete_snapshots_by_state(self, state_id: str) -> int:
        """删除状态的所有快照
        
        Args:
            state_id: 状态ID
            
        Returns:
            int: 删除的快照数量
        """
        return self._storage.delete_snapshots_by_state(state_id)
    
    def get_latest_snapshot(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态的最新快照
        
        Args:
            state_id: 状态ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新快照信息
        """
        snapshots = self._storage.list_snapshots(state_id, limit=1)
        
        if not snapshots:
            return None
        
        return snapshots[0].to_dict()
    
    def compare_snapshots(self, 
                         snapshot_id1: str,
                         snapshot_id2: str) -> Dict[str, Any]:
        """比较两个快照
        
        Args:
            snapshot_id1: 快照ID1
            snapshot_id2: 快照ID2
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        snapshot1 = self._storage.get_snapshot(snapshot_id1)
        snapshot2 = self._storage.get_snapshot(snapshot_id2)
        
        if snapshot1 is None or snapshot2 is None:
            return {"error": "One or both snapshots not found"}
        
        # 恢复状态进行比较
        state1 = self._restorer.restore_state(snapshot1)
        state2 = self._restorer.restore_state(snapshot2)
        
        if state1 is None or state2 is None:
            return {"error": "Failed to restore states"}
        
        # 比较状态数据
        differences = self._compare_state_data(state1, state2)
        
        return {
            "snapshot1": {
                "id": snapshot1.id,
                "name": snapshot1.name,
                "created_at": snapshot1.created_at
            },
            "snapshot2": {
                "id": snapshot2.id,
                "name": snapshot2.name,
                "created_at": snapshot2.created_at
            },
            "differences": differences
        }
    
    def export_snapshot(self, 
                       snapshot_id: str,
                       format: str = "json") -> str:
        """导出快照
        
        Args:
            snapshot_id: 快照ID
            format: 导出格式
            
        Returns:
            str: 导出的快照数据
        """
        snapshot = self._storage.get_snapshot(snapshot_id)
        
        if snapshot is None:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        if format.lower() == "json":
            import json
            return json.dumps(snapshot.to_dict(), indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_snapshot(self, 
                       data: str,
                       format: str = "json") -> str:
        """导入快照
        
        Args:
            data: 快照数据
            format: 数据格式
            
        Returns:
            str: 快照ID
        """
        if format.lower() == "json":
            import json
            snapshot_data = json.loads(data)
            
            # 重建快照对象
            snapshot = self._creator.create_from_dict(snapshot_data)
            
            # 存储快照
            self._storage.save_snapshot(snapshot)
            
            return snapshot.id
        else:
            raise ValueError(f"Unsupported import format: {format}")
    
    def create_auto_snapshot(self, 
                            state: IState,
                            trigger: str = "auto") -> Optional[str]:
        """创建自动快照
        
        Args:
            state: 状态对象
            trigger: 触发原因
            
        Returns:
            Optional[str]: 快照ID
        """
        # 检查是否需要创建自动快照
        if not self._should_create_auto_snapshot(state, trigger):
            return None
        
        # 创建自动快照
        name = f"auto_{trigger}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        description = f"Automatic snapshot triggered by {trigger}"
        tags = ["auto", trigger]
        
        return self.create_snapshot(state, name, description, tags)
    
    def get_snapshot_statistics(self, state_id: Optional[str] = None) -> Dict[str, Any]:
        """获取快照统计信息
        
        Args:
            state_id: 状态ID（可选）
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        snapshots = self._storage.list_snapshots(state_id)
        
        total_count = len(snapshots)
        auto_count = sum(1 for s in snapshots if "auto" in s.tags)
        manual_count = total_count - auto_count
        
        # 计算存储大小
        total_size = sum(s.size for s in snapshots)
        
        # 按标签分组
        tag_counts: Dict[str, int] = {}
        for snapshot in snapshots:
            for tag in snapshot.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "total_count": total_count,
            "auto_count": auto_count,
            "manual_count": manual_count,
            "total_size": total_size,
            "tag_counts": tag_counts,
            "oldest_snapshot": min(s.created_at for s in snapshots) if snapshots else None,
            "newest_snapshot": max(s.created_at for s in snapshots) if snapshots else None
        }
    
    def cleanup_old_snapshots(self, state_id: str, keep_count: int = 10) -> int:
        """清理旧快照
        
        Args:
            state_id: 状态ID
            keep_count: 保留数量
            
        Returns:
            int: 删除的快照数量
        """
        snapshots = self._storage.list_snapshots(state_id)
        
        if len(snapshots) <= keep_count:
            return 0
        
        # 按创建时间排序，保留最新的
        snapshots.sort(key=lambda s: s.created_at, reverse=True)
        
        # 删除多余的快照
        to_delete = snapshots[keep_count:]
        deleted_count = 0
        
        for snapshot in to_delete:
            if self._storage.delete_snapshot(snapshot.id):
                deleted_count += 1
        
        return deleted_count
    
    def _should_create_auto_snapshot(self, state: IState, trigger: str) -> bool:
        """判断是否应该创建自动快照
        
        Args:
            state: 状态对象
            trigger: 触发原因
            
        Returns:
            bool: 是否应该创建
        """
        # 检查是否已有最近的自动快照
        recent_snapshots = self._storage.list_snapshots(
            state.get_id(), 
            tags=["auto", trigger],
            limit=1
        )
        
        if not recent_snapshots:
            return True
        
        # 检查时间间隔（例如：至少间隔1小时）
        from datetime import timedelta
        min_interval = timedelta(hours=1)
        
        last_snapshot = recent_snapshots[0]
        return datetime.now() - last_snapshot.created_at > min_interval
    
    def _cleanup_old_snapshots(self, state_id: str) -> None:
        """清理旧快照
        
        Args:
            state_id: 状态ID
        """
        snapshots = self._storage.list_snapshots(state_id)
        
        if len(snapshots) > self._max_snapshots:
            # 按创建时间排序，删除最旧的
            snapshots.sort(key=lambda s: s.created_at)
            
            excess_count = len(snapshots) - self._max_snapshots
            to_delete = snapshots[:excess_count]
            
            for snapshot in to_delete:
                self._storage.delete_snapshot(snapshot.id)
    
    def _compare_state_data(self, state1: IState, state2: IState) -> Dict[str, Any]:
        """比较状态数据
        
        Args:
            state1: 状态1
            state2: 状态2
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        differences: Dict[str, Dict[str, Any]] = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # 比较数据
        data1 = state1.to_dict()
        data2 = state2.to_dict()
        
        # 找出添加的字段
        for key in data2:
            if key not in data1:
                differences["added"][key] = data2[key]
        
        # 找出删除的字段
        for key in data1:
            if key not in data2:
                differences["removed"][key] = data1[key]
        
        # 找出修改的字段
        for key in data1:
            if key in data2 and data1[key] != data2[key]:
                differences["modified"][key] = {
                    "old": data1[key],
                    "new": data2[key]
                }
        
        return differences


# 便捷函数
def create_snapshot_manager(storage: Optional[ISnapshotStorage] = None,
                           auto_cleanup: bool = True,
                           max_snapshots: int = 100) -> StateSnapshotManager:
    """创建状态快照管理器的便捷函数
    
    Args:
        storage: 快照存储后端
        auto_cleanup: 是否自动清理旧快照
        max_snapshots: 最大快照数量
        
    Returns:
        StateSnapshotManager: 快照管理器实例
    """
    return StateSnapshotManager(storage, auto_cleanup, max_snapshots)