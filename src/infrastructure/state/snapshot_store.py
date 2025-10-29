import pickle
import zlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from dataclasses import dataclass, field


@dataclass
class StateSnapshot:
    """状态快照"""
    snapshot_id: str
    agent_id: str
    domain_state: Dict[str, Any]  # 序列化的域状态
    timestamp: datetime
    snapshot_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 性能优化字段
    compressed_data: Optional[bytes] = None
    size_bytes: int = 0


class StateSnapshotStore:
    """状态快照存储"""
    
    def __init__(self, storage_backend: str = "memory"):
        self.storage_backend = storage_backend
        self._setup_storage()
    
    def _setup_storage(self):
        """设置存储后端"""
        if self.storage_backend == "memory":
            self._setup_memory_storage()
        elif self.storage_backend == "sqlite":
            self._setup_sqlite_storage()
        elif self.storage_backend == "file":
            self._setup_file_storage()
    
    def _setup_memory_storage(self):
        """设置内存存储"""
        self.snapshots: Dict[str, StateSnapshot] = {}
        self.agent_snapshots: Dict[str, List[str]] = {}
    
    def _setup_sqlite_storage(self):
        """设置SQLite存储"""
        # 占位实现，实际实现将在后续添加
        self._setup_memory_storage()
    
    def _setup_file_storage(self):
        """设置文件存储"""
        # 占位实现，实际实现将在后续添加
        self._setup_memory_storage()
    
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """保存快照"""
        # 序列化状态
        serialized_state = self._serialize_state(snapshot.domain_state)
        compressed_data = self._compress_data(serialized_state)
        
        snapshot.compressed_data = compressed_data
        snapshot.size_bytes = len(compressed_data)
        
        return self._save_to_backend(snapshot)
    
    def _serialize_state(self, state: Dict[str, Any]) -> bytes:
        """序列化状态"""
        return pickle.dumps(state)
    
    def _compress_data(self, data: bytes) -> bytes:
        """压缩数据"""
        return zlib.compress(data)
    
    def _decompress_data(self, compressed_data: bytes) -> bytes:
        """解压缩数据"""
        return zlib.decompress(compressed_data)
    
    def _deserialize_state(self, data: bytes) -> Dict[str, Any]:
        """反序列化状态"""
        return pickle.loads(data)
    
    def _save_to_backend(self, snapshot: StateSnapshot) -> bool:
        """保存到后端存储"""
        if self.storage_backend == "memory":
            return self._save_to_memory(snapshot)
        else:
            # 其他存储后端的实现
            return self._save_to_memory(snapshot)
    
    def _save_to_memory(self, snapshot: StateSnapshot) -> bool:
        """保存到内存"""
        self.snapshots[snapshot.snapshot_id] = snapshot
        
        # 管理Agent的快照列表
        if snapshot.agent_id not in self.agent_snapshots:
            self.agent_snapshots[snapshot.agent_id] = []
        
        self.agent_snapshots[snapshot.agent_id].append(snapshot.snapshot_id)
        
        # 清理旧快照（保留最新的50个）
        self._cleanup_old_snapshots(snapshot.agent_id, max_snapshots=50)
        
        return True
    
    def _cleanup_old_snapshots(self, agent_id: str, max_snapshots: int = 50):
        """清理旧快照"""
        if agent_id in self.agent_snapshots:
            snapshots = self.agent_snapshots[agent_id]
            if len(snapshots) > max_snapshots:
                # 删除最旧的快照
                excess_count = len(snapshots) - max_snapshots
                for i in range(excess_count):
                    oldest_snapshot_id = snapshots.pop(0)
                    if oldest_snapshot_id in self.snapshots:
                        del self.snapshots[oldest_snapshot_id]
    
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载快照"""
        if self.storage_backend == "memory":
            return self._load_from_memory(snapshot_id)
        else:
            # 其他存储后端的实现
            return self._load_from_memory(snapshot_id)
    
    def _load_from_memory(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """从内存加载快照"""
        snapshot = self.snapshots.get(snapshot_id)
        if snapshot and snapshot.compressed_data:
            decompressed_data = self._decompress_data(snapshot.compressed_data)
            snapshot.domain_state = self._deserialize_state(decompressed_data)
        return snapshot
    
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定Agent的快照列表"""
        if self.storage_backend == "memory":
            return self._get_snapshots_from_memory(agent_id, limit)
        else:
            # 其他存储后端的实现
            return self._get_snapshots_from_memory(agent_id, limit)
    
    def _get_snapshots_from_memory(self, agent_id: str, limit: int) -> List[StateSnapshot]:
        """从内存获取快照列表"""
        if agent_id not in self.agent_snapshots:
            return []
        
        snapshot_ids = self.agent_snapshots[agent_id][-limit:]  # 获取最新的快照
        snapshots = []
        
        for snapshot_id in snapshot_ids:
            snapshot = self.snapshots.get(snapshot_id)
            if snapshot:
                # 如果需要，解压缩数据
                if snapshot.compressed_data and not snapshot.domain_state:
                    decompressed_data = self._decompress_data(snapshot.compressed_data)
                    snapshot.domain_state = self._deserialize_state(decompressed_data)
                snapshots.append(snapshot)
        
        return snapshots