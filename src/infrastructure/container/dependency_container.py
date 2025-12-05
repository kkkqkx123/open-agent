"""依赖注入容器实现

提供依赖注入容器功能，支持单例、瞬态和作用域生命周期。
"""

import sys
import threading
import time
from typing import Type, TypeVar, Dict, Any, Optional, List, Callable, Iterator, Generator
from contextlib import contextmanager

from src.interfaces.container import (
    IDependencyContainer,
    ILifecycleAware,
)
from src.interfaces.container.core import ServiceRegistration, ServiceLifetime
from src.interfaces.container.exceptions import (
    IExceptionHandler,
    DefaultExceptionHandler,
    RegistrationError,
    ServiceCreationError,
    CircularDependencyError,
    ValidationError,
    ContainerException
)
from src.interfaces.container.testing import (
    ITestContainerManager,
    DefaultTestIsolationStrategy
)
from src.interfaces.configuration import ValidationResult

# 延迟导入logger以避免循环依赖
def _get_logger() -> Optional[Any]:
    try:
        from src.services.logger import get_logger
        return get_logger(__name__)
    except:
        # 如果logger不可用，返回None
        return None

logger = _get_logger()

T = TypeVar('T')


class SimpleServiceCache:
    """简单的服务缓存实现"""
    
    def __init__(self) -> None:
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
    
    def __init__(self) -> None:
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
    
    def __init__(self) -> None:
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
                            if logger:
                                logger.error(f"释放作用域服务失败: {e}")
                            else:
                                print(f"[ERROR] 释放作用域服务失败: {e}", file=sys.stderr)
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
    def scope_context(self) -> Iterator[str]:
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
        
        # 新增：延迟工厂存储
        self._delayed_factories: Dict[Type, Callable[[], Callable[..., Any]]] = {}
        
        # 新增：异常处理器
        self._exception_handler: Optional[IExceptionHandler] = DefaultExceptionHandler(use_system_output=True)
        
        # 新增：测试支持
        self._test_manager: Optional[ITestContainerManager] = None
        self._isolation_strategy = DefaultTestIsolationStrategy()
        
        if logger:
            logger.debug("DependencyContainer初始化完成")
        else:
            print("[INFO] DependencyContainer初始化完成", file=sys.stdout)
    
    def register(
        self,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """注册服务实现"""
        try:
            with self._lock:
                if environment not in self._registrations:
                    self._registrations[environment] = {}
                
                registration = ServiceRegistration(
                    interface=interface,
                    implementation=implementation,
                    lifetime=lifetime,
                    environment=environment,
                    metadata=metadata
                )
                self._registrations[environment][interface] = registration
                
                if logger:
                    logger.debug(f"服务注册: {interface.__name__} -> {implementation.__name__}, lifetime: {lifetime}")
        except Exception as e:
            registration_error = RegistrationError(
                f"服务注册失败: {e}",
                interface.__name__
            )
            self._handle_exception(registration_error, f"register({interface.__name__})")
            raise
    
    def register_factory(
        self,
        interface: Type,
        factory: Callable[[], Any],
        environment: str = "default",
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """注册服务工厂"""
        try:
            with self._lock:
                if environment not in self._registrations:
                    self._registrations[environment] = {}
                
                registration = ServiceRegistration(
                    interface=interface,
                    factory=factory,
                    lifetime=lifetime,
                    environment=environment,
                    metadata=metadata
                )
                self._registrations[environment][interface] = registration
                
                if logger:
                    logger.debug(f"工厂注册: {interface.__name__}, lifetime: {lifetime}")
        except Exception as e:
            registration_error = RegistrationError(
                f"工厂注册失败: {e}",
                interface.__name__
            )
            self._handle_exception(registration_error, f"register_factory({interface.__name__})")
            raise
    
    def register_instance(
        self,
        interface: Type,
        instance: Any,
        environment: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """注册服务实例"""
        try:
            with self._lock:
                if environment not in self._registrations:
                    self._registrations[environment] = {}
                
                registration = ServiceRegistration(
                    interface=interface,
                    instance=instance,
                    lifetime=ServiceLifetime.SINGLETON,  # 实例默认为单例
                    environment=environment,
                    metadata=metadata
                )
                self._registrations[environment][interface] = registration
                
                # 对于实例注册，直接放入实例缓存
                self._instances[interface] = instance
                
                if logger:
                    logger.debug(f"实例注册: {interface.__name__}")
        except Exception as e:
            registration_error = RegistrationError(
                f"实例注册失败: {e}",
                interface.__name__
            )
            self._handle_exception(registration_error, f"register_instance({interface.__name__})")
            raise
    
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
        elif registration.lifetime == ServiceLifetime.SCOPED:
            current_scope_id = self._scope_manager.get_current_scope_id()
            if current_scope_id:
                instance = self._scope_manager.get_scoped_instance(current_scope_id, service_type)
        
        # 如果还没有实例，创建新实例
        if instance is None:
            instance = self._create_instance(registration)
            
            # 根据生命周期存储实例
            if registration.lifetime == ServiceLifetime.SINGLETON:
                self._instances[service_type] = instance
            elif registration.lifetime == ServiceLifetime.SCOPED:
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
                    if logger:
                        logger.error(f"服务初始化失败: {service_type.__name__}, 错误: {e}")
                    else:
                        print(f"[ERROR] 服务初始化失败: {service_type.__name__}, 错误: {e}", file=sys.stderr)
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
                            if logger:
                                logger.warning(f"无法解析依赖 {param.annotation}，参数 {name}")
                            else:
                                print(f"[WARNING] 无法解析依赖 {param.annotation}，参数 {name}", file=sys.stderr)
            
            try:
                instance = impl_class(**params)
            except TypeError:
                # 如果参数注入失败，尝试无参构造
                try:
                    instance = impl_class()
                except Exception as e:
                    if logger:
                        logger.error(f"创建服务实例失败: {impl_class.__name__}, 错误: {e}")
                    else:
                        print(f"[ERROR] 创建服务实例失败: {impl_class.__name__}, 错误: {e}", file=sys.stderr)
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
            if logger:
                logger.debug(f"环境设置为: {env}")
            else:
                print(f"[INFO] 环境设置为: {env}", file=sys.stdout)
    
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
            if logger:
                logger.debug("DependencyContainer已清除")
            else:
                print("[INFO] DependencyContainer已清除", file=sys.stdout)
    
    def try_get(self, service_type: Type[T]) -> Optional[T]:
        """尝试获取服务实例，如果不存在返回None"""
        try:
            return self.get(service_type)
        except (ValueError, Exception):
            return None
    
    def validate_configuration(self) -> ValidationResult:
        """验证容器配置"""
        errors: List[str] = []
        warnings: List[str] = []
        
        # 验证所有注册的服务
        for environment, registrations in self._registrations.items():
            for interface, registration in registrations.items():
                # 验证注册信息
                reg_errors = []
                
                # 检查至少有一种实现方式
                if not any([registration.implementation, registration.factory, registration.instance]):
                    reg_errors.append(f"必须提供 implementation、factory 或 instance 中的一个 (环境: {environment}, 接口: {interface.__name__})")
                
                # 检查不能同时提供多种实现方式
                impl_count = sum([
                    1 for item in [registration.implementation, registration.factory, registration.instance]
                    if item is not None
                ])
                if impl_count > 1:
                    reg_errors.append(f"只能提供 implementation、factory 或 instance 中的一种 (环境: {environment}, 接口: {interface.__name__})")
                
                errors.extend(reg_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_registration_count(self) -> int:
        """获取注册的服务数量"""
        count = 0
        for registrations in self._registrations.values():
            count += len(registrations)
        return count
    
    def get_registered_services(self) -> List[Type]:
        """获取已注册的服务类型列表"""
        services: List[Type] = []
        for registrations in self._registrations.values():
            services.extend(registrations.keys())
        # 返回唯一的服务类型
        return list(set(services))
    
    def register_factory_with_delayed_resolution(
        self,
        interface: Type,
        factory_factory: Callable[[], Callable[..., Any]],
        environment: str = "default",
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None: 
        """注册延迟解析的工厂工厂"""
        with self._lock:
            if environment not in self._registrations:
                self._registrations[environment] = {}
            
            # 存储工厂工厂而不是工厂
            self._delayed_factories[interface] = factory_factory
            
            # 注册一个代理工厂
            def delayed_factory():
                try:
                    actual_factory = factory_factory()
                    return actual_factory()
                except Exception as e:
                    creation_error = ServiceCreationError(
                        f"延迟工厂创建失败: {e}",
                        interface.__name__
                    )
                    self._handle_exception(creation_error, f"delayed_factory({interface.__name__})")
                    raise
            
            registration = ServiceRegistration(
                interface=interface,
                factory=delayed_factory,
                lifetime=lifetime,
                environment=environment,
                metadata=metadata
            )
            self._registrations[environment][interface] = registration
            
            if logger:
                logger.debug(f"延迟工厂注册: {interface.__name__}, lifetime: {lifetime.value}")
    
    def resolve_dependencies(self, service_types: List[Type]) -> Dict[Type, Any]:
        """批量解析依赖"""
        results: Dict[Type, Any] = {}
        resolution_chain: List[Type] = []
        
        try:
            for service_type in service_types:
                if service_type in resolution_chain:
                    # 检测到循环依赖
                    chain_str = " -> ".join(t.__name__ for t in resolution_chain + [service_type])
                    circular_error = CircularDependencyError(
                        f"检测到循环依赖: {chain_str}",
                        [t.__name__ for t in resolution_chain + [service_type]]
                    )
                    self._handle_exception(circular_error, "resolve_dependencies")
                    raise
                
                resolution_chain.append(service_type)
                try:
                    results[service_type] = self.get(service_type)
                except Exception as e:
                    creation_error = ServiceCreationError(
                        f"服务解析失败: {e}",
                        service_type.__name__
                    )
                    self._handle_exception(creation_error, f"resolve_dependencies({service_type.__name__})")
                    raise
                finally:
                    resolution_chain.pop()
                    
        except Exception as e:
            if not isinstance(e, CircularDependencyError):
                # 如果不是循环依赖错误，重新抛出
                raise
        
        return results
    
    def set_exception_handler(self, handler: IExceptionHandler) -> None:
        """设置异常处理器"""
        self._exception_handler = handler
    
    def set_test_manager(self, manager: ITestContainerManager) -> None:
        """设置测试管理器"""
        self._test_manager = manager
    
    def create_test_isolation(self, isolation_id: Optional[str] = None) -> 'DependencyContainer':
        """创建测试隔离容器"""
        test_container = DependencyContainer(environment=f"test_{isolation_id or 'default'}")
        
        # 复制当前容器的注册信息到测试容器
        for env, registrations in self._registrations.items():
            if env.startswith("test_"):
                continue  # 跳过其他测试环境
            test_container._registrations[env] = registrations.copy()
        
        # 复制延迟工厂
        test_container._delayed_factories = self._delayed_factories.copy()
        
        # 设置相同的异常处理器
        test_container._exception_handler = self._exception_handler
        
        return test_container
    
    def reset_test_state(self, isolation_id: Optional[str] = None) -> None:
        """重置测试状态"""
        test_env = f"test_{isolation_id or 'default'}"
        if test_env in self._registrations:
            del self._registrations[test_env]
        
        # 清理测试相关的实例
        test_instances = {
            service_type: instance
            for service_type, instance in self._instances.items()
            if hasattr(instance, '_test_isolation')
        }
        for service_type in test_instances:
            del self._instances[service_type]
    
    def copy_registrations(self, target_container: 'DependencyContainer') -> None:
        """复制注册信息到目标容器"""
        with self._lock:
            for env, registrations in self._registrations.items():
                if env not in target_container._registrations:
                    target_container._registrations[env] = {}
                target_container._registrations[env].update(registrations.copy())
            
            # 复制延迟工厂
            target_container._delayed_factories.update(self._delayed_factories.copy())
    
    def _handle_exception(self, exception: Exception, context: str) -> None:
        """统一异常处理"""
        if self._exception_handler:
            if isinstance(exception, RegistrationError):
                handled = self._exception_handler.handle_registration_error(exception, context)
            elif isinstance(exception, ServiceCreationError):
                handled = self._exception_handler.handle_creation_error(exception, context)
            elif isinstance(exception, CircularDependencyError):
                handled = self._exception_handler.handle_circular_dependency_error(exception)
            elif isinstance(exception, ValidationError):
                handled = self._exception_handler.handle_validation_error(exception)
            else:
                handled = False
            
            if not handled:
                # 如果异常未被处理，使用默认方式
                if logger:
                    logger.error(f"{context}: {exception}")
                else:
                    print(f"[ERROR] {context}: {exception}", file=sys.stderr)
        else:
            # 默认处理：使用系统标准输出避免循环依赖
            if logger:
                logger.error(f"{context}: {exception}")
            else:
                print(f"[ERROR] {context}: {exception}", file=sys.stderr)


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