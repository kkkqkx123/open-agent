"""线程状态管理服务"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from src.interfaces.threads.storage import IThreadRepository
from src.core.threads.entities import Thread
from src.interfaces.storage.exceptions import StorageValidationError as ValidationError
from .base_service import BaseThreadService

logger = get_logger(__name__)


class SyncStrategy(str, Enum):
    """同步策略枚举"""
    UNIDIRECTIONAL = "unidirectional"  # 单向同步
    BIDIRECTIONAL = "bidirectional"    # 双向同步
    MERGE = "merge"                    # 合并同步


class StateConflict:
    """状态冲突"""
    
    def __init__(
        self,
        field_path: str,
        source_value: Any,
        target_value: Any,
        source_timestamp: datetime,
        target_timestamp: datetime
    ):
        self.field_path = field_path
        self.source_value = source_value
        self.target_value = target_value
        self.source_timestamp = source_timestamp
        self.target_timestamp = target_timestamp
        self.resolved_value = None


class SyncResult:
    """同步结果"""
    
    def __init__(self) -> None:
        self.success = False
        self.synced_thread_ids: List[str] = []
        self.conflicts: List[StateConflict] = []
        self.failed_thread_ids: List[str] = []
        self.sync_metadata: Dict[str, Any] = {}
        self.sync_timestamp = datetime.now()


class ThreadStateService(BaseThreadService):
    """线程状态管理服务"""
    
    def __init__(
        self,
        thread_repository: IThreadRepository
    ):
        """初始化状态服务
        
        Args:
            thread_repository: 线程仓储接口
        """
        super().__init__(thread_repository)
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取线程状态
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程状态，如果不存在则返回None
        """
        try:
            self._log_operation("get_thread_state", thread_id)
            
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                return None
            
            return {
                "thread_id": thread.id,
                "status": thread.status,
                "state": thread.state.copy(),
                "config": thread.config.copy(),
                "metadata": thread.metadata,
                "updated_at": thread.updated_at.isoformat(),
                "message_count": thread.message_count,
                "checkpoint_count": thread.checkpoint_count,
                "branch_count": thread.branch_count
            }
            
        except Exception as e:
            self._handle_exception(e, "get thread state")
            return None
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新线程状态
        
        Args:
            thread_id: 线程ID
            state: 新状态
            
        Returns:
            更新是否成功
        """
        try:
            self._log_operation("update_thread_state", thread_id, state_keys=list(state.keys()))
            
            thread = await self._validate_thread_exists(thread_id)
            
            # 更新状态
            thread.state.update(state)
            thread.update_timestamp()
            
            # 保存线程
            success = await self._thread_repository.update(thread)
            
            return success
            
        except Exception as e:
            self._handle_exception(e, "update thread state")
            return False
    
    async def sync_thread_states(self, thread_ids: List[str], sync_strategy: SyncStrategy = SyncStrategy.BIDIRECTIONAL) -> SyncResult:
        """同步多个线程状态
        
        Args:
            thread_ids: 线程ID列表
            sync_strategy: 同步策略
            
        Returns:
            同步结果
        """
        result = SyncResult()
        
        try:
            # 验证输入参数
            if not thread_ids or len(thread_ids) < 2:
                logger.warning("需要至少两个线程进行同步")
                return result
            
            # 验证所有线程存在
            valid_threads = []
            for thread_id in thread_ids:
                thread = await self._thread_repository.get(thread_id)
                if thread:
                    valid_threads.append(thread)
                else:
                    logger.warning(f"Thread {thread_id} not found, skipping")
                    result.failed_thread_ids.append(thread_id)
            
            if len(valid_threads) < 2:
                logger.warning("需要至少两个有效线程进行同步")
                return result
            
            # 根据同步策略执行同步
            if sync_strategy == SyncStrategy.UNIDIRECTIONAL:
                success = await self._unidirectional_sync(valid_threads, result)
            elif sync_strategy == SyncStrategy.BIDIRECTIONAL:
                success = await self._bidirectional_sync(valid_threads, result)
            elif sync_strategy == SyncStrategy.MERGE:
                success = await self._merge_sync(valid_threads, result)
            else:
                logger.warning(f"不支持的同步策略: {sync_strategy}")
                return result
            
            result.success = success
            
            if success:
                logger.info(f"Thread states synchronized using strategy: {sync_strategy.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"同步线程状态失败: {e}")
            return result
    
    async def _unidirectional_sync(self, threads: List[Thread], result: SyncResult) -> bool:
        """单向同步"""
        try:
            # 使用第一个线程的状态同步到其他线程
            source_thread = threads[0]
            source_state = await self.get_thread_state(source_thread.id)
            
            if not source_state:
                logger.warning(f"Failed to get state from source thread {source_thread.id}")
                return False
            
            state_to_sync = source_state.get("state", {})
            
            # 同步到其他线程
            for thread in threads[1:]:
                success = await self.update_thread_state(thread.id, state_to_sync)
                if success:
                    result.synced_thread_ids.append(thread.id)
                    
                    # 记录同步信息
                    metadata_obj = thread.get_metadata_object()
                    metadata_obj.custom_data['last_sync'] = {
                        "synced_from": source_thread.id,
                        "synced_at": source_state.get("updated_at", ""),
                        "strategy": SyncStrategy.UNIDIRECTIONAL.value
                    }
                    thread.set_metadata_object(metadata_obj)
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
                else:
                    result.failed_thread_ids.append(thread.id)
                    logger.warning(f"Failed to sync state to thread {thread.id}")
            
            return len(result.failed_thread_ids) == 0
            
        except Exception as e:
            logger.error(f"单向同步失败: {e}")
            return False
    
    async def _bidirectional_sync(self, threads: List[Thread], result: SyncResult) -> bool:
        """双向同步"""
        try:
            # 合并所有线程的状态
            merged_state = {}
            
            # 获取所有线程的状态并合并
            for thread in threads:
                thread_state = await self.get_thread_state(thread.id)
                if thread_state and thread_state.get("state"):
                    merged_state.update(thread_state.get("state", {}))
            
            # 将合并后的状态同步到所有线程
            for thread in threads:
                success = await self.update_thread_state(thread.id, merged_state)
                if success:
                    result.synced_thread_ids.append(thread.id)
                    
                    # 记录同步信息
                    metadata_obj = thread.get_metadata_object()
                    metadata_obj.custom_data['last_sync'] = {
                        "synced_with": [t.id for t in threads if t.id != thread.id],
                        "synced_at": datetime.now().isoformat(),
                        "strategy": SyncStrategy.BIDIRECTIONAL.value
                    }
                    thread.set_metadata_object(metadata_obj)
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
                else:
                    result.failed_thread_ids.append(thread.id)
                    logger.warning(f"Failed to sync merged state to thread {thread.id}")
            
            return len(result.failed_thread_ids) == 0
            
        except Exception as e:
            logger.error(f"双向同步失败: {e}")
            return False
    
    async def _merge_sync(self, threads: List[Thread], result: SyncResult) -> bool:
        """合并同步"""
        try:
            merged_state = {}
            sync_sources = {}
            
            # 收集所有状态和来源信息
            for thread in threads:
                thread_state = await self.get_thread_state(thread.id)
                if thread_state and thread_state.get("state"):
                    state_data = thread_state.get("state", {})
                    for key, value in state_data.items():
                        if key not in merged_state:
                            merged_state[key] = value
                            sync_sources[key] = thread.id
                        # 简单的冲突处理：使用最新的值
                        elif thread_state.get("updated_at", "") > sync_sources.get(key, ""):
                            merged_state[key] = value
                            sync_sources[key] = thread.id
            
            # 将合并后的状态同步到所有线程
            for thread in threads:
                success = await self.update_thread_state(thread.id, merged_state)
                if success:
                    result.synced_thread_ids.append(thread.id)
                    
                    # 记录同步信息
                    metadata_obj = thread.get_metadata_object()
                    metadata_obj.custom_data['last_sync'] = {
                        "synced_with": [t.id for t in threads if t.id != thread.id],
                        "synced_at": datetime.now().isoformat(),
                        "strategy": SyncStrategy.MERGE.value,
                        "sources": sync_sources
                    }
                    thread.set_metadata_object(metadata_obj)
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
                else:
                    result.failed_thread_ids.append(thread.id)
                    logger.warning(f"Failed to sync merged state to thread {thread.id}")
            
            return len(result.failed_thread_ids) == 0
            
        except Exception as e:
            logger.error(f"合并同步失败: {e}")
            return False
    
    async def detect_state_conflicts(self, source_thread_id: str, target_thread_id: str) -> List[StateConflict]:
        """检测状态冲突
        
        Args:
            source_thread_id: 源线程ID
            target_thread_id: 目标线程ID
            
        Returns:
            冲突列表
        """
        conflicts: List[StateConflict] = []
        
        try:
            source_state = await self.get_thread_state(source_thread_id)
            target_state = await self.get_thread_state(target_thread_id)
            
            if not source_state or not target_state:
                return conflicts
            
            source_data = source_state.get("state", {})
            target_data = target_state.get("state", {})
            
            # 获取所有字段的并集
            all_fields = set(source_data.keys()) | set(target_data.keys())
            
            for field in all_fields:
                source_value = source_data.get(field)
                target_value = target_data.get(field)
                
                # 检测值冲突
                if source_value != target_value:
                    conflicts.append(StateConflict(
                        field_path=field,
                        source_value=source_value,
                        target_value=target_value,
                        source_timestamp=datetime.fromisoformat(source_state.get("updated_at", "")),
                        target_timestamp=datetime.fromisoformat(target_state.get("updated_at", ""))
                    ))
            
            return conflicts
            
        except Exception as e:
            logger.error(f"检测状态冲突失败: {e}")
            return conflicts
    
    async def validate_thread_state(self, thread_id: str) -> bool:
        """验证线程状态
        
        Args:
            thread_id: 线程ID
            
        Returns:
            状态有效返回True，无效返回False
        """
        try:
            self._log_operation("validate_thread_state", thread_id)
            
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                return False
            
            # 基本状态验证
            if thread.status not in ["active", "paused", "completed", "error"]:
                return False
            
            # 计数器验证
            if thread.message_count < 0 or thread.checkpoint_count < 0 or thread.branch_count < 0:
                return False
            
            # 时间戳验证
            if thread.updated_at < thread.created_at:
                return False
            
            return True
        except Exception:
            return False