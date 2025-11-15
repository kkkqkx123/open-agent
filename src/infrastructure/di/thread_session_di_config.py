"""Thread与Session重构后的依赖注入配置

展示如何组装重构后的组件，实现清晰的职责划分
"""

from typing import Optional
from pathlib import Path
import logging

from ...domain.threads.repository import ThreadRepository, ThreadBranchRepository, ThreadSnapshotRepository
from ...domain.threads.domain_service import ThreadDomainService
from ...application.threads.thread_service import ThreadService
from ...application.threads.interfaces import IThreadService
from ...application.sessions.manager import SessionManager
from ...infrastructure.langgraph.adapter import LangGraphAdapter
from ...infrastructure.threads.metadata_store import FileThreadMetadataStore, MemoryThreadMetadataStore, IThreadMetadataStore
from ...infrastructure.threads.branch_store import ThreadBranchStore, IThreadBranchStore
from ...infrastructure.threads.snapshot_store import ThreadSnapshotStore, IThreadSnapshotStore
from ...application.checkpoint.manager import CheckpointManager
from ...domain.sessions.store import FileSessionStore, MemorySessionStore, ISessionStore
from ...application.sessions.git_manager import GitManager, MockGitManager, IGitManager
from ...domain.state.interfaces import IStateManager
from ...infrastructure.graph.builder import GraphBuilder
from ...infrastructure.graph.registry import get_global_registry

logger = logging.getLogger(__name__)


