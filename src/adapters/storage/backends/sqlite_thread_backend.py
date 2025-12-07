"""SQLite 线程存储后端实现"""

import json
import sqlite3
from src.services.logger.injection import get_logger
from typing import Dict, Any, Optional, List
from pathlib import Path

from .thread_base import IThreadStorageBackend
from src.interfaces.storage.exceptions import StorageError

logger = get_logger(__name__)


class SQLiteThreadBackend(IThreadStorageBackend):
    """SQLite 线程存储后端 - 专注于线程数据存储"""
    
    def __init__(self, db_path: str = "./data/threads.db"):
        """初始化 SQLite 线程后端
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 创建线程表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS threads (
                        thread_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        metadata TEXT,
                        tags TEXT,
                        branch_ids TEXT
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_threads_session_id ON threads(session_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_threads_status ON threads(status)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_threads_created_at ON threads(created_at)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_threads_updated_at ON threads(updated_at)"
                )
                
                conn.commit()
                logger.debug("SQLite thread storage tables initialized")
        except Exception as e:
            raise StorageError(f"Failed to initialize database: {e}")
    
    async def save(self, thread_id: str, data: Dict[str, Any]) -> bool:
        """保存线程数据
        
        Args:
            thread_id: 线程ID
            data: 线程数据字典
            
        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO threads 
                    (thread_id, session_id, status, 
                     created_at, updated_at, metadata, tags, branch_ids)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["thread_id"],
                    data["session_id"],
                    data["status"],
                    data["created_at"],
                    data["updated_at"],
                    json.dumps(data.get("metadata", {})),
                    json.dumps(data.get("tags", [])),
                    json.dumps(data.get("branch_ids", []))
                ))
                conn.commit()
                logger.debug(f"Thread saved: {thread_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to save thread {thread_id}: {e}")
            raise StorageError(f"Failed to save thread: {e}")
    
    async def load(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程数据，不存在返回None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM threads WHERE thread_id = ?",
                    (thread_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    "thread_id": row[0],
                    "session_id": row[1],
                    "status": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {},
                    "tags": json.loads(row[6]) if row[6] else [],
                    "branch_ids": json.loads(row[7]) if row[7] else []
                }
        except Exception as e:
            logger.error(f"Failed to load thread {thread_id}: {e}")
            raise StorageError(f"Failed to load thread: {e}")
    
    async def delete(self, thread_id: str) -> bool:
        """删除线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM threads WHERE thread_id = ?",
                    (thread_id,)
                )
                conn.commit()
                result = cursor.rowcount > 0
                if result:
                    logger.debug(f"Thread deleted: {thread_id}")
                return result
        except Exception as e:
            logger.error(f"Failed to delete thread {thread_id}: {e}")
            raise StorageError(f"Failed to delete thread: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有线程键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            线程ID列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if prefix:
                    cursor = conn.execute(
                        "SELECT thread_id FROM threads WHERE thread_id LIKE ?",
                        (f"{prefix}%",)
                    )
                else:
                    cursor = conn.execute("SELECT thread_id FROM threads")
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            raise StorageError(f"Failed to list keys: {e}")
    
    async def exists(self, thread_id: str) -> bool:
        """检查线程是否存在
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM threads WHERE thread_id = ? LIMIT 1",
                    (thread_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check thread existence: {e}")
            raise StorageError(f"Failed to check thread existence: {e}")
    
    async def close(self) -> None:
        """关闭后端连接"""
        logger.debug("SQLite thread backend connection closed")