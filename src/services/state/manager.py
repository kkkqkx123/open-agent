"""状态管理服务实现

提供简化的状态管理功能，直接整合历史记录、快照和持久化功能。
"""

import asyncio
import time
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime

from src.interfaces.state.base import IState
from src.interfaces.state.manager import IStateManager
from src.infrastructure.common.serialization import Serializer
from src.core.state.entities import StateStatistics
from src.core.state.core.base import BaseStateManager, StateValidationMixin

from src.interfaces.repository import IHistoryRepository, ISnapshotRepository
from src.core.state.entities import StateDiff, StateHistoryEntry, StateSnapshot


logger = get_logger(__name__)


class StateManager(IStateManager, BaseStateManager, StateValidationMixin):
    """简化的状态管理器实现
    
    直接整合基础状态管理、历史记录和快照功能，避免过度抽象。
    """
    
    def __init__(self,
                 history_repository: IHistoryRepository,
                 snapshot_repository: ISnapshotRepository,
                 serializer: Optional[Serializer] = None,
                 cache_size: int = 1000,
                 cache_ttl: int = 300):
        """初始化状态管理器
        
        Args:
            history_repository: 历史记录Repository
            snapshot_repository: 快照Repository
            serializer: 序列化器
            cache_size: 缓存大小
            cache_ttl: 缓存TTL（秒）
        """
        super().__init__(serializer)
        self._history_repository = history_repository
        self._snapshot_repository = snapshot_repository
        
        # 简单的内存缓存
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_size = cache_size
        self._cache_ttl = cache_ttl
        
        # 状态到线程的映射
        self._state_threads: Dict[str, str] = {}
        
        logger.info("状态管理器初始化完成（简化版本）")
    
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> IState:
        """创建状态"""
        self._validate_state_id(state_id)
        self._validate_state_data(initial_state)
        
        # 确保状态有ID
        state_data = initial_state.copy()
        state_data['id'] = state_id
        state_data['created_at'] = datetime.now().isoformat()
        state_data['updated_at'] = datetime.now().isoformat()
        
        # 保存到内存
        self._states[state_id] = state_data
        
        # 缓存状态
        self._set_cache(state_id, state_data)
        
        logger.debug(f"状态创建成功: {state_id}")
        return self._create_state_wrapper(state_data)
    
    def get_state(self, state_id: str) -> Optional[IState]:
        """获取状态"""
        # 先从缓存获取
        state_data = self._get_cache(state_id)
        if state_data:
            logger.debug(f"状态缓存命中: {state_id}")
            return self._create_state_wrapper(state_data)
        
        # 从内存获取
        state_data = self._states.get(state_id)
        if state_data:
            logger.debug(f"状态内存命中: {state_id}")
            # 回填缓存
            self._set_cache(state_id, state_data)
            return self._create_state_wrapper(state_data)
        
        logger.warning(f"状态不存在: {state_id}")
        return None
    
    def update_state(self, state_id: str, updates: Dict[str, Any]) -> IState:
        """更新状态"""
        if state_id not in self._states:
            raise ValueError(f"状态不存在: {state_id}")
        
        self._validate_state_data(updates)
        
        # 合并更新
        current_state = self._states[state_id]
        updated_state = self._merge_states(current_state, updates)
        updated_state['updated_at'] = datetime.now().isoformat()
        
        # 更新内存
        self._states[state_id] = updated_state
        
        # 更新缓存
        self._set_cache(state_id, updated_state)
        
        logger.debug(f"状态更新成功: {state_id}")
        return self._create_state_wrapper(updated_state)
    
    def delete_state(self, state_id: str) -> bool:
        """删除状态"""
        # 从内存删除
        memory_deleted = state_id in self._states
        if memory_deleted:
            del self._states[state_id]
        
        # 从线程映射删除
        thread_deleted = state_id in self._state_threads
        if thread_deleted:
            del self._state_threads[state_id]
        
        # 从缓存删除
        cache_deleted = self._delete_cache(state_id)
        
        success = memory_deleted or cache_deleted
        if success:
            logger.debug(f"状态删除成功: {state_id}")
        else:
            logger.warning(f"状态不存在，无法删除: {state_id}")
        
        return success
    
    def list_states(self) -> List[str]:
        """列出所有状态ID"""
        return list(self._states.keys())
    
    def create_state_with_history(self, state_id: str, initial_state: Dict[str, Any],
                                 thread_id: str) -> IState:
        """创建状态并启用历史记录"""
        state = self.create_state(state_id, initial_state)
        self._state_threads[state_id] = thread_id
        
        # 记录初始状态
        asyncio.create_task(self._record_state_change_async(
            thread_id, {}, initial_state, "create"
        ))
        
        return state
    
    def update_state_with_history(self, state_id: str, updates: Dict[str, Any],
                                 thread_id: str, action: str = "update") -> IState:
        """更新状态并记录历史"""
        if state_id not in self._states:
            raise ValueError(f"状态不存在: {state_id}")
        
        # 获取当前状态
        old_state = self._states[state_id].copy()
        
        # 更新状态
        new_state = self.update_state(state_id, updates)
        
        # 记录历史
        asyncio.create_task(self._record_state_change_async(
            thread_id, old_state, self._states[state_id], action
        ))
        
        # 更新线程映射
        self._state_threads[state_id] = thread_id
        
        return new_state
    
    def create_state_snapshot(self, state_id: str, thread_id: str,
                             snapshot_name: str = "") -> str:
        """为状态创建快照"""
        state_data = self._states.get(state_id)
        if not state_data:
            raise ValueError(f"状态不存在: {state_id}")
        
        # 创建快照
        snapshot_id = asyncio.run(self._create_snapshot_async(
            thread_id, state_data, snapshot_name
        ))
        
        logger.debug(f"快照创建成功: {snapshot_id}")
        return snapshot_id
    
    def restore_state_from_snapshot(self, snapshot_id: str, state_id: str) -> Optional[IState]:
        """从快照恢复状态"""
        snapshot_data = asyncio.run(self._restore_snapshot_async(snapshot_id))
        if not snapshot_data:
            logger.warning(f"快照不存在: {snapshot_id}")
            return None
        
        # 恢复状态数据
        restored_state = snapshot_data.copy()
        restored_state['id'] = state_id
        restored_state['updated_at'] = datetime.now().isoformat()
        
        # 更新内存和缓存
        self._states[state_id] = restored_state
        self._set_cache(state_id, restored_state)
        
        # 更新线程映射
        thread_id = snapshot_data.get('thread_id')
        if thread_id:
            self._state_threads[state_id] = thread_id
        
        logger.debug(f"状态从快照恢复成功: {state_id} <- {snapshot_id}")
        return self._create_state_wrapper(restored_state)
    
    def get_state_thread(self, state_id: str) -> Optional[str]:
        """获取状态关联的线程ID"""
        return self._state_threads.get(state_id)
    
    def get_thread_states(self, thread_id: str) -> List[str]:
        """获取线程关联的所有状态ID"""
        return [state_id for state_id, tid in self._state_threads.items() if tid == thread_id]
    
    def validate_state(self, state_id: str) -> List[str]:
        """验证状态"""
        state_data = self._states.get(state_id)
        if not state_data:
            state_data = self._get_cache(state_id)
        
        if not state_data:
            return [f"状态不存在: {state_id}"]
        
        return self.validate_state_completeness(state_data)
    
    def get_statistics(self) -> StateStatistics:
        """获取状态统计信息"""
        base_stats = super().get_statistics()
        
        # 统计线程数量
        thread_counts: Dict[str, int] = {}
        for thread_id in self._state_threads.values():
            thread_counts[thread_id] = thread_counts.get(thread_id, 0) + 1
        
        return StateStatistics(
            total_states=base_stats.total_states,
            total_snapshots=0,  # 简化版本暂不统计
            total_history_entries=0,  # 简化版本暂不统计
            storage_size_bytes=0,  # 简化版本暂不统计
            thread_counts=thread_counts,
            last_updated=datetime.now()
        )
    
    def execute_with_state_management(
        self,
        state_id: str,
        executor: Callable[[Dict[str, Any]], Tuple[Dict[str, Any], bool]],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[IState], bool]:
        """带状态管理的执行"""
        try:
            # 1. 获取当前状态
            current_state = self.get_state(state_id)
            if not current_state:
                raise ValueError(f"状态不存在: {state_id}")
            
            current_state_dict = current_state.to_dict()
            
            # 2. 执行业务逻辑
            new_state_dict, success = executor(current_state_dict)
            
            if success:
                # 3. 更新状态
                updated_state = self.update_state(state_id, new_state_dict)
                return updated_state, True
            else:
                return current_state, False
            
        except Exception as e:
            logger.error(f"带状态管理的执行失败: {e}")
            raise
    
    def cleanup_cache(self) -> int:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self._cache_timestamps.items():
            if current_time - timestamp > self._cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._delete_cache(key)
        
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")
        
        return len(expired_keys)
    
    def _create_state_wrapper(self, state_data: Dict[str, Any]) -> IState:
        """创建状态包装器"""
        return StateWrapper(state_data, self)
    
    # 缓存方法
    def _get_cache(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存"""
        if state_id not in self._cache:
            return None
        
        # 检查是否过期
        if state_id in self._cache_timestamps:
            if time.time() - self._cache_timestamps[state_id] > self._cache_ttl:
                self._delete_cache(state_id)
                return None
        
        return self._cache.get(state_id)
    
    def _set_cache(self, state_id: str, state_data: Dict[str, Any]) -> None:
        """设置缓存"""
        # 检查缓存大小限制
        if len(self._cache) >= self._cache_size:
            # 删除最旧的缓存项
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=lambda k: self._cache_timestamps[k])
            self._delete_cache(oldest_key)
        
        self._cache[state_id] = state_data.copy()
        self._cache_timestamps[state_id] = time.time()
    
    def _delete_cache(self, state_id: str) -> bool:
        """删除缓存"""
        deleted = False
        if state_id in self._cache:
            del self._cache[state_id]
            deleted = True
        if state_id in self._cache_timestamps:
            del self._cache_timestamps[state_id]
            deleted = True
        return deleted
    
    # 异步辅助方法
    async def _record_state_change_async(self, thread_id: str, old_state: Dict[str, Any],
                                        new_state: Dict[str, Any], action: str) -> str:
        """异步记录状态变化"""
        try:
            # 创建历史记录条目
            entry = self._create_history_entry(thread_id, old_state, new_state, action)
            
            # 转换为字典格式保存到Repository
            entry_dict = {
                "history_id": entry.history_id,
                "thread_id": entry.thread_id,
                "timestamp": entry.timestamp,
                "action": entry.action,
                "state_diff": entry.state_diff,
                "metadata": entry.metadata or {}
            }
            
            # 保存到Repository
            await self._history_repository.save_history(entry_dict)
            
            logger.debug(f"状态变化记录成功: {entry.history_id}")
            return entry.history_id
            
        except Exception as e:
            logger.error(f"记录状态变化失败: {e}")
            raise
    
    async def _create_snapshot_async(self, thread_id: str, state_data: Dict[str, Any],
                                   snapshot_name: str) -> str:
        """异步创建快照"""
        try:
            # 创建快照对象
            snapshot = self._create_snapshot(thread_id, state_data, snapshot_name)
            
            # 转换为字典格式保存到Repository
            snapshot_dict = {
                "snapshot_id": snapshot.snapshot_id,
                "thread_id": snapshot.thread_id,
                "domain_state": snapshot.domain_state,
                "timestamp": snapshot.timestamp,
                "snapshot_name": snapshot.snapshot_name,
                "metadata": snapshot.metadata or {}
            }
            
            # 保存到Repository
            snapshot_id = await self._snapshot_repository.save_snapshot(snapshot_dict)
            
            logger.debug(f"快照创建成功: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"创建快照失败: {e}")
            raise
    
    async def _restore_snapshot_async(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """异步恢复快照"""
        try:
            # 从Repository获取
            snapshot_dict = await self._snapshot_repository.load_snapshot(snapshot_id)
            if not snapshot_dict:
                return None
            
            return snapshot_dict["domain_state"]
            
        except Exception as e:
            logger.error(f"恢复快照失败: {e}")
            return None
    
    def _create_history_entry(self, thread_id: str, old_state: Dict[str, Any],
                             new_state: Dict[str, Any], action: str) -> StateHistoryEntry:
        """创建历史记录条目"""
        from uuid import uuid4
        state_diff = StateDiff.calculate(old_state, new_state)
        
        return StateHistoryEntry(
            history_id=str(uuid4()),
            thread_id=thread_id,
            timestamp=datetime.now().isoformat(),
            action=action,
            state_diff=state_diff.to_dict()
        )
    
    def _create_snapshot(self, thread_id: str, state_data: Dict[str, Any],
                        snapshot_name: str) -> StateSnapshot:
        """创建快照对象"""
        from uuid import uuid4
        
        return StateSnapshot(
            snapshot_id=str(uuid4()),
            thread_id=thread_id,
            domain_state=state_data,
            timestamp=datetime.now().isoformat(),
            snapshot_name=snapshot_name or f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            metadata={}
        )


class StateWrapper(IState):
    """状态包装器实现"""
    
    def __init__(self, state_data: Dict[str, Any], manager: Optional[StateManager] = None):
        """初始化状态包装器"""
        self._state_data = state_data
        self._manager = manager
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        return self._state_data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置数据"""
        self._state_data[key] = value
        self._state_data['updated_at'] = datetime.now().isoformat()
        
        # 如果有管理器，同步更新
        if self._manager:
            state_id = self.get_id()
            if state_id:
                self._manager.update_state(state_id, {key: value})
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        metadata = self._state_data.get('metadata', {})
        return metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        if 'metadata' not in self._state_data:
            self._state_data['metadata'] = {}
        self._state_data['metadata'][key] = value
        self._state_data['updated_at'] = datetime.now().isoformat()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        return self._state_data.get('id')
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._state_data['id'] = id
        self._state_data['updated_at'] = datetime.now().isoformat()
    
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        created_at = self._state_data.get('created_at')
        if created_at:
            return datetime.fromisoformat(created_at)
        return datetime.now()
    
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        updated_at = self._state_data.get('updated_at')
        if updated_at:
            return datetime.fromisoformat(updated_at)
        return datetime.now()
    
    def is_complete(self) -> bool:
        """检查是否完成"""
        return bool(self._state_data.get('complete', False))
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self._state_data['complete'] = True
        self._state_data['updated_at'] = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._state_data.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateWrapper':
        """从字典创建状态"""
        return cls(data, None)