"""基础依赖注入容器实现"""

import threading
import logging
import sys
from typing import Type, TypeVar, Dict, Any, Optional, Callable
from inspect import signature
from contextlib import contextmanager

from ..container_interfaces import (
    IDependencyContainer, 
    IServiceTracker, 
    ServiceStatus, 
    ILifecycleAware,
    ServiceRegistration
)
from ..types import ServiceLifetime, T
from ..exceptions import (
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
)

logger = logging.getLogger(__name__)


class DefaultServiceTracker(IServiceTracker):
    """默认服务跟踪器实现"""
    
    def __init__(self):
        self._tracked_services: Dict[Type, list] = {}  # 存储弱引用
        self._lock = threading.RLock()
    
    def track_creation(self, service_type: Type, instance: Any) -> None:
        """跟踪服务创建"""
        with self._lock:
            if service_type not in self._tracked_services:
                self._tracked_services[service_type] = []
            
            # 简单实现，实际应该使用弱引用
            self._tracked_services[service_type].append(instance)
    
    def track_disposal(self, service_type: Type, instance: Any) -> None:
        """跟踪服务释放"""
        with self._lock:
            if service_type in self._tracked_services:
                if instance in self._tracked_services[service_type]:
                    self._tracked_services[service_type].remove(instance)
    
    def get_tracked_services(self) -> Dict[Type, list]:
        """获取跟踪的服务"""
        with self._lock:
            # 过滤已释放的实例
            result = {}
            for service_type, instances in self._tracked_services.items():
                valid_instances = [inst for inst in instances if inst is not None]
                if valid_instances:
                    result[service_type] = valid_instances
            return result


class BaseDependencyContainer(IDependencyContainer):
    """基础依赖注入容器"""
    
    def __init__(self, service_tracker: Optional[IServiceTracker] = None):
        """初始化基础依赖注入容器
        
        Args:
            service_tracker: 服务跟踪器
        """
        # 基础服务注册
        self._services: Dict[Type, ServiceRegistration] = {}
        self._environment_services: Dict[Type, Dict[str, ServiceRegistration]] = {}
        self._instances: Dict[Type, Any] = {}
        self._environment = "default"
        self._lock = threading.RLock()
        
        # 服务跟踪
        self._service_tracker = service_tracker or DefaultServiceTracker()
        self._creation_stack: list = []  # 创建栈，用于检测循环依赖
        self._service_status: Dict[Type, ServiceStatus] = {}  # 服务状态
        self._initialization_order: list = []  # 初始化顺序
        self._disposed = False
        
        logger.debug("BaseDependencyContainer初始化完成")
    
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
            self._service_tracker.track_creation(interface, instance)
            
            logger.debug(f"注册实例服务: {interface.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        # 检查服务是否已注册
        registration = self._find_registration(service_type)
        if registration is None:
            raise ServiceNotRegisteredError(f"Service {service_type} not registered")
        
        # 如果注册了实例，直接返回注册的实例
        if registration.instance is not None:
            return registration.instance  # type: ignore
        
        try:
            # 检测循环依赖
            self._check_circular_dependency(service_type)
            
            # 创建服务实例
            instance = self._create_instance(service_type, registration)
            return instance
            
        except CircularDependencyError:
            # 如果是循环依赖错误，直接抛出，不要包装
            raise
        except Exception as e:
            raise ServiceCreationError(f"Failed to get service {service_type.__name__}: {e}")
    
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
            服务状态
        """
        return self._service_status.get(service_type)
    
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
        """检查循环依赖"""
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
    
    def _dispose_all_instances(self) -> None:
        """释放所有实例"""
        # 按照初始化的逆序释放
        for service_type in reversed(self._initialization_order):
            # 首先检查实例缓存
            if service_type in self._instances:
                instance = self._instances[service_type]
                if isinstance(instance, ILifecycleAware):
                    try:
                        self._service_status[service_type] = ServiceStatus.DISPOSING
                        instance.dispose()
                        self._service_status[service_type] = ServiceStatus.DISPOSED
                    except Exception as e:
                        logger.error(f"释放服务 {service_type.__name__} 失败: {e}")
        
        # 释放通过register_instance注册的实例
        for service_type, registration in self._services.items():
            if registration.instance is not None and isinstance(registration.instance, ILifecycleAware):
                # 检查该服务类型是否已经在初始化顺序中，避免重复释放
                if service_type not in self._initialization_order:
                    try:
                        self._service_status[service_type] = ServiceStatus.DISPOSING
                        registration.instance.dispose()
                        self._service_status[service_type] = ServiceStatus.DISPOSED
                    except Exception as e:
                        logger.error(f"释放注册实例 {service_type.__name__} 失败: {e}")
        
        # 释放环境特定服务中的实例
        for service_type, env_registrations in self._environment_services.items():
            for env_name, registration in env_registrations.items():
                if registration.instance is not None and isinstance(registration.instance, ILifecycleAware):
                    # 检查该服务类型是否已经在初始化顺序中，避免重复释放
                    if service_type not in self._initialization_order:
                        try:
                            self._service_status[service_type] = ServiceStatus.DISPOSING
                            registration.instance.dispose()
                            self._service_status[service_type] = ServiceStatus.DISPOSED
                        except Exception as e:
                            logger.error(f"释放环境特定实例 {service_type.__name__} 失败: {e}")
        
        # 清除实例缓存
        self._instances.clear()