class ThreadSessionDIConfig:
    """Thread与Session重构后的依赖注入配置"""
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        use_memory_storage: bool = False,
        use_git: bool = True,
        use_mock_git: bool = False
    ):
        """初始化DI配置
        
        Args:
            storage_path: 存储路径
            use_memory_storage: 是否使用内存存储
            use_git: 是否启用Git
            use_mock_git: 是否使用模拟Git
        """
        self.storage_path = storage_path or Path("./storage")
        self.use_memory_storage = use_memory_storage
        self.use_git = use_git
        self.use_mock_git = use_mock_git
        
        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_langgraph_adapter(
        self,
        state_manager: Optional[IStateManager] = None,
        use_memory_checkpoint: bool = False
    ) -> LangGraphAdapter:
        """创建LangGraph适配器"""
        logger.info("创建LangGraph适配器")
        
        # 创建图构建器
        node_registry = get_global_registry()
        graph_builder = GraphBuilder(node_registry=node_registry)
        
        return LangGraphAdapter(
            checkpoint_saver=None,  # 使用默认的checkpoint保存器
            graph_builder=graph_builder,
            state_manager=state_manager,
            use_memory_checkpoint=use_memory_checkpoint
        )
    
    def create_thread_metadata_store(self) -> IThreadMetadataStore:
        """创建Thread元数据存储"""
        if self.use_memory_storage:
            logger.info("使用内存Thread元数据存储")
            return MemoryThreadMetadataStore()
        else:
            logger.info(f"使用文件Thread元数据存储: {self.storage_path / 'threads'}")
            return FileThreadMetadataStore(self.storage_path / "threads")
    
    def create_thread_branch_store(self) -> IThreadBranchStore:
        """创建Thread分支存储"""
        if self.use_memory_storage:
            logger.info("使用内存Thread分支存储")
            return ThreadBranchStore()  # 内存存储
        else:
            logger.info(f"使用文件Thread分支存储: {self.storage_path / 'branches'}")
            # TODO: 实现文件分支存储
            return ThreadBranchStore()  # 暂时使用内存存储
    
    def create_thread_snapshot_store(self) -> IThreadSnapshotStore:
        """创建Thread快照存储"""
        if self.use_memory_storage:
            logger.info("使用内存Thread快照存储")
            return ThreadSnapshotStore()  # 内存存储
        else:
            logger.info(f"使用文件Thread快照存储: {self.storage_path / 'snapshots'}")
            # TODO: 实现文件快照存储
            return ThreadSnapshotStore()  # 暂时使用内存存储
    
    def create_checkpoint_manager(self) -> CheckpointManager:
        """创建Checkpoint管理器"""
        logger.info("创建Checkpoint管理器")

        # 使用CheckpointManagerFactory创建
        from ...infrastructure.checkpoint.factory import CheckpointManagerFactory
        return CheckpointManagerFactory.create_manager()
    
    def create_thread_service(
        self,
        langgraph_adapter: Optional[LangGraphAdapter] = None,
        state_manager: Optional[IStateManager] = None
    ) -> IThreadService:
        """创建重构后的Thread服务"""
        logger.info("创建重构后的Thread服务")
        
        # 创建基础设施层组件
        metadata_store = self.create_thread_metadata_store()
        branch_store = self.create_thread_branch_store()
        snapshot_store = self.create_thread_snapshot_store()
        checkpoint_manager = self.create_checkpoint_manager()
        
        if langgraph_adapter is None:
            langgraph_adapter = self.create_langgraph_adapter(state_manager)
        
        # 创建领域层组件
        thread_repository = ThreadRepository(metadata_store)
        branch_repository = ThreadBranchRepository(branch_store)
        snapshot_repository = ThreadSnapshotRepository(snapshot_store)
        thread_domain_service = ThreadDomainService()
        
        # 创建应用层服务
        return ThreadService(
            thread_repository=thread_repository,
            thread_domain_service=thread_domain_service,
            branch_repository=branch_repository,
            snapshot_repository=snapshot_repository,
            checkpoint_manager=checkpoint_manager,
            langgraph_adapter=langgraph_adapter,
            metadata_store=metadata_store,
            branch_store=branch_store,
            snapshot_store=snapshot_store
        )
    
    def create_session_store(self) -> ISessionStore:
        """创建会话存储"""
        if self.use_memory_storage:
            logger.info("使用内存会话存储")
            return MemorySessionStore()
        else:
            logger.info(f"使用文件会话存储: {self.storage_path / 'sessions'}")
            return FileSessionStore(self.storage_path / "sessions")
    
    def create_git_manager(self) -> Optional[IGitManager]:
        """创建Git管理器"""
        if not self.use_git:
            logger.info("Git功能已禁用")
            return None
        
        if self.use_mock_git:
            logger.info("使用模拟Git管理器")
            return MockGitManager()
        else:
            logger.info("使用真实Git管理器")
            return GitManager()
    
    def create_session_manager(
        self,
        thread_service: Optional[IThreadService] = None,
        state_manager: Optional[IStateManager] = None
    ) -> SessionManager:
        """创建重构后的Session管理器"""
        logger.info("创建重构后的Session管理器")
        
        # 创建依赖
        if thread_service is None:
            thread_service = self.create_thread_service(state_manager=state_manager)
        
        session_store = self.create_session_store()
        git_manager = self.create_git_manager()
        
        return SessionManager(
            thread_service=thread_service,  # 使用ThreadService而不是ThreadManager
            session_store=session_store,
            git_manager=git_manager,
            storage_path=self.storage_path / "sessions",
            state_manager=state_manager
        )
    
    def create_complete_stack(
        self,
        state_manager: Optional[IStateManager] = None
    ) -> dict:
        """创建完整的组件栈"""
        logger.info("创建完整的Thread与Session组件栈")
        
        # 创建基础设施层组件（用于返回）
        metadata_store = self.create_thread_metadata_store()
        branch_store = self.create_thread_branch_store()
        snapshot_store = self.create_thread_snapshot_store()
        checkpoint_manager = self.create_checkpoint_manager()
        
        # 创建核心组件
        langgraph_adapter = self.create_langgraph_adapter(state_manager)
        thread_service = self.create_thread_service(langgraph_adapter, state_manager)
        session_manager = self.create_session_manager(thread_service, state_manager)
        
        return {
            "langgraph_adapter": langgraph_adapter,
            "thread_service": thread_service,
            "session_manager": session_manager,
            "metadata_store": metadata_store,
            "branch_store": branch_store,
            "snapshot_store": snapshot_store,
            "checkpoint_manager": checkpoint_manager,
            "session_store": session_manager.session_store,
            "git_manager": session_manager.git_manager
        }


