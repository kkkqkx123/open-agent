"""会话数据访问对象"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiosqlite
import json
from pathlib import Path


class SessionDAO:
    """会话数据访问对象"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """初始化数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    workflow_config_path TEXT NOT NULL,
                    workflow_id TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    agent_config TEXT,
                    metadata TEXT
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)
            """)
            await db.commit()
    
    async def create_session(self, session_data: Dict[str, Any]) -> bool:
        """创建会话"""
        metadata = session_data.get("metadata", {})
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sessions (
                    session_id, workflow_config_path, workflow_id, status,
                    created_at, updated_at, agent_config, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.get("session_id"),
                metadata.get("workflow_config_path"),
                metadata.get("workflow_id"),
                metadata.get("status", "active"),
                metadata.get("created_at"),
                metadata.get("updated_at"),
                json.dumps(metadata.get("agent_config", {})),
                json.dumps(metadata.get("metadata", {}))
            ))
            await db.commit()
            return True
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "session_id": row[0],
                        "workflow_config_path": row[1],
                        "workflow_id": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "updated_at": row[5],
                        "agent_config": json.loads(row[6]) if row[6] else {},
                        "metadata": json.loads(row[7]) if row[7] else {}
                    }
                return None
    
    async def list_sessions(
        self, 
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出会话"""
        query = "SELECT * FROM sessions"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                sessions = []
                for row in rows:
                    sessions.append({
                        "session_id": row[0],
                        "workflow_config_path": row[1],
                        "workflow_id": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "updated_at": row[5],
                        "agent_config": json.loads(row[6]) if row[6] else {},
                        "metadata": json.loads(row[7]) if row[7] else {}
                    })
                return sessions
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE sessions SET status = ?, updated_at = ? WHERE session_id = ?",
                (status, datetime.now().isoformat(), session_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def update_session_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """更新会话状态数据
        
        Args:
            session_id: 会话ID
            state_data: 状态数据字典
            
        Returns:
            bool: 是否成功更新
        """
        # 将会话状态数据序列化到metadata字段中
        current_session = await self.get_session(session_id)
        if not current_session:
            return False
        
        # 合并现有的metadata与新的状态数据
        metadata = current_session.get("metadata", {})
        metadata["state_data"] = state_data
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE sessions SET metadata = ?, updated_at = ? WHERE session_id = ?",
                (json.dumps(metadata), datetime.now().isoformat(), session_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_sessions_count(self, status: Optional[str] = None) -> int:
        """获取会话总数"""
        query = "SELECT COUNT(*) FROM sessions"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0