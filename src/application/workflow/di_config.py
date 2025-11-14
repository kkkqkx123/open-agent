"""工作流模块依赖注入配置

提供工作流相关服务的注册和配置。
"""

from typing import Type, Optional
from src.infrastructure.container import IDependencyContainer, ServiceLifetime
from infrastructure.config.loader.yaml_loader import IConfigLoader
from src.infrastructure.graph.registry import NodeRegistry
from src.infrastructure.graph.states import StateFactory, StateSerializer
from src.infrastructure.graph.builder import GraphBuilder
from .interfaces import IWorkflowManager
from .factory import IWorkflowFactory
from .factory import WorkflowFactory
from .manager import WorkflowManager


class WorkflowModule:
    """工作流模块服务注册配置"""
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册工作流相关服务
        
        Args:
            container: 依赖注入容器
        """
        # 注册状态工厂（单例）
        container.register(
            StateFactory,
            StateFactory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册状态序列化器（单例）
        container.register(
            StateSerializer,
            StateSerializer,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册图构建器（单例）
        container.register(
            GraphBuilder,
            GraphBuilder,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流工厂（单例）
        container.register(
            IWorkflowFactory,
            WorkflowFactory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流管理器（单例）
        container.register(
            IWorkflowManager,
            WorkflowManager,
            lifetime=ServiceLifetime.SINGLETON
        )
    
    @staticmethod
    def register_services_with_dependencies(
        container: IDependencyContainer,
        config_loader: IConfigLoader,
        node_registry: NodeRegistry
    ) -> None:
        """注册工作流相关服务（带依赖）
        
        Args:
            container: 依赖注入容器
            config_loader: 配置加载器
            node_registry: 节点注册表
        """
        # 注册配置加载器（如果未注册）
        if not container.has_service(IConfigLoader):
            container.register_instance(IConfigLoader, config_loader)
        
        # 注册节点注册表（如果未注册）
        if not container.has_service(NodeRegistry):
            container.register_instance(NodeRegistry, node_registry)
        
        # 注册通用工作流加载器
        from .universal_loader import UniversalWorkflowLoader
        container.register_factory(
            UniversalWorkflowLoader,
            lambda: UniversalWorkflowLoader(
                config_loader=container.get(IConfigLoader),
                container=container,
                enable_auto_registration=True
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册图构建器（带依赖）
        container.register_factory(
            GraphBuilder,
            lambda: GraphBuilder(node_registry=node_registry),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流工厂（带依赖）
        container.register_factory(
            IWorkflowFactory,
            lambda: WorkflowFactory(container=container, config_loader=config_loader),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流管理器（带依赖）
        container.register_factory(
            IWorkflowManager,
            lambda: WorkflowManager(
                config_loader=config_loader
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
    
    @staticmethod
    def register_test_services(container: IDependencyContainer) -> None:
        """注册测试环境专用服务
        
        Args:
            container: 依赖注入容器
        """
        # 在测试环境中，可以使用Mock实现
        from unittest.mock import Mock
        
        # 注册Mock配置加载器
        mock_config_loader = Mock(spec=IConfigLoader)
        container.register_instance(IConfigLoader, mock_config_loader, "test")
        
        # 注册Mock节点注册表
        mock_node_registry = Mock(spec=NodeRegistry)
        container.register_instance(NodeRegistry, mock_node_registry, "test")
        
        # 注册测试用的工作流管理器
        container.register(
            IWorkflowManager,
            WorkflowManager,
            environment="test",
            lifetime=ServiceLifetime.TRANSIENT
        )
    
    @staticmethod
    def register_development_services(container: IDependencyContainer) -> None:
        """注册开发环境专用服务
        
        Args:
            container: 依赖注入容器
        """
        # 在开发环境中，可以启用额外的调试功能
        container.register_factory(
            GraphBuilder,
            lambda: GraphBuilder(),
            environment="development",
            lifetime=ServiceLifetime.SINGLETON
        )
    
    @staticmethod
    def register_production_services(container: IDependencyContainer) -> None:
        """注册生产环境专用服务
        
        Args:
            container: 依赖注入容器
        """
        # 在生产环境中，可以启用性能优化
        container.register_factory(
            WorkflowFactory,
            lambda: WorkflowFactory(container=container),
            environment="production",
            lifetime=ServiceLifetime.SINGLETON
        )


def configure_workflow_container(
    container: IDependencyContainer,
    environment: str = "default",
    config_loader: Optional[IConfigLoader] = None,
    node_registry: Optional[NodeRegistry] = None
) -> None:
    """配置工作流容器
    
    Args:
        container: 依赖注入容器
        environment: 环境名称
        config_loader: 配置加载器
        node_registry: 节点注册表
    """
    # 设置环境
    container.set_environment(environment)
    
    # 注册基础服务
    WorkflowModule.register_services(container)
    
    # 根据环境注册特定服务
    if environment == "test":
        WorkflowModule.register_test_services(container)
    elif environment == "development":
        WorkflowModule.register_development_services(container)
    elif environment == "production":
        WorkflowModule.register_production_services(container)
    
    # 如果提供了依赖，注册带依赖的服务
    if config_loader and node_registry:
        WorkflowModule.register_services_with_dependencies(
            container, config_loader, node_registry
        )


def get_workflow_manager(container: IDependencyContainer) -> IWorkflowManager:
    """获取工作流管理器
    
    Args:
        container: 依赖注入容器
        
    Returns:
        IWorkflowManager: 工作流管理器实例
    """
    return container.get(IWorkflowManager)


def get_workflow_factory(container: IDependencyContainer) -> IWorkflowFactory:
    """获取工作流工厂
    
    Args:
        container: 依赖注入容器
        
    Returns:
        IWorkflowFactory: 工作流工厂实例
    """
    return container.get(IWorkflowFactory)


def get_state_factory(container: IDependencyContainer) -> StateFactory:
    """获取状态工厂
    
    Args:
        container: 依赖注入容器
        
    Returns:
        StateFactory: 状态工厂实例
    """
    return container.get(StateFactory)


def get_state_serializer(container: IDependencyContainer) -> StateSerializer:
    """获取状态序列化器
    
    Args:
        container: 依赖注入容器
        
    Returns:
        StateSerializer: 状态序列化器实例
    """
    return container.get(StateSerializer)


def get_graph_builder(container: IDependencyContainer) -> GraphBuilder:
    """获取图构建器
    
    Args:
        container: 依赖注入容器
        
    Returns:
        GraphBuilder: 图构建器实例
    """
    return container.get(GraphBuilder)