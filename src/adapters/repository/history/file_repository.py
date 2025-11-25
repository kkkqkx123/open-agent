"""文件历史记录Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import IHistoryRepository
from ..file_base import FileBaseRepository
from ..utils import TimeUtils, IdUtils, FileUtils


class FileHistoryRepository(FileBaseRepository, IHistoryRepository):
    """文件历史Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件历史Repository"""
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
                
                # 保存到文件
                self._save_item(entry["agent_id"], history_id, full_entry)
                
                self._log_operation("文件历史记录保存", True, history_id)
                return history_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存文件历史记录", e)
            raise  # 重新抛出异常
    
    async def get_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录"""
        try:
            def _get():
                history = self._list_items(agent_id)
                
                # 按时间倒序排序
                history = TimeUtils.sort_by_time(history, "timestamp", True)
                history = history[:limit]
                
                self._log_operation("列出文件历史记录", True, f"{agent_id}, 共{len(history)}条")
                return history
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("列出文件历史记录", e)
            raise # 重新抛出异常
    
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录"""
        try:
            def _delete():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除文件历史记录", e)
            raise # 重新抛出异常
    
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            def _clear():
                import shutil
                from pathlib import Path
                agent_dir = Path(self.base_path) / agent_id
                
                if agent_dir.exists():
                    shutil.rmtree(agent_dir)
                    self._log_operation("文件代理历史记录清空", True, agent_id)
                    return True
                return False
            
            return await asyncio.get_event_loop().run_in_executor(None, _clear)
            
        except Exception as e:
            self._handle_exception("清空文件代理历史记录", e)
            raise # 重新抛出异常
    
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
            def _get_stats():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_stats)
            
        except Exception as e:
            self._handle_exception("获取文件历史统计信息", e)
            raise  # 重新抛出异常