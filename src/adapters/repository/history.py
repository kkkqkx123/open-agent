"""历史Repository重构实现

使用基类和工具类重构的历史Repository实现。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.interfaces.repository import IHistoryRepository
from .base import SQLiteBaseRepository, MemoryBaseRepository, FileBaseRepository
from .utils import JsonUtils, TimeUtils, IdUtils, SQLiteUtils, FileUtils


class SQLiteHistoryRepository(SQLiteBaseRepository, IHistoryRepository):
    """SQLite历史Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite历史Repository"""
        table_sql = """
            CREATE TABLE IF NOT EXISTS history (
                history_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                action TEXT NOT NULL,
                old_state TEXT,
                new_state TEXT,
                state_diff TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
        except Exception as e:
            self._handle_exception("保存历史记录", e)
            raise  # 重新抛出异常，不会到达下一行
    
    async def get_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录"""
        try:
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
            
        except Exception as e:
            self._handle_exception("获取历史记录", e)
            raise  # 重新抛出异常
    
    async def get_history_by_timerange(
        self, 
        agent_id: str, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """按时间范围获取历史记录"""
        try:
            query = """
                SELECT history_id, agent_id, timestamp, action, 
                       old_state, new_state, state_diff, metadata
                FROM history
                WHERE agent_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            results = SQLiteUtils.execute_query(
                self.db_path, query, (agent_id, start_time.isoformat(), end_time.isoformat(), limit)
            )
            
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
            
            self._log_operation("按时间范围获取历史记录", True, f"{agent_id}, 共{len(history)}条")
            return history
            
        except Exception as e:
            self._handle_exception("按时间范围获取历史记录", e)
            raise  # 重新抛出异常
    
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录"""
        try:
            deleted = self._delete_by_id("history_id", history_id)
            self._log_operation("历史记录删除", deleted, history_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除历史记录", e)
            raise  # 重新抛出异常
    
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            query = "DELETE FROM history WHERE agent_id = ?"
            affected_rows = SQLiteUtils.execute_update(self.db_path, query, (agent_id,))
            deleted = affected_rows > 0
            self._log_operation("代理历史记录清空", deleted, agent_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("清空代理历史记录", e)
            raise # 重新抛出异常
    
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
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
            
        except Exception as e:
            self._handle_exception("获取历史统计信息", e)
            raise # 重新抛出异常
    
    async def get_history_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取历史记录"""
        try:
            row = self._find_by_id("history_id", history_id)
            if row:
                return {
                    "history_id": row[0],
                    "agent_id": row[1],
                    "timestamp": row[2],
                    "action": row[3],
                    "old_state": JsonUtils.deserialize(row[4]),
                    "new_state": JsonUtils.deserialize(row[5]),
                    "state_diff": JsonUtils.deserialize(row[6]),
                    "metadata": JsonUtils.deserialize(row[7])
                }
            return None
            
        except Exception as e:
            self._handle_exception("根据ID获取历史记录", e)
            raise  # 重新抛出异常


class MemoryHistoryRepository(MemoryBaseRepository, IHistoryRepository):
    """内存历史Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存历史Repository"""
        super().__init__(config)
    
    async def save_history(self, entry: Dict[str, Any]) -> str:
        """保存历史记录"""
        try:
            history_id = IdUtils.get_or_generate_id(
                entry, "history_id", IdUtils.generate_history_id
            )
            
            full_entry = TimeUtils.add_timestamp({
                "history_id": history_id,
                **entry,
                "timestamp": entry.get("timestamp", TimeUtils.now_iso())
            })
            
            # 保存到存储
            self._save_item(history_id, full_entry)
            
            # 更新索引
            self._add_to_index("agent", entry["agent_id"], history_id)
            
            self._log_operation("内存历史记录保存", True, history_id)
            return history_id
            
        except Exception as e:
            self._handle_exception("保存内存历史记录", e)
            raise  # 重新抛出异常
    
    async def get_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录"""
        try:
            history_ids = self._get_from_index("agent", agent_id)
            # 过滤掉None值，确保只返回有效的历史记录
            history = [item for hid in history_ids if (item := self._load_item(hid)) is not None]
            
            # 按时间倒序排序
            history = TimeUtils.sort_by_time(history, "timestamp", True)
            history = history[:limit]
            
            self._log_operation("获取内存历史记录", True, f"{agent_id}, 共{len(history)}条")
            return history
            
        except Exception as e:
            self._handle_exception("获取内存历史记录", e)
            raise  # 重新抛出异常
    
    async def get_history_by_timerange(
        self, 
        agent_id: str, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """按时间范围获取历史记录"""
        try:
            history_ids = self._get_from_index("agent", agent_id)
            history = [item for hid in history_ids if (item := self._load_item(hid)) is not None]
            
            # 过滤时间范围
            filtered_history = []
            for entry in history:
                if TimeUtils.is_time_in_range(entry["timestamp"], start_time, end_time):
                    filtered_history.append(entry)
            
            # 按时间倒序排序
            filtered_history = TimeUtils.sort_by_time(filtered_history, "timestamp", True)
            filtered_history = filtered_history[:limit]
            
            self._log_operation("按时间范围获取内存历史记录", True, f"{agent_id}, 共{len(filtered_history)}条")
            return filtered_history
            
        except Exception as e:
            self._handle_exception("按时间范围获取内存历史记录", e)
            raise  # 重新抛出异常
    
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录"""
        try:
            history = self._load_item(history_id)
            if not history:
                return False
            
            # 从索引中移除
            self._remove_from_index("agent", history["agent_id"], history_id)
            
            # 从存储中删除
            deleted = self._delete_item(history_id)
            self._log_operation("内存历史记录删除", deleted, history_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除内存历史记录", e)
            raise  # 重新抛出异常
    
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            history_ids = self._get_from_index("agent", agent_id)
            
            # 删除所有历史记录
            deleted_count = 0
            for history_id in history_ids:
                if self._delete_item(history_id):
                    deleted_count += 1
            
            # 清空索引
            if agent_id in self._indexes.get("agent", {}):
                del self._indexes["agent"][agent_id]
            
            deleted = deleted_count > 0
            self._log_operation("内存代理历史记录清空", deleted, f"{agent_id}, 删除{deleted_count}条")
            return deleted
            
        except Exception as e:
            self._handle_exception("清空内存代理历史记录", e)
            raise  # 重新抛出异常
    
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
            total_count = len(self._storage)
            
            # 按代理统计
            top_agents = []
            for agent_id, history_ids in self._indexes.get("agent", {}).items():
                top_agents.append({"agent_id": agent_id, "count": len(history_ids)})
            # 修复排序函数的类型问题
            top_agents = sorted(top_agents, key=lambda x: x["count"], reverse=True)[:10]  # type: ignore
            
            # 按动作类型统计
            action_counts = {}
            for entry in self._storage.values():
                action = entry.get("action", "unknown")
                action_counts[action] = action_counts.get(action, 0) + 1
            
            top_actions = [{"action": action, "count": count} 
                          for action, count in sorted(action_counts.items(), 
                                                    key=lambda x: x[1], reverse=True)[:10]]
            
            stats = {
                "total_count": total_count,
                "agent_count": len(top_agents),
                "top_agents": top_agents,
                "top_actions": top_actions
            }
            
            self._log_operation("获取内存历史统计信息", True)
            return stats
            
        except Exception as e:
            self._handle_exception("获取内存历史统计信息", e)
            raise # 重新抛出异常
    
    async def get_history_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取历史记录"""
        try:
            history = self._load_item(history_id)
            if history:
                self._log_operation("内存历史记录加载", True, history_id)
                return history
            return None
            
        except Exception as e:
            self._handle_exception("根据ID获取内存历史记录", e)
            raise # 重新抛出异常


class FileHistoryRepository(FileBaseRepository, IHistoryRepository):
    """文件历史Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件历史Repository"""
        super().__init__(config)
    
    async def save_history(self, entry: Dict[str, Any]) -> str:
        """保存历史记录"""
        try:
            history_id = IdUtils.get_or_generate_id(
                entry, "history_id", IdUtils.generate_history_id
            )
            
            full_entry = TimeUtils.add_timestamp({
                "history_id": history_id,
                **entry,
                "timestamp": entry.get("timestamp", TimeUtils.now_iso())
            })
            
            # 保存到文件
            self._save_item(entry["agent_id"], history_id, full_entry)
            
            self._log_operation("文件历史记录保存", True, history_id)
            return history_id
            
        except Exception as e:
            self._handle_exception("保存文件历史记录", e)
            raise  # 重新抛出异常
    
    async def get_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录"""
        try:
            history = self._list_items(agent_id)
            
            # 按时间倒序排序
            history = TimeUtils.sort_by_time(history, "timestamp", True)
            history = history[:limit]
            
            self._log_operation("列出文件历史记录", True, f"{agent_id}, 共{len(history)}条")
            return history
            
        except Exception as e:
            self._handle_exception("列出文件历史记录", e)
            raise # 重新抛出异常
    
    async def get_history_by_timerange(
        self, 
        agent_id: str, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """按时间范围获取历史记录"""
        try:
            history = self._list_items(agent_id)
            
            # 过滤时间范围
            filtered_history = []
            for entry in history:
                if TimeUtils.is_time_in_range(entry["timestamp"], start_time, end_time):
                    filtered_history.append(entry)
            
            # 按时间倒序排序
            filtered_history = TimeUtils.sort_by_time(filtered_history, "timestamp", True)
            filtered_history = filtered_history[:limit]
            
            self._log_operation("按时间范围获取文件历史记录", True, f"{agent_id}, 共{len(filtered_history)}条")
            return filtered_history
            
        except Exception as e:
            self._handle_exception("按时间范围获取文件历史记录", e)
            raise  # 重新抛出异常
    
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录"""
        try:
            # 遍历所有代理目录查找并删除历史记录
            from pathlib import Path
            base_path = Path(self.base_path)
            
            for agent_dir in base_path.iterdir():
                if agent_dir.is_dir():
                    deleted = self._delete_item(agent_dir.name, history_id)
                    if deleted:
                        self._log_operation("文件历史记录删除", True, history_id)
                        return True
            return False
            
        except Exception as e:
            self._handle_exception("删除文件历史记录", e)
            raise  # 重新抛出异常
    
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            import shutil
            from pathlib import Path
            agent_dir = Path(self.base_path) / agent_id
            
            if agent_dir.exists():
                shutil.rmtree(agent_dir)
                self._log_operation("文件代理历史记录清空", True, agent_id)
                return True
            return False
            
        except Exception as e:
            self._handle_exception("清空文件代理历史记录", e)
            raise  # 重新抛出异常
    
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
            from pathlib import Path
            base_path = Path(self.base_path)
            
            total_count = 0
            agent_counts = {}
            action_counts = {}
            
            for agent_dir in base_path.iterdir():
                if agent_dir.is_dir():
                    history_files = list(agent_dir.glob("*.json"))
                    agent_id = agent_dir.name
                    agent_counts[agent_id] = len(history_files)
                    total_count += len(history_files)
                    
                    # 统计动作类型
                    for file_path in history_files:
                        history = FileUtils.load_json(file_path)
                        if history:
                            action = history.get("action", "unknown")
                            action_counts[action] = action_counts.get(action, 0) + 1
            
            # 排序统计结果
            top_agents_items = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_agents = [{"agent_id": str(aid), "count": count} for aid, count in top_agents_items]
            
            top_actions_items = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_actions = [{"action": str(action), "count": count} for action, count in top_actions_items]
            
            stats = {
                "total_count": total_count,
                "agent_count": len(agent_counts),
                "top_agents": top_agents,
                "top_actions": top_actions
            }
            
            self._log_operation("获取文件历史统计信息", True)
            return stats
            
        except Exception as e:
            self._handle_exception("获取文件历史统计信息", e)
            raise  # 重新抛出异常
    
    async def get_history_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取历史记录"""
        try:
            # 遍历所有代理目录查找历史记录
            from pathlib import Path
            base_path = Path(self.base_path)
            
            for agent_dir in base_path.iterdir():
                if agent_dir.is_dir():
                    history = self._load_item(agent_dir.name, history_id)
                    if history:
                        self._log_operation("文件历史记录加载", True, history_id)
                        return history
            return None
            
        except Exception as e:
            self._handle_exception("根据ID获取文件历史记录", e)
            raise # 重新抛出异常