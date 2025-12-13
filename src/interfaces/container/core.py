"""
依赖注入容器核心接口

定义容器的基础数据类型和核心接口。
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Callable, Dict, Any, Optional
from enum import Enum

T = TypeVar('T')

class ServiceLifetime(Enum):
    """服务生命周期"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class IDependencyContainer(ABC):
    """依赖注入容器接口"""
    
    @abstractmethod
    def register(
        self,
        interface: Type,
        implementation: Type,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> None:
        """注册服务实现"""
        pass
    
    @abstractmethod
    def register_factory(
        self,
        interface: Type,
        factory: Callable[[], Any],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> None:
        """注册服务工厂"""
        pass
    
    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        pass
    
    @abstractmethod
    def has_service(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        pass