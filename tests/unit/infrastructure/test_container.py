"""依赖注入容器单元测试"""

import pytest
from src.infrastructure.container import DependencyContainer
from src.infrastructure.exceptions import (
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError
)
from src.infrastructure.types import ServiceLifetime


# 测试接口和实现类
class IService:
    """测试服务接口"""
    pass


class ServiceA(IService):
    """测试服务实现A"""
    def __init__(self) -> None:
        self.name = "ServiceA"


class ServiceB(IService):
    """测试服务实现B"""
    def __init__(self) -> None:
        self.name = "ServiceB"


class ServiceWithDependency:
    """有依赖的服务"""
    def __init__(self, service: IService):
        self.service = service


class CircularDependencyA:
    """循环依赖测试A"""
    def __init__(self, b: 'CircularDependencyB'):
        self.b = b


class CircularDependencyB:
    """循环依赖测试B"""
    def __init__(self, a: CircularDependencyA):
        self.a = a


class TestDependencyContainer:
    """依赖注入容器测试"""
    
    def test_register_and_get_service(self) -> None:
        """测试服务注册和获取"""
        container = DependencyContainer()
        container.register(IService, ServiceA)
        
        service = container.get(IService)
        assert isinstance(service, ServiceA)
        assert service.name == "ServiceA"
    
    def test_service_not_registered(self) -> None:
        """测试未注册服务异常"""
        container = DependencyContainer()
        
        with pytest.raises(ServiceNotRegisteredError):
            container.get(IService)
    
    def test_environment_specific_registration(self) -> None:
        """测试环境特定注册"""
        container = DependencyContainer()
        
        container.register(IService, ServiceA, "development")
        container.register(IService, ServiceB, "production")
        
        # 测试开发环境
        container.set_environment("development")
        service = container.get(IService)
        assert isinstance(service, ServiceA)
        
        # 测试生产环境
        container.set_environment("production")
        service = container.get(IService)
        assert isinstance(service, ServiceB)
        
        # 测试默认环境（应该使用第一个注册的）
        container.set_environment("default")
        service = container.get(IService)
        assert isinstance(service, ServiceA)
    
    def test_service_lifetime_singleton(self) -> None:
        """测试单例生命周期"""
        container = DependencyContainer()
        container.register(IService, ServiceA, lifetime=ServiceLifetime.SINGLETON)
        
        service1 = container.get(IService)
        service2 = container.get(IService)
        
        assert service1 is service2
    
    def test_service_lifetime_transient(self) -> None:
        """测试瞬态生命周期"""
        container = DependencyContainer()
        container.register(IService, ServiceA, lifetime=ServiceLifetime.TRANSIENT)
        
        service1 = container.get(IService)
        service2 = container.get(IService)
        
        assert service1 is not service2
        assert isinstance(service1, ServiceA)
        assert isinstance(service2, ServiceA)
    
    def test_dependency_injection(self) -> None:
        """测试依赖注入"""
        container = DependencyContainer()
        container.register(IService, ServiceA)
        container.register(ServiceWithDependency, ServiceWithDependency)
        
        service = container.get(ServiceWithDependency)
        assert isinstance(service, ServiceWithDependency)
        assert isinstance(service.service, ServiceA)
    
    def test_register_factory(self) -> None:
        """测试工厂方法注册"""
        container = DependencyContainer()
        
        def factory() -> IService:
            return ServiceA()
        
        container.register_factory(IService, factory)
        
        service = container.get(IService)
        assert isinstance(service, ServiceA)
    
    def test_register_instance(self) -> None:
        """测试实例注册"""
        container = DependencyContainer()
        instance = ServiceA()
        
        container.register_instance(IService, instance)
        
        service = container.get(IService)
        assert service is instance
    
    def test_circular_dependency_detection(self) -> None:
        """测试循环依赖检测"""
        container = DependencyContainer()
        container.register(CircularDependencyA, CircularDependencyA)
        container.register(CircularDependencyB, CircularDependencyB)
        
        with pytest.raises(CircularDependencyError):
            container.get(CircularDependencyA)
    
    def test_has_service(self) -> None:
        """测试服务检查"""
        container = DependencyContainer()
        
        assert not container.has_service(IService)
        
        container.register(IService, ServiceA)
        assert container.has_service(IService)
    
    def test_clear(self) -> None:
        """测试清除服务"""
        container = DependencyContainer()
        container.register(IService, ServiceA)
        
        service = container.get(IService)
        assert service is not None
        
        container.clear()
        
        assert not container.has_service(IService)
        with pytest.raises(ServiceNotRegisteredError):
            container.get(IService)
    
    def test_get_registered_services(self) -> None:
        """测试获取已注册服务列表"""
        container = DependencyContainer()
        
        assert container.get_registered_services() == []
        
        container.register(IService, ServiceA)
        container.register(ServiceWithDependency, ServiceWithDependency)
        
        services = container.get_registered_services()
        assert IService in services
        assert ServiceWithDependency in services
        assert len(services) == 2
    
    def test_environment_change_clears_cache(self) -> None:
        """测试环境改变清除缓存"""
        container = DependencyContainer()
        container.register(IService, ServiceA, "development")
        container.register(IService, ServiceB, "production")
        
        # 获取开发环境服务
        container.set_environment("development")
        service1 = container.get(IService)
        
        # 切换到生产环境
        container.set_environment("production")
        service2 = container.get(IService)
        
        # 应该是不同的实例
        assert service1 is not service2
        assert isinstance(service1, ServiceA)
        assert isinstance(service2, ServiceB)