class ThreadSessionFactory:
    """Thread与Session组件工厂"""
    
    def __init__(self, di_config: ThreadSessionDIConfig):
        """初始化工厂
        
        Args:
            di_config: 依赖注入配置
        """
        self.di_config = di_config
        self._components_cache = {}
    
    def get_langgraph_adapter(self, state_manager: Optional[IStateManager] = None) -> LangGraphAdapter:
        """获取LangGraph适配器（单例）"""
        if "langgraph_adapter" not in self._components_cache:
            self._components_cache["langgraph_adapter"] = self.di_config.create_langgraph_adapter(state_manager)
        return self._components_cache["langgraph_adapter"]
    
    def get_thread_service(self, state_manager: Optional[IStateManager] = None) -> IThreadService:
        """获取Thread服务（单例）"""
        if "thread_service" not in self._components_cache:
            langgraph_adapter = self.get_langgraph_adapter(state_manager)
            self._components_cache["thread_service"] = self.di_config.create_thread_service(langgraph_adapter, state_manager)
        return self._components_cache["thread_service"]
    
    def get_session_manager(self, state_manager: Optional[IStateManager] = None) -> SessionManager:
        """获取Session管理器（单例）"""
        if "session_manager" not in self._components_cache:
            thread_service = self.get_thread_service(state_manager)
            self._components_cache["session_manager"] = self.di_config.create_session_manager(thread_service, state_manager)
        return self._components_cache["session_manager"]
    
    def clear_cache(self) -> None:
        """清空组件缓存"""
        self._components_cache.clear()
        logger.info("Thread与Session组件缓存已清空")


# === 使用示例 ===

def create_development_stack(storage_path: Optional[Path] = None) -> dict:
    """创建开发环境组件栈"""
    di_config = ThreadSessionDIConfig(
        storage_path=storage_path,
        use_memory_storage=False,
        use_git=True,
        use_mock_git=False
    )
    return di_config.create_complete_stack()


def create_testing_stack() -> dict:
    """创建测试环境组件栈"""
    di_config = ThreadSessionDIConfig(
        storage_path=Path("./test_storage"),
        use_memory_storage=True,
        use_git=False,
        use_mock_git=True
    )
    return di_config.create_complete_stack()


def create_production_stack(storage_path: Path) -> dict:
    """创建生产环境组件栈"""
    di_config = ThreadSessionDIConfig(
        storage_path=storage_path,
        use_memory_storage=False,
        use_git=True,
        use_mock_git=False
    )
    return di_config.create_complete_stack()


# === 全局工厂实例 ===

_default_factory: Optional[ThreadSessionFactory] = None


def get_default_factory() -> ThreadSessionFactory:
    """获取默认工厂实例"""
    global _default_factory
    if _default_factory is None:
        di_config = ThreadSessionDIConfig()
        _default_factory = ThreadSessionFactory(di_config)
    return _default_factory


def get_thread_service(state_manager: Optional[IStateManager] = None) -> IThreadService:
    """获取Thread服务（便捷方法）"""
    return get_default_factory().get_thread_service(state_manager)


def get_session_manager(state_manager: Optional[IStateManager] = None) -> SessionManager:
    """获取Session管理器（便捷方法）"""
    return get_default_factory().get_session_manager(state_manager)


def get_langgraph_adapter(state_manager: Optional[IStateManager] = None) -> LangGraphAdapter:
    """获取LangGraph适配器（便捷方法）"""
    return get_default_factory().get_langgraph_adapter(state_manager)


# === 初始化函数 ===

def initialize_thread_session_system(
    storage_path: Optional[Path] = None,
    use_memory_storage: bool = False,
    use_git: bool = True,
    state_manager: Optional[IStateManager] = None
) -> dict:
    """初始化Thread与Session系统
    
    Args:
        storage_path: 存储路径
        use_memory_storage: 是否使用内存存储
        use_git: 是否启用Git
        state_manager: 状态管理器
        
    Returns:
        dict: 组件字典
    """
    logger.info("初始化Thread与Session系统")
    
    # 创建DI配置
    di_config = ThreadSessionDIConfig(
        storage_path=storage_path,
        use_memory_storage=use_memory_storage,
        use_git=use_git
    )
    
    # 创建完整组件栈
    components = di_config.create_complete_stack(state_manager)
    
    # 设置全局工厂
    global _default_factory
    _default_factory = ThreadSessionFactory(di_config)
    
    logger.info("Thread与Session系统初始化完成")
    return components


# === 向后兼容的别名 ===

# 为了向后兼容，保留一些旧的别名
def get_thread_manager(state_manager: Optional[IStateManager] = None) -> IThreadService:
    """获取Thread管理器（向后兼容别名）"""
    logger.warning("get_thread_manager已废弃，请使用get_thread_service")
    return get_thread_service(state_manager)