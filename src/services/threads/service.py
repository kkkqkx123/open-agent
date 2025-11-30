"""线程管理服务实现 - 主服务门面"""

from typing import AsyncGenerator, Dict, Any, Optional, List, Coroutine, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from interfaces.state import IWorkflowState as WorkflowState  # type: ignore[import-untyped]
    from interfaces.state.workflow import IWorkflowState  # type: ignore[import-untyped]
else:
    IWorkflowState = Any  # type: ignore[assignment]
from src.interfaces.threads.service import IThreadService
from src.interfaces.sessions.service import ISessionService
from src.core.threads.interfaces import IThreadCore
from src.interfaces.threads.storage import IThreadRepository
from src.interfaces.history import IHistoryManager

from .basic_service import BasicThreadService
from .workflow_service import WorkflowThreadService
from .collaboration_service import ThreadCollaborationService
from .branch_service import ThreadBranchService
from .snapshot_service import ThreadSnapshotService

from src.core.common.exceptions import ValidationError


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
        session_service: Optional[ISessionService] = None,
        history_manager: Optional[IHistoryManager] = None
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
            session_service: 会话服务（可选）
            history_manager: 历史管理器（可选）
        """
        self._thread_core = thread_core
        self._thread_repository = thread_repository
        self._basic_service = basic_service
        self._workflow_service = workflow_service
        self._collaboration_service = collaboration_service
        self._branch_service = branch_service
        self._snapshot_service = snapshot_service
        self._session_service = session_service
        self._history_manager = history_manager
    
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
        return await self._basic_service.get_thread_state(thread_id)
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态"""
        return await self._basic_service.update_thread_state(thread_id, state)
    
    async def rollback_thread(self, thread_id: str, checkpoint_id: str) -> bool:
        """回滚Thread到指定检查点"""
        return await self._basic_service.rollback_thread(thread_id, checkpoint_id)
    
    async def share_thread_state(self, source_thread_id: str, target_thread_id: str, checkpoint_id: str, permissions: Optional[Dict[str, Any]] = None) -> bool:
        """共享Thread状态到其他Thread"""
        # 简化实现：复制状态从源线程到目标线程
        try:
            source_state = await self._basic_service.get_thread_state(source_thread_id)
            if not source_state:
                return False
            
            state_to_share = source_state.get("state", {})
            return await self._basic_service.update_thread_state(target_thread_id, state_to_share)
        except Exception:
            return False
    
    async def create_shared_session(self, thread_ids: List[str], session_config: Dict[str, Any]) -> str:
        """创建共享会话"""
        # 简化实现：生成共享会话ID
        try:
            import uuid
            shared_session_id = str(uuid.uuid4())
            
            # 将会话ID记录到线程的自定义数据中（ThreadMetadata支持extra="allow"）
            for thread_id in thread_ids:
                thread = await self._thread_repository.get(thread_id)
                if thread:
                    # 使用ThreadMetadata的custom_data字段来存储共享会话
                    if 'shared_sessions' not in thread.metadata.custom_data:
                        thread.metadata.custom_data['shared_sessions'] = []
                    thread.metadata.custom_data['shared_sessions'].append(shared_session_id)
                    thread.update_timestamp()
                    await self._thread_repository.update(thread)
            
            return shared_session_id
        except Exception:
            raise ValidationError("Failed to create shared session")
    
    async def sync_thread_states(self, thread_ids: List[str], sync_strategy: str = "bidirectional") -> bool:
        """同步多个Thread状态"""
        try:
            if not thread_ids:
                return False
            
            # 简化实现：获取第一个线程的状态，同步到其他线程
            first_state = await self._basic_service.get_thread_state(thread_ids[0])
            if not first_state:
                return False
            
            state_to_sync = first_state.get("state", {})
            
            for thread_id in thread_ids[1:]:
                success = await self._basic_service.update_thread_state(thread_id, state_to_sync)
                if not success:
                    return False
            
            return True
        except Exception:
            return False
    
    async def get_thread_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取Thread历史记录
        
        注：当前实现为简化版本，完整实现需要：
        1. 在Thread实体中添加历史记录ID关联
        2. 在IHistoryManager中添加按thread_id查询的支持
        3. 或实现专门的ThreadHistoryService
        """
        try:
            # 目前暂时返回空列表，表示需要与history_manager集成
            # TODO: 完整实现需要添加对thread_id的历史查询支持
            if self._history_manager:
                # 当history_manager支持thread_id查询时，应该这样实现：
                # from src.core.history.entities import HistoryQuery
                # query = HistoryQuery(
                #     session_id=None,  # 如果Thread关联了session_id
                #     limit=limit or 100
                # )
                # result = await self._history_manager.query_history(query)
                # return [record.dict() for record in result.records]
                pass
            return []
        except Exception:
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
        """合并分支到目标Thread"""
        # 这里需要从source_thread_id获取branch_id
        # 简化处理，假设source_thread_id就是branch_id
        return await self._branch_service.merge_branch_to_main(
            target_thread_id, source_thread_id, merge_strategy
        )
    
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
        """删除快照"""
        # ThreadSnapshotService没有直接的delete方法，需要实现
        # 暂时返回False
        return False
    
    # === 委托给基础服务的fork方法 ===
    
    async def fork_thread(self, source_thread_id: str, checkpoint_id: str, branch_name: str) -> str:
        """创建线程分支"""
        return await self._branch_service.create_branch_from_checkpoint(
            source_thread_id, checkpoint_id, branch_name
        )