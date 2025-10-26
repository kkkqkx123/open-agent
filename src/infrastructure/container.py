"""增强的依赖注入容器实现

提供更完善的生命周期管理和循环依赖检测功能。
"""

import threading
import weakref
import time
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Dict, Any, Optional, List, Set, Callable, Union
from inspect import isclass, signature
from contextlib import contextmanager
from enum import Enum

from .container import IDependencyContainer, ServiceRegistration, ServiceLifetime, T
from .exceptions import (
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
)

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""
    REGISTERED = "registered"
    CREATING = "creating"
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    DISPOSING = "disposing"
    DISPOSED = "disposed"


class ILifecycleAware(ABC):
    """生命周期感知接口"""
    
    @abstractmethod
    def initialize(self) -> None:
        """初始化服务"""
        pass
    
    @abstractmethod
    def dispose(self) -> None:
        """释放服务资源"""
        pass


class IServiceTracker(ABC):
    """服务跟踪器接口"""
    
    @abstractmethod
    def track_creation(self, service_type: Type, instance: Any) -> None:
        """跟踪服务创建"""
        pass
    
    @abstractmethod
    def track_disposal(self, service_type: Type, instance: Any) -> None:
        """跟踪服务释放"""
        pass
    
    @abstractmethod
    def get_tracked_services(self) -> Dict[Type, List[Any]]:
        """获取跟踪的服务"""
        pass


class DefaultServiceTracker(IServiceTracker):
    """默认服务跟踪器实现"""
    
    def __init__(self):
        self._tracked_services: Dict[Type, List[weakref.ref]] = {}
        self._lock = threading.RLock()
    
    def track_creation(self, service_type: Type, instance: Any) -> None:
        """跟踪服务创建"""
        with self._lock:
            if service_type not in self._tracked_services:
                self._tracked_services[service_type] = []
            
            # 使用弱引用避免内存泄漏
            self._tracked_services[service_type].append(weakref.ref(instance))
    
    def track_disposal(self, service_type: Type, instance: Any) -> None:
        """跟踪服务释放"""
        with self._lock:
            if service_type in self._tracked_services:
                # 移除已释放的实例
                self._tracked_services[service_type] = [
                    ref for ref in self._tracked_services[service_type]
                    if ref() is not instance
                ]
    
    def get_tracked_services(self) -> Dict[Type, List[Any]]:
        """获取跟踪的服务"""
        with self._lock:
            result = {}
            for service_type, refs in self._tracked_services.items():
                # 转换弱引用为实际实例，过滤已释放的
                instances = [ref() for ref in refs if ref() is not None]
                if instances:
                    result[service_type] = instances
            return result


