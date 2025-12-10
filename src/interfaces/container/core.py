"""
依赖注入容器核心接口

定义容器的基础数据类型和核心接口。
"""

from abc import ABC, abstractmethod
from typing import List, Type, TypeVar, Dict, Any, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass

from ..config import ValidationResult

# 泛型类型变量
_ServiceT = TypeVar("_ServiceT")


'''
基础枚举和数据类型
'''

class ServiceLifetime(str, Enum):
    """
    服务生命周期枚举
    
    定义依赖注入容器中服务的生命周期类型。
    """
    SINGLETON = "singleton"  # 单例模式，整个应用生命周期内只有一个实例
    TRANSIENT = "transient"  # 瞬态模式，每次请求都创建新实例
    SCOPED = "scoped"       # 作用域模式，在特定作用域内是单例

class ServiceStatus(Enum):
    """
    服务状态枚举
    
    定义服务在容器中的生命周期状态。
    """
    REGISTERED = "registered"      # 已注册
    CREATING = "creating"          # 创建中
    CREATED = "created"            # 已创建
    INITIALIZING = "initializing"  # 初始化中
    INITIALIZED = "initialized"    # 已初始化
    STOPPED = "stopped"            # 已停止
    DISPOSING = "disposing"        # 释放中
    DISPOSED = "disposed"          # 已释放


