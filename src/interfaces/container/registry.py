"""
服务注册接口

定义服务注册和管理的相关接口，支持多种注册方式和环境管理。
"""

from abc import ABC, abstractmethod
from typing import Type, Dict, Any, Optional, List, Callable

from .core import ServiceRegistration, ServiceLifetime


'''
服务注册接口
'''

class IServiceRegistry(ABC):
    """
    服务注册接口
    
    负责服务的注册、注销和管理，支持多种注册方式和环境隔离。
    这是依赖注入容器的核心组件之一，专注于服务注册功能。
    
    主要功能：
    - 类型注册
    - 工厂注册
    - 实例注册
    - 环境管理
    - 注册验证
    
    使用示例：
        ```python
        # 类型注册
        registry.register(IUserService, UserService, lifetime=ServiceLifetime.SINGLETON)
        
        # 工厂注册
        registry.register_factory(IDatabaseService, create_database_connection)
        
        # 实例注册
        registry.register_instance(IConfigService, config_instance)
        
        # 环境特定注册
        registry.register(ILogger, TestLogger, environment="test")
        ```
    """
    
    @abstractmethod
    def register(
        self,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册服务实现
        
        将接口类型与实现类型关联，支持环境隔离和生命周期管理。
        
        Args:
            interface: 接口类型，必须是抽象基类或协议
            implementation: 实现类型，必须实现接口
            environment: 环境名称，用于环境隔离
            lifetime: 生命周期类型，决定实例的创建和销毁方式
            metadata: 元数据字典，用于存储额外的注册信息
            
        Raises:
            RegistrationError: 注册失败时抛出
            TypeError: 参数类型错误时抛出
            InterfaceError: 接口类型无效时抛出
            ImplementationError: 实现类型无效时抛出
            
        Examples:
            ```python
            # 基本注册
            registry.register(IUserService, UserService)
            
            # 带生命周期的注册
            registry.register(IRepository, SqlRepository, lifetime=ServiceLifetime.SCOPED)
            
            # 环境特定注册
            registry.register(ILogger, ConsoleLogger, environment="development")
            registry.register(ILogger, FileLogger, environment="production")
            
            # 带元数据的注册
            registry.register(
                ICacheService, 
                RedisCache,
                metadata={"max_size": 1000, "ttl": 3600}
            )
            ```
        """
        pass
    
    @abstractmethod
    def register_factory(
        self,
        interface: Type,
        factory: Callable,
        environment: str = "default",
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册服务工厂
        
        使用工厂函数来创建服务实例，适用于需要复杂初始化逻辑的场景。
        
        Args:
            interface: 接口类型
            factory: 工厂函数，必须返回接口的实例
            environment: 环境名称
            lifetime: 生命周期类型
            metadata: 元数据字典
            
        Raises:
            RegistrationError: 注册失败时抛出
            TypeError: 参数类型错误时抛出
            
        Examples:
            ```python
            # 简单工厂
            def create_database():
                return DatabaseConnection("localhost:5432")
            
            registry.register_factory(IDatabase, create_database)
            
            # 带参数的工厂
            def create_http_client():
                config = load_config()
                return HttpClient(config.base_url, config.timeout)
            
            registry.register_factory(IHttpClient, create_http_client)
            
            # lambda工厂
            registry.register_factory(
                ITimestampService,
                lambda: TimestampService(datetime.now())
            )
            ```
        """
        pass
    
    @abstractmethod
    def register_instance(
        self, 
        interface: Type, 
        instance: Any, 
        environment: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册服务实例
        
        直接注册已创建的服务实例，适用于单例对象或外部提供的实例。
        
        Args:
            interface: 接口类型
            instance: 服务实例，必须实现接口
            environment: 环境名称
            metadata: 元数据字典
            
        Raises:
            RegistrationError: 注册失败时抛出
            TypeError: 参数类型错误时抛出
            
        Examples:
            ```python
            # 注册配置实例
            config = ApplicationConfig()
            registry.register_instance(IConfig, config)
            
            # 注册外部服务
            external_db = ExternalDatabase()
            registry.register_instance(IDatabase, external_db)
            
            # 注册测试实例
            test_logger = TestLogger()
            registry.register_instance(ILogger, test_logger, environment="test")
            ```
        """
        pass
    
    @abstractmethod
    def unregister(self, interface: Type, environment: str = "default") -> bool:
        """
        注销服务
        
        移除指定接口和环境的注册信息。
        
        Args:
            interface: 接口类型
            environment: 环境名称
            
        Returns:
            bool: 是否成功注销
            
        Examples:
            ```python
            # 注销默认环境的服务
            success = registry.unregister(IUserService)
            
            # 注销特定环境的服务
            success = registry.unregister(ILogger, environment="test")
            ```
        """
        pass
    
    @abstractmethod
    def is_registered(self, interface: Type, environment: str = "default") -> bool:
        """
        检查服务是否已注册
        
        Args:
            interface: 接口类型
            environment: 环境名称
            
        Returns:
            bool: 是否已注册
            
        Examples:
            ```python
            if registry.is_registered(IUserService):
                user_service = container.get(IUserService)
            
            if registry.is_registered(ILogger, environment="production"):
                logger = container.get(ILogger)
            ```
        """
        pass
    
    @abstractmethod
    def get_registration(self, interface: Type, environment: str = "default") -> Optional[ServiceRegistration]:
        """
        获取服务注册信息
        
        Args:
            interface: 接口类型
            environment: 环境名称
            
        Returns:
            Optional[ServiceRegistration]: 注册信息，如果不存在则返回None
            
        Examples:
            ```python
            registration = registry.get_registration(IUserService)
            if registration:
                print(f"Lifetime: {registration.lifetime}")
                print(f"Metadata: {registration.metadata}")
            ```
        """
        pass
    
    @abstractmethod
    def list_registrations(self, environment: Optional[str] = None) -> List[ServiceRegistration]:
        """
        列出所有注册信息
        
        Args:
            environment: 环境名称过滤，None表示所有环境
            
        Returns:
            List[ServiceRegistration]: 注册信息列表
            
        Examples:
            ```python
            # 列出所有注册
            all_regs = registry.list_registrations()
            
            # 列出特定环境的注册
            prod_regs = registry.list_registrations("production")
            
            # 列出单例注册
            singleton_regs = [
                reg for reg in registry.list_registrations()
                if reg.lifetime == ServiceLifetime.SINGLETON
            ]
            ```
        """
        pass
    
    @abstractmethod
    def get_registered_interfaces(self, environment: Optional[str] = None) -> List[Type]:
        """
        获取已注册的接口类型列表
        
        Args:
            environment: 环境名称过滤，None表示所有环境
            
        Returns:
            List[Type]: 接口类型列表
            
        Examples:
            ```python
            interfaces = registry.get_registered_interfaces()
            for interface in interfaces:
                print(f"Registered: {interface.__name__}")
            ```
        """
        pass
    
    @abstractmethod
    def get_environments(self) -> List[str]:
        """
        获取所有环境名称
        
        Returns:
            List[str]: 环境名称列表
            
        Examples:
            ```python
            environments = registry.get_environments()
            print(f"Available environments: {environments}")
            ```
        """
        pass
    
    @abstractmethod
    def validate_registration(self, interface: Type, implementation: Type) -> List[str]:
        """
        验证注册信息
        
        在注册前验证接口和实现的有效性。
        
        Args:
            interface: 接口类型
            implementation: 实现类型
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
            
        Examples:
            ```python
            errors = registry.validate_registration(IUserService, UserService)
            if errors:
                for error in errors:
                    print(f"Validation error: {error}")
            else:
                registry.register(IUserService, UserService)
            ```
        """
        pass
    
    @abstractmethod
    def copy_registration(self, interface: Type, from_env: str, to_env: str) -> bool:
        """
        复制注册信息到另一个环境
        
        Args:
            interface: 接口类型
            from_env: 源环境名称
            to_env: 目标环境名称
            
        Returns:
            bool: 是否成功复制
            
        Examples:
            ```python
            # 将开发环境的配置复制到测试环境
            success = registry.copy_registration(IConfig, "development", "test")
            ```
        """
        pass
    
    @abstractmethod
    def get_registration_count(self, environment: Optional[str] = None) -> int:
        """
        获取注册数量
        
        Args:
            environment: 环境名称过滤，None表示所有环境
            
        Returns:
            int: 注册数量
            
        Examples:
            ```python
            total_count = registry.get_registration_count()
            prod_count = registry.get_registration_count("production")
            print(f"Total registrations: {total_count}")
            print(f"Production registrations: {prod_count}")
            ```
        """
        pass
    
    @abstractmethod
    def clear_registrations(self, environment: Optional[str] = None) -> int:
        """
        清除注册信息
        
        Args:
            environment: 环境名称，None表示清除所有环境
            
        Returns:
            int: 清除的注册数量
            
        Examples:
            ```python
            # 清除特定环境的注册
            cleared_count = registry.clear_registrations("test")
            
            # 清除所有注册
            total_cleared = registry.clear_registrations()
            ```
        """
        pass


'''
注册验证器接口
'''

class IRegistrationValidator(ABC):
    """
    注册验证器接口
    
    定义服务注册验证的契约，确保注册的有效性。
    """
    
    @abstractmethod
    def validate_interface(self, interface: Type) -> List[str]:
        """
        验证接口类型
        
        Args:
            interface: 接口类型
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def validate_implementation(self, interface: Type, implementation: Type) -> List[str]:
        """
        验证实现类型
        
        Args:
            interface: 接口类型
            implementation: 实现类型
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def validate_factory(self, interface: Type, factory: Callable) -> List[str]:
        """
        验证工厂函数
        
        Args:
            interface: 接口类型
            factory: 工厂函数
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def validate_instance(self, interface: Type, instance: Any) -> List[str]:
        """
        验证服务实例
        
        Args:
            interface: 接口类型
            instance: 服务实例
            
        Returns:
            List[str]: 验证错误列表
        """
        pass