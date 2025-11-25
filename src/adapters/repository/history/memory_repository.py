"""内存历史记录Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import IHistoryRepository
from ..memory_base import MemoryBaseRepository
from ..utils import TimeUtils, IdUtils


class MemoryHistoryRepository(MemoryBaseRepository, IHistoryRepository):
    """内存历史Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存历史Repository"""
        super().__init__(config)
    
    async def save_history(self, entry: Dict[str, Any]) -> str:
        """保存历史记录"""
        try:
            def _save():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存内存历史记录", e)
            raise  # 重新抛出异常
    
    async def get_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录"""
        try:
            def _get():
                history_ids = self._get_from_index("agent", agent_id)
                # 过滤掉None值，确保只返回有效的历史记录
                history = [item for hid in history_ids if (item := self._load_item(hid)) is not None]
                
                # 按时间倒序排序
                history = TimeUtils.sort_by_time(history, "timestamp", True)
                history = history[:limit]
                
                self._log_operation("获取内存历史记录", True, f"{agent_id}, 共{len(history)}条")
                return history
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取内存历史记录", e)
            raise # 重新抛出异常
    
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录"""
        try:
            def _delete():
                history = self._load_item(history_id)
                if not history:
                    return False
                
                # 从索引中移除
                self._remove_from_index("agent", history["agent_id"], history_id)
                
                # 从存储中删除
                deleted = self._delete_item(history_id)
                self._log_operation("内存历史记录删除", deleted, history_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除内存历史记录", e)
            raise  # 重新抛出异常
    
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            def _clear():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _clear)
            
        except Exception as e:
            self._handle_exception("清空内存代理历史记录", e)
            raise # 重新抛出异常
    
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
            def _get_stats():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_stats)
            
        except Exception as e:
            self._handle_exception("获取内存历史统计信息", e)
            raise # 重新抛出异常