"""SQLite状态Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.adapters.repository.utils.sqlite_utils import SQLiteUtils
from src.interfaces.repository.state import IStateRepository
from src.core.state.entities import StateSnapshot, StateHistoryEntry, StateDiff
from ..base import BaseRepository


class SQLiteStateRepository(BaseRepository, IStateRepository):
    """SQLite状态Repository实现"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化SQLite状态Repository"""
        # 初始化基类，指定仓库类型为state
        super().__init__(
            config=config,
            repository_type="state"
        )
    
    def _create_additional_tables(self, snapshots_sql: str, history_sql: str) -> None:
        """创建额外的表"""
        try:
            db_path = self.config.get("db_path")
            if db_path:
                SQLiteUtils.execute_update(db_path, snapshots_sql)
                SQLiteUtils.execute_update(db_path, history_sql)
        except Exception as e:
            self._handle_exception("创建额外表", e)
            raise
    
    async def save_state(self, state_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态
        
        Args:
            state_id: 状态ID
            state_data: 状态数据
            
        Returns:
            保存的状态ID
        """
        try:
            # 准备状态数据
            data = {
                "id": state_id,
                "state_id": state_id,
                "state_data": state_data,
                "type": "state"
            }
            
            # 使用存储后端保存
            result_id = await self.storage_backend.save(self.table_name, data)
            
            self._log_operation("状态保存", True, state_id)
            return result_id
            
        except Exception as e:
            self._handle_exception("保存状态", e)
            raise
    
    async def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """加载状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态数据，如果不存在则返回None
        """
        try:
            # 使用存储后端加载
            data = await self.storage_backend.load(self.table_name, state_id)
            
            if data:
                return data.get("state_data")
            
            return None
            
        except Exception as e:
            self._handle_exception("加载状态", e)
            raise
    
    async def delete_state(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            是否删除成功
        """
        try:
            # 使用存储后端删除
            result = await self.storage_backend.delete(self.table_name, state_id)
            
            self._log_operation("状态删除", result, state_id)
            return result
            
        except Exception as e:
            self._handle_exception("删除状态", e)
            raise
    
    async def exists_state(self, state_id: str) -> bool:
        """检查状态是否存在
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态是否存在
        """
        try:
            # 使用存储后端检查存在性
            return await self.storage_backend.exists(self.table_name, state_id)
            
        except Exception as e:
            self._handle_exception("检查状态存在性", e)
            raise
    
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            状态列表
        """
        try:
            # 使用存储后端列表查询
            filters = {"type": "state"}
            results = await self.storage_backend.list(self.table_name, filters, limit)
            
            # 提取状态数据
            states = []
            for data in results:
                states.append({
                    "state_id": data.get("state_id"),
                    "state_data": data.get("state_data"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at")
                })
            
            self._log_operation("列出状态", True, f"共{len(states)}条")
            return states
            
        except Exception as e:
            self._handle_exception("列出状态", e)
            raise
    
    async def save_snapshot(self, snapshot: StateSnapshot) -> str:
        """保存状态快照
        
        Args:
            snapshot: 状态快照
            
        Returns:
            快照ID
        """
        try:
            # 准备快照数据
            data = {
                "id": snapshot.snapshot_id,
                "snapshot_id": snapshot.snapshot_id,
                "thread_id": snapshot.thread_id,
                "domain_state": snapshot.domain_state,
                "timestamp": snapshot.timestamp,
                "snapshot_name": snapshot.snapshot_name,
                "metadata": snapshot.metadata or {},
                "type": "snapshot"
            }
            
            # 使用存储后端保存
            result_id = await self.storage_backend.save(self.table_name, data)
            
            self._log_operation("快照保存", True, snapshot.snapshot_id)
            return result_id
            
        except Exception as e:
            self._handle_exception("保存快照", e)
            raise
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态快照，如果不存在则返回None
        """
        try:
            # 使用存储后端加载
            data = await self.storage_backend.load(self.table_name, snapshot_id)
            
            if data:
                snapshot_id_value = data.get("snapshot_id")
                thread_id_value = data.get("thread_id")
                domain_state_value = data.get("domain_state")
                timestamp_value = data.get("timestamp")
                
                if snapshot_id_value and thread_id_value and domain_state_value and timestamp_value:
                    return StateSnapshot(
                        snapshot_id=snapshot_id_value,
                        thread_id=thread_id_value,
                        domain_state=domain_state_value,
                        timestamp=timestamp_value,
                        snapshot_name=data.get("snapshot_name", ""),
                        metadata=data.get("metadata", {})
                    )
            
            return None
            
        except Exception as e:
            self._handle_exception("加载快照", e)
            raise
    
    async def save_history_entry(self, entry: StateHistoryEntry) -> str:
        """保存状态历史记录
        
        Args:
            entry: 状态历史记录
            
        Returns:
            历史记录ID
        """
        try:
            # 准备历史记录数据
            data = {
                "id": entry.history_id,
                "history_id": entry.history_id,
                "thread_id": entry.thread_id,
                "timestamp": entry.timestamp,
                "action": entry.action,
                "state_diff": entry.state_diff,
                "metadata": entry.metadata or {},
                "type": "history"
            }
            
            # 使用存储后端保存
            result_id = await self.storage_backend.save(self.table_name, data)
            
            self._log_operation("历史记录保存", True, entry.history_id)
            return result_id
            
        except Exception as e:
            self._handle_exception("保存历史记录", e)
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
            # 使用存储后端列表查询
            filters = {"thread_id": thread_id, "type": "history"}
            results = await self.storage_backend.list(self.table_name, filters, limit)
            
            # 转换为历史记录对象
            entries = []
            for data in results:
                history_id_value = data.get("history_id")
                thread_id_value = data.get("thread_id")
                timestamp_value = data.get("timestamp")
                action_value = data.get("action")
                state_diff_value = data.get("state_diff")
                
                if history_id_value and thread_id_value and timestamp_value and action_value and state_diff_value:
                    entries.append(StateHistoryEntry(
                        history_id=history_id_value,
                        thread_id=thread_id_value,
                        timestamp=timestamp_value,
                        action=action_value,
                        state_diff=state_diff_value,
                        metadata=data.get("metadata", {})
                    ))
            
            self._log_operation("列出历史记录", True, f"共{len(entries)}条")
            return entries
            
        except Exception as e:
            self._handle_exception("列出历史记录", e)
            raise
