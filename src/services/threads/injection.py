"""Threads依赖注入便利层

使用通用依赖注入框架提供简洁的Threads服务获取方式。
"""

from typing import Optional, Dict, Any, List, AsyncGenerator, TYPE_CHECKING
from datetime import datetime

from src.interfaces.threads import IThreadRepository
from src.interfaces.threads.service import IThreadService
from src.services.threads.basic_service import BasicThreadService
from src.services.threads.workflow_service import WorkflowThreadService
from src.services.threads.collaboration_service import ThreadCollaborationService
from src.services.threads.branch_service import ThreadBranchService
from src.services.threads.snapshot_service import ThreadSnapshotService
from src.services.threads.state_service import ThreadStateService
from src.services.threads.history_service import ThreadHistoryService
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable

if TYPE_CHECKING:
    from src.core.threads.entities import Thread, ThreadStatus, ThreadType
    from src.interfaces.state.workflow import IWorkflowState as WorkflowState


class _StubWorkflowState:
    """临时 WorkflowState 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        self._messages: List[Any] = []
        self._fields: Dict[str, Any] = {}
        self._values: Dict[str, Any] = {}
        self._iteration_count = 0
        self._id = "stub_state_id"
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
        self._metadata: Dict[str, Any] = {}
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
    
    @property
    def messages(self) -> List[Any]:
        return self._messages
    
    @property
    def fields(self) -> Dict[str, Any]:
        return self._fields
    
    @property
    def values(self) -> Dict[str, Any]:
        return self._values
    
    @property
    def iteration_count(self) -> int:
        return self._iteration_count
    
    def get_field(self, key: str, default: Any = None) -> Any:
        return self._fields.get(key, default)
    
    def set_field(self, key: str, value: Any) -> '_StubWorkflowState':
        new_state = _StubWorkflowState()
        new_state._messages = self._messages.copy()
        new_state._fields = self._fields.copy()
        new_state._fields[key] = value
        new_state._values = self._values.copy()
        new_state._iteration_count = self._iteration_count
        return new_state
    
    def with_messages(self, messages: List[Any]) -> '_StubWorkflowState':
        new_state = _StubWorkflowState()
        new_state._messages = messages.copy()
        new_state._fields = self._fields.copy()
        new_state._values = self._values.copy()
        new_state._iteration_count = self._iteration_count
        return new_state
    
    def with_metadata(self, metadata: Dict[str, Any]) -> '_StubWorkflowState':
        new_state = _StubWorkflowState()
        new_state._messages = self._messages.copy()
        new_state._fields = self._fields.copy()
        new_state._values = self._values.copy()
        new_state._values.update(metadata)
        new_state._iteration_count = self._iteration_count
        return new_state
    
    def add_message(self, message: Any) -> None:
        self._messages.append(message)
    
    def get_messages(self) -> List[Any]:
        return self._messages.copy()
    
    def get_last_message(self) -> Any | None:
        return self._messages[-1] if self._messages else None
    
    def copy(self) -> '_StubWorkflowState':
        new_state = _StubWorkflowState()
        new_state._messages = self._messages.copy()
        new_state._fields = self._fields.copy()
        new_state._values = self._values.copy()
        new_state._iteration_count = self._iteration_count
        return new_state
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        self._values[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "metadata": self._metadata,
            "messages": self._messages,
            "fields": self._fields,
            "values": self._values,
            "iteration_count": self._iteration_count
        }


class _StubThreadRepository(IThreadRepository):
    """临时 ThreadRepository 实现（用于极端情况）"""
    
    async def create(self, thread: 'Thread') -> bool:
        """创建线程"""
        return False
    
    async def get(self, thread_id: str) -> Optional['Thread']:
        """获取线程"""
        return None
    
    async def update(self, thread: 'Thread') -> bool:
        """更新线程"""
        return False
    
    async def delete(self, thread_id: str) -> bool:
        """删除线程数据"""
        return False
    
    async def list_by_session(self, session_id: str) -> List['Thread']:
        """按会话列线程"""
        return []
    
    async def list_by_status(self, status: 'ThreadStatus') -> List['Thread']:
        """按状态列线程"""
        return []
    
    async def search(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List['Thread']:
        """搜索线程"""
        return []
    
    async def get_count_by_session(self, session_id: str) -> int:
        """获取会话的线程计数"""
        return 0
    
    async def cleanup_old(self, max_age_days: int = 30) -> int:
        """清理旧线程"""
        return 0
    
    async def exists(self, thread_id: str) -> bool:
        """检查线程是否存在"""
        return False
    
    async def list_by_type(self, thread_type: 'ThreadType') -> List['Thread']:
        """按类型列线程"""
        return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {}
    
    async def search_with_filters(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List['Thread']:
        """带过滤条件的搜索"""
        return []


class _StubThreadService(IThreadService):
    """临时 ThreadService 实现（用于极端情况）"""
    
    async def create_thread_with_session(
        self,
        thread_config: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """创建线程并关联会话"""
        return "stub_thread_id"
    
    async def fork_thread_from_checkpoint(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建thread分支"""
        return "stub_thread_id"
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新线程元数据"""
        return False
    
    async def increment_message_count(self, thread_id: str) -> int:
        """增加消息计数"""
        return 0
    
    async def increment_checkpoint_count(self, thread_id: str) -> int:
        """增加检查点计数"""
        return 0
    
    async def increment_branch_count(self, thread_id: str) -> int:
        """增加分支计数"""
        return 0
    
    async def get_thread_summary(self, thread_id: str) -> Dict[str, Any]:
        """获取线程摘要信息"""
        return {}
    
    async def list_threads_by_type(self, thread_type: str) -> List[Dict[str, Any]]:
        """按类型列线程"""
        return []
    
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新的Thread"""
        return "stub_thread_id"
    
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """从配置文件创建Thread"""
        return "stub_thread_id"
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息"""
        return None
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态"""
        return False
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread"""
        return False
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads"""
        return []
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        return False
    
    async def execute_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> 'WorkflowState':
        """执行工作流"""
        # 类型转换：将 _StubWorkflowState 转换为 WorkflowState 接口
        stub_state = _StubWorkflowState()
        return stub_state  # type: ignore
    
    async def stream_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        async def _generator() -> AsyncGenerator[Dict[str, Any], None]:
            yield {}
        return _generator()
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态"""
        return None
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态"""
        return False
    
    async def create_branch(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建Thread分支"""
        return "stub_branch_id"
    
    async def get_thread_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取Thread的所有分支"""
        return []
    
    async def merge_branch(
        self,
        target_thread_id: str,
        source_thread_id: str,
        merge_strategy: str = "latest"
    ) -> bool:
        """合并分支到目标Thread"""
        return False
    
    async def create_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建Thread快照"""
        return "stub_snapshot_id"
    
    async def restore_snapshot(
        self,
        thread_id: str,
        snapshot_id: str
    ) -> bool:
        """从快照恢复Thread状态"""
        return False
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        return False
    
    async def rollback_thread(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        """回滚Thread到指定检查点"""
        return False
    
    async def search_threads(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """搜索Threads"""
        return []
    
    async def get_thread_statistics(self) -> Dict[str, Any]:
        """获取Thread统计信息"""
        return {}
    
    async def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取Thread历史记录"""
        return []
    
    async def share_thread_state(
        self,
        source_thread_id: str,
        target_thread_id: str,
        checkpoint_id: str,
        permissions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """共享Thread状态到其他Thread"""
        return False
    
    async def create_shared_session(
        self,
        thread_ids: List[str],
        session_config: Dict[str, Any]
    ) -> str:
        """创建共享会话"""
        return "stub_session_id"
    
    async def sync_thread_states(
        self,
        thread_ids: List[str],
        sync_strategy: str = "bidirectional"
    ) -> bool:
        """同步多个Thread状态"""
        return False
    
    async def validate_thread_state(self, thread_id: str) -> bool:
        """验证Thread状态"""
        return False
    
    async def can_transition_to_status(self, thread_id: str, new_status: str) -> bool:
        """检查是否可以转换到指定状态"""
        return False


class _StubBasicThreadService(BasicThreadService):
    """临时 BasicThreadService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def create_basic_thread(self, thread_data: dict) -> str:
        """创建基础线程"""
        return "stub_thread_id"
    
    def get_basic_thread(self, thread_id: str) -> Optional[dict]:
        """获取基础线程"""
        return None


class _StubWorkflowThreadService(WorkflowThreadService):
    """临时 WorkflowThreadService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def create_workflow_thread(self, workflow_data: dict) -> str:
        """创建工作流线程"""
        return "stub_thread_id"
    
    def get_workflow_thread(self, thread_id: str) -> Optional[dict]:
        """获取工作流线程"""
        return None


class _StubThreadCollaborationService(ThreadCollaborationService):
    """临时 ThreadCollaborationService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def add_collaborator(self, thread_id: str, user_id: str) -> bool:
        """添加协作者"""
        return True
    
    def remove_collaborator(self, thread_id: str, user_id: str) -> bool:
        """移除协作者"""
        return True


class _StubThreadBranchService(ThreadBranchService):
    """临时 ThreadBranchService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def create_branch(self, thread_id: str, branch_data: dict) -> str:
        """创建分支"""
        return "stub_branch_id"
    
    def get_branch(self, branch_id: str) -> Optional[dict]:
        """获取分支"""
        return None


class _StubThreadSnapshotService(ThreadSnapshotService):
    """临时 ThreadSnapshotService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def create_snapshot(self, thread_id: str, snapshot_data: dict) -> str:
        """创建快照"""
        return "stub_snapshot_id"
    
    def get_snapshot(self, snapshot_id: str) -> Optional[dict]:
        """获取快照"""
        return None


class _StubThreadStateService(ThreadStateService):
    """临时 ThreadStateService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def update_state(self, thread_id: str, state_data: dict) -> bool:
        """更新状态"""
        return True
    
    def get_state(self, thread_id: str) -> Optional[dict]:
        """获取状态"""
        return None


class _StubThreadHistoryService(ThreadHistoryService):
    """临时 ThreadHistoryService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def add_history_entry(self, thread_id: str, entry_data: dict) -> str:
        """添加历史条目"""
        return "stub_entry_id"
    
    def get_history(self, thread_id: str) -> list:
        """获取历史"""
        return []


def _create_fallback_thread_repository() -> IThreadRepository:
    """创建fallback thread repository"""
    return _StubThreadRepository()


def _create_fallback_thread_service() -> IThreadService:
    """创建fallback thread service"""
    return _StubThreadService()


def _create_fallback_basic_thread_service() -> BasicThreadService:
    """创建fallback basic thread service"""
    return _StubBasicThreadService()


def _create_fallback_workflow_thread_service() -> WorkflowThreadService:
    """创建fallback workflow thread service"""
    return _StubWorkflowThreadService()


def _create_fallback_collaboration_thread_service() -> ThreadCollaborationService:
    """创建fallback collaboration thread service"""
    return _StubThreadCollaborationService()


def _create_fallback_branch_thread_service() -> ThreadBranchService:
    """创建fallback branch thread service"""
    return _StubThreadBranchService()


def _create_fallback_snapshot_thread_service() -> ThreadSnapshotService:
    """创建fallback snapshot thread service"""
    return _StubThreadSnapshotService()


def _create_fallback_state_thread_service() -> ThreadStateService:
    """创建fallback state thread service"""
    return _StubThreadStateService()


def _create_fallback_history_thread_service() -> ThreadHistoryService:
    """创建fallback history thread service"""
    return _StubThreadHistoryService()


# 注册Threads注入
_thread_repository_injection = get_global_injection_registry().register(
    IThreadRepository, _create_fallback_thread_repository  # type: ignore
)
_thread_service_injection = get_global_injection_registry().register(
    IThreadService, _create_fallback_thread_service  # type: ignore
)
_basic_thread_service_injection = get_global_injection_registry().register(
    BasicThreadService, _create_fallback_basic_thread_service
)
_workflow_thread_service_injection = get_global_injection_registry().register(
    WorkflowThreadService, _create_fallback_workflow_thread_service
)
_collaboration_thread_service_injection = get_global_injection_registry().register(
    ThreadCollaborationService, _create_fallback_collaboration_thread_service
)
_branch_thread_service_injection = get_global_injection_registry().register(
    ThreadBranchService, _create_fallback_branch_thread_service
)
_snapshot_thread_service_injection = get_global_injection_registry().register(
    ThreadSnapshotService, _create_fallback_snapshot_thread_service
)
_state_thread_service_injection = get_global_injection_registry().register(
    ThreadStateService, _create_fallback_state_thread_service
)
_history_thread_service_injection = get_global_injection_registry().register(
    ThreadHistoryService, _create_fallback_history_thread_service
)


@injectable(IThreadRepository, _create_fallback_thread_repository)  # type: ignore
def get_thread_repository() -> IThreadRepository:
    """获取Thread仓储实例
    
    Returns:
        IThreadRepository: Thread仓储实例
    """
    return _thread_repository_injection.get_instance()


@injectable(IThreadService, _create_fallback_thread_service)  # type: ignore
def get_thread_service() -> IThreadService:
    """获取Thread服务实例
    
    Returns:
        IThreadService: Thread服务实例
    """
    return _thread_service_injection.get_instance()


@injectable(BasicThreadService, _create_fallback_basic_thread_service)  # type: ignore
def get_basic_thread_service() -> BasicThreadService:
    """获取基础Thread服务实例
    
    Returns:
        BasicThreadService: 基础Thread服务实例
    """
    return _basic_thread_service_injection.get_instance()


@injectable(WorkflowThreadService, _create_fallback_workflow_thread_service)  # type: ignore
def get_workflow_thread_service() -> WorkflowThreadService:
    """获取工作流Thread服务实例
    
    Returns:
        WorkflowThreadService: 工作流Thread服务实例
    """
    return _workflow_thread_service_injection.get_instance()


@injectable(ThreadCollaborationService, _create_fallback_collaboration_thread_service)  # type: ignore
def get_collaboration_thread_service() -> ThreadCollaborationService:
    """获取协作Thread服务实例
    
    Returns:
        ThreadCollaborationService: 协作Thread服务实例
    """
    return _collaboration_thread_service_injection.get_instance()


@injectable(ThreadBranchService, _create_fallback_branch_thread_service)  # type: ignore
def get_branch_thread_service() -> ThreadBranchService:
    """获取分支Thread服务实例
    
    Returns:
        ThreadBranchService: 分支Thread服务实例
    """
    return _branch_thread_service_injection.get_instance()


@injectable(ThreadSnapshotService, _create_fallback_snapshot_thread_service)  # type: ignore
def get_snapshot_thread_service() -> ThreadSnapshotService:
    """获取快照Thread服务实例
    
    Returns:
        ThreadSnapshotService: 快照Thread服务实例
    """
    return _snapshot_thread_service_injection.get_instance()


@injectable(ThreadStateService, _create_fallback_state_thread_service)  # type: ignore
def get_state_thread_service() -> ThreadStateService:
    """获取状态Thread服务实例
    
    Returns:
        ThreadStateService: 状态Thread服务实例
    """
    return _state_thread_service_injection.get_instance()


@injectable(ThreadHistoryService, _create_fallback_history_thread_service)  # type: ignore
def get_history_thread_service() -> ThreadHistoryService:
    """获取历史Thread服务实例
    
    Returns:
        ThreadHistoryService: 历史Thread服务实例
    """
    return _history_thread_service_injection.get_instance()


# 设置实例的函数
def set_thread_repository_instance(thread_repository: IThreadRepository) -> None:
    """在应用启动时设置全局 ThreadRepository 实例
    
    Args:
        thread_repository: IThreadRepository 实例
    """
    _thread_repository_injection.set_instance(thread_repository)


def set_thread_service_instance(thread_service: IThreadService) -> None:
    """在应用启动时设置全局 ThreadService 实例
    
    Args:
        thread_service: IThreadService 实例
    """
    _thread_service_injection.set_instance(thread_service)


def set_basic_thread_service_instance(basic_thread_service: BasicThreadService) -> None:
    """在应用启动时设置全局 BasicThreadService 实例
    
    Args:
        basic_thread_service: BasicThreadService 实例
    """
    _basic_thread_service_injection.set_instance(basic_thread_service)


def set_workflow_thread_service_instance(workflow_thread_service: WorkflowThreadService) -> None:
    """在应用启动时设置全局 WorkflowThreadService 实例
    
    Args:
        workflow_thread_service: WorkflowThreadService 实例
    """
    _workflow_thread_service_injection.set_instance(workflow_thread_service)


def set_collaboration_thread_service_instance(collaboration_thread_service: ThreadCollaborationService) -> None:
    """在应用启动时设置全局 ThreadCollaborationService 实例
    
    Args:
        collaboration_thread_service: ThreadCollaborationService 实例
    """
    _collaboration_thread_service_injection.set_instance(collaboration_thread_service)


def set_branch_thread_service_instance(branch_thread_service: ThreadBranchService) -> None:
    """在应用启动时设置全局 ThreadBranchService 实例
    
    Args:
        branch_thread_service: ThreadBranchService 实例
    """
    _branch_thread_service_injection.set_instance(branch_thread_service)


def set_snapshot_thread_service_instance(snapshot_thread_service: ThreadSnapshotService) -> None:
    """在应用启动时设置全局 ThreadSnapshotService 实例
    
    Args:
        snapshot_thread_service: ThreadSnapshotService 实例
    """
    _snapshot_thread_service_injection.set_instance(snapshot_thread_service)


def set_state_thread_service_instance(state_thread_service: ThreadStateService) -> None:
    """在应用启动时设置全局 ThreadStateService 实例
    
    Args:
        state_thread_service: ThreadStateService 实例
    """
    _state_thread_service_injection.set_instance(state_thread_service)


def set_history_thread_service_instance(history_thread_service: ThreadHistoryService) -> None:
    """在应用启动时设置全局 ThreadHistoryService 实例
    
    Args:
        history_thread_service: ThreadHistoryService 实例
    """
    _history_thread_service_injection.set_instance(history_thread_service)


# 清除实例的函数
def clear_thread_repository_instance() -> None:
    """清除全局 ThreadRepository 实例"""
    _thread_repository_injection.clear_instance()


def clear_thread_service_instance() -> None:
    """清除全局 ThreadService 实例"""
    _thread_service_injection.clear_instance()


def clear_basic_thread_service_instance() -> None:
    """清除全局 BasicThreadService 实例"""
    _basic_thread_service_injection.clear_instance()


def clear_workflow_thread_service_instance() -> None:
    """清除全局 WorkflowThreadService 实例"""
    _workflow_thread_service_injection.clear_instance()


def clear_collaboration_thread_service_instance() -> None:
    """清除全局 ThreadCollaborationService 实例"""
    _collaboration_thread_service_injection.clear_instance()


def clear_branch_thread_service_instance() -> None:
    """清除全局 ThreadBranchService 实例"""
    _branch_thread_service_injection.clear_instance()


def clear_snapshot_thread_service_instance() -> None:
    """清除全局 ThreadSnapshotService 实例"""
    _snapshot_thread_service_injection.clear_instance()


def clear_state_thread_service_instance() -> None:
    """清除全局 ThreadStateService 实例"""
    _state_thread_service_injection.clear_instance()


def clear_history_thread_service_instance() -> None:
    """清除全局 ThreadHistoryService 实例"""
    _history_thread_service_injection.clear_instance()


# 获取状态的函数
def get_thread_repository_status() -> dict:
    """获取Thread仓储注入状态"""
    return _thread_repository_injection.get_status()


def get_thread_service_status() -> dict:
    """获取Thread服务注入状态"""
    return _thread_service_injection.get_status()


def get_basic_thread_service_status() -> dict:
    """获取基础Thread服务注入状态"""
    return _basic_thread_service_injection.get_status()


def get_workflow_thread_service_status() -> dict:
    """获取工作流Thread服务注入状态"""
    return _workflow_thread_service_injection.get_status()


def get_collaboration_thread_service_status() -> dict:
    """获取协作Thread服务注入状态"""
    return _collaboration_thread_service_injection.get_status()


def get_branch_thread_service_status() -> dict:
    """获取分支Thread服务注入状态"""
    return _branch_thread_service_injection.get_status()


def get_snapshot_thread_service_status() -> dict:
    """获取快照Thread服务注入状态"""
    return _snapshot_thread_service_injection.get_status()


def get_state_thread_service_status() -> dict:
    """获取状态Thread服务注入状态"""
    return _state_thread_service_injection.get_status()


def get_history_thread_service_status() -> dict:
    """获取历史Thread服务注入状态"""
    return _history_thread_service_injection.get_status()


# 导出的公共接口
__all__ = [
    "get_thread_repository",
    "get_thread_service",
    "get_basic_thread_service",
    "get_workflow_thread_service",
    "get_collaboration_thread_service",
    "get_branch_thread_service",
    "get_snapshot_thread_service",
    "get_state_thread_service",
    "get_history_thread_service",
    "set_thread_repository_instance",
    "set_thread_service_instance",
    "set_basic_thread_service_instance",
    "set_workflow_thread_service_instance",
    "set_collaboration_thread_service_instance",
    "set_branch_thread_service_instance",
    "set_snapshot_thread_service_instance",
    "set_state_thread_service_instance",
    "set_history_thread_service_instance",
    "clear_thread_repository_instance",
    "clear_thread_service_instance",
    "clear_basic_thread_service_instance",
    "clear_workflow_thread_service_instance",
    "clear_collaboration_thread_service_instance",
    "clear_branch_thread_service_instance",
    "clear_snapshot_thread_service_instance",
    "clear_state_thread_service_instance",
    "clear_history_thread_service_instance",
    "get_thread_repository_status",
    "get_thread_service_status",
    "get_basic_thread_service_status",
    "get_workflow_thread_service_status",
    "get_collaboration_thread_service_status",
    "get_branch_thread_service_status",
    "get_snapshot_thread_service_status",
    "get_state_thread_service_status",
    "get_history_thread_service_status",
]