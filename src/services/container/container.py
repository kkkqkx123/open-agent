"""依赖注入容器实现

提供依赖注入容器功能，支持单例、瞬态和作用域生命周期。
"""

import logging
import threading
import time
from typing import Type, TypeVar, Dict, Any, Optional, List, Callable, ContextManager
from contextlib import contextmanager
from enum import Enum

from src.interfaces.container import (
    IDependencyContainer, 
    ILifecycleAware, 
    ServiceStatus, 
    IServiceTracker, 
    IServiceCache,
    IPerformanceMonitor,
    IScopeManager
)
from src.core.common.types import ServiceLifetime


logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceRegistration:
    """服务注册信息"""
    def __init__(
        self, 
        interface: Type, 
        implementation: Optional[Type] = None, 
        factory: Optional[Callable[[], Any]] = None, 
        instance: Optional[Any] = None,
        lifetime: str = ServiceLifetime.SINGLETON
    ):
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        self.created_at = time.time()


class SimpleServiceCache:
    """简单的服务缓存实现"""
    
    def __init__(self):
        self._cache: Dict[Type, Any] = {}
        self._lock = threading.RLock()
    
    def get(self, service_type: Type) -> Optional[Any]:
        with self._lock:
            return self._cache.get(service_type)
    
    def put(self, service_type: Type, instance: Any) -> None:
        with self._lock:
            self._cache[service_type] = instance
    
    def remove(self, service_type: Type) -> None:
        with self._lock:
            if service_type in self._cache:
                del self._cache[service_type]
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
    
    def optimize(self) -> Dict[str, Any]:
        with self._lock:
            return {"size": len(self._cache)}
    
    def get_size(self) -> int:
        with self._lock:
            return len(self._cache)
    
    def get_memory_usage(self) -> int:
        with self._lock:
            # 简单估算内存使用
            return len(self._cache) * 1024  # 每个实例估算1KB


