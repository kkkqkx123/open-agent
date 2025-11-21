"""SQLite会话存储适配器实现"""

import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from src.core.sessions.entities import Session, SessionStatus
from src.interfaces.sessions.storage import ISessionStore
from src.core.common.exceptions import StorageError


class SQLiteSessionStore(ISessionStore):
    """SQLite会话存储适配器"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
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
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at)")
    
    def _row_to_session(self, row) -> Session:
        """将数据库行转换为会话实体"""
        return Session(
            session_id=row[0],
            status=SessionStatus(row[1]),
            message_count=row[2],
            checkpoint_count=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
            metadata=json.loads(row[6]) if row[6] else {},
            tags=json.loads(row[7]) if row[7] else [],
            thread_ids=json.loads(row[8]) if row[8] else []
        )
    
    def _session_to_row(self, session: Session) -> tuple:
        """将会话实体转换为数据库行"""
        return (
            session.session_id,
            session.status.value,
            session.message_count,
            session.checkpoint_count,
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
            json.dumps(session.metadata),
            json.dumps(session.tags),
            json.dumps(session.thread_ids)
        )
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                row = cursor.fetchone()
                return self._row_to_session(row) if row else None
        except Exception as e:
            raise StorageError(f"Failed to get session {session_id}: {str(e)}")
    
    async def create_session(self, session: Session) -> bool:
        """创建会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO sessions (
                        session_id, status, message_count, checkpoint_count,
                        created_at, updated_at, metadata, tags, thread_ids
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    self._session_to_row(session)
                )
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            raise StorageError(f"Failed to create session {session.session_id}: {str(e)}")
    
    async def update_session(self, session_id: str, session: Session) -> bool:
        """更新会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """UPDATE sessions SET
                        status = ?, message_count = ?, checkpoint_count = ?,
                        updated_at = ?, metadata = ?, tags = ?, thread_ids = ?
                    WHERE session_id = ?""",
                    (
                        session.status.value,
                        session.message_count,
                        session.checkpoint_count,
                        session.updated_at.isoformat(),
                        json.dumps(session.metadata),
                        json.dumps(session.tags),
                        json.dumps(session.thread_ids),
                        session_id
                    )
                )
                return cursor.rowcount > 0
        except Exception as e:
            raise StorageError(f"Failed to update session {session_id}: {str(e)}")
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            raise StorageError(f"Failed to delete session {session_id}: {str(e)}")
    
    async def list_sessions_by_status(self, status: SessionStatus) -> List[Session]:
        """按状态列会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC",
                    (status.value,)
                )
                return [self._row_to_session(row) for row in cursor.fetchall()]
        except Exception as e:
            raise StorageError(f"Failed to list sessions by status {status}: {str(e)}")
    
    async def list_sessions_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Session]:
        """按日期范围列会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT * FROM sessions 
                    WHERE created_at >= ? AND created_at <= ?
                    ORDER BY created_at DESC""",
                    (start_date.isoformat(), end_date.isoformat())
                )
                return [self._row_to_session(row) for row in cursor.fetchall()]
        except Exception as e:
            raise StorageError(f"Failed to list sessions by date range: {str(e)}")
    
    async def search_sessions(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Session]:
        """搜索会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT * FROM sessions 
                    WHERE session_id LIKE ? OR metadata LIKE ?
                    ORDER BY updated_at DESC
                    LIMIT ?""",
                    (f"%{query}%", f"%{query}%", limit)
                )
                return [self._row_to_session(row) for row in cursor.fetchall()]
        except Exception as e:
            raise StorageError(f"Failed to search sessions: {str(e)}")
    
    async def get_session_count_by_status(self) -> Dict[str, int]:
        """获取各状态会话数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT status, COUNT(*) FROM sessions GROUP BY status"
                )
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            raise StorageError(f"Failed to get session count by status: {str(e)}")
    
    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """清理旧会话"""
        try:
            cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """DELETE FROM sessions 
                    WHERE (status = 'completed' OR status = 'failed')
                    AND strftime('%s', updated_at) < ?""",
                    (cutoff_date,)
                )
                return cursor.rowcount
        except Exception as e:
            raise StorageError(f"Failed to cleanup old sessions: {str(e)}")