"""通用依赖注入便利层基础框架

提供统一的服务注入机制，支持缓存、降级和测试隔离。
"""

import threading
from typing import TypeVar, Type, Optional, Callable, Any, Dict, Generic
from abc import ABC, abstractmethod

T = TypeVar('T')


class ServiceInjectionBase(ABC, Generic[T]):
    """服务注入基类
    
    提供统一的服务获取机制，支持缓存、容器查找和降级处理。
    """
    
    def __init__(self, service_type: Type[T], fallback_factory: Optional[Callable[[], T]] = None):
        self._service_type = service_type
        self._fallback_factory = fallback_factory
        self._instance: Optional[T] = None
        self._lock = threading.RLock()  # 使用可重入锁
        self._initialized = False
        self._container_fallback_enabled = True
    
    def set_instance(self, instance: T) -> None:
        """设置全局实例
        
        Args:
            instance: 服务实例
        """
        with self._lock:
            self._instance = instance
            self._initialized = True
    
    def get_instance(self) -> T:
        """获取服务实例
        
        获取策略：
        1. 返回缓存实例（最快）
        2. 从容器获取并缓存
        3. 使用fallback工厂
        4. 抛出异常
        
        Returns:
            服务实例
            
        Raises:
            RuntimeError: 无法获取服务实例时
        """
        # 1. 返回缓存实例
        if self._instance is not None:
            return self._instance
        
        with self._lock:
            # 双重检查锁定模式
            if self._instance is not None:
                return self._instance
            
            # 2. 从容器获取
            if self._container_fallback_enabled:
                try:
                    from src.services.container import get_global_container
                    container = get_global_container()
                    if container.has_service(self._service_type):
                        instance = container.get(self._service_type)
                        self.set_instance(instance)  # 缓存
                        return instance
                except Exception:
                    # 容器获取失败，继续尝试fallback
                    pass
            
            # 3. 使用fallback工厂
            if self._fallback_factory is not None:
                try:
                    instance = self._fallback_factory()
                    self.set_instance(instance)
                    return instance
                except Exception as e:
                    raise RuntimeError(f"Fallback工厂创建实例失败: {e}")
            
            # 4. 无法获取实例
            raise RuntimeError(f"无法获取服务实例: {self._service_type.__name__}")
    
    def clear_instance(self) -> None:
        """清除全局实例（主要用于测试）"""
        with self._lock:
            self._instance = None
            self._initialized = False
    
    def disable_container_fallback(self) -> None:
        """禁用容器降级（主要用于测试）"""
        with self._lock:
            self._container_fallback_enabled = False
    
    def enable_container_fallback(self) -> None:
        """启用容器降级"""
        with self._lock:
            self._container_fallback_enabled = True
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    @property
    def service_type(self) -> Type[T]:
        """获取服务类型"""
        return self._service_type
    
    def get_status(self) -> Dict[str, Any]:
        """获取注入状态信息"""
        with self._lock:
            return {
                "service_type": self._service_type.__name__,
                "initialized": self._initialized,
                "has_instance": self._instance is not None,
                "container_fallback_enabled": self._container_fallback_enabled,
                "has_fallback_factory": self._fallback_factory is not None
            }


class ServiceInjectionRegistry:
    """服务注入注册表
    
    管理所有服务的注入实例，提供统一的注册和获取接口。
    """
    
    def __init__(self):
        self._injections: Dict[Type, ServiceInjectionBase] = {}
        self._lock = threading.RLock()
    
    def register(self, service_type: Type[T], fallback_factory: Optional[Callable[[], T]] = None) -> ServiceInjectionBase[T]:
        """注册服务注入
        
        Args:
            service_type: 服务类型
            fallback_factory: fallback工厂函数
            
        Returns:
            服务注入实例
        """
        with self._lock:
            if service_type not in self._injections:
                injection = ServiceInjectionBase(service_type, fallback_factory)
                self._injections[service_type] = injection
            return self._injections[service_type]
    
    def get_injection(self, service_type: Type[T]) -> ServiceInjectionBase[T]:
        """获取服务注入
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务注入实例
            
        Raises:
            ValueError: 服务类型未注册
        """
        with self._lock:
            if service_type not in self._injections:
                raise ValueError(f"服务类型未注册: {service_type.__name__}")
            return self._injections[service_type]
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """检查服务类型是否已注册"""
        with self._lock:
            return service_type in self._injections
    
    def unregister(self, service_type: Type[T]) -> None:
        """注销服务类型"""
        with self._lock:
            if service_type in self._injections:
                del self._injections[service_type]
    
    def clear_all(self) -> None:
        """清除所有实例（测试用）"""
        with self._lock:
            for injection in self._injections.values():
                injection.clear_instance()
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有注入状态"""
        with self._lock:
            return {
                service_type.__name__: injection.get_status()
                for service_type, injection in self._injections.items()
            }
    
    def get_registered_types(self) -> list[Type]:
        """获取已注册的服务类型列表"""
        with self._lock:
            return list(self._injections.keys())


# 全局注册表实例
_global_injection_registry = ServiceInjectionRegistry()


def get_global_injection_registry() -> ServiceInjectionRegistry:
    """获取全局注入注册表
    
    Returns:
        全局注入注册表实例
    """
    return _global_injection_registry


def clear_all_injections() -> None:
    """清除所有注入实例（测试用）"""
    get_global_injection_registry().clear_all()


def get_injection_status() -> Dict[str, Dict[str, Any]]:
    """获取所有注入状态信息
    
    Returns:
        状态信息字典
    """
    return get_global_injection_registry().get_all_status()