"""文件状态Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional, cast

from src.interfaces.repository.state import IStateRepository
from src.interfaces.state.base import IState
from src.core.state.entities import StateSnapshot, StateHistoryEntry, StateDiff
from ..file_base import FileBaseRepository
from ..utils import TimeUtils


class FileStateRepository(FileBaseRepository, IStateRepository):
    """文件状态Repository实现"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化文件状态Repository"""
        super().__init__(config)
    
    async def save_state(self, state_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态
        
        Args:
            state_id: 状态ID
            state_data: 状态数据
            
        Returns:
            保存的状态ID
        """
        try:
            def _save() -> str:
                # 添加元数据
                full_data = TimeUtils.add_timestamp({
                    "state_id": state_id,
                    "state_data": state_data
                })
                
                # 保存到文件
                self._save_item("states", state_id, full_data)
                
                self._log_operation("文件状态保存", True, state_id)
                return state_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存文件状态", e)
            raise # 重新抛出异常
    
    async def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """加载状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态数据，如果不存在则返回None
        """
        try:
            def _load() -> Optional[Dict[str, Any]]:
                data = self._load_item("states", state_id)
                if data:
                    self._log_operation("文件状态加载", True, state_id)
                    return data["state_data"]  # type: ignore[no-any-return]
                return None
            
            result = await asyncio.get_event_loop().run_in_executor(None, _load)
            return result
            
        except Exception as e:
            self._handle_exception("加载文件状态", e)
            raise # 重新抛出异常
    
    async def delete_state(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            是否删除成功
        """
        try:
            def _delete() -> bool:
                deleted = self._delete_item("states", state_id)
                self._log_operation("文件状态删除", deleted, state_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除文件状态", e)
            raise # 重新抛出异常
    
    async def exists_state(self, state_id: str) -> bool:
        """检查状态是否存在
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态是否存在
        """
        try:
            def _exists() -> bool:
                return self._load_item("states", state_id) is not None
            
            return await asyncio.get_event_loop().run_in_executor(None, _exists)
            
        except Exception as e:
            self._handle_exception("检查文件状态存在性", e)
            raise # 重新抛出异常
    
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            状态列表
        """
        try:
            def _list() -> List[Dict[str, Any]]:
                states = self._list_items("states")
                
                # 按更新时间排序
                states = TimeUtils.sort_by_time(states, "updated_at", True)
                states = states[:limit]
                
                # 只返回需要的格式
                result = []
                for state in states:
                    result.append({
                        "state_id": state["state_id"],
                        "state_data": state["state_data"],
                        "created_at": state["created_at"],
                        "updated_at": state["updated_at"]
                    })
                
                self._log_operation("列出文件状态", True, f"共{len(result)}条")
                return result
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出文件状态", e)
            raise # 重新抛出异常
    
    async def save_snapshot(self, snapshot: StateSnapshot) -> str:
        """保存状态快照
        
        Args:
            snapshot: 状态快照
            
        Returns:
            快照ID
        """
        try:
            def _save() -> str:
                snapshot_data = snapshot.to_dict()
                self._save_item("snapshots", snapshot.snapshot_id, snapshot_data)
                self._log_operation("文件快照保存", True, snapshot.snapshot_id)
                return snapshot.snapshot_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存文件快照", e)
            raise
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态快照，如果不存在则返回None
        """
        try:
            def _load() -> Optional[StateSnapshot]:
                data = self._load_item("snapshots", snapshot_id)
                if data:
                    self._log_operation("文件快照加载", True, snapshot_id)
                    return StateSnapshot.from_dict(data)
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载文件快照", e)
            raise
    
    async def save_history_entry(self, entry: StateHistoryEntry) -> str:
        """保存状态历史记录
        
        Args:
            entry: 状态历史记录
            
        Returns:
            历史记录ID
        """
        try:
            def _save() -> str:
                entry_data = entry.to_dict()
                self._save_item("history", entry.history_id, entry_data)
                self._log_operation("文件历史记录保存", True, entry.history_id)
                return entry.history_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存文件历史记录", e)
            raise
    
    async def list_history_entries(self, thread_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """列出线程的历史记录
        
        Args:
            thread_id: 线程ID
            limit: 返回记录数限制
            
        Returns:
            历史记录列表
        """
        try:
            def _list() -> List[StateHistoryEntry]:
                all_entries = self._list_items("history")
                
                # 过滤线程ID
                thread_entries = [
                    entry for entry in all_entries
                    if entry.get("thread_id") == thread_id
                ]
                
                # 按时间戳排序
                thread_entries = TimeUtils.sort_by_time(thread_entries, "timestamp", True)
                thread_entries = thread_entries[:limit]
                
                # 转换为StateHistoryEntry对象
                result = []
                for entry_data in thread_entries:
                    result.append(StateHistoryEntry.from_dict(entry_data))
                
                self._log_operation("列出文件历史记录", True, f"共{len(result)}条")
                return result
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出文件历史记录", e)
            raise