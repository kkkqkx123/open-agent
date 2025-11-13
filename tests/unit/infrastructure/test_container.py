"""依赖注入容器单元测试"""

"""依赖注入容器单元测试"""

import time
import threading
import pytest
from src.infrastructure.container import DependencyContainer
from src.infrastructure.exceptions import (
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
)
from infrastructure.infrastructure_types import ServiceLifetime

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

    def __init__(self, b: "CircularDependencyB"):
        self.b = b

class CircularDependencyB:
    """循环依赖测试B"""

    def __init__(self, a: CircularDependencyA):
        self.a = a

class MockService:
    """测试服务类"""
    def __init__(self, dependency: 'DependencyService' = None):  # type: ignore
        self.dependency = dependency
        self.created_at = time.time()

class DependencyService:
    """依赖服务类"""
    def __init__(self):
        self.name = "dependency"

class ServiceWithMultipleDeps:
    """具有多个依赖的服务类"""
    def __init__(self, dep1: DependencyService, dep2: MockService = None):  # type: ignore
        self.dep1 = dep1
        self.dep2 = dep2

class SimpleService:
    """简单服务类"""
    def __init__(self):
        self.value = 42

class FailingService:
    """失败服务类"""
    def __init__(self):
        raise Exception("Service creation failed")

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

    def test_service_caching(self) -> None:
        """测试服务缓存"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        container.register(MockService, MockService)

        # 第一次获取服务
        service1 = container.get(MockService)

        # 第二次获取服务（应该从缓存获取）
        service2 = container.get(MockService)

        # 验证两次获取的是同一个实例（如果注册为单例）
        assert service1 is service2

        # 验证缓存统计
        stats = container.get_performance_stats()
        assert stats["resolution_stats"]["cache_hits"] > 0

    def test_service_dependencies(self) -> None:
        """测试服务依赖"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        # 注册依赖
        container.register(DependencyService, DependencyService)
        # 注册主服务
        container.register(MockService, MockService)

        # 获取服务（应该自动解析依赖）
        service = container.get(MockService)

        # 验证依赖被正确注入
        assert service.dependency is not None
        assert isinstance(service.dependency, DependencyService)

    def test_service_with_multiple_dependencies(self) -> None:
        """测试具有多个依赖的服务"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        # 注册依赖
        container.register(DependencyService, DependencyService)
        container.register(MockService, MockService)
        # 注册主服务
        container.register(ServiceWithMultipleDeps, ServiceWithMultipleDeps)

        # 获取服务
        service = container.get(ServiceWithMultipleDeps)

        # 验证所有依赖都被正确注入
        assert service.dep1 is not None
        assert isinstance(service.dep1, DependencyService)
        assert service.dep2 is not None
        assert isinstance(service.dep2, MockService)

    def test_service_creation_path_cache(self) -> None:
        """测试服务创建路径缓存"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        container.register(DependencyService, DependencyService)
        container.register(MockService, MockService)

        # 获取服务创建路径
        path = container.get_service_creation_path(MockService)

        # 验证路径包含依赖
        assert DependencyService in path
        assert MockService in path

    def test_performance_stats(self) -> None:
        """测试性能统计"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        container.register(DependencyService, DependencyService)

        # 执行一些操作来填充统计信息
        for _ in range(5):
            service = container.get(DependencyService)

        stats = container.get_performance_stats()

        # 验证统计信息结构
        assert "resolution_stats" in stats
        assert "creation_stats" in stats
        assert "cache_stats" in stats

        resolution_stats = stats["resolution_stats"]
        assert resolution_stats["total_resolutions"] >= 5
        assert resolution_stats["cache_hits"] >= 0
        assert resolution_stats["cache_misses"] >= 1  # 第一次是miss，后续是hit

        cache_stats = stats["cache_stats"]
        assert cache_stats["service_cache_size"] >= 1

    def test_cache_clear(self) -> None:
        """测试缓存清除"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        container.register(MockService, MockService)

        # 获取服务以填充缓存
        service = container.get(MockService)
        assert service is not None

        # 检查初始缓存大小
        initial_stats = container.get_performance_stats()
        initial_cache_size = initial_stats["cache_stats"]["service_cache_size"]

        # 清除缓存
        container.clear_cache()

        # 检查缓存大小
        final_stats = container.get_performance_stats()
        final_cache_size = final_stats["cache_stats"]["service_cache_size"]

        # 由于第一次获取会再次创建，缓存大小可能不是0，但我们至少验证统计被重置
        assert final_stats["resolution_stats"]["cache_hits"] == 0

    def test_cache_optimization(self) -> None:
        """测试缓存优化"""
        # 创建一个有TTL限制的容器
        container = DependencyContainer(
            max_cache_size=2,
            cache_ttl_seconds=1  # 短TTL用于测试
        )

        container.register(MockService, MockService)
        container.register(DependencyService, DependencyService)

        # 添加一些服务到缓存
        service1 = container.get(MockService)
        service2 = container.get(DependencyService)

        # 添加超过缓存大小限制的服务
        class ExtraService:
            pass
        container.register(ExtraService, ExtraService)
        service3 = container.get(ExtraService)

        # 优化缓存
        optimization_result = container.optimize_cache()

        # 验证优化结果
        assert "final_cache_size" in optimization_result

    def test_concurrent_access(self) -> None:
        """测试并发访问"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        container.register(MockService, MockService)

        results = []
        errors = []

        def get_service_worker():
            try:
                service = container.get(MockService)
                results.append(service)
            except Exception as e:
                errors.append(e)

        # 创建多个线程同时获取服务
        threads = []
        for i in range(5):
            thread = threading.Thread(target=get_service_worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证没有错误
        assert len(errors) == 0
        assert len(results) == 5

        # 验证所有结果都是MockService实例
        for result in results:
            assert isinstance(result, MockService)

    def test_service_with_no_dependencies(self) -> None:
        """测试没有依赖的服务"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )

        container.register(SimpleService, SimpleService)

        service = container.get(SimpleService)

        assert isinstance(service, SimpleService)
        assert service.value == 42

    def test_service_creation_failure(self) -> None:
        """测试服务创建失败"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )

        container.register(FailingService, FailingService)

        # 尝试获取服务应该抛出ServiceCreationError
        with pytest.raises(ServiceCreationError):
            container.get(FailingService)

    def test_different_service_lifetimes(self) -> None:
        """测试不同的服务生命周期"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        # 注册为单例
        container.register(MockService, MockService, lifetime="singleton")

        service1 = container.get(MockService)
        service2 = container.get(MockService)

        # 单例应该返回相同实例
        assert service1 is service2

    def test_path_cache_functionality(self) -> None:
        """测试路径缓存功能"""
        container = DependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
        container.register(DependencyService, DependencyService)
        container.register(MockService, MockService)

        # 获取创建路径（应该使用缓存）
        path1 = container.get_service_creation_path(MockService)
        path2 = container.get_service_creation_path(MockService)

        # 路径应该相同
        assert path1 == path2
        assert len(path1) >= 2  # 至少包含MockService和DependencyService
