"""LLM模块依赖注入配置"""

from ..container_interfaces import IDependencyContainer, ServiceLifetime
from ..config.interfaces import IConfigLoader
from .task_group_manager import TaskGroupManager


def register_task_group_services(
    container: IDependencyContainer,
    config_loader: IConfigLoader
) -> None:
    """注册任务组相关服务
    
    Args:
        container: 依赖注入容器
        config_loader: 配置加载器
    """
    # 注册任务组管理器
    container.register_factory(
        interface=TaskGroupManager,
        factory=lambda: TaskGroupManager(config_loader),
        lifetime=ServiceLifetime.SINGLETON
    )


def register_llm_enhanced_services(
    container: IDependencyContainer,
    config_loader: IConfigLoader
) -> None:
    """注册LLM增强服务
    
    Args:
        container: 依赖注入容器
        config_loader: 配置加载器
    """
    # 注册任务组服务
    register_task_group_services(container, config_loader)
    
    # TODO: 注册轮询池管理器
    # TODO: 注册并发控制器
    # TODO: 注册限流器