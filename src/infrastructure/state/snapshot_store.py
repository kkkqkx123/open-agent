import pickle
import zlib
import json
import os
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from dataclasses import dataclass, field

from .interfaces import IStateSnapshotStore, StateSnapshot


class StateSnapshotStore(IStateSnapshotStore):
    """状态快照存储"""
    
    def __init__(self, storage_backend: str = "memory"):
        self.storage_backend = storage_backend
        self.db_connection = None
        self.storage_path = None
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
        db_path = os.path.join(os.getcwd(), "data", "snapshots.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_connection = sqlite3.connect(db_path, check_same_thread=False)
        self.db_connection.row_factory = sqlite3.Row
        
        cursor = self.db_connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                domain_state BLOB NOT NULL,
                timestamp TEXT NOT NULL,
                snapshot_name TEXT,
                compressed_data BLOB,
                size_bytes INTEGER,
                metadata TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON snapshots(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON snapshots(timestamp)")
        self.db_connection.commit()
        
        self.agent_snapshots: Dict[str, List[str]] = {}
    
    def _setup_file_storage(self):
        """设置文件存储"""
        self.storage_path = os.path.join(os.getcwd(), "data", "snapshots")
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.snapshots: Dict[str, StateSnapshot] = {}
        self.agent_snapshots: Dict[str, List[str]] = {}
    
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """保存快照"""
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
        elif self.storage_backend == "sqlite":
            return self._save_to_sqlite(snapshot)
        elif self.storage_backend == "file":
            return self._save_to_file(snapshot)
        return False
    
    def _save_to_memory(self, snapshot: StateSnapshot) -> bool:
        """保存到内存"""
        self.snapshots[snapshot.snapshot_id] = snapshot
        
        if snapshot.agent_id not in self.agent_snapshots:
            self.agent_snapshots[snapshot.agent_id] = []
        
        self.agent_snapshots[snapshot.agent_id].append(snapshot.snapshot_id)
        self._cleanup_old_snapshots(snapshot.agent_id, max_snapshots=50)
        
        return True
    
    def _save_to_sqlite(self, snapshot: StateSnapshot) -> bool:
        """保存到SQLite"""
        if not self.db_connection:
            return False
        cursor = self.db_connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO snapshots 
            (snapshot_id, agent_id, domain_state, timestamp, snapshot_name, compressed_data, size_bytes, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.snapshot_id,
            snapshot.agent_id,
            pickle.dumps(snapshot.domain_state),
            snapshot.timestamp.isoformat(),
            snapshot.snapshot_name,
            snapshot.compressed_data,
            snapshot.size_bytes,
            json.dumps(snapshot.metadata)
        ))
        self.db_connection.commit()
        
        if snapshot.agent_id not in self.agent_snapshots:
            self.agent_snapshots[snapshot.agent_id] = []
        self.agent_snapshots[snapshot.agent_id].append(snapshot.snapshot_id)
        
        return True
    
    def _save_to_file(self, snapshot: StateSnapshot) -> bool:
        """保存到文件"""
        if not self.storage_path:
            return False
        file_path = os.path.join(self.storage_path, f"{snapshot.snapshot_id}.pkl")
        with open(file_path, 'wb') as f:
            pickle.dump(snapshot, f)
        
        if snapshot.agent_id not in self.agent_snapshots:
            self.agent_snapshots[snapshot.agent_id] = []
        self.agent_snapshots[snapshot.agent_id].append(snapshot.snapshot_id)
        
        return True
    
    def _cleanup_old_snapshots(self, agent_id: str, max_snapshots: int = 50):
        """清理旧快照"""
        if agent_id in self.agent_snapshots:
            snapshots = self.agent_snapshots[agent_id]
            if len(snapshots) > max_snapshots:
                excess_count = len(snapshots) - max_snapshots
                for i in range(excess_count):
                    oldest_snapshot_id = snapshots.pop(0)
                    if oldest_snapshot_id in self.snapshots:
                        del self.snapshots[oldest_snapshot_id]
    
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载快照"""
        if self.storage_backend == "memory":
            return self._load_from_memory(snapshot_id)
        elif self.storage_backend == "sqlite":
            return self._load_from_sqlite(snapshot_id)
        elif self.storage_backend == "file":
            return self._load_from_file(snapshot_id)
        return None
    
    def _load_from_memory(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """从内存加载快照"""
        snapshot = self.snapshots.get(snapshot_id)
        if snapshot and snapshot.compressed_data:
            decompressed_data = self._decompress_data(snapshot.compressed_data)
            snapshot.domain_state = self._deserialize_state(decompressed_data)
        return snapshot
    
    def _load_from_sqlite(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """从SQLite加载快照"""
        if not self.db_connection:
            return None
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
        row = cursor.fetchone()
        
        if row:
            snapshot = StateSnapshot(
                snapshot_id=row['snapshot_id'],
                agent_id=row['agent_id'],
                domain_state=pickle.loads(row['domain_state']),
                timestamp=datetime.fromisoformat(row['timestamp']),
                snapshot_name=row['snapshot_name'],
                compressed_data=row['compressed_data'],
                size_bytes=row['size_bytes'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
            return snapshot
        return None
    
    def _load_from_file(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """从文件加载快照"""
        if not self.storage_path:
            return None
        file_path = os.path.join(self.storage_path, f"{snapshot_id}.pkl")
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定Agent的快照列表"""
        if self.storage_backend == "memory":
            return self._get_snapshots_from_memory(agent_id, limit)
        elif self.storage_backend == "sqlite":
            return self._get_snapshots_from_sqlite(agent_id, limit)
        elif self.storage_backend == "file":
            return self._get_snapshots_from_file(agent_id, limit)
        return []
    
    def _get_snapshots_from_memory(self, agent_id: str, limit: int) -> List[StateSnapshot]:
        """从内存获取快照列表"""
        if agent_id not in self.agent_snapshots:
            return []
        
        snapshot_ids = self.agent_snapshots[agent_id][-limit:]
        snapshots = []
        
        for snapshot_id in snapshot_ids:
            snapshot = self.snapshots.get(snapshot_id)
            if snapshot:
                if snapshot.compressed_data and not snapshot.domain_state:
                    decompressed_data = self._decompress_data(snapshot.compressed_data)
                    snapshot.domain_state = self._deserialize_state(decompressed_data)
                snapshots.append(snapshot)
        
        return snapshots
    
    def _get_snapshots_from_sqlite(self, agent_id: str, limit: int) -> List[StateSnapshot]:
        """从SQLite获取快照列表"""
        if not self.db_connection:
            return []
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT * FROM snapshots 
            WHERE agent_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (agent_id, limit))
        
        snapshots = []
        for row in cursor.fetchall():
            snapshot = StateSnapshot(
                snapshot_id=row['snapshot_id'],
                agent_id=row['agent_id'],
                domain_state=pickle.loads(row['domain_state']),
                timestamp=datetime.fromisoformat(row['timestamp']),
                snapshot_name=row['snapshot_name'],
                compressed_data=row['compressed_data'],
                size_bytes=row['size_bytes'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
            snapshots.append(snapshot)
        
        return snapshots
    
    def _get_snapshots_from_file(self, agent_id: str, limit: int) -> List[StateSnapshot]:
        """从文件获取快照列表"""
        if agent_id not in self.agent_snapshots:
            return []
        
        snapshot_ids = self.agent_snapshots[agent_id][-limit:]
        snapshots = []
        
        for snapshot_id in snapshot_ids:
            snapshot = self._load_from_file(snapshot_id)
            if snapshot:
                snapshots.append(snapshot)
        
        return snapshots