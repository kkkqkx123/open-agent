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
            def _save() -> str:
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
            def _load() -> Optional[Dict[str, Any]]:
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
            def _get() -> List[Dict[str, Any]]:
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
            def _delete() -> bool:
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
            def _get_stats() -> Dict[str, Any]:
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
    
    async def delete_snapshots_by_thread(self, thread_id: str) -> int:
        """删除线程的所有快照"""
        try:
            def _delete() -> int:
                query = "DELETE FROM snapshots WHERE thread_id = ?"
                deleted_count = SQLiteUtils.execute_update(self.db_path, query, (thread_id,))
                
                self._log_operation("删除线程快照", True, f"{thread_id}, 共{deleted_count}条")
                return deleted_count
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除线程快照", e)
            raise # 重新抛出异常
    
    async def get_latest_snapshot(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取线程的最新快照"""
        try:
            def _get() -> Optional[Dict[str, Any]]:
                query = """
                    SELECT snapshot_id, thread_id, workflow_id,
                           timestamp, state_data, metadata, created_at
                    FROM snapshots
                    WHERE thread_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (thread_id,))
                
                if not results:
                    return None
                
                row = results[0]
                snapshot = {
                    "snapshot_id": row[0],
                    "thread_id": row[1],
                    "workflow_id": row[2],
                    "timestamp": row[3],
                    "state_data": JsonUtils.deserialize(row[4]),
                    "metadata": JsonUtils.deserialize(row[5]),
                    "created_at": row[6]
                }
                
                self._log_operation("获取最新快照", True, f"{thread_id}")
                return snapshot
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取最新快照", e)
            raise # 重新抛出异常
    
    async def cleanup_old_snapshots(self, thread_id: str, max_count: int) -> int:
        """清理旧的快照，保留最新的max_count个"""
        try:
            def _cleanup() -> int:
                # 先获取所有快照，按创建时间排序
                query = """
                    SELECT snapshot_id FROM snapshots
                    WHERE thread_id = ?
                    ORDER BY created_at DESC
                """
                all_snapshots = SQLiteUtils.execute_query(self.db_path, query, (thread_id,))
                
                if len(all_snapshots) <= max_count:
                    return 0
                
                # 获取要删除的快照ID（除了最新的max_count个）
                to_delete_ids = [row[0] for row in all_snapshots[max_count:]]
                
                if not to_delete_ids:
                    return 0
                
                # 构建删除查询
                placeholders = ",".join(["?" for _ in to_delete_ids])
                delete_query = f"DELETE FROM snapshots WHERE snapshot_id IN ({placeholders})"
                
                deleted_count = SQLiteUtils.execute_update(self.db_path, delete_query, tuple(to_delete_ids))
                
                self._log_operation("清理旧快照", True, f"{thread_id}, 删除{deleted_count}条")
                return deleted_count
            
            return await asyncio.get_event_loop().run_in_executor(None, _cleanup)
            
        except Exception as e:
            self._handle_exception("清理旧快照", e)
            raise # 重新抛出异常
    
    async def get_snapshot_comparison(
        self,
        snapshot_id1: str,
        snapshot_id2: str
    ) -> Dict[str, Any]:
        """比较两个快照"""
        try:
            snapshot1 = await self.load_snapshot(snapshot_id1)
            snapshot2 = await self.load_snapshot(snapshot_id2)
            
            if not snapshot1 or not snapshot2:
                return {
                    "error": "一个或两个快照不存在",
                    "snapshot1_exists": snapshot1 is not None,
                    "snapshot2_exists": snapshot2 is not None
                }
            
            # 简单的状态数据比较
            state1 = snapshot1.get("state_data", {})
            state2 = snapshot2.get("state_data", {})
            
            comparison = {
                "snapshot_id1": snapshot_id1,
                "snapshot_id2": snapshot_id2,
                "timestamp1": snapshot1.get("timestamp"),
                "timestamp2": snapshot2.get("timestamp"),
                "thread_id1": snapshot1.get("thread_id"),
                "thread_id2": snapshot2.get("thread_id"),
                "state_equal": state1 == state2,
                "metadata_equal": snapshot1.get("metadata") == snapshot2.get("metadata")
            }
            
            self._log_operation("快照比较", True, f"{snapshot_id1} vs {snapshot_id2}")
            return comparison
            
        except Exception as e:
            self._handle_exception("快照比较", e)
            raise # 重新抛出异常
    
    async def validate_snapshot_integrity(self, snapshot_id: str) -> bool:
        """验证快照完整性"""
        try:
            snapshot = await self.load_snapshot(snapshot_id)
            
            if not snapshot:
                return False
            
            # 检查必需字段
            required_fields = ["snapshot_id", "thread_id", "state_data", "timestamp"]
            for field in required_fields:
                if field not in snapshot:
                    self._log_operation("快照完整性验证", False, f"{snapshot_id}, 缺少字段: {field}")
                    return False
            
            # 检查时间戳格式 - 简单验证，不依赖可能不存在的方法
            timestamp = snapshot.get("timestamp")
            if not timestamp or not isinstance(timestamp, str):
                self._log_operation("快照完整性验证", False, f"{snapshot_id}, 无效时间戳")
                return False
            
            self._log_operation("快照完整性验证", True, snapshot_id)
            return True
            
        except Exception as e:
            self._handle_exception("快照完整性验证", e)
            raise # 重新抛出异常