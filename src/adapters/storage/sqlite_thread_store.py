"""SQLite线程存储适配器实现"""

import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from src.core.threads.entities import Thread, ThreadStatus
from src.interfaces.threads.storage import IThreadStore
from src.core.common.exceptions import StorageError


class SQLiteThreadStore(IThreadStore):
    """SQLite线程存储适配器"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS threads (
                    thread_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_checkpoint_id TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    metadata TEXT,
                    tags TEXT,
                    branch_ids TEXT
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_threads_session_id ON threads(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_threads_status ON threads(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_threads_created_at ON threads(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_threads_updated_at ON threads(updated_at)")
    
    def _row_to_thread(self, row) -> Thread:
        """将数据库行转换为线程实体"""
        return Thread(
            thread_id=row[0],
            session_id=row[1],
            status=ThreadStatus(row[2]),
            current_checkpoint_id=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
            metadata=json.loads(row[6]) if row[6] else {},
            tags=json.loads(row[7]) if row[7] else [],
            branch_ids=json.loads(row[8]) if row[8] else []
        )
    
    def _thread_to_row(self, thread: Thread) -> tuple:
        """将线程实体转换为数据库行"""
        return (
            thread.thread_id,
            thread.session_id,
            thread.status.value,
            thread.current_checkpoint_id,
            thread.created_at.isoformat(),
            thread.updated_at.isoformat(),
            json.dumps(thread.metadata),
            json.dumps(thread.tags),
            json.dumps(thread.branch_ids)
        )
    
    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """获取线程"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM threads WHERE thread_id = ?",
                    (thread_id,)
                )
                row = cursor.fetchone()
                return self._row_to_thread(row) if row else None
        except Exception as e:
            raise StorageError(f"Failed to get thread {thread_id}: {str(e)}")
    
    async def create_thread(self, thread: Thread) -> bool:
        """创建线程"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO threads (
                        thread_id, session_id, status, current_checkpoint_id,
                        created_at, updated_at, metadata, tags, branch_ids
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    self._thread_to_row(thread)
                )
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            raise StorageError(f"Failed to create thread {thread.thread_id}: {str(e)}")
    
    async def update_thread(self, thread_id: str, thread: Thread) -> bool:
        """更新线程"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """UPDATE threads SET
                        session_id = ?, status = ?, current_checkpoint_id = ?,
                        updated_at = ?, metadata = ?, tags = ?, branch_ids = ?
                    WHERE thread_id = ?""",
                    (
                        thread.session_id,
                        thread.status.value,
                        thread.current_checkpoint_id,
                        thread.updated_at.isoformat(),
                        json.dumps(thread.metadata),
                        json.dumps(thread.tags),
                        json.dumps(thread.branch_ids),
                        thread_id
                    )
                )
                return cursor.rowcount > 0
        except Exception as e:
            raise StorageError(f"Failed to update thread {thread_id}: {str(e)}")
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM threads WHERE thread_id = ?",
                    (thread_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            raise StorageError(f"Failed to delete thread {thread_id}: {str(e)}")
    
    async def list_threads_by_session(self, session_id: str) -> List[Thread]:
        """按会话列线程"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM threads WHERE session_id = ? ORDER BY created_at DESC",
                    (session_id,)
                )
                return [self._row_to_thread(row) for row in cursor.fetchall()]
        except Exception as e:
            raise StorageError(f"Failed to list threads by session {session_id}: {str(e)}")
    
    async def list_threads_by_status(self, status: ThreadStatus) -> List[Thread]:
        """按状态列线程"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM threads WHERE status = ? ORDER BY updated_at DESC",
                    (status.value,)
                )
                return [self._row_to_thread(row) for row in cursor.fetchall()]
        except Exception as e:
            raise StorageError(f"Failed to list threads by status {status}: {str(e)}")
    
    async def get_thread_by_checkpoint(self, checkpoint_id: str) -> Optional[Thread]:
        """按检查点获取线程"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM threads WHERE current_checkpoint_id = ?",
                    (checkpoint_id,)
                )
                row = cursor.fetchone()
                return self._row_to_thread(row) if row else None
        except Exception as e:
            raise StorageError(f"Failed to get thread by checkpoint {checkpoint_id}: {str(e)}")
    
    async def search_threads(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Thread]:
        """搜索线程"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if session_id:
                    cursor = conn.execute(
                        """SELECT * FROM threads 
                        WHERE session_id = ? AND (thread_id LIKE ? OR metadata LIKE ?)
                        ORDER BY updated_at DESC
                        LIMIT ?""",
                        (session_id, f"%{query}%", f"%{query}%", limit)
                    )
                else:
                    cursor = conn.execute(
                        """SELECT * FROM threads 
                        WHERE thread_id LIKE ? OR metadata LIKE ?
                        ORDER BY updated_at DESC
                        LIMIT ?""",
                        (f"%{query}%", f"%{query}%", limit)
                    )
                return [self._row_to_thread(row) for row in cursor.fetchall()]
        except Exception as e:
            raise StorageError(f"Failed to search threads: {str(e)}")
    
    async def get_thread_count_by_session(self, session_id: str) -> int:
        """获取会话线程数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM threads WHERE session_id = ?",
                    (session_id,)
                )
                return cursor.fetchone()[0]
        except Exception as e:
            raise StorageError(f"Failed to get thread count by session {session_id}: {str(e)}")
    
    async def cleanup_old_threads(self, max_age_days: int = 30) -> int:
        """清理旧线程"""
        try:
            cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """DELETE FROM threads 
                    WHERE (status = 'completed' OR status = 'failed')
                    AND strftime('%s', updated_at) < ?""",
                    (cutoff_date,)
                )
                return cursor.rowcount
        except Exception as e:
            raise StorageError(f"Failed to cleanup old threads: {str(e)}")