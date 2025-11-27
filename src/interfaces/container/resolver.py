"""
服务解析接口

定义服务解析和创建的相关接口，支持多种解析策略和缓存机制。
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, List, Any, Dict

# 泛型类型变量
_T = TypeVar('_T')


'''
服务解析接口
'''

class IServiceResolver(ABC):
    """
    服务解析接口
    
    负责服务的解析和创建，支持多种解析策略和缓存机制。
    这是依赖注入容器的核心组件之一，专注于服务解析功能。
    
    主要功能：
    - 服务实例解析
    - 多实现支持
    - 命名服务支持
    - 解析缓存
    - 循环依赖检测
    
    使用示例：
        ```python
        # 基本解析
        user_service = resolver.get(IUserService)
        
        # 尝试解析
        logger = resolver.try_get(ILogger)
        
        # 获取所有实现
        all_handlers = resolver.get_all(IMessageHandler)
        
        # 命名服务解析
        primary_db = resolver.get_named(IDatabase, "primary")
        ```
    """
    
    @abstractmethod
    def get(self, service_type: Type[_T]) -> _T:
        """
        获取服务实例
        
        根据服务类型解析并返回服务实例。如果服务尚未创建，
        将根据注册信息创建新实例。
        
        Args:
            service_type: 服务类型
            
        Returns:
            _T: 服务实例
            
        Raises:
            ServiceNotFoundError: 服务未注册时抛出
            ServiceCreationError: 服务创建失败时抛出
            CircularDependencyError: 检测到循环依赖时抛出
            
        Examples:
            ```python
            # 基本用法
            user_service = resolver.get(IUserService)
            
            # 泛型用法
            repository = resolver.get(IRepository[User])
            
            # 嵌套解析
            class OrderService:
                def __init__(self, user_service: IUserService):
                    self.user_service = user_service
            
            order_service = resolver.get(OrderService)
            ```
        """
        pass
    
    @abstractmethod
    def try_get(self, service_type: Type[_T]) -> Optional[_T]:
        """
        尝试获取服务实例
        
        与 get() 方法不同，如果服务未注册或创建失败，
        此方法不会抛出异常，而是返回 None。
        
        Args:
            service_type: 服务类型
            
        Returns:
            Optional[_T]: 服务实例，如果不存在则返回None
            
        Examples:
            ```python
            # 安全获取
            logger = resolver.try_get(ILogger)
            if logger:
                logger.info("Service resolved successfully")
            else:
                print("Logger not available")
            
            # 条件解析
            cache = resolver.try_get(ICacheService)
            if cache:
                cached_data = cache.get("key")
            else:
                data = fetch_from_database()
            ```
        """
        pass
    
    @abstractmethod
    def get_all(self, interface: Type) -> List[Any]:
        """
        获取接口的所有实现
        
        当一个接口有多个实现时，此方法返回所有实现实例。
        
        Args:
            interface: 接口类型
            
        Returns:
            List[Any]: 实现实例列表
            
        Raises:
            ServiceNotFoundError: 接口未注册时抛出
            
        Examples:
            ```python
            # 获取所有消息处理器
            handlers = resolver.get_all(IMessageHandler)
            for handler in handlers:
                handler.process(message)
            
            # 获取所有插件
            plugins = resolver.get_all(IPlugin)
            for plugin in plugins:
                plugin.initialize()
            ```
        """
        pass
    
    @abstractmethod
    def get_named(self, interface: Type, name: str) -> Any:
        """
        按名称获取服务实例
        
        支持命名服务注册，允许同一接口的多个实现通过名称区分。
        
        Args:
            interface: 接口类型
            name: 服务名称
            
        Returns:
            Any: 服务实例
            
        Raises:
            ServiceNotFoundError: 命名服务未注册时抛出
            
        Examples:
            ```python
            # 注册命名服务
            registry.register_named(IDatabase, "primary", PrimaryDatabase)
            registry.register_named(IDatabase, "backup", BackupDatabase)
            
            # 获取命名服务
            primary_db = resolver.get_named(IDatabase, "primary")
            backup_db = resolver.get_named(IDatabase, "backup")
            
            # 使用不同的数据库
            data = primary_db.query("SELECT * FROM users")
            backup_data = backup_db.query("SELECT * FROM users")
            ```
        """
        pass
    
    @abstractmethod
    def try_get_named(self, interface: Type, name: str) -> Optional[Any]:
        """
        尝试按名称获取服务实例
        
        安全版本的命名服务解析，不会抛出异常。
        
        Args:
            interface: 接口类型
            name: 服务名称
            
        Returns:
            Optional[Any]: 服务实例，如果不存在则返回None
            
        Examples:
            ```python
            # 安全获取命名服务
            cache = resolver.try_get_named(ICache, "redis")
            if cache:
                cache.set("key", "value")
            else:
                # 使用默认缓存
                default_cache = resolver.get(ICache)
                default_cache.set("key", "value")
            ```
        """
        pass
    
    @abstractmethod
    def can_resolve(self, service_type: Type) -> bool:
        """
        检查是否可以解析指定类型的服务
        
        Args:
            service_type: 服务类型
            
        Returns:
            bool: 是否可以解析
            
        Examples:
            ```python
            # 检查服务可用性
            if resolver.can_resolve(IUserService):
                user_service = resolver.get(IUserService)
            else:
                print("User service not available")
            
            # 条件功能
            if resolver.can_resolve(ICacheService):
                enable_caching()
            else:
                disable_caching()
            ```
        """
        pass
    
    @abstractmethod
    def get_resolution_path(self, service_type: Type) -> List[Type]:
        """
        获取服务解析路径
        
        返回服务解析过程中的依赖链，用于调试和监控。
        
        Args:
            service_type: 服务类型
            
        Returns:
            List[Type]: 依赖类型列表
            
        Examples:
            ```python
            # 调试依赖关系
            path = resolver.get_resolution_path(OrderService)
            print(f"Resolution path: {[t.__name__ for t in path]}")
            
            # 监控解析深度
            depth = len(resolver.get_resolution_path(ComplexService))
            if depth > 5:
                logger.warning(f"Deep dependency chain detected: {depth}")
            ```
        """
        pass
    
    @abstractmethod
    def warm_up(self, service_types: Optional[List[Type]] = None) -> Dict[Type, bool]:
        """
        预热服务
        
        预先创建指定的服务实例，减少首次访问的延迟。
        
        Args:
            service_types: 要预热的服务类型列表，None表示所有服务
            
        Returns:
            Dict[Type, bool]: 服务类型到预热结果的映射
            
        Examples:
            ```python
            # 预热关键服务
            critical_services = [IDatabase, ICache, ILogger]
            results = resolver.warm_up(critical_services)
            
            for service_type, success in results.items():
                if success:
                    print(f"Warmed up {service_type.__name__}")
                else:
                    print(f"Failed to warm up {service_type.__name__}")
            
            # 预热所有服务
            all_results = resolver.warm_up()
            success_count = sum(all_results.values())
            print(f"Warmed up {success_count}/{len(all_results)} services")
            ```
        """
        pass
    
    @abstractmethod
    def get_resolution_cache_stats(self) -> Dict[str, Any]:
        """
        获取解析缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
            
        Examples:
            ```python
            stats = resolver.get_resolution_cache_stats()
            print(f"Cache hits: {stats['hits']}")
            print(f"Cache misses: {stats['misses']}")
            print(f"Hit rate: {stats['hit_rate']:.2%}")
            print(f"Cache size: {stats['size']}")
            ```
        """
        pass
    
    @abstractmethod
    def clear_resolution_cache(self, service_type: Optional[Type] = None) -> int:
        """
        清除解析缓存
        
        Args:
            service_type: 要清除缓存的服务类型，None表示清除所有缓存
            
        Returns:
            int: 清除的缓存条目数量
            
        Examples:
            ```python
            # 清除特定服务的缓存
            cleared_count = resolver.clear_resolution_cache(IUserService)
            
            # 清除所有缓存
            total_cleared = resolver.clear_resolution_cache()
            print(f"Cleared {total_cleared} cache entries")
            ```
        """
        pass


'''
服务工厂接口
'''

class IServiceFactory(ABC):
    """
    服务工厂接口
    
    定义服务创建的契约，支持复杂的创建逻辑和依赖注入。
    """
    
    @abstractmethod
    def create_service(self, service_type: Type, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        创建服务实例
        
        Args:
            service_type: 服务类型
            context: 创建上下文
            
        Returns:
            Any: 服务实例
            
        Raises:
            ServiceCreationError: 创建失败时抛出
        """
        pass
    
    @abstractmethod
    def can_create(self, service_type: Type) -> bool:
        """
        检查是否可以创建指定类型的服务
        
        Args:
            service_type: 服务类型
            
        Returns:
            bool: 是否可以创建
        """
        pass


'''
解析策略接口
'''

class IResolutionStrategy(ABC):
    """
    解析策略接口
    
    定义服务解析的策略，支持不同的解析算法。
    """
    
    @abstractmethod
    def resolve(self, service_type: Type, resolver: IServiceResolver) -> Any:
        """
        解析服务
        
        Args:
            service_type: 服务类型
            resolver: 服务解析器
            
        Returns:
            Any: 服务实例
        """
        pass


'''
循环依赖检测接口
'''

class ICircularDependencyDetector(ABC):
    """
    循环依赖检测接口
    
    定义循环依赖检测的契约。
    """
    
    @abstractmethod
    def detect_circular_dependency(self, service_type: Type, dependency_graph: Dict[Type, List[Type]]) -> Optional[List[Type]]:
        """
        检测循环依赖
        
        Args:
            service_type: 起始服务类型
            dependency_graph: 依赖关系图
            
        Returns:
            Optional[List[Type]]: 循环依赖路径，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_dependency_depth(self, service_type: Type, dependency_graph: Dict[Type, List[Type]]) -> int:
        """
        计算依赖深度
        
        Args:
            service_type: 服务类型
            dependency_graph: 依赖关系图
            
        Returns:
            int: 依赖深度
        """
        pass