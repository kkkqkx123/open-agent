"""线程协作服务"""

import uuid
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime
import logging

from src.interfaces.threads.storage import IThreadRepository
from src.interfaces.history import IHistoryManager
from src.core.common.exceptions import ValidationError, StorageNotFoundError as EntityNotFoundError

if TYPE_CHECKING:
    from src.interfaces.checkpoint import ICheckpointManager
    from src.interfaces.threads.checkpoint import IThreadCheckpointManager

logger = logging.getLogger(__name__)


class ThreadCollaborationService:
    """线程协作服务"""
    
    def __init__(
        self,
        thread_repository: IThreadRepository,
        history_manager: Optional[IHistoryManager] = None,
        checkpoint_manager: Optional['ICheckpointManager'] = None,
        thread_checkpoint_manager: Optional['IThreadCheckpointManager'] = None
    ):
        """初始化协作服务
        
        Args:
            thread_repository: 线程仓储接口
            history_manager: 历史管理器（可选）
            checkpoint_manager: 检查点管理器（可选）
        """
        self._thread_repository = thread_repository
        self._history_manager = history_manager
        self._checkpoint_manager = checkpoint_manager
        self._thread_checkpoint_manager = thread_checkpoint_manager
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread状态，如果不存在则返回None
        """
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                return None
            
            return {
                "thread_id": thread.id,
                "status": thread.status.value,
                "state": thread.state.copy(),
                "config": thread.config.copy(),
                "metadata": thread.metadata.model_dump(),
                "updated_at": thread.updated_at.isoformat(),
                "message_count": thread.message_count,
                "checkpoint_count": thread.checkpoint_count,
                "branch_count": thread.branch_count
            }
            
        except Exception as e:
            raise ValidationError(f"Failed to get thread state: {str(e)}")
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态
        
        Args:
            thread_id: Thread ID
            state: 新状态
            
        Returns:
            更新是否成功
        """
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 记录状态变更历史
            old_state = thread.state.copy()
            
            # 更新状态
            thread.state.update(state)
            thread.update_timestamp()
            
            # 保存线程
            success = await self._thread_repository.update(thread)
            
            # 记录历史
            if success and self._history_manager:
                try:
                    await self._record_state_change(thread_id, old_state, state)
                except Exception as e:
                    logger.warning(f"Failed to record state change: {e}")
            
            return success
            
        except Exception as e:
            raise ValidationError(f"Failed to update thread state: {str(e)}")
    
    async def rollback_thread(self, thread_id: str, checkpoint_id: str) -> bool:
        """回滚Thread到指定检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            回滚是否成功
        """
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 需要与检查点系统集成
            # 由于我们没有直接的依赖，这里使用一个通用方法获取检查点状态
            # 实际实现中需要从checkpoint_manager获取指定checkpoint的状态
            checkpoint_state = await self._get_checkpoint_state(thread_id, checkpoint_id)
            if checkpoint_state is None:
                raise EntityNotFoundError(f"Checkpoint {checkpoint_id} not found")
            
            # 更新线程状态为检查点状态
            thread.state = checkpoint_state
            thread.update_timestamp()
            
            success = await self._thread_repository.update(thread)
            
            # 记录回滚历史
            if success and self._history_manager:
                try:
                    await self._record_rollback(thread_id, checkpoint_id)
                except Exception as e:
                    logger.warning(f"Failed to record rollback: {e}")
            
            if success:
                logger.info(f"Thread {thread_id} rolled back to checkpoint {checkpoint_id}")
            
            return success
            
        except Exception as e:
            raise ValidationError(f"Failed to rollback thread: {str(e)}")
    
    async def share_thread_state(
        self,
        source_thread_id: str,
        target_thread_id: str,
        checkpoint_id: str,
        permissions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """共享Thread状态到其他Thread
        
        Args:
            source_thread_id: 源Thread ID
            target_thread_id: 目标Thread ID
            checkpoint_id: 检查点ID
            permissions: 权限配置
            
        Returns:
            共享是否成功
        """
        try:
            # 验证源线程存在
            source_thread = await self._thread_repository.get(source_thread_id)
            if not source_thread:
                raise EntityNotFoundError(f"Source thread {source_thread_id} not found")
            
            # 验证目标线程存在
            target_thread = await self._thread_repository.get(target_thread_id)
            if not target_thread:
                raise EntityNotFoundError(f"Target thread {target_thread_id} not found")
            
            # 获取源线程状态
            source_state = source_thread.state.copy()
            
            # 应用权限过滤
            if permissions:
                source_state = self._apply_permissions(source_state, permissions)
            
            # 更新目标线程状态
            target_thread.state.update(source_state)
            target_thread.update_timestamp()
            
            success = await self._thread_repository.update(target_thread)
            
            # 记录共享历史
            if success and self._history_manager:
                try:
                    await self._record_state_share(source_thread_id, target_thread_id, checkpoint_id)
                except Exception as e:
                    logger.warning(f"Failed to record state share: {e}")
            
            logger.info(f"Shared state from thread {source_thread_id} to {target_thread_id}")
            return success
            
        except Exception as e:
            raise ValidationError(f"Failed to share thread state: {str(e)}")
    
    async def create_shared_session(self, thread_ids: List[str], session_config: Dict[str, Any]) -> str:
        """创建共享会话
        
        Args:
            thread_ids: Thread ID列表
            session_config: 会话配置
            
        Returns:
            共享会话ID
        """
        try:
            # 验证所有线程存在
            for thread_id in thread_ids:
                thread = await self._thread_repository.get(thread_id)
                if not thread:
                    raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 生成会话ID
            session_id = str(uuid.uuid4())
            
            # TODO: 实际的共享会话创建逻辑
            # 这里需要与会话系统集成
            # 目前简化处理，只记录会话信息
            
            logger.info(f"Created shared session {session_id} for threads {thread_ids}")
            
            # 记录会话创建历史
            if self._history_manager:
                try:
                    await self._record_session_creation(session_id, thread_ids, session_config)
                except Exception as e:
                    logger.warning(f"Failed to record session creation: {e}")
            
            return session_id
            
        except Exception as e:
            raise ValidationError(f"Failed to create shared session: {str(e)}")
    
    async def sync_thread_states(
        self,
        thread_ids: List[str],
        sync_strategy: str = "bidirectional"
    ) -> bool:
        """同步多个Thread状态
        
        Args:
            thread_ids: Thread ID列表
            sync_strategy: 同步策略
            
        Returns:
            同步是否成功
        """
        try:
            if len(thread_ids) < 2:
                raise ValidationError("At least 2 threads required for synchronization")
            
            # 验证所有线程存在
            threads = []
            for thread_id in thread_ids:
                thread = await self._thread_repository.get(thread_id)
                if not thread:
                    raise EntityNotFoundError(f"Thread {thread_id} not found")
                threads.append(thread)
            
            # 根据同步策略执行同步
            if sync_strategy == "bidirectional":
                # 双向同步：合并所有线程状态
                merged_state = {}
                for thread in threads:
                    merged_state.update(thread.state)
                
                # 更新所有线程
                for thread in threads:
                    thread.state.update(merged_state)
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
                    
            elif sync_strategy == "latest":
                # 最新同步：使用最新更新的线程状态
                latest_thread = max(threads, key=lambda t: t.updated_at)
                latest_state = latest_thread.state.copy()
                
                # 更新其他线程
                for thread in threads:
                    if thread.id != latest_thread.id:
                        thread.state.update(latest_state)
                        thread.update_timestamp()
                        await self._thread_repository.update(thread)
                        
            elif sync_strategy == "master":
                # 主从同步：使用第一个线程作为主线程
                master_thread = threads[0]
                master_state = master_thread.state.copy()
                
                # 更新从线程
                for thread in threads[1:]:
                    thread.state.update(master_state)
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
            else:
                raise ValidationError(f"Unsupported sync strategy: {sync_strategy}")
            
            # 记录同步历史
            if self._history_manager:
                try:
                    await self._record_state_sync(thread_ids, sync_strategy)
                except Exception as e:
                    logger.warning(f"Failed to record state sync: {e}")
            
            logger.info(f"Synchronized states for threads {thread_ids} using strategy {sync_strategy}")
            return True
            
        except Exception as e:
            raise ValidationError(f"Failed to sync thread states: {str(e)}")
    
    async def get_thread_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取Thread历史记录
        
        Args:
            thread_id: Thread ID
            limit: 记录数量限制
            
        Returns:
            历史记录列表
        """
        try:
            if not self._history_manager:
                # 如果没有历史管理器，返回基本历史
                thread = await self._thread_repository.get(thread_id)
                if not thread:
                    return []
                
                return [{
                    "thread_id": thread_id,
                    "event_type": "thread_created",
                    "timestamp": thread.created_at.isoformat(),
                    "data": {
                        "status": thread.status.value,
                        "type": thread.type.value
                    }
                }]
            
            # TODO: 从历史管理器获取详细历史
            # 目前返回模拟历史
            return [{
                "thread_id": thread_id,
                "event_type": "state_update",
                "timestamp": datetime.now().isoformat(),
                "data": {"message": "Thread state updated"}
            }]
            
        except Exception as e:
            raise ValidationError(f"Failed to get thread history: {str(e)}")
    
    # === 私有方法 ===
    
    async def _get_checkpoint_state(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取检查点状态
        """
        # 优先使用新的Thread checkpoint管理器
        if self._thread_checkpoint_manager:
            try:
                checkpoint = await self._thread_checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
                if checkpoint:
                    return checkpoint.state_data
                return None
            except Exception:
                return None
        
        # 回退到旧的checkpoint管理器
        if self._checkpoint_manager:
            try:
                checkpoint_data = await self._checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
                if checkpoint_data:
                    # 从checkpoint数据中提取状态
                    return checkpoint_data.get("state_data", {})
                return None
            except Exception:
                return None
        
        return None
    
    def _apply_permissions(self, state: Dict[str, Any], permissions: Dict[str, Any]) -> Dict[str, Any]:
        """应用权限过滤
        
        Args:
            state: 原始状态
            permissions: 权限配置
            
        Returns:
            过滤后的状态
        """
        filtered_state = state.copy()
        
        # 只读字段
        read_only = permissions.get("read_only", [])
        for field in read_only:
            filtered_state.pop(field, None)
        
        # 允许的字段
        allowed = permissions.get("allowed_fields")
        if allowed:
            filtered_state = {k: v for k, v in filtered_state.items() if k in allowed}
        
        return filtered_state
    
    async def _record_state_change(self, thread_id: str, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """记录状态变更"""
        if not self._history_manager:
            return
        
        # TODO: 实现状态变更记录
        pass
    
    async def _record_rollback(self, thread_id: str, checkpoint_id: str) -> None:
        """记录回滚操作"""
        if not self._history_manager:
            return
        
        # TODO: 实现回滚记录
        pass
    
    async def _record_state_share(self, source_id: str, target_id: str, checkpoint_id: str) -> None:
        """记录状态共享"""
        if not self._history_manager:
            return
        
        # TODO: 实现状态共享记录
        pass
    
    async def _record_session_creation(self, session_id: str, thread_ids: List[str], config: Dict[str, Any]) -> None:
        """记录会话创建"""
        if not self._history_manager:
            return
        
        # TODO: 实现会话创建记录
        pass
    
    async def _record_state_sync(self, thread_ids: List[str], strategy: str) -> None:
        """记录状态同步"""
        if not self._history_manager:
            return
        
        # TODO: 实现状态同步记录
        pass