class EnhancedDependencyContainer(IDependencyContainer):
    """增强的依赖注入容器实现
    
    提供更完善的生命周期管理和循环依赖检测功能。
    """
    
    def __init__(
        self,
        service_tracker: Optional[IServiceTracker] = None,
        enable_tracking: bool = False
    ):
        """初始化增强的依赖注入容器
        
        Args:
            service_tracker: 服务跟踪器
            enable_tracking: 是否启用服务跟踪
        """
        # 基础服务注册
        self._services: Dict[Type, ServiceRegistration] = {}
        self._environment_services: Dict[Type, Dict[str, ServiceRegistration]] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._environment = "default"
        self._lock = threading.RLock()
        
        # 增强功能
        self._service_tracker = service_tracker or DefaultServiceTracker()
        self._enable_tracking = enable_tracking
        self._creation_stack: List[Type] = []  # 创建栈，用于检测循环依赖
        self._dependency_graph: Dict[Type, Set[Type]] = {}  # 依赖关系图
        self._service_status: Dict[Type, ServiceStatus] = {}  # 服务状态
        self._initialization_order: List[Type] = []  # 初始化顺序
        self._disposed = False
        
        # 作用域管理
        self._current_scope_id: Optional[str] = None
        self._scope_counter = 0
        
        logger.debug("EnhancedDependencyContainer初始化完成")
    
    def register(
        self,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务实现"""
        with self._lock:
            if self._disposed:
                raise ServiceCreationError("容器已释放，无法注册服务")
            
            # 更新依赖关系图
            self._update_dependency_graph(interface, implementation)
            
            # 注册服务
            registration = ServiceRegistration(
                implementation=implementation,
                lifetime=lifetime
            )
            
            if environment == "default":
                self._services[interface] = registration
            else:
                if interface not in self._environment_services:
                    self._environment_services[interface] = {}
                self._environment_services[interface][environment] = registration
            
            # 设置服务状态
            self._service_status[interface] = ServiceStatus.REGISTERED
            
            logger.debug(f"注册服务: {interface.__name__} -> {implementation.__name__}")
    
    def register_factory(
        self,
        interface: Type,
        factory: Callable[[], Any],
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务工厂"""
        with self._lock:
            if self._disposed:
                raise ServiceCreationError("容器已释放，无法注册服务")
            
            registration = ServiceRegistration(
                implementation=type(None),
                lifetime=lifetime,
                factory=factory,
            )
            
            if environment == "default":
                self._services[interface] = registration
            else:
                if interface not in self._environment_services:
                    self._environment_services[interface] = {}
                self._environment_services[interface][environment] = registration
            
            # 设置服务状态
            self._service_status[interface] = ServiceStatus.REGISTERED
            
            logger.debug(f"注册工厂服务: {interface.__name__}")
    
    def register_instance(
        self,
        interface: Type,
        instance: Any,
        environment: str = "default"
    ) -> None:
        """注册服务实例"""
        with self._lock:
            if self._disposed:
                raise ServiceCreationError("容器已释放，无法注册服务")
            
            registration = ServiceRegistration(
                implementation=type(instance),
                lifetime=ServiceLifetime.SINGLETON,
                instance=instance,
            )
            
            if environment == "default":
                self._services[interface] = registration
            else:
                if interface not in self._environment_services:
                    self._environment_services[interface] = {}
                self._environment_services[interface][environment] = registration
            
            # 设置服务状态
            self._service_status[interface] = ServiceStatus.CREATED
            
            # 初始化生命周期感知的服务
            if isinstance(instance, ILifecycleAware):
                try:
                    instance.initialize()
                    self._service_status[interface] = ServiceStatus.INITIALIZED
                except Exception as e:
                    logger.error(f"初始化服务 {interface.__name__} 失败: {e}")
                    raise ServiceCreationError(f"初始化服务失败: {e}")
            
            # 跟踪服务
            if self._enable_tracking:
                self._service_tracker.track_creation(interface, instance)
            
            logger.debug(f"注册实例服务: {interface.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        with self._lock:
            if self._disposed:
                raise ServiceCreationError("容器已释放，无法获取服务")
            
            # 检测循环依赖（增强版）
            self._check_circular_dependency(service_type)
            
            # 查找服务注册
            registration = self._find_registration(service_type)
            if registration is None:
                raise ServiceNotRegisteredError(f"Service {service_type} not registered")
            
            # 处理已注册的实例
            if registration.instance is not None:
                return registration.instance  # type: ignore
            
            # 根据生命周期获取实例
            if registration.lifetime == ServiceLifetime.SINGLETON:
                return self._get_singleton_instance(service_type, registration)
            elif registration.lifetime == ServiceLifetime.SCOPED:
                return self._get_scoped_instance(service_type, registration)
            else:  # TRANSIENT
                return self._create_instance(service_type, registration)
    
    def create_scope(self) -> str:
        """创建新的作用域
        
        Returns:
            str: 作用域ID
        """
        with self._lock:
            self._scope_counter += 1
            scope_id = f"scope_{self._scope_counter}"
            self._scoped_instances[scope_id] = {}
            logger.debug(f"创建作用域: {scope_id}")
            return scope_id
    
    def dispose_scope(self, scope_id: str) -> None:
        """释放作用域
        
        Args:
            scope_id: 作用域ID
        """
        with self._lock:
            if scope_id in self._scoped_instances:
                # 释放作用域内的所有实例
                for service_type, instance in self._scoped_instances[scope_id].items():
                    if isinstance(instance, ILifecycleAware):
                        try:
                            instance.dispose()
                        except Exception as e:
                            logger.error(f"释放作用域服务 {service_type.__name__} 失败: {e}")
                
                del self._scoped_instances[scope_id]
                logger.debug(f"释放作用域: {scope_id}")
    
    @contextmanager
    def scope(self):
        """作用域上下文管理器"""
        scope_id = self.create_scope()
        try:
            old_scope_id = self._current_scope_id
            self._current_scope_id = scope_id
            yield scope_id
        finally:
            self._current_scope_id = old_scope_id
            self.dispose_scope(scope_id)
    
    def get_environment(self) -> str:
        """获取当前环境"""
        return self._environment
    
    def set_environment(self, env: str) -> None:
        """设置当前环境"""
        with self._lock:
            if env != self._environment:
                self._environment = env
                # 清除单例缓存，因为环境改变可能需要不同的实现
                self._instances.clear()
                logger.debug(f"环境设置为: {env}")
    
    def has_service(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return self._find_registration(service_type) is not None
    
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
            self._dependency_graph.clear()
            self._service_status.clear()
            self._initialization_order.clear()
            self._creation_stack.clear()
            
            logger.debug("容器已清除")
    
    def dispose(self) -> None:
        """释放容器资源"""
        with self._lock:
            if self._disposed:
                return
            
            self._disposed = True
            self._dispose_all_instances()
            logger.debug("容器已释放")
    
    def get_service_status(self, service_type: Type) -> Optional[ServiceStatus]:
        """获取服务状态
        
        Args:
            service_type: 服务类型
            
        Returns:
            Optional[ServiceStatus]: 服务状态
        """
        return self._service_status.get(service_type)
    
    def get_dependency_graph(self) -> Dict[Type, Set[Type]]:
        """获取依赖关系图
        
        Returns:
            Dict[Type, Set[Type]]: 依赖关系图
        """
        return {k: v.copy() for k, v in self._dependency_graph.items()}
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """分析依赖关系
        
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 检测循环依赖
        circular_deps = self._detect_circular_dependencies()
        
        # 计算依赖深度
        dependency_depths = {}
        for service_type in self._dependency_graph:
            dependency_depths[service_type] = self._calculate_dependency_depth(service_type)
        
        # 找出根服务（没有依赖的服务）
        root_services = [
            service_type for service_type in self._dependency_graph
            if not self._dependency_graph[service_type]
        ]
        
        return {
            "circular_dependencies": circular_deps,
            "dependency_depths": dependency_depths,
            "root_services": root_services,
            "total_services": len(self._dependency_graph)
        }
    
    def _find_registration(self, service_type: Type) -> Optional[ServiceRegistration]:
        """查找服务注册"""
        # 首先查找当前环境的注册
        if service_type in self._environment_services:
            env_services = self._environment_services[service_type]
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
    
    def _check_circular_dependency(self, service_type: Type) -> None:
        """检查循环依赖（增强版）"""
        if service_type in self._creation_stack:
            # 构建循环路径
            cycle_start = self._creation_stack.index(service_type)
            cycle_path = self._creation_stack[cycle_start:] + [service_type]
            
            # 生成详细的错误信息
            cycle_str = " -> ".join([t.__name__ for t in cycle_path])
            raise CircularDependencyError(
                f"检测到循环依赖: {cycle_str}\n"
                f"依赖深度: {len(cycle_path)}\n"
                f"建议: 考虑使用接口抽象或延迟初始化来打破循环依赖"
            )
    
    def _get_singleton_instance(self, service_type: Type, registration: ServiceRegistration) -> Any:
        """获取单例实例"""
        if service_type in self._instances:
            return self._instances[service_type]
        
        instance = self._create_instance(service_type, registration)
        self._instances[service_type] = instance
        return instance
    
    def _get_scoped_instance(self, service_type: Type, registration: ServiceRegistration) -> Any:
        """获取作用域实例"""
        if self._current_scope_id is None:
            # 如果没有当前作用域，创建一个临时作用域
            self._current_scope_id = self.create_scope()
        
        scope_instances = self._scoped_instances[self._current_scope_id]
        if service_type in scope_instances:
            return scope_instances[service_type]
        
        instance = self._create_instance(service_type, registration)
        scope_instances[service_type] = instance
        return instance
    
    def _create_instance(self, service_type: Type, registration: ServiceRegistration) -> Any:
        """创建服务实例"""
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
                        continue
                
                if not isinstance(dependency_type, type):
                    continue
                
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
        import sys
        
        # 尝试从上下文模块获取类型
        context_module = sys.modules[context_type.__module__]
        globalns = getattr(context_module, "__dict__", {})
        localns = {context_type.__name__: context_type}
        
        # 使用eval解析字符串类型注解
        resolved_type = eval(type_str, globalns, localns)
        return resolved_type
    
    def _update_dependency_graph(self, interface: Type, implementation: Type) -> None:
        """更新依赖关系图"""
        if interface not in self._dependency_graph:
            self._dependency_graph[interface] = set()
        
        # 分析实现类的依赖
        sig = signature(implementation.__init__)
        for param_name, param in sig.parameters.items():
            if param_name == "self" or param.annotation == param.empty:
                continue
            
            dependency_type = param.annotation
            if isinstance(dependency_type, str):
                try:
                    dependency_type = self._resolve_string_type(dependency_type, implementation)
                except Exception:
                    continue
            
            if isinstance(dependency_type, type):
                self._dependency_graph[interface].add(dependency_type)
    
    def _detect_circular_dependencies(self) -> List[List[Type]]:
        """检测循环依赖"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: Type, path: List[Type]) -> None:
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self._dependency_graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in self._dependency_graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _calculate_dependency_depth(self, service_type: Type, visited: Optional[Set[Type]] = None) -> int:
        """计算依赖深度"""
        if visited is None:
            visited = set()
        
        if service_type in visited:
            return 0  # 避免循环
        
        visited.add(service_type)
        
        dependencies = self._dependency_graph.get(service_type, [])
        if not dependencies:
            return 0
        
        max_depth = 0
        for dep in dependencies:
            depth = self._calculate_dependency_depth(dep, visited.copy())
            max_depth = max(max_depth, depth)
        
        return max_depth + 1
    
    def _dispose_all_instances(self) -> None:
        """释放所有实例"""
        # 按照初始化的逆序释放
        for service_type in reversed(self._initialization_order):
            if service_type in self._instances:
                instance = self._instances[service_type]
                if isinstance(instance, ILifecycleAware):
                    try:
                        self._service_status[service_type] = ServiceStatus.DISPOSING
                        instance.dispose()
                        self._service_status[service_type] = ServiceStatus.DISPOSED
                    except Exception as e:
                        logger.error(f"释放服务 {service_type.__name__} 失败: {e}")
        
        # 释放作用域实例
        for scope_id in list(self._scoped_instances.keys()):
            self.dispose_scope(scope_id)
        
        # 清除实例缓存
        self._instances.clear()