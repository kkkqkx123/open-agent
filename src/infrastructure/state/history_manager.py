import pickle
import zlib
import json
import os
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from dataclasses import dataclass, field

from .interfaces import IStateHistoryManager, StateHistoryEntry


class StateHistoryManager(IStateHistoryManager):
    """状态历史管理器"""
    
    def __init__(self, max_history_size: int = 1000, storage_backend: str = "memory"):
        self.max_history_size = max_history_size
        self.storage_backend = storage_backend
        self.db_connection: Optional[sqlite3.Connection] = None
        self.storage_path: Optional[str] = None
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
        self.history_entries: List[StateHistoryEntry] = []
        self.agent_history: Dict[str, List[str]] = {}
        self.history_index: Dict[str, StateHistoryEntry] = {}
    
    def _setup_sqlite_storage(self):
        """设置SQLite存储"""
        db_path = os.path.join(os.getcwd(), "data", "history.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_connection = sqlite3.connect(db_path, check_same_thread=False)
        self.db_connection.row_factory = sqlite3.Row
        
        cursor = self.db_connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                history_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                state_diff BLOB NOT NULL,
                compressed_diff BLOB,
                metadata TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON history(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON history(timestamp)")
        self.db_connection.commit()
        
        self.agent_history: Dict[str, List[str]] = {}
    
    def _setup_file_storage(self):
        """设置文件存储"""
        self.storage_path = os.path.join(os.getcwd(), "data", "history")
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.history_entries: List[StateHistoryEntry] = []
        self.agent_history: Dict[str, List[str]] = {}
        self.history_index: Dict[str, StateHistoryEntry] = {}
    
    def record_state_change(self, agent_id: str, old_state: Dict[str, Any], 
                          new_state: Dict[str, Any], action: str) -> str:
        """记录状态变化"""
        state_diff = self._calculate_state_diff(old_state, new_state)
        
        history_entry = StateHistoryEntry(
            history_id=self._generate_history_id(),
            agent_id=agent_id,
            timestamp=datetime.now(),
            action=action,
            state_diff=state_diff,
            metadata={
                "old_state_keys": list(old_state.keys()),
                "new_state_keys": list(new_state.keys())
            }
        )
        
        history_entry.compressed_diff = self._compress_diff(state_diff)
        self._save_history_entry(history_entry)
        self._cleanup_old_entries(agent_id)
        
        return history_entry.history_id
    
    def _calculate_state_diff(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """计算状态差异"""
        diff = {}
        
        for key, new_value in new_state.items():
            if key not in old_state:
                diff[f"added_{key}"] = new_value
            elif old_state[key] != new_value:
                diff[f"modified_{key}"] = {
                    "old": old_state[key],
                    "new": new_value
                }
        
        for key in old_state:
            if key not in new_state:
                diff[f"removed_{key}"] = old_state[key]
        
        return diff
    
    def _compress_diff(self, diff: Dict[str, Any]) -> bytes:
        """压缩差异数据"""
        serialized_diff = pickle.dumps(diff)
        return zlib.compress(serialized_diff)
    
    def _decompress_diff(self, compressed_diff: bytes) -> Dict[str, Any]:
        """解压缩差异数据"""
        decompressed_data = zlib.decompress(compressed_diff)
        return pickle.loads(decompressed_data)
    
    def _generate_history_id(self) -> str:
        """生成历史记录ID"""
        return str(uuid.uuid4())
    
    def _save_history_entry(self, entry: StateHistoryEntry):
        """保存历史记录"""
        if self.storage_backend == "memory":
            self._save_to_memory(entry)
        elif self.storage_backend == "sqlite":
            self._save_to_sqlite(entry)
        elif self.storage_backend == "file":
            self._save_to_file(entry)
    
    def _save_to_memory(self, entry: StateHistoryEntry):
        """保存到内存"""
        self.history_index[entry.history_id] = entry
        
        if entry.agent_id not in self.agent_history:
            self.agent_history[entry.agent_id] = []
        
        self.agent_history[entry.agent_id].append(entry.history_id)
        self.history_entries.append(entry)
    
    def _save_to_sqlite(self, entry: StateHistoryEntry):
        """保存到SQLite"""
        if self.db_connection is None:
            return
        cursor = self.db_connection.cursor()
        cursor.execute("""
            INSERT INTO history 
            (history_id, agent_id, timestamp, action, state_diff, compressed_diff, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.history_id,
            entry.agent_id,
            entry.timestamp.isoformat(),
            entry.action,
            pickle.dumps(entry.state_diff),
            entry.compressed_diff,
            json.dumps(entry.metadata)
        ))
        self.db_connection.commit()
        
        if entry.agent_id not in self.agent_history:
            self.agent_history[entry.agent_id] = []
        self.agent_history[entry.agent_id].append(entry.history_id)
    
    def _save_to_file(self, entry: StateHistoryEntry):
        """保存到文件"""
        if self.storage_path is None:
            return
        file_path = os.path.join(self.storage_path, f"{entry.history_id}.pkl")
        with open(file_path, 'wb') as f:
            pickle.dump(entry, f)
        
        if entry.agent_id not in self.agent_history:
            self.agent_history[entry.agent_id] = []
        self.agent_history[entry.agent_id].append(entry.history_id)
    
    def _cleanup_old_entries(self, agent_id: str):
        """清理旧记录"""
        if agent_id in self.agent_history:
            history_ids = self.agent_history[agent_id]
            if len(history_ids) > self.max_history_size:
                excess_count = len(history_ids) - self.max_history_size
                for i in range(excess_count):
                    oldest_history_id = history_ids.pop(0)
                    
                    if self.storage_backend == "memory":
                        if oldest_history_id in self.history_index:
                            del self.history_index[oldest_history_id]
                        self.history_entries = [
                            entry for entry in self.history_entries 
                            if entry.agent_id != agent_id or entry.history_id in history_ids
                        ]
                    elif self.storage_backend == "sqlite":
                        if self.db_connection is not None:
                            cursor = self.db_connection.cursor()
                            cursor.execute("DELETE FROM history WHERE history_id = ?", (oldest_history_id,))
                            self.db_connection.commit()
                    elif self.storage_backend == "file":
                        if self.storage_path is not None:
                            file_path = os.path.join(self.storage_path, f"{oldest_history_id}.pkl")
                            if os.path.exists(file_path):
                                os.remove(file_path)
    
    def get_state_history(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取状态历史"""
        if self.storage_backend == "memory":
            return self._get_from_memory(agent_id, limit)
        elif self.storage_backend == "sqlite":
            return self._get_from_sqlite(agent_id, limit)
        elif self.storage_backend == "file":
            return self._get_from_file(agent_id, limit)
        return []
    
    def _get_from_memory(self, agent_id: str, limit: int) -> List[StateHistoryEntry]:
        """从内存获取历史"""
        if agent_id not in self.agent_history:
            return []
        
        history_ids = self.agent_history[agent_id][-limit:]
        history_entries = []
        
        for history_id in history_ids:
            entry = self.history_index.get(history_id)
            if entry:
                if entry.compressed_diff and not entry.state_diff:
                    entry.state_diff = self._decompress_diff(entry.compressed_diff)
                history_entries.append(entry)
        
        history_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return history_entries
    
    def _get_from_sqlite(self, agent_id: str, limit: int) -> List[StateHistoryEntry]:
        """从SQLite获取历史"""
        if self.db_connection is None:
            return []
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT * FROM history 
            WHERE agent_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (agent_id, limit))
        
        history_entries = []
        for row in cursor.fetchall():
            entry = StateHistoryEntry(
                history_id=row['history_id'],
                agent_id=row['agent_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                action=row['action'],
                state_diff=pickle.loads(row['state_diff']),
                compressed_diff=row['compressed_diff'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
            history_entries.append(entry)
        
        return history_entries
    
    def _get_from_file(self, agent_id: str, limit: int) -> List[StateHistoryEntry]:
        """从文件获取历史"""
        if agent_id not in self.agent_history or self.storage_path is None:
            return []
        
        history_ids = self.agent_history[agent_id][-limit:]
        history_entries = []
        
        for history_id in history_ids:
            file_path = os.path.join(self.storage_path, f"{history_id}.pkl")
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    entry = pickle.load(f)
                    history_entries.append(entry)
        
        history_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return history_entries
    
    def replay_history(self, agent_id: str, base_state: Dict[str, Any], 
                      until_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """重放历史记录到指定时间点"""
        current_state = base_state.copy()
        history_entries = self.get_state_history(agent_id, limit=1000)
        
        history_entries.sort(key=lambda x: x.timestamp)
        
        for entry in history_entries:
            if until_timestamp and entry.timestamp > until_timestamp:
                break
            current_state = self._apply_state_diff(current_state, entry.state_diff)
        
        return current_state
    
    def _apply_state_diff(self, current_state: Dict[str, Any], diff: Dict[str, Any]) -> Dict[str, Any]:
        """应用状态差异"""
        new_state = current_state.copy()
        
        for key, value in diff.items():
            if key.startswith("added_"):
                new_key = key[6:]
                new_state[new_key] = value
            elif key.startswith("modified_"):
                new_key = key[9:]
                if isinstance(value, dict) and "new" in value:
                    new_state[new_key] = value["new"]
            elif key.startswith("removed_"):
                new_key = key[8:]
                if new_key in new_state:
                    del new_state[new_key]
        
        return new_state