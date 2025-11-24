"""快照存储

提供快照的存储接口和实现。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


class StateSnapshot:
    """状态快照
    
    表示某个时间点的状态快照。
    """
    
    def __init__(self,
                 state_id: str,
                 state_data: Dict[str, Any],
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 created_at: Optional[datetime] = None) -> None:
        """初始化状态快照
        
        Args:
            state_id: 状态ID
            state_data: 状态数据
            name: 快照名称
            description: 快照描述
            tags: 快照标签
            created_at: 创建时间
        """
        self.id = str(uuid4())
        self.state_id = state_id
        self.state_data = state_data.copy()
        self.name = name
        self.description = description
        self.tags = tags or []
        self.created_at = created_at or datetime.now()
        self.size = len(str(state_data))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "id": self.id,
            "state_id": self.state_id,
            "state_data": self.state_data,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "size": self.size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSnapshot":
        """从字典创建状态快照
        
        Args:
            data: 字典数据
            
        Returns:
            StateSnapshot: 状态快照
        """
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        
        return cls(
            state_id=data["state_id"],
            state_data=data["state_data"],
            name=data.get("name"),
            description=data.get("description"),
            tags=data.get("tags", []),
            created_at=created_at
        )


class ISnapshotStorage(ABC):
    """快照存储接口
    
    定义快照存储的抽象接口。
    """
    
    @abstractmethod
    def save_snapshot(self, snapshot: StateSnapshot) -> None:
        """保存快照
        
        Args:
            snapshot: 状态快照
        """
        pass
    
    @abstractmethod
    def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """获取快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[StateSnapshot]: 状态快照
        """
        pass
    
    @abstractmethod
    def list_snapshots(self, 
                      state_id: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      limit: Optional[int] = None) -> List[StateSnapshot]:
        """列出快照
        
        Args:
            state_id: 状态ID（可选）
            tags: 标签过滤（可选）
            limit: 限制数量（可选）
            
        Returns:
            List[StateSnapshot]: 快照列表
        """
        pass
    
    @abstractmethod
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    def delete_snapshots_by_state(self, state_id: str) -> int:
        """删除状态的所有快照
        
        Args:
            state_id: 状态ID
            
        Returns:
            int: 删除的快照数量
        """
        pass


class MemorySnapshotStorage(ISnapshotStorage):
    """内存快照存储
    
    将快照存储在内存中。
    """
    
    def __init__(self) -> None:
        """初始化内存存储"""
        self._snapshots: Dict[str, StateSnapshot] = {}
        self._state_snapshots: Dict[str, List[str]] = {}
    
    def save_snapshot(self, snapshot: StateSnapshot) -> None:
        """保存快照
        
        Args:
            snapshot: 状态快照
        """
        self._snapshots[snapshot.id] = snapshot
        
        # 更新状态快照索引
        if snapshot.state_id not in self._state_snapshots:
            self._state_snapshots[snapshot.state_id] = []
        
        if snapshot.id not in self._state_snapshots[snapshot.state_id]:
            self._state_snapshots[snapshot.state_id].append(snapshot.id)
    
    def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """获取快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[StateSnapshot]: 状态快照
        """
        return self._snapshots.get(snapshot_id)
    
    def list_snapshots(self, 
                      state_id: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      limit: Optional[int] = None) -> List[StateSnapshot]:
        """列出快照
        
        Args:
            state_id: 状态ID（可选）
            tags: 标签过滤（可选）
            limit: 限制数量（可选）
            
        Returns:
            List[StateSnapshot]: 快照列表
        """
        # 获取候选快照
        if state_id:
            snapshot_ids = self._state_snapshots.get(state_id, [])
            snapshots = [self._snapshots[sid] for sid in snapshot_ids if sid in self._snapshots]
        else:
            snapshots = list(self._snapshots.values())
        
        # 标签过滤
        if tags:
            filtered_snapshots = []
            for snapshot in snapshots:
                if any(tag in snapshot.tags for tag in tags):
                    filtered_snapshots.append(snapshot)
            snapshots = filtered_snapshots
        
        # 按创建时间排序（最新的在前）
        snapshots.sort(key=lambda x: x.created_at, reverse=True)
        
        # 应用限制
        if limit:
            snapshots = snapshots[:limit]
        
        return snapshots
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 是否删除成功
        """
        if snapshot_id not in self._snapshots:
            return False
        
        snapshot = self._snapshots[snapshot_id]
        
        # 从主存储中删除
        del self._snapshots[snapshot_id]
        
        # 从状态快照索引中删除
        if snapshot.state_id in self._state_snapshots:
            if snapshot_id in self._state_snapshots[snapshot.state_id]:
                self._state_snapshots[snapshot.state_id].remove(snapshot_id)
            
            # 如果状态没有快照了，删除状态条目
            if not self._state_snapshots[snapshot.state_id]:
                del self._state_snapshots[snapshot.state_id]
        
        return True
    
    def delete_snapshots_by_state(self, state_id: str) -> int:
        """删除状态的所有快照
        
        Args:
            state_id: 状态ID
            
        Returns:
            int: 删除的快照数量
        """
        if state_id not in self._state_snapshots:
            return 0
        
        snapshot_ids = self._state_snapshots[state_id]
        deleted_count = 0
        
        # 删除所有相关快照
        for snapshot_id in snapshot_ids:
            if snapshot_id in self._snapshots:
                del self._snapshots[snapshot_id]
                deleted_count += 1
        
        # 删除状态快照索引
        del self._state_snapshots[state_id]
        
        return deleted_count