@dataclass
class ServiceRegistration:
    """
    服务注册信息
    
    封装服务注册的详细信息，包括接口类型、实现类型、生命周期等。
    
    Attributes:
        interface: 接口类型
        implementation: 实现类型（可选）
        factory: 工厂函数（可选）
        instance: 服务实例（可选）
        lifetime: 生命周期类型
        environment: 环境名称
        metadata: 元数据字典
    """
    interface: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable[..., Any]] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    environment: str = "default"
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_factory_registration(self) -> bool:
        """检查是否为工厂注册"""
        return self.factory is not None
    
    @property
    def is_instance_registration(self) -> bool:
        """检查是否为实例注册"""
        return self.instance is not None
    
    @property
    def is_type_registration(self) -> bool:
        """检查是否为类型注册"""
        return self.implementation is not None
    
    def validate(self) -> List[str]:
        """
        验证注册信息
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 检查至少有一种实现方式
        if not any([self.implementation, self.factory, self.instance]):
            errors.append("必须提供 implementation、factory 或 instance 中的一个")
        
        # 检查不能同时提供多种实现方式
        implementation_count = sum([
            1 for item in [self.implementation, self.factory, self.instance]
            if item is not None
        ])
        if implementation_count > 1:
            errors.append("只能提供 implementation、factory 或 instance 中的一种")
        
        # 检查类型注册的实现类型
        if self.implementation and not isinstance(self.implementation, type):
            errors.append("implementation 必须是类型")
        
        # 检查工厂注册的工厂类型
        if self.factory and not callable(self.factory):
            errors.append("factory 必须是可调用对象")
        
        return errors


@dataclass
class DependencyChain:
    """
    依赖链信息
    
    表示服务之间的依赖关系链，用于循环依赖检测。
    
    Attributes:
        service_type: 服务类型
        dependencies: 依赖的服务类型列表
        depth: 依赖深度
    """
    service_type: Type
    dependencies: List[Type]
    depth: int
    
    def has_circular_dependency(self) -> bool:
        """
        检查是否存在循环依赖
        
        Returns:
            bool: 如果存在循环依赖返回True
        """
        return self.service_type in self.dependencies
    
    def get_circular_path(self) -> Optional[List[Type]]:
        """
        获取循环依赖路径
        
        Returns:
            Optional[List[Type]]: 循环依赖路径，如果不存在循环依赖则返回None
        """
        if not self.has_circular_dependency():
            return None
        
        # 找到循环开始的位置
        try:
            index = self.dependencies.index(self.service_type)
            return self.dependencies[index:] + [self.service_type]
        except ValueError:
            return None


'''
核心容器接口
'''

class IDependencyContainer(ABC):
    """
    依赖注入容器主接口
    
    组合服务注册和解析功能，提供完整的依赖注入容器功能。
    这是基础设施层的核心接口，为整个系统提供依赖注入支持。
    
    主要职责：
    - 服务注册管理
    - 服务实例解析
    - 生命周期管理
    - 环境切换支持
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
        
        Args:
            interface: 接口类型
            implementation: 实现类型
            environment: 环境名称
            lifetime: 生命周期类型
            metadata: 元数据
            
        Raises:
            RegistrationError: 注册失败时抛出
            TypeError: 参数类型错误时抛出
        """
        pass
    
    @abstractmethod
    def register_factory(
        self,
        interface: Type,
        factory: Callable[..., Any],
        environment: str = "default",
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册服务工厂
        
        Args:
            interface: 接口类型
            factory: 工厂函数
            environment: 环境名称
            lifetime: 生命周期类型
            metadata: 元数据
            
        Raises:
            RegistrationError: 注册失败时抛出
            TypeError: 参数类型错误时抛出
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
        
        Args:
            interface: 接口类型
            instance: 服务实例
            environment: 环境名称
            metadata: 元数据
            
        Raises:
            RegistrationError: 注册失败时抛出
            TypeError: 参数类型错误时抛出
        """
        pass
    
    @abstractmethod
    def get(self, service_type: Type[_ServiceT]) -> _ServiceT:
        """
        获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            _ServiceT: 服务实例
            
        Raises:
            ServiceNotFoundError: 服务未找到时抛出
            ServiceCreationError: 服务创建失败时抛出
        """
        pass
    
    @abstractmethod
    def register_factory_with_delayed_resolution(
        self,
        interface: Type,
        factory_factory: Callable[[], Callable[..., Any]],
        environment: str = "default",
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册延迟解析的工厂工厂
        
        这种方式允许在工厂函数中解析依赖，避免注册阶段的循环依赖。
        
        Args:
            interface: 接口类型
            factory_factory: 工厂工厂函数，返回实际的工厂函数
            environment: 环境名称
            lifetime: 生命周期类型
            metadata: 元数据
            
        Raises:
            RegistrationError: 注册失败时抛出
            TypeError: 参数类型错误时抛出
        """
        pass
    
    @abstractmethod
    def resolve_dependencies(self, service_types: List[Type]) -> Dict[Type, Any]:
        """
        批量解析依赖
        
        Args:
            service_types: 要解析的服务类型列表
            
        Returns:
            Dict[Type, Any]: 服务类型到实例的映射
            
        Raises:
            ServiceNotFoundError: 服务未找到时抛出
            ServiceCreationError: 服务创建失败时抛出
            CircularDependencyError: 存在循环依赖时抛出
        """
        pass
    
    @abstractmethod
    def try_get(self, service_type: Type[_ServiceT]) -> Optional[_ServiceT]:
        """
        尝试获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            Optional[_ServiceT]: 服务实例，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def has_service(self, service_type: Type) -> bool:
        """
        检查服务是否已注册
        
        Args:
            service_type: 服务类型
            
        Returns:
            bool: 是否已注册
        """
        pass
    
    @abstractmethod
    def get_environment(self) -> str:
        """
        获取当前环境
        
        Returns:
            str: 当前环境名称
        """
        pass
    
    @abstractmethod
    def set_environment(self, env: str) -> None:
        """
        设置当前环境
        
        Args:
            env: 环境名称
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        清除所有服务和缓存
        
        清除容器中的所有注册信息、缓存和实例。
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> ValidationResult:
        """
        验证容器配置
        
        检查容器配置的有效性，包括循环依赖、类型兼容性等。
        
        Returns:
            ValidationResult: 验证结果
        """
        pass
    
    @abstractmethod
    def get_registration_count(self) -> int:
        """
        获取注册的服务数量
        
        Returns:
            int: 已注册的服务数量
        """
        pass
    
    @abstractmethod
    def get_registered_services(self) -> List[Type]:
        """
        获取已注册的服务类型列表
        
        Returns:
            List[Type]: 已注册的服务类型列表
        """
        pass
    
    @abstractmethod
    def create_test_isolation(self, isolation_id: Optional[str] = None) -> "IDependencyContainer":
        """
        创建测试隔离容器
        
        Args:
            isolation_id: 隔离ID
            
        Returns:
            IDependencyContainer: 隔离的容器实例
        """
        pass
    
    @abstractmethod
    def reset_test_state(self, isolation_id: Optional[str] = None) -> None:
        """
        重置测试状态
        
        Args:
            isolation_id: 隔离ID
        """
        pass