"""增强的依赖注入容器实现

提供更完善的生命周期管理和循环依赖检测功能。
"""

import threading
import time
import logging
import sys
from typing import Type, TypeVar, Dict, Any, Optional, List, Set, Callable
from contextlib import contextmanager
from inspect import signature

from ..container_interfaces import (
    IDependencyContainer,
    IServiceCache,
    IPerformanceMonitor,
    IDependencyAnalyzer,
    IScopeManager,
    IServiceTracker,
    ServiceStatus,
    ILifecycleAware,
    ServiceRegistration
)
from ..cache.service_cache import LRUServiceCache
from ..container.performance_monitor_adapter import ContainerPerformanceMonitor
from ..container.dependency_analyzer import DependencyAnalyzer
from ..container.scope_manager import ScopeManager
from ..container.base_container import BaseDependencyContainer
from ..monitoring.performance_monitor import PerformanceMonitor
from ..types import ServiceLifetime, T
from ..exceptions import (
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
)

logger = logging.getLogger(__name__)


class EnhancedDependencyContainer(BaseDependencyContainer):
    """增强的依赖注入容器
    
    提供以下增强功能：
    1. 服务实例缓存
    2. 性能监控
    3. 依赖分析
    4. 作用域管理
    """
    
    def __init__(
        self,
        service_cache: Optional[IServiceCache] = None,
        performance_monitor: Optional[IPerformanceMonitor] = None,
        dependency_analyzer: Optional[IDependencyAnalyzer] = None,
        scope_manager: Optional[IScopeManager] = None,
        service_tracker: Optional[IServiceTracker] = None,
        enable_tracking: bool = False,
        enable_service_cache: bool = True,
        enable_path_cache: bool = True,
        max_cache_size: int = 1000,
        cache_ttl_seconds: int = 3600
    ):
        """初始化增强的依赖注入容器
        
        Args:
            service_cache: 服务缓存
            performance_monitor: 性能监控器
            dependency_analyzer: 依赖分析器
            scope_manager: 作用域管理器
            service_tracker: 服务跟踪器
            enable_tracking: 是否启用服务跟踪
            enable_service_cache: 是否启用服务缓存
            enable_path_cache: 是否启用路径缓存
            max_cache_size: 最大缓存大小
            cache_ttl_seconds: 缓存过期时间
        """
        # 初始化基础容器
        super().__init__(service_tracker)
        
        # 增强功能
        self._service_cache = service_cache or LRUServiceCache(max_size=max_cache_size, ttl_seconds=cache_ttl_seconds)
        self._performance_monitor = performance_monitor or ContainerPerformanceMonitor(PerformanceMonitor())
        self._dependency_analyzer = dependency_analyzer or DependencyAnalyzer()
        self._scope_manager = scope_manager or ScopeManager()
        self._enable_tracking = enable_tracking
        self._enable_service_cache = enable_service_cache
        self._enable_path_cache = enable_path_cache
        self._max_cache_size = max_cache_size
        self._cache_ttl_seconds = cache_ttl_seconds
        
        # 创建路径缓存
        self._creation_path_cache: Dict[Type, List[Type]] = {}
        self._path_cache_lock = threading.RLock()
        
        # 作用域管理
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        
        # 性能统计
        self._performance_stats = {
            "total_resolutions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "service_creations": 0,
            "total_creation_time": 0.0,
            "average_creation_time": 0.0,
        }
        
        logger.debug("EnhancedDependencyContainer初始化完成")
    
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例（增强版本）
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        start_time = time.time()
        self._performance_stats["total_resolutions"] += 1
        
        # 检查服务缓存
        if self._enable_service_cache:
            cached_instance = self._get_from_cache(service_type)
            if cached_instance is not None:
                self._performance_stats["cache_hits"] += 1
                self._performance_monitor.record_cache_hit(service_type)
                return cached_instance
            self._performance_stats["cache_misses"] += 1
            self._performance_monitor.record_cache_miss(service_type)
        
        # 检查服务是否已注册
        registration = self._find_registration(service_type)
        if registration is None:
            raise ServiceNotRegisteredError(f"Service {service_type} not registered")
        
        # 如果注册了实例，直接返回注册的实例
        if registration.instance is not None:
            return registration.instance  # type: ignore
        
        try:
            # 检测循环依赖（增强版）
            self._check_circular_dependency(service_type)
            
            # 创建服务实例
            instance = self._create_instance(service_type, registration)
            
            # 缓存服务实例（仅对单例和作用域服务，且不是实例注册）
            if self._enable_service_cache and registration.lifetime != ServiceLifetime.TRANSIENT:
                self._add_to_cache(service_type, instance)
            
            # 记录性能指标
            end_time = time.time()
            creation_time = end_time - start_time
            self._performance_stats["total_creation_time"] += creation_time
            self._performance_stats["service_creations"] += 1
            self._performance_stats["average_creation_time"] = (
                self._performance_stats["total_creation_time"] /
                self._performance_stats["service_creations"]
            )
            self._performance_monitor.record_resolution(service_type, start_time, end_time)
            
            return instance
            
        except CircularDependencyError:
            # 如果是循环依赖错误，直接抛出，不要包装
            raise
        except Exception as e:
            raise ServiceCreationError(f"Failed to get service {service_type.__name__}: {e}")
    
    def set_environment(self, env: str) -> None:
        """设置当前环境"""
        with self._lock:
            if env != self._environment:
                self._environment = env
                # 清除单例缓存和所有其他缓存，因为环境改变可能需要不同的实现
                self._instances.clear()
                self._service_cache.clear()
                self._creation_path_cache.clear()
                logger.debug(f"环境设置为: {env}")
    
    def create_scope(self) -> str:
        """创建新的作用域
        
        Returns:
            str: 作用域ID
        """
        return self._scope_manager.create_scope()
    
    def dispose_scope(self, scope_id: str) -> None:
        """释放作用域
        
        Args:
            scope_id: 作用域ID
        """
        self._scope_manager.dispose_scope(scope_id)
    
    @contextmanager
    def scope(self):
        """作用域上下文管理器"""
        with self._scope_manager.scope_context() as scope_id:
            yield scope_id
    
    def get_registered_services(self) -> List[Type]:
        """获取已注册的服务列表
        
        Returns:
            已注册的服务类型列表
        """
        with self._lock:
            services = list(self._services.keys())
            # 添加环境特定的服务
            for service_type, env_services in self._environment_services.items():
                services.append(service_type)
            # 去重
            return list(set(services))
    
    def clear(self) -> None:
        """清除所有服务和缓存"""
        with self._lock:
            # 释放所有实例
            self._dispose_all_instances()
            
            # 清除注册和缓存
            self._services.clear()
            self._environment_services.clear()
            self._instances.clear()
            self._scoped_instances.clear()
            self._service_status.clear()
            self._initialization_order.clear()
            self._creation_stack.clear()
            
            # 清除缓存
            self._creation_path_cache.clear()
            self._service_cache.clear()
            
            # 重置性能统计
            self._performance_stats["cache_hits"] = 0
            self._performance_stats["cache_misses"] = 0
            
            logger.debug("容器已清除")
    
    def dispose(self) -> None:
        """释放容器资源"""
        with self._lock:
            if self._disposed:
                return
            
            self._disposed = True
            self._dispose_all_instances()
            
            # 清除缓存
            self._service_cache.clear()
            self._creation_path_cache.clear()
            
            logger.debug("容器已释放")
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """分析依赖关系
        
        Returns:
            分析结果
        """
        return self._dependency_analyzer.analyze()
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        self._service_cache.clear()
        
        with self._path_cache_lock:
            self._creation_path_cache.clear()
        
        # 重置性能统计
        self._performance_stats["cache_hits"] = 0
        self._performance_stats["cache_misses"] = 0
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            性能统计信息
        """
        total_requests = self._performance_stats["total_resolutions"]
        cache_hit_rate = (
            self._performance_stats["cache_hits"] / total_requests * 100
        ) if total_requests > 0 else 0
        
        # 获取监控器的统计信息
        monitor_stats = self._performance_monitor.get_stats()
        
        # 获取服务缓存统计
        service_cache_size = 0
        cache_memory = 0
        try:
            # 获取服务缓存大小
            if hasattr(self._service_cache, 'get_size'):
                service_cache_size = self._service_cache.get_size()
            # 获取缓存内存使用
            if hasattr(self._service_cache, 'get_memory_usage'):
                cache_memory = self._service_cache.get_memory_usage()
        except Exception:
            pass
        
        return {
            "resolution_stats": {
                "total_resolutions": total_requests,
                "cache_hits": self._performance_stats["cache_hits"],
                "cache_misses": self._performance_stats["cache_misses"],
                "cache_hit_rate": f"{cache_hit_rate:.2f}%"
            },
            "creation_stats": {
                "service_creations": self._performance_stats["service_creations"],
                "total_creation_time": self._performance_stats["total_creation_time"],
                "average_creation_time": self._performance_stats["average_creation_time"]
            },
            "cache_stats": {
                "service_cache_size": service_cache_size,
                "path_cache_size": len(self._creation_path_cache),
                "max_cache_size": self._max_cache_size,
                "cache_memory_bytes": cache_memory,
            },
            "monitor_stats": monitor_stats
        }
    
    def optimize_cache(self) -> Dict[str, Any]:
        """优化缓存
        
        Returns:
            优化结果
        """
        return self._service_cache.optimize()
    
    def get_service_creation_path(self, service_type: Type) -> List[Type]:
        """获取服务创建路径
        
        Args:
            service_type: 服务类型
            
        Returns:
            创建路径
        """
        if self._enable_path_cache:
            return self._get_creation_path(service_type)
        else:
            return self._build_creation_path(service_type)
    
    def _find_registration(self, service_type: Type) -> Optional[ServiceRegistration]:
        """查找服务注册"""
        # 首先查找当前环境的注册
        if service_type in self._environment_services:
            env_services = self._environment_services[service_type]
            current_scope_id = self._scope_manager.get_current_scope_id()
            if current_scope_id:
                # 检查作用域内的实例
                scoped_instance = self._scope_manager.get_scoped_instance(current_scope_id, service_type)
                if scoped_instance:
                    # 返回一个特殊的注册，包含作用域实例
                    return ServiceRegistration(
                        implementation=type(scoped_instance),
                        lifetime=ServiceLifetime.SCOPED,
                        instance=scoped_instance
                    )
            
            if self._environment in env_services:
                return env_services[self._environment]
        
        # 查找默认注册
        if service_type in self._services:
            return self._services[service_type]
        
        # 查找其他环境的默认注册
        if service_type in self._environment_services:
            env_services = self._environment_services[service_type]
            if "default" in env_services:
                return env_services["default"]
            # 返回任意一个注册
            if env_services:
                return next(iter(env_services.values()))
        
        return None
    
    def _create_instance(self, service_type: Type, registration: ServiceRegistration) -> Any:
        """创建服务实例（增强版）"""
        # 设置服务状态
        self._service_status[service_type] = ServiceStatus.CREATING
        
        # 添加到创建栈
        self._creation_stack.append(service_type)
        
        try:
            # 使用工厂方法创建
            if registration.factory is not None:
                instance = registration.factory()
            # 使用实现类创建
            elif registration.implementation is not type(None):
                instance = self._create_with_injection(registration.implementation)
            else:
                raise ServiceCreationError("No factory or implementation available")
            
            # 设置服务状态
            self._service_status[service_type] = ServiceStatus.CREATED
            
            # 初始化生命周期感知的服务
            if isinstance(instance, ILifecycleAware):
                self._service_status[service_type] = ServiceStatus.INITIALIZING
                instance.initialize()
                self._service_status[service_type] = ServiceStatus.INITIALIZED
                self._initialization_order.append(service_type)
            
            # 跟踪服务
            if self._enable_tracking:
                self._service_tracker.track_creation(service_type, instance)
            
            # 更新依赖分析
            if registration.implementation is not type(None):
                self._dependency_analyzer.update_from_implementation(service_type, registration.implementation)
            
            return instance
        except CircularDependencyError:
            # 如果是循环依赖错误，直接抛出，不要包装
            raise
        except Exception as e:
            self._service_status[service_type] = ServiceStatus.DISPOSED
            raise ServiceCreationError(f"Failed to create service {service_type.__name__}: {e}")
        finally:
            # 从创建栈中移除
            if service_type in self._creation_stack:
                self._creation_stack.remove(service_type)
    
    def _create_with_injection(self, implementation: Type) -> Any:
        """通过依赖注入创建实例"""
        # 获取构造函数参数
        sig = signature(implementation.__init__)
        parameters = sig.parameters
        
        # 准备参数
        kwargs: Dict[str, Any] = {}
        for param_name, param in parameters.items():
            if param_name == "self":
                continue
            
            # 尝试从容器获取依赖
            if param.annotation != param.empty:
                dependency_type = param.annotation
                
                # 如果注解是字符串，尝试解析为类型
                if isinstance(dependency_type, str):
                    try:
                        dependency_type = self._resolve_string_type(dependency_type, implementation)
                    except Exception:
                        if param.default != param.empty:
                            kwargs[param_name] = param.default
                            continue
                        else:
                            raise ServiceCreationError(
                                f"Cannot resolve dependency {dependency_type} for parameter {param_name}"
                            )
                
                if not isinstance(dependency_type, type):
                    if param.default != param.empty:
                        kwargs[param_name] = param.default
                        continue
                    else:
                        raise ServiceCreationError(
                            f"Invalid dependency type {dependency_type} for parameter {param_name}"
                        )
                
                if self.has_service(dependency_type):
                    kwargs[param_name] = self.get(dependency_type)
                elif param.default != param.empty:
                    kwargs[param_name] = param.default
                else:
                    raise ServiceCreationError(
                        f"Cannot resolve dependency {dependency_type} for parameter {param_name}"
                    )
            elif param.default != param.empty:
                kwargs[param_name] = param.default
        
        return implementation(**kwargs)
    
    def _resolve_string_type(self, type_str: str, context_type: Type) -> Type:
        """解析字符串类型注解"""
        # 尝试从上下文模块获取类型
        context_module = sys.modules[context_type.__module__]
        globalns = getattr(context_module, "__dict__", {})
        localns = {context_type.__name__: context_type}
        
        # 使用eval解析字符串类型注解
        resolved_type = eval(type_str, globalns, localns)
        return resolved_type
    
    def _get_from_cache(self, service_type: Type) -> Optional[Any]:
        """从缓存获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            缓存的服务实例，如果不存在则返回None
        """
        return self._service_cache.get(service_type)
    
    def _add_to_cache(self, service_type: Type, instance: Any) -> None:
        """添加服务实例到缓存
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        # 检查是否是实例注册（有明确的注册实例），如果是则不缓存，直接返回注册的实例
        registration = self._find_registration(service_type)
        if registration and registration.instance is not None:
            # 这是实例注册，不进行缓存，直接返回注册的实例
            return
        
        self._service_cache.put(service_type, instance)
    
    def _get_creation_path(self, service_type: Type) -> List[Type]:
        """从缓存获取创建路径
        
        Args:
            service_type: 服务类型
            
        Returns:
            创建路径
        """
        with self._path_cache_lock:
            if service_type in self._creation_path_cache:
                return self._creation_path_cache[service_type].copy()
            
            # 构建创建路径并缓存
            path = self._build_creation_path(service_type)
            self._creation_path_cache[service_type] = path.copy()
            
            return path
    
    def _build_creation_path(self, service_type: Type) -> List[Type]:
        """构建服务创建路径
        
        Args:
            service_type: 服务类型
            
        Returns:
            创建路径
        """
        path = []
        visited = set()
        
        def build_path_recursive(current_type: Type) -> None:
            if current_type in visited:
                return
            
            visited.add(current_type)
            path.append(current_type)
            
            # 获取依赖
            registration = self._find_registration(current_type)
            if registration and registration.implementation != type(None):
                dependencies = self._get_dependencies(registration.implementation)
                for dep_type in dependencies:
                    build_path_recursive(dep_type)
        
        build_path_recursive(service_type)
        return path
    
    def _get_dependencies(self, implementation: Type) -> List[Type]:
        """获取实现的依赖类型
        
        Args:
            implementation: 实现类
            
        Returns:
            依赖类型列表
        """
        dependencies = []
        
        try:
            sig = signature(implementation.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == "self" or param.annotation == param.empty:
                    continue
                
                dep_type = param.annotation
                if isinstance(dep_type, str):
                    # 尝试解析字符串类型
                    try:
                        dep_type = self._resolve_string_type(dep_type, implementation)
                    except Exception:
                        continue
                
                if isinstance(dep_type, type) and self.has_service(dep_type):
                    dependencies.append(dep_type)
        except Exception:
            pass
        
        return dependencies


def create_optimized_container(
    enable_service_cache: bool = True,
    enable_path_cache: bool = True,
    max_cache_size: int = 1000,
    cache_ttl_seconds: int = 3600,
    enable_tracking: bool = False
) -> EnhancedDependencyContainer:
    """创建优化的依赖注入容器
    
    Args:
        enable_service_cache: 是否启用服务缓存
        enable_path_cache: 是否启用路径缓存
        max_cache_size: 最大缓存大小
        cache_ttl_seconds: 缓存过期时间
        enable_tracking: 是否启用服务跟踪
        
    Returns:
        优化的依赖注入容器实例
    """
    return EnhancedDependencyContainer(
        enable_service_cache=enable_service_cache,
        enable_path_cache=enable_path_cache,
        max_cache_size=max_cache_size,
        cache_ttl_seconds=cache_ttl_seconds,
        enable_tracking=enable_tracking
    )


# 全局依赖注入容器实例
_global_container: Optional[EnhancedDependencyContainer] = None


def get_global_container() -> EnhancedDependencyContainer:
    """获取全局依赖注入容器

    Returns:
        EnhancedDependencyContainer: 全局依赖注入容器
    """
    global _global_container
    if _global_container is None:
        _global_container = create_optimized_container()
    return _global_container