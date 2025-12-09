"""历史存储

提供历史记录的存储接口和实现。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


class HistoryEntry:
    """历史记录条目
    
    表示一次状态变化的记录。
    """
    
    def __init__(self,
                 state_id: str,
                 operation: str,
                 data: Dict[str, Any],
                 context: Optional[Dict[str, Any]] = None,
                 timestamp: Optional[datetime] = None,
                 version: Optional[int] = None) -> None:
        """初始化历史记录条目
        
        Args:
            state_id: 状态ID
            operation: 操作类型
            data: 状态数据
            context: 上下文信息
            timestamp: 时间戳
            version: 版本号
        """
        self.id = str(uuid4())
        self.state_id = state_id
        self.operation = operation
        self.data = data.copy()
        self.context = context or {}
        self.timestamp = timestamp or datetime.now()
        self.version = version
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "id": self.id,
            "state_id": self.state_id,
            "operation": self.operation,
            "data": self.data,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """从字典创建历史记录条目
        
        Args:
            data: 字典数据
            
        Returns:
            HistoryEntry: 历史记录条目
        """
        timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        
        return cls(
            state_id=data["state_id"],
            operation=data["operation"],
            data=data["data"],
            context=data.get("context", {}),
            timestamp=timestamp,
            version=data.get("version")
        )


class IHistoryStorage(ABC):
    """历史存储接口
    
    定义历史记录存储的抽象接口。
    """
    
    @abstractmethod
    def save_history_entry(self, entry: HistoryEntry) -> None:
        """保存历史记录条目
        
        Args:
            entry: 历史记录条目
        """
        pass
    
    @abstractmethod
    def get_history_entry(self, entry_id: str) -> Optional[HistoryEntry]:
        """获取历史记录条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            Optional[HistoryEntry]: 历史记录条目
        """
        pass
    
    @abstractmethod
    def get_state_history(self, state_id: str, limit: Optional[int] = None) -> List[HistoryEntry]:
        """获取状态历史
        
        Args:
            state_id: 状态ID
            limit: 限制数量
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        pass
    
    @abstractmethod
    def get_state_history_before(self, state_id: str, timestamp: datetime) -> List[HistoryEntry]:
        """获取指定时间之前的状态历史
        
        Args:
            state_id: 状态ID
            timestamp: 时间戳
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        pass
    
    @abstractmethod
    def get_state_history_up_to_version(self, state_id: str, version: int) -> List[HistoryEntry]:
        """获取指定版本之前的状态历史
        
        Args:
            state_id: 状态ID
            version: 版本号
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        pass
    
    @abstractmethod
    def delete_history_entry(self, entry_id: str) -> bool:
        """删除历史记录条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    def clear_state_history(self, state_id: str) -> None:
        """清除状态历史
        
        Args:
            state_id: 状态ID
        """
        pass
    
    @abstractmethod
    def get_all_state_ids(self) -> List[str]:
        """获取所有状态ID
        
        Returns:
            List[str]: 状态ID列表
        """
        pass


class MemoryHistoryStorage(IHistoryStorage):
    """内存历史存储
    
    将历史记录存储在内存中。
    """
    
    def __init__(self) -> None:
        """初始化内存存储"""
        self._entries: Dict[str, HistoryEntry] = {}
        self._state_history: Dict[str, List[str]] = {}
    
    def save_history_entry(self, entry: HistoryEntry) -> None:
        """保存历史记录条目
        
        Args:
            entry: 历史记录条目
        """
        self._entries[entry.id] = entry
        
        # 更新状态历史索引
        if entry.state_id not in self._state_history:
            self._state_history[entry.state_id] = []
        
        if entry.id not in self._state_history[entry.state_id]:
            self._state_history[entry.state_id].append(entry.id)
    
    def get_history_entry(self, entry_id: str) -> Optional[HistoryEntry]:
        """获取历史记录条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            Optional[HistoryEntry]: 历史记录条目
        """
        return self._entries.get(entry_id)
    
    def get_state_history(self, state_id: str, limit: Optional[int] = None) -> List[HistoryEntry]:
        """获取状态历史
        
        Args:
            state_id: 状态ID
            limit: 限制数量
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        entry_ids = self._state_history.get(state_id, [])
        
        if not entry_ids:
            return []
        
        # 获取所有条目
        entries = [self._entries[entry_id] for entry_id in entry_ids if entry_id in self._entries]
        
        # 按版本号排序
        entries.sort(key=lambda x: x.version or 0)
        
        # 应用限制
        if limit:
            entries = entries[-limit:]
        
        return entries
    
    def get_state_history_before(self, state_id: str, timestamp: datetime) -> List[HistoryEntry]:
        """获取指定时间之前的状态历史
        
        Args:
            state_id: 状态ID
            timestamp: 时间戳
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        entries = self.get_state_history(state_id)
        
        # 过滤出指定时间之前的条目
        filtered_entries = [entry for entry in entries if entry.timestamp <= timestamp]
        
        return filtered_entries
    
    def get_state_history_up_to_version(self, state_id: str, version: int) -> List[HistoryEntry]:
        """获取指定版本之前的状态历史
        
        Args:
            state_id: 状态ID
            version: 版本号
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        entries = self.get_state_history(state_id)
        
        # 过滤出指定版本之前的条目
        filtered_entries = [entry for entry in entries if (entry.version or 0) <= version]
        
        return filtered_entries
    
    def delete_history_entry(self, entry_id: str) -> bool:
        """删除历史记录条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            bool: 是否删除成功
        """
        if entry_id not in self._entries:
            return False
        
        entry = self._entries[entry_id]
        
        # 从主存储中删除
        del self._entries[entry_id]
        
        # 从状态历史索引中删除
        if entry.state_id in self._state_history:
            if entry_id in self._state_history[entry.state_id]:
                self._state_history[entry.state_id].remove(entry_id)
            
            # 如果状态没有历史记录了，删除状态条目
            if not self._state_history[entry.state_id]:
                del self._state_history[entry.state_id]
        
        return True
    
    def clear_state_history(self, state_id: str) -> None:
        """清除状态历史
        
        Args:
            state_id: 状态ID
        """
        if state_id not in self._state_history:
            return
        
        entry_ids = self._state_history[state_id]
        
        # 删除所有相关条目
        for entry_id in entry_ids:
            if entry_id in self._entries:
                del self._entries[entry_id]
        
        # 删除状态历史索引
        del self._state_history[state_id]
    
    def get_all_state_ids(self) -> List[str]:
        """获取所有状态ID
        
        Returns:
            List[str]: 状态ID列表
        """
        return list(self._state_history.keys())


