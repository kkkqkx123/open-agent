"""
容器核心单元测试
"""

import pytest
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime
from src.infrastructure.container.dependency_container import DependencyContainer

class TestService:
    """测试服务类"""
    def __init__(self):
        self.value = "test"

class TestServiceFactory:
    """测试服务工厂类"""
    def __init__(self):
        self.value = "factory"
    
    @staticmethod
    def create():
        return TestServiceFactory()

def test_container_register_and_get():
    """测试容器注册和获取服务"""
    container = DependencyContainer()
    
    # 注册服务
    container.register(TestService, TestService, ServiceLifetime.SINGLETON)
    
    # 获取服务
    service = container.get(TestService)
    
    assert service is not None
    assert isinstance(service, TestService)
    assert service.value == "test"

def test_container_register_factory():
    """测试容器注册工厂"""
    container = DependencyContainer()
    
    # 注册工厂
    container.register_factory(TestService, TestServiceFactory.create, ServiceLifetime.SINGLETON)
    
    # 获取服务
    service = container.get(TestService)
    
    assert service is not None
    assert isinstance(service, TestServiceFactory)
    assert service.value == "factory"

def test_container_singleton():
    """测试单例模式"""
    container = DependencyContainer()
    
    # 注册单例服务
    container.register(TestService, TestService, ServiceLifetime.SINGLETON)
    
    # 获取两次服务
    service1 = container.get(TestService)
    service2 = container.get(TestService)
    
    # 应该是同一个实例
    assert service1 is service2

def test_container_transient():
    """测试瞬态模式"""
    container = DependencyContainer()
    
    # 注册瞬态服务
    container.register(TestService, TestService, ServiceLifetime.TRANSIENT)
    
    # 获取两次服务
    service1 = container.get(TestService)
    service2 = container.get(TestService)
    
    # 应该是不同的实例
    assert service1 is not service2

def test_container_has_service():
    """测试检查服务是否已注册"""
    container = DependencyContainer()
    
    # 注册前检查
    assert not container.has_service(TestService)
    
    # 注册服务
    container.register(TestService, TestService, ServiceLifetime.SINGLETON)
    
    # 注册后检查
    assert container.has_service(TestService)

def test_container_get_unregistered_service():
    """测试获取未注册的服务"""
    container = DependencyContainer()
    
    # 尝试获取未注册的服务
    with pytest.raises(ValueError, match="服务未注册"):
        container.get(TestService)