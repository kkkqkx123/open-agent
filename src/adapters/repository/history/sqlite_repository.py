"""SQLite历史记录Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import IHistoryRepository
from ..sqlite_base import SQLiteBaseRepository
from ..utils import JsonUtils, TimeUtils, IdUtils, SQLiteUtils


class SQLiteHistoryRepository(SQLiteBaseRepository, IHistoryRepository):
    """SQLite历史Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite历史Repository"""
        table_sql = """
            CREATE TABLE IF NOT EXISTS history (
                history_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                old_state TEXT,
                new_state TEXT,
                state_diff TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_history_agent_id ON history(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp)"
        ]
        
        super().__init__(config, "history", table_sql, indexes_sql)
    
    async def save_history(self, entry: Dict[str, Any]) -> str:
        """保存历史记录"""
        try:
            def _save():
                history_id = IdUtils.get_or_generate_id(
                    entry, "history_id", IdUtils.generate_history_id
                )
                
                data = {
                    "history_id": history_id,
                    "agent_id": entry["agent_id"],
                    "timestamp": entry.get("timestamp", TimeUtils.now_iso()),
                    "action": entry["action"],
                    "old_state": JsonUtils.serialize(entry.get("old_state", {})),
                    "new_state": JsonUtils.serialize(entry.get("new_state", {})),
                    "state_diff": JsonUtils.serialize(entry.get("state_diff", {})),
                    "metadata": JsonUtils.serialize(entry.get("metadata", {}))
                }
                
                self._insert_or_replace(data)
                self._log_operation("历史记录保存", True, history_id)
                return history_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存历史记录", e)
            raise  # 重新抛出异常，不会到达下一行
    
    async def get_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录"""
        try:
            def _get():
                query = """
                    SELECT history_id, agent_id, timestamp, action, 
                           old_state, new_state, state_diff, metadata
                    FROM history
                    WHERE agent_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                results = SQLiteUtils.execute_query(self.db_path, query, (agent_id, limit))
                
                history = []
                for row in results:
                    history.append({
                        "history_id": row[0],
                        "agent_id": row[1],
                        "timestamp": row[2],
                        "action": row[3],
                        "old_state": JsonUtils.deserialize(row[4]),
                        "new_state": JsonUtils.deserialize(row[5]),
                        "state_diff": JsonUtils.deserialize(row[6]),
                        "metadata": JsonUtils.deserialize(row[7])
                    })
                
                self._log_operation("获取历史记录", True, f"{agent_id}, 共{len(history)}条")
                return history
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取历史记录", e)
            raise  # 重新抛出异常
    
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录"""
        try:
            def _delete():
                deleted = self._delete_by_id("history_id", history_id)
                self._log_operation("历史记录删除", deleted, history_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除历史记录", e)
            raise  # 重新抛出异常
    
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            def _clear():
                query = "DELETE FROM history WHERE agent_id = ?"
                affected_rows = SQLiteUtils.execute_update(self.db_path, query, (agent_id,))
                deleted = affected_rows > 0
                self._log_operation("代理历史记录清空", deleted, agent_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _clear)
            
        except Exception as e:
            self._handle_exception("清空代理历史记录", e)
            raise # 重新抛出异常
    
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
            def _get_stats():
                # 总记录数
                total_count = self._count_records()
                
                # 按代理统计
                top_agents_results = SQLiteUtils.get_top_records(
                    self.db_path, self.table_name, "agent_id", "timestamp", 10
                )
                top_agents = [{"agent_id": row[0], "count": row[1]} for row in top_agents_results]
                
                # 按动作类型统计
                top_actions_results = SQLiteUtils.get_top_records(
                    self.db_path, self.table_name, "action", "timestamp", 10
                )
                top_actions = [{"action": row[0], "count": row[1]} for row in top_actions_results]
                
                stats = {
                    "total_count": total_count,
                    "agent_count": len(top_agents),
                    "top_agents": top_agents,
                    "top_actions": top_actions
                }
                
                self._log_operation("获取历史统计信息", True)
                return stats
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_stats)
            
        except Exception as e:
            self._handle_exception("获取历史统计信息", e)
            raise # 重新抛出异常