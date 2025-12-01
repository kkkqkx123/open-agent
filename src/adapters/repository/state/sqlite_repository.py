"""SQLite状态Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository.state import IStateRepository
from src.interfaces.state.interfaces import IState
from src.core.state.entities import StateSnapshot, StateHistoryEntry, StateDiff
from ..sqlite_base import SQLiteBaseRepository
from ..utils import JsonUtils, TimeUtils, SQLiteUtils


class SQLiteStateRepository(SQLiteBaseRepository, IStateRepository):
    """SQLite状态Repository实现"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化SQLite状态Repository"""
        # 状态表
        states_table_sql = """
            CREATE TABLE IF NOT EXISTS states (
                state_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        # 快照表
        snapshots_table_sql = """
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                domain_state TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                snapshot_name TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        # 历史记录表
        history_table_sql = """
            CREATE TABLE IF NOT EXISTS history (
                history_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                state_diff TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        super().__init__(config, "states", states_table_sql)
        
        # 创建额外的表
        self._create_additional_tables(snapshots_table_sql, history_table_sql)
    
    def _create_additional_tables(self, snapshots_sql: str, history_sql: str) -> None:
        """创建额外的表"""
        try:
            SQLiteUtils.execute_update(self.db_path, snapshots_sql)
            SQLiteUtils.execute_update(self.db_path, history_sql)
        except Exception as e:
            self._handle_exception("创建额外表", e)
            raise
    
    async def save_state(self, state_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态
        
        Args:
            state_id: 状态ID
            state_data: 状态数据
            
        Returns:
            保存的状态ID
        """
        try:
            def _save() -> str:
                data = {
                    "state_id": state_id,
                    "state_data": JsonUtils.serialize(state_data),
                    "updated_at": TimeUtils.now_iso()
                }
                
                self._insert_or_replace(data)
                self._log_operation("状态保存", True, state_id)
                return state_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存状态", e)
            raise  # 重新抛出异常，不会到达下一行
    
    async def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """加载状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态数据，如果不存在则返回None
        """
        try:
            def _load() -> Optional[Dict[str, Any]]:
                row = self._find_by_id("state_id", state_id)
                if row:
                    return JsonUtils.deserialize(row[1])
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载状态", e)
            raise  # 重新抛出异常
    
    async def delete_state(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            是否删除成功
        """
        try:
            def _delete() -> bool:
                deleted = self._delete_by_id("state_id", state_id)
                self._log_operation("状态删除", deleted, state_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除状态", e)
            raise # 重新抛出异常
    
    async def exists_state(self, state_id: str) -> bool:
        """检查状态是否存在
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态是否存在
        """
        try:
            def _exists() -> bool:
                query = "SELECT 1 FROM states WHERE state_id = ?"
                results = SQLiteUtils.execute_query(self.db_path, query, (state_id,))
                exists = len(results) > 0
                return exists
            
            return await asyncio.get_event_loop().run_in_executor(None, _exists)
            
        except Exception as e:
            self._handle_exception("检查状态存在性", e)
            raise # 重新抛出异常
    
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            状态列表
        """
        try:
            def _list() -> List[Dict[str, Any]]:
                query = """
                    SELECT state_id, state_data, created_at, updated_at
                    FROM states
                    ORDER BY updated_at DESC
                    LIMIT ?
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (limit,))
                
                states = []
                for row in results:
                    states.append({
                        "state_id": row[0],
                        "state_data": JsonUtils.deserialize(row[1]),
                        "created_at": row[2],
                        "updated_at": row[3]
                    })
                
                self._log_operation("列出状态", True, f"共{len(states)}条")
                return states
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出状态", e)
            raise # 重新抛出异常
    
    async def save_snapshot(self, snapshot: StateSnapshot) -> str:
        """保存状态快照
        
        Args:
            snapshot: 状态快照
            
        Returns:
            快照ID
        """
        try:
            def _save() -> str:
                data = {
                    "snapshot_id": snapshot.snapshot_id,
                    "thread_id": snapshot.thread_id,
                    "domain_state": JsonUtils.serialize(snapshot.domain_state),
                    "timestamp": snapshot.timestamp,
                    "snapshot_name": snapshot.snapshot_name,
                    "metadata": JsonUtils.serialize(snapshot.metadata) if snapshot.metadata else None
                }
                
                query = """
                    INSERT OR REPLACE INTO snapshots
                    (snapshot_id, thread_id, domain_state, timestamp, snapshot_name, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                SQLiteUtils.execute_update(self.db_path, query, (
                    data["snapshot_id"],
                    data["thread_id"],
                    data["domain_state"],
                    data["timestamp"],
                    data["snapshot_name"],
                    data["metadata"]
                ))
                
                self._log_operation("快照保存", True, snapshot.snapshot_id)
                return snapshot.snapshot_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存快照", e)
            raise
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态快照，如果不存在则返回None
        """
        try:
            def _load() -> Optional[StateSnapshot]:
                query = """
                    SELECT snapshot_id, thread_id, domain_state, timestamp, snapshot_name, metadata
                    FROM snapshots
                    WHERE snapshot_id = ?
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (snapshot_id,))
                
                if results:
                    row = results[0]
                    return StateSnapshot(
                        snapshot_id=row[0],
                        thread_id=row[1],
                        domain_state=JsonUtils.deserialize(row[2]),
                        timestamp=row[3],
                        snapshot_name=row[4] or "",
                        metadata=JsonUtils.deserialize(row[5]) if row[5] else {}
                    )
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载快照", e)
            raise
    
    async def save_history_entry(self, entry: StateHistoryEntry) -> str:
        """保存状态历史记录
        
        Args:
            entry: 状态历史记录
            
        Returns:
            历史记录ID
        """
        try:
            def _save() -> str:
                data = {
                    "history_id": entry.history_id,
                    "thread_id": entry.thread_id,
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "state_diff": JsonUtils.serialize(entry.state_diff),
                    "metadata": JsonUtils.serialize(entry.metadata) if entry.metadata else None
                }
                
                query = """
                    INSERT OR REPLACE INTO history
                    (history_id, thread_id, timestamp, action, state_diff, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                SQLiteUtils.execute_update(self.db_path, query, (
                    data["history_id"],
                    data["thread_id"],
                    data["timestamp"],
                    data["action"],
                    data["state_diff"],
                    data["metadata"]
                ))
                
                self._log_operation("历史记录保存", True, entry.history_id)
                return entry.history_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存历史记录", e)
            raise
    
    async def list_history_entries(self, thread_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """列出线程的历史记录
        
        Args:
            thread_id: 线程ID
            limit: 返回记录数限制
            
        Returns:
            历史记录列表
        """
        try:
            def _list() -> List[StateHistoryEntry]:
                query = """
                    SELECT history_id, thread_id, timestamp, action, state_diff, metadata
                    FROM history
                    WHERE thread_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (thread_id, limit))
                
                entries = []
                for row in results:
                    entries.append(StateHistoryEntry(
                        history_id=row[0],
                        thread_id=row[1],
                        timestamp=row[2],
                        action=row[3],
                        state_diff=JsonUtils.deserialize(row[4]),
                        metadata=JsonUtils.deserialize(row[5]) if row[5] else {}
                    ))
                
                self._log_operation("列出历史记录", True, f"共{len(entries)}条")
                return entries
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出历史记录", e)
            raise