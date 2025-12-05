"""Sessions依赖注入便利层

使用通用依赖注入框架提供简洁的Sessions服务获取方式。
"""

from typing import Optional, Dict, Any, List, AsyncGenerator, Sequence, TYPE_CHECKING

from src.interfaces.sessions import ISessionRepository
from src.interfaces.sessions.service import ISessionService
from src.interfaces.sessions.association import (
    ISessionThreadAssociationRepository,
    ISessionThreadSynchronizer,
    ISessionThreadTransaction,
    ISessionThreadAssociation
)
from src.interfaces.threads import IThreadRepository
from src.interfaces.threads.service import IThreadService
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable

if TYPE_CHECKING:
    from src.core.sessions.entities import Session, SessionStatus, UserRequestEntity as UserRequest, UserInteractionEntity as UserInteraction, SessionContext
    from src.core.threads.entities import Thread, ThreadStatus, ThreadType
    from src.core.state import WorkflowState


class _StubSessionRepository(ISessionRepository):
    """临时 SessionRepository 实现（用于极端情况）"""
    
    async def create(self, session: 'Session') -> bool:
        """创建会话"""
        return False
    
    async def get(self, session_id: str) -> Optional['Session']:
        """获取会话"""
        return None
    
    async def update(self, session: 'Session') -> bool:
        """更新会话"""
        return False
    
    async def delete(self, session_id: str) -> bool:
        """删除会话"""
        return False
    
    async def list_by_status(self, status: 'SessionStatus') -> List['Session']:
        """按状态列会话"""
        return []
    
    async def list_by_date_range(self, start_date, end_date) -> List['Session']:
        """按日期范围列会话"""
        return []
    
    async def search(self, query: str, limit: int = 10) -> List['Session']:
        """搜索会话"""
        return []
    
    async def get_count_by_status(self) -> Dict[str, int]:
        """获取各状态会话数量"""
        return {}
    
    async def cleanup_old(self, max_age_days: int = 30) -> int:
        """清理旧会话"""
        return 0
    
    async def add_interaction(self, session_id: str, interaction: Dict[str, Any]) -> bool:
        """添加用户交互"""
        return False
    
    async def get_interactions(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取交互历史"""
        return []
    
    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return False


class _StubSessionService(ISessionService):
    """临时 SessionService 实现（用于极端情况）"""
    
    async def create_session(self, user_request: 'UserRequest') -> str:
        """创建会话"""
        return "stub_session_id"
    
    async def get_session_context(self, session_id: str) -> Optional['SessionContext']:
        """获取会话上下文"""
        return None
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        return False
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        return []
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return None
    
    async def track_user_interaction(self, session_id: str, interaction: 'UserInteraction') -> None:
        """追踪用户交互"""
        pass
    
    async def get_interaction_history(self, session_id: str, limit: Optional[int] = None) -> List['UserInteraction']:
        """获取交互历史"""
        return []
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        return []
    
    async def coordinate_threads(self, session_id: str, thread_configs: List[Dict[str, Any]]) -> Dict[str, str]:
        """协调多个Thread执行"""
        return {}
    
    async def execute_workflow_in_session(self, session_id: str, thread_name: str, config: Optional[Dict[str, Any]] = None) -> 'WorkflowState':
        """在会话中执行工作流"""
        return {}  # type: ignore
    
    def stream_workflow_in_session(self, session_id: str, thread_name: str, config: Optional[Dict[str, Any]] = None):
        """在会话中流式执行工作流"""
        async def _stream():
            return
            yield
        return _stream
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要"""
        return {}
    
    async def create_session_with_threads(self, workflow_configs: Dict[str, str], dependencies: Optional[Dict[str, List[str]]] = None, agent_config: Optional[Dict[str, Any]] = None, initial_states: Optional[Dict[str, 'WorkflowState']] = None) -> str:
        """创建会话并关联多个Thread"""
        return "stub_session_id"


class _StubAssociationRepository(ISessionThreadAssociationRepository):
    """临时 AssociationRepository 实现（用于极端情况）"""
    
    async def create(self, association: ISessionThreadAssociation) -> bool:
        """创建关联"""
        return False
    
    async def get(self, association_id: str) -> Optional[ISessionThreadAssociation]:
        """获取关联"""
        return None
    
    async def get_by_session_and_thread(self, session_id: str, thread_id: str) -> Optional[ISessionThreadAssociation]:
        """根据Session和Thread ID获取关联"""
        return None
    
    async def list_by_session(self, session_id: str) -> Sequence[ISessionThreadAssociation]:
        """列出Session的所有关联"""
        return []
    
    async def list_by_thread(self, thread_id: str) -> Sequence[ISessionThreadAssociation]:
        """列出Thread的所有关联"""
        return []
    
    async def update(self, association: ISessionThreadAssociation) -> bool:
        """更新关联"""
        return False
    
    async def delete(self, association_id: str) -> bool:
        """删除关联"""
        return False
    
    async def delete_by_session_and_thread(self, session_id: str, thread_id: str) -> bool:
        """根据Session和Thread ID删除关联"""
        return False
    
    async def exists(self, session_id: str, thread_id: str) -> bool:
        """检查关联是否存在"""
        return False
    
    async def get_active_associations_by_session(self, session_id: str) -> Sequence[ISessionThreadAssociation]:
        """获取Session的活跃关联"""
        return []
    
    async def cleanup_inactive_associations(self, max_age_days: int = 30) -> int:
        """清理非活跃关联"""
        return 0


class _StubSynchronizer(ISessionThreadSynchronizer):
    """临时 Synchronizer 实现（用于极端情况）"""
    
    async def sync_session_threads(self, session_id: str) -> Dict[str, Any]:
        """同步Session的Thread关联"""
        return {}
    
    async def validate_consistency(self, session_id: str) -> List[str]:
        """验证Session-Thread一致性"""
        return []
    
    async def repair_inconsistencies(self, session_id: str) -> Dict[str, Any]:
        """修复不一致问题"""
        return {}


class _StubTransaction(ISessionThreadTransaction):
    """临时 Transaction 实现（用于极端情况）"""
    
    async def create_thread_with_session(self, session_id: str, thread_config: Dict[str, Any], thread_name: str) -> str:
        """原子性地创建Thread并建立Session关联"""
        return "stub_thread_id"
    
    async def remove_thread_from_session(self, session_id: str, thread_id: str) -> bool:
        """原子性地从Session中移除Thread"""
        return False
    
    async def transfer_thread_between_sessions(self, thread_id: str, from_session_id: str, to_session_id: str, new_thread_name: Optional[str] = None) -> bool:
        """原子性地在线程间转移Thread"""
        return False


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
        """删除线程"""
        return False
    
    async def list_by_session(self, session_id: str) -> List['Thread']:
        """按会话列线程"""
        return []
    
    async def list_by_status(self, status: 'ThreadStatus') -> List['Thread']:
        """按状态列线程"""
        return []
    
    async def search(self, query: str, session_id: Optional[str] = None, limit: int = 10) -> List['Thread']:
        """搜索线程"""
        return []
    
    async def get_count_by_session(self, session_id: str) -> int:
        """获取会话的线程数量"""
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
        """获取线程统计信息"""
        return {}
    
    async def search_with_filters(self, filters: Dict[str, Any], limit: Optional[int] = None, offset: Optional[int] = None) -> List['Thread']:
        """根据过滤条件搜索线程"""
        return []


class _StubThreadService(IThreadService):
    """临时 ThreadService 实现（用于极端情况）"""
    
    async def create_thread_with_session(self, thread_config: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """创建线程并关联会话"""
        return "stub_thread_id"
    
    async def fork_thread_from_checkpoint(self, source_thread_id: str, checkpoint_id: str, branch_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
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
    
    async def execute_workflow(self, thread_id: str, config: Optional[Dict[str, Any]] = None, initial_state: Optional[Dict[str, Any]] = None) -> 'WorkflowState':
        """执行工作流"""
        return {}  # type: ignore
    
    async def stream_workflow(self, thread_id: str, config: Optional[Dict[str, Any]] = None, initial_state: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:  # type: ignore
        """流式执行工作流"""
        if False:
            yield  # pragma: no cover
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态"""
        return None
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态"""
        return False
    
    async def create_branch(self, thread_id: str, checkpoint_id: str, branch_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建Thread分支"""
        return "stub_thread_id"
    
    async def get_thread_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取Thread的所有分支"""
        return []
    
    async def merge_branch(self, target_thread_id: str, source_thread_id: str, merge_strategy: str = "latest") -> bool:
        """合并分支到目标Thread"""
        return False
    
    async def create_snapshot(self, thread_id: str, snapshot_name: str, description: Optional[str] = None) -> str:
        """创建Thread快照"""
        return "stub_snapshot_id"
    
    async def restore_snapshot(self, thread_id: str, snapshot_id: str) -> bool:
        """从快照恢复Thread状态"""
        return False
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        return False
    
    async def rollback_thread(self, thread_id: str, checkpoint_id: str) -> bool:
        """回滚Thread到指定检查点"""
        return False
    
    async def search_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """搜索Threads"""
        return []
    
    async def get_thread_statistics(self) -> Dict[str, Any]:
        """获取Thread统计信息"""
        return {}
    
    async def get_thread_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取Thread历史记录"""
        return []
    
    async def share_thread_state(self, source_thread_id: str, target_thread_id: str, checkpoint_id: str, permissions: Optional[Dict[str, Any]] = None) -> bool:
        """共享Thread状态到其他Thread"""
        return False
    
    async def create_shared_session(self, thread_ids: List[str], session_config: Dict[str, Any]) -> str:
        """创建共享会话"""
        return "stub_session_id"
    
    async def sync_thread_states(self, thread_ids: List[str], sync_strategy: str = "bidirectional") -> bool:
        """同步多个Thread状态"""
        return False
    
    async def validate_thread_state(self, thread_id: str) -> bool:
        """验证Thread状态"""
        return False
    
    async def can_transition_to_status(self, thread_id: str, new_status: str) -> bool:
        """检查是否可以转换到指定状态"""
        return False


def _create_fallback_session_repository() -> ISessionRepository:
    """创建fallback session repository"""
    return _StubSessionRepository()


def _create_fallback_session_service() -> ISessionService:
    """创建fallback session service"""
    return _StubSessionService()


def _create_fallback_association_repository() -> ISessionThreadAssociationRepository:
    """创建fallback association repository"""
    return _StubAssociationRepository()


def _create_fallback_synchronizer() -> ISessionThreadSynchronizer:
    """创建fallback synchronizer"""
    return _StubSynchronizer()


def _create_fallback_transaction() -> ISessionThreadTransaction:
    """创建fallback transaction"""
    return _StubTransaction()


def _create_fallback_thread_repository() -> IThreadRepository:
    """创建fallback thread repository"""
    return _StubThreadRepository()


def _create_fallback_thread_service() -> IThreadService:
    """创建fallback thread service"""
    return _StubThreadService()


# 注册Sessions注入
_session_repository_injection = get_global_injection_registry().register(
    ISessionRepository, _create_fallback_session_repository
)
_session_service_injection = get_global_injection_registry().register(
    ISessionService, _create_fallback_session_service
)
_association_repository_injection = get_global_injection_registry().register(
    ISessionThreadAssociationRepository, _create_fallback_association_repository
)
_synchronizer_injection = get_global_injection_registry().register(
    ISessionThreadSynchronizer, _create_fallback_synchronizer
)
_transaction_injection = get_global_injection_registry().register(
    ISessionThreadTransaction, _create_fallback_transaction
)
_thread_repository_injection = get_global_injection_registry().register(
    IThreadRepository, _create_fallback_thread_repository
)
_thread_service_injection = get_global_injection_registry().register(
    IThreadService, _create_fallback_thread_service
)


@injectable(ISessionRepository, _create_fallback_session_repository)
def get_session_repository() -> ISessionRepository:
    """获取Session仓储实例
    
    Returns:
        ISessionRepository: Session仓储实例
    """
    return _session_repository_injection.get_instance()


@injectable(ISessionService, _create_fallback_session_service)
def get_session_service() -> ISessionService:
    """获取Session服务实例
    
    Returns:
        ISessionService: Session服务实例
    """
    return _session_service_injection.get_instance()


@injectable(ISessionThreadAssociationRepository, _create_fallback_association_repository)
def get_association_repository() -> ISessionThreadAssociationRepository:
    """获取关联仓储实例
    
    Returns:
        ISessionThreadAssociationRepository: 关联仓储实例
    """
    return _association_repository_injection.get_instance()


@injectable(ISessionThreadSynchronizer, _create_fallback_synchronizer)
def get_synchronizer() -> ISessionThreadSynchronizer:
    """获取同步器实例
    
    Returns:
        ISessionThreadSynchronizer: 同步器实例
    """
    return _synchronizer_injection.get_instance()


@injectable(ISessionThreadTransaction, _create_fallback_transaction)
def get_transaction_manager() -> ISessionThreadTransaction:
    """获取事务管理器实例
    
    Returns:
        ISessionThreadTransaction: 事务管理器实例
    """
    return _transaction_injection.get_instance()


@injectable(IThreadRepository, _create_fallback_thread_repository)
def get_thread_repository() -> IThreadRepository:
    """获取Thread仓储实例
    
    Returns:
        IThreadRepository: Thread仓储实例
    """
    return _thread_repository_injection.get_instance()


@injectable(IThreadService, _create_fallback_thread_service)
def get_thread_service() -> IThreadService:
    """获取Thread服务实例
    
    Returns:
        IThreadService: Thread服务实例
    """
    return _thread_service_injection.get_instance()


# 设置实例的函数
def set_session_repository_instance(session_repository: ISessionRepository) -> None:
    """在应用启动时设置全局 SessionRepository 实例
    
    Args:
        session_repository: ISessionRepository 实例
    """
    _session_repository_injection.set_instance(session_repository)


def set_session_service_instance(session_service: ISessionService) -> None:
    """在应用启动时设置全局 SessionService 实例
    
    Args:
        session_service: ISessionService 实例
    """
    _session_service_injection.set_instance(session_service)


def set_association_repository_instance(association_repository: ISessionThreadAssociationRepository) -> None:
    """在应用启动时设置全局 AssociationRepository 实例
    
    Args:
        association_repository: ISessionThreadAssociationRepository 实例
    """
    _association_repository_injection.set_instance(association_repository)


def set_synchronizer_instance(synchronizer: ISessionThreadSynchronizer) -> None:
    """在应用启动时设置全局 Synchronizer 实例
    
    Args:
        synchronizer: ISessionThreadSynchronizer 实例
    """
    _synchronizer_injection.set_instance(synchronizer)


def set_transaction_manager_instance(transaction_manager: ISessionThreadTransaction) -> None:
    """在应用启动时设置全局 TransactionManager 实例
    
    Args:
        transaction_manager: ISessionThreadTransaction 实例
    """
    _transaction_injection.set_instance(transaction_manager)


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


# 清除实例的函数
def clear_session_repository_instance() -> None:
    """清除全局 SessionRepository 实例"""
    _session_repository_injection.clear_instance()


def clear_session_service_instance() -> None:
    """清除全局 SessionService 实例"""
    _session_service_injection.clear_instance()


def clear_association_repository_instance() -> None:
    """清除全局 AssociationRepository 实例"""
    _association_repository_injection.clear_instance()


def clear_synchronizer_instance() -> None:
    """清除全局 Synchronizer 实例"""
    _synchronizer_injection.clear_instance()


def clear_transaction_manager_instance() -> None:
    """清除全局 TransactionManager 实例"""
    _transaction_injection.clear_instance()


def clear_thread_repository_instance() -> None:
    """清除全局 ThreadRepository 实例"""
    _thread_repository_injection.clear_instance()


def clear_thread_service_instance() -> None:
    """清除全局 ThreadService 实例"""
    _thread_service_injection.clear_instance()


# 获取状态的函数
def get_session_repository_status() -> dict:
    """获取Session仓储注入状态"""
    return _session_repository_injection.get_status()


def get_session_service_status() -> dict:
    """获取Session服务注入状态"""
    return _session_service_injection.get_status()


def get_association_repository_status() -> dict:
    """获取关联仓储注入状态"""
    return _association_repository_injection.get_status()


def get_synchronizer_status() -> dict:
    """获取同步器注入状态"""
    return _synchronizer_injection.get_status()


def get_transaction_manager_status() -> dict:
    """获取事务管理器注入状态"""
    return _transaction_injection.get_status()


def get_thread_repository_status() -> dict:
    """获取Thread仓储注入状态"""
    return _thread_repository_injection.get_status()


def get_thread_service_status() -> dict:
    """获取Thread服务注入状态"""
    return _thread_service_injection.get_status()


# 导出的公共接口
__all__ = [
    "get_session_repository",
    "get_session_service",
    "get_association_repository",
    "get_synchronizer",
    "get_transaction_manager",
    "get_thread_repository",
    "get_thread_service",
    "set_session_repository_instance",
    "set_session_service_instance",
    "set_association_repository_instance",
    "set_synchronizer_instance",
    "set_transaction_manager_instance",
    "set_thread_repository_instance",
    "set_thread_service_instance",
    "clear_session_repository_instance",
    "clear_session_service_instance",
    "clear_association_repository_instance",
    "clear_synchronizer_instance",
    "clear_transaction_manager_instance",
    "clear_thread_repository_instance",
    "clear_thread_service_instance",
    "get_session_repository_status",
    "get_session_service_status",
    "get_association_repository_status",
    "get_synchronizer_status",
    "get_transaction_manager_status",
    "get_thread_repository_status",
    "get_thread_service_status",
]
