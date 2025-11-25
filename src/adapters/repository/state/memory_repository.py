"""内存状态Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import IStateRepository
from ..memory_base import MemoryBaseRepository
from ..utils import TimeUtils


class MemoryStateRepository(MemoryBaseRepository, IStateRepository):
    """内存状态Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存状态Repository"""
        super().__init__(config)
    
    async def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态"""
        try:
            def _save():
                full_state = TimeUtils.add_timestamp({
                    "agent_id": agent_id,
                    "state_data": state_data
                })
                
                # 保存到存储
                self._save_item(agent_id, full_state)
                
                self._log_operation("内存状态保存", True, agent_id)
                return agent_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存内存状态", e)
            raise # 重新抛出异常
    
    async def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载状态"""
        try:
            def _load():
                state = self._load_item(agent_id)
                if state:
                    self._log_operation("内存状态加载", True, agent_id)
                    return state["state_data"]
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载内存状态", e)
            raise # 重新抛出异常
    
    async def delete_state(self, agent_id: str) -> bool:
        """删除状态"""
        try:
            def _delete():
                deleted = self._delete_item(agent_id)
                self._log_operation("内存状态删除", deleted, agent_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除内存状态", e)
            raise # 重新抛出异常
    
    async def exists_state(self, agent_id: str) -> bool:
        """检查状态是否存在"""
        try:
            def _exists():
                return self._load_item(agent_id) is not None
            
            return await asyncio.get_event_loop().run_in_executor(None, _exists)
            
        except Exception as e:
            self._handle_exception("检查内存状态存在性", e)
            raise # 重新抛出异常
    
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态"""
        try:
            def _list():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出内存状态", e)
            raise # 重新抛出异常