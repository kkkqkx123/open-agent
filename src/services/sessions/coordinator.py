"""Session-Thread协调器实现"""

from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from datetime import datetime

from src.interfaces.sessions.association import (
    ISessionThreadAssociationRepository,
    ISessionThreadSynchronizer,
    ISessionThreadTransaction
)
from src.interfaces.sessions.service import ISessionService
from src.interfaces.threads.service import IThreadService
from src.interfaces.logger import ILogger
from src.core.sessions.entities import UserInteractionEntity
from src.interfaces.container.exceptions import ValidationError
from src.interfaces.storage.exceptions import StorageError


class SessionThreadCoordinator:
    """Session-Thread协调器 - 负责Session层面的Thread协调管理"""
    
    def __init__(
        self,
        session_service: ISessionService,
        thread_service: IThreadService,
        association_repository: ISessionThreadAssociationRepository,
        synchronizer: ISessionThreadSynchronizer,
        transaction: ISessionThreadTransaction,
        logger: Optional[ILogger] = None
    ):
        """初始化协调器
        
        Args:
            session_service: 会话服务
            thread_service: 线程服务
            association_repository: 关联仓储
            synchronizer: 同步器
            transaction: 事务管理器
            logger: 日志记录器
        """
        self._session_service = session_service
        self._thread_service = thread_service
        self._association_repository = association_repository
        self._synchronizer = synchronizer
        self._transaction = transaction
        self._logger = logger
        if self._logger:
            self._logger.info("SessionThreadCoordinator initialized")
    
    async def coordinate_threads(
        self, 
        session_id: str, 
        thread_configs: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """协调Thread创建，保证数据一致性
        
        Args:
            session_id: 会话ID
            thread_configs: Thread配置列表
            
        Returns:
            Thread名称到Thread ID的映射
        """
        try:
            if self._logger:
                self._logger.info(f"Coordinating thread creation for session: {session_id}")
            
            # 1. 验证Session存在
            session_context = await self._session_service.get_session_context(session_id)
            if not session_context:
                raise ValidationError(f"Session not found: {session_id}")
            
            # 2. 验证Thread配置
            thread_names = [config.get("name") for config in thread_configs]
            if len(thread_names) != len(set(thread_names)):
                raise ValidationError("Duplicate thread names in configuration")
            
            # 3. 检查名称冲突
            existing_associations = await self._association_repository.list_by_session(session_id)
            existing_names = {assoc.thread_name for assoc in existing_associations if assoc.is_active}
            
            for thread_name in thread_names:
                if thread_name in existing_names:
                    raise ValidationError(f"Thread name '{thread_name}' already exists in session")
            
            # 4. 创建Thread
            thread_ids = {}
            created_threads = []
            
            try:
                for thread_config in thread_configs:
                    thread_name = thread_config["name"]
                    config = thread_config.get("config", {})
                    
                    # 使用事务创建Thread
                    thread_id = await self._transaction.create_thread_with_session(
                        session_id=session_id,
                        thread_config=config,
                        thread_name=thread_name
                    )
                    
                    thread_ids[thread_name] = thread_id
                    created_threads.append((thread_name, thread_id))
                    
                    # 追踪Thread创建交互
                    interaction = UserInteractionEntity(
                        interaction_id=f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(created_threads)}",
                        session_id=session_id,
                        thread_id=thread_id,
                        interaction_type="thread_created",
                        content=f"创建Thread: {thread_name}",
                        metadata={
                            "thread_name": thread_name,
                            "config_path": thread_config.get("config_path"),
                            "coordinated_by": "SessionThreadCoordinator"
                        },
                        timestamp=datetime.now()
                    )
                    await self._session_service.track_user_interaction(session_id, interaction)
                    
                    if self._logger:
                        self._logger.debug(f"Created thread {thread_name} with ID {thread_id}")

                if self._logger:
                    self._logger.info(f"Successfully coordinated creation of {len(thread_ids)} threads for session {session_id}")
                return thread_ids
                
            except Exception as e:
                # 清理已创建的Thread
                if self._logger:
                    self._logger.error(f"Failed to coordinate threads, cleaning up: {e}")
                await self._cleanup_created_threads(session_id, created_threads)
                raise
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"Thread coordination failed for session {session_id}: {e}")
            raise StorageError(f"Thread coordination failed: {e}")
    
    async def execute_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """在会话中执行工作流
        
        Args:
            session_id: 会话ID
            thread_name: Thread名称
            config: 执行配置
            
        Returns:
            工作流执行结果
        """
        try:
            if self._logger:
                self._logger.info(f"Executing workflow in session {session_id}, thread {thread_name}")
            
            # 1. 验证Session存在
            session_context = await self._session_service.get_session_context(session_id)
            if not session_context:
                raise ValidationError(f"Session not found: {session_id}")
            
            # 2. 查找Thread
            associations = await self._association_repository.list_by_session(session_id)
            target_association = None
            
            for association in associations:
                if association.is_active and association.thread_name == thread_name:
                    target_association = association
                    break
            
            if not target_association:
                raise ValidationError(f"Thread '{thread_name}' not found in session {session_id}")
            
            thread_id = target_association.thread_id
            
            # 3. 追踪执行开始交互
            start_interaction = UserInteractionEntity(
                interaction_id=f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_start",
                session_id=session_id,
                thread_id=thread_id,
                interaction_type="workflow_execution_start",
                content=f"开始执行工作流: {thread_name}",
                metadata={
                    "thread_name": thread_name,
                    "config": config,
                    "coordinated_by": "SessionThreadCoordinator"
                },
                timestamp=datetime.now()
            )
            await self._session_service.track_user_interaction(session_id, start_interaction)
            
            # 4. 执行工作流
            try:
                result = await self._thread_service.execute_workflow(thread_id, config)
                
                # 5. 追踪执行成功交互
                success_interaction = UserInteractionEntity(
                    interaction_id=f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_success",
                    session_id=session_id,
                    thread_id=thread_id,
                    interaction_type="workflow_execution_success",
                    content=f"工作流执行成功: {thread_name}",
                    metadata={
                        "thread_name": thread_name,
                        "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                        "coordinated_by": "SessionThreadCoordinator"
                    },
                    timestamp=datetime.now()
                )
                await self._session_service.track_user_interaction(session_id, success_interaction)
                
                if self._logger:
                    self._logger.info(f"Workflow execution completed successfully for thread {thread_name}")
                return result
                
            except Exception as e:
                # 6. 追踪执行错误交互
                error_interaction = UserInteractionEntity(
                    interaction_id=f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_error",
                    session_id=session_id,
                    thread_id=thread_id,
                    interaction_type="workflow_execution_error",
                    content=f"工作流执行失败: {thread_name}",
                    metadata={
                        "thread_name": thread_name,
                        "error": str(e),
                        "coordinated_by": "SessionThreadCoordinator"
                    },
                    timestamp=datetime.now()
                )
                await self._session_service.track_user_interaction(session_id, error_interaction)
                raise
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"Workflow execution failed for session {session_id}, thread {thread_name}: {e}")
            raise StorageError(f"Workflow execution failed: {e}")
    
    async def stream_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Callable:
        """在会话中流式执行工作流
        
        Args:
            session_id: 会话ID
            thread_name: Thread名称
            config: 执行配置
            
        Returns:
            返回异步生成器的可调用对象
        """
        async def _stream_impl() -> AsyncGenerator[Dict[str, Any], None]:
            try:
                if self._logger:
                    self._logger.info(f"Starting workflow stream in session {session_id}, thread {thread_name}")
                
                # 1. 验证Session存在
                session_context = await self._session_service.get_session_context(session_id)
                if not session_context:
                    raise ValidationError(f"Session not found: {session_id}")
                
                # 2. 查找Thread
                associations = await self._association_repository.list_by_session(session_id)
                target_association = None
                
                for association in associations:
                    if association.is_active and association.thread_name == thread_name:
                        target_association = association
                        break
                
                if not target_association:
                    raise ValidationError(f"Thread '{thread_name}' not found in session {session_id}")
                
                thread_id = target_association.thread_id
                
                # 3. 追踪流式执行开始交互
                start_interaction = UserInteractionEntity(
                    interaction_id=f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_stream_start",
                    session_id=session_id,
                    thread_id=thread_id,
                    interaction_type="workflow_stream_start",
                    content=f"开始流式执行工作流: {thread_name}",
                    metadata={
                        "thread_name": thread_name,
                        "config": config,
                        "coordinated_by": "SessionThreadCoordinator"
                    },
                    timestamp=datetime.now()
                )
                await self._session_service.track_user_interaction(session_id, start_interaction)
                
                # 4. 流式执行工作流
                try:
                    async for state in await self._thread_service.stream_workflow(thread_id, config):
                        yield state
                    
                    # 5. 追踪流式执行完成交互
                    completion_interaction = UserInteractionEntity(
                        interaction_id=f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_stream_complete",
                        session_id=session_id,
                        thread_id=thread_id,
                        interaction_type="workflow_stream_complete",
                        content=f"流式工作流执行完成: {thread_name}",
                        metadata={
                            "thread_name": thread_name,
                            "coordinated_by": "SessionThreadCoordinator"
                        },
                        timestamp=datetime.now()
                    )
                    await self._session_service.track_user_interaction(session_id, completion_interaction)
                    
                    if self._logger:
                        self._logger.info(f"Workflow stream completed successfully for thread {thread_name}")
                    
                except Exception as e:
                    # 6. 追踪流式执行错误交互
                    error_interaction = UserInteractionEntity(
                        interaction_id=f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_stream_error",
                        session_id=session_id,
                        thread_id=thread_id,
                        interaction_type="workflow_stream_error",
                        content=f"流式工作流执行失败: {thread_name}",
                        metadata={
                            "thread_name": thread_name,
                            "error": str(e),
                            "coordinated_by": "SessionThreadCoordinator"
                        },
                        timestamp=datetime.now()
                    )
                    await self._session_service.track_user_interaction(session_id, error_interaction)
                    raise
            
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Workflow stream failed for session {session_id}, thread {thread_name}: {e}")
                raise StorageError(f"Workflow stream failed: {e}")
        
        return _stream_impl
    
    async def sync_session_data(self, session_id: str) -> Dict[str, Any]:
        """同步Session数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            同步结果
        """
        try:
            if self._logger:
                self._logger.info(f"Syncing session data for: {session_id}")
            return await self._synchronizer.sync_session_threads(session_id)
        except Exception as e:
            if self._logger:
                self._logger.error(f"Session data sync failed for {session_id}: {e}")
            raise StorageError(f"Session data sync failed: {e}")
    
    async def validate_session_consistency(self, session_id: str) -> List[str]:
        """验证Session一致性
        
        Args:
            session_id: 会话ID
            
        Returns:
            发现的问题列表
        """
        try:
            if self._logger:
                self._logger.info(f"Validating session consistency for: {session_id}")
            return await self._synchronizer.validate_consistency(session_id)
        except Exception as e:
            if self._logger:
                self._logger.error(f"Session consistency validation failed for {session_id}: {e}")
            raise StorageError(f"Session consistency validation failed: {e}")
    
    async def repair_session_inconsistencies(self, session_id: str) -> Dict[str, Any]:
        """修复Session不一致问题
        
        Args:
            session_id: 会话ID
            
        Returns:
            修复结果
        """
        try:
            if self._logger:
                self._logger.info(f"Repairing session inconsistencies for: {session_id}")
            return await self._synchronizer.repair_inconsistencies(session_id)
        except Exception as e:
            if self._logger:
                self._logger.error(f"Session inconsistency repair failed for {session_id}: {e}")
            raise StorageError(f"Session inconsistency repair failed: {e}")
    
    async def remove_thread_from_session(
        self,
        session_id: str,
        thread_name: str
    ) -> bool:
        """从Session中移除Thread
        
        Args:
            session_id: 会话ID
            thread_name: Thread名称
            
        Returns:
            是否移除成功
        """
        try:
            if self._logger:
                self._logger.info(f"Removing thread {thread_name} from session {session_id}")
            
            # 1. 查找Thread
            associations = await self._association_repository.list_by_session(session_id)
            target_association = None
            
            for association in associations:
                if association.is_active and association.thread_name == thread_name:
                    target_association = association
                    break
            
            if not target_association:
                raise ValidationError(f"Thread '{thread_name}' not found in session {session_id}")
            
            thread_id = target_association.thread_id
            
            # 2. 使用事务移除Thread
            success = await self._transaction.remove_thread_from_session(session_id, thread_id)
            
            if success:
                # 3. 追踪移除交互
                interaction = UserInteractionEntity(
                    interaction_id=f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_remove",
                    session_id=session_id,
                    thread_id=thread_id,
                    interaction_type="thread_removed",
                    content=f"移除Thread: {thread_name}",
                    metadata={
                        "thread_name": thread_name,
                        "coordinated_by": "SessionThreadCoordinator"
                    },
                    timestamp=datetime.now()
                )
                await self._session_service.track_user_interaction(session_id, interaction)
                
                if self._logger:
                    self._logger.info(f"Successfully removed thread {thread_name} from session {session_id}")
            
            return success
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to remove thread {thread_name} from session {session_id}: {e}")
            raise StorageError(f"Thread removal failed: {e}")
    
    # === 私有辅助方法 ===
    
    async def _cleanup_created_threads(
        self,
        session_id: str,
        created_threads: List[tuple]
    ) -> None:
        """清理已创建的Thread
        
        Args:
            session_id: 会话ID
            created_threads: 已创建的Thread列表 [(thread_name, thread_id), ...]
        """
        if self._logger:
            self._logger.warning(f"Cleaning up {len(created_threads)} created threads")
        
        for thread_name, thread_id in created_threads:
            try:
                await self._transaction.remove_thread_from_session(session_id, thread_id)
                if self._logger:
                    self._logger.debug(f"Cleaned up thread {thread_name} ({thread_id})")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to cleanup thread {thread_name} ({thread_id}): {e}")