class SQLiteHistoryStorage(IHistoryStorage):
    """SQLite历史存储
    
    将历史记录存储在SQLite数据库中。
    """
    
    def __init__(self, database_path: str = ":memory:") -> None:
        """初始化SQLite存储
        
        Args:
            database_path: 数据库路径
        """
        self._database_path = database_path
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库"""
        import sqlite3
        
        with sqlite3.connect(self._database_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history_entries (
                    id TEXT PRIMARY KEY,
                    state_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    data TEXT NOT NULL,
                    context TEXT,
                    timestamp TEXT NOT NULL,
                    version INTEGER
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_id ON history_entries(state_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON history_entries(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_version ON history_entries(version)
            """)
            
            conn.commit()
    
    def save_history_entry(self, entry: HistoryEntry) -> None:
        """保存历史记录条目
        
        Args:
            entry: 历史记录条目
        """
        import json
        import sqlite3
        
        with sqlite3.connect(self._database_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO history_entries 
                (id, state_id, operation, data, context, timestamp, version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.state_id,
                entry.operation,
                json.dumps(entry.data),
                json.dumps(entry.context),
                entry.timestamp.isoformat(),
                entry.version
            ))
            
            conn.commit()
    
    def get_history_entry(self, entry_id: str) -> Optional[HistoryEntry]:
        """获取历史记录条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            Optional[HistoryEntry]: 历史记录条目
        """
        import json
        import sqlite3
        from datetime import datetime
        
        with sqlite3.connect(self._database_path) as conn:
            cursor = conn.execute("""
                SELECT id, state_id, operation, data, context, timestamp, version
                FROM history_entries
                WHERE id = ?
            """, (entry_id,))
            
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return HistoryEntry(
                state_id=row[1],
                operation=row[2],
                data=json.loads(row[3]),
                context=json.loads(row[4]),
                timestamp=datetime.fromisoformat(row[5]),
                version=row[6]
            )
    
    def get_state_history(self, state_id: str, limit: Optional[int] = None) -> List[HistoryEntry]:
        """获取状态历史
        
        Args:
            state_id: 状态ID
            limit: 限制数量
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        import json
        import sqlite3
        from datetime import datetime
        
        with sqlite3.connect(self._database_path) as conn:
            query = """
                SELECT id, state_id, operation, data, context, timestamp, version
                FROM history_entries
                WHERE state_id = ?
                ORDER BY version
            """
            
            params: List[Any] = [state_id]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entry = HistoryEntry(
                    state_id=row[1],
                    operation=row[2],
                    data=json.loads(row[3]),
                    context=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    version=row[6]
                )
                entries.append(entry)
            
            return entries
    
    def get_state_history_before(self, state_id: str, timestamp: datetime) -> List[HistoryEntry]:
        """获取指定时间之前的状态历史
        
        Args:
            state_id: 状态ID
            timestamp: 时间戳
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        import json
        import sqlite3
        from datetime import datetime
        
        with sqlite3.connect(self._database_path) as conn:
            cursor = conn.execute("""
                SELECT id, state_id, operation, data, context, timestamp, version
                FROM history_entries
                WHERE state_id = ? AND timestamp <= ?
                ORDER BY version
            """, (state_id, timestamp.isoformat()))
            
            rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entry = HistoryEntry(
                    state_id=row[1],
                    operation=row[2],
                    data=json.loads(row[3]),
                    context=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    version=row[6]
                )
                entries.append(entry)
            
            return entries
    
    def get_state_history_up_to_version(self, state_id: str, version: int) -> List[HistoryEntry]:
        """获取指定版本之前的状态历史
        
        Args:
            state_id: 状态ID
            version: 版本号
            
        Returns:
            List[HistoryEntry]: 历史记录条目列表
        """
        import json
        import sqlite3
        from datetime import datetime
        
        with sqlite3.connect(self._database_path) as conn:
            cursor = conn.execute("""
                SELECT id, state_id, operation, data, context, timestamp, version
                FROM history_entries
                WHERE state_id = ? AND version <= ?
                ORDER BY version
            """, (state_id, version))
            
            rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entry = HistoryEntry(
                    state_id=row[1],
                    operation=row[2],
                    data=json.loads(row[3]),
                    context=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    version=row[6]
                )
                entries.append(entry)
            
            return entries
    
    def delete_history_entry(self, entry_id: str) -> bool:
        """删除历史记录条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            bool: 是否删除成功
        """
        import sqlite3
        
        with sqlite3.connect(self._database_path) as conn:
            cursor = conn.execute("""
                DELETE FROM history_entries WHERE id = ?
            """, (entry_id,))
            
            conn.commit()
            
            return cursor.rowcount > 0
    
    def clear_state_history(self, state_id: str) -> None:
        """清除状态历史
        
        Args:
            state_id: 状态ID
        """
        import sqlite3
        
        with sqlite3.connect(self._database_path) as conn:
            conn.execute("""
                DELETE FROM history_entries WHERE state_id = ?
            """, (state_id,))
            
            conn.commit()
    
    def get_all_state_ids(self) -> List[str]:
        """获取所有状态ID
        
        Returns:
            List[str]: 状态ID列表
        """
        import sqlite3
        
        with sqlite3.connect(self._database_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT state_id FROM history_entries
            """)
            
            rows = cursor.fetchall()
            
            return [row[0] for row in rows]