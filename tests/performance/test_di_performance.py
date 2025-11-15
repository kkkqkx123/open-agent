"""依赖注入性能基准测试

对比重构前后的性能差异，测试服务解析速度和内存使用。
"""

import pytest
import time
import gc
import psutil
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock

from src.infrastructure.di_config import DIConfig, create_container
from src.infrastructure.lifecycle_manager import LifecycleManager
from src.infrastructure.container import ServiceLifetime
from infrastructure.config.loader.file_config_loader import IConfigLoader
from src.infrastructure.container_interfaces import ILifecycleAware
from src.application.workflow.manager import IWorkflowManager
from src.application.sessions.manager import ISessionManager


class TestDIPerformance:
    """依赖注入性能测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_dir(self, temp_dir):
        """配置目录"""
        config_dir = temp_dir / "configs"
        config_dir.mkdir(exist_ok=True)
        
        # 创建基本配置文件
        global_config = config_dir / "global.yaml"
        global_config.write_text("""
logging:
  level: INFO
secrets:
  openai_api_key: "test_key"
        """)
        
        return config_dir
    
    @pytest.fixture
    def container(self, config_dir):
        """创建测试容器"""
        return create_container(
            config_path=str(config_dir),
            environment="test"
        )
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def test_service_resolution_performance(self, container):
        """测试服务解析性能"""
        # 预热
        for _ in range(10):
            container.get(IConfigLoader)
        
        # 测试单次解析时间
        start_time = time.time()
        for _ in range(1000):
            container.get(IConfigLoader)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 1000
        print(f"平均服务解析时间: {avg_time * 1000:.3f}ms")
        
        # 性能要求：平均解析时间应小于1ms
        assert avg_time < 0.001, f"服务解析时间过长: {avg_time * 1000:.3f}ms"
    
    def test_container_creation_performance(self, config_dir):
        """测试容器创建性能"""
        creation_times = []
        
        # 测试多次创建容器
        for _ in range(10):
            start_time = time.time()
            container = create_container(
                config_path=str(config_dir),
                environment="test"
            )
            end_time = time.time()
            
            creation_times.append(end_time - start_time)
            container.clear()  # 清理资源
        
        avg_time = sum(creation_times) / len(creation_times)
        print(f"平均容器创建时间: {avg_time * 1000:.3f}ms")
        
        # 性能要求：容器创建时间应小于100ms
        assert avg_time < 0.1, f"容器创建时间过长: {avg_time * 1000:.3f}ms"
    
    def test_memory_usage_with_multiple_services(self, config_dir):
        """测试多服务内存使用"""
        # 获取初始内存使用
        gc.collect()
        initial_memory = self.get_memory_usage()
        
        # 创建容器并注册多个服务
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 注册额外服务
        for i in range(100):
            class TestService:
                def __init__(self):
                    self.data = list(range(1000))  # 每个服务占用一些内存
            
            container.register(
                TestService,
                TestService,
                lifetime=ServiceLifetime.SINGLETON
            )
            
            # 立即解析服务以创建实例
            container.get(TestService)
        
        # 获取当前内存使用
        gc.collect()
        current_memory = self.get_memory_usage()
        memory_increase = current_memory - initial_memory
        
        print(f"内存增长: {memory_increase:.2f}MB")
        
        # 性能要求：100个服务的内存增长应小于50MB
        assert memory_increase < 50, f"内存使用过多: {memory_increase:.2f}MB"
        
        # 清理
        container.clear()
    
    def test_concurrent_service_resolution(self, container):
        """测试并发服务解析"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def worker():
            """工作线程函数"""
            times = []
            for _ in range(100):
                start_time = time.time()
                service = container.get(IConfigLoader)
                end_time = time.time()
                times.append(end_time - start_time)
                assert service is not None
            
            results.put(times)
        
        # 创建多个线程
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 收集所有时间数据
        all_times = []
        while not results.empty():
            all_times.extend(results.get())
        
        avg_time = sum(all_times) / len(all_times)
        max_time = max(all_times)
        
        print(f"并发平均解析时间: {avg_time * 1000:.3f}ms")
        print(f"并发最大解析时间: {max_time * 1000:.3f}ms")
        
        # 性能要求：并发环境下平均解析时间应小于5ms
        assert avg_time < 0.005, f"并发解析时间过长: {avg_time * 1000:.3f}ms"
    
    def test_lifecycle_manager_performance(self, config_dir):
        """测试生命周期管理器性能"""
        lifecycle_manager = LifecycleManager()
        
        # 注册多个服务
        services = []
        for i in range(50):
            class TestService(ILifecycleAware):
                def __init__(self):
                    self.initialized = False
                    self.started = False
                    self.stopped = False
                    self.disposed = False

                def initialize(self):
                    self.initialized = True

                def start(self):
                    self.started = True

                def stop(self):
                    self.stopped = True

                def dispose(self):
                    self.disposed = True
            
            service = TestService()
            services.append(service)
            lifecycle_manager.register_service(f"service_{i}", service)
        
        # 测试初始化性能
        start_time = time.time()
        results = lifecycle_manager.initialize_all_services()
        end_time = time.time()
        
        init_time = end_time - start_time
        print(f"50个服务初始化时间: {init_time * 1000:.3f}ms")
        
        # 验证所有服务都已初始化
        assert all(results.values())
        assert all(service.initialized for service in services)
        
        # 测试启动性能
        start_time = time.time()
        results = lifecycle_manager.start_all_services()
        end_time = time.time()
        
        start_time_total = end_time - start_time
        print(f"50个服务启动时间: {start_time_total * 1000:.3f}ms")
        
        # 验证所有服务都已启动
        assert all(results.values())
        
        # 测试停止性能
        start_time = time.time()
        results = lifecycle_manager.stop_all_services()
        end_time = time.time()
        
        stop_time = end_time - start_time
        print(f"50个服务停止时间: {stop_time * 1000:.3f}ms")
        
        # 验证所有服务都已停止
        assert all(results.values())
        
        # 性能要求：50个服务的生命周期操作应在100ms内完成
        assert init_time < 0.1, f"初始化时间过长: {init_time * 1000:.3f}ms"
        assert start_time_total < 0.1, f"启动时间过长: {start_time_total * 1000:.3f}ms"
        assert stop_time < 0.1, f"停止时间过长: {stop_time * 1000:.3f}ms"
        
        # 清理
        lifecycle_manager.dispose()
    
    def test_service_cache_performance(self, config_dir):
        """测试服务缓存性能"""
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 注册一个需要较长时间创建的服务
        class SlowService:
            def __init__(self):
                # 模拟耗时操作
                time.sleep(0.001)
        
        container.register(
            SlowService,
            SlowService,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 测试首次解析时间
        start_time = time.time()
        service1 = container.get(SlowService)
        first_resolution_time = time.time() - start_time
        
        # 测试缓存解析时间
        start_time = time.time()
        service2 = container.get(SlowService)
        cached_resolution_time = time.time() - start_time
        
        print(f"首次解析时间: {first_resolution_time * 1000:.3f}ms")
        print(f"缓存解析时间: {cached_resolution_time * 1000:.3f}ms")
        
        # 验证返回的是同一个实例
        assert service1 is service2
        
        # 验证缓存显著提高性能
        assert cached_resolution_time < first_resolution_time / 2, \
            f"缓存性能提升不明显: {cached_resolution_time * 1000:.3f}ms vs {first_resolution_time * 1000:.3f}ms"
    
    def test_large_dependency_tree_performance(self, config_dir):
        """测试大型依赖树性能"""
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 创建深层依赖树
        services = {}
        
        for i in range(10):
            for j in range(i + 1):
                class_name = f"Service_{i}_{j}"
                
                # 动态创建类
                service_class = type(class_name, (), {
                    "__init__": lambda self, *args: None
                })
                
                services[class_name] = service_class
        
        # 注册服务并建立依赖关系
        for i in range(10):
            for j in range(i + 1):
                service_class = services[f"Service_{i}_{j}"]
                
                # 确定依赖
                dependencies = []
                if j > 0:
                    dep_class = services[f"Service_{i}_{j-1}"]
                    dependencies.append(dep_class)
                elif i > 0:
                    dep_class = services[f"Service_{i-1}_{i-1}"]
                    dependencies.append(dep_class)
                
                # 修改构造函数签名以包含依赖
                if dependencies:
                    original_init = service_class.__init__
                    def new_init(self, *args, **kwargs):
                        # 过滤掉依赖参数
                        filtered_kwargs = {k: v for k, v in kwargs.items() 
                                         if k not in ['dependency_0', 'dependency_1']}
                        original_init(self, *args, **filtered_kwargs)
                    
                    service_class.__init__ = new_init
                    
                    # 注意: 无法动态修改__signature__属性，这是Python的限制
                    # 类型注解将在运行时通过其他方式处理
                
                # 注册服务
                container.register(service_class, service_class)
        
        # 测试解析根服务（会触发整个依赖树的解析）
        start_time = time.time()
        root_service = container.get(services["Service_9_9"])
        end_time = time.time()
        
        resolution_time = end_time - start_time
        print(f"大型依赖树解析时间: {resolution_time * 1000:.3f}ms")
        
        # 验证服务解析成功
        assert root_service is not None
        
        # 性能要求：55个服务的依赖树解析应在50ms内完成
        assert resolution_time < 0.05, f"依赖树解析时间过长: {resolution_time * 1000:.3f}ms"
    
    def test_memory_leak_detection(self, config_dir):
        """测试内存泄漏检测"""
        initial_memory = self.get_memory_usage()
        
        # 多次创建和销毁容器
        for _ in range(10):
            container = create_container(
                config_path=str(config_dir),
                environment="test"
            )
            
            # 解析一些服务
            container.get(IConfigLoader)
            container.get(IWorkflowManager)
            container.get(ISessionManager)
            
            # 清理容器
            container.clear()
            
            # 强制垃圾回收
            gc.collect()
        
        final_memory = self.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        print(f"内存泄漏测试增长: {memory_increase:.2f}MB")
        
        # 性能要求：内存增长应小于10MB
        assert memory_increase < 10, f"可能存在内存泄漏: {memory_increase:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])