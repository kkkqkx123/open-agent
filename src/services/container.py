"""服务层容器模块

提供服务层的依赖注入容器功能。
"""

from typing import TypeVar, Type, Any, Optional, Dict, List
from enum import Enum, auto

from src.infrastructure.container import get_global_container, IDependencyContainer


class ServiceLifetime(Enum):
    """服务生命周期枚举"""
    SINGLETON = auto()
    TRANSIENT = auto()
    SCOPED = auto()


# 创建全局容器实例
container = get_global_container()


def register_service(
    service_type: Type,
    implementation_type: Optional[Type] = None,
    instance: Optional[Any] = None,
    factory: Optional[callable] = None,
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
) -> None:
    """注册服务到容器
    
    Args:
        service_type: 服务接口类型
        implementation_type: 实现类型
        instance: 实例对象
        factory: 工厂函数
        lifetime: 生命周期
    """
    if instance is not None:
        container.register_instance(service_type, instance)
    elif factory is not None:
        container.register_factory(service_type, factory)
    elif implementation_type is not None:
        container.register(service_type, implementation_type, lifetime.value)
    else:
        raise ValueError("必须提供 implementation_type, instance 或 factory 中的一个")


def get_service(service_type: Type) -> Any:
    """从容器获取服务
    
    Args:
        service_type: 服务类型
        
    Returns:
        服务实例
    """
    return container.get(service_type)


def is_service_registered(service_type: Type) -> bool:
    """检查服务是否已注册
    
    Args:
        service_type: 服务类型
        
    Returns:
        是否已注册
    """
    return container.is_registered(service_type)


# 导出接口
__all__ = [
    "ServiceLifetime",
    "container",
    "register_service",
    "get_service",
    "is_service_registered",
    "IDependencyContainer",
    "get_global_container"
]