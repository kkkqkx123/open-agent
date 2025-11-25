"""SQLite状态Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import IStateRepository
from ..sqlite_base import SQLiteBaseRepository
from ..utils import JsonUtils, TimeUtils, SQLiteUtils


class SQLiteStateRepository(SQLiteBaseRepository, IStateRepository):
    """SQLite状态Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite状态Repository"""
        table_sql = """
            CREATE TABLE IF NOT EXISTS states (
                agent_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        super().__init__(config, "states", table_sql)
    
    async def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态"""
        try:
            def _save():
                data = {
                    "agent_id": agent_id,
                    "state_data": JsonUtils.serialize(state_data),
                    "updated_at": TimeUtils.now_iso()
                }
                
                self._insert_or_replace(data)
                self._log_operation("状态保存", True, agent_id)
                return agent_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存状态", e)
            raise  # 重新抛出异常，不会到达下一行
    
    async def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载状态"""
        try:
            def _load():
                row = self._find_by_id("agent_id", agent_id)
                if row:
                    return JsonUtils.deserialize(row[1])
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载状态", e)
            raise  # 重新抛出异常
    
    async def delete_state(self, agent_id: str) -> bool:
        """删除状态"""
        try:
            def _delete():
                deleted = self._delete_by_id("agent_id", agent_id)
                self._log_operation("状态删除", deleted, agent_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除状态", e)
            raise # 重新抛出异常
    
    async def exists_state(self, agent_id: str) -> bool:
        """检查状态是否存在"""
        try:
            def _exists():
                query = "SELECT 1 FROM states WHERE agent_id = ?"
                results = SQLiteUtils.execute_query(self.db_path, query, (agent_id,))
                exists = len(results) > 0
                return exists
            
            return await asyncio.get_event_loop().run_in_executor(None, _exists)
            
        except Exception as e:
            self._handle_exception("检查状态存在性", e)
            raise # 重新抛出异常
    
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态"""
        try:
            def _list():
                query = """
                    SELECT agent_id, state_data, created_at, updated_at
                    FROM states
                    ORDER BY updated_at DESC
                    LIMIT ?
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (limit,))
                
                states = []
                for row in results:
                    states.append({
                        "agent_id": row[0],
                        "state_data": JsonUtils.deserialize(row[1]),
                        "created_at": row[2],
                        "updated_at": row[3]
                    })
                
                self._log_operation("列出状态", True, f"共{len(states)}条")
                return states
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出状态", e)
            raise # 重新抛出异常