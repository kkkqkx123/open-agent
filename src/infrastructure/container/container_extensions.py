"""
容器扩展功能

提供额外的容器功能，支持服务层的常见需求。
"""

from typing import Type, TypeVar, Dict, Any, List, Optional, Callable
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

T = TypeVar('T')


class ContainerExtensions:
    """容器扩展功能类
    
    提供额外的容器操作方法，简化服务层的常见任务。
    """
    
    def __init__(self, container: IDependencyContainer):
        """初始化容器扩展
        
        Args:
            container: 依赖注入容器实例
        """
        self._container = container
    
    def get_optional(self, service_type: Type[T]) -> Optional[T]:
        """获取可选服务
        
        如果服务未注册，返回None而不是抛出异常。
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例或None
        """
        if self._container.has_service(service_type):
            return self._container.get(service_type)
        return None
    
    def get_all(self, service_types: List[Type]) -> Dict[Type, Any]:
        """批量获取服务
        
        Args:
            service_types: 服务类型列表
            
        Returns:
            服务类型到实例的映射
        """
        services = {}
        for service_type in service_types:
            if self._container.has_service(service_type):
                services[service_type] = self._container.get(service_type)
        return services
    
    def register_named(self, name: str, service_type: Type[T], implementation: Type[T], 
                      lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> None:
        """注册命名服务
        
        为同一接口的多个实现提供命名支持。
        
        Args:
            name: 服务名称
            service_type: 服务接口类型
            implementation: 服务实现类型
            lifetime: 服务生命周期
        """
        # 创建命名服务类型
        named_type = self._create_named_type(name, service_type)
        
        # 注册命名服务
        self._container.register(named_type, implementation, lifetime)
    
    def get_named(self, name: str, service_type: Type[T]) -> T:
        """获取命名服务
        
        Args:
            name: 服务名称
            service_type: 服务接口类型
            
        Returns:
            服务实例
        """
        # 创建命名服务类型
        named_type = self._create_named_type(name, service_type)
        
        # 获取命名服务
        return self._container.get(named_type)
    
    def register_factory_with_params(self, service_type: Type[T], 
                                    factory: Callable[..., T], 
                                    params: Dict[str, Any],
                                    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> None:
        """注册带参数的工厂
        
        Args:
            service_type: 服务类型
            factory: 工厂函数
            params: 工厂参数
            lifetime: 服务生命周期
        """
        def factory_wrapper() -> T:
            return factory(**params)
        
        self._container.register_factory(service_type, factory_wrapper, lifetime)
    
    def create_scope(self) -> 'ScopedContainer':
        """创建作用域容器
        
        返回一个新的容器实例，用于特定作用域内的服务解析。
        
        Returns:
            作用域容器实例
        """
        return ScopedContainer(self._container)
    
    def validate_dependencies(self) -> List[str]:
        """验证依赖关系
        
        检查所有已注册服务的依赖关系是否完整。
        
        Returns:
            缺失依赖的服务列表
        """
        # 这里需要容器提供获取所有注册的服务的方法
        # 由于当前容器接口不支持，这里只是一个占位实现
        return []
    
    def _create_named_type(self, name: str, service_type: Type[T]) -> Type[T]:
        """创建命名服务类型
        
        Args:
            name: 服务名称
            service_type: 服务接口类型
            
        Returns:
            命名服务类型
        """
        # 创建一个新的类型，用于区分同名服务的不同实现
        class NamedService:
            _original_type: Type[Any] = service_type
            _service_name: str = name
        
        # 设置类型名称和原始类型
        NamedService.__name__ = f"{name}_{service_type.__name__}"
        
        return NamedService  # type: ignore[return-value]


class ScopedContainer:
    """作用域容器
    
    在特定作用域内提供服务解析，支持作用域生命周期的服务。
    """
    
    def __init__(self, parent_container: IDependencyContainer):
        """初始化作用域容器
        
        Args:
            parent_container: 父容器实例
        """
        self._parent_container = parent_container
        self._scoped_instances: Dict[Type, Any] = {}
    
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例
        
        优先从作用域内获取，如果没有则从父容器获取。
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        # 检查作用域内是否有实例
        if service_type in self._scoped_instances:
            return self._scoped_instances[service_type]  # type: ignore[no-any-return]
        
        # 从父容器获取
        return self._parent_container.get(service_type)
    
    def register_scoped(self, service_type: Type[T], instance: T) -> None:
        """注册作用域实例
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        self._scoped_instances[service_type] = instance
    
    def dispose(self) -> None:
        """释放作用域资源
        
        清理作用域内的所有实例。
        """
        # 调用所有实例的dispose方法（如果存在）
        for instance in self._scoped_instances.values():
            if hasattr(instance, 'dispose') and callable(getattr(instance, 'dispose')):
                try:
                    instance.dispose()
                except Exception:
                    # 忽略释放时的错误
                    pass
        
        # 清理作用域实例
        self._scoped_instances.clear()


class ServiceLocator:
    """服务定位器
    
    提供全局访问点，用于在无法直接注入容器的场景中获取服务。
    """
    
    _instance: Optional['ServiceLocator'] = None
    _container: Optional[IDependencyContainer] = None
    
    def __new__(cls) -> 'ServiceLocator':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, container: IDependencyContainer) -> None:
        """初始化服务定位器
        
        Args:
            container: 依赖注入容器
        """
        if cls._instance is None:
            cls._instance = cls()
        cls._instance._container = container
    
    @classmethod
    def get_instance(cls) -> 'ServiceLocator':
        """获取服务定位器实例
        
        Returns:
            服务定位器实例
        """
        if cls._instance is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._instance
    
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        if self._container is None:
            raise RuntimeError("Container not set")
        return self._container.get(service_type)
    
    def get_optional(self, service_type: Type[T]) -> Optional[T]:
        """获取可选服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例或None
        """
        if self._container is None:
            return None
        
        if self._container.has_service(service_type):
            return self._container.get(service_type)
        return None


# 便捷函数
def get_service(service_type: Type[T]) -> T:
    """获取服务的便捷函数
    
    Args:
        service_type: 服务类型
        
    Returns:
        服务实例
    """
    return ServiceLocator.get_instance().get(service_type)


def get_optional_service(service_type: Type[T]) -> Optional[T]:
    """获取可选服务的便捷函数
    
    Args:
        service_type: 服务类型
        
    Returns:
        服务实例或None
    """
    return ServiceLocator.get_instance().get_optional(service_type)