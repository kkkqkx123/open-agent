"""SQLite检查点Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ICheckpointRepository
from ..sqlite_base import SQLiteBaseRepository
from ..utils import JsonUtils, TimeUtils, IdUtils, SQLiteUtils


class SQLiteCheckpointRepository(SQLiteBaseRepository, ICheckpointRepository):
    """SQLite检查点Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite检查点Repository"""
        table_sql = """
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                workflow_id TEXT,
                checkpoint_data TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_id ON checkpoints(workflow_id)",
            "CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at)"
        ]
        
        super().__init__(config, "checkpoints", table_sql, indexes_sql)
    
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存checkpoint数据"""
        try:
            def _save():
                checkpoint_id = IdUtils.get_or_generate_id(
                    checkpoint_data, "checkpoint_id", IdUtils.generate_checkpoint_id
                )
                
                data = {
                    "checkpoint_id": checkpoint_id,
                    "thread_id": checkpoint_data["thread_id"],
                    "workflow_id": checkpoint_data.get("workflow_id"),
                    "checkpoint_data": JsonUtils.serialize(checkpoint_data["checkpoint_data"]),
                    "metadata": JsonUtils.serialize(checkpoint_data.get("metadata", {})),
                    "updated_at": TimeUtils.now_iso()
                }
                
                self._insert_or_replace(data)
                self._log_operation("检查点保存", True, checkpoint_id)
                return checkpoint_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存检查点", e)
            raise # 重新抛出异常，不会到达下一行
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        try:
            def _load():
                row = self._find_by_id("checkpoint_id", checkpoint_id)
                if row:
                    return {
                        "checkpoint_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "checkpoint_data": JsonUtils.deserialize(row[3]),
                        "metadata": JsonUtils.deserialize(row[4]),
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载检查点", e)
            raise  # 重新抛出异常
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出指定thread的所有checkpoint"""
        try:
            def _list():
                query = """
                    SELECT checkpoint_id, thread_id, workflow_id, checkpoint_data, 
                           metadata, created_at, updated_at
                    FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY created_at DESC
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (thread_id,))
                
                checkpoints = []
                for row in results:
                    checkpoints.append({
                        "checkpoint_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "checkpoint_data": JsonUtils.deserialize(row[3]),
                        "metadata": JsonUtils.deserialize(row[4]),
                        "created_at": row[5],
                        "updated_at": row[6]
                    })
                
                self._log_operation("列出检查点", True, f"{thread_id}, 共{len(checkpoints)}条")
                return checkpoints
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出检查点", e)
            raise  # 重新抛出异常
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的checkpoint"""
        try:
            def _delete():
                deleted = self._delete_by_id("checkpoint_id", checkpoint_id)
                self._log_operation("检查点删除", deleted, checkpoint_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除检查点", e)
            raise # 重新抛出异常
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        try:
            def _get_latest():
                query = """
                    SELECT checkpoint_id, thread_id, workflow_id, checkpoint_data, 
                           metadata, created_at, updated_at
                    FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (thread_id,))
                
                if results:
                    row = results[0]
                    return {
                        "checkpoint_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "checkpoint_data": JsonUtils.deserialize(row[3]),
                        "metadata": JsonUtils.deserialize(row[4]),
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_latest)
            
        except Exception as e:
            self._handle_exception("获取最新检查点", e)
            raise  # 重新抛出异常
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        try:
            def _get_by_workflow():
                query = """
                    SELECT checkpoint_id, thread_id, workflow_id, checkpoint_data, 
                           metadata, created_at, updated_at
                    FROM checkpoints
                    WHERE thread_id = ? AND workflow_id = ?
                    ORDER BY created_at DESC
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (thread_id, workflow_id))
                
                checkpoints = []
                for row in results:
                    checkpoints.append({
                        "checkpoint_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "checkpoint_data": JsonUtils.deserialize(row[3]),
                        "metadata": JsonUtils.deserialize(row[4]),
                        "created_at": row[5],
                        "updated_at": row[6]
                    })
                
                self._log_operation("获取工作流检查点", True, f"{thread_id}/{workflow_id}, 共{len(checkpoints)}条")
                return checkpoints
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_by_workflow)
            
        except Exception as e:
            self._handle_exception("获取工作流检查点", e)
            raise  # 重新抛出异常
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        try:
            def _cleanup():
                # 获取所有checkpoint ID，按创建时间排序
                query = """
                    SELECT checkpoint_id FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY created_at DESC
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (thread_id,))
                all_checkpoint_ids = [row[0] for row in results]
                
                if len(all_checkpoint_ids) <= max_count:
                    return 0
                
                # 需要删除的checkpoint
                to_delete_ids = all_checkpoint_ids[max_count:]
                
                # 删除旧checkpoint
                deleted_count = 0
                for checkpoint_id in to_delete_ids:
                    if self._delete_by_id("checkpoint_id", checkpoint_id):
                        deleted_count += 1
                
                self._log_operation("清理旧检查点", True, f"{thread_id}, 删除{deleted_count}条")
                return deleted_count
            
            return await asyncio.get_event_loop().run_in_executor(None, _cleanup)
            
        except Exception as e:
            self._handle_exception("清理旧检查点", e)
            raise  # 重新抛出异常