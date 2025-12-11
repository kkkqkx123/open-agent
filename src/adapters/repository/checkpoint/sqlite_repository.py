"""SQLite检查点Repository实现"""

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ICheckpointRepository
from src.interfaces.dependency_injection import get_logger


logger = get_logger(__name__)


class SQLiteCheckpointRepository(ICheckpointRepository):
    """SQLite检查点Repository实现 - 直接使用SQLite数据库"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite检查点Repository"""
        self.db_path = Path(config.get("db_path", "./checkpoints.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 创建检查点表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        checkpoint_id TEXT PRIMARY KEY,
                        thread_id TEXT NOT NULL,
                        workflow_id TEXT,
                        checkpoint_data TEXT NOT NULL,
                        metadata TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)
                
                # 创建索引
                conn.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_id ON checkpoints(workflow_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at)")
                
                conn.commit()
                logger.debug("SQLite checkpoint repository initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite checkpoint repository: {e}")
            raise
    
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存checkpoint数据"""
        try:
            checkpoint_id = checkpoint_data.get("checkpoint_id")
            if not checkpoint_id:
                checkpoint_id = str(uuid.uuid4())
            
            current_time = time.time()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO checkpoints (
                        checkpoint_id, thread_id, workflow_id, checkpoint_data,
                        metadata, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    checkpoint_id,
                    checkpoint_data["thread_id"],
                    checkpoint_data.get("workflow_id"),
                    json.dumps(checkpoint_data.get("checkpoint_data", {})),
                    json.dumps(checkpoint_data.get("metadata", {})),
                    current_time,
                    current_time
                ))
                conn.commit()
            
            logger.debug(f"SQLite checkpoint saved: {checkpoint_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to save SQLite checkpoint: {e}")
            raise
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT checkpoint_id, thread_id, workflow_id, checkpoint_data,
                           metadata, created_at, updated_at
                    FROM checkpoints WHERE checkpoint_id = ?
                """, (checkpoint_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "checkpoint_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "checkpoint_data": json.loads(row[3]),
                        "metadata": json.loads(row[4]),
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                return None
            
        except Exception as e:
            logger.error(f"Failed to load SQLite checkpoint {checkpoint_id}: {e}")
            raise
    
    async def list_checkpoints(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出指定thread的所有checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if limit is not None:
                    query = """
                        SELECT checkpoint_id, thread_id, workflow_id, checkpoint_data,
                               metadata, created_at, updated_at
                        FROM checkpoints
                        WHERE thread_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """
                    cursor = conn.execute(query, (thread_id, limit))
                else:
                    query = """
                        SELECT checkpoint_id, thread_id, workflow_id, checkpoint_data,
                               metadata, created_at, updated_at
                        FROM checkpoints
                        WHERE thread_id = ?
                        ORDER BY created_at DESC
                    """
                    cursor = conn.execute(query, (thread_id,))
                
                checkpoints = []
                for row in cursor.fetchall():
                    checkpoints.append({
                        "checkpoint_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "checkpoint_data": json.loads(row[3]),
                        "metadata": json.loads(row[4]),
                        "created_at": row[5],
                        "updated_at": row[6]
                    })
                
                logger.debug(f"Listed SQLite checkpoints for {thread_id}: {len(checkpoints)} items")
                return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list SQLite checkpoints for {thread_id}: {e}")
            raise
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.debug(f"SQLite checkpoint deleted: {checkpoint_id}")
                return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete SQLite checkpoint {checkpoint_id}: {e}")
            raise
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT checkpoint_id, thread_id, workflow_id, checkpoint_data,
                           metadata, created_at, updated_at
                    FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (thread_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "checkpoint_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "checkpoint_data": json.loads(row[3]),
                        "metadata": json.loads(row[4]),
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                return None
            
        except Exception as e:
            logger.error(f"Failed to get latest SQLite checkpoint for {thread_id}: {e}")
            raise
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT checkpoint_id, thread_id, workflow_id, checkpoint_data,
                           metadata, created_at, updated_at
                    FROM checkpoints
                    WHERE thread_id = ? AND workflow_id = ?
                    ORDER BY created_at DESC
                """, (thread_id, workflow_id))
                
                checkpoints = []
                for row in cursor.fetchall():
                    checkpoints.append({
                        "checkpoint_id": row[0],
                        "thread_id": row[1],
                        "workflow_id": row[2],
                        "checkpoint_data": json.loads(row[3]),
                        "metadata": json.loads(row[4]),
                        "created_at": row[5],
                        "updated_at": row[6]
                    })
                
                logger.debug(f"Got workflow SQLite checkpoints for {thread_id}/{workflow_id}: {len(checkpoints)} items")
                return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to get workflow SQLite checkpoints for {thread_id}/{workflow_id}: {e}")
            raise
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取所有checkpoint ID，按创建时间排序
                cursor = conn.execute("""
                    SELECT checkpoint_id FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY created_at DESC
                """, (thread_id,))
                
                all_checkpoint_ids = [row[0] for row in cursor.fetchall()]
                
                if len(all_checkpoint_ids) <= max_count:
                    return 0
                
                # 需要删除的checkpoint
                to_delete_ids = all_checkpoint_ids[max_count:]
                
                # 删除旧checkpoint
                deleted_count = 0
                for checkpoint_id in to_delete_ids:
                    cursor = conn.execute("DELETE FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
                    if cursor.rowcount > 0:
                        deleted_count += 1
                
                conn.commit()
                logger.debug(f"Cleaned up old SQLite checkpoints for {thread_id}: deleted {deleted_count} items")
                return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old SQLite checkpoints for {thread_id}: {e}")
            raise