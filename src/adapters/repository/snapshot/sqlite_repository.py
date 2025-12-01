"""SQLite快照Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ISnapshotRepository
from ..sqlite_base import SQLiteBaseRepository
from ..utils import JsonUtils, TimeUtils, IdUtils, SQLiteUtils


class SQLiteSnapshotRepository(SQLiteBaseRepository, ISnapshotRepository):
    """SQLite快照Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite快照Repository"""
        table_sql = """
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                workflow_id TEXT,
                timestamp TEXT NOT NULL,
                state_data TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_snapshots_thread_id ON snapshots(thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON snapshots(created_at)"
        ]
        
        super().__init__(config, "snapshots", table_sql, indexes_sql)
    
    async def save_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """保存快照"""
        try:
            def _save():
                snapshot_id = IdUtils.get_or_generate_id(
                    snapshot, "snapshot_id", IdUtils.generate_snapshot_id
                )
                
                data = {
                    "snapshot_id": snapshot_id,
                    "thread_id": snapshot["thread_id"],
                    "workflow_id": snapshot.get("workflow_id"),
                    "timestamp": snapshot.get("timestamp", TimeUtils.now_iso()),
                    "state_data": JsonUtils.serialize(snapshot["state_data"]),
                    "metadata": JsonUtils.serialize(snapshot.get("metadata", {}))
                }
                
                self._insert_or_replace(data)
                self._log_operation("快照保存", True, snapshot_id)
                return snapshot_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存快照", e)
            raise # 重新抛出异常，不会到达下一行
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照"""
        try:
            def _load():
                row = self._find_by_id("snapshot_id", snapshot_id)
                if row:
                    return {
                        "snapshot_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "timestamp": row[3],
                        "state_data": JsonUtils.deserialize(row[4]),
                        "metadata": JsonUtils.deserialize(row[5]),
                        "created_at": row[6]
                    }
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载快照", e)
            raise  # 重新抛出异常
    
    async def get_snapshots(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取线程的快照列表"""
        try:
            def _get():
                query = """
                    SELECT snapshot_id, thread_id, workflow_id,
                           timestamp, state_data, metadata, created_at
                    FROM snapshots
                    WHERE thread_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (thread_id, limit))
                
                snapshots = []
                for row in results:
                    snapshots.append({
                        "snapshot_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "timestamp": row[3],
                        "state_data": JsonUtils.deserialize(row[4]),
                        "metadata": JsonUtils.deserialize(row[5]),
                        "created_at": row[6]
                    })
                
                self._log_operation("获取快照列表", True, f"{thread_id}, 共{len(snapshots)}条")
                return snapshots
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取快照列表", e)
            raise  # 重新抛出异常
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            def _delete():
                deleted = self._delete_by_id("snapshot_id", snapshot_id)
                self._log_operation("快照删除", deleted, snapshot_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除快照", e)
            raise # 重新抛出异常
    
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            def _get_stats():
                # 总快照数
                total_count = self._count_records()
                
                # 按线程统计
                top_threads_results = SQLiteUtils.get_top_records(
                    self.db_path, self.table_name, "thread_id", "created_at", 10
                )
                top_threads = [{"thread_id": row[0], "count": row[1]} for row in top_threads_results]
                
                stats = {
                    "total_count": total_count,
                    "thread_count": len(top_threads),
                    "top_threads": top_threads
                }
                
                self._log_operation("获取快照统计信息", True)
                return stats
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_stats)
            
        except Exception as e:
            self._handle_exception("获取快照统计信息", e)
            raise # 重新抛出异常