class SimplePerformanceMonitor:
    """简单的性能监控实现"""
    
    def __init__(self):
        self._resolution_times: Dict[Type, List[float]] = {}
        self._cache_hits: Dict[Type, int] = {}
        self._cache_misses: Dict[Type, int] = {}
        self._lock = threading.RLock()
    
    def record_resolution(self, service_type: Type, start_time: float, end_time: float) -> None:
        with self._lock:
            duration = end_time - start_time
            if service_type not in self._resolution_times:
                self._resolution_times[service_type] = []
            self._resolution_times[service_type].append(duration)
    
    def record_cache_hit(self, service_type: Type) -> None:
        with self._lock:
            self._cache_hits[service_type] = self._cache_hits.get(service_type, 0) + 1
    
    def record_cache_miss(self, service_type: Type) -> None:
        with self._lock:
            self._cache_misses[service_type] = self._cache_misses.get(service_type, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_resolutions = sum(len(times) for times in self._resolution_times.values())
            total_hits = sum(self._cache_hits.values())
            total_misses = sum(self._cache_misses.values())
            
            avg_resolution_times = {}
            for service_type, times in self._resolution_times.items():
                if times:
                    avg_resolution_times[service_type.__name__] = sum(times) / len(times)
            
            return {
                "total_resolutions": total_resolutions,
                "total_cache_hits": total_hits,
                "total_cache_misses": total_misses,
                "average_resolution_times": avg_resolution_times,
                "cache_hit_rate": total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
            }


class SimpleScopeManager:
    """简单的作用域管理器实现"""
    
    def __init__(self):
        self._scopes: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: threading.local = threading.local()
        self._lock = threading.RLock()
    
    def create_scope(self) -> str:
        import uuid
        scope_id = str(uuid.uuid4())
        with self._lock:
            self._scopes[scope_id] = {}
        return scope_id
    
    def dispose_scope(self, scope_id: str) -> None:
        with self._lock:
            if scope_id in self._scopes:
                # 释放作用域中的服务实例
                for instance in self._scopes[scope_id].values():
                    if isinstance(instance, ILifecycleAware):
                        try:
                            instance.dispose()
                        except Exception as e:
                            logger.error(f"释放作用域服务失败: {e}")
                del self._scopes[scope_id]
    
    def get_current_scope_id(self) -> Optional[str]:
        return getattr(self._current_scope, 'scope_id', None)
    
    def set_current_scope_id(self, scope_id: Optional[str]) -> None:
        if scope_id is None:
            if hasattr(self._current_scope, 'scope_id'):
                delattr(self._current_scope, 'scope_id')
        else:
            self._current_scope.scope_id = scope_id
    
    def get_scoped_instance(self, scope_id: str, service_type: Type) -> Optional[Any]:
        with self._lock:
            if scope_id in self._scopes:
                return self._scopes[scope_id].get(service_type)
            return None
    
    def set_scoped_instance(self, scope_id: str, service_type: Type, instance: Any) -> None:
        with self._lock:
            if scope_id in self._scopes:
                self._scopes[scope_id][service_type] = instance
    
    @contextmanager
    def scope_context(self) -> ContextManager[str]:
        scope_id = self.create_scope()
        old_scope_id = self.get_current_scope_id()
        self.set_current_scope_id(scope_id)
        try:
            yield scope_id
        finally:
            self.set_current_scope_id(old_scope_id)
            self.dispose_scope(scope_id)


class DependencyContainer(IDependencyContainer):
    """依赖注入容器实现"""
    
    def __init__(self, environment: str = "default"):
        self._registrations: Dict[str, Dict[Type, ServiceRegistration]] = {"default": {}}
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._environment = environment
        self._service_cache = SimpleServiceCache()
        self._performance_monitor = SimplePerformanceMonitor()
        self._scope_manager = SimpleScopeManager()
        
        logger.debug("DependencyContainer初始化完成")
    
    def register(
        self,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务实现"""
        with self._lock:
            if environment not in self._registrations:
                self._registrations[environment] = {}
            
            registration = ServiceRegistration(
                interface=interface,
                implementation=implementation,
                lifetime=lifetime
            )
            self._registrations[environment][interface] = registration
            logger.debug(f"服务注册: {interface.__name__} -> {implementation.__name__}, lifetime: {lifetime}")
    
    def register_factory(
        self,
        interface: Type,
        factory: Callable[[], Any],
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务工厂"""
        with self._lock:
            if environment not in self._registrations:
                self._registrations[environment] = {}
            
            registration = ServiceRegistration(
                interface=interface,
                factory=factory,
                lifetime=lifetime
            )
            self._registrations[environment][interface] = registration
            logger.debug(f"工厂注册: {interface.__name__}, lifetime: {lifetime}")
    
    def register_instance(
        self, interface: Type, instance: Any, environment: str = "default"
    ) -> None:
        """注册服务实例"""
        with self._lock:
            if environment not in self._registrations:
                self._registrations[environment] = {}
            
            registration = ServiceRegistration(
                interface=interface,
                instance=instance,
                lifetime=ServiceLifetime.SINGLETON  # 实例默认为单例
            )
            self._registrations[environment][interface] = registration
            
            # 对于实例注册，直接放入实例缓存
            self._instances[interface] = instance
            logger.debug(f"实例注册: {interface.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        start_time = time.time()
        
        # 检查当前环境的注册
        environment_registrations = self._registrations.get(self._environment, {})
        if service_type not in environment_registrations:
            # 尝试默认环境
            environment_registrations = self._registrations.get("default", {})
        
        if service_type not in environment_registrations:
            raise ValueError(f"服务未注册: {service_type.__name__}")
        
        registration = environment_registrations[service_type]
        
        # 根据生命周期处理服务实例
        instance = None
        
        # 首先检查单例缓存
        if registration.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._instances:
                instance = self._instances[service_type]
        
        # 如果是作用域生命周期，检查当前作用域
        elif registration.lifetime == ServiceLifetime.SCOPE:
            current_scope_id = self._scope_manager.get_current_scope_id()
            if current_scope_id:
                instance = self._scope_manager.get_scoped_instance(current_scope_id, service_type)
        
        # 如果还没有实例，创建新实例
        if instance is None:
            instance = self._create_instance(registration)
            
            # 根据生命周期存储实例
            if registration.lifetime == ServiceLifetime.SINGLETON:
                self._instances[service_type] = instance
            elif registration.lifetime == ServiceLifetime.SCOPE:
                current_scope_id = self._scope_manager.get_current_scope_id()
                if current_scope_id:
                    self._scope_manager.set_scoped_instance(current_scope_id, service_type, instance)
        
        # 初始化生命周期感知服务
        if isinstance(instance, ILifecycleAware):
            if not hasattr(instance, '_initialized') or not instance._initialized:
                try:
                    instance.initialize()
                    instance._initialized = True
                except Exception as e:
                    logger.error(f"服务初始化失败: {service_type.__name__}, 错误: {e}")
                    raise
        
        end_time = time.time()
        self._performance_monitor.record_resolution(service_type, start_time, end_time)
        
        return instance  # type: ignore
    
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """创建服务实例"""
        if registration.instance is not None:
            # 已注册实例，直接返回
            return registration.instance
        
        if registration.factory is not None:
            # 使用工厂创建实例
            return registration.factory()
        
        if registration.implementation is not None:
            # 使用实现类创建实例
            impl_class = registration.implementation
            
            # 检查构造函数参数并尝试注入依赖
            import inspect
            sig = inspect.signature(impl_class.__init__)
            params = {}
            
            for name, param in sig.parameters.items():
                if name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    try:
                        # 尝试从容器获取依赖
                        dependency = self.get(param.annotation)
                        params[name] = dependency
                    except ValueError:
                        # 如果依赖未注册，使用默认值或跳过
                        if param.default != inspect.Parameter.empty:
                            params[name] = param.default
                        else:
                            logger.warning(f"无法解析依赖 {param.annotation}，参数 {name}")
            
            try:
                instance = impl_class(**params)
            except TypeError:
                # 如果参数注入失败，尝试无参构造
                try:
                    instance = impl_class()
                except Exception as e:
                    logger.error(f"创建服务实例失败: {impl_class.__name__}, 错误: {e}")
                    raise
            
            return instance
        
        raise ValueError(f"注册信息不完整: {registration.interface.__name__}")
    
    def get_environment(self) -> str:
        """获取当前环境"""
        return self._environment
    
    def set_environment(self, env: str) -> None:
        """设置当前环境"""
        with self._lock:
            self._environment = env
            logger.debug(f"环境设置为: {env}")
    
    def has_service(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        environment_registrations = self._registrations.get(self._environment, {})
        if service_type not in environment_registrations:
            environment_registrations = self._registrations.get("default", {})
        
        return service_type in environment_registrations
    
    def clear(self) -> None:
        """清除所有服务和缓存"""
        with self._lock:
            self._registrations = {"default": {}}
            self._instances.clear()
            self._service_cache.clear()
            logger.debug("DependencyContainer已清除")


# 全局容器实例
_global_container: Optional[DependencyContainer] = None
_global_lock = threading.Lock()


def get_global_container() -> DependencyContainer:
    """获取全局容器实例"""
    global _global_container
    if _global_container is None:
        with _global_lock:
            if _global_container is None:
                _global_container = DependencyContainer()
    return _global_container


def reset_global_container() -> None:
    """重置全局容器实例"""
    global _global_container
    with _global_lock:
        _global_container = None