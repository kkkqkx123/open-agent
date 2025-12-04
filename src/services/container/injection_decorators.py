"""依赖注入装饰器

提供装饰器模式的服务注入支持，简化使用方式。
"""

from typing import TypeVar, Type, Optional, Callable, Any, Dict, cast
from functools import wraps
from src.services.container.injection_base import get_global_injection_registry

T = TypeVar('T')


def injectable(service_type: Type[T], fallback_factory: Optional[Callable[[], T]] = None):
    """装饰器：创建可注入的服务获取函数
    
    将普通函数转换为服务获取函数，支持缓存和降级。
    
    Args:
        service_type: 服务类型
        fallback_factory: fallback工厂函数
        
    Returns:
        装饰器函数
        
    Example:
        ```python
        @injectable(ILogger)
        def get_logger(module_name: str = None) -> ILogger:
            '''获取日志记录器'''
            pass
        
        # 使用
        logger = get_logger("my_module")
        ```
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 注册服务注入
        injection = get_global_injection_registry().register(service_type, fallback_factory)
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return injection.get_instance()
        
        # 添加额外方法
        wrapper_cast = cast(Any, wrapper)
        wrapper_cast.set_instance = injection.set_instance
        wrapper_cast.clear_instance = injection.clear_instance
        wrapper_cast.is_initialized = lambda: injection.is_initialized
        wrapper_cast.get_status = injection.get_status
        wrapper_cast.disable_container_fallback = injection.disable_container_fallback
        wrapper_cast.enable_container_fallback = injection.enable_container_fallback
        
        return wrapper
    
    return decorator


def service_accessor(service_type: Type[T], fallback_factory: Optional[Callable[[], T]] = None):
    """装饰器：为类添加服务访问器方法
    
    为类自动添加 `get_{service_name}` 方法。
    
    Args:
        service_type: 服务类型
        fallback_factory: fallback工厂函数
        
    Returns:
        类装饰器
        
    Example:
        ```python
        @service_accessor(ILLMManager)
        class MyService:
            def process_data(self):
                llm = self.get_illmmanager()
                return llm.generate_response("Hello")
        ```
    """
    def decorator(cls: type) -> type:
        # 注册服务注入
        injection = get_global_injection_registry().register(service_type, fallback_factory)
        
        # 创建访问器方法名
        service_name = service_type.__name__.lower()
        accessor_name = f'get_{service_name}'
        
        def get_service(self) -> T:
            """获取服务实例"""
            return injection.get_instance()
        
        # 设置方法文档
        get_service.__doc__ = f"获取 {service_type.__name__} 实例"
        get_service.__name__ = accessor_name
        
        # 添加到类
        setattr(cls, accessor_name, get_service)
        
        # 添加类级别的静态方法
        def get_service_static() -> T:
            """静态方法：获取服务实例"""
            return injection.get_instance()
        
        static_name = f'get_{service_name}_static'
        get_service_static.__doc__ = f"静态方法：获取 {service_type.__name__} 实例"
        get_service_static.__name__ = static_name
        
        setattr(cls, static_name, staticmethod(get_service_static))
        
        return cls
    
    return decorator


def auto_inject(*service_types: Type[T], fallback_factories: Optional[Dict[Type, Callable[[], T]]] = None):
    """装饰器：自动注入服务到函数参数
    
    自动将服务实例注入到函数参数中。
    
    Args:
        *service_types: 要注入的服务类型
        fallback_factories: fallback工厂字典
        
    Returns:
        装饰器函数
        
    Example:
        ```python
        @auto_inject(ILogger, ILLMManager)
        def process_data(logger, llm_manager, data):
            logger.info("处理数据")
            return llm_manager.process(data)
        
        # 使用时只需要传递 data 参数
        result = process_data(data="test")
        ```
    """
    if fallback_factories is None:
        fallback_factories = {}
    
    def decorator(func: Callable) -> Callable:
        # 注册所有服务注入
        injections = {}
        for service_type in service_types:
            fallback_factory = fallback_factories.get(service_type) if fallback_factories else None
            injection = get_global_injection_registry().register(service_type, fallback_factory)
            injections[service_type] = injection
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            
            # 自动注入服务
            for service_type, injection in injections.items():
                param_name = service_type.__name__.lower()
                if param_name not in bound_args.arguments:
                    try:
                        service_instance = injection.get_instance()
                        bound_args.arguments[param_name] = service_instance
                    except RuntimeError:
                        # 如果无法获取服务实例，跳过注入
                        pass
            
            # 调用原函数
            return func(**bound_args.arguments)
        
        return wrapper
    
    return decorator


def inject_property(service_type: Type[T], fallback_factory: Optional[Callable[[], T]] = None):
    """装饰器：创建注入属性
    
    为类添加自动注入的属性。
    
    Args:
        service_type: 服务类型
        fallback_factory: fallback工厂函数
        
    Returns:
        属性描述符
        
    Example:
        ```python
        class MyService:
            logger = inject_property(ILogger)
            llm_manager = inject_property(ILLMManager)
            
            def process_data(self):
                self.logger.info("处理数据")
                return self.llm_manager.process("test")
        ```
    """
    class InjectedProperty:
        def __init__(self):
            self._injection = get_global_injection_registry().register(service_type, fallback_factory)
            self._attr_name = f'_injected_{service_type.__name__.lower()}'
        
        def __get__(self, instance, owner) -> T:
            if instance is None:
                return self._injection.get_instance()
            
            # 实例级别缓存
            if not hasattr(instance, self._attr_name):
                setattr(instance, self._attr_name, self._injection.get_instance())
            
            return getattr(instance, self._attr_name)
        
        def __set_name__(self, owner, name):
            self._attr_name = f'_injected_{name}'
    
    return InjectedProperty()


# 便捷函数
def create_service_getter(service_type: Type[T], fallback_factory: Optional[Callable[[], T]] = None) -> Callable[[], T]:
    """创建服务获取函数
    
    Args:
        service_type: 服务类型
        fallback_factory: fallback工厂函数
        
    Returns:
        服务获取函数
        
    Example:
        ```python
        get_logger = create_service_getter(ILogger)
        get_llm_manager = create_service_getter(ILLMManager)
        
        # 使用
        logger = get_logger()
        llm = get_llm_manager()
        ```
    """
    injection = get_global_injection_registry().register(service_type, fallback_factory)
    
    def getter() -> T:
        return injection.get_instance()
    
    # 添加额外方法
    getter_cast = cast(Any, getter)
    getter_cast.set_instance = injection.set_instance
    getter_cast.clear_instance = injection.clear_instance
    getter_cast.is_initialized = lambda: injection.is_initialized
    getter_cast.get_status = injection.get_status
    
    return getter