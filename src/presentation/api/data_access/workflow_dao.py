"""工作流数据访问对象"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiosqlite
import json
from pathlib import Path


class WorkflowDAO:
    """工作流数据访问对象"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """初始化数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT,
                    config_path TEXT,
                    loaded_at TIMESTAMP,
                    last_used TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    config_data TEXT
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflows_loaded_at ON workflows(loaded_at)
            """)
            await db.commit()
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """创建工作流"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO workflows (
                    workflow_id, name, description, version, config_path,
                    loaded_at, last_used, usage_count, config_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow_data.get("workflow_id"),
                workflow_data.get("name"),
                workflow_data.get("description"),
                workflow_data.get("version"),
                workflow_data.get("config_path"),
                workflow_data.get("loaded_at", datetime.now().isoformat()),
                workflow_data.get("last_used"),
                workflow_data.get("usage_count", 0),
                json.dumps(workflow_data.get("config_data", {}))
            ))
            await db.commit()
            return True
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "workflow_id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "version": row[3],
                        "config_path": row[4],
                        "loaded_at": row[5],
                        "last_used": row[6],
                        "usage_count": row[7],
                        "config_data": json.loads(row[8]) if row[8] else {}
                    }
                return None
    
    async def list_workflows(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出工作流"""
        query = "SELECT * FROM workflows ORDER BY loaded_at DESC LIMIT ? OFFSET ?"
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, [limit, offset]) as cursor:
                rows = await cursor.fetchall()
                workflows = []
                for row in rows:
                    workflows.append({
                        "workflow_id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "version": row[3],
                        "config_path": row[4],
                        "loaded_at": row[5],
                        "last_used": row[6],
                        "usage_count": row[7],
                        "config_data": json.loads(row[8]) if row[8] else {}
                    })
                return workflows
    
    async def update_workflow_usage(self, workflow_id: str) -> bool:
        """更新工作流使用次数和最后使用时间"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE workflows 
                SET usage_count = usage_count + 1, last_used = ? 
                WHERE workflow_id = ?
            """, (datetime.now().isoformat(), workflow_id))
            await db.commit()
            return cursor.rowcount > 0
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM workflows WHERE workflow_id = ?", (workflow_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_workflows_count(self) -> int:
        """获取工作流总数"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM workflows") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def search_workflows(self, query: str) -> List[Dict[str, Any]]:
        """搜索工作流"""
        search_pattern = f"%{query}%"
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT * FROM workflows 
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY usage_count DESC
            """, (search_pattern, search_pattern)) as cursor:
                rows = await cursor.fetchall()
                workflows = []
                for row in rows:
                    workflows.append({
                        "workflow_id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "version": row[3],
                        "config_path": row[4],
                        "loaded_at": row[5],
                        "last_used": row[6],
                        "usage_count": row[7],
                        "config_data": json.loads(row[8]) if row[8] else {}
                    })
                return workflows
    
    async def update_workflow(self, workflow_id: str, update_data: Dict[str, Any]) -> bool:
        """更新工作流"""
        # 构建更新SQL
        fields = []
        values = []
        
        for field, value in update_data.items():
            if field == "config_data" and isinstance(value, (dict, list)):
                fields.append(f"{field} = ?")
                values.append(json.dumps(value))
            else:
                fields.append(f"{field} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        # 添加更新时间
        if "updated_at" not in update_data:
            fields.append("loaded_at = ?")
            values.append(datetime.now().isoformat())
        
        values.append(workflow_id)  # WHERE条件
        
        sql = f"UPDATE workflows SET {', '.join(fields)} WHERE workflow_id = ?"
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(sql, values)
            await db.commit()
            return cursor.rowcount > 0