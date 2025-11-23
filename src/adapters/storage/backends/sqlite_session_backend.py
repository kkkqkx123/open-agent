"""SQLite 会话存储后端实现"""

import json
import sqlite3
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from src.interfaces.sessions.backends import ISessionStorageBackend
from src.core.common.exceptions import StorageError

logger = logging.getLogger(__name__)


class SQLiteSessionBackend(ISessionStorageBackend):
    """SQLite 会话存储后端"""
    
    def __init__(self, db_path: str = "./data/sessions.db"):
        """初始化 SQLite 后端
        
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
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        message_count INTEGER DEFAULT 0,
                        checkpoint_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        metadata TEXT,
                        tags TEXT,
                        thread_ids TEXT
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at)"
                )
                conn.commit()
                logger.debug("SQLite sessions table initialized")
        except Exception as e:
            raise StorageError(f"Failed to initialize database: {e}")
    
    async def save(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据
        
        Args:
            session_id: 会话ID
            data: 会话数据字典
            
        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (session_id, status, message_count, checkpoint_count, 
                     created_at, updated_at, metadata, tags, thread_ids)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["session_id"],
                    data["status"],
                    data.get("message_count", 0),
                    data.get("checkpoint_count", 0),
                    data["created_at"],
                    data["updated_at"],
                    json.dumps(data.get("metadata", {})),
                    json.dumps(data.get("tags", [])),
                    json.dumps(data.get("thread_ids", []))
                ))
                conn.commit()
                logger.debug(f"Session saved: {session_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise StorageError(f"Failed to save session: {e}")
    
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，不存在返回None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    "session_id": row[0],
                    "status": row[1],
                    "message_count": row[2],
                    "checkpoint_count": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                    "metadata": json.loads(row[6]) if row[6] else {},
                    "tags": json.loads(row[7]) if row[7] else [],
                    "thread_ids": json.loads(row[8]) if row[8] else []
                }
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            raise StorageError(f"Failed to load session: {e}")
    
    async def delete(self, session_id: str) -> bool:
        """删除会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                conn.commit()
                result = cursor.rowcount > 0
                if result:
                    logger.debug(f"Session deleted: {session_id}")
                return result
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise StorageError(f"Failed to delete session: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有会话键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            会话ID列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if prefix:
                    cursor = conn.execute(
                        "SELECT session_id FROM sessions WHERE session_id LIKE ?",
                        (f"{prefix}%",)
                    )
                else:
                    cursor = conn.execute("SELECT session_id FROM sessions")
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            raise StorageError(f"Failed to list keys: {e}")
    
    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否存在
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1",
                    (session_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check session existence: {e}")
            raise StorageError(f"Failed to check session existence: {e}")
    
    async def close(self) -> None:
        """关闭后端连接"""
        logger.debug("SQLite backend connection closed")
