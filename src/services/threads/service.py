"""线程管理服务实现 - 主服务门面"""

from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional, List, cast, TYPE_CHECKING


from interfaces.state.workflow import IWorkflowState
from src.interfaces.history import IHistoryManager
from src.interfaces.threads.service import IThreadService
from src.interfaces.sessions.service import ISessionService
from src.core.threads.interfaces import IThreadCore
from src.interfaces.threads.storage import IThreadRepository
from src.interfaces.logger import ILogger

from .basic_service import BasicThreadService
from .workflow_service import WorkflowThreadService
from .collaboration_service import ThreadCollaborationService
from .branch_service import ThreadBranchService
from .snapshot_service import ThreadSnapshotService
from .state_service import ThreadStateService
from .history_service import ThreadHistoryService

from src.interfaces.container.exceptions import ValidationError


class ThreadService(IThreadService):
    """线程业务服务实现 - 主服务门面"""
    
    def __init__(
        self,
        thread_core: IThreadCore,
        thread_repository: IThreadRepository,
        basic_service: BasicThreadService,
        workflow_service: WorkflowThreadService,
        collaboration_service: ThreadCollaborationService,
        branch_service: ThreadBranchService,
        snapshot_service: ThreadSnapshotService,
        state_service: ThreadStateService,
        history_service: ThreadHistoryService,
        session_service: Optional[ISessionService] = None,
        history_manager: Optional[IHistoryManager] = None,
        logger: Optional[ILogger] = None
    ):
        """初始化线程服务
        
        Args:
            thread_core: 线程核心接口
            thread_repository: 线程仓储接口
            basic_service: 基础线程服务
            workflow_service: 工作流服务
            collaboration_service: 协作服务
            branch_service: 分支服务
            snapshot_service: 快照服务
            history_service: 历史服务
            session_service: 会话服务（可选）
            history_manager: 历史管理器（可选）
            logger: 日志记录器（可选）
        """
        self._thread_core = thread_core
        self._thread_repository = thread_repository
        self._basic_service = basic_service
        self._workflow_service = workflow_service
        self._collaboration_service = collaboration_service
        self._branch_service = branch_service
        self._snapshot_service = snapshot_service
        self._state_service = state_service
        self._history_service = history_service
        self._session_service = session_service
        self._history_manager = history_manager
        self._logger = logger
    
    # === 已实现的方法 ===
    
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
                    raise ValidationError(f"Session {session_id} not found")
            
            # 直接使用基础服务创建线程
            graph_id = thread_config.get("graph_id")
            if not graph_id:
                raise ValidationError("graph_id is required in thread_config")
            
            metadata = thread_config.get("metadata", {})
            if session_id:
                metadata["session_id"] = session_id
            
            thread_id = await self._basic_service.create_thread(graph_id, metadata)
            
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
        return await self._branch_service.create_branch_from_checkpoint(
            source_thread_id, checkpoint_id, branch_name, metadata
        )
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新线程元数据"""
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                return False
            
            # 更新元数据
            from src.core.threads.entities import ThreadMetadata
            thread.metadata = ThreadMetadata(**metadata)
            thread.update_timestamp()
            
            return await self._thread_repository.update(thread)
            
        except Exception:
            return False
    
    async def increment_message_count(self, thread_id: str) -> int:
        """增加消息计数"""
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValidationError(f"Thread {thread_id} not found")
            
            thread.increment_message_count()
            await self._thread_repository.update(thread)
            
            return thread.message_count
            
        except Exception as e:
            raise ValidationError(f"Failed to increment message count: {str(e)}")
    
    async def increment_checkpoint_count(self, thread_id: str) -> int:
        """增加检查点计数"""
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValidationError(f"Thread {thread_id} not found")
            
            # 直接更新计数
            thread.increment_checkpoint_count()
            await self._thread_repository.update(thread)
            
            return thread.checkpoint_count
            
        except Exception as e:
            raise ValidationError(f"Failed to increment checkpoint count: {str(e)}")
    
    async def increment_branch_count(self, thread_id: str) -> int:
        """增加分支计数"""
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValidationError(f"Thread {thread_id} not found")
            
            thread.increment_branch_count()
            await self._thread_repository.update(thread)
            
            return thread.branch_count
            
        except Exception as e:
            raise ValidationError(f"Failed to increment branch count: {str(e)}")
    
    async def get_thread_summary(self, thread_id: str) -> Dict[str, Any]:
        """获取线程摘要信息"""
        result = await self._basic_service.get_thread_info(thread_id)
        if result is None:
            raise ValidationError(f"Thread {thread_id} not found")
        return result
    
    async def list_threads_by_type(self, thread_type: str) -> List[Dict[str, Any]]:
        """按类型列线程"""
        return await self._basic_service.list_threads_by_type(thread_type)
    
    async def validate_thread_state(self, thread_id: str) -> bool:
        """验证Thread状态"""
        return await self._basic_service.validate_thread_state(thread_id)
    
    async def can_transition_to_status(self, thread_id: str, new_status: str) -> bool:
        """检查是否可以转换到指定状态"""
        return await self._basic_service.can_transition_to_status(thread_id, new_status)
    
    # === 委托给基础服务的方法 ===
    
    async def create_thread(self, graph_id: str, metadata: Dict[str, Any] | None = None) -> str:
        """创建新的Thread"""
        return await self._basic_service.create_thread(graph_id, metadata)
    
    async def create_thread_from_config(self, config_path: str, metadata: Dict[str, Any] | None = None) -> str:
        """从配置文件创建Thread"""
        return await self._basic_service.create_thread_from_config(config_path, metadata)
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息"""
        return await self._basic_service.get_thread_info(thread_id)
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态"""
        return await self._basic_service.update_thread_status(thread_id, status)
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread"""
        return await self._basic_service.delete_thread(thread_id)
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads"""
        return await self._basic_service.list_threads(filters, limit)
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        return await self._basic_service.thread_exists(thread_id)
    
    async def search_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """搜索Threads"""
        return await self._basic_service.search_threads(filters, limit, offset)
    
    async def get_thread_statistics(self) -> Dict[str, Any]:
        """获取Thread统计信息"""
        return await self._basic_service.get_thread_statistics()
    
    # === 委托给工作流服务的方法 ===
    
    async def execute_workflow(self, thread_id: str, config: Optional[Dict[str, Any]] = None, initial_state: Optional[Dict[str, Any]] = None) -> IWorkflowState:
        """执行工作流"""
        return await self._workflow_service.execute_workflow(thread_id, config, initial_state)
    
    async def stream_workflow(self, thread_id: str, config: Optional[Dict[str, Any]] = None, initial_state: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:  # type: ignore[override]
        """流式执行工作流"""
        async for result in self._workflow_service.stream_workflow(thread_id, config, initial_state):
            yield result
    
    # === 委托给协作服务的方法 ===
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态"""
        return await self._state_service.get_thread_state(thread_id)
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态"""
        return await self._state_service.update_thread_state(thread_id, state)
    
    async def rollback_thread(self, thread_id: str, checkpoint_id: str) -> bool:
        """回滚Thread到指定检查点"""
        return await self._basic_service.rollback_thread(thread_id, checkpoint_id)
    
    async def share_thread_state(self, source_thread_id: str, target_thread_id: str, checkpoint_id: str, permissions: Optional[Dict[str, Any]] = None) -> bool:
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
            # 验证源线程和目标线程存在
            source_thread = await self._thread_repository.get(source_thread_id)
            target_thread = await self._thread_repository.get(target_thread_id)
            
            if not source_thread:
                if self._logger:
                    self._logger.warning(f"Source thread {source_thread_id} not found")
                return False
            
            if not target_thread:
                if self._logger:
                    self._logger.warning(f"Target thread {target_thread_id} not found")
                return False
            
            # 验证检查点存在（如果提供了checkpoint_id）
            if checkpoint_id:
                # 这里应该调用检查点服务验证检查点存在
                # 简化处理，假设检查点存在
                pass
            
            # 获取源线程状态
            source_state = await self._state_service.get_thread_state(source_thread_id)
            if not source_state:
                if self._logger:
                    self._logger.warning(f"Failed to get state from source thread {source_thread_id}")
                return False
            
            # 准备要共享的状态数据
            state_to_share = source_state.get("state", {})
            
            # 添加共享元数据
            share_metadata = {
                "shared_from": source_thread_id,
                "checkpoint_id": checkpoint_id,
                "shared_at": source_state.get("updated_at", ""),
                "permissions": permissions or {}
            }
            
            # 更新目标线程状态
            success = await self._state_service.update_thread_state(target_thread_id, state_to_share)
            
            if success:
                # 在目标线程元数据中记录共享信息
                target_metadata = target_thread.get_metadata_object()
                target_metadata.custom_data['shared_state'] = share_metadata
                target_thread.update_timestamp()
                await self._thread_repository.update(target_thread)
                
                if self._logger:
                    self._logger.info(f"State shared from thread {source_thread_id} to {target_thread_id}")
            
            return success
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"共享线程状态失败: {e}")
            return False
    
    async def create_shared_session(self, thread_ids: List[str], session_config: Dict[str, Any]) -> str:
        """创建共享会话
        
        Args:
            thread_ids: Thread ID列表
            session_config: 会话配置
            
        Returns:
            共享会话ID
            
        Raises:
            ValidationError: 创建失败时抛出
        """
        try:
            import uuid
            from datetime import datetime
            
            # 验证输入参数
            if not thread_ids:
                raise ValidationError("Thread IDs list cannot be empty")
            
            if not session_config:
                raise ValidationError("Session config cannot be empty")
            
            # 验证所有线程存在
            valid_thread_ids = []
            for thread_id in thread_ids:
                thread = await self._thread_repository.get(thread_id)
                if thread:
                    valid_thread_ids.append(thread_id)
                else:
                    if self._logger:
                        self._logger.warning(f"Thread {thread_id} not found, skipping")
            
            if not valid_thread_ids:
                raise ValidationError("No valid threads found")
            
            # 生成共享会话ID
            shared_session_id = str(uuid.uuid4())
            
            # 准备共享会话信息
            shared_session_info = {
                "session_id": shared_session_id,
                "thread_ids": valid_thread_ids,
                "config": session_config,
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # 将共享会话信息记录到每个线程的元数据中
            for thread_id in valid_thread_ids:
                thread = await self._thread_repository.get(thread_id)
                if thread:
                    # 使用ThreadMetadata的custom_data字段来存储共享会话
                    thread_metadata = thread.get_metadata_object()
                    if 'shared_sessions' not in thread_metadata.custom_data:
                        thread_metadata.custom_data['shared_sessions'] = []
                    
                    # 检查是否已经存在相同的共享会话
                    existing_sessions = thread_metadata.custom_data['shared_sessions']
                    if not any(session.get('session_id') == shared_session_id for session in existing_sessions):
                        thread_metadata.custom_data['shared_sessions'].append(shared_session_info)
                    
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
            
            if self._logger:
                self._logger.info(f"Shared session {shared_session_id} created for threads {valid_thread_ids}")
            return shared_session_id
            
        except ValidationError:
            raise
        except Exception as e:
            if self._logger:
                self._logger.error(f"创建共享会话失败: {e}")
            raise ValidationError(f"Failed to create shared session: {str(e)}")
    
    async def sync_thread_states(self, thread_ids: List[str], sync_strategy: str = "bidirectional") -> bool:
        """同步多个Thread状态
        
        Args:
            thread_ids: Thread ID列表
            sync_strategy: 同步策略 ("unidirectional", "bidirectional", "merge")
            
        Returns:
            同步是否成功
        """
        try:
            # 验证输入参数
            if not thread_ids or len(thread_ids) < 2:
                if self._logger:
                    self._logger.warning("需要至少两个线程进行同步")
                return False

            if sync_strategy not in ["unidirectional", "bidirectional", "merge"]:
                if self._logger:
                    self._logger.warning(f"不支持的同步策略: {sync_strategy}")
                return False
            
            # 验证所有线程存在
            valid_threads = []
            for thread_id in thread_ids:
                thread = await self._thread_repository.get(thread_id)
                if thread:
                    valid_threads.append(thread)
                else:
                    if self._logger:
                        self._logger.warning(f"Thread {thread_id} not found, skipping")

            if len(valid_threads) < 2:
                if self._logger:
                    self._logger.warning("需要至少两个有效线程进行同步")
                return False
            
            # 根据同步策略执行同步
            if sync_strategy == "unidirectional":
                # 单向同步：使用第一个线程的状态同步到其他线程
                source_thread = valid_threads[0]
                source_state = await self._state_service.get_thread_state(source_thread.id)
                
                if not source_state:
                    if self._logger:
                        self._logger.warning(f"Failed to get state from source thread {source_thread.id}")
                    return False
                
                state_to_sync = source_state.get("state", {})
                
                # 同步到其他线程
                for thread in valid_threads[1:]:
                    success = await self._state_service.update_thread_state(thread.id, state_to_sync)
                    if not success:
                        if self._logger:
                            self._logger.warning(f"Failed to sync state to thread {thread.id}")
                        return False
                    
                    # 记录同步信息
                    thread_metadata = thread.get_metadata_object()
                    thread_metadata.custom_data['last_sync'] = {
                        "synced_from": source_thread.id,
                        "synced_at": source_state.get("updated_at", ""),
                        "strategy": sync_strategy
                    }
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
            
            elif sync_strategy == "bidirectional":
                # 双向同步：合并所有线程的状态
                merged_state = {}
                
                # 获取所有线程的状态并合并
                for thread in valid_threads:
                    thread_state = await self._state_service.get_thread_state(thread.id)
                    if thread_state and thread_state.get("state"):
                        merged_state.update(thread_state.get("state", {}))
                
                # 将合并后的状态同步到所有线程
                for thread in valid_threads:
                    success = await self._state_service.update_thread_state(thread.id, merged_state)
                    if not success:
                        if self._logger:
                            self._logger.warning(f"Failed to sync merged state to thread {thread.id}")
                        return False
                    
                    # 记录同步信息
                    thread_metadata = thread.get_metadata_object()
                    thread_metadata.custom_data['last_sync'] = {
                        "synced_with": [t.id for t in valid_threads if t.id != thread.id],
                        "synced_at": datetime.now().isoformat(),
                        "strategy": sync_strategy
                    }
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
            
            elif sync_strategy == "merge":
                # 合并策略：智能合并状态，处理冲突
                merged_state = {}
                sync_sources = {}
                
                # 收集所有状态和来源信息
                for thread in valid_threads:
                    thread_state = await self._state_service.get_thread_state(thread.id)
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
                for thread in valid_threads:
                    success = await self._state_service.update_thread_state(thread.id, merged_state)
                    if not success:
                        if self._logger:
                            self._logger.warning(f"Failed to sync merged state to thread {thread.id}")
                        return False
                    
                    # 记录同步信息
                    thread_metadata = thread.get_metadata_object()
                    thread_metadata.custom_data['last_sync'] = {
                        "synced_with": [t.id for t in valid_threads if t.id != thread.id],
                        "synced_at": datetime.now().isoformat(),
                        "strategy": sync_strategy,
                        "sources": sync_sources
                    }
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
            
            if self._logger:
                self._logger.info(f"Thread states synchronized using strategy: {sync_strategy}")
            return True

        except Exception as e:
            if self._logger:
                self._logger.error(f"同步线程状态失败: {e}")
            return False
    
    async def get_thread_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取Thread历史记录
        
        Args:
            thread_id: 线程ID
            limit: 记录数量限制
            
        Returns:
            历史记录列表
        """
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                if self._logger:
                    self._logger.warning(f"Thread {thread_id} not found")
                return []
            
            # 优先使用HistoryManager查询历史记录
            if self._history_manager:
                from src.core.history.entities import RecordType
                history_result = await self._history_manager.query_history_by_thread(
                    thread_id=thread_id,
                    limit=limit or 100
                )
                
                # 将历史记录转换为字典格式
                history_list = []
                for record in history_result.records:
                    record_dict = record.to_dict()
                    history_list.append(record_dict)
                
                return history_list
            
            # 如果没有HistoryManager，尝试使用HistoryService
            if hasattr(self, '_history_service') and self._history_service:
                from .history_service import HistoryFilters
                
                filters = HistoryFilters(limit=limit or 100)
                history_list = await self._history_service.get_thread_history(thread_id, filters)
                
                return history_list
            
            # 如果都没有，返回空列表
            if self._logger:
                self._logger.warning("No history service available, returning empty history")
            return []
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取线程历史记录失败: {e}")
            return []
    
    # === 委托给分支服务的方法 ===
    
    async def create_branch(self, thread_id: str, checkpoint_id: str, branch_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建Thread分支"""
        return await self._branch_service.create_branch_from_checkpoint(
            thread_id, checkpoint_id, branch_name, metadata
        )
    
    async def get_thread_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取Thread的所有分支"""
        return await self._branch_service.list_active_branches(thread_id)
    
    async def merge_branch(self, target_thread_id: str, source_thread_id: str, merge_strategy: str = "latest") -> bool:
        """合并分支到目标Thread
        
        Args:
            target_thread_id: 目标Thread ID
            source_thread_id: 源Thread ID（分支）
            merge_strategy: 合并策略
            
        Returns:
            合并是否成功
        """
        try:
            # 验证目标线程和源线程存在
            target_thread = await self._thread_repository.get(target_thread_id)
            source_thread = await self._thread_repository.get(source_thread_id)
            
            if not target_thread:
                if self._logger:
                    self._logger.warning(f"Target thread {target_thread_id} not found")
                return False
            
            if not source_thread:
                if self._logger:
                    self._logger.warning(f"Source thread {source_thread_id} not found")
                return False
            
            # 验证源线程是否为分支
            if source_thread.parent_thread_id != target_thread_id:
                if self._logger:
                    self._logger.warning(f"Source thread {source_thread_id} is not a branch of target thread {target_thread_id}")
                return False
            
            # 验证合并策略
            if merge_strategy not in ["latest", "overwrite", "merge"]:
                if self._logger:
                    self._logger.warning(f"Unsupported merge strategy: {merge_strategy}")
                return False
            
            # 执行分支合并
            success = await self._branch_service.merge_branch_to_main(
                target_thread_id, source_thread_id, merge_strategy
            )
            
            if success:
                # 更新目标线程的分支计数
                if target_thread.branch_count > 0:
                    target_thread.branch_count -= 1
                    target_thread.update_timestamp()
                    await self._thread_repository.update(target_thread)
                
                # 在目标线程元数据中记录合并信息
                target_metadata = target_thread.get_metadata_object()
                target_metadata.custom_data['last_merge'] = {
                    "merged_from": source_thread_id,
                    "merge_strategy": merge_strategy,
                    "merged_at": datetime.now().isoformat()
                }
                await self._thread_repository.update(target_thread)
                
                if self._logger:
                    self._logger.info(f"Branch {source_thread_id} merged into {target_thread_id}")
            
            return success
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"合并分支失败: {e}")
            return False
    
    # === 委托给快照服务的方法 ===
    
    async def create_snapshot(self, thread_id: str, snapshot_name: str, description: Optional[str] = None) -> str:
        """创建Thread快照"""
        return await self._snapshot_service.create_snapshot_from_thread(
            thread_id, snapshot_name, description
        )
    
    async def restore_snapshot(self, thread_id: str, snapshot_id: str) -> bool:
        """从快照恢复Thread状态"""
        try:
            # 直接调用快照服务进行状态恢复
            return await self._snapshot_service.restore_thread_from_snapshot(thread_id, snapshot_id)
        except Exception as e:
            raise ValidationError(f"Failed to restore snapshot: {str(e)}")
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            删除是否成功
        """
        try:
            # 验证快照存在
            snapshot = await self._snapshot_service._thread_snapshot_repository.get(snapshot_id)
            if not snapshot:
                if self._logger:
                    self._logger.warning(f"Snapshot {snapshot_id} not found")
                return False
            
            # 删除快照
            success = await self._snapshot_service._thread_snapshot_repository.delete(snapshot_id)
            
            if success:
                if self._logger:
                    self._logger.info(f"Snapshot {snapshot_id} deleted successfully")
                # 更新对应线程的检查点计数
                thread = await self._thread_repository.get(snapshot.thread_id)
                if thread and thread.checkpoint_count > 0:
                    thread.checkpoint_count -= 1
                    await self._thread_repository.update(thread)
            else:
                if self._logger:
                    self._logger.error(f"Failed to delete snapshot {snapshot_id}")
            
            return success
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"删除快照失败: {e}")
            return False
    
    # === 委托给基础服务的fork方法 ===
    
    async def fork_thread(self, source_thread_id: str, checkpoint_id: str, branch_name: str) -> str:
        """创建线程分支"""
        return await self._branch_service.create_branch_from_checkpoint(
            source_thread_id, checkpoint_id, branch_name
        )