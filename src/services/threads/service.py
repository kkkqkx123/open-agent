"""线程管理服务实现"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.threads.interfaces import IThreadCore
from src.core.threads.entities import ThreadStatus
from src.interfaces.threads import IThreadService, IThreadRepository
from src.interfaces.sessions import ISessionService
from src.core.common.exceptions import EntityNotFoundError, ValidationError


class ThreadService(IThreadService):
    """线程业务服务实现"""
    
    def __init__(
        self,
        thread_core: IThreadCore,
        thread_repository: IThreadRepository,
        session_service: Optional[ISessionService] = None
    ):
        self._thread_core = thread_core
        self._thread_repository = thread_repository
        self._session_service = session_service
    
    async def create_thread_with_session(
        self,
        thread_config: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """创建线程并关联会话"""
        try:
            # 验证会话存在性
            if session_id and self._session_service:
                session = await self._session_service.get_session_summary(session_id)
                if not session:
                    raise EntityNotFoundError(f"Session {session_id} not found")
            
            # 创建线程实体
            thread_id = await self._thread_core.create_thread(thread_config)
            
            # 关联会话（如果提供）
            if session_id:
                await self._thread_repository.associate_with_session(thread_id, session_id)
            
            return thread_id
        except Exception as e:
            raise ValidationError(f"Failed to create thread with session: {str(e)}")
    
    async def fork_thread_from_checkpoint(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建thread分支"""
        try:
            # 验证源线程存在
            source_thread = await self._thread_repository.get_thread(source_thread_id)
            if not source_thread:
                raise EntityNotFoundError(f"Source thread {source_thread_id} not found")
            
            # 验证检查点存在（这里假设检查点服务会验证）
            # 创建分支配置
            branch_config = {
                "parent_thread_id": source_thread_id,
                "checkpoint_id": checkpoint_id,
                "branch_name": branch_name,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat()
            }
            
            # 创建分支线程
            branch_thread_id = await self._thread_core.create_thread(branch_config)
            
            # 更新源线程的分支计数
            await self.increment_branch_count(source_thread_id)
            
            return branch_thread_id
        except Exception as e:
            raise ValidationError(f"Failed to fork thread from checkpoint: {str(e)}")
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新线程元数据"""
        try:
            # 验证线程存在
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 更新元数据
            thread.metadata.update(metadata)
            thread.updated_at = datetime.now()
            
            # 保存更新
            success = await self._thread_repository.update_thread(thread_id, thread)
            return success
        except Exception as e:
            raise ValidationError(f"Failed to update thread metadata: {str(e)}")
    
    async def increment_message_count(self, thread_id: str) -> int:
        """增加消息计数"""
        try:
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            thread.message_count += 1
            thread.updated_at = datetime.now()
            
            await self._thread_repository.update_thread(thread_id, thread)
            return thread.message_count
        except Exception as e:
            raise ValidationError(f"Failed to increment message count: {str(e)}")
    
    async def increment_checkpoint_count(self, thread_id: str) -> int:
        """增加检查点计数"""
        try:
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            thread.checkpoint_count += 1
            thread.updated_at = datetime.now()
            
            await self._thread_repository.update_thread(thread_id, thread)
            return thread.checkpoint_count
        except Exception as e:
            raise ValidationError(f"Failed to increment checkpoint count: {str(e)}")
    
    async def increment_branch_count(self, thread_id: str) -> int:
        """增加分支计数"""
        try:
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            thread.branch_count += 1
            thread.updated_at = datetime.now()
            
            await self._thread_repository.update_thread(thread_id, thread)
            return thread.branch_count
        except Exception as e:
            raise ValidationError(f"Failed to increment branch count: {str(e)}")
    
    async def get_thread_summary(self, thread_id: str) -> Dict[str, Any]:
        """获取线程摘要信息"""
        try:
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            return {
                "thread_id": thread.thread_id,
                "status": thread.status.value,
                "message_count": thread.message_count,
                "checkpoint_count": thread.checkpoint_count,
                "branch_count": thread.branch_count,
                "created_at": thread.created_at.isoformat(),
                "updated_at": thread.updated_at.isoformat(),
                "metadata": thread.metadata,
                "tags": thread.tags
            }
        except Exception as e:
            raise ValidationError(f"Failed to get thread summary: {str(e)}")
    
    async def list_threads_by_type(self, thread_type: str) -> List[Dict[str, Any]]:
        """按类型列线程"""
        try:
            threads = await self._thread_repository.list_threads_by_type(thread_type)
            return [
                {
                    "thread_id": thread.thread_id,
                    "status": thread.status.value,
                    "message_count": thread.message_count,
                    "created_at": thread.created_at.isoformat(),
                    "updated_at": thread.updated_at.isoformat()
                }
                for thread in threads
            ]
        except Exception as e:
            raise ValidationError(f"Failed to list threads by type: {str(e)}")
    
    async def validate_thread_state(self, thread_id: str) -> bool:
        """验证Thread状态"""
        try:
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                return False
            
            # 基本状态验证
            if thread.status not in ThreadStatus:
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
    
    async def can_transition_to_status(self, thread_id: str, new_status: str) -> bool:
        """检查是否可以转换到指定状态"""
        try:
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                return False
            
            current_status = thread.status
            
            # 定义状态转换规则
            valid_transitions = {
                ThreadStatus.PENDING: [ThreadStatus.ACTIVE, ThreadStatus.FAILED],
                ThreadStatus.ACTIVE: [ThreadStatus.PAUSED, ThreadStatus.COMPLETED, ThreadStatus.FAILED],
                ThreadStatus.PAUSED: [ThreadStatus.ACTIVE, ThreadStatus.COMPLETED, ThreadStatus.FAILED],
                ThreadStatus.COMPLETED: [ThreadStatus.ACTIVE],  # 允许重新激活
                ThreadStatus.FAILED: [ThreadStatus.ACTIVE, ThreadStatus.PENDING]
            }
            
            try:
                target_status = ThreadStatus(new_status)
            except ValueError:
                return False
            
            return target_status in valid_transitions.get(current_status, [])
        except Exception:
            return False