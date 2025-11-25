"""状态Repository重构实现

使用基类和工具类重构的状态Repository实现。
"""

from typing import Dict, Any, List, Optional

from src.interfaces.repository import IStateRepository
from .base import SQLiteBaseRepository, MemoryBaseRepository, FileBaseRepository
from .utils import JsonUtils, TimeUtils, IdUtils, SQLiteUtils, FileUtils


class SQLiteStateRepository(SQLiteBaseRepository, IStateRepository):
    """SQLite状态Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite状态Repository"""
        table_sql = """
            CREATE TABLE IF NOT EXISTS states (
                agent_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        super().__init__(config, "states", table_sql)
    
    async def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态"""
        try:
            data = {
                "agent_id": agent_id,
                "state_data": JsonUtils.serialize(state_data)
            }
            
            self._insert_or_replace(data)
            self._log_operation("状态保存", True, agent_id)
            return agent_id
            
        except Exception as e:
            self._handle_exception("保存状态", e)
            raise  # 重新抛出异常，不会到达下一行
    
    async def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载状态"""
        try:
            row = self._find_by_id("agent_id", agent_id)
            if row:
                return JsonUtils.deserialize(row[1])
            return None
            
        except Exception as e:
            self._handle_exception("加载状态", e)
            raise  # 重新抛出异常
    
    async def delete_state(self, agent_id: str) -> bool:
        """删除状态"""
        try:
            deleted = self._delete_by_id("agent_id", agent_id)
            self._log_operation("状态删除", deleted, agent_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除状态", e)
            raise # 重新抛出异常
    
    async def exists_state(self, agent_id: str) -> bool:
        """检查状态是否存在"""
        try:
            query = "SELECT 1 FROM states WHERE agent_id = ?"
            results = SQLiteUtils.execute_query(self.db_path, query, (agent_id,))
            exists = len(results) > 0
            return exists
            
        except Exception as e:
            self._handle_exception("检查状态存在性", e)
            raise # 重新抛出异常
    
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态"""
        try:
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
            
        except Exception as e:
            self._handle_exception("列出状态", e)
            raise # 重新抛出异常


class MemoryStateRepository(MemoryBaseRepository, IStateRepository):
    """内存状态Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存状态Repository"""
        super().__init__(config)
    
    async def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态"""
        try:
            full_state = TimeUtils.add_timestamp({
                "agent_id": agent_id,
                "state_data": state_data
            })
            
            # 保存到存储
            self._save_item(agent_id, full_state)
            
            self._log_operation("内存状态保存", True, agent_id)
            return agent_id
            
        except Exception as e:
            self._handle_exception("保存内存状态", e)
            raise # 重新抛出异常
    
    async def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载状态"""
        try:
            state = self._load_item(agent_id)
            if state:
                self._log_operation("内存状态加载", True, agent_id)
                return state["state_data"]
            return None
            
        except Exception as e:
            self._handle_exception("加载内存状态", e)
            raise # 重新抛出异常
    
    async def delete_state(self, agent_id: str) -> bool:
        """删除状态"""
        try:
            deleted = self._delete_item(agent_id)
            self._log_operation("内存状态删除", deleted, agent_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除内存状态", e)
            raise # 重新抛出异常
    
    async def exists_state(self, agent_id: str) -> bool:
        """检查状态是否存在"""
        try:
            return self._load_item(agent_id) is not None
            
        except Exception as e:
            self._handle_exception("检查内存状态存在性", e)
            raise # 重新抛出异常
    
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态"""
        try:
            states = [item for item in self._storage.values() if item is not None]
            
            # 按更新时间排序
            states = TimeUtils.sort_by_time(states, "updated_at", True)
            states = states[:limit]
            
            # 只返回状态数据
            result = []
            for state in states:
                result.append({
                    "agent_id": state["agent_id"],
                    "state_data": state["state_data"],
                    "created_at": state["created_at"],
                    "updated_at": state["updated_at"]
                })
            
            self._log_operation("列出内存状态", True, f"共{len(result)}条")
            return result
            
        except Exception as e:
            self._handle_exception("列出内存状态", e)
            raise # 重新抛出异常


class FileStateRepository(FileBaseRepository, IStateRepository):
    """文件状态Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件状态Repository"""
        super().__init__(config)
    
    async def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态"""
        try:
            # 添加元数据
            full_data = TimeUtils.add_timestamp({
                "agent_id": agent_id,
                "state_data": state_data
            })
            
            # 保存到文件
            self._save_item("states", agent_id, full_data)
            
            self._log_operation("文件状态保存", True, agent_id)
            return agent_id
            
        except Exception as e:
            self._handle_exception("保存文件状态", e)
            raise # 重新抛出异常
    
    async def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载状态"""
        try:
            data = self._load_item("states", agent_id)
            if data:
                self._log_operation("文件状态加载", True, agent_id)
                return data["state_data"]
            return None
            
        except Exception as e:
            self._handle_exception("加载文件状态", e)
            raise # 重新抛出异常
    
    async def delete_state(self, agent_id: str) -> bool:
        """删除状态"""
        try:
            deleted = self._delete_item("states", agent_id)
            self._log_operation("文件状态删除", deleted, agent_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除文件状态", e)
            raise # 重新抛出异常
    
    async def exists_state(self, agent_id: str) -> bool:
        """检查状态是否存在"""
        try:
            return self._load_item("states", agent_id) is not None
            
        except Exception as e:
            self._handle_exception("检查文件状态存在性", e)
            raise # 重新抛出异常
    
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态"""
        try:
            states = self._list_items("states")
            
            # 按更新时间排序
            states = TimeUtils.sort_by_time(states, "updated_at", True)
            states = states[:limit]
            
            # 只返回需要的格式
            result = []
            for state in states:
                result.append({
                    "agent_id": state["agent_id"],
                    "state_data": state["state_data"],
                    "created_at": state["created_at"],
                    "updated_at": state["updated_at"]
                })
            
            self._log_operation("列出文件状态", True, f"共{len(result)}条")
            return result
            
        except Exception as e:
            self._handle_exception("列出文件状态", e)
            raise # 重新抛出异常