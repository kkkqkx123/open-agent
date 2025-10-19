"""依赖注入容器实现"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Dict, Any, Optional, List, Set, Callable
from inspect import isclass, signature
import threading

from .exceptions import (
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
)
from .types import ServiceRegistration, ServiceLifetime, T


class IDependencyContainer(ABC):
    """依赖注入容器接口"""

    @abstractmethod
    def register(
        self,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务实现"""
        pass

    @abstractmethod
    def register_factory(
        self,
        interface: Type,
        factory: Callable[[], Any],
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务工厂"""
        pass

    @abstractmethod
    def register_instance(
        self, interface: Type, instance: Any, environment: str = "default"
    ) -> None:
        """注册服务实例"""
        pass

    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        pass

    @abstractmethod
    def get_environment(self) -> str:
        """获取当前环境"""
        pass

    @abstractmethod
    def set_environment(self, env: str) -> None:
        """设置当前环境"""
        pass

    @abstractmethod
    def has_service(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清除所有服务和缓存"""
        pass


class DependencyContainer(IDependencyContainer):
    """依赖注入容器实现"""

    def __init__(self) -> None:
        self._services: Dict[Type, ServiceRegistration] = {}
        self._environment_services: Dict[Type, Dict[str, ServiceRegistration]] = {}
        self._instances: Dict[Type, Any] = {}
        self._environment = "default"
        self._lock = threading.RLock()
        self._creating: Set[Type] = set()  # 用于检测循环依赖

    def register(
        self,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务实现"""
        with self._lock:
            if environment == "default":
                self._services[interface] = ServiceRegistration(
                    implementation=implementation, lifetime=lifetime
                )
            else:
                if interface not in self._environment_services:
                    self._environment_services[interface] = {}
                self._environment_services[interface][environment] = (
                    ServiceRegistration(
                        implementation=implementation, lifetime=lifetime
                    )
                )

    def register_factory(
        self,
        interface: Type,
        factory: Callable[[], Any],
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务工厂"""
        with self._lock:
            if environment == "default":
                self._services[interface] = ServiceRegistration(
                    implementation=type(None),  # 工厂模式不需要实现类
                    lifetime=lifetime,
                    factory=factory,
                )
            else:
                if interface not in self._environment_services:
                    self._environment_services[interface] = {}
                self._environment_services[interface][environment] = (
                    ServiceRegistration(
                        implementation=type(None), lifetime=lifetime, factory=factory
                    )
                )

    def register_instance(
        self, interface: Type, instance: Any, environment: str = "default"
    ) -> None:
        """注册服务实例"""
        with self._lock:
            if environment == "default":
                self._services[interface] = ServiceRegistration(
                    implementation=type(instance),
                    lifetime=ServiceLifetime.SINGLETON,
                    instance=instance,
                )
            else:
                if interface not in self._environment_services:
                    self._environment_services[interface] = {}
                self._environment_services[interface][environment] = (
                    ServiceRegistration(
                        implementation=type(instance),
                        lifetime=ServiceLifetime.SINGLETON,
                        instance=instance,
                    )
                )

    def get(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        with self._lock:
            # 检查循环依赖
            if service_type in self._creating:
                raise CircularDependencyError(
                    f"Circular dependency detected for {service_type}"
                )

            # 查找服务注册
            registration = self._find_registration(service_type)
            if registration is None:
                raise ServiceNotRegisteredError(
                    f"Service {service_type} not registered"
                )

            # 处理已注册的实例
            if registration.instance is not None:
                return registration.instance  # type: ignore

            # 处理单例模式
            if registration.lifetime == ServiceLifetime.SINGLETON:
                if service_type in self._instances:
                    return self._instances[service_type]  # type: ignore

            # 创建服务实例
            self._creating.add(service_type)
            try:
                instance = self._create_instance(registration)

                # 缓存单例实例
                if registration.lifetime == ServiceLifetime.SINGLETON:
                    self._instances[service_type] = instance

                return instance  # type: ignore
            finally:
                self._creating.discard(service_type)

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

    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """创建服务实例"""
        try:
            # 使用工厂方法创建
            if registration.factory is not None:
                return registration.factory()

            # 使用实现类创建
            if registration.implementation is not type(None):
                return self._create_with_injection(registration.implementation)

            raise ServiceCreationError("No factory or implementation available")
        except CircularDependencyError:
            # 如果是循环依赖错误，直接抛出，不要包装
            raise
        except Exception as e:
            raise ServiceCreationError(f"Failed to create service: {e}")

    def _create_with_injection(self, implementation: Type) -> Any:
        """通过依赖注入创建实例"""
        # 获取构造函数参数
        sig = signature(implementation.__init__)
        parameters = sig.parameters

        # 准备参数
        kwargs = {}
        for param_name, param in parameters.items():
            if param_name == "self":
                continue

            # 尝试从容器获取依赖
            if param.annotation != param.empty:
                dependency_type = param.annotation

                # 如果注解是字符串，尝试解析为类型
                if isinstance(dependency_type, str):
                    # 尝试从当前模块获取类型
                    import sys

                    current_module = sys.modules[implementation.__module__]
                    try:
                        # 获取局部和全局命名空间
                        globalns = getattr(current_module, "__dict__", {})
                        localns = {implementation.__name__: implementation}

                        # 使用eval解析字符串类型注解
                        resolved_type = eval(dependency_type, globalns, localns)
                        dependency_type = resolved_type
                    except:
                        # 如果无法解析，保持原字符串类型
                        pass

                if self.has_service(dependency_type):
                    kwargs[param_name] = self.get(dependency_type)
                elif param.default != param.empty:
                    # 使用默认值
                    kwargs[param_name] = param.default
                else:
                    raise ServiceCreationError(
                        f"Cannot resolve dependency {dependency_type} for parameter {param_name}"
                    )
            elif param.default != param.empty:
                kwargs[param_name] = param.default

        return implementation(**kwargs)

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

    def has_service(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return self._find_registration(service_type) is not None

    def clear(self) -> None:
        """清除所有服务和缓存"""
        with self._lock:
            self._services.clear()
            self._environment_services.clear()
            self._instances.clear()
            self._creating.clear()

    def get_registered_services(self) -> List[Type]:
        """获取所有已注册的服务类型"""
        with self._lock:
            services: Set[Type] = set(self._services.keys())
            services.update(self._environment_services.keys())
            return list(services)
