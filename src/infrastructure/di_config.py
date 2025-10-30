"""简化的依赖注入配置模块

提供统一的服务注册和配置管理，减少不必要的抽象层。
"""

import logging
from typing import Optional, Dict, Any, Type
from pathlib import Path

from .container import IDependencyContainer, DependencyContainer, ServiceLifetime
from .config_loader import IConfigLoader, YamlConfigLoader
from .graph.registry import NodeRegistry
from src.application.sessions.manager import ISessionManager, SessionManager
from src.application.workflow.manager import IWorkflowManager, WorkflowManager
from src.domain.sessions.store import ISessionStore
from src.domain.state.interfaces import IStateManager, IStateCollaborationManager
from src.domain.threads.interfaces import IThreadManager
from src.infrastructure.state.snapshot_store import StateSnapshotStore
from src.infrastructure.state.history_manager import StateHistoryManager

logger = logging.getLogger(__name__)


class DIConfig:
    """简化的依赖注入配置类
    
    负责统一管理所有服务的注册和配置，减少代码重复和复杂性。
    """
    
    def __init__(self, container: Optional[IDependencyContainer] = None):
        """初始化DI配置
        
        Args:
            container: 依赖注入容器，如果为None则创建新容器
        """
        self.container = container or DependencyContainer()
        self._config_loader: Optional[IConfigLoader] = None
        self._node_registry: Optional[NodeRegistry] = None
        self._session_store: Optional[ISessionStore] = None
        
    def configure_core_services(
        self,
        config_path: str = "configs",
        environment: str = "default"
    ) -> IDependencyContainer:
        """配置核心服务
        
        Args:
            config_path: 配置文件路径
            environment: 环境名称
            
        Returns:
            配置好的依赖注入容器
        """
        logger.info(f"开始配置核心服务，环境: {environment}")
        
        # 设置环境
        self.container.set_environment(environment)
        
        # 注册配置加载器
        self._register_config_loader(config_path)
        
        # 注册节点注册表
        self._register_node_registry()
        
        # 注册状态管理器
        self._register_state_manager()
        
        # 注册状态协作管理器
        self._register_state_collaboration_manager()
        
        # 注册工作流管理器
        self._register_workflow_manager()
        
        # 注册会话存储
        self._register_session_store()
        
        # 注册会话管理器
        self._register_session_manager()
        
        # 注册线程管理器（如果可用）
        self._register_thread_manager()
        
        logger.info("核心服务配置完成")
        return self.container
    
    def _register_config_loader(self, config_path: str) -> None:
        """注册配置加载器"""
        if not self.container.has_service(IConfigLoader):
            config_loader = YamlConfigLoader(base_path=config_path)
            self.container.register_instance(IConfigLoader, config_loader)
            self._config_loader = config_loader
            logger.debug("配置加载器注册完成")
        
        # 注册增强的配置验证器
        from .config.enhanced_validator import EnhancedConfigValidator
        self.container.register_factory(
            EnhancedConfigValidator,
            lambda: EnhancedConfigValidator(),
            lifetime=ServiceLifetime.SINGLETON
        )
        logger.debug("增强配置验证器注册完成")
    
    def _register_node_registry(self) -> None:
        """注册节点注册表"""
        if not self.container.has_service(NodeRegistry):
            node_registry = NodeRegistry()
            self.container.register_instance(NodeRegistry, node_registry)
            self._node_registry = node_registry
            logger.debug("节点注册表注册完成")
    
    def _register_state_manager(self) -> None:
        """注册状态管理器"""
        # 注册组合的状态管理器（提供完整功能）
        try:
            from .graph.states.composite_manager import CompositeStateManager
            self.container.register_factory(
                CompositeStateManager,
                lambda: CompositeStateManager(),
                lifetime=ServiceLifetime.SINGLETON
            )
            logger.debug("组合状态管理器注册完成")
        except ImportError as e:
            logger.warning(f"组合状态管理器不可用: {e}")
        
        # 尝试注册基础状态管理器
        try:
            from src.domain.state.manager import StateManager
            if not self.container.has_service(IStateManager):
                # 使用工厂方法注册，确保依赖注入
                self.container.register_factory(
                    IStateManager,
                    lambda: StateManager(),
                    lifetime=ServiceLifetime.SINGLETON
                )
                logger.debug("状态管理器注册完成")
        except ImportError as e:
            logger.warning(f"基础状态管理器不可用: {e}")
    
    def _register_state_collaboration_manager(self) -> None:
        """注册状态协作管理器 - 重构版本"""
        try:
            # 注册SQLite快照存储
            from .state.sqlite_snapshot_store import SQLiteSnapshotStore
            self.container.register_factory(
                StateSnapshotStore,
                lambda: SQLiteSnapshotStore(),
                lifetime=ServiceLifetime.SINGLETON
            )
            logger.debug("SQLite快照存储注册完成")
            
            # 注册SQLite历史管理器
            from .state.sqlite_history_manager import SQLiteHistoryManager
            self.container.register_factory(
                StateHistoryManager,
                lambda: SQLiteHistoryManager(),
                lifetime=ServiceLifetime.SINGLETON
            )
            logger.debug("SQLite历史管理器注册完成")
            
            # 注册增强状态管理器（实现协作管理器接口）
            from src.domain.state.enhanced_manager import EnhancedStateManager
            def create_enhanced_state_manager():
                snapshot_store = self.container.get(StateSnapshotStore)
                history_manager = self.container.get(StateHistoryManager)
                return EnhancedStateManager(snapshot_store, history_manager)
            
            self.container.register_factory(
                IStateCollaborationManager,
                create_enhanced_state_manager,
                lifetime=ServiceLifetime.SINGLETON
            )
            logger.debug("状态协作管理器注册完成")
            
        except ImportError as e:
            logger.warning(f"状态协作管理器不可用: {e}")
    
    def _register_workflow_manager(self) -> None:
        """注册工作流管理器"""
        if not self.container.has_service(IWorkflowManager):
            # 使用工厂方法注册，确保依赖注入
            self.container.register_factory(
                IWorkflowManager,
                lambda: WorkflowManager(
                    self._config_loader,
                    self.container
                ),
                lifetime=ServiceLifetime.SINGLETON
            )
            logger.debug("工作流管理器注册完成")
    
    def _register_session_store(self) -> None:
        # 注册会话存储
        try:
            from src.domain.sessions.store import FileSessionStore
            if not self.container.has_service(ISessionStore):
                # 使用工厂方法注册，确保依赖注入
                self.container.register_factory(
                    ISessionStore,
                    lambda: FileSessionStore(Path("./history")),
                    lifetime=ServiceLifetime.SINGLETON
                )
                logger.debug("会话存储注册完成")
        except ImportError:
            logger.warning("会话存储不可用，跳过注册")
    
    def _register_session_manager(self) -> None:
        """注册会话管理器"""
        if not self.container.has_service(ISessionManager):
            # 使用工厂方法注册，确保依赖注入
            self.container.register_factory(
                ISessionManager,
                lambda: SessionManager(
                    workflow_manager=self.container.get(IWorkflowManager),
                    session_store=self.container.get(ISessionStore),
                    state_manager=self.container.get(IStateManager) if self.container.has_service(IStateManager) else None,
                    thread_manager=self.container.get(IThreadManager) if self.container.has_service(IThreadManager) else None
                ),
                lifetime=ServiceLifetime.SINGLETON
            )
            logger.debug("会话管理器注册完成")
    
    def _register_thread_manager(self) -> None:
       """注册线程管理器"""
       # 注册线程管理器（可选组件，需要额外依赖）
       # 由于ThreadManager需要metadata_store和checkpoint_manager作为依赖，
       # 而这些依赖可能比较复杂，暂时跳过注册，可在需要时单独配置
       pass
    
    def register_additional_services(self, services_config: Dict[str, Any]) -> None:
        """注册额外的服务
        
        Args:
            services_config: 服务配置字典
        """
        for service_name, service_config in services_config.items():
            try:
                self._register_single_service(service_name, service_config)
            except Exception as e:
                logger.error(f"注册服务 {service_name} 失败: {e}")
    
    def _register_single_service(self, service_name: str, service_config: Dict[str, Any]) -> None:
        """注册单个服务
        
        Args:
            service_name: 服务名称
            service_config: 服务配置
        """
        # 获取服务类型
        service_type = self._resolve_service_type(service_config.get("type"))
        if not service_type:
            logger.warning(f"无法解析服务类型: {service_config.get('type')}")
            return
        
        # 获取实现类型
        implementation_type = self._resolve_service_type(service_config.get("implementation"))
        if not implementation_type:
            logger.warning(f"无法解析实现类型: {service_config.get('implementation')}")
            return
        
        # 获取生命周期
        lifetime = service_config.get("lifetime", ServiceLifetime.SINGLETON)
        
        # 注册服务
        self.container.register(
            service_type,
            implementation_type,
            environment=service_config.get("environment", "default"),
            lifetime=lifetime
        )
        
        logger.debug(f"服务 {service_name} 注册完成")
    
    def _resolve_service_type(self, type_str: Optional[str]) -> Optional[Type]:
        """解析服务类型字符串

        Args:
            type_str: 类型字符串

        Returns:
            解析后的类型，如果解析失败则返回None
        """
        if not type_str:
            return None
        
        try:
            # 简单的类型解析，可以根据需要扩展
            module_path, class_name = type_str.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError, ValueError):
            return None
    
    def get_container(self) -> IDependencyContainer:
        """获取配置好的容器
        
        Returns:
            依赖注入容器
        """
        return self.container
    
    def validate_configuration(self) -> Dict[str, Any]:
        """验证配置
        
        Returns:
            验证结果
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "registered_services": []
        }
        
        # 检查核心服务
        core_services = [
            IConfigLoader,
            NodeRegistry,
            IWorkflowManager,
            ISessionManager
        ]
        
        for service_type in core_services:
            if self.container.has_service(service_type):
                results["registered_services"].append(service_type.__name__)
                try:
                    # 尝试获取服务实例
                    self.container.get(service_type)
                except Exception as e:
                    results["errors"].append(f"无法获取服务 {service_type.__name__}: {e}")
                    results["valid"] = False
            else:
                results["warnings"].append(f"核心服务未注册: {service_type.__name__}")
                # 如果核心服务未注册，配置无效
                results["valid"] = False
                # 添加错误信息，因为核心服务缺失是一个严重问题
                results["errors"].append(f"核心服务缺失: {service_type.__name__}")
        
        return results


def create_container(
    config_path: str = "configs",
    environment: str = "default",
    additional_services: Optional[Dict[str, Any]] = None
) -> IDependencyContainer:
    """创建配置好的依赖注入容器
    
    Args:
        config_path: 配置文件路径
        environment: 环境名称
        additional_services: 额外服务配置
        
    Returns:
        配置好的依赖注入容器
    """
    di_config = DIConfig()
    container = di_config.configure_core_services(config_path, environment)
    
    if additional_services:
        di_config.register_additional_services(additional_services)
    
    # 验证配置
    validation_result = di_config.validate_configuration()
    if not validation_result["valid"]:
        logger.error(f"依赖注入配置验证失败: {validation_result['errors']}")
    
    return container


# 全局容器实例
_global_container: Optional[IDependencyContainer] = None


def get_global_container(
    config_path: str = "configs",
    environment: str = "default"
) -> IDependencyContainer:
    """获取全局依赖注入容器
    
    Args:
        config_path: 配置文件路径
        environment: 环境名称
        
    Returns:
        全局依赖注入容器
    """
    global _global_container
    if _global_container is None:
        _global_container = create_container(config_path, environment)
    return _global_container


def reset_global_container() -> None:
    """重置全局容器"""
    global _global_container
    if _global_container:
        _global_container.clear()
    _global_container = None