"""
依赖注入容器实现

提供依赖注入容器功能，支持单例、瞬态和作用域生命周期。
"""

import threading
from typing import Type, TypeVar, Dict, Any, Optional, Callable

from src.interfaces.container.core import (
    IDependencyContainer,
    ServiceLifetime
)

T = TypeVar('T')

class ServiceRegistration:
    """服务注册信息"""
    
    def __init__(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable[[], Any]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ):
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.lifetime = lifetime

class DependencyContainer(IDependencyContainer):
    """依赖注入容器实现"""
    
    def __init__(self):
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
    
    def register(
        self,
        interface: Type,
        implementation: Type,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> None:
        """注册服务实现"""
        with self._lock:
            registration = ServiceRegistration(
                interface=interface,
                implementation=implementation,
                lifetime=lifetime
            )
            self._registrations[interface] = registration
    
    def register_factory(
        self,
        interface: Type,
        factory: Callable[[], Any],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> None:
        """注册服务工厂"""
        with self._lock:
            registration = ServiceRegistration(
                interface=interface,
                factory=factory,
                lifetime=lifetime
            )
            self._registrations[interface] = registration
    
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        with self._lock:
            if service_type not in self._registrations:
                raise ValueError(f"服务未注册: {service_type.__name__}")
            
            registration = self._registrations[service_type]
            
            # 单例模式检查缓存
            if registration.lifetime == ServiceLifetime.SINGLETON:
                if service_type in self._instances:
                    return self._instances[service_type]
            
            # 创建实例
            if registration.factory:
                instance = registration.factory()
            elif registration.implementation:
                instance = registration.implementation()
            else:
                raise ValueError(f"注册信息不完整: {service_type.__name__}")
            
            # 缓存单例实例
            if registration.lifetime == ServiceLifetime.SINGLETON:
                self._instances[service_type] = instance
            
            return instance
    
    def has_service(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._registrations