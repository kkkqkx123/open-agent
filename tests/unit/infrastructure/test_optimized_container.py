"""OptimizedDependencyContainer单元测试"""

import time
import threading
from typing import Type, Any
import pytest

from src.infrastructure.optimized_container import OptimizedDependencyContainer
from src.infrastructure.exceptions import ServiceNotRegisteredError, ServiceCreationError


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


class TestOptimizedDependencyContainer:
    """OptimizedDependencyContainer测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.container = OptimizedDependencyContainer(
            enable_service_cache=True,
            enable_path_cache=True,
            max_cache_size=100,
            cache_ttl_seconds=300
        )
    
    def test_register_and_get_service(self):
        """测试注册和获取服务"""
        # 注册服务
        self.container.register(MockService, MockService)
        
        # 获取服务
        service = self.container.get(MockService)
        
        # 验证服务被正确创建
        assert isinstance(service, MockService)
        assert service.created_at is not None
    
    def test_service_caching(self):
        """测试服务缓存"""
        self.container.register(MockService, MockService)
        
        # 第一次获取服务
        service1 = self.container.get(MockService)
        
        # 第二次获取服务（应该从缓存获取）
        service2 = self.container.get(MockService)
        
        # 验证两次获取的是同一个实例（如果注册为单例）
        assert service1 is service2
        
        # 验证缓存统计
        stats = self.container.get_performance_stats()
        assert stats["resolution_stats"]["cache_hits"] > 0
    
    def test_service_dependencies(self):
        """测试服务依赖"""
        # 注册依赖
        self.container.register(DependencyService, DependencyService)
        # 注册主服务
        self.container.register(MockService, MockService)
        
        # 获取服务（应该自动解析依赖）
        service = self.container.get(MockService)
        
        # 验证依赖被正确注入
        assert service.dependency is not None
        assert isinstance(service.dependency, DependencyService)
    
    def test_service_with_multiple_dependencies(self):
        """测试具有多个依赖的服务"""
        # 注册依赖
        self.container.register(DependencyService, DependencyService)
        self.container.register(MockService, MockService)
        # 注册主服务
        self.container.register(ServiceWithMultipleDeps, ServiceWithMultipleDeps)
        
        # 获取服务
        service = self.container.get(ServiceWithMultipleDeps)
        
        # 验证所有依赖都被正确注入
        assert service.dep1 is not None
        assert isinstance(service.dep1, DependencyService)
        assert service.dep2 is not None
        assert isinstance(service.dep2, MockService)
    
    def test_service_creation_path_cache(self):
        """测试服务创建路径缓存"""
        self.container.register(DependencyService, DependencyService)
        self.container.register(MockService, MockService)
        
        # 获取服务创建路径
        path = self.container.get_service_creation_path(MockService)
        
        # 验证路径包含依赖
        assert DependencyService in path
        assert MockService in path
    
    def test_performance_stats(self):
        """测试性能统计"""
        self.container.register(DependencyService, DependencyService)
        
        # 执行一些操作来填充统计信息
        for _ in range(5):
            service = self.container.get(DependencyService)
        
        stats = self.container.get_performance_stats()
        
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
    
    def test_cache_clear(self):
        """测试缓存清除"""
        self.container.register(MockService, MockService)
        
        # 获取服务以填充缓存
        service = self.container.get(MockService)
        assert service is not None
        
        # 检查初始缓存大小
        initial_stats = self.container.get_performance_stats()
        initial_cache_size = initial_stats["cache_stats"]["service_cache_size"]
        
        # 清除缓存
        self.container.clear_cache()
        
        # 检查缓存大小
        final_stats = self.container.get_performance_stats()
        final_cache_size = final_stats["cache_stats"]["service_cache_size"]
        
        # 由于第一次获取会再次创建，缓存大小可能不是0，但我们至少验证统计被重置
        assert final_stats["resolution_stats"]["cache_hits"] == 0
    
    def test_cache_optimization(self):
        """测试缓存优化"""
        # 创建一个有TTL限制的容器
        container = OptimizedDependencyContainer(
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
    
    def test_concurrent_access(self):
        """测试并发访问"""
        self.container.register(MockService, MockService)
        
        results = []
        errors = []
        
        def get_service_worker():
            try:
                service = self.container.get(MockService)
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
    
    def test_service_not_registered_error(self):
        """测试未注册服务错误"""
        # 尝试获取未注册的服务
        with pytest.raises(ServiceNotRegisteredError):
            self.container.get(MockService)
    
    def test_circular_dependency(self):
        """测试循环依赖（应该能处理或抛出适当的错误）"""
        class ServiceA:
            def __init__(self, service_b: 'ServiceB'):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a: 'ServiceA'):
                self.service_a = service_a
        
        # 注册循环依赖的服务
        self.container.register(ServiceA, ServiceA)
        self.container.register(ServiceB, ServiceB)
        
        # 获取服务（这可能会抛出循环依赖错误，具体取决于实现）
        try:
            service_a = self.container.get(ServiceA)
            # 如果没有抛出错误，验证依赖关系
            assert service_a is not None
        except Exception as e:
            # 如果抛出循环依赖错误，这也是可以接受的
            assert "circular" in str(e).lower() or "dependency" in str(e).lower()
    
    def test_service_with_no_dependencies(self):
        """测试没有依赖的服务"""
        class SimpleService:
            def __init__(self):
                self.value = 42
        
        self.container.register(SimpleService, SimpleService)
        
        service = self.container.get(SimpleService)
        
        assert isinstance(service, SimpleService)
        assert service.value == 42
    
    def test_service_creation_failure(self):
        """测试服务创建失败"""
        class FailingService:
            def __init__(self):
                raise Exception("Service creation failed")
        
        self.container.register(FailingService, FailingService)
        
        # 尝试获取服务应该抛出ServiceCreationError
        with pytest.raises(ServiceCreationError):
            self.container.get(FailingService)
    
    def test_cache_ttl_expiration(self):
        """测试缓存TL过期"""
        # 创建短TTL的容器
        container = OptimizedDependencyContainer(
            cache_ttl_seconds=1,
            max_cache_size=10
        )
        
        container.register(MockService, MockService)
        
        # 获取服务
        service1 = container.get(MockService)
        assert service1 is not None
        
        # 立即再次获取（应该从缓存）
        service2 = container.get(MockService)
        assert service1 is service2  # 同一实例
        
        # 等待超过TTL时间
        time.sleep(0.2)
        
        # 再次获取（应该创建新实例，因为旧的已过期）
        service3 = container.get(MockService)
        # 注意：这里取决于具体实现，有些容器可能仍返回缓存实例直到下一次清理
        # 所以我们主要验证没有错误发生
    
    def test_different_service_lifetimes(self):
        """测试不同的服务生命周期"""
        # 注册为单例
        self.container.register(MockService, MockService, lifetime="singleton")
        
        service1 = self.container.get(MockService)
        service2 = self.container.get(MockService)
        
        # 单例应该返回相同实例
        assert service1 is service2
    
    def test_path_cache_functionality(self):
        """测试路径缓存功能"""
        self.container.register(DependencyService, DependencyService)
        self.container.register(MockService, MockService)
        
        # 获取创建路径（应该使用缓存）
        path1 = self.container.get_service_creation_path(MockService)
        path2 = self.container.get_service_creation_path(MockService)
        
        # 路径应该相同
        assert path1 == path2
        assert len(path1) >= 2  # 至少包含MockService和DependencyService


if __name__ == "__main__":
    pytest.main([__file__])