class FileSnapshotStorage(ISnapshotStorage):
    """文件快照存储
    
    将快照存储在文件系统中。
    """
    
    def __init__(self, storage_path: str) -> None:
        """初始化文件存储
        
        Args:
            storage_path: 存储路径
        """
        self._storage_path = storage_path
        self._init_storage()
    
    def _init_storage(self) -> None:
        """初始化存储"""
        import os
        
        os.makedirs(self._storage_path, exist_ok=True)
    
    def _get_snapshot_file_path(self, snapshot_id: str) -> str:
        """获取快照文件路径
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            str: 文件路径
        """
        import os
        
        return os.path.join(self._storage_path, f"{snapshot_id}.json")
    
    def _get_state_index_file_path(self, state_id: str) -> str:
        """获取状态索引文件路径
        
        Args:
            state_id: 状态ID
            
        Returns:
            str: 文件路径
        """
        import os
        
        return os.path.join(self._storage_path, f"state_{state_id}.json")
    
    def save_snapshot(self, snapshot: StateSnapshot) -> None:
        """保存快照
        
        Args:
            snapshot: 状态快照
        """
        import json
        import os
        
        # 保存快照文件
        snapshot_file = self._get_snapshot_file_path(snapshot.id)
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)
        
        # 更新状态索引
        index_file = self._get_state_index_file_path(snapshot.state_id)
        snapshot_ids = []
        
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                snapshot_ids = json.load(f)
        
        if snapshot.id not in snapshot_ids:
            snapshot_ids.append(snapshot.id)
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_ids, f, indent=2)
    
    def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """获取快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[StateSnapshot]: 状态快照
        """
        import json
        import os
        
        snapshot_file = self._get_snapshot_file_path(snapshot_id)
        
        if not os.path.exists(snapshot_file):
            return None
        
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return StateSnapshot.from_dict(data)
        except Exception:
            return None
    
    def list_snapshots(self, 
                      state_id: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      limit: Optional[int] = None) -> List[StateSnapshot]:
        """列出快照
        
        Args:
            state_id: 状态ID（可选）
            tags: 标签过滤（可选）
            limit: 限制数量（可选）
            
        Returns:
            List[StateSnapshot]: 快照列表
        """
        import json
        import os
        import glob
        
        snapshots = []
        
        if state_id:
            # 获取特定状态的快照
            index_file = self._get_state_index_file_path(state_id)
            
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    snapshot_ids = json.load(f)
                
                for snapshot_id in snapshot_ids:
                    snapshot = self.get_snapshot(snapshot_id)
                    if snapshot:
                        snapshots.append(snapshot)
        else:
            # 获取所有快照
            pattern = os.path.join(self._storage_path, "*.json")
            state_files = glob.glob(pattern)
            
            for file_path in state_files:
                # 跳过状态索引文件
                if os.path.basename(file_path).startswith("state_"):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    snapshot = StateSnapshot.from_dict(data)
                    snapshots.append(snapshot)
                except Exception:
                    continue
        
        # 标签过滤
        if tags:
            filtered_snapshots = []
            for snapshot in snapshots:
                if any(tag in snapshot.tags for tag in tags):
                    filtered_snapshots.append(snapshot)
            snapshots = filtered_snapshots
        
        # 按创建时间排序（最新的在前）
        snapshots.sort(key=lambda x: x.created_at, reverse=True)
        
        # 应用限制
        if limit:
            snapshots = snapshots[:limit]
        
        return snapshots
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 是否删除成功
        """
        import json
        import os
        
        snapshot = self.get_snapshot(snapshot_id)
        
        if snapshot is None:
            return False
        
        # 删除快照文件
        snapshot_file = self._get_snapshot_file_path(snapshot_id)
        if os.path.exists(snapshot_file):
            os.remove(snapshot_file)
        
        # 更新状态索引
        index_file = self._get_state_index_file_path(snapshot.state_id)
        
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                snapshot_ids = json.load(f)
            
            if snapshot_id in snapshot_ids:
                snapshot_ids.remove(snapshot_id)
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_ids, f, indent=2)
        
        return True
    
    def delete_snapshots_by_state(self, state_id: str) -> int:
        """删除状态的所有快照
        
        Args:
            state_id: 状态ID
            
        Returns:
            int: 删除的快照数量
        """
        import json
        import os
        
        index_file = self._get_state_index_file_path(state_id)
        
        if not os.path.exists(index_file):
            return 0
        
        with open(index_file, 'r', encoding='utf-8') as f:
            snapshot_ids = json.load(f)
        
        deleted_count = 0
        
        # 删除所有快照文件
        for snapshot_id in snapshot_ids:
            snapshot_file = self._get_snapshot_file_path(snapshot_id)
            if os.path.exists(snapshot_file):
                os.remove(snapshot_file)
                deleted_count += 1
        
        # 删除状态索引文件
        os.remove(index_file)
        
        